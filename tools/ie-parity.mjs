/* Proves tools/ie.js agrees with includes/IE.php from Checkout Brasil Pro.
 *
 * Two files implementing the same 27 rules WILL drift. This runs both against the 24 worked
 * examples published by the states, and against a large sweep of generated numbers, and fails on
 * the first disagreement. Run it after touching either file:
 *     node tools/ie-parity.mjs
 */
import { execFileSync } from 'node:child_process';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
const IE = require('./ie.js');

const PHP = '/home/me/SAAS/checkout-brasil-pro/includes/IE.php';

/** Ask the PHP implementation, in one batch. */
function php(pairs) {
  const script = `<?php define('ABSPATH',1); require '${PHP}';
use RebelStudios\\CheckoutBrasilPro\\IE;
$in = json_decode(file_get_contents('php://stdin'), true);
$out = [];
foreach ($in as $p) { $out[] = IE::is_valid($p[0], $p[1]) ? 1 : 0; }
echo json_encode($out);`;
  return JSON.parse(execFileSync('php', ['-r', script.replace(/^<\?php\s*/, '')],
    { input: JSON.stringify(pairs), encoding: 'utf8', maxBuffer: 1 << 24 }));
}

const SINTEGRA = [
  ['0100482300112','AC'],['240000048','AL'],['030123459','AP'],['12345663','BA'],
  ['61234557','BA'],['100000306','BA'],['060000015','CE'],['109876547','GO'],
  ['120000385','MA'],['0623079040081','MG'],['00130000019','MT'],['159999995','PA'],
  ['750000023','PA'],['032141840','PE'],['18100100000049','PE'],['1234567850','PR'],
  ['200400401','RN'],['2000400400','RN'],['00000000625213','RO'],['240061536','RR'],
  ['2243658792','RS'],['251040852','SC'],['110042490114','SP'],['29010227836','TO'],
];

let fail = 0;

// 1. the published examples must be valid in BOTH implementations
const a = php(SINTEGRA.map(([n, uf]) => [n, uf]));
SINTEGRA.forEach(([n, uf], i) => {
  const js = IE.isValid(n, uf), ph = !!a[i];
  if (!js || !ph) { fail++; console.log(`  FAIL ${uf} ${n}: js=${js} php=${ph} (both must be true)`); }
});
console.log(`  ${SINTEGRA.length} published examples checked in both implementations`);

// 2. a wide sweep: every state, many shapes, including junk. Any disagreement at all is a bug.
const pairs = [];
const rnd = (n) => Array.from({ length: n }, () => Math.floor(Math.random() * 10)).join('');
for (const uf of IE.STATES) {
  for (const len of [7, 8, 9, 10, 11, 12, 13, 14]) {
    for (let k = 0; k < 40; k++) pairs.push([rnd(len), uf]);
  }
  pairs.push(['ISENTO', uf], ['isenta', uf], ['', uf], ['abc', uf]);
}
pairs.push(['123456789', 'ZZ'], ['ISENTO', 'XX']);

const phpOut = php(pairs);
let agree = 0;
pairs.forEach(([n, uf], i) => {
  const js = IE.isValid(n, uf), ph = !!phpOut[i];
  if (js !== ph) { fail++; if (fail < 8) console.log(`  FAIL ${uf} "${n}": js=${js} php=${ph}`); }
  else agree++;
});
console.log(`  ${pairs.length} generated cases checked, ${agree} agreed`);

console.log(fail ? `\n${fail} DISAGREEMENTS — the two implementations have drifted` : '\nPHP and JS agree on every case');
process.exit(fail ? 1 : 0);
