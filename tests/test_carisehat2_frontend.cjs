const test = require("node:test");
const assert = require("node:assert");
const fs = require("node:fs");
const path = require("node:path");

const htmlPath = path.resolve(__dirname, "../frontend/index.html");
const html = fs.readFileSync(htmlPath, "utf8");

test("Fitur 1: Filter select #lay contains optgroup and specialty options", () => {
  assert.ok(html.includes('id="lay"'), "Select element #lay must exist");
  assert.ok(
    html.includes("Spesialisasi Medis Terlapor (SIRS)"),
    "Optgroup for SIRS reported specialties must exist in loadFilterOptions"
  );
  assert.ok(
    html.includes("Layanan Diagnostik &amp; Penunjang") || html.includes("Layanan Diagnostik"),
    "Optgroup for diagnostic services must exist"
  );
});

test("Fitur 2: Compare dock and modal dialog markup exist", () => {
  assert.ok(html.includes('id="compare-modal-wrap"'), "Modal wrap #compare-modal-wrap must exist");
  assert.ok(html.includes('id="compare-modal-title"'), "Modal title must exist");
  assert.ok(html.includes('id="compare-dock"'), "Floating dock #compare-dock must exist");
  assert.ok(html.includes('id="btn-dock-open-compare"'), "Dock open button must exist");
  assert.ok(html.includes('data-act="compare-toggle"'), "Action compare-toggle must be supported");
});

test("Fitur 3: Alternatives section exists in detail template", () => {
  assert.ok(html.includes('id="sec-alternatif"'), "Section #sec-alternatif must exist in detail view");
  assert.ok(
    html.includes('id="d-alternatives-container"'),
    "Alternatives container #d-alternatives-container must exist"
  );
  assert.ok(
    html.includes("loadAlternatives"),
    "Function loadAlternatives must be present"
  );
});

test("Fitur 4: Complete profile displays Kode Kemenkes and UGD indicators", () => {
  assert.ok(
    html.includes("Kode Registrasi Kemenkes"),
    "Detail sheet must render Kode Registrasi Kemenkes"
  );
  assert.ok(
    html.includes("UGD 24 Jam Terlapor SIRS"),
    "Detail sheet must render UGD 24 Jam status"
  );
  assert.ok(
    html.includes("Spesialisasi Medis Terlapor SIRS"),
    "Detail sheet must render reported medical specialties"
  );
});

test("Responsive UI: Compare dock and dialog styles support mobile 375px & desktop", () => {
  assert.ok(html.includes(".compare-dock"), "CSS for .compare-dock must exist");
  assert.ok(html.includes(".compare-modal-dialog"), "CSS for .compare-modal-dialog must exist");
  assert.ok(html.includes(".compare-table-wrap"), "CSS for scrollable compare table must exist");
  assert.ok(html.includes(".d-alternatives-grid"), "CSS for .d-alternatives-grid must exist");
});
