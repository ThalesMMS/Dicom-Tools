//
// storage_tests.rs
// Dicom-Tools-rs
//
// Testes adicionais para FileStore (armazenamento seguro de arquivos DICOM).
//
// Thales Matheus Mendonça Santos - November 2025

use dicom_tools::storage::FileStore;
use std::fs;
use tempfile::tempdir;

#[test]
fn test_save_with_original_name() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename = store
        .save(Some("patient^file.dcm"), b"dicom data")
        .expect("save");

    assert!(filename.contains("patient"));
    assert!(filename.ends_with(".dcm"));
    assert!(dir.path().join(&filename).exists());
}

#[test]
fn test_save_without_original_name() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename = store.save(None, b"dicom data").expect("save");

    assert!(filename.starts_with("dicom-"));
    assert!(filename.ends_with(".dcm"));
    assert!(dir.path().join(&filename).exists());
}

#[test]
fn test_save_sanitizes_filename() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename = store
        .save(Some("../../etc/passwd.dcm"), b"data")
        .expect("save");

    // Verificar que caracteres perigosos foram removidos
    assert!(!filename.contains("../"));
    assert!(!filename.contains("/"));
    assert!(dir.path().join(&filename).exists());
}

#[test]
fn test_save_creates_unique_names() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename1 = store.save(Some("test.dcm"), b"data1").expect("save");
    let filename2 = store.save(Some("test.dcm"), b"data2").expect("save");

    // Arquivos diferentes devem ter nomes diferentes (hash diferente)
    assert_ne!(filename1, filename2);
}

#[test]
fn test_resolve_valid_file() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename = store.save(Some("test.dcm"), b"data").expect("save");
    let resolved = store.resolve(&filename).expect("resolve");

    assert!(resolved.exists());
    assert!(resolved.is_file());
}

#[test]
fn test_resolve_rejects_path_traversal() {
    let dir = tempdir().expect("tempdir");
    let store_root = dir.path().join("safe");
    fs::create_dir_all(&store_root).expect("create safe dir");
    let store = FileStore::new(&store_root).expect("store");

    // Criar arquivo fora do diretório seguro
    let outside = dir.path().join("outside.dcm");
    fs::write(&outside, b"outside").expect("write outside");

    // Tentar acessar usando path traversal
    assert!(store.resolve("../outside.dcm").is_err());
}

#[test]
fn test_derived_path() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let (filename, path) = store
        .derived_path("source.dcm", "preview", "png")
        .expect("derived path");

    assert_eq!(filename, "source-preview.png");
    assert_eq!(path, dir.path().join("source-preview.png"));
}

#[test]
fn test_derived_path_sanitizes() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let (filename, _) = store
        .derived_path("../../source.dcm", "preview", "png")
        .expect("derived path");

    assert!(!filename.contains("../"));
    assert_eq!(filename, "source-preview.png");
}

#[test]
fn test_save_empty_name() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename = store.save(Some(""), b"data").expect("save");

    assert!(filename.starts_with("dicom-"));
    assert!(filename.ends_with(".dcm"));
}

#[test]
fn test_save_special_characters() {
    let dir = tempdir().expect("tempdir");
    let store = FileStore::new(dir.path()).expect("store");

    let filename = store
        .save(Some("file with spaces & symbols!.dcm"), b"data")
        .expect("save");

    // Verificar que caracteres especiais foram removidos
    assert!(!filename.contains(" "));
    assert!(!filename.contains("&"));
    assert!(!filename.contains("!"));
    assert!(dir.path().join(&filename).exists());
}

