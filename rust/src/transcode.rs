//
// transcode.rs
// Dicom-Tools-rs
//
// Transcodes DICOM files to uncompressed transfer syntaxes while preserving raw pixel meaning.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::{Context, Result};
use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::object::open_file;
use dicom::pixeldata::PixelDecoder;
use dicom::transfer_syntax::entries::{EXPLICIT_VR_LITTLE_ENDIAN, IMPLICIT_VR_LITTLE_ENDIAN};
use dicom_pixeldata::{ConvertOptions, ModalityLutOption, VoiLutOption};
use std::borrow::Cow;
use std::path::Path;

/// Supported uncompressed transfer syntaxes for transcoding.
#[derive(Debug, Copy, Clone, Eq, PartialEq)]
pub enum UncompressedTransferSyntax {
    ExplicitVRLittleEndian,
    ImplicitVRLittleEndian,
}

impl UncompressedTransferSyntax {
    fn uid(self) -> &'static str {
        match self {
            UncompressedTransferSyntax::ExplicitVRLittleEndian => EXPLICIT_VR_LITTLE_ENDIAN.uid(),
            UncompressedTransferSyntax::ImplicitVRLittleEndian => IMPLICIT_VR_LITTLE_ENDIAN.uid(),
        }
    }
}

/// Transcode a DICOM file to an uncompressed transfer syntax (explicit or implicit VR LE).
pub fn transcode(input: &Path, output: &Path, target_ts: UncompressedTransferSyntax) -> Result<()> {
    let obj = open_file(input).context("Failed to open DICOM file")?;

    // 1. Decode Pixel Data.
    //    We rely on dicom-pixeldata to decompress any encapsulated streams for us.
    let decoded = obj
        .decode_pixel_data()
        .context("Failed to decode pixel data")?;

    // 2. Get raw bytes (native) without applying LUTs.
    //    This avoids altering pixel meaning while changing transfer syntax.
    let convert_options = ConvertOptions::new()
        .with_modality_lut(ModalityLutOption::None)
        .with_voi_lut(VoiLutOption::Identity);
    let bits_allocated = decoded.bits_allocated();
    let pixel_bytes = if bits_allocated > 8 {
        let words = decoded
            .to_vec_with_options::<u16>(&convert_options)
            .context("Failed to convert decoded pixels to vector")?;
        words
            .into_iter()
            .flat_map(|v| v.to_le_bytes())
            .collect::<Vec<u8>>()
    } else {
        decoded
            .to_vec_with_options::<u8>(&convert_options)
            .context("Failed to convert decoded pixels to vector")?
    };

    // Release borrow on obj so we can consume it.
    drop(decoded);

    // 3. Reconstruct object.
    let mut new_obj = obj.into_inner(); // Unwrap the FileDicomObject to get InMemDicomObject

    // Update Pixel Data Element (7FE0,0010) with raw bytes and correct VR.
    let pixel_data_tag = Tag(0x7FE0, 0x0010);

    let vr = if bits_allocated > 8 { VR::OW } else { VR::OB };

    new_obj.put(DataElement::new(
        pixel_data_tag,
        vr,
        PrimitiveValue::from(pixel_bytes),
    ));

    // 4. Save with new Transfer Syntax and regenerated file meta.

    use dicom::object::FileDicomObject;
    use dicom::object::FileMetaTableBuilder;

    let sop_class_uid = new_obj
        .element(Tag(0x0008, 0x0016))
        .ok()
        .and_then(|e| e.to_str().ok())
        .unwrap_or(Cow::Borrowed("1.2.840.10008.5.1.4.1.1.7"));

    let sop_instance_uid = new_obj
        .element(Tag(0x0008, 0x0018))
        .ok()
        .and_then(|e| e.to_str().ok())
        .unwrap_or(Cow::Borrowed("1.2.3.4.5"));

    let file_meta = FileMetaTableBuilder::new()
        .transfer_syntax(target_ts.uid())
        .media_storage_sop_class_uid(sop_class_uid.as_ref())
        .media_storage_sop_instance_uid(sop_instance_uid.as_ref())
        .build()?;

    let mut file_obj = FileDicomObject::new_empty_with_dict_and_meta(
        dicom::dictionary_std::StandardDataDictionary,
        file_meta,
    );

    for elem in new_obj {
        file_obj.put(elem);
    }

    file_obj
        .write_to_file(output)
        .context("Failed to write output file")?;
    println!("Transcoded to {}: {:?}", target_ts.uid(), output);

    Ok(())
}
