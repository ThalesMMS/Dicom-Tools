//
// main.rs
// Dicom-Tools-rs
//
// Tokio entry point that hands off execution to the CLI layer so commands are resolved asynchronously.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom_tools::cli;

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Tokio runtime entry point: delegate all argument parsing and dispatching to the CLI module.
    cli::run().await
}
