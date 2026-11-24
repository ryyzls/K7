// Pure JS ISO/IEC 18004 Version 3-L (29x29) QR Code SVG Encoder
const GF_EXP = new Uint8Array(512);
const GF_LOG = new Uint8Array(256);
(() => {
  let x = 1;
  for (let i = 0; i < 255; i++) {
    GF_EXP[i] = x;
    GF_LOG[x] = i;
    x <<= 1;
    if (x & 0x100) x ^= 0x11d;
  }
  for (let i = 255; i < 512; i++) GF_EXP[i] = GF_EXP[i - 255];
})();

function gfMul(a, b) {
  return a === 0 || b === 0 ? 0 : GF_EXP[GF_LOG[a] + GF_LOG[b]];
}

function rsGeneratorPoly(degree) {
  let poly = [1];
  for (let i = 0; i < degree; i++) {
    const next = new Array(poly.length + 1).fill(0);
    const factor = GF_EXP[i];
    for (let j = 0; j < poly.length; j++) {
      next[j] ^= poly[j];
      next[j + 1] ^= gfMul(poly[j], factor);
    }
    poly = next;
  }
  return poly;
}

function rsEncode(data, ecCount) {
  const gen = rsGeneratorPoly(ecCount);
  const res = new Uint8Array(data.length + ecCount);
  res.set(data);
  for (let i = 0; i < data.length; i++) {
    const coef = res[i];
    if (coef !== 0) {
      for (let j = 0; j < gen.length; j++) {
        res[i + j] ^= gfMul(gen[j], coef);
      }
    }
  }
  return res.slice(data.length);
}

export function buildQrMatrix(text) {
  const raw = new TextEncoder().encode(String(text || 'CARISEHAT').slice(0, 50));
  const dataCap = 55; // Version 3-L data codewords
  const ecCount = 15; // Version 3-L EC codewords

  const bits = [];
  const pushBits = (val, len) => {
    for (let i = len - 1; i >= 0; i--) bits.push((val >> i) & 1);
  };

  pushBits(0b0100, 4); // Byte mode
  pushBits(raw.length, 8);
  for (const b of raw) pushBits(b, 8);
  pushBits(0, Math.min(4, dataCap * 8 - bits.length));
  while (bits.length % 8 !== 0) bits.push(0);

  const codewords = [];
  for (let i = 0; i < bits.length; i += 8) {
    let byte = 0;
    for (let b = 0; b < 8; b++) byte = (byte << 1) | bits[i + b];
    codewords.push(byte);
  }
  const pads = [0xec, 0x11];
  let padIdx = 0;
  while (codewords.length < dataCap) {
    codewords.push(pads[padIdx % 2]);
    padIdx++;
  }

  const ec = rsEncode(codewords, ecCount);
  const fullBytes = [...codewords, ...ec];
  const stream = [];
  for (const byte of fullBytes) {
    for (let b = 7; b >= 0; b--) stream.push((byte >> b) & 1);
  }

  const size = 29;
  const grid = Array.from({ length: size }, () => new Array(size).fill(null));
  const reserved = Array.from({ length: size }, () => new Array(size).fill(false));

  const placeFinder = (ox, oy) => {
    for (let dy = -1; dy <= 7; dy++) {
      for (let dx = -1; dx <= 7; dx++) {
        const x = ox + dx;
        const y = oy + dy;
        if (x < 0 || y < 0 || x >= size || y >= size) continue;
        const inOuter = dx >= 0 && dx <= 6 && dy >= 0 && dy <= 6;
        const inCore = dx >= 2 && dx <= 4 && dy >= 2 && dy <= 4;
        const onBorder = dx === 0 || dx === 6 || dy === 0 || dy === 6;
        grid[y][x] = inOuter && (inCore || onBorder) ? 1 : 0;
        reserved[y][x] = true;
      }
    }
  };

  placeFinder(0, 0);
  placeFinder(size - 7, 0);
  placeFinder(0, size - 7);

  // Alignment pattern at (22, 22)
  for (let dy = -2; dy <= 2; dy++) {
    for (let dx = -2; dx <= 2; dx++) {
      const x = 22 + dx;
      const y = 22 + dy;
      grid[y][x] = Math.max(Math.abs(dx), Math.abs(dy)) === 2 || (dx === 0 && dy === 0) ? 1 : 0;
      reserved[y][x] = true;
    }
  }

  // Timing patterns
  for (let i = 8; i < size - 8; i++) {
    const bit = i % 2 === 0 ? 1 : 0;
    grid[6][i] = bit;
    reserved[6][i] = true;
    grid[i][6] = bit;
    reserved[i][6] = true;
  }

  // Dark module & reserve format info
  grid[21][8] = 1;
  reserved[21][8] = true;
  for (let i = 0; i < 9; i++) {
    if (i !== 6) {
      reserved[8][i] = true;
      reserved[i][8] = true;
    }
  }
  for (let i = 0; i < 8; i++) {
    reserved[8][size - 1 - i] = true;
    if (i < 7) reserved[size - 1 - i][8] = true;
  }

  // Zigzag placement + Mask 0 ((r + c) % 2 === 0)
  let bitIdx = 0;
  let upward = true;
  for (let col = size - 1; col > 0; col -= 2) {
    if (col === 6) col--;
    for (let step = 0; step < size; step++) {
      const r = upward ? size - 1 - step : step;
      for (let dc = 0; dc < 2; dc++) {
        const c = col - dc;
        if (!reserved[r][c]) {
          const rawBit = bitIdx < stream.length ? stream[bitIdx++] : 0;
          grid[r][c] = (r + c) % 2 === 0 ? rawBit ^ 1 : rawBit;
        }
      }
    }
    upward = !upward;
  }

  // Format info Level L + Mask 0 = 0x77C4 (111011111000100)
  const fmt = 0x77c4;
  const fBits = Array.from({ length: 15 }, (_, i) => (fmt >> (14 - i)) & 1);
  const coords1 = [
    [8, 0], [8, 1], [8, 2], [8, 3], [8, 4], [8, 5], [8, 7], [8, 8],
    [7, 8], [5, 8], [4, 8], [3, 8], [2, 8], [1, 8], [0, 8],
  ];
  const coords2 = [
    [size - 1, 8], [size - 2, 8], [size - 3, 8], [size - 4, 8], [size - 5, 8], [size - 6, 8], [size - 7, 8],
    [8, size - 8], [8, size - 7], [8, size - 6], [8, size - 5], [8, size - 4], [8, size - 3], [8, size - 2], [8, size - 1],
  ];
  fBits.forEach((b, i) => {
    grid[coords1[i][0]][coords1[i][1]] = b;
    grid[coords2[i][0]][coords2[i][1]] = b;
  });

  return grid;
}
