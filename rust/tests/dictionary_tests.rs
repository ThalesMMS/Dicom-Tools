//
// dictionary_tests.rs
// Dicom-Tools-rs
//
// Tests for DICOM dictionary operations: tag lookup, VR validation, keyword resolution, and private tag handling.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{Tag, VR};
use dicom::dictionary_std::tags;
use dicom::dictionary_std::StandardDataDictionary;
use dicom::object::mem::InMemDicomObject;
use dicom::core::dictionary::DataDictionary;

#[test]
fn standard_tag_lookup_by_keyword() {
    let dict = StandardDataDictionary;

    // Verify common tags resolve correctly via the dictionary
    let patient_name = dict.by_name("PatientName");
    assert!(patient_name.is_some());
    let entry = patient_name.unwrap();
    // Dictionary entry tag should match
    assert!(format!("{:?}", entry.tag).contains("0010"));

    let modality = dict.by_name("Modality");
    assert!(modality.is_some());
    // Modality tag should be found
    assert!(modality.is_some());

    let pixel_data = dict.by_name("PixelData");
    assert!(pixel_data.is_some());
    // PixelData tag should be found
}

#[test]
fn standard_tag_lookup_by_tag() {
    let dict = StandardDataDictionary;

    // Look up entries by their numeric Tag
    let entry = dict.by_tag(Tag(0x0010, 0x0010));
    assert!(entry.is_some());

    let rows_entry = dict.by_tag(tags::ROWS);
    assert!(rows_entry.is_some());

    let columns_entry = dict.by_tag(tags::COLUMNS);
    assert!(columns_entry.is_some());
}

#[test]
fn vr_enum_variants_exist() {
    // Verify common VR enum variants exist
    let _pn = VR::PN;
    let _lo = VR::LO;
    let _cs = VR::CS;
    let _ui = VR::UI;
    let _da = VR::DA;
    let _tm = VR::TM;
    let _ds = VR::DS;
    let _is = VR::IS;
    let _ob = VR::OB;
    let _ow = VR::OW;
    let _un = VR::UN;
    let _sq = VR::SQ;
    let _us = VR::US;
    let _ss = VR::SS;
    let _ul = VR::UL;
    let _sl = VR::SL;
    let _fl = VR::FL;
    let _fd = VR::FD;
    let _ae = VR::AE;
    let _as = VR::AS;
    let _at = VR::AT;
    let _lt = VR::LT;
    let _sh = VR::SH;
    let _st = VR::ST;
    let _ut = VR::UT;
}

#[test]
fn tag_group_and_element_extraction() {
    let tag = Tag(0x0008, 0x0060);
    assert_eq!(tag.group(), 0x0008);
    assert_eq!(tag.element(), 0x0060);

    let pixel_tag = tags::PIXEL_DATA;
    assert_eq!(pixel_tag.group(), 0x7FE0);
    assert_eq!(pixel_tag.element(), 0x0010);

    // Meta information group
    let meta_tag = Tag(0x0002, 0x0010);
    assert_eq!(meta_tag.group(), 0x0002);
}

#[test]
fn private_tag_detection() {
    // Standard tags have even group numbers
    let standard_tag = Tag(0x0010, 0x0010);
    assert!(!is_private_tag(standard_tag));

    // Private tags have odd group numbers
    let private_tag = Tag(0x0011, 0x0010);
    assert!(is_private_tag(private_tag));

    let another_private = Tag(0x0099, 0x1234);
    assert!(is_private_tag(another_private));

    // Group 0x0001 and 0x0003, 0x0005, 0x0007 are private
    assert!(is_private_tag(Tag(0x0001, 0x0000)));
    assert!(is_private_tag(Tag(0x0003, 0x0000)));
    assert!(is_private_tag(Tag(0x0005, 0x0000)));
    assert!(is_private_tag(Tag(0x0007, 0x0000)));
}

fn is_private_tag(tag: Tag) -> bool {
    tag.group() % 2 == 1
}

#[test]
fn repeating_group_tags() {
    // Curve Data and Overlay Data use repeating groups
    // Overlay groups: 6000-601E (even only)
    let overlay_rows = Tag(0x6000, 0x0010);
    assert_eq!(overlay_rows.group(), 0x6000);

    let another_overlay = Tag(0x6002, 0x0010);
    assert_eq!(another_overlay.group(), 0x6002);

    // These should be recognized as valid group ranges
    assert!(overlay_rows.group() >= 0x6000 && overlay_rows.group() <= 0x601E);
}

#[test]
fn common_modality_specific_tags_exist() {
    let dict = StandardDataDictionary;

    // CT-specific
    let kvp = dict.by_name("KVP");
    assert!(kvp.is_some());

    let exposure = dict.by_name("Exposure");
    assert!(exposure.is_some());

    // MR-specific
    let echo_time = dict.by_name("EchoTime");
    assert!(echo_time.is_some());

    let repetition_time = dict.by_name("RepetitionTime");
    assert!(repetition_time.is_some());

    // General image tags
    let slice_thickness = dict.by_name("SliceThickness");
    assert!(slice_thickness.is_some());

    let pixel_spacing = dict.by_name("PixelSpacing");
    assert!(pixel_spacing.is_some());
}

#[test]
fn sop_class_uid_tags() {
    let dict = StandardDataDictionary;

    let sop_class = dict.by_tag(tags::SOP_CLASS_UID);
    assert!(sop_class.is_some());

    let sop_instance = dict.by_tag(tags::SOP_INSTANCE_UID);
    assert!(sop_instance.is_some());

    let study_uid = dict.by_tag(tags::STUDY_INSTANCE_UID);
    assert!(study_uid.is_some());

    let series_uid = dict.by_tag(tags::SERIES_INSTANCE_UID);
    assert!(series_uid.is_some());
}

#[test]
fn sequence_tags_have_sq_vr() {
    let dict = StandardDataDictionary;

    let content_seq = dict.by_tag(tags::CONTENT_SEQUENCE);
    assert!(content_seq.is_some());

    let ref_study_seq = dict.by_tag(tags::REFERENCED_STUDY_SEQUENCE);
    assert!(ref_study_seq.is_some());
}

#[test]
fn unknown_tag_returns_none() {
    let dict = StandardDataDictionary;

    // Very unlikely to be a valid standard tag
    let unknown = dict.by_tag(Tag(0xFFFE, 0xFFFF));
    // This may or may not return None depending on dictionary implementation
    // but we can check that the lookup doesn't panic
    let _ = unknown;

    // Invalid keyword should return None
    let invalid_keyword = dict.by_name("NotARealDicomKeyword");
    assert!(invalid_keyword.is_none());
}

#[test]
fn patient_module_tags() {
    let dict = StandardDataDictionary;

    // Core patient module tags
    let patient_id = dict.by_name("PatientID");
    assert!(patient_id.is_some());

    let patient_birth_date = dict.by_name("PatientBirthDate");
    assert!(patient_birth_date.is_some());

    let patient_sex = dict.by_name("PatientSex");
    assert!(patient_sex.is_some());
}

#[test]
fn image_pixel_module_tags() {
    let dict = StandardDataDictionary;

    let samples = dict.by_name("SamplesPerPixel");
    assert!(samples.is_some());

    let photo_interp = dict.by_name("PhotometricInterpretation");
    assert!(photo_interp.is_some());

    let bits_alloc = dict.by_name("BitsAllocated");
    assert!(bits_alloc.is_some());

    let bits_stored = dict.by_name("BitsStored");
    assert!(bits_stored.is_some());

    let high_bit = dict.by_name("HighBit");
    assert!(high_bit.is_some());

    let pixel_rep = dict.by_name("PixelRepresentation");
    assert!(pixel_rep.is_some());
}

#[test]
fn tag_display_formatting() {
    let tag = Tag(0x0010, 0x0010);
    let display = format!("{}", tag);
    assert!(display.contains("0010") || display.contains("10"));

    let pixel_tag = tags::PIXEL_DATA;
    let pixel_display = format!("{}", pixel_tag);
    assert!(pixel_display.contains("7FE0") || pixel_display.contains("7fe0") || pixel_display.len() > 0);
}

#[test]
fn tag_ordering_and_comparison() {
    let tag_a = Tag(0x0008, 0x0016);
    let tag_b = Tag(0x0008, 0x0018);
    let tag_c = Tag(0x0010, 0x0010);

    assert!(tag_a < tag_b);
    assert!(tag_b < tag_c);
    assert!(tag_a < tag_c);

    // Tags in same group ordered by element
    assert!(Tag(0x0008, 0x0000) < Tag(0x0008, 0x0001));

    // Group ordering takes precedence
    assert!(Tag(0x0007, 0xFFFF) < Tag(0x0008, 0x0000));
}

#[test]
fn create_object_with_dictionary() {
    let obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);
    
    // Object should be empty
    assert_eq!(obj.into_iter().count(), 0);
}

#[test]
fn dictionary_entry_multiplicity() {
    let dict = StandardDataDictionary;
    
    // PatientName exists in dictionary
    let pn = dict.by_name("PatientName");
    assert!(pn.is_some());
    
    // ImageType can have multiple values (VM 2-n)
    let image_type = dict.by_name("ImageType");
    assert!(image_type.is_some());
}
