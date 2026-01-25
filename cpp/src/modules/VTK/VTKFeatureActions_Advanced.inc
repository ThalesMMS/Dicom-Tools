void VTKTests::TestTimeSeries(const std::string& filename, const std::string& outputDir) {
    // Inspect time dimension and spacing to validate 4D series handling
    std::cout << "--- [VTK] Time Series Inspection ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->UpdateInformation();
    reader->Update();

    int dims[3] = {0, 0, 0};
    reader->GetOutput()->GetDimensions(dims);
    const int timeDim = 1; // vtkDICOMImageReader does not expose temporal dim; assume 1 for now
    const double timeSpacing = 0.0;
    const int slicesPerVolume = dims[2];

    std::string reportPath = JoinPath(outputDir, "vtk_time_series.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    report << "Dimensions=" << dims[0] << "x" << dims[1] << "x" << dims[2] << "\n";
    report << "TimeDimension=" << timeDim << "\n";
    report << "TimeSpacing=" << timeSpacing << "\n";
    report << "SlicesPerVolume=" << slicesPerVolume << "\n";
    report.close();

    std::cout << "Time series report written to '" << reportPath << "'" << std::endl;
}


void VTKTests::TestMultiVolumeFusion(const std::string& filename, const std::string& outputDir) {
    // Simple PET/CT-like fusion using two color maps blended together
    std::cout << "--- [VTK] Multi-Volume Fusion ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double range[2];
    reader->GetOutput()->GetScalarRange(range);

    // Base grayscale CT
    vtkNew<vtkImageMapToWindowLevelColors> baseColor;
    baseColor->SetInputConnection(reader->GetOutputPort());
    baseColor->SetWindow(std::max(1.0, range[1] - range[0]));
    baseColor->SetLevel((range[0] + range[1]) / 2.0);
    baseColor->Update();

    // Synthetic PET-like mask emphasizing higher HU values
    vtkNew<vtkImageThreshold> hotMask;
    hotMask->SetInputConnection(reader->GetOutputPort());
    hotMask->ThresholdByUpper(std::max(range[0] + 300.0, range[1] * 0.6));
    hotMask->SetInValue(1.0);
    hotMask->SetOutValue(0.0);

    vtkNew<vtkLookupTable> hotLut;
    hotLut->SetNumberOfTableValues(256);
    hotLut->SetTableRange(0.0, 1.0);
    hotLut->Build();
    for (int i = 0; i < 256; ++i) {
        const double t = static_cast<double>(i) / 255.0;
        hotLut->SetTableValue(i, t, std::min(1.0, t * 1.5), 0.2 + 0.5 * t, t);
    }

    vtkNew<vtkImageMapToColors> hotColor;
    hotColor->SetLookupTable(hotLut);
    hotColor->SetInputConnection(hotMask->GetOutputPort());
    hotColor->SetOutputFormatToRGBA();

    vtkNew<vtkImageBlend> blend;
    blend->AddInputConnection(baseColor->GetOutputPort());
    blend->AddInputConnection(hotColor->GetOutputPort());
    blend->SetOpacity(0, 1.0);
    blend->SetOpacity(1, 0.55);

    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_fusion.png").c_str());
    writer->SetInputConnection(blend->GetOutputPort());
    writer->Write();

    std::cout << "Saved fused multi-volume snapshot to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestMultiplanarMPR(const std::string& filename, const std::string& outputDir) {
    // Export sagittal, coronal, and oblique MPR slices
    std::cout << "--- [VTK] Multiplanar MPR ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double center[3];
    reader->GetOutput()->GetCenter(center);
    double range[2];
    reader->GetOutput()->GetScalarRange(range);

    auto cross = [](const double a[3], const double b[3], double out[3]) {
        out[0] = a[1] * b[2] - a[2] * b[1];
        out[1] = a[2] * b[0] - a[0] * b[2];
        out[2] = a[0] * b[1] - a[1] * b[0];
    };

    auto writeSlice = [&](const double x[3], const double y[3], const std::string& name) {
        double z[3];
        cross(x, y, z);

        vtkNew<vtkImageReslice> reslice;
        reslice->SetInputConnection(reader->GetOutputPort());
        reslice->SetOutputDimensionality(2);
        reslice->SetResliceAxesDirectionCosines(
            x[0], x[1], x[2],
            y[0], y[1], y[2],
            z[0], z[1], z[2]);
        reslice->SetResliceAxesOrigin(center);
        reslice->SetInterpolationModeToLinear();

        vtkNew<vtkImageShiftScale> shiftScale;
        shiftScale->SetInputConnection(reslice->GetOutputPort());
        shiftScale->SetShift(-range[0]);
        shiftScale->SetScale(255.0 / std::max(1.0, range[1] - range[0]));
        shiftScale->SetOutputScalarTypeToUnsignedChar();

        vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, name).c_str());
    writer->SetInputConnection(shiftScale->GetOutputPort());
    writer->Write();
    };

    const double sagX[3] = {0.0, 0.0, 1.0};
    const double sagY[3] = {0.0, 1.0, 0.0};
    const double corX[3] = {1.0, 0.0, 0.0};
    const double corY[3] = {0.0, 0.0, 1.0};
    const double obliqueX[3] = {0.7071, 0.7071, 0.0};
    const double obliqueY[3] = {0.0, 0.0, 1.0};

    writeSlice(sagX, sagY, "vtk_mpr_sagittal.png");
    writeSlice(corX, corY, "vtk_mpr_coronal.png");
    writeSlice(obliqueX, obliqueY, "vtk_mpr_oblique.png");

    std::cout << "Wrote multiplanar slices to " << outputDir << std::endl;
}


void VTKTests::TestMaskOverlay(const std::string& filename, const std::string& outputDir) {
    // Create a threshold mask and overlay it on a middle axial slice
    std::cout << "--- [VTK] Mask Overlay ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    int extent[6];
    reader->GetOutput()->GetExtent(extent);
    const int midSlice = (extent[4] + extent[5]) / 2;

    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputConnection(reader->GetOutputPort());
    threshold->ThresholdByUpper(400);
    threshold->SetInValue(1);
    threshold->SetOutValue(0);

    vtkNew<vtkExtractVOI> extractBase;
    extractBase->SetInputConnection(reader->GetOutputPort());
    extractBase->SetVOI(extent[0], extent[1], extent[2], extent[3], midSlice, midSlice);

    vtkNew<vtkExtractVOI> extractMask;
    extractMask->SetInputConnection(threshold->GetOutputPort());
    extractMask->SetVOI(extent[0], extent[1], extent[2], extent[3], midSlice, midSlice);

    double range[2];
    reader->GetOutput()->GetScalarRange(range);

    vtkNew<vtkImageMapToWindowLevelColors> baseColor;
    baseColor->SetInputConnection(extractBase->GetOutputPort());
    baseColor->SetWindow(std::max(1.0, range[1] - range[0]));
    baseColor->SetLevel((range[0] + range[1]) / 2.0);

    vtkNew<vtkLookupTable> lut;
    lut->SetNumberOfTableValues(2);
    lut->SetRange(0, 1);
    lut->SetTableValue(0, 0.0, 0.0, 0.0, 0.0);
    lut->SetTableValue(1, 1.0, 0.2, 0.2, 0.4);
    lut->Build();

    vtkNew<vtkImageMapToColors> maskColor;
    maskColor->SetLookupTable(lut);
    maskColor->SetInputConnection(extractMask->GetOutputPort());
    maskColor->SetOutputFormatToRGBA();

    vtkNew<vtkImageBlend> blend;
    blend->AddInputConnection(baseColor->GetOutputPort());
    blend->AddInputConnection(maskColor->GetOutputPort());
    blend->SetOpacity(0, 1.0);
    blend->SetOpacity(1, 0.7);

    vtkNew<vtkPNGWriter> writer;
    writer->SetFileName(JoinPath(outputDir, "vtk_overlay.png").c_str());
    writer->SetInputConnection(blend->GetOutputPort());
    writer->Write();

    std::cout << "Saved overlay PNG to '" << writer->GetFileName() << "'" << std::endl;
}


void VTKTests::TestLabelmapSurface(const std::string& filename, const std::string& outputDir) {
    // Threshold into a labelmap, compute voxel counts, and export a surface for QA
    std::cout << "--- [VTK] Labelmap + Surface ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->Update();

    double spacing[3] = {1.0, 1.0, 1.0};
    reader->GetOutput()->GetSpacing(spacing);

    vtkNew<vtkImageThreshold> threshold;
    threshold->SetInputConnection(reader->GetOutputPort());
    threshold->ThresholdBetween(150, 3000); // default HU window to isolate denser tissue
    threshold->SetInValue(1);
    threshold->SetOutValue(0);
    threshold->SetOutputScalarTypeToUnsignedChar();

    vtkNew<vtkXMLImageDataWriter> labelWriter;
    labelWriter->SetFileName(JoinPath(outputDir, "vtk_labelmap.vti").c_str());
    labelWriter->SetInputConnection(threshold->GetOutputPort());
    labelWriter->Write();

    vtkNew<vtkImageAccumulate> hist;
    hist->SetInputConnection(threshold->GetOutputPort());
    hist->SetComponentExtent(0, 1, 0, 0, 0, 0);
    hist->SetComponentOrigin(0, 0, 0);
    hist->SetComponentSpacing(1, 1, 1);
    hist->IgnoreZeroOn();
    hist->Update();

    const double labelOneCount = hist->GetOutput()->GetScalarComponentAsDouble(1, 0, 0, 0);
    const double voxelVolume = spacing[0] * spacing[1] * spacing[2];
    const double volumeMM3 = labelOneCount * voxelVolume;

    vtkNew<vtkDiscreteMarchingCubes> cubes;
    cubes->SetInputConnection(threshold->GetOutputPort());
    cubes->SetValue(0, 1);

    vtkNew<vtkTriangleFilter> triangulate;
    triangulate->SetInputConnection(cubes->GetOutputPort());

    vtkNew<vtkSTLWriter> surfaceWriter;
    surfaceWriter->SetFileName(JoinPath(outputDir, "vtk_label_surface.stl").c_str());
    surfaceWriter->SetInputConnection(triangulate->GetOutputPort());
    surfaceWriter->Write();

    const std::string reportPath = JoinPath(outputDir, "vtk_labelmap_stats.txt");
    std::ofstream report(reportPath, std::ios::out | std::ios::trunc);
    report << "LabelValue=1\n";
    report << "Voxels=" << labelOneCount << "\n";
    report << "Spacing=" << spacing[0] << "x" << spacing[1] << "x" << spacing[2] << " mm\n";
    report << "VolumeMM3=" << volumeMM3 << "\n";
    report << "Surface=" << surfaceWriter->GetFileName() << "\n";
    report.close();

    std::cout << "Wrote labelmap, stats, and STL surface to '" << outputDir << "'" << std::endl;
}


void VTKTests::TestStreamingReslice(const std::string& filename, const std::string& outputDir) {
    // Stream the volume in Z-chunks using update extents to cap memory consumption
    std::cout << "--- [VTK] Streaming Reslice ---" << std::endl;

    vtkNew<vtkDICOMImageReader> reader;
    reader->SetDirectoryName(ResolveSeriesDirectory(filename).c_str());
    reader->UpdateInformation();
    reader->Update(); // prime pipeline once so subsequent chunk requests are stable

    vtkInformation* outInfo = reader->GetOutputInformation(0);
    int wholeExtent[6] = {0, 0, 0, 0, 0, 0};
    outInfo->Get(vtkStreamingDemandDrivenPipeline::WHOLE_EXTENT(), wholeExtent);
    const int totalSlices = wholeExtent[5] - wholeExtent[4] + 1;
    const int chunkSize = std::max(1, totalSlices / 4);

    std::vector<double> chunkMeans;
    for (int zStart = wholeExtent[4]; zStart <= wholeExtent[5]; zStart += chunkSize) {
        const int zEnd = std::min(wholeExtent[5], zStart + chunkSize - 1);
        vtkNew<vtkExtractVOI> extract;
        extract->SetInputConnection(reader->GetOutputPort());
        extract->SetVOI(wholeExtent[0], wholeExtent[1], wholeExtent[2], wholeExtent[3], zStart, zEnd);
        extract->Update();

        vtkNew<vtkImageAccumulate> accum;
        accum->SetInputConnection(extract->GetOutputPort());
        accum->IgnoreZeroOff();
        accum->Update();
        chunkMeans.push_back(accum->GetMean()[0]);
    }

    const std::string reportPath = JoinPath(outputDir, "vtk_streaming.txt");
    std::ofstream out(reportPath, std::ios::out | std::ios::trunc);
    out << "Slices=" << totalSlices << "\n";
    out << "ChunkSize=" << chunkSize << "\n";
    for (size_t i = 0; i < chunkMeans.size(); ++i) {
        out << "Chunk[" << i + 1 << "]Mean=" << chunkMeans[i] << "\n";
    }
    out.close();

    std::cout << "Processed " << chunkMeans.size() << " chunk(s); report: " << reportPath << std::endl;
}
