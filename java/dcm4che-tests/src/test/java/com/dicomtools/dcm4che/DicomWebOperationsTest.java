package com.dicomtools.dcm4che;

import com.dicomtools.cli.DicomWebOperations;
import com.dicomtools.cli.OperationResult;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertTrue;

class DicomWebOperationsTest {

    @TempDir
    Path tempDir;

    private HttpServer server;
    private ExecutorService executor;
    private Path stowDir;

    @AfterEach
    void tearDown() {
        if (server != null) {
            server.stop(0);
        }
        if (executor != null) {
            executor.shutdownNow();
        }
    }

    @Test
    void stowQidoWadoRoundTrip() throws Exception {
        startServer();
        int port = server.getAddress().getPort();
        Path sample = TestData.sampleDicom();

        OperationResult stow = DicomWebOperations.stow(sample, "http://127.0.0.1:" + port + "/stow");
        assertTrue(stow.isSuccess());
        assertEquals(1, Files.list(stowDir).count());

        OperationResult qido = DicomWebOperations.qido("http://127.0.0.1:" + port + "/qido");
        assertTrue(qido.isSuccess());
        assertEquals(1, ((Number) qido.getMetadata().get("count")).intValue());

        Path wadoOut = tempDir.resolve("wado.dcm");
        OperationResult wado = DicomWebOperations.wado("http://127.0.0.1:" + port + "/wado", wadoOut);
        assertTrue(wado.isSuccess());
        assertTrue(Files.exists(wadoOut));
        assertEquals(Files.size(sample), Files.size(wadoOut));
    }

    private void startServer() throws IOException {
        server = HttpServer.create(new InetSocketAddress(0), 0);
        executor = Executors.newSingleThreadExecutor();
        server.setExecutor(executor);
        stowDir = tempDir.resolve("stow");
        Files.createDirectories(stowDir);
        server.createContext("/stow", new StowHandler());
        server.createContext("/qido", exchange -> respond(exchange, 200, "[{\"PatientName\":\"DOE^JOHN\"}]"));
        server.createContext("/wado", exchange -> {
            byte[] content = Files.readAllBytes(TestData.sampleDicom());
            exchange.getResponseHeaders().add("Content-Type", "application/dicom");
            exchange.sendResponseHeaders(200, content.length);
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(content);
            }
        });
        server.start();
    }

    private void respond(HttpExchange exchange, int code, String body) throws IOException {
        byte[] bytes = body.getBytes();
        exchange.getResponseHeaders().add("Content-Type", "application/json");
        exchange.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    private class StowHandler implements HttpHandler {
        @Override
        public void handle(HttpExchange exchange) throws IOException {
            byte[] data = exchange.getRequestBody().readAllBytes();
            Files.write(stowDir.resolve("object.dcm"), data);
            respond(exchange, 200, "{\"status\":\"OK\"}");
        }
    }
}
