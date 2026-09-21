// Use the pinned Canny ledger library; does not install hooks or call JEV.
import { readFileSync } from 'node:fs';
import { append, read, summarize } from './upstream/canny/dist/ledger.js';

const [input, ledger] = process.argv.slice(2);
if (!input || !ledger) throw new Error('usage: node canny_evidence.mjs events.json ledger.jsonl');
const events = JSON.parse(readFileSync(input, 'utf8'));
for (const entry of events) append(ledger, entry);
const summary = summarize(read(ledger));
console.log(JSON.stringify({ component: 'qkal/Canny', verification_after_last_edit: summary.verified !== null,
  edited_files: summary.codeFiles, failed_command_groups: Object.keys(summary.repeats).length }));
