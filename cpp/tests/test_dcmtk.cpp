//
// test_dcmtk.cpp
// DicomToolsCpp
//
// Unit tests for DCMTK library features including file parsing, dataset manipulation,
// codec support, network primitives, and DICOM validation.
//
// Thales Matheus Mendonça Santos - November 2025

#include "test_framework.h"

#include <filesystem>
#include <fstream>
#include <cstring>
#include <memory>

#ifdef USE_DCMTK
#include <dcmtk/dcmdata/dctk.h>
#include <dcmtk/dcmdata/dcfilefo.h>
#include <dcmtk/dcmdata/dcuid.h>
#include <dcmtk/dcmdata/dcdict.h>
#include <dcmtk/dcmdata/dcdeftag.h>
#include <dcmtk/dcmdata/dcistrmb.h>
#include <dcmtk/dcmdata/dcostrmb.h>
#include <dcmtk/dcmdata/dcvrda.h>
#include <dcmtk/dcmdata/dcvrtm.h>
#include <dcmtk/dcmdata/dcvrui.h>
#include <dcmtk/dcmdata/dcvrat.h>
#include <dcmtk/dcmimgle/dcmimage.h>
#include <dcmtk/dcmimage/diregist.h>
#include <dcmtk/dcmjpeg/djdecode.h>
#include <dcmtk/dcmjpeg/djencode.h>
#include <dcmtk/dcmdata/libi2d/i2d.h>
#endif

namespace fs = std::filesystem;

// Helper to find a test DICOM file
static std::string FindTestDicom() {
    std::vector<std::string> searchPaths = {
        "../sample_series",
        "../../sample_series",
        "../../../sample_series",
        "sample_series"
    };
    for (const auto& base : searchPaths) {
        fs::path p(base);
        if (fs::exists(p) && fs::is_directory(p)) {
            for (const auto& entry : fs::directory_iterator(p)) {
                if (entry.path().extension() == ".dcm") {
                    return entry.path().string();
                }
            }
        }
    }
    return "";
}

#ifdef USE_DCMTK

// =============================================================================
// DCMTK Basic Functionality Tests
// =============================================================================

TEST_CASE(DCMTK_DataDictionaryLoaded) {
    // Verify the data dictionary is loaded
    const DcmDataDictionary& dict = dcmDataDict.rdlock();
    
    // Look up Patient Name tag
    const DcmDictEntry* entry = dict.findEntry(DCM_PatientName);
    EXPECT_TRUE(entry != nullptr);
    EXPECT_EQ(entry->getVR().getEVR(), EVR_PN);
    
    dcmDataDict.rdunlock();
    return true;
}

TEST_CASE(DCMTK_TagConstruction) {
    DcmTag tag1(DCM_PatientName);
    DcmTag tag2(DCM_SOPInstanceUID);
    DcmTag tag3(DCM_PixelData);
    
    EXPECT_EQ(tag1.getGroup(), 0x0010);
    EXPECT_EQ(tag1.getElement(), 0x0010);
    EXPECT_EQ(tag2.getGroup(), 0x0008);
    EXPECT_EQ(tag2.getElement(), 0x0018);
    EXPECT_EQ(tag3.getGroup(), 0x7FE0);
    EXPECT_EQ(tag3.getElement(), 0x0010);
    return true;
}

TEST_CASE(DCMTK_VRTypes) {
    EXPECT_EQ(DcmVR(EVR_PN).getVRName(), std::string("PN"));
    EXPECT_EQ(DcmVR(EVR_UI).getVRName(), std::string("UI"));
    EXPECT_EQ(DcmVR(EVR_DA).getVRName(), std::string("DA"));
    EXPECT_EQ(DcmVR(EVR_TM).getVRName(), std::string("TM"));
    EXPECT_EQ(DcmVR(EVR_US).getVRName(), std::string("US"));
    EXPECT_EQ(DcmVR(EVR_OW).getVRName(), std::string("OW"));
    return true;
}

TEST_CASE(DCMTK_UIDGeneration) {
    char uid1[100], uid2[100];
    dcmGenerateUniqueIdentifier(uid1, SITE_INSTANCE_UID_ROOT);
    dcmGenerateUniqueIdentifier(uid2, SITE_INSTANCE_UID_ROOT);
    
    EXPECT_TRUE(strlen(uid1) > 0);
    EXPECT_TRUE(strlen(uid2) > 0);
    EXPECT_NE(std::string(uid1), std::string(uid2));
    return true;
}

TEST_CASE(DCMTK_DateTimeFormatting) {
    DcmDate date(DCM_StudyDate);
    OFCondition status = date.putOFStringArray("20231115");
    EXPECT_TRUE(status.good());
    
    OFString value;
    date.getOFStringArray(value);
    EXPECT_EQ(value.c_str(), std::string("20231115"));
    return true;
}

// =============================================================================
// DCMTK Dataset Creation Tests
// =============================================================================

TEST_CASE(DCMTK_CreateEmptyDataset) {
    DcmDataset dataset;
    EXPECT_TRUE(dataset.isEmpty());
    return true;
}

TEST_CASE(DCMTK_AddStringElement) {
    DcmDataset dataset;
    
    OFCondition status = dataset.putAndInsertString(DCM_PatientName, "Test^Patient");
    EXPECT_TRUE(status.good());
    
    OFString value;
    status = dataset.findAndGetOFString(DCM_PatientName, value);
    EXPECT_TRUE(status.good());
    EXPECT_EQ(value.c_str(), std::string("Test^Patient"));
    return true;
}

TEST_CASE(DCMTK_AddMultipleElements) {
    DcmDataset dataset;
    
    dataset.putAndInsertString(DCM_PatientName, "Test^Patient");
    dataset.putAndInsertString(DCM_PatientID, "12345");
    dataset.putAndInsertString(DCM_StudyDate, "20231115");
    dataset.putAndInsertString(DCM_Modality, "CT");
    
    EXPECT_EQ(dataset.card(), 4u);
    return true;
}

TEST_CASE(DCMTK_AddIntegerElement) {
    DcmDataset dataset;
    
    dataset.putAndInsertUint16(DCM_Rows, 512);
    dataset.putAndInsertUint16(DCM_Columns, 512);
    dataset.putAndInsertUint16(DCM_BitsAllocated, 16);
    
    Uint16 rows = 0, cols = 0;
    dataset.findAndGetUint16(DCM_Rows, rows);
    dataset.findAndGetUint16(DCM_Columns, cols);
    
    EXPECT_EQ(rows, 512);
    EXPECT_EQ(cols, 512);
    return true;
}

TEST_CASE(DCMTK_SequenceCreation) {
    DcmDataset dataset;
    DcmItem* item = nullptr;
    
    OFCondition status = dataset.findOrCreateSequenceItem(DCM_ReferencedStudySequence, item, 0);
    EXPECT_TRUE(status.good());
    EXPECT_TRUE(item != nullptr);
    
    if (item) {
        item->putAndInsertString(DCM_ReferencedSOPClassUID, "1.2.3.4.5");
        item->putAndInsertString(DCM_ReferencedSOPInstanceUID, "1.2.3.4.5.6.7");
    }
    return true;
}

// =============================================================================
// DCMTK File I/O Tests
// =============================================================================

TEST_CASE(DCMTK_ReadDicomFile) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) {
        std::cerr << "  [SKIP] No test DICOM file found" << std::endl;
        return true;
    }
    
    DcmFileFormat fileFormat;
    OFCondition status = fileFormat.loadFile(testFile.c_str());
    EXPECT_TRUE(status.good());
    
    DcmDataset* dataset = fileFormat.getDataset();
    EXPECT_TRUE(dataset != nullptr);
    EXPECT_FALSE(dataset->isEmpty());
    return true;
}

TEST_CASE(DCMTK_ExtractPatientInfo) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DcmFileFormat fileFormat;
    OFCondition status = fileFormat.loadFile(testFile.c_str());
    EXPECT_TRUE(status.good());
    
    DcmDataset* dataset = fileFormat.getDataset();
    
    OFString patientName, studyDate, modality;
    dataset->findAndGetOFString(DCM_PatientName, patientName);
    dataset->findAndGetOFString(DCM_StudyDate, studyDate);
    dataset->findAndGetOFString(DCM_Modality, modality);
    
    // Just verify extraction doesn't crash
    return true;
}

TEST_CASE(DCMTK_ReadTransferSyntax) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DcmFileFormat fileFormat;
    OFCondition status = fileFormat.loadFile(testFile.c_str());
    EXPECT_TRUE(status.good());
    
    DcmMetaInfo* metaInfo = fileFormat.getMetaInfo();
    EXPECT_TRUE(metaInfo != nullptr);
    
    OFString ts;
    metaInfo->findAndGetOFString(DCM_TransferSyntaxUID, ts);
    EXPECT_FALSE(ts.empty());
    return true;
}

TEST_CASE(DCMTK_WriteDataset) {
    DcmFileFormat fileFormat;
    DcmDataset* dataset = fileFormat.getDataset();
    
    // Create minimal dataset
    dataset->putAndInsertString(DCM_SOPClassUID, UID_SecondaryCaptureImageStorage);
    char uid[100];
    dcmGenerateUniqueIdentifier(uid, SITE_INSTANCE_UID_ROOT);
    dataset->putAndInsertString(DCM_SOPInstanceUID, uid);
    dataset->putAndInsertString(DCM_PatientName, "Test^Patient");
    dataset->putAndInsertString(DCM_Modality, "OT");
    
    std::string outPath = fs::temp_directory_path().string() + "/test_dcmtk_write.dcm";
    OFCondition status = fileFormat.saveFile(outPath.c_str(), EXS_LittleEndianExplicit);
    EXPECT_TRUE(status.good());
    
    EXPECT_TRUE(fs::exists(outPath));
    fs::remove(outPath);
    return true;
}

TEST_CASE(DCMTK_RoundTripPreservation) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    // Read original
    DcmFileFormat ff1;
    ff1.loadFile(testFile.c_str());
    OFString originalModality;
    ff1.getDataset()->findAndGetOFString(DCM_Modality, originalModality);
    
    // Write to temp
    std::string outPath = fs::temp_directory_path().string() + "/test_dcmtk_roundtrip.dcm";
    ff1.saveFile(outPath.c_str());
    
    // Read back
    DcmFileFormat ff2;
    ff2.loadFile(outPath.c_str());
    OFString readBackModality;
    ff2.getDataset()->findAndGetOFString(DCM_Modality, readBackModality);
    
    EXPECT_EQ(originalModality.c_str(), std::string(readBackModality.c_str()));
    
    fs::remove(outPath);
    return true;
}

// =============================================================================
// DCMTK Image Processing Tests
// =============================================================================

TEST_CASE(DCMTK_DicomImageLoad) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DicomImage image(testFile.c_str());
    
    if (image.getStatus() == EIS_Normal) {
        EXPECT_GT(image.getWidth(), 0u);
        EXPECT_GT(image.getHeight(), 0u);
    }
    return true;
}

TEST_CASE(DCMTK_DicomImageDepth) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DicomImage image(testFile.c_str());
    
    if (image.getStatus() == EIS_Normal) {
        int depth = image.getDepth();
        EXPECT_GT(depth, 0);
        EXPECT_LE(depth, 32);
    }
    return true;
}

TEST_CASE(DCMTK_DicomImageFrameCount) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DicomImage image(testFile.c_str());
    
    if (image.getStatus() == EIS_Normal) {
        unsigned long frames = image.getFrameCount();
        EXPECT_GE(frames, 1u);
    }
    return true;
}

// =============================================================================
// DCMTK Codec Tests
// =============================================================================

TEST_CASE(DCMTK_JPEGCodecRegistration) {
    DJDecoderRegistration::registerCodecs();
    DJEncoderRegistration::registerCodecs();
    
    // Verify registration (no crash)
    DJDecoderRegistration::cleanup();
    DJEncoderRegistration::cleanup();
    return true;
}

TEST_CASE(DCMTK_TransferSyntaxCheck) {
    // Verify known transfer syntaxes
    EXPECT_TRUE(DcmXfer(EXS_LittleEndianExplicit).isValid());
    EXPECT_TRUE(DcmXfer(EXS_BigEndianExplicit).isValid());
    EXPECT_TRUE(DcmXfer(EXS_LittleEndianImplicit).isValid());
    EXPECT_TRUE(DcmXfer(EXS_JPEGProcess1).isValid());
    EXPECT_TRUE(DcmXfer(EXS_JPEGProcess14SV1).isValid());
    EXPECT_TRUE(DcmXfer(EXS_RLELossless).isValid());
    return true;
}

TEST_CASE(DCMTK_TranscodeToExplicitVR) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DcmFileFormat ff;
    OFCondition status = ff.loadFile(testFile.c_str());
    if (!status.good()) return true;
    
    // Try to change representation
    DcmDataset* ds = ff.getDataset();
    status = ds->chooseRepresentation(EXS_LittleEndianExplicit, nullptr);
    // Success depends on original format
    return true;
}

// =============================================================================
// DCMTK Validation Tests
// =============================================================================

TEST_CASE(DCMTK_ValidateSOPClassUID) {
    DcmDataset dataset;
    dataset.putAndInsertString(DCM_SOPClassUID, UID_CTImageStorage);
    
    OFString sopClass;
    dataset.findAndGetOFString(DCM_SOPClassUID, sopClass);
    
    EXPECT_EQ(sopClass.c_str(), std::string(UID_CTImageStorage));
    return true;
}

TEST_CASE(DCMTK_TagPresenceCheck) {
    std::string testFile = FindTestDicom();
    if (testFile.empty()) return true;
    
    DcmFileFormat ff;
    ff.loadFile(testFile.c_str());
    DcmDataset* ds = ff.getDataset();
    
    // These tags should exist in most DICOM files
    EXPECT_TRUE(ds->tagExistsWithValue(DCM_SOPClassUID));
    EXPECT_TRUE(ds->tagExistsWithValue(DCM_SOPInstanceUID));
    return true;
}

// =============================================================================
// DCMTK Memory Stream Tests
// =============================================================================

TEST_CASE(DCMTK_MemoryBuffer) {
    DcmFileFormat ff;
    DcmDataset* ds = ff.getDataset();
    
    ds->putAndInsertString(DCM_SOPClassUID, UID_SecondaryCaptureImageStorage);
    char uid[100];
    dcmGenerateUniqueIdentifier(uid);
    ds->putAndInsertString(DCM_SOPInstanceUID, uid);
    ds->putAndInsertString(DCM_PatientName, "Memory^Test");
    
    // Write to buffer
    Uint32 bufSize = 0;
    ff.calcElementLength(EXS_LittleEndianExplicit, EET_ExplicitLength);
    
    // Create output stream to buffer
    DcmOutputBufferStream outStream(nullptr, 0);
    ff.write(outStream, EXS_LittleEndianExplicit, EET_ExplicitLength);
    
    return true;
}

#else // !USE_DCMTK

TEST_CASE(DCMTK_NotAvailable) {
    std::cerr << "  [INFO] DCMTK not available - skipping DCMTK tests" << std::endl;
    return true;
}

#endif // USE_DCMTK

// =============================================================================
// Main
// =============================================================================

int main(int argc, char* argv[]) {
    return RUN_TESTS("DCMTK Feature Tests");
}
