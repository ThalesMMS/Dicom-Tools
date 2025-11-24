using System.IO;
using System.Linq;
using FellowOakDicom;
using FellowOakDicom.Imaging;
using FellowOakDicom.Imaging.Codec;
using FellowOakDicom.Media;

namespace DicomTools.Tests;

public class TranscodeAndDirectoryTests
{
    [Fact]
    public void Transcoder_ImplicitLittleEndian_RetainsPixels()
    {
        var file = DicomFile.Open(SampleSeriesHelper.GetFirstFilePath());
        var originalSyntax = file.FileMetaInfo.TransferSyntax;
        var targetSyntax = DicomTransferSyntax.ImplicitVRLittleEndian;

        var transcoder = new DicomTranscoder(originalSyntax, targetSyntax);
        var transcoded = transcoder.Transcode(file);

        Assert.Equal(targetSyntax, transcoded.FileMetaInfo.TransferSyntax);

        var originalPixels = DicomPixelData.Create(file.Dataset, false).GetFrame(0).Data;
        var transcodedPixels = DicomPixelData.Create(transcoded.Dataset, false).GetFrame(0).Data;
        Assert.Equal(originalPixels, transcodedPixels);

        Assert.Equal(
            file.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID),
            transcoded.Dataset.GetSingleValue<string>(DicomTag.SOPInstanceUID));
    }

    [Fact]
    public void DicomDirectory_BuildsHierarchy_FromSampleSeries()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"dicomdir-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);

        try
        {
            var files = SampleSeriesHelper.GetSeriesFiles(3).ToArray();
            var dicomDir = new DicomDirectory();
            for (var i = 0; i < files.Length; i++)
            {
                var filePath = files[i];
                var fileId = $"IM{i + 1:0000}";
                dicomDir.AddFile(DicomFile.Open(filePath), referencedFileId: fileId);
            }

            var outputPath = Path.Combine(tempDir, "DICOMDIR");
            dicomDir.FileSetID = "SAMPLESET";
            dicomDir.Save(outputPath);

            var reloaded = DicomDirectory.Open(outputPath);

            Assert.NotNull(reloaded.RootDirectoryRecord);
            Assert.NotEmpty(reloaded.RootDirectoryRecordCollection);

            var patientRecords = reloaded.RootDirectoryRecordCollection.ToArray();
            Assert.NotEmpty(patientRecords);

            var firstPatient = patientRecords.First();
            var studies = firstPatient.LowerLevelDirectoryRecordCollection;
            Assert.NotNull(studies);
            Assert.NotEmpty(studies);

            var firstStudy = studies.First();
            var seriesRecords = firstStudy.LowerLevelDirectoryRecordCollection;
            Assert.NotNull(seriesRecords);
            Assert.NotEmpty(seriesRecords);

            var firstSeries = seriesRecords.First();
            var instances = firstSeries.LowerLevelDirectoryRecordCollection;
            Assert.NotNull(instances);
            Assert.True(instances.Count() >= files.Length);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }
}
