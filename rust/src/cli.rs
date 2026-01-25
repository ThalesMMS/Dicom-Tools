//
// cli.rs
// Dicom-Tools-rs
//
// Defines the CLI surface with Clap and dispatches user-selected commands to the corresponding modules.
//
// Thales Matheus Mendonça Santos - November 2025

use std::path::PathBuf;

use anyhow::{anyhow, bail};
use clap::{Parser, Subcommand, ValueEnum};
use dicom_pixeldata::WindowLevel;

use crate::{anonymize, batch, dump, image, json, metadata, scu, stats, transcode, validate, web};

/// Command-line interface glue code: defines the available verbs and dispatches to modules.
#[derive(Parser)]
#[command(name = "dicom-tools")]
#[command(about = "Ferramentas DICOM em Rust", long_about = None)]
pub struct Cli {
    #[command(subcommand)]
    pub command: Commands,
}

#[derive(Subcommand)]
pub enum Commands {
    /// Extract metadata (analogue to extract_metadata.py / dicom_info.py)
    Info {
        file: PathBuf,
        #[arg(short, long)]
        verbose: bool,
        #[arg(long, help = "Emit metadata as JSON instead of plain text")]
        json: bool,
    },
    /// Anonymize a DICOM file
    Anonymize {
        input: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Convert to an image (similar to convert_to_image.py)
    #[command(alias = "to_image")]
    ToImage {
        input: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
        #[arg(long, default_value = "png")]
        format: String,
        #[arg(long)]
        frame: Option<u32>,
        #[arg(long)]
        window_center: Option<f64>,
        #[arg(long)]
        window_width: Option<f64>,
        #[arg(long)]
        normalize: bool,
        #[arg(long)]
        disable_modality_lut: bool,
        #[arg(long)]
        disable_voi_lut: bool,
        #[arg(long, conflicts_with = "force_16bit")]
        force_8bit: bool,
        #[arg(long)]
        force_16bit: bool,
    },
    /// Validate file integrity
    Validate { file: PathBuf },
    /// Start the web server
    Web {
        #[arg(short, long, default_value = "127.0.0.1")]
        host: String,
        #[arg(short, long, default_value_t = 3000)]
        port: u16,
    },
    /// Batch processing over a directory
    Batch {
        #[arg(short, long)]
        directory: PathBuf,
        #[arg(short, long, value_enum)]
        operation: BatchOperation,
    },
    /// Perform a DICOM C-ECHO (Ping)
    Echo { addr: String },
    /// Perform a DICOM C-STORE (Push)
    Push { addr: String, file: PathBuf },
    /// Convert DICOM to JSON
    ToJson {
        file: PathBuf,
        #[arg(short, long)]
        output: Option<PathBuf>,
    },
    /// Convert JSON to DICOM
    FromJson {
        input: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
    },
    /// Transcode a DICOM file (Decompress)
    Transcode {
        input: PathBuf,
        #[arg(short, long)]
        output: PathBuf,
        #[arg(
            long,
            value_enum,
            default_value_t = TransferSyntax::ExplicitVrLittleEndian,
            visible_alias = "syntax",
            help = "Target transfer syntax (uncompressed only)"
        )]
        transfer_syntax: TransferSyntax,
    },
    /// Calculate Pixel Statistics
    Stats { file: PathBuf },
    /// Generate an intensity histogram
    Histogram {
        file: PathBuf,
        #[arg(long, default_value_t = 256)]
        bins: usize,
    },
    /// Dump the whole DICOM dataset
    Dump {
        file: PathBuf,
        #[arg(long, default_value_t = 4, visible_alias = "depth")]
        max_depth: usize,
        #[arg(long, default_value_t = 64)]
        max_value_len: usize,
        #[arg(long, help = "Emit dataset as DICOM JSON instead of text")]
        json: bool,
    },
}

#[derive(Copy, Clone, Debug, ValueEnum)]
pub enum BatchOperation {
    Anonymize,
    Validate,
}

#[derive(Copy, Clone, Debug, ValueEnum)]
pub enum TransferSyntax {
    ExplicitVrLittleEndian,
    ImplicitVrLittleEndian,
}

impl From<TransferSyntax> for transcode::UncompressedTransferSyntax {
    fn from(value: TransferSyntax) -> Self {
        match value {
            TransferSyntax::ExplicitVrLittleEndian => {
                transcode::UncompressedTransferSyntax::ExplicitVRLittleEndian
            }
            TransferSyntax::ImplicitVrLittleEndian => {
                transcode::UncompressedTransferSyntax::ImplicitVRLittleEndian
            }
        }
    }
}

pub async fn run() -> anyhow::Result<()> {
    // Parse the raw CLI arguments once and dispatch to a subcommand handler.
    let cli = Cli::parse();

    match cli.command {
        Commands::Info {
            file,
            verbose,
            json,
        } => metadata::print_info(&file, verbose, json)?,
        Commands::Anonymize { input, output } => anonymize::process_file(&input, output)?,
        Commands::ToImage {
            input,
            output,
            format,
            frame,
            window_center,
            window_width,
            normalize,
            disable_modality_lut,
            disable_voi_lut,
            force_8bit,
            force_16bit,
        } => {
            let window = parse_window(window_center, window_width)?;
            let options = image::ImageExportOptions {
                frame,
                window,
                normalize,
                disable_modality_lut,
                disable_voi_lut,
                force_8bit,
                force_16bit,
            };
            image::convert(&input, output, &format, &options)?
        }
        Commands::Validate { file } => validate::check_file(&file)?,
        Commands::Web { host, port } => web::start_server(&host, port).await?,
        Commands::Batch {
            directory,
            operation,
        } => batch::process_directory(&directory, operation)?,
        Commands::Echo { addr } => scu::echo(&addr)?,
        Commands::Push { addr, file } => scu::push(&addr, &file)?,
        Commands::ToJson { file, output } => json::to_json(&file, output.as_deref())?,
        Commands::FromJson { input, output } => json::from_json(&input, &output)?,
        Commands::Transcode {
            input,
            output,
            transfer_syntax,
        } => transcode::transcode(&input, &output, transfer_syntax.into())?,
        Commands::Stats { file } => stats::stats(&file)?,
        Commands::Histogram { file, bins } => {
            if bins == 0 {
                bail!("Number of bins must be greater than zero");
            }
            let histogram = stats::histogram_for_file(&file, bins)?;
            let total: u64 = histogram.bins.iter().sum();
            println!(
                "Histogram for {:?} | bins: {} | total pixels: {}",
                file,
                histogram.bins.len(),
                total
            );
            println!("  Min: {:.2}", histogram.min);
            println!("  Max: {:.2}", histogram.max);
            let range = if histogram.bins.len() > 1 {
                (histogram.max - histogram.min) / histogram.bins.len() as f32
            } else {
                0.0
            };
            let preview = histogram.bins.iter().take(16);
            for (idx, count) in preview.enumerate() {
                let start = histogram.min + (idx as f32) * range;
                let end = start + range;
                println!("  Bin {:03}: [{:.2}, {:.2}] -> {}", idx, start, end, count);
            }
            if histogram.bins.len() > 16 {
                println!("  ... {} more bins omitted", histogram.bins.len() - 16);
            }
        }
        Commands::Dump {
            file,
            max_depth,
            max_value_len,
            json,
        } => {
            if json {
                let output = dump::dump_to_json(&file)?;
                println!("{output}");
            } else {
                dump::dump_file(&file, max_depth, max_value_len)?;
            }
        }
    }

    Ok(())
}

fn parse_window(center: Option<f64>, width: Option<f64>) -> anyhow::Result<Option<WindowLevel>> {
    // Window requires both center and width to make sense; reject mismatched input early.
    match (center, width) {
        (Some(c), Some(w)) => Ok(Some(WindowLevel {
            center: c,
            width: w,
        })),
        (None, None) => Ok(None),
        _ => Err(anyhow!(
            "Provide both --window-center and --window-width, or neither"
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_window_accepts_complete_pair() {
        let wl = parse_window(Some(10.0), Some(20.0))
            .expect("window")
            .expect("present");
        assert_eq!(wl.center, 10.0);
        assert_eq!(wl.width, 20.0);
    }

    #[test]
    fn parse_window_rejects_partial_values() {
        let err = parse_window(Some(10.0), None).unwrap_err();
        assert!(err.to_string().contains("window-center"));
    }

    #[test]
    fn parse_window_none_returns_none() {
        assert!(parse_window(None, None).unwrap().is_none());
    }
}
