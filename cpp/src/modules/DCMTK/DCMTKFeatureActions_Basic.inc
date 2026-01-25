void DCMTKTests::TestTagModification(const std::string& filename, const std::string& outputDir) {
    // Demonstrates basic tag read/write and saving a sanitized copy
    std::cout << "--- [DCMTK] Tag Modification ---" << std::endl;
    DcmFileFormat fileformat;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (status.good()) {
        OFString patientName;
        if (fileformat.getDataset()->findAndGetOFString(DCM_PatientName, patientName).good()) {
            std::cout << "Original Patient Name: " << patientName << std::endl;
        }

        std::cout << "Modifying PatientID to 'ANONYMIZED'..." << std::endl;
        fileformat.getDataset()->putAndInsertString(DCM_PatientID, "ANONYMIZED");

        std::string outFile = JoinPath(outputDir, "dcmtk_modified.dcm");
        status = fileformat.saveFile(outFile.c_str());
        if (status.good()) {
            std::cout << "Saved modified file to '" << outFile << "'" << std::endl;
        } else {
            std::cerr << "Error saving file: " << status.text() << std::endl;
        }
    } else {
        std::cerr << "Error reading file: " << status.text() << std::endl;
    }
}


void DCMTKTests::TestPixelDataExtraction(const std::string& filename, const std::string& outputDir) {
    // Extracts pixel data and writes a PPM/PGM preview using DCMTK image tools
    std::cout << "--- [DCMTK] Pixel Data Extraction ---" << std::endl;
    
    DicomImage* image = new DicomImage(filename.c_str());
    if (image != NULL) {
        if (image->getStatus() == EIS_Normal) {
            std::cout << "Image loaded. Size: " << image->getWidth() << "x" << image->getHeight() << std::endl;
            
            if (image->isMonochrome()) {
                image->setMinMaxWindow();
            }

            std::string outFilename = JoinPath(outputDir, "dcmtk_pixel_output.ppm");
            if (image->writePPM(outFilename.c_str())) {
                 std::cout << "Saved PPM/PGM image to: " << outFilename << std::endl;
            } else {
                std::cerr << "Failed to write PPM image." << std::endl;
            }
        } else {
            std::cerr << "Error: cannot load DICOM image (" << DicomImage::getString(image->getStatus()) << ")" << std::endl;
        }
        delete image;
    } else {
        std::cerr << "Error: Memory allocation failed for DicomImage." << std::endl;
    }
}


void DCMTKTests::TestDICOMDIRGeneration(const std::string& directory, const std::string& outputDir) {
    // Copies an input series to a fake media root and builds a DICOMDIR index
    std::cout << "--- [DCMTK] DICOMDIR Generation ---" << std::endl;
    fs::path sourceRoot = fs::is_directory(directory) ? fs::path(directory) : fs::path(directory).parent_path();
    fs::path mediaRoot = fs::path(outputDir) / "dicomdir_media";
    if (sourceRoot.empty() || !fs::exists(sourceRoot)) {
        std::cerr << "Input path is invalid for DICOMDIR generation." << std::endl;
        return;
    }

    std::vector<fs::path> dicomFiles;
    for (const auto& entry : fs::recursive_directory_iterator(sourceRoot)) {
        if (entry.is_regular_file() && entry.path().extension() == ".dcm") {
            dicomFiles.push_back(entry.path());
        }
    }

    if (dicomFiles.empty()) {
        std::cerr << "No DICOM files found under " << sourceRoot << " to include in DICOMDIR." << std::endl;
        return;
    }

    // Mirror the source tree into a temporary media folder to keep relative paths intact
    std::error_code ec;
    fs::create_directories(mediaRoot, ec);
    if (ec) {
        std::cerr << "Failed to create media output root: " << mediaRoot << " (" << ec.message() << ")" << std::endl;
        return;
    }

    auto to83Name = [](size_t index) {
        std::ostringstream oss;
        oss << "IM" << std::setw(6) << std::setfill('0') << index;
        return oss.str(); // DICOM File IDs do not carry extensions
    };

    std::map<fs::path, std::string> mediaMapping;
    size_t copied = 0;
    size_t counter = 1;
    for (const auto& dicom : dicomFiles) {
        const std::string shortName = to83Name(counter++);
        fs::path dest = mediaRoot / shortName;
        std::error_code copyErr;
        fs::copy_file(dicom, dest, fs::copy_options::overwrite_existing, copyErr);
        if (!copyErr) {
            mediaMapping[dicom] = shortName;
            ++copied;
        } else {
            std::cerr << "Failed to copy " << dicom << " -> " << dest << " (" << copyErr.message() << ")" << std::endl;
        }
    }

    std::string dicomdirPath = (mediaRoot / "DICOMDIR").string();
    OFFilename dicomdirName(dicomdirPath.c_str());
    OFFilename rootDir(mediaRoot.c_str());
    DicomDirInterface dirif;
    dirif.disableConsistencyCheck(OFTrue);
    OFCondition status = dirif.createNewDicomDir(DicomDirInterface::AP_GeneralPurpose, dicomdirName, "DICOMTOOLS");
    if (status.bad()) {
        std::cerr << "Failed to create DICOMDIR scaffold: " << status.text() << std::endl;
        return;
    }

    size_t added = 0;
    for (const auto& dicom : dicomFiles) {
        // Use relative paths inside the media root to mimic disc layout
        auto mapped = mediaMapping.find(dicom);
        if (mapped == mediaMapping.end()) {
            std::cerr << "  Skipped " << dicom << " (copy failed earlier)" << std::endl;
            continue;
        }
        const std::string& fileId = mapped->second;
        status = dirif.addDicomFile(OFFilename(fileId.c_str()), rootDir);
        if (status.good()) {
            ++added;
        } else {
            std::cerr << "  Skipped " << dicom << ": " << status.text() << std::endl;
        }
    }

    status = dirif.writeDicomDir();
    if (status.good()) {
        std::cout << "Copied " << copied << " files and wrote DICOMDIR (" << added << " entries) to '" << dicomdirPath << "'" << std::endl;
        std::cout << "Media root (relative references): " << mediaRoot << std::endl;
    } else {
        std::cerr << "Failed to write DICOMDIR: " << status.text() << std::endl;
    }
}


void DCMTKTests::TestLosslessJPEGReencode(const std::string& filename, const std::string& outputDir) {
    // Round-trip the dataset through JPEG Lossless to validate codec configuration
    std::cout << "--- [DCMTK] JPEG Lossless Re-encode ---" << std::endl;
    DJDecoderRegistration::registerCodecs();
    DJEncoderRegistration::registerCodecs();

    DcmFileFormat fileformat;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (!status.good()) {
        std::cerr << "Error reading file for JPEG re-encode: " << status.text() << std::endl;
        DJDecoderRegistration::cleanup();
        DJEncoderRegistration::cleanup();
        return;
    }

    std::string outFile = JoinPath(outputDir, "dcmtk_jpeg_lossless.dcm");
    status = fileformat.saveFile(outFile.c_str(), EXS_JPEGProcess14SV1);
    if (status.good()) {
        std::cout << "Saved JPEG Lossless file to '" << outFile << "'" << std::endl;
    } else {
        std::cerr << "JPEG re-encode failed: " << status.text() << std::endl;
    }

    DJDecoderRegistration::cleanup();
    DJEncoderRegistration::cleanup();
}


void DCMTKTests::TestExplicitVRRewrite(const std::string& filename, const std::string& outputDir) {
    // Force a transcode to Explicit VR Little Endian to ensure basic transfer syntax handling
    std::cout << "--- [DCMTK] Explicit VR Little Endian ---" << std::endl;
    DcmFileFormat fileformat;
    OFCondition status = fileformat.loadFile(filename.c_str());
    if (!status.good()) {
        std::cerr << "Error reading file for explicit VR rewrite: " << status.text() << std::endl;
        return;
    }

    std::string outFile = JoinPath(outputDir, "dcmtk_explicit_vr.dcm");
    status = fileformat.saveFile(outFile.c_str(), EXS_LittleEndianExplicit);
    if (status.good()) {
        std::cout << "Saved Explicit VR Little Endian copy to '" << outFile << "'" << std::endl;
    } else {
        std::cerr << "Explicit VR transcode failed: " << status.text() << std::endl;
    }
}
