//
// batch.rs
// Dicom-Tools-rs
//
// Recursively scans directories and runs anonymization or validation in parallel over all DICOM files.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::Result;
use rayon::prelude::*;
use std::path::Path;
use walkdir::WalkDir;

use crate::{anonymize, cli::BatchOperation, validate};

pub fn process_directory(dir: &Path, operation: BatchOperation) -> Result<()> {
    // Scan recursively for `.dcm` files and fan out work across threads with Rayon.
    println!(
        "Processando diretório: {:?} | Operação: {:?}",
        dir, operation
    );

    let files: Vec<_> = WalkDir::new(dir)
        .into_iter()
        .filter_map(|e| e.ok())
        .filter(|e| e.path().extension().map_or(false, |ext| ext == "dcm"))
        .collect();

    println!("Encontrados {} arquivos.", files.len());

    files.par_iter().for_each(|entry| {
        let path = entry.path();
        // Each file is processed independently; failures are logged but do not stop the batch.
        let res = match operation {
            BatchOperation::Anonymize => anonymize::process_file(path, None),
            BatchOperation::Validate => validate::check_file(path),
        };

        if let Err(e) = res {
            eprintln!("Erro em {:?}: {}", path, e);
        } else {
            println!("Sucesso: {:?}", path.file_name().unwrap());
        }
    });

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
    use dicom::dictionary_std::StandardDataDictionary;
    use dicom::object::{FileDicomObject, FileMetaTableBuilder, InMemDicomObject};
    use dicom::transfer_syntax::entries::EXPLICIT_VR_LITTLE_ENDIAN;
    use tempfile::tempdir;

    fn write_minimal_dicom(path: &Path) {
        let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
        obj.put(DataElement::new(
            Tag(0x0010, 0x0010),
            VR::PN,
            PrimitiveValue::from("Batch^Patient"),
        ));
        obj.put(DataElement::new(
            Tag(0x7FE0, 0x0010),
            VR::OB,
            PrimitiveValue::from(vec![0_u8]),
        ));

        let meta = FileMetaTableBuilder::new()
            .transfer_syntax(EXPLICIT_VR_LITTLE_ENDIAN.uid())
            .media_storage_sop_class_uid("1.2.840.10008.5.1.4.1.1.7")
            .media_storage_sop_instance_uid("1.2.826.0.1.3680043.2.1125.9.1")
            .build()
            .expect("meta");

        let mut file_obj =
            FileDicomObject::new_empty_with_dict_and_meta(StandardDataDictionary, meta);
        for elem in obj {
            file_obj.put(elem);
        }
        file_obj.write_to_file(path).expect("write dicom");
    }

    #[test]
    fn batch_process_handles_anonymize_and_validate() {
        let dir = tempdir().expect("tempdir");
        let dcm_path = dir.path().join("sample.dcm");
        write_minimal_dicom(&dcm_path);

        process_directory(dir.path(), BatchOperation::Validate).expect("validate batch");
        process_directory(dir.path(), BatchOperation::Anonymize).expect("anon batch");
    }
}
