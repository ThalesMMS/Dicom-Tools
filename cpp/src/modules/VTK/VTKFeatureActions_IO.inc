void VTKTests::TestImageExport(const std::string& filename, const std::string& outputDir) {
    // Read a series and serialize it to VTK's VTI format
    std::cout << "--- [VTK] Image Export ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetFileName(filename.c_str());
    reader->Update();

    int* dims = reader->GetOutput()->GetDimensions();
    std::cout << "Dimensions: " << dims[0] << " x " << dims[1] << " x " << dims[2] << std::endl;

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_export.vti").c_str());
    writer->SetInputData(reader->GetOutput());
    writer->Write();
    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestNiftiExport(const std::string& filename, const std::string& outputDir) {
    // Export the loaded series directly to compressed NIfTI
    std::cout << "--- [VTK] NIfTI Export ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    vtkNew<vtkNIFTIImageWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_volume.nii.gz").c_str());
    writer->SetInputConnection(reader->GetOutputPort());
    writer->Write();

    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestIsosurfaceExtraction(const std::string& filename, const std::string& outputDir) {
    // Run marching cubes on the CT volume to produce a quick STL mesh
    std::cout << "--- [VTK] Isosurface Extraction (Marching Cubes) ---" << std::endl;
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();
    
    vtkNew<vtkMarchingCubes> surface;
    surface->SetInputConnection(reader->GetOutputPort());
    surface->ComputeNormalsOn();
    surface->ComputeGradientsOn();
    surface->SetValue(0, 500);

    vtkNew<vtkSTLWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_isosurface.stl").c_str());
    writer->SetInputConnection(surface->GetOutputPort());
    writer->Write();
    
    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestMPR(const std::string& filename, const std::string& outputDir) {
    // Slice through the volume center and export a single MPR PNG
    std::cout << "--- [VTK] MPR (Single Slice Export) ---" << std::endl;
    
    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();
    
    double* center = reader->GetOutput()->GetCenter();
    double* range = reader->GetOutput()->GetScalarRange();
    
    vtkNew<vtkImageReslice> reslice;
    reslice->SetInputConnection(reader->GetOutputPort());
    reslice->SetOutputDimensionality(2);
    reslice->SetResliceAxesOrigin(center[0], center[1], center[2]);
    
    vtkNew<vtkImageShiftScale> shiftScale;
    shiftScale->SetInputConnection(reslice->GetOutputPort());
    shiftScale->SetShift(-range[0]);
    shiftScale->SetScale(255.0 / (range[1] - range[0]));
    shiftScale->SetOutputScalarTypeToUnsignedChar();
    
    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_mpr_slice.png").c_str());
    writer->SetInputConnection(shiftScale->GetOutputPort());
    writer->Write();
    
    std::cout << "Saved to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestThresholdMask(const std::string& filename, const std::string& outputDir) {
    // Create a binary mask with a simple HU window and save as VTI
    std::cout << "--- [VTK] Threshold Mask ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputConnection(reader->GetOutputPort());
    threshold->ThresholdBetween(300, 3000);
    threshold->SetInValue(1);
    threshold->SetOutValue(0);
    threshold->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_threshold_mask.vti").c_str());
    writer->SetInputConnection(threshold->GetOutputPort());
    writer->Write();

    std::cout << "Saved binary mask to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestVolumeStatistics(const std::string& filename, const std::string& outputDir) {
    // Compute histogram-driven stats for a CT volume and persist to text
    std::cout << "--- [VTK] Volume Statistics ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double scalarRange[2];
    reader->GetOutput()->GetScalarRange(scalarRange);
    const int minBin = static_cast<int>(std::floor(scalarRange[0]));
    const int maxBin = static_cast<int>(std::ceil(scalarRange[1]));
    const int extent = std::max(1, std::min(8192, maxBin - minBin + 1));

    vtkNew<vtkImageAccumulate> hist;
    hist->SetInputConnection(reader->GetOutputPort());
    hist->SetComponentExtent(0, extent - 1, 0, 0, 0, 0);
    hist->SetComponentOrigin(minBin, 0, 0);
    hist->SetComponentSpacing(1, 1, 1);
    hist->IgnoreZeroOn();
    hist->Update();

    const double minValue = hist->GetMin()[0];
    const double maxValue = hist->GetMax()[0];
    const double meanValue = hist->GetMean()[0];
    const double stddevValue = hist->GetStandardDeviation()[0];

    std::string outFile = JoinPath(outputDir, "vtk_stats.txt");
    std::ofstream out(outFile, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open stats output: " << outFile << std::endl;
        return;
    }

    int* dims = reader->GetOutput()->GetDimensions();
    out << "Dimensions=" << dims[0] << "x" << dims[1] << "x" << dims[2] << "\n";
    out << "Range=[" << minValue << ", " << maxValue << "]\n";
    out << "Mean=" << meanValue << "\n";
    out << "StdDev=" << stddevValue << "\n";
    out.close();

    std::cout << "Wrote stats to '" << outFile << "'" << std::endl;
}


void VTKTests::TestMetadataExport(const std::string& filename, const std::string& outputDir) {
    // Grab common DICOM metadata fields from the VTK reader and log them
    std::cout << "--- [VTK] Metadata Export ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    std::string outFile = JoinPath(outputDir, "vtk_metadata.txt");
    std::ofstream out(outFile, std::ios::out | std::ios::trunc);
    if (!out.is_open()) {
        std::cerr << "Failed to open metadata output: " << outFile << std::endl;
        return;
    }

    int* dims = reader->GetOutput()->GetDimensions();
    double spacing[3];
    reader->GetOutput()->GetSpacing(spacing);
    float* origin = reader->GetImagePositionPatient();
    float* orientation = reader->GetImageOrientationPatient();

    out << "PatientName: " << (reader->GetPatientName() ? reader->GetPatientName() : "") << "\n";
    out << "StudyInstanceUID: " << (reader->GetStudyUID() ? reader->GetStudyUID() : "") << "\n";
    out << "StudyID: " << (reader->GetStudyID() ? reader->GetStudyID() : "") << "\n";
    out << "TransferSyntaxUID: " << (reader->GetTransferSyntaxUID() ? reader->GetTransferSyntaxUID() : "") << "\n";
    out << "Dimensions: " << dims[0] << "x" << dims[1] << "x" << dims[2] << "\n";
    out << "Spacing: " << spacing[0] << "x" << spacing[1] << "x" << spacing[2] << "\n";
    out << "Origin: " << origin[0] << "," << origin[1] << "," << origin[2] << "\n";
    out << "Orientation: ";
    if (orientation) {
        out << orientation[0] << "," << orientation[1] << "," << orientation[2] << ","
            << orientation[3] << "," << orientation[4] << "," << orientation[5] << "\n";
    } else {
        out << "\n";
    }
    out.close();

    std::cout << "Wrote metadata summary to '" << outFile << "'" << std::endl;
}
