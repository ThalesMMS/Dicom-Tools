//
// dicom_web_client.rs
// Dicom-Tools-rs
//
// Exercises DICOMweb QIDO/WADO flows using the dicom-web crate with a mocked server.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, VR};
use dicom::dictionary_std::{StandardDataDictionary, tags};
use dicom_core_09::Tag as TagV9;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom_web::DicomWebClient;
use serde_json::json;
use tempfile::tempdir;
use wiremock::matchers::{method, path, path_regex, query_param};
use wiremock::{Mock, MockServer, ResponseTemplate};

fn build_sample_dicom_bytes() -> Vec<u8> {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Web^Patient"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.99"),
    ));
    obj.put(DataElement::new(
        tags::ROWS,
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    obj.put(DataElement::new(
        tags::COLUMNS,
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(vec![10_u8, 20, 30, 40]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.99")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }

    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("web_sample.dcm");
    file_obj
        .write_to_file(&path)
        .expect("write sample dicom for web mock");
    std::fs::read(path).expect("read dicom bytes")
}

#[tokio::test]
async fn dicom_web_client_handles_qido_and_wado() {
    let server = MockServer::start().await;

    // Mock QIDO studies endpoint with query params for pagination and fields.
    let qido_body = json!([{
        "0020000D": { "vr": "UI", "Value": ["1.2.3.4"] },
        "00080050": { "vr": "SH", "Value": ["ACC-123"] }
    }]);
    Mock::given(method("GET"))
        .and(path("/studies"))
        .and(query_param("limit", "2"))
        .and(query_param("offset", "0"))
        .respond_with(
            ResponseTemplate::new(200)
                .insert_header("Content-Type", "application/dicom+json")
                .set_body_json(qido_body),
        )
        .mount(&server)
        .await;

    // Mock WADO instance retrieval.
    let dicom_bytes = build_sample_dicom_bytes();
    let wado_boundary = "web-boundary";
    let mut wado_body = Vec::new();
    wado_body.extend_from_slice(
        format!(
            "--{wado_boundary}\r\nContent-Type: application/dicom+json\r\n\r\n"
        )
        .as_bytes(),
    );
    wado_body.extend_from_slice(&dicom_bytes);
    wado_body.extend_from_slice(format!("\r\n--{wado_boundary}--\r\n").as_bytes());

    Mock::given(method("GET"))
        .and(path("/studies/1.2.3.4/series/4.5/instances/6.7"))
        .respond_with(
            ResponseTemplate::new(200)
                .insert_header(
                    "Content-Type",
                    format!(
                        "multipart/related; type=\"application/dicom+json\"; boundary={wado_boundary}"
                    ),
                )
                .set_body_bytes(wado_body),
        )
        .mount(&server)
        .await;

    // Mock frames retrieval (two frames returned).
    let frame_boundary = "frame-boundary";
    let frame1 = vec![1_u8, 2, 3, 4];
    let frame3 = vec![5_u8, 6, 7, 8];
    let mut frames_body = Vec::new();
    frames_body.extend_from_slice(
        format!("--{frame_boundary}\r\nContent-Type: application/octet-stream\r\n\r\n").as_bytes(),
    );
    frames_body.extend_from_slice(&frame1);
    frames_body.extend_from_slice(
        format!("\r\n--{frame_boundary}\r\nContent-Type: application/octet-stream\r\n\r\n")
            .as_bytes(),
    );
    frames_body.extend_from_slice(&frame3);
    frames_body.extend_from_slice(format!("\r\n--{frame_boundary}--\r\n").as_bytes());

    Mock::given(method("GET"))
        .and(path_regex(
            "^/studies/1\\.2\\.3\\.4/series/4\\.5/instances/6\\.7/frames/1,3$",
        ))
        .respond_with(
            ResponseTemplate::new(200)
                .insert_header(
                    "Content-Type",
                    format!("multipart/related; boundary={frame_boundary}"),
                )
                .set_body_bytes(frames_body),
        )
        .mount(&server)
        .await;

    let client = DicomWebClient::with_single_url(&server.uri());

    let mut qido = client.query_studies();
    qido.with_limit(2).with_offset(0);
    let studies = qido.run().await.expect("qido run");
    assert_eq!(studies.len(), 1);
    let study_uid = studies[0]
        .element(TagV9(0x0020, 0x000D))
        .expect("study uid")
        .to_str()
        .unwrap();
    assert_eq!(study_uid, "1.2.3.4");

    let instance = client
        .retrieve_instance("1.2.3.4", "4.5", "6.7")
        .run()
        .await
        .expect("wado instance");
    let sop_uid = instance
        .element(TagV9(0x0008, 0x0018))
        .expect("sop uid")
        .to_str()
        .unwrap();
    assert_eq!(sop_uid, "1.2.826.0.1.3680043.2.1125.99");

    let frames = client
        .retrieve_frames("1.2.3.4", "4.5", "6.7", &[1, 3])
        .run()
        .await
        .expect("frames");
    assert_eq!(frames.len(), 2);
    assert_eq!(frames[0].data, frame1);
    assert_eq!(frames[1].data, frame3);
}
