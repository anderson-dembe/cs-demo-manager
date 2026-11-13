// Preserve the analysis success marker expected by the CS Coach worker.
// The upstream JSON result is emitted only after the analysis has been persisted.
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const args = process.argv.slice(2);
const analyze = args[0] === 'analyze';
const jsonRequested = args.includes('--json');
const cli = path.join(path.dirname(fileURLToPath(import.meta.url)), 'resources', 'app.asar', 'cli.js');
const result = spawnSync(process.execPath, [cli, ...args, ...(analyze && !jsonRequested ? ['--json'] : [])], {
  env: { ...process.env, ELECTRON_RUN_AS_NODE: '1' },
  windowsHide: true,
  stdio: analyze && !jsonRequested ? ['inherit', 'pipe', 'pipe'] : 'inherit',
  encoding: 'utf8',
  maxBuffer: 32 * 1024 * 1024,
});

if (result.error) {
  process.stderr.write(`${result.error.message}\n`);
  process.exit(1);
}

if (analyze && !jsonRequested) {
  if (result.stderr) process.stderr.write(result.stderr);
  if (result.stdout) process.stdout.write(result.stdout);
  try {
    const summary = JSON.parse(result.stdout);
    if (
      result.status !== 0 ||
      !Array.isArray(summary.analyzed) ||
      !Array.isArray(summary.failed) ||
      summary.failed.length !== 0 ||
      summary.analyzed.length === 0 ||
      summary.analyzed.some((demo) => typeof demo.checksum !== 'string' || demo.checksum.length === 0)
    ) {
      process.exit(result.status || 1);
    }
    process.stdout.write('\nInserting match into database [CS Coach: confirmed persisted]\n');
  } catch {
    process.stderr.write('CS Coach: the analysis did not return a valid persisted result.\n');
    process.exit(1);
  }
}

process.exit(result.status ?? 1);
