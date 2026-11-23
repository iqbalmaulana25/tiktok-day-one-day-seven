// Entry program for the make.fun "Day one, day seven" TikTok bounty
// (post-tiktok-day-one-day-seven-20261123-0327). Node 22, standard library only.
//
// The entry itself is the TikTok video; this program's whole job is to hand
// the grader the video's address. It reads VIDEO.json from the repository
// root (the bot directory), checks that it parses (a file that does not
// parse can never be an entry), and copies it byte for byte to VIDEO.json
// in the output directory, where the gate reads it. A url that is not a
// TikTok video address — the starter placeholder, say — earns a warning
// here but is still copied: refusing it is the gate's call, not this
// program's, and the same program must run unchanged before and after the
// real address is filled in. Nothing here is scored: the house reads the
// video's counts from TikTok itself.
//
// Outside the grader's container, MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR
// stand in for /bot and /output:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const botDir = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const outputDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

const sourcePath = join(botDir, 'VIDEO.json');
const targetPath = join(outputDir, 'VIDEO.json');

let record: unknown;
try {
  record = JSON.parse(readFileSync(sourcePath, 'utf8'));
} catch (err) {
  console.error(`VIDEO.json could not be read or parsed at ${sourcePath}: ${(err as Error).message}`);
  process.exit(1);
}

const url = (record as { url?: unknown } | null)?.url;
if (typeof url !== 'string' || !/^https:\/\/(www\.|m\.)?tiktok\.com\/@[^/]+\/video\/\d+$/.test(url)) {
  console.error(`warning: VIDEO.json at ${sourcePath} does not yet name a TikTok video address ({"url": "https://www.tiktok.com/@<handle>/video/<id>"}); copying it as it stands.`);
}

mkdirSync(outputDir, { recursive: true });
copyFileSync(sourcePath, targetPath);
