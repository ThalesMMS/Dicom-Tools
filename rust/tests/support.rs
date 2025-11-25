//
// support.rs
// Helpers shared across integration tests (builders and fake DICOM services).
//
// Thales Matheus Mendonça Santos - November 2025

use std::net::TcpListener;
use std::path::PathBuf;
use std::thread;

use dicom::core::value::DataSetSequence;
use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::encoding::TransferSyntaxIndex;
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom::transfer_syntax::TransferSyntaxRegistry;
use dicom_ul::association::server::ServerAssociationOptions;
use dicom_ul::pdu::{PDataValue, PDataValueType, Pdu, PresentationContextResultReason};
use tempfile::{tempdir, TempDir};

pub fn build_multiframe_fg_dicom() -> (TempDir, PathBuf) {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("multi_frame_fg.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Minimal demographic + identification data.
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Functional^Group"),
    ));
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from("FG123"),
    ));
    obj.put(DataElement::new(
        tags::STUDY_DATE,
        VR::DA,
        PrimitiveValue::from("20240401"),
    ));
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("MR"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.4"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.2.1"),
    ));

    // Image shape and encoding.
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
        tags::NUMBER_OF_FRAMES,
        VR::IS,
        PrimitiveValue::from("3"),
    ));
    obj.put(DataElement::new(
        tags::SAMPLES_PER_PIXEL,
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    obj.put(DataElement::new(
        tags::PHOTOMETRIC_INTERPRETATION,
        VR::CS,
        PrimitiveValue::from("MONOCHROME2"),
    ));
    obj.put(DataElement::new(
        tags::BITS_ALLOCATED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::BITS_STORED,
        VR::US,
        PrimitiveValue::from(8_u16),
    ));
    obj.put(DataElement::new(
        tags::HIGH_BIT,
        VR::US,
        PrimitiveValue::from(7_u16),
    ));
    obj.put(DataElement::new(
        tags::PIXEL_REPRESENTATION,
        VR::US,
        PrimitiveValue::from(0_u16),
    ));

    // Shared FG: pixel spacing, spacing between slices, and orientation.
    let mut pixel_measures = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    pixel_measures.put(DataElement::new(
        tags::PIXEL_SPACING,
        VR::DS,
        PrimitiveValue::from([0.5_f64, 0.5_f64]),
    ));
    pixel_measures.put(DataElement::new(
        tags::SPACING_BETWEEN_SLICES,
        VR::DS,
        PrimitiveValue::from([2.0_f64]),
    ));
    let mut plane_orientation = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    plane_orientation.put(DataElement::new(
        tags::IMAGE_ORIENTATION_PATIENT,
        VR::DS,
        PrimitiveValue::from([1.0_f64, 0.0, 0.0, 0.0, 1.0, 0.0]),
    ));

    let mut shared_item = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    shared_item.put(DataElement::new(
        tags::PIXEL_MEASURES_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![pixel_measures]),
    ));
    shared_item.put(DataElement::new(
        tags::PLANE_ORIENTATION_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![plane_orientation]),
    ));

    obj.put(DataElement::new(
        tags::SHARED_FUNCTIONAL_GROUPS_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![shared_item]),
    ));

    // Per-frame FG: VOI (window) and positions vary per frame.
    let mut per_frame_items = Vec::new();
    let window_centers = [10.0, 60.0, 100.0];
    let window_widths = [20.0, 30.0, 40.0];
    let z_positions = [0.0, 2.0, 4.0];

    for ((wc, ww), z) in window_centers.iter().zip(window_widths.iter()).zip(z_positions.iter()) {
        let mut voi = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        voi.put(DataElement::new(
            tags::WINDOW_CENTER,
            VR::DS,
            PrimitiveValue::from([*wc]),
        ));
        voi.put(DataElement::new(
            tags::WINDOW_WIDTH,
            VR::DS,
            PrimitiveValue::from([*ww]),
        ));

        let mut plane_position = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        plane_position.put(DataElement::new(
            tags::IMAGE_POSITION_PATIENT,
            VR::DS,
            PrimitiveValue::from([0.0_f64, 0.0, *z]),
        ));

        let mut frame_item = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        frame_item.put(DataElement::new(
            tags::FRAME_VOILUT_SEQUENCE,
            VR::SQ,
            DataSetSequence::from(vec![voi]),
        ));
        frame_item.put(DataElement::new(
            tags::PLANE_POSITION_SEQUENCE,
            VR::SQ,
            DataSetSequence::from(vec![plane_position]),
        ));

        per_frame_items.push(frame_item);
    }

    obj.put(DataElement::new(
        tags::PER_FRAME_FUNCTIONAL_GROUPS_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(per_frame_items),
    ));

    // Pixel data across three frames: incremental values for easy verification.
    let pixels: Vec<u8> = vec![0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110];
    obj.put(DataElement::new(tags::PIXEL_DATA, VR::OB, PrimitiveValue::from(pixels)));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.4")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.2.1")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }

    file_obj
        .write_to_file(&path)
        .expect("Failed to write DICOM file");

    (dir, path)
}

pub fn build_sr_like_dicom() -> (TempDir, PathBuf) {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("sr_like.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Structured^Report"),
    ));
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from("SR001"),
    ));
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("SR"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.88.11"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.3.1"),
    ));

    // Build SR ContentSequence with nested items.
    let mut concept = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    concept.put(DataElement::new(
        tags::CODE_VALUE,
        VR::SH,
        PrimitiveValue::from("121070"),
    ));
    concept.put(DataElement::new(
        tags::CODE_MEANING,
        VR::LO,
        PrimitiveValue::from("Findings"),
    ));
    concept.put(DataElement::new(
        tags::CODING_SCHEME_DESIGNATOR,
        VR::SH,
        PrimitiveValue::from("DCM"),
    ));

    let mut nested_text = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    nested_text.put(DataElement::new(
        tags::VALUE_TYPE,
        VR::CS,
        PrimitiveValue::from("TEXT"),
    ));
    nested_text.put(DataElement::new(
        tags::TEXT_VALUE,
        VR::UT,
        PrimitiveValue::from("Lesion size 3mm"),
    ));

    let mut container_child = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    container_child.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![nested_text]),
    ));

    let mut root_container = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    root_container.put(DataElement::new(
        tags::VALUE_TYPE,
        VR::CS,
        PrimitiveValue::from("CONTAINER"),
    ));
    root_container.put(DataElement::new(
        tags::CONCEPT_NAME_CODE_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![concept]),
    ));
    root_container.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![container_child]),
    ));

    obj.put(DataElement::new(
        tags::CONTENT_SEQUENCE,
        VR::SQ,
        DataSetSequence::from(vec![root_container]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.88.11")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.3.1")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj
        .write_to_file(&path)
        .expect("Failed to write SR-like DICOM");

    (dir, path)
}

pub fn spawn_fake_find_scp() -> (thread::JoinHandle<()>, String) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind listener");
    let addr = listener.local_addr().expect("addr");
    let handle = thread::spawn(move || {
        let (stream, _) = listener.accept().expect("accept");
        let mut assoc = ServerAssociationOptions::new()
            .with_abstract_syntax("1.2.840.10008.5.1.4.1.2.2.1")
            .establish(stream)
            .expect("establish association");

        let accepted_pc = assoc
            .presentation_contexts()
            .iter()
            .find(|pc| pc.reason == PresentationContextResultReason::Acceptance)
            .expect("accepted pc");
        let pc_id = accepted_pc.id;
        let negotiated_ts = TransferSyntaxRegistry
            .get(&accepted_pc.transfer_syntax)
            .expect("ts");
        let ts_cmd = TransferSyntaxRegistry
            .get("1.2.840.10008.1.2")
            .expect("cmd ts");

        // Consume request PDUs then reply with pending + final.
        let _ = assoc.receive().expect("receive request");

        let mut pending_cmd = InMemDicomObject::new_empty();
        pending_cmd.put(DataElement::new(
            Tag(0x0000, 0x0002),
            VR::UI,
            PrimitiveValue::from("1.2.840.10008.5.1.4.1.2.2.1"),
        ));
        pending_cmd.put(DataElement::new(
            Tag(0x0000, 0x0100),
            VR::US,
            PrimitiveValue::from(0x8020_u16),
        ));
        pending_cmd.put(DataElement::new(
            Tag(0x0000, 0x0120),
            VR::US,
            PrimitiveValue::from(1_u16),
        ));
        pending_cmd.put(DataElement::new(
            Tag(0x0000, 0x0800),
            VR::US,
            PrimitiveValue::from(0x0000_u16),
        ));
        pending_cmd.put(DataElement::new(
            Tag(0x0000, 0x0900),
            VR::US,
            PrimitiveValue::from(0xFF00_u16),
        ));

        let mut pending_ds = InMemDicomObject::new_empty();
        pending_ds.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("FIND^PATIENT"),
        ));
        pending_ds.put(DataElement::new(
            Tag(0x0020, 0x000D),
            VR::UI,
            PrimitiveValue::from("1.2.3.4"),
        ));

        let mut cmd_bytes = Vec::new();
        pending_cmd
            .write_dataset_with_ts(&mut cmd_bytes, ts_cmd)
            .expect("encode pending cmd");

        let mut ds_bytes = Vec::new();
        pending_ds
            .write_dataset_with_ts(&mut ds_bytes, negotiated_ts)
            .expect("encode pending ds");

        assoc
            .send(&Pdu::PData {
                data: vec![PDataValue {
                    presentation_context_id: pc_id,
                    value_type: PDataValueType::Command,
                    is_last: true,
                    data: cmd_bytes.clone(),
                }],
            })
            .expect("send pending cmd");
        assoc
            .send(&Pdu::PData {
                data: vec![PDataValue {
                    presentation_context_id: pc_id,
                    value_type: PDataValueType::Data,
                    is_last: true,
                    data: ds_bytes,
                }],
            })
            .expect("send pending data");

        // Final success without dataset.
        let mut final_cmd = pending_cmd;
        final_cmd.put(DataElement::new(
            Tag(0x0000, 0x0900),
            VR::US,
            PrimitiveValue::from(0x0000_u16),
        ));
        final_cmd.put(DataElement::new(
            Tag(0x0000, 0x0800),
            VR::US,
            PrimitiveValue::from(0x0101_u16),
        ));

        let mut final_cmd_bytes = Vec::new();
        final_cmd
            .write_dataset_with_ts(&mut final_cmd_bytes, ts_cmd)
            .expect("encode final cmd");

        assoc
            .send(&Pdu::PData {
                data: vec![PDataValue {
                    presentation_context_id: pc_id,
                    value_type: PDataValueType::Command,
                    is_last: true,
                    data: final_cmd_bytes,
                }],
            })
            .expect("send final cmd");

        if let Ok(Pdu::ReleaseRQ) = assoc.receive() {
            let _ = assoc.send(&Pdu::ReleaseRP);
        }
    });

    (handle, format!("{}", addr))
}

/// Write a small Secondary Capture DICOM useful for quick tests.
pub fn write_secondary_capture(path: &std::path::Path, patient_name: &str) {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        Tag(0x0010, 0x0010),
        VR::PN,
        PrimitiveValue::from(patient_name),
    ));
    obj.put(DataElement::new(
        Tag(0x7FE0, 0x0010),
        VR::OB,
        PrimitiveValue::from(vec![0_u8, 1, 2, 3]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.9.99")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj.write_to_file(path).expect("write dicom");
}
