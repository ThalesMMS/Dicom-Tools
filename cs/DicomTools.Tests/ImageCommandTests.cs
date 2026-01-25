using FellowOakDicom;

namespace DicomTools.Tests;

public class ImageCommandTests
{
    [Fact]
    public void ToImage_Creates_PNG_File()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"img-png-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, "output.png");

        try
        {
            var result = CliRunner.Run("to-image", input, "--output", output);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(output));
            Assert.True(new FileInfo(output).Length > 0);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void ToImage_Creates_JPEG_File()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"img-jpg-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, "output.jpg");

        try
        {
            var result = CliRunner.Run("to-image", input, "--output", output, "--format", "jpeg");
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(output));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void ToImage_Uses_Default_Output_Name()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"img-default-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var inputPath = Path.Combine(tempDir, "source.dcm");

        try
        {
            File.Copy(SampleSeriesHelper.GetFirstFilePath(), inputPath);
            var result = CliRunner.Run("to-image", inputPath);
            Assert.Equal(0, result.ExitCode);

            var pngExists = File.Exists(Path.Combine(tempDir, "source.png"));
            var jpgExists = File.Exists(Path.Combine(tempDir, "source.jpg"));
            Assert.True(pngExists || jpgExists);
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void ToImage_Handles_Specific_Frame()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"img-frame-{Guid.NewGuid():N}");
        Directory.CreateDirectory(tempDir);
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(tempDir, "frame0.png");

        try
        {
            var result = CliRunner.Run("to-image", input, "--frame", "0", "--output", output);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(output));
        }
        finally
        {
            Directory.Delete(tempDir, recursive: true);
        }
    }

    [Fact]
    public void ToImage_Creates_Parent_Directory()
    {
        var tempDir = Path.Combine(Path.GetTempPath(), $"img-subdir-{Guid.NewGuid():N}");
        var subDir = Path.Combine(tempDir, "nested", "output");
        var input = SampleSeriesHelper.GetFirstFilePath();
        var output = Path.Combine(subDir, "image.png");

        try
        {
            var result = CliRunner.Run("to-image", input, "--output", output);
            Assert.Equal(0, result.ExitCode);
            Assert.True(File.Exists(output));
        }
        finally
        {
            if (Directory.Exists(tempDir))
                Directory.Delete(tempDir, recursive: true);
        }
    }
}
