package com.dicomtools.cli;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;
import java.util.Map;

public class DicomToolsCli {
    public static void main(String[] args) {
        int exitCode = run(args);
        System.exit(exitCode);
    }

    private static int run(String[] args) {
        if (args.length == 0) {
            usage();
            return 1;
        }

        String command = args[0];
        List<String> restList = new ArrayList<>(Arrays.asList(Arrays.copyOfRange(args, 1, args.length)));
        boolean pretty = popFlag(restList, "--pretty");
        boolean text = popFlag(restList, "--text");
        String[] rest = restList.toArray(new String[0]);

        try {
            OperationResult result;
            switch (command) {
                case "info" -> result = handleInfo(rest);
                case "anonymize" -> result = handleAnonymize(rest);
                case "to-image" -> result = handleToImage(rest);
                case "transcode" -> result = handleTranscode(rest);
                case "validate" -> result = handleValidate(rest);
                case "dump" -> result = handleDump(rest);
                case "stats", "histogram" -> result = handleStats(rest);
                case "echo" -> result = handleEcho(rest);
                default -> {
                    System.err.println("Unknown command: " + command);
                    usage();
                    return 1;
                }
            }
            printResult(result, text, pretty);
            return result != null && result.isSuccess() ? 0 : 1;
        } catch (Exception e) {
            System.err.println("Error: " + e.getMessage());
            e.printStackTrace(System.err);
            return 1;
        }
    }

    private static OperationResult handleInfo(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("info requires <input>");
        }
        Path input = Paths.get(args[0]);
        OperationResult result = DicomOperations.info(input);
        return result;
    }

    private static OperationResult handleAnonymize(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("anonymize requires <input>");
        }
        Path input = Paths.get(args[0]);
        String outputOpt = optionValue(args, "--output");
        Path output = outputOpt != null
                ? Paths.get(outputOpt)
                : deriveSibling(input, "_anon.dcm");
        OperationResult result = DicomOperations.anonymize(input, output);
        System.out.println(result.getMessage());
        return result;
    }

    private static OperationResult handleToImage(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("to-image requires <input>");
        }
        Path input = Paths.get(args[0]);
        String outputOpt = optionValue(args, "--output");
        String format = optionValue(args, "--format");
        int frame = optionInt(args, "--frame", 0);
        Path output = outputOpt != null
                ? Paths.get(outputOpt)
                : deriveSibling(input, format != null && format.startsWith("jp") ? ".jpg" : ".png");

        return DicomOperations.toImage(input, output, format, frame);
    }

    private static OperationResult handleTranscode(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("transcode requires <input>");
        }
        Path input = Paths.get(args[0]);
        String outputOpt = optionValue(args, "--output");
        String syntax = optionValue(args, "--syntax");
        Path output = outputOpt != null
                ? Paths.get(outputOpt)
                : deriveSibling(input, "_transcoded.dcm");

        return DicomOperations.transcode(input, output, syntax);
    }

    private static OperationResult handleValidate(String[] args) {
        if (args.length == 0) {
            throw new IllegalArgumentException("validate requires <input>");
        }
        Path input = Paths.get(args[0]);
        return DicomOperations.validate(input);
    }

    private static OperationResult handleDump(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("dump requires <input>");
        }
        Path input = Paths.get(args[0]);
        int maxWidth = optionInt(args, "--max-width", 120);
        return DicomOperations.dump(input, maxWidth);
    }

    private static OperationResult handleStats(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("stats requires <input>");
        }
        Path input = Paths.get(args[0]);
        int bins = optionInt(args, "--bins", 256);

        return DicomOperations.stats(input, bins);
    }

    private static OperationResult handleEcho(String[] args) {
        if (args.length == 0) {
            throw new IllegalArgumentException("echo requires host:port");
        }
        String target = args[0];
        String[] parts = target.split(":");
        String host = parts[0];
        int port = parts.length > 1 ? Integer.parseInt(parts[1]) : 104;
        int timeout = optionInt(args, "--timeout", 2000);
        String calling = optionValue(args, "--calling");
        if (calling == null) calling = "ECHO-SCU";
        String called = optionValue(args, "--called");
        if (called == null) called = "ANY-SCP";

        return DicomOperations.echo(host, port, timeout, calling, called);
    }

    private static void usage() {
        System.out.println("""
                Usage: java -jar dcm4che-tests.jar <command> [args]
                  info <input> [--json] [--pretty]
                  anonymize <input> [--output <file>]
                  to-image <input> [--output <file>] [--format png|jpeg] [--frame N]
                  transcode <input> [--output <file>] [--syntax explicit|implicit|rle|jpeg2000]
                  validate <input>
                  dump <input> [--max-width N]
                  stats <input> [--bins N] [--json] [--pretty]
                  echo <host:port> [--timeout ms] [--calling AET] [--called AET]
                """);
    }

    private static String optionValue(String[] args, String flag) {
        for (int i = 0; i < args.length - 1; i++) {
            if (flag.equals(args[i])) {
                return args[i + 1];
            }
        }
        return null;
    }

    private static int optionInt(String[] args, String flag, int defaultValue) {
        String val = optionValue(args, flag);
        if (val == null) return defaultValue;
        try {
            return Integer.parseInt(val);
        } catch (NumberFormatException e) {
            return defaultValue;
        }
    }

    private static Path deriveSibling(Path input, String suffix) {
        String name = input.getFileName().toString();
        int idx = name.lastIndexOf('.');
        String base = idx > 0 ? name.substring(0, idx) : name;
        Path parent = input.toAbsolutePath().getParent();
        if (parent == null) {
            return Paths.get(base + suffix);
        }
        return parent.resolve(base + suffix);
    }

    private static void printResult(OperationResult result, boolean text, boolean pretty) {
        if (text) {
            System.out.println(result.getMessage());
            return;
        }
        Map<String, Object> envelope = Map.of(
                "ok", result.isSuccess(),
                "returncode", result.isSuccess() ? 0 : 1,
                "stdout", result.isSuccess() ? result.getMessage() : "",
                "stderr", result.isSuccess() ? "" : result.getMessage(),
                "output_files", result.getOutputFiles().stream().map(Path::toString).toList(),
                "metadata", result.getMetadata());
        System.out.println(JsonUtils.toJsonString(envelope, pretty));
    }

    private static boolean popFlag(List<String> args, String flag) {
        boolean found = args.remove(flag);
        return found;
    }
}
