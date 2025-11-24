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
