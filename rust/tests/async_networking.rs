//
// async_networking.rs
// Dicom-Tools-rs
//
// Parallel networking smoke tests using the SCU helpers against a lightweight in-process SCP.
//
// Thales Matheus Mendonça Santos - November 2025

use std::net::TcpListener;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
use dicom::transfer_syntax::TransferSyntaxRegistry;
use dicom::encoding::TransferSyntaxIndex;
use dicom_tools::scu;
use dicom_ul::association::server::ServerAssociationOptions;
use dicom_ul::pdu::{PDataValue, PDataValueType, Pdu, PresentationContextResultReason};
use tempfile::{tempdir, TempDir};

#[tokio::test]
async fn storescu_runs_in_parallel_against_fake_scp() {
    let expected = 4usize;
    let (scp_handle, addr, deliveries) = spawn_fake_store_scp(expected);
    let (_dir, sample_path) = build_sample_store_file();

    let mut tasks = Vec::new();
    for _ in 0..expected {
        let addr = addr.clone();
        let path = sample_path.clone();
        tasks.push(tokio::spawn(async move {
            tokio::task::spawn_blocking(move || scu::push(&addr, &path))
                .await
                .expect("join blocking task")
                .expect("push");
        }));
    }

    for task in tasks {
        task.await.expect("task join");
    }

    scp_handle.join().expect("store scp thread");
    assert_eq!(deliveries.load(Ordering::SeqCst), expected);
}

fn spawn_fake_store_scp(
    expected_deliveries: usize,
) -> (thread::JoinHandle<()>, String, Arc<AtomicUsize>) {
    let listener = TcpListener::bind("127.0.0.1:0").expect("bind listener");
    let addr = listener.local_addr().expect("addr").to_string();
    let counter = Arc::new(AtomicUsize::new(0));
    let counter_clone = counter.clone();

    let handle = thread::spawn(move || {
        for stream in listener.incoming() {
            let stream = stream.expect("accept stream");
            let mut assoc = ServerAssociationOptions::new()
                .with_abstract_syntax("1.2.840.10008.5.1.4.1.1.7")
                .establish(stream)
                .expect("establish association");

            let accepted_pc = assoc
                .presentation_contexts()
                .iter()
                .find(|pc| pc.reason == PresentationContextResultReason::Acceptance)
                .expect("accepted pc for store");
            let pc_id = accepted_pc.id;
            let ts_cmd = TransferSyntaxRegistry
                .get("1.2.840.10008.1.2")
                .expect("cmd ts");
            let mut reached_limit = false;

            loop {
                match assoc.receive().expect("receive pdu") {
                    Pdu::PData { data } => {
                        let has_dataset = data
                            .iter()
                            .any(|pdv| pdv.value_type == PDataValueType::Data);
                        if has_dataset {
                            counter_clone.fetch_add(1, Ordering::SeqCst);
                        }

                        let mut rsp = InMemDicomObject::new_empty();
                        rsp.put(DataElement::new(
                            Tag(0x0000, 0x0100),
                            VR::US,
                            PrimitiveValue::from(0x8001_u16),
                        ));
                        rsp.put(DataElement::new(
                            Tag(0x0000, 0x0900),
                            VR::US,
                            PrimitiveValue::from(0x0000_u16),
                        ));
                        rsp.put(DataElement::new(
                            Tag(0x0000, 0x0800),
                            VR::US,
                            PrimitiveValue::from(0x0101_u16),
                        ));

                        let mut rsp_bytes = Vec::new();
                        rsp.write_dataset_with_ts(&mut rsp_bytes, ts_cmd)
                            .expect("encode rsp");
                        let _ = assoc.send(&Pdu::PData {
                            data: vec![PDataValue {
                                presentation_context_id: pc_id,
                                value_type: PDataValueType::Command,
                                is_last: true,
                                data: rsp_bytes,
                            }],
                        });

                        if counter_clone.load(Ordering::SeqCst) >= expected_deliveries {
                            reached_limit = true;
                        }
                    }
                    Pdu::ReleaseRQ => {
                        let _ = assoc.send(&Pdu::ReleaseRP);
                        break;
                    }
                    _ => {}
                }
                if reached_limit {
                    // Allow the client to drive the release after the response.
                    continue;
                }
            }

            if reached_limit {
                break;
            }
        }
    });

    (handle, addr, counter)
}

fn build_sample_store_file() -> (TempDir, std::path::PathBuf) {
    let dir = tempdir().expect("tempdir");
    let path = dir.path().join("store_sample.dcm");

    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Async^Store"),
    ));
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from("1.2.840.10008.5.1.4.1.1.7"),
    ));
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.826.0.1.3680043.2.1125.4001"),
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
        PrimitiveValue::from(vec![1_u8, 2, 3, 4]),
    ));

    let meta = FileMetaTableBuilder::new()
        .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
        .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
        .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.4001")
        .build()
        .expect("meta");

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
    for elem in obj {
        file_obj.put(elem);
    }
    file_obj
        .write_to_file(&path)
        .expect("write sample store file");

    (dir, path)
}
