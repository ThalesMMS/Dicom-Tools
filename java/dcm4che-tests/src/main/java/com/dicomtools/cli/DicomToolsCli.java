package com.dicomtools.cli;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import org.dcm4che3.data.Tag;

public class DicomToolsCli {
    public static void main(String[] args) {
        int exitCode = run(args);
        System.exit(exitCode);
    }

    /** Exposed for tests to execute commands without System.exit. */
    public static int execute(String... args) {
        return run(args);
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
                case "store-scu" -> result = handleStore(rest);
                case "store-scp" -> result = handleStoreScp(rest);
                case "find" -> result = handleFind(rest, false);
                case "mwl" -> result = handleFind(rest, true);
                case "cmove", "c-move" -> result = handleMove(rest);
                case "cget", "c-get" -> result = handleGet(rest);
                case "stgcmt" -> result = handleStorageCommit(rest);
                case "qido" -> result = handleQido(rest);
                case "stow" -> result = handleStow(rest);
                case "wado" -> result = handleWado(rest);
                case "sr", "sr-summary" -> result = handleStructuredReport(rest);
                case "rt-check" -> result = handleRtCheck(rest);
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

    private static OperationResult handleStore(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("store-scu requires <input> and --target host:port");
        }
        Path input = Paths.get(args[0]);
        String target = optionValue(args, "--target");
        if (target == null) {
            throw new IllegalArgumentException("store-scu requires --target host:port");
        }
        String[] parts = target.split(":");
        String host = parts[0];
        int port = parts.length > 1 ? Integer.parseInt(parts[1]) : 104;
        String calling = optionValue(args, "--calling");
        if (calling == null) calling = "STORE-SCU";
        String called = optionValue(args, "--called");
        if (called == null) called = "STORE-SCP";
        int timeout = optionInt(args, "--timeout", 2000);
        return DicomOperations.store(input, host, port, timeout, calling, called);
    }

    private static OperationResult handleStoreScp(String[] args) throws Exception {
        int port = optionInt(args, "--port", -1);
        if (port < 0) throw new IllegalArgumentException("store-scp requires --port");
        String aet = optionValue(args, "--aet");
        if (aet == null) aet = "STORE-SCP";
        String output = optionValue(args, "--output");
        if (output == null) throw new IllegalArgumentException("store-scp requires --output <dir>");
        int duration = optionInt(args, "--duration", 10);
        return DicomOperations.storeSCP(port, aet, Paths.get(output), duration);
    }

    private static OperationResult handleFind(String[] args, boolean worklist) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException((worklist ? "mwl" : "find") + " requires <host:port>");
        }
        String target = args[0];
        String[] parts = target.split(":");
        String host = parts[0];
        int port = parts.length > 1 ? Integer.parseInt(parts[1]) : 104;
        String calling = optionValue(args, "--calling");
        if (calling == null) calling = worklist ? "MWL-SCU" : "FIND-SCU";
        String called = optionValue(args, "--called");
        if (called == null) called = worklist ? "MWL-SCP" : "FIND-SCP";
        String level = worklist ? "WORKLIST" : optionValue(args, "--level");
        if (!worklist && level == null) level = "STUDY";
        Map<Integer, String> filters = new HashMap<>();
        String patient = optionValue(args, "--patient");
        if (patient != null) filters.put(Tag.PatientName, patient);
        String study = optionValue(args, "--study");
        if (study != null) filters.put(Tag.StudyInstanceUID, study);
        return DicomOperations.cfind(host, port, calling, called, level, filters, 2000);
    }

    private static OperationResult handleMove(String[] args) throws Exception {
        if (args.length == 0) throw new IllegalArgumentException("c-move requires <host:port>");
        String target = args[0];
        String dest = optionValue(args, "--dest");
        if (dest == null) throw new IllegalArgumentException("c-move requires --dest DEST_AET");
        String[] parts = target.split(":");
        String host = parts[0];
        int port = parts.length > 1 ? Integer.parseInt(parts[1]) : 104;
        String calling = optionValue(args, "--calling");
        if (calling == null) calling = "MOVE-SCU";
        String called = optionValue(args, "--called");
        if (called == null) called = "MOVE-SCP";
        Map<Integer, String> filters = new HashMap<>();
        String study = optionValue(args, "--study");
        if (study != null) filters.put(Tag.StudyInstanceUID, study);
        return DicomOperations.cmove(host, port, calling, called, dest, filters, 2000);
    }

    private static OperationResult handleGet(String[] args) throws Exception {
        if (args.length == 0) throw new IllegalArgumentException("c-get requires <host:port>");
        String target = args[0];
        String[] parts = target.split(":");
        String host = parts[0];
        int port = parts.length > 1 ? Integer.parseInt(parts[1]) : 104;
        String output = optionValue(args, "--output");
        if (output == null) throw new IllegalArgumentException("c-get requires --output <dir>");
        String calling = optionValue(args, "--calling");
        if (calling == null) calling = "GET-SCU";
        String called = optionValue(args, "--called");
        if (called == null) called = "GET-SCP";
        Map<Integer, String> filters = new HashMap<>();
        String study = optionValue(args, "--study");
        if (study != null) filters.put(Tag.StudyInstanceUID, study);
        return DicomOperations.cget(host, port, calling, called, filters, Paths.get(output), 2000);
    }

    private static OperationResult handleStorageCommit(String[] args) throws Exception {
        if (args.length == 0) throw new IllegalArgumentException("stgcmt requires <host:port>");
        String target = args[0];
        String files = optionValue(args, "--files");
        if (files == null) throw new IllegalArgumentException("stgcmt requires --files comma-separated list");
        String[] parts = target.split(":");
        String host = parts[0];
        int port = parts.length > 1 ? Integer.parseInt(parts[1]) : 104;
        String calling = optionValue(args, "--calling");
        if (calling == null) calling = "STGCMT-SCU";
        String called = optionValue(args, "--called");
        if (called == null) called = "STGCMT-SCP";
        List<Path> paths = Arrays.stream(files.split(","))
                .map(String::trim)
                .filter(s -> !s.isEmpty())
                .map(Paths::get)
                .toList();
        return DicomOperations.storageCommit(host, port, calling, called, paths, 2000);
    }

    private static OperationResult handleQido(String[] args) throws Exception {
        if (args.length == 0) throw new IllegalArgumentException("qido requires <url>");
        return DicomWebOperations.qido(args[0]);
    }

    private static OperationResult handleStow(String[] args) throws Exception {
        if (args.length < 2) throw new IllegalArgumentException("stow requires <url> <input>");
        Path input = Paths.get(args[1]);
        return DicomWebOperations.stow(input, args[0]);
    }

    private static OperationResult handleWado(String[] args) throws Exception {
        if (args.length == 0) throw new IllegalArgumentException("wado requires <url>");
        String output = optionValue(args, "--output");
        if (output == null) throw new IllegalArgumentException("wado requires --output <file>");
        return DicomWebOperations.wado(args[0], Paths.get(output));
    }

    private static OperationResult handleStructuredReport(String[] args) throws Exception {
        if (args.length == 0) {
            throw new IllegalArgumentException("sr-summary requires <input>");
        }
        Path input = Paths.get(args[0]);
        return DicomOperations.structuredReport(input);
    }

    private static OperationResult handleRtCheck(String[] args) throws Exception {
        String planOpt = optionValue(args, "--plan");
        String doseOpt = optionValue(args, "--dose");
        String structOpt = optionValue(args, "--struct");

        Path plan = planOpt != null ? Paths.get(planOpt) : (args.length > 0 ? Paths.get(args[0]) : null);
        if (plan == null) {
            throw new IllegalArgumentException("rt-check requires --plan <plan.dcm> (or first positional argument)");
        }
        Path dose = doseOpt != null ? Paths.get(doseOpt) : null;
        Path struct = structOpt != null ? Paths.get(structOpt) : null;

        return DicomOperations.rtConsistency(plan, dose, struct);
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
                  store-scu <input> --target host:port [--calling AET] [--called AET] [--timeout ms]
                  store-scp --port N [--aet AET] --output <dir> [--duration seconds]
                  find <host:port> --level patient|study|series [--called AET] [--calling AET] [--patient PAT] [--study STUDY_UID]
                  mwl <host:port> [--called AET] [--calling AET] [--patient PAT]
                  c-move <host:port> --dest DEST_AET [--called AET] [--calling AET] [--study STUDY_UID]
                  c-get <host:port> --output <dir> [--called AET] [--calling AET] [--study STUDY_UID]
                  stgcmt <host:port> --files <comma list> [--called AET] [--calling AET]
                  qido <url>
                  stow <url> <input>
                  wado <url> --output <file>
                  sr-summary <input>
                  rt-check --plan <plan.dcm> [--dose <dose.dcm>] [--struct <rtstruct.dcm>]
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
