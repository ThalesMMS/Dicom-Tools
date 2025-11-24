//
// scu.rs
// Dicom-Tools-rs
//
// Implements minimal C-ECHO and C-STORE service class user operations for testing network connectivity.
//
// Thales Matheus Mendonça Santos - November 2025

use anyhow::{Context, Result};
use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::object::{open_file, InMemDicomObject};
use dicom_ul::association::client::ClientAssociationOptions;
use dicom_ul::pdu::{PDataValue, PDataValueType, Pdu, PresentationContextResultReason};
use std::path::Path;

// Import Registry
use dicom::transfer_syntax::TransferSyntaxRegistry;
// Import Index trait to enable .get().
// Using generic encoding path which usually works for dicom 0.7
use dicom::encoding::TransferSyntaxIndex;

/// Perform a DICOM C-ECHO request against the given AE.
pub fn echo(addr: &str) -> Result<()> {
    println!("Sending C-ECHO to {}", addr);

    let abstract_syntax = "1.2.840.10008.1.1";

    let mut association = ClientAssociationOptions::new()
        .with_abstract_syntax(abstract_syntax)
        .establish(addr)
        .context("Failed to establish association")?;

    let pc_id = association
        .presentation_contexts()
        .iter()
        .find(|pc| pc.reason == PresentationContextResultReason::Acceptance)
        .map(|pc| pc.id)
        .context("No accepted presentation context for Verification")?;

    // Construct C-ECHO-RQ
    // Command set is a tiny DICOM dataset encoded with the negotiated transfer syntax.
    let mut cmd = InMemDicomObject::new_empty();
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0002),
        VR::UI,
        PrimitiveValue::from(abstract_syntax),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0100),
        VR::US,
        PrimitiveValue::from(0x0030_u16),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0110),
        VR::US,
        PrimitiveValue::from(1_u16),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0800),
        VR::US,
        PrimitiveValue::from(0x0101_u16),
    ));

    // Get IVRLE Transfer Syntax
    let ts = TransferSyntaxRegistry
        .get("1.2.840.10008.1.2")
        .context("Implicit VR Little Endian transfer syntax not found")?;

    let mut command_bytes = Vec::new();
    cmd.write_dataset_with_ts(&mut command_bytes, ts)
        .context("Failed to encode command set")?;

    let pdu = Pdu::PData {
        data: vec![PDataValue {
            presentation_context_id: pc_id,
            value_type: PDataValueType::Command,
            is_last: true,
            data: command_bytes,
        }],
    };

    association.send(&pdu).context("Failed to send C-ECHO-RQ")?;

    let msg = association
        .receive()
        .context("Failed to receive C-ECHO-RSP")?;
    println!("Received response: {:?}", msg);

    let _ = association.release();
    Ok(())
}

/// Perform a minimal C-STORE to push a single object to a remote AE.
pub fn push(addr: &str, file: &Path) -> Result<()> {
    println!("Sending C-STORE for {:?} to {}", file, addr);

    let obj = open_file(file).context("Failed to open DICOM file")?;

    let sop_class = obj
        .element(Tag(0x0008, 0x0016))
        .context("Missing SOP Class UID")?
        .to_str()?;
    let sop_instance = obj
        .element(Tag(0x0008, 0x0018))
        .context("Missing SOP Instance UID")?
        .to_str()?;

    let mut association = ClientAssociationOptions::new()
        .with_abstract_syntax(&*sop_class)
        .establish(addr)
        .context("Failed to establish association")?;

    let pc_id = association
        .presentation_contexts()
        .iter()
        .find(|pc| pc.reason == PresentationContextResultReason::Acceptance)
        .map(|pc| pc.id)
        .context("No accepted presentation context for file SOP Class")?;

    // Construct C-STORE-RQ
    // Only the required command elements are included here; dataset follows later as PDV.
    let mut cmd = InMemDicomObject::new_empty();
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0002),
        VR::UI,
        PrimitiveValue::from(sop_class.to_string()),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0100),
        VR::US,
        PrimitiveValue::from(0x0001_u16),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0110),
        VR::US,
        PrimitiveValue::from(2_u16),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 0x0800),
        VR::US,
        PrimitiveValue::from(0x0000_u16),
    ));
    cmd.put(DataElement::new(
        Tag(0x0000, 1000),
        VR::UI,
        PrimitiveValue::from(sop_instance.to_string()),
    ));

    // Get IVRLE Transfer Syntax for Command Set
    let ts_ivrle = TransferSyntaxRegistry
        .get("1.2.840.10008.1.2")
        .context("Implicit VR Little Endian transfer syntax not found")?;

    let mut command_bytes = Vec::new();
    // Encode command as a command PDV (even though this code path uses the same TS as dataset).
    cmd.write_dataset_with_ts(&mut command_bytes, ts_ivrle)
        .context("Failed to encode command set")?;

    // Encode File Dataset
    let pc = association
        .presentation_contexts()
        .iter()
        .find(|pc| pc.id == pc_id)
        .unwrap();
    let negotiated_ts_uid = &pc.transfer_syntax;
    let ts_negotiated = TransferSyntaxRegistry
        .get(negotiated_ts_uid)
        .context(format!(
            "Negotiated transfer syntax {} not found",
            negotiated_ts_uid
        ))?;

    let mut data_bytes = Vec::new();
    obj.write_dataset_with_ts(&mut data_bytes, ts_negotiated)
        .context("Failed to encode data set")?;

    // Send Command
    association.send(&Pdu::PData {
        data: vec![PDataValue {
            presentation_context_id: pc_id,
            value_type: PDataValueType::Command,
            is_last: true,
            data: command_bytes,
        }],
    })?;

    // Send Data
    association.send(&Pdu::PData {
        data: vec![PDataValue {
            presentation_context_id: pc_id,
            value_type: PDataValueType::Data,
            is_last: true,
            data: data_bytes,
        }],
    })?;

    let msg = association
        .receive()
        .context("Failed to receive C-STORE-RSP")?;
    println!("Received response: {:?}", msg);

    let _ = association.release();
    Ok(())
}
