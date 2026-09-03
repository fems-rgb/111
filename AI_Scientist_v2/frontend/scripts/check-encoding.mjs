import { readdir, readFile } from 'fs/promises';
import { join, extname } from 'path';

const EXTENSIONS = new Set(['.vue', '.ts', '.tsx', '.js', '.json']);
const SRC_DIR = 'src';

async function walk(dir) {
  const entries = await readdir(dir, { withFileTypes: true });
  const files = [];
  for (const e of entries) {
    const full = join(dir, e.name);
    if (e.isDirectory()) files.push(...await walk(full));
    else if (EXTENSIONS.has(extname(e.name))) files.push(full);
  }
  return files;
}

const files = await walk(SRC_DIR);
let hasError = false;

for (const f of files) {
  const buf = await readFile(f);
  if (buf[0] === 0xEF && buf[1] === 0xBB && buf[2] === 0xBF) {
    console.error('BOM detected: ' + f);
    hasError = true;
  }
}

if (hasError) {
  console.error('Please remove BOM from the above files.');
  process.exit(1);
} else {
  console.log('All files are clean UTF-8 without BOM');
}