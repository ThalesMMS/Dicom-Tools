void VTKTests::TestIsotropicResample(const std::string& filename, const std::string& outputDir) {
    // Resample the volume to 1mm spacing and export as VTI
    std::cout << "--- [VTK] Isotropic Resample ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double* originalSpacing = reader->GetOutput()->GetSpacing();

    vtkNew<vtkImageResample> resample;
    resample->SetInputConnection(reader->GetOutputPort());
    resample->SetAxisOutputSpacing(0, 1.0);
    resample->SetAxisOutputSpacing(1, 1.0);
    resample->SetAxisOutputSpacing(2, 1.0);
    resample->SetInterpolationModeToLinear();
    resample->Update();

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_resampled.vti").c_str());
    writer->SetInputConnection(resample->GetOutputPort());
    writer->Write();

    double* newSpacing = resample->GetOutput()->GetSpacing();
    std::cout << "Resampled spacing " << originalSpacing[0] << "x" << originalSpacing[1] << "x" << originalSpacing[2]
              << " -> " << newSpacing[0] << "x" << newSpacing[1] << "x" << newSpacing[2]
              << " and saved to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestMaximumIntensityProjection(const std::string& filename, const std::string& outputDir) {
    // Generate an axial MIP with a small slab thickness and export to PNG
    std::cout << "--- [VTK] Maximum Intensity Projection ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double range[2];
    reader->GetOutput()->GetScalarRange(range);
    double center[3];
    reader->GetOutput()->GetCenter(center);
    double spacing[3];
    reader->GetOutput()->GetSpacing(spacing);

    vtkNew<vtkImageSlabReslice> slab;
    slab->SetInputConnection(reader->GetOutputPort());
    slab->SetBlendModeToMax();
    slab->SetSlabThickness(std::max(1.0, spacing[2] * 8.0));
    slab->SetSlabResolution(spacing[2]);
    slab->SetOutputDimensionality(2);
    slab->SetResliceAxesDirectionCosines(1, 0, 0, 0, 1, 0, 0, 0, 1);
    slab->SetResliceAxesOrigin(center);

    vtkNew<vtkImageShiftScale> shiftScale;
    shiftScale->SetInputConnection(slab->GetOutputPort());
    shiftScale->SetShift(-range[0]);
    shiftScale->SetScale(255.0 / std::max(1.0, range[1] - range[0]));
    shiftScale->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_mip.png").c_str());
    writer->SetInputConnection(shiftScale->GetOutputPort());
    writer->Write();

    std::cout << "Saved axial MIP PNG to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestConnectivityLabels(const std::string& filename, const std::string& outputDir) {
    // Label connected regions in a thresholded volume to exercise vtkImageConnectivityFilter
    std::cout << "--- [VTK] Connected Components ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputConnection(reader->GetOutputPort());
    threshold->ThresholdBetween(150, 3000);
    threshold->SetInValue(1);
    threshold->SetOutValue(0);
    threshold->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkImageConnectivityFilter> connectivity;
    connectivity->SetInputConnection(threshold->GetOutputPort());
    connectivity->SetExtractionModeToAllRegions();
    connectivity->SetLabelModeToSizeRank();
    connectivity->SetLabelScalarTypeToUnsignedShort();
    connectivity->GenerateRegionExtentsOn();
    connectivity->Update();

    vtkNew<vtkXMLImageDataWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_connectivity_mask.vti").c_str());
    writer->SetInputConnection(connectivity->GetOutputPort());
    writer->Write();

    std::cout << "Labeled " << connectivity->GetNumberOfExtractedRegions()
              << " connected region(s) and saved to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestViewerSnapshot(const std::string& filename, const std::string& outputDir) {
    // Render a middle slice via vtkImageViewer2 and capture an off-screen PNG
    std::cout << "--- [VTK] ImageViewer2 Snapshot ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    int extent[6];
    reader->GetOutput()->GetExtent(extent);
    const int midSlice = (extent[4] + extent[5]) / 2;

    vtkNew<vtkImageViewer2> viewer;
    viewer->SetInputConnection(reader->GetOutputPort());
    viewer->SetSlice(midSlice);
    viewer->GetRenderWindow()->SetOffScreenRendering(1);
    viewer->Render();

    vtkNew<vtkWindowToImageFilter> capture;
    capture->SetInput(viewer->GetRenderWindow());
    capture->SetInputBufferTypeToRGB();
    capture->ReadFrontBufferOff();
    capture->Update();

    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_viewer_slice.png").c_str());
    writer->SetInputConnection(capture->GetOutputPort());
    writer->Write();

    std::cout << "Captured viewer slice " << midSlice << " to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestVolumeRenderingSnapshot(const std::string& filename, const std::string& outputDir) {
    // Headless volume rendering snapshot using vtkSmartVolumeMapper
    std::cout << "--- [VTK] Volume Rendering ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double range[2];
    reader->GetOutput()->GetScalarRange(range);

    // Fallback-friendly: render a central slice with window/level to avoid GPU-specific crashes
    vtkNew<vtkImageReslice> reslice;
    reslice->SetInputConnection(reader->GetOutputPort());
    reslice->SetOutputDimensionality(2);
    double center[3];
    reader->GetOutput()->GetCenter(center);
    reslice->SetResliceAxesOrigin(center);

    vtkNew<vtkImageShiftScale> shiftScale;
    shiftScale->SetInputConnection(reslice->GetOutputPort());
    shiftScale->SetShift(-range[0]);
    shiftScale->SetScale(255.0 / std::max(1.0, range[1] - range[0]));
    shiftScale->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkPNGWriter> writer;
    const std::string outFile = JoinPath(outputDir, "vtk_volume_render.png");
    writer->SetFileName(outFile.c_str());
    writer->SetInputConnection(shiftScale->GetOutputPort());
    writer->Write();

    std::cout << "Saved volume rendering snapshot to '" << outFile << "'" << std::endl;
}
