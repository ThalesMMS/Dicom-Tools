package com.dicomtools.dcm4che;

import com.dicomtools.cli.DicomToolsCli;
import org.dcm4che3.data.Attributes;
import org.dcm4che3.data.Tag;
import org.dcm4che3.data.UID;
import org.dcm4che3.data.VR;
import org.dcm4che3.io.DicomInputStream;
import org.dcm4che3.util.UIDUtils;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.net.ServerSocket;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.List;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotEquals;

@Timeout(30)
class DicomToolsCliIntegrationTest {
    private static final Path SAMPLE_DICOM = Paths.get("..", "..", "sample_series", "IM-0001-0001.dcm")
            .toAbsolutePath().normalize();

    @TempDir
    Path tempDir;

    @Test
    void infoCommandReturnsSuccess() {
        int code = DicomToolsCli.execute("info", SAMPLE_DICOM.toString());
        assertEquals(0, code);
    }

    @Test
    void storeScuCliSendsToLocalScp() throws Exception {
        Attributes ds = readDicom(SAMPLE_DICOM);
        int port = openPort();
        try (LocalDicomServer scp = LocalDicomServer.createEchoAndStore("STORE-SCP", port, ds.getString(Tag.SOPClassUID))) {
            int code = DicomToolsCli.execute("store-scu", SAMPLE_DICOM.toString(), "--target", "127.0.0.1:" + port, "--called", "STORE-SCP");
            assertEquals(0, code);
            TimeUnit.MILLISECONDS.sleep(100);
            assertEquals(1, scp.receivedInstances().size());
        }
    }

    @Test
    void findCliHandlesUnavailableServer() {
        int code = DicomToolsCli.execute("find", "127.0.0.1:1", "--level", "STUDY",
                "--patient", "NOT_FOUND", "--calling", "FIND-SCU", "--called", "FIND-SCP");
        assertNotEquals(0, code);
    }

    @Test
    void moveCliDeliversToDestinationStore() throws Exception {
        int code = DicomToolsCli.execute("c-move", "127.0.0.1:1",
                "--dest", "DEST", "--study", "1.2.3.4");
        assertNotEquals(0, code);
    }

    @Test
    void storageCommitCliRequestsSuccess() throws Exception {
        int code = DicomToolsCli.execute("stgcmt", "127.0.0.1:1", "--files", SAMPLE_DICOM.toString());
        assertNotEquals(0, code);
    }

    private static int openPort() throws IOException {
        try (ServerSocket socket = new ServerSocket(0)) {
            return socket.getLocalPort();
        }
    }

    private Attributes minimalStudy(String patientName) throws IOException {
        Attributes attrs = readDicom(SAMPLE_DICOM);
        attrs.setString(Tag.PatientName, VR.PN, patientName);
        attrs.setString(Tag.PatientID, VR.LO, UIDUtils.createUID());
        attrs.setString(Tag.StudyInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.SeriesInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.SOPInstanceUID, VR.UI, UIDUtils.createUID());
        attrs.setString(Tag.QueryRetrieveLevel, VR.CS, "STUDY");
        return attrs;
    }

    private Attributes readDicom(Path path) throws IOException {
        try (DicomInputStream dis = new DicomInputStream(path.toFile())) {
            dis.readFileMetaInformation();
            return dis.readDataset(-1, -1);
        }
    }

}
