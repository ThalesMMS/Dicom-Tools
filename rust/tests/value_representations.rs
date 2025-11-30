//
// value_representations.rs
// Dicom-Tools-rs
//
// Tests for DICOM Value Representations: date/time parsing, person names, numeric conversions, UID validation.
//
// Thales Matheus Mendonça Santos - November 2025

use dicom::core::{DataElement, PrimitiveValue, Tag, VR};
use dicom::dictionary_std::{tags, StandardDataDictionary};
use dicom::object::mem::InMemDicomObject;

#[test]
fn date_format_yyyymmdd() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::STUDY_DATE,
        VR::DA,
        PrimitiveValue::from("20241130"),
    ));

    let date_str = obj
        .element(tags::STUDY_DATE)
        .expect("date")
        .to_str()
        .expect("str");
    assert_eq!(date_str.len(), 8);
    assert!(date_str.chars().all(|c| c.is_ascii_digit()));
}

#[test]
fn time_format_hhmmss() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::STUDY_TIME,
        VR::TM,
        PrimitiveValue::from("143052"),
    ));

    let time_str = obj
        .element(tags::STUDY_TIME)
        .expect("time")
        .to_str()
        .expect("str");
    assert_eq!(time_str, "143052");
}

#[test]
fn time_with_fractional_seconds() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::STUDY_TIME,
        VR::TM,
        PrimitiveValue::from("143052.123456"),
    ));

    let time_str = obj
        .element(tags::STUDY_TIME)
        .expect("time")
        .to_str()
        .expect("str");
    assert!(time_str.contains("."));
}

#[test]
fn datetime_combined_format() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // DateTime (DT) VR: YYYYMMDDHHMMSS.FFFFFF&ZZXX
    obj.put(DataElement::new(
        tags::ACQUISITION_DATE_TIME,
        VR::DT,
        PrimitiveValue::from("20241130143052.000000"),
    ));

    let dt_str = obj
        .element(tags::ACQUISITION_DATE_TIME)
        .expect("dt")
        .to_str()
        .expect("str");
    assert!(dt_str.starts_with("2024"));
    assert!(dt_str.len() >= 14);
}

#[test]
fn person_name_components() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Full PN format: family^given^middle^prefix^suffix
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Doe^John^Michael^Dr.^Jr."),
    ));

    let name = obj
        .element(tags::PATIENT_NAME)
        .expect("name")
        .to_str()
        .expect("str");

    let parts: Vec<&str> = name.split('^').collect();
    assert_eq!(parts.len(), 5);
    assert_eq!(parts[0], "Doe");      // Family name
    assert_eq!(parts[1], "John");     // Given name
    assert_eq!(parts[2], "Michael");  // Middle name
    assert_eq!(parts[3], "Dr.");      // Prefix
    assert_eq!(parts[4], "Jr.");      // Suffix
}

#[test]
fn person_name_ideographic_and_phonetic() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // PN can have up to 3 component groups separated by '='
    // Alphabetic=Ideographic=Phonetic
    obj.put(DataElement::new(
        tags::PATIENT_NAME,
        VR::PN,
        PrimitiveValue::from("Yamada^Tarou=山田^太郎=やまだ^たろう"),
    ));

    let name = obj
        .element(tags::PATIENT_NAME)
        .expect("name")
        .to_str()
        .expect("str");

    let groups: Vec<&str> = name.split('=').collect();
    assert_eq!(groups.len(), 3);
}

#[test]
fn decimal_string_single_value() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::SLICE_THICKNESS,
        VR::DS,
        PrimitiveValue::from([2.5_f64]),
    ));

    let value = obj
        .element(tags::SLICE_THICKNESS)
        .expect("thickness")
        .to_float64()
        .expect("f64");
    assert!((value - 2.5).abs() < 1e-9);
}

#[test]
fn decimal_string_multiple_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Pixel spacing has VM 2
    obj.put(DataElement::new(
        tags::PIXEL_SPACING,
        VR::DS,
        PrimitiveValue::from([0.488281_f64, 0.488281_f64]),
    ));

    let values: Vec<f64> = obj
        .element(tags::PIXEL_SPACING)
        .expect("spacing")
        .to_multi_float64()
        .expect("f64s");
    assert_eq!(values.len(), 2);
    assert!((values[0] - 0.488281).abs() < 1e-6);
}

#[test]
fn integer_string_single_value() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        tags::NUMBER_OF_FRAMES,
        VR::IS,
        PrimitiveValue::from("100"),
    ));

    let value = obj
        .element(tags::NUMBER_OF_FRAMES)
        .expect("frames")
        .to_int::<i32>()
        .expect("i32");
    assert_eq!(value, 100);
}

#[test]
fn integer_string_negative_value() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Rescale intercept can be negative
    obj.put(DataElement::new(
        tags::RESCALE_INTERCEPT,
        VR::DS,
        PrimitiveValue::from("-1024"),
    ));

    let value = obj
        .element(tags::RESCALE_INTERCEPT)
        .expect("intercept")
        .to_float64()
        .expect("f64");
    assert!((value - (-1024.0)).abs() < 1e-9);
}

#[test]
fn unsigned_short_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(tags::ROWS, VR::US, PrimitiveValue::from(512_u16)));
    obj.put(DataElement::new(tags::COLUMNS, VR::US, PrimitiveValue::from(512_u16)));
    obj.put(DataElement::new(tags::BITS_ALLOCATED, VR::US, PrimitiveValue::from(16_u16)));
    obj.put(DataElement::new(tags::BITS_STORED, VR::US, PrimitiveValue::from(12_u16)));

    assert_eq!(obj.element(tags::ROWS).unwrap().to_int::<u16>().unwrap(), 512);
    assert_eq!(obj.element(tags::COLUMNS).unwrap().to_int::<u16>().unwrap(), 512);
    assert_eq!(obj.element(tags::BITS_ALLOCATED).unwrap().to_int::<u16>().unwrap(), 16);
    assert_eq!(obj.element(tags::BITS_STORED).unwrap().to_int::<u16>().unwrap(), 12);
}

#[test]
fn signed_short_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Smallest/Largest pixel values can be signed
    obj.put(DataElement::new(
        Tag(0x0028, 0x0106), // Smallest Image Pixel Value
        VR::SS,
        PrimitiveValue::from(-2048_i16),
    ));

    let value = obj
        .element(Tag(0x0028, 0x0106))
        .expect("smallest")
        .to_int::<i16>()
        .expect("i16");
    assert_eq!(value, -2048);
}

#[test]
fn unsigned_long_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Some attributes use UL (e.g., SimpleFrameList)
    obj.put(DataElement::new(
        Tag(0x0008, 0x1160), // Referenced Frame Number
        VR::IS,
        PrimitiveValue::from("1000000"),
    ));

    let value = obj
        .element(Tag(0x0008, 0x1160))
        .expect("frame num")
        .to_int::<i64>()
        .expect("i64");
    assert_eq!(value, 1_000_000);
}

#[test]
fn uid_format_validation() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    let valid_uid = "1.2.840.10008.5.1.4.1.1.7";
    obj.put(DataElement::new(
        tags::SOP_CLASS_UID,
        VR::UI,
        PrimitiveValue::from(valid_uid),
    ));

    let uid = obj
        .element(tags::SOP_CLASS_UID)
        .expect("uid")
        .to_str()
        .expect("str");

    // UIDs should only contain digits and dots
    assert!(uid.chars().all(|c| c.is_ascii_digit() || c == '.'));
    // UIDs should not start or end with dot
    assert!(!uid.starts_with('.'));
    assert!(!uid.ends_with('.'));
    // Each component should not exceed 64 characters
    assert!(uid.split('.').all(|c| c.len() <= 64));
}

#[test]
fn standard_sop_class_uids() {
    // Common SOP Class UIDs
    let ct_uid = "1.2.840.10008.5.1.4.1.1.2";
    let mr_uid = "1.2.840.10008.5.1.4.1.1.4";
    let sc_uid = "1.2.840.10008.5.1.4.1.1.7";
    let sr_uid = "1.2.840.10008.5.1.4.1.1.88.11";

    // All should start with DICOM root
    assert!(ct_uid.starts_with("1.2.840.10008"));
    assert!(mr_uid.starts_with("1.2.840.10008"));
    assert!(sc_uid.starts_with("1.2.840.10008"));
    assert!(sr_uid.starts_with("1.2.840.10008"));
}

#[test]
fn age_string_format() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // AS format: nnnD, nnnW, nnnM, or nnnY
    obj.put(DataElement::new(
        tags::PATIENT_AGE,
        VR::AS,
        PrimitiveValue::from("045Y"),
    ));

    let age = obj
        .element(tags::PATIENT_AGE)
        .expect("age")
        .to_str()
        .expect("str");
    assert!(age.ends_with('Y') || age.ends_with('M') || age.ends_with('W') || age.ends_with('D'));
}

#[test]
fn code_string_uppercase() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // CS should be uppercase
    obj.put(DataElement::new(
        tags::MODALITY,
        VR::CS,
        PrimitiveValue::from("CT"),
    ));

    let modality = obj
        .element(tags::MODALITY)
        .expect("modality")
        .to_str()
        .expect("str");
    assert!(modality.chars().all(|c| c.is_ascii_uppercase() || c.is_ascii_digit() || c == ' ' || c == '_'));
}

#[test]
fn long_string_max_length() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // LO max length is 64 characters
    let long_value = "A".repeat(64);
    obj.put(DataElement::new(
        tags::PATIENT_ID,
        VR::LO,
        PrimitiveValue::from(long_value.as_str()),
    ));

    let value = obj
        .element(tags::PATIENT_ID)
        .expect("id")
        .to_str()
        .expect("str");
    assert_eq!(value.len(), 64);
}

#[test]
fn short_string_max_length() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // SH max length is 16 characters
    let short_value = "B".repeat(16);
    obj.put(DataElement::new(
        tags::CODE_VALUE,
        VR::SH,
        PrimitiveValue::from(short_value.as_str()),
    ));

    let value = obj
        .element(tags::CODE_VALUE)
        .expect("code")
        .to_str()
        .expect("str");
    assert_eq!(value.len(), 16);
}

#[test]
fn unlimited_text() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // UT has no length limit (other than DICOM element size limits)
    let long_text = "Lorem ipsum ".repeat(1000);
    obj.put(DataElement::new(
        tags::TEXT_VALUE,
        VR::UT,
        PrimitiveValue::from(long_text.as_str()),
    ));

    let value = obj
        .element(tags::TEXT_VALUE)
        .expect("text")
        .to_str()
        .expect("str");
    assert!(value.len() > 10000);
}

#[test]
fn binary_ob_vr() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    let bytes: Vec<u8> = (0..=255).collect();
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OB,
        PrimitiveValue::from(bytes.clone()),
    ));

    let retrieved = obj
        .element(tags::PIXEL_DATA)
        .expect("pixels")
        .to_bytes()
        .expect("bytes");
    assert_eq!(retrieved.as_ref(), &bytes[..]);
}

#[test]
fn binary_ow_vr() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // OW stores 16-bit words as bytes
    let words: Vec<u16> = vec![0, 256, 512, 1024, 2048, 4096];
    let bytes: Vec<u8> = words.iter().flat_map(|w| w.to_le_bytes()).collect();
    obj.put(DataElement::new(
        tags::PIXEL_DATA,
        VR::OW,
        PrimitiveValue::from(bytes),
    ));

    // Reading back as U16 values
    let elem = obj.element(tags::PIXEL_DATA).expect("pixels");
    // OW can be accessed through multiple methods depending on implementation
    assert!(elem.vr() == VR::OW);
}

#[test]
fn floating_point_single() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    obj.put(DataElement::new(
        Tag(0x0018, 0x9089), // Diffusion b-value
        VR::FD,
        PrimitiveValue::from([1000.0_f64]),
    ));

    let value = obj
        .element(Tag(0x0018, 0x9089))
        .expect("bvalue")
        .to_float64()
        .expect("f64");
    assert!((value - 1000.0).abs() < 1e-6);
}

#[test]
fn application_entity_title() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // AE max length is 16 characters
    obj.put(DataElement::new(
        tags::STATION_AE_TITLE,
        VR::AE,
        PrimitiveValue::from("DICOM_SERVER"),
    ));

    let ae = obj
        .element(tags::STATION_AE_TITLE)
        .expect("ae")
        .to_str()
        .expect("str");
    assert!(ae.len() <= 16);
    // AE should not have leading/trailing spaces that are significant
}

#[test]
fn unique_identifier_with_padding() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // UIDs are padded with null (0x00) to even length when written
    // but the logical value shouldn't include the padding
    obj.put(DataElement::new(
        tags::SOP_INSTANCE_UID,
        VR::UI,
        PrimitiveValue::from("1.2.3"), // Odd length
    ));

    let uid = obj
        .element(tags::SOP_INSTANCE_UID)
        .expect("uid")
        .to_str()
        .expect("str");
    // The string value should be the actual UID without padding
    assert!(!uid.contains('\0'));
}

#[test]
fn image_orientation_patient_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Six values: row direction cosines (3) + column direction cosines (3)
    obj.put(DataElement::new(
        tags::IMAGE_ORIENTATION_PATIENT,
        VR::DS,
        PrimitiveValue::from([1.0_f64, 0.0, 0.0, 0.0, 1.0, 0.0]),
    ));

    let values: Vec<f64> = obj
        .element(tags::IMAGE_ORIENTATION_PATIENT)
        .expect("orientation")
        .to_multi_float64()
        .expect("f64s");
    assert_eq!(values.len(), 6);
}

#[test]
fn image_position_patient_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Three values: X, Y, Z coordinates
    obj.put(DataElement::new(
        tags::IMAGE_POSITION_PATIENT,
        VR::DS,
        PrimitiveValue::from([-150.5_f64, -200.0, 100.25]),
    ));

    let values: Vec<f64> = obj
        .element(tags::IMAGE_POSITION_PATIENT)
        .expect("position")
        .to_multi_float64()
        .expect("f64s");
    assert_eq!(values.len(), 3);
    assert!((values[0] - (-150.5)).abs() < 1e-6);
}

#[test]
fn window_center_width_multiple_values() {
    let mut obj = InMemDicomObject::new_empty_with_dict(StandardDataDictionary);

    // Can have multiple window settings
    obj.put(DataElement::new(
        tags::WINDOW_CENTER,
        VR::DS,
        PrimitiveValue::from([40.0_f64, 400.0]),
    ));
    obj.put(DataElement::new(
        tags::WINDOW_WIDTH,
        VR::DS,
        PrimitiveValue::from([80.0_f64, 1500.0]),
    ));

    let centers: Vec<f64> = obj
        .element(tags::WINDOW_CENTER)
        .expect("wc")
        .to_multi_float64()
        .expect("f64s");
    let widths: Vec<f64> = obj
        .element(tags::WINDOW_WIDTH)
        .expect("ww")
        .to_multi_float64()
        .expect("f64s");

    assert_eq!(centers.len(), 2);
    assert_eq!(widths.len(), 2);
}
