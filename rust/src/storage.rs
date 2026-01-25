//
// storage.rs
// Dicom-Tools-rs
//
// Provides a safe file store for uploaded/derived DICOM files with path sanitization and hashing.
//
// Thales Matheus Mendonça Santos - November 2025

use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{bail, Context, Result};
use sha2::{Digest, Sha256};

#[derive(Clone)]
pub struct FileStore {
    root: PathBuf,
}

impl FileStore {
    pub fn new(root: impl AsRef<Path>) -> Result<Self> {
        let root = root.as_ref().to_path_buf();
        // Create the upload directory eagerly so subsequent saves do not fail at runtime.
        fs::create_dir_all(&root).context("Failed to create upload directory")?;
        Ok(Self { root })
    }

    pub fn save(&self, original_name: Option<&str>, bytes: &[u8]) -> Result<String> {
        // Use a sanitized stem plus a content hash to avoid collisions and unsafe paths.
        let stem = original_name
            .and_then(|n| Path::new(n).file_stem().and_then(|s| s.to_str()))
            .map(sanitize_filename)
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| "dicom".to_string());

        let hash = hex::encode(Sha256::digest(bytes));
        let filename = format!("{}-{}.dcm", stem, &hash[..12]);
        let path = self.root.join(&filename);
        fs::write(&path, bytes).context("Failed to persist uploaded file")?;
        Ok(filename)
    }

    pub fn resolve(&self, name: &str) -> Result<PathBuf> {
        let candidate = self.root.join(name);
        let canonical_root = self
            .root
            .canonicalize()
            .unwrap_or_else(|_| self.root.clone());
        let canonical = candidate
            .canonicalize()
            .context("Requested file not found")?;
        // Guard against path traversal by enforcing the canonical root prefix.
        if !canonical.starts_with(&canonical_root) {
            bail!("Attempt to access file outside storage root");
        }
        Ok(canonical)
    }

    pub fn derived_path(
        &self,
        source_name: &str,
        suffix: &str,
        extension: &str,
    ) -> Result<(String, PathBuf)> {
        let base = Path::new(source_name)
            .file_stem()
            .and_then(|s| s.to_str())
            .map(sanitize_filename)
            .filter(|s| !s.is_empty())
            .unwrap_or_else(|| "dicom".to_string());

        let filename = format!("{}-{}.{}", base, suffix, extension);
        Ok((filename.clone(), self.root.join(filename)))
    }
}

fn sanitize_filename(input: &str) -> String {
    // Keep only ASCII word characters and a few safe separators to avoid filesystem surprises.
    input
        .chars()
        .filter(|c| c.is_ascii_alphanumeric() || *c == '-' || *c == '_')
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    use tempfile::tempdir;

    #[test]
    fn sanitize_strips_dangerous_characters() {
        let cleaned = sanitize_filename("../weird name 123.dcm");
        assert_eq!(cleaned, "weirdname123dcm");
    }

    #[test]
    fn resolve_rejects_paths_outside_root() {
        let root = tempdir().expect("tmpdir");
        let store_root = root.path().join("safe-area");
        fs::create_dir_all(&store_root).expect("create nested root");
        let store = FileStore::new(&store_root).expect("store");

        let outside = root.path().join("escape.dcm");
        fs::write(&outside, b"attack").expect("write outside file");

        assert!(store.resolve("../escape.dcm").is_err());

        let legit = store.save(Some("patient^file.dcm"), b"abc").expect("save");
        let resolved = store.resolve(&legit).expect("resolve legit");
        let canonical_root = store_root.canonicalize().expect("canonical root");
        assert!(resolved.starts_with(&canonical_root));
    }
}
