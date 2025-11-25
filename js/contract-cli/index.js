#!/usr/bin/env node
/**
 * Contract-compliant JS CLI shim.
 * For now it forwards operations to the Python backend so the Tkinter UI can invoke a JS binary.
 */

const { spawnSync } = require("child_process");
const path = require("path");

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--op") args.op = argv[++i];
    else if (arg === "--input") args.input = argv[++i];
    else if (arg === "--output") args.output = argv[++i];
    else if (arg === "--options") args.options = argv[++i];
    else if (arg === "--help" || arg === "-h") args.help = true;
  }
  if (args.options) {
    try {
      args.options = JSON.parse(args.options);
    } catch (err) {
      console.error(JSON.stringify({ ok: false, returncode: 1, stderr: `Invalid JSON in --options: ${err.message}` }));
      process.exit(1);
    }
  } else {
    args.options = {};
  }
  return args;
}

function usage() {
  console.log("Usage: node index.js --op <op> --input <path> [--output <path>] [--options '{\"k\":\"v\"}']");
  process.exit(1);
}

function run() {
  const args = parseArgs(process.argv);
  if (args.help || !args.op) usage();

  const backingCmd = process.env.BACKING_CMD || "python -m DICOM_reencoder.cli";
  const parts = backingCmd.split(" ");
  const cmd = parts.shift();
  const baseArgs = parts;

  const input = args.input;
  const output = args.output;
  const opt = args.options || {};

  const map = {
    info: () => baseArgs.concat(["info", input, "--json"]),
    anonymize: () => baseArgs.concat(["anonymize", input, "-o", output || inferredOutput("_anon.dcm", input)]),
    to_image: () => {
      const fmt = opt.format || "png";
      const out = output || inferredOutput(fmt === "jpeg" ? ".jpg" : ".png", input);
      const res = baseArgs.concat(["to_image", input, "--format", fmt, "-o", out]);
      if (opt.frame != null) res.push("--frame", String(opt.frame));
      return res;
    },
    transcode: () => {
      const syntax = opt.syntax || "explicit";
      const out = output || inferredOutput("_transcoded.dcm", input);
      return baseArgs.concat(["transcode", input, "--syntax", syntax, "-o", out]);
    },
    validate: () => baseArgs.concat(["validate", input, "--json"]),
    stats: () => baseArgs.concat(["stats", input]),
    dump: () => baseArgs.concat(["info", input, "--json", "--verbose"]),
    volume: () => {
      const out = output || path.join("output", "volume.npy");
      const res = baseArgs.concat(["volume", input, "-o", out]);
      if (opt.preview) res.push("--preview");
      return res;
    },
    nifti: () => {
      const out = output || path.join("output", "volume.nii.gz");
      const res = baseArgs.concat(["nifti", input, "-o", out]);
      if (opt.series_uid) res.push("--series-uid", opt.series_uid);
      if (opt.no_compress) res.push("--no-compress");
      return res;
    },
    echo: () => {
      const host = opt.host || "127.0.0.1";
      const port = opt.port || 11112;
      return baseArgs.concat(["echo", `${host}`, "--port", String(port)]);
    },
  };

  if (!map[args.op]) {
    console.error(JSON.stringify({ ok: false, returncode: 1, stderr: `Unsupported op: ${args.op}` }));
    process.exit(1);
  }

  const child = spawnSync(cmd, map[args.op](), { encoding: "utf-8" });
  const stdout = child.stdout || "";
  const stderr = child.stderr || "";
  const outputFiles = [];

  if (output) outputFiles.push(output);

  const payload = {
    ok: child.status === 0,
    returncode: child.status ?? 1,
    stdout,
    stderr,
    output_files: outputFiles,
    metadata: null,
  };

  console.log(JSON.stringify(payload, null, 2));
  process.exit(child.status || 0);
}

function inferredOutput(suffix, inputPath) {
  if (!inputPath) return suffix;
  const p = path.parse(inputPath);
  return path.join(p.dir || ".", `${p.name}${suffix}`);
}

run();
