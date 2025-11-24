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

    let app = Router::new()
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
        .layer(CorsLayer::permissive());

    let addr: SocketAddr = format!("{}:{}", host, port).parse()?;
    println!("Server running at http://{}", addr);

    let listener = TcpListener::bind(addr).await?;
    axum::serve(listener, app).await?;
    Ok(())
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
