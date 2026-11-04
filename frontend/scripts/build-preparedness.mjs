// Generate an exact integrity-pinned minimal shell allowlist after Vite builds.
import { readFile, writeFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { resolve } from 'node:path';
const root = fileURLToPath(new URL('../', import.meta.url));
const dist = resolve(root, 'dist');
const manifest = JSON.parse(await readFile(resolve(dist, '.vite/manifest.json'), 'utf8'));
const files = new Set(['preparedness/index.html', 'preparedness/kit.txt']);
function visit(key) {
  const entry = manifest[key];
  if (!entry) throw new Error('Missing preparedness entry');
  files.add(entry.file);
  for (const css of entry.css ?? []) files.add(css);
  for (const dependency of entry.imports ?? []) visit(dependency);
}
visit('preparedness/index.html');
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const allowlist = {};
for (const file of [...files].sort()) {
  if (!file.startsWith('assets/') && !['preparedness/index.html','preparedness/kit.txt'].includes(file)) throw new Error('Unapproved shell asset');
  allowlist['/' + file] = digest(await readFile(resolve(dist, file)));
}
allowlist['/preparedness/'] = allowlist['/preparedness/index.html'];
const template = await readFile(resolve(root, 'scripts/preparedness-worker.js'), 'utf8');
const version = digest(JSON.stringify(allowlist) + template).slice(0, 20);
await writeFile(resolve(dist, 'preparedness/service-worker.js'),
  'const ALLOW = ' + JSON.stringify(allowlist) + ';\nconst CACHE = "gridguide-preparedness-' + version + '";\n' + template);
await writeFile(resolve(dist, 'preparedness/cache-manifest.json'), JSON.stringify({ version, allowlist }, null, 2));
console.log('Preparedness shell:', Object.keys(allowlist).length, 'integrity-pinned entries;', version);
