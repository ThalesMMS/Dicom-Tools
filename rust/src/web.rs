//
// web.rs
// Dicom-Tools-rs
//
// Axum-based HTTP server exposing upload, metadata, image preview, anonymization, and validation APIs.
//
// Thales Matheus Mendonça Santos - November 2025

use std::fmt::Display;
use std::net::SocketAddr;

use axum::{
    extract::{Multipart, Path, Query, State},
    http::{header, HeaderValue, StatusCode},
    response::{Html, IntoResponse},
    routing::{get, post},
    Json, Router,
};
use dicom::object::open_file;
use dicom::pixeldata::PixelDecoder;
use serde::Deserialize;
use serde_json::{json, Value};
use tokio::net::TcpListener;
use tower_http::cors::CorsLayer;

use crate::{
    anonymize, image, json, metadata,
    models::{DetailedMetadata, PixelStatistics, ValidationSummary},
    stats,
    storage::FileStore,
    validate,
};

#[derive(Clone)]
struct AppState {
    store: FileStore,
}

type ApiResult<T> = Result<T, (StatusCode, String)>;

/// Bootstraps the Axum HTTP server and wires up API routes.
pub async fn start_server(host: &str, port: u16) -> anyhow::Result<()> {
    let state = AppState {
        store: FileStore::new("target/uploads")?,
    };

    let app = build_app(state).into_make_service();

    let addr: SocketAddr = format!("{}:{}", host, port).parse()?;
    println!("Server running at http://{}", addr);

    let listener = TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
}

fn build_app(state: AppState) -> Router {
    Router::new()
        .route("/", get(root_handler))
        .route("/api/metadata/:filename", get(get_metadata))
        .route("/api/upload", post(upload_handler))
        .route("/api/stats/:filename", get(get_stats))
        .route("/api/image/:filename", get(get_image_preview))
        .route("/api/anonymize/:filename", post(anonymize_handler))
        .route("/api/validate/:filename", get(validate_handler))
        .route("/api/json/:filename", get(json_handler))
        .route("/api/download/:filename", get(download_handler))
        .route("/api/histogram/:filename", get(histogram_handler))
        .with_state(state)
        .layer(CorsLayer::permissive())
}

async fn root_handler() -> Html<&'static str> {
    Html(include_str!("templates/index.html"))
}

async fn upload_handler(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> ApiResult<Json<Value>> {
    let mut original_name = None;
    let mut data = None;

    // Find the first part named "file" and pull bytes eagerly.
    while let Some(field) = multipart.next_field().await.map_err(bad_request)? {
        if field.name() == Some("file") {
            original_name = field.file_name().map(|s| s.to_string());
            data = Some(field.bytes().await.map_err(internal_error)?);
            break;
        }
    }

    let data = data.ok_or((StatusCode::BAD_REQUEST, "No file uploaded".to_string()))?;
    let saved_name = state
        .store
        .save(original_name.as_deref(), &data)
        .map_err(internal_error)?;
    let path = state.store.resolve(&saved_name).map_err(internal_error)?;

    // Parse once so we can return metadata, validation, and pixel information together.
    let obj = open_file(&path).map_err(internal_error)?;
    let info = metadata::extract_basic_metadata(&obj);
    let validation = validate::validate_obj(&obj);
    let summary = validate::as_summary(&validation);
    let decoded = obj.decode_pixel_data().ok();
    let pixel_format = decoded
        .as_ref()
        .and_then(|d| stats::pixel_format_from_decoded(d).ok())
        .or_else(|| stats::pixel_format_for_file(&path).ok());

    Ok(Json(json!({
        "success": true,
        "filename": saved_name,
        "info": info,
        "validation": summary,
        "pixel_format": pixel_format
    })))
}

async fn get_metadata(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<Json<DetailedMetadata>> {
    // Detailed metadata is read lazily when requested to keep uploads fast.
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let detailed = metadata::read_detailed_metadata(&path).map_err(internal_error)?;
    Ok(Json(detailed))
}

async fn get_stats(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<Json<PixelStatistics>> {
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let stats = stats::pixel_statistics_for_file(&path).map_err(internal_error)?;
    Ok(Json(stats))
}

#[derive(Debug, Default, Deserialize)]
struct HistogramQuery {
    bins: Option<usize>,
}

async fn histogram_handler(
    State(state): State<AppState>,
    Path(filename): Path<String>,
    Query(query): Query<HistogramQuery>,
) -> ApiResult<Json<Value>> {
    let bins = query.bins.unwrap_or(256);
    if bins == 0 {
        return Err((
            StatusCode::BAD_REQUEST,
            "bins must be greater than 0".into(),
        ));
    }
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let histogram = stats::histogram_for_file(&path, bins).map_err(internal_error)?;
    Ok(Json(json!({
        "bins": histogram.bins,
        "min": histogram.min,
        "max": histogram.max
    })))
}

async fn get_image_preview(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<impl IntoResponse> {
    let path = state.store.resolve(&filename).map_err(not_found)?;
    // Render the first frame to PNG bytes so the UI can embed an <img>.
    let bytes = image::first_frame_png_bytes(&path).map_err(internal_error)?;
    Ok(([(header::CONTENT_TYPE, "image/png")], bytes))
}

async fn anonymize_handler(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<Json<Value>> {
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let (anon_name, anon_path) = state
        .store
        .derived_path(&filename, "anon", "dcm")
        .map_err(internal_error)?;

    // Run anonymization in-place and return the new filename for download.
    anonymize::process_file(&path, Some(anon_path)).map_err(internal_error)?;

    Ok(Json(json!({ "success": true, "filename": anon_name })))
}

async fn validate_handler(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<Json<Value>> {
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let obj = open_file(&path).map_err(internal_error)?;
    let report = validate::validate_obj(&obj);
    let summary = validate::as_summary(&report);
    let (errors, warnings) = validation_messages(&summary);

    Ok(Json(json!({
        "valid": summary.valid,
        "errors": errors,
        "warnings": warnings,
        "missing_tags": summary.missing_tags,
        "has_pixel_data": summary.has_pixel_data
    })))
}

async fn json_handler(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<Json<Value>> {
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let json_string = json::to_json_string(&path).map_err(internal_error)?;
    let value: Value = serde_json::from_str(&json_string).map_err(internal_error)?;
    Ok(Json(value))
}

async fn download_handler(
    State(state): State<AppState>,
    Path(filename): Path<String>,
) -> ApiResult<impl IntoResponse> {
    let path = state.store.resolve(&filename).map_err(not_found)?;
    let bytes = tokio::fs::read(&path).await.map_err(internal_error)?;
    let disposition = HeaderValue::from_str(&format!("attachment; filename=\"{}\"", filename))
        .map_err(internal_error)?;
    Ok((
        [
            (
                header::CONTENT_TYPE,
                HeaderValue::from_static("application/dicom"),
            ),
            (header::CONTENT_DISPOSITION, disposition),
        ],
        bytes,
    ))
}

fn validation_messages(summary: &ValidationSummary) -> (Vec<String>, Vec<String>) {
    // Split validation findings into fatal errors and softer warnings for the UI.
    let mut errors = Vec::new();
    if !summary.missing_tags.is_empty() {
        errors.push(format!(
            "Missing {} attribute(s): {}",
            summary.missing_tags.len(),
            summary.missing_tags.join(", ")
        ));
    }

    let mut warnings = Vec::new();
    if !summary.has_pixel_data {
        warnings.push("Pixel Data element not present".to_string());
    }

    (errors, warnings)
}

fn bad_request<E: Display>(err: E) -> (StatusCode, String) {
    (StatusCode::BAD_REQUEST, err.to_string())
}

fn internal_error<E: Display>(err: E) -> (StatusCode, String) {
    (StatusCode::INTERNAL_SERVER_ERROR, err.to_string())
}

fn not_found<E: Display>(err: E) -> (StatusCode, String) {
    (StatusCode::NOT_FOUND, err.to_string())
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::models::ValidationSummary;
    use tempfile::tempdir;

    #[test]
    fn validation_messages_splits_errors_and_warnings() {
        let summary = ValidationSummary {
            valid: false,
            missing_tags: vec!["PatientID".into(), "Modality".into()],
            has_pixel_data: false,
        };
        let (errors, warnings) = validation_messages(&summary);
        assert_eq!(errors.len(), 1);
        assert_eq!(warnings.len(), 1);
        assert!(errors[0].contains("Missing 2 attribute"));
        assert!(warnings[0].contains("Pixel Data"));
    }

    #[test]
    fn error_helpers_return_status_and_message() {
        let e = bad_request("fail");
        assert_eq!(e.0, StatusCode::BAD_REQUEST);
        assert_eq!(e.1, "fail");

        let i = internal_error("boom");
        assert_eq!(i.0, StatusCode::INTERNAL_SERVER_ERROR);
        assert_eq!(i.1, "boom");

        let n = not_found("missing");
        assert_eq!(n.0, StatusCode::NOT_FOUND);
        assert_eq!(n.1, "missing");
    }

    #[tokio::test]
    async fn histogram_handler_returns_bins() {
        let dir = tempdir().expect("tempdir");
        let store = FileStore::new(dir.path().to_str().unwrap()).expect("store");
        let sample_path = dir.path().join("web_hist.dcm");
        write_minimal_dicom(&sample_path);
        let saved = store
            .save(Some("web_hist.dcm"), &std::fs::read(&sample_path).unwrap())
            .expect("save");

        let state = AppState { store };
        let Json(json) = histogram_handler(
            State(state),
            Path(saved),
            Query(HistogramQuery { bins: Some(4) }),
        )
        .await
        .expect("histogram");
        assert_eq!(json["bins"].as_array().unwrap().len(), 4);
    }

    #[tokio::test]
    async fn validate_handler_reports_missing_tags() {
        let dir = tempdir().expect("tempdir");
        let store = FileStore::new(dir.path().to_str().unwrap()).expect("store");
        let sample_path = dir.path().join("web_validate.dcm");
        write_minimal_dicom(&sample_path);
        let saved = store
            .save(Some("web_validate.dcm"), &std::fs::read(&sample_path).unwrap())
            .expect("save");

        let state = AppState { store };
        let Json(json) = validate_handler(State(state), Path(saved))
            .await
            .expect("validate");
        assert!(json["errors"].as_array().unwrap().is_empty());
    }

    fn write_minimal_dicom(path: &std::path::Path) {
        use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
        use dicom::dictionary_std::StandardDataDictionary;
        use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
        use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;

        let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        obj.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("Web^Patient"),
        ));
        obj.put(DataElement::new(
            Tag(0x0010, 0x0020),
            VR::LO,
            PrimitiveValue::from("WEB123"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0016),
            VR::UI,
            PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0018),
            VR::UI,
            PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.9.3.1"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0060),
            VR::CS,
            PrimitiveValue::from("OT"),
        ));
        obj.put(DataElement::new(
            Tag(0x0008, 0x0020),
            VR::DA,
            PrimitiveValue::from("20240101"),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0010),
            VR::US,
            PrimitiveValue::from(2_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0011),
            VR::US,
            PrimitiveValue::from(2_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0002),
            VR::US,
            PrimitiveValue::from(1_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0100),
            VR::US,
            PrimitiveValue::from(8_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0101),
            VR::US,
            PrimitiveValue::from(8_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0102),
            VR::US,
            PrimitiveValue::from(7_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0103),
            VR::US,
            PrimitiveValue::from(0_u16),
        ));
        obj.put(DataElement::new(
            Tag(0x0028, 0x0004),
            VR::CS,
            PrimitiveValue::from("MONOCHROME2"),
        ));
        obj.put(DataElement::new(
            Tag(0x7FE0, 0x0010),
            VR::OB,
            PrimitiveValue::from(vec![0_u8, 1, 2, 3]),
        ));

        let meta = FileMetaTableBuilder::new()
            .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
            .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
            .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.9.3")
            .build()
            .expect("meta");

        let mut file_obj =
            FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
        for elem in obj {
            file_obj.put(elem);
        }
        file_obj.write_to_file(path).expect("write dicom");
    }
}
