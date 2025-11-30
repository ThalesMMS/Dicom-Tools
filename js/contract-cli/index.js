#!/usr/bin/env node
/**
 * Contract-compliant JS CLI shim.
 * Delegates to the TypeScript build in dist/index.js.
 */
const { run } = require('./dist/index.js');

if (typeof run === 'function') {
  run();
} else {
  console.error('contract-cli: missing run() export from dist build');
  process.exit(1);
}
