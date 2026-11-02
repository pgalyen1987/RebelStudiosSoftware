#!/usr/bin/env node
/**
 * Finds and verifies a mate-in-one for the landing page's hero puzzle.
 *
 * The rules here are a line-for-line port of the shipped game's
 * CrossPlatformApps/OopsAllKnights/src/engine.ts (KNIGHT_DELTAS, isKingInCheck,
 * getValidMoves, hasLegalMove, statusFor). If that file changes, re-run this.
 * The point of the port is that the puzzle on the page is mate under the SAME
 * rules the game enforces, not under my memory of them. --verify re-checks the
 * position that is actually embedded in oops-all-knights.html.
 */
const SIZE = 8, FILES = 'abcdefgh';
const KD = [[-2,-1],[-2,1],[-1,-2],[-1,2],[1,-2],[1,2],[2,-1],[2,1]];
const col = p => p.startsWith('w') ? 'w' : 'b';
const name = (r,c) => FILES[c] + (SIZE - r);
const parse = sq => ({ row: SIZE - Number(sq[1]), col: FILES.indexOf(sq[0]) });
const clone = b => b.map(r => r.slice());
const empty = () => Array.from({length:SIZE}, () => Array(SIZE).fill(null));

function findKing(b, color) {
  for (let r=0;r<SIZE;r++) for (let c=0;c<SIZE;c++) if (b[r][c] === color+'K') return {row:r,col:c};
  return null;
}
function inCheck(b, color) {
  const k = findKing(b, color); if (!k) return false;
  const foe = color === 'w' ? 'b' : 'w';
  for (let r=0;r<SIZE;r++) for (let c=0;c<SIZE;c++) {
    const p = b[r][c]; if (!p || col(p) !== foe) continue;
    if (p[1] === 'N') { for (const [dr,dc] of KD) if (r+dr===k.row && c+dc===k.col) return true; }
    else if (Math.abs(r-k.row) <= 1 && Math.abs(c-k.col) <= 1) return true;
  }
  return false;
}
function pseudo(b, r, c) {
  const p = b[r][c]; if (!p) return [];
  const mine = col(p), out = [];
  const push = (nr,nc) => {
    if (nr<0||nr>=SIZE||nc<0||nc>=SIZE) return;
    const t = b[nr][nc]; if (!t || col(t) !== mine) out.push({row:nr,col:nc});
  };
  if (p[1] === 'N') for (const [dr,dc] of KD) push(r+dr, c+dc);
  else for (let dr=-1;dr<=1;dr++) for (let dc=-1;dc<=1;dc++) if (dr||dc) push(r+dr, c+dc);
  return out;
}
function legal(b, r, c) {
  const p = b[r][c]; if (!p) return [];
  return pseudo(b,r,c).filter(d => {
    const n = clone(b); n[d.row][d.col] = p; n[r][c] = null;
    return !inCheck(n, col(p));
  });
}
function allMoves(b, color) {
  const out = [];
  for (let r=0;r<SIZE;r++) for (let c=0;c<SIZE;c++) {
    const p = b[r][c]; if (!p || col(p) !== color) continue;
    for (const d of legal(b,r,c)) out.push({from:{row:r,col:c}, to:d, piece:p, captures:b[d.row][d.col]});
  }
  return out;
}
const apply = (b,m) => { const n = clone(b); n[m.to.row][m.to.col] = m.piece; n[m.from.row][m.from.col] = null; return n; };
function status(b, turn) {               // turn = side to move
  if (!findKing(b, turn)) return 'checkmate';
  const chk = inCheck(b, turn), can = allMoves(b, turn).length > 0;
  if (!can && chk) return 'checkmate';
  if (!can) return 'stalemate';
  return chk ? 'check' : 'playing';
}

/** Full report on a position with White to move. */
function analyse(board) {
  const wm = allMoves(board, 'w');
  const mates = [], others = [];
  for (const m of wm) {
    const after = apply(board, m);
    const st = status(after, 'b');
    const rec = { san: (m.piece[1]==='K'?'K':'N') + (m.captures?'x':'') + name(m.to.row,m.to.col),
                  from: name(m.from.row,m.from.col), to: name(m.to.row,m.to.col), piece: m.piece, st };
    if (st === 'checkmate') mates.push(rec);
    else {
      const replies = allMoves(after, 'b');
      // the most natural refutation to quote: take the piece that just moved, else step the king
      const take = replies.find(r => r.to.row===m.to.row && r.to.col===m.to.col);
      const kstep = replies.find(r => r.piece === 'bK');
      const r = take || kstep || replies[0];
      rec.reply = r ? (r.piece[1]==='K'?'K':'N') + (r.captures?'x':'') + name(r.to.row,r.to.col) : null;
      rec.replyKind = take ? 'take' : (r && r.piece === 'bK' ? 'king' : 'other');
      others.push(rec);
    }
  }
  return { mates, others,
    blackReplies: allMoves(board,'b').length,
    whiteInCheck: inCheck(board,'w'), blackInCheck: inCheck(board,'b') };
}

function show(board) {
  let s = '';
  for (let r=0;r<SIZE;r++) {
    s += (SIZE-r) + ' ';
    for (let c=0;c<SIZE;c++) s += (board[r][c] || '..') + ' ';
    s += '\n';
  }
  return s + '  ' + FILES.split('').map(f => ' '+f+' ').join('') + '\n';
}
function fromMap(map) {           // {e8:'bK', ...}
  const b = empty();
  for (const [sq, p] of Object.entries(map)) { const {row,col} = parse(sq); b[row][col] = p; }
  return b;
}

// ---- the position embedded in the page -------------------------------------
export const PUZZLE = {
  bK:['a6'], bN:['b7','f8','f7','g6'], wK:['h3'], wN:['e8','c6','d5'],
};
function puzzleBoard(p = PUZZLE) {
  const m = {};
  for (const sq of p.bK) m[sq]='bK'; for (const sq of p.bN) m[sq]='bN';
  for (const sq of p.wK) m[sq]='wK'; for (const sq of p.wN) m[sq]='wN';
  return fromMap(m);
}

// ---- search ----------------------------------------------------------------
function randomPosition(rng) {
  const sq = () => ({ row: Math.floor(rng()*8), col: Math.floor(rng()*8) });
  const b = empty();
  const place = (p) => { for (let i=0;i<60;i++) { const s = sq(); if (!b[s.row][s.col]) { b[s.row][s.col]=p; return s; } } return null; };
  const bk = place('bK'); if (!bk) return null;
  const wk = place('wK'); if (!wk) return null;
  if (Math.abs(bk.row-wk.row) <= 1 && Math.abs(bk.col-wk.col) <= 1) return null;
  const nb = 2 + Math.floor(rng()*3), nw = 2 + Math.floor(rng()*2);
  for (let i=0;i<nb;i++) place('bN');
  for (let i=0;i<nw;i++) place('wN');
  return b;
}
function mulberry(a){return function(){a|=0;a=a+0x6D2B79F5|0;let t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}

function search(seed, tries) {
  const rng = mulberry(seed), found = [];
  for (let i=0;i<tries;i++) {
    const b = randomPosition(rng); if (!b) continue;
    if (inCheck(b,'w') || inCheck(b,'b')) continue;          // quiet: nobody already in check
    const a = analyse(b);
    if (a.mates.length !== 1) continue;                       // exactly one answer
    if (a.mates[0].piece !== 'wN') continue;                   // a knight must deliver it
    const bn = b.flat().filter(p => p === 'bN').length;
    if (bn < 3) continue;                                      // black has knights that cannot interpose
    if (a.blackReplies < 10) continue;                          // position looks alive before the move
    found.push({ b, a, score: bn*10 + a.blackReplies });
  }
  found.sort((x,y) => y.score - x.score);
  return found;
}

const arg = process.argv[2];
if (arg === '--verify') {
  const b = puzzleBoard();
  const a = analyse(b);
  console.log(show(b));
  console.log('white in check:', a.whiteInCheck, ' black in check:', a.blackInCheck);
  console.log('black legal replies before White moves:', a.blackReplies);
  console.log('white legal moves:', a.mates.length + a.others.length);
  console.log('MATING MOVES:', a.mates.map(m => m.from+'-'+m.to+' '+m.san).join(', ') || '(none)');
  console.log('stalemates:', a.others.filter(o=>o.st==='stalemate').length,
              ' checks:', a.others.filter(o=>o.st==='check').length);
  const ok = a.mates.length === 1 && !a.whiteInCheck && !a.blackInCheck && a.mates[0].piece === 'wN';
  console.log(ok ? 'OK: exactly one mate in one, by a knight, from a quiet position' : 'FAIL');
  process.exit(ok ? 0 : 1);
} else if (arg === '--data') {
  const b = puzzleBoard(), a = analyse(b);
  console.log(JSON.stringify({ mate: a.mates[0], others: a.others }, null, 1));
} else if (arg === '--search') {
  const out = search(Number(process.argv[3]||1), Number(process.argv[4]||20000));
  console.log('candidates:', out.length);
  for (const f of out.slice(0,6)) {
    console.log(show(f.b));
    console.log('  mate:', f.mate || f.a.mates[0].from+'-'+f.a.mates[0].to,
                ' blackReplies:', f.a.blackReplies, ' whiteMoves:', f.a.mates.length+f.a.others.length, '\n');
  }
}

// --emit: the compact table the page embeds. Generated, never hand-typed, so the
// page cannot disagree with the engine about what happens after a move.
if (arg === '--emit') {
  const b = puzzleBoard(), a = analyse(b);
  const T = {};
  T[a.mates[0].from + a.mates[0].to] = { k: 'mate' };
  for (const o of a.others) T[o.from + o.to] = { k: o.replyKind === 'take' ? 'take' : (o.st === 'check' ? 'check' : 'quiet'), r: o.reply };
  const pos = {};
  for (const [k, sqs] of Object.entries(PUZZLE)) for (const s of sqs) pos[s] = k;
  console.log('const POS = ' + JSON.stringify(pos) + ';');
  console.log('const VERDICT = ' + JSON.stringify(T) + ';');
  console.log('// mate:', a.mates[0].from + '-' + a.mates[0].to, '| white moves:', a.mates.length + a.others.length, '| black replies:', a.blackReplies);
}
