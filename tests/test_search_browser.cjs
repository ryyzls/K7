const { chromium } = require("playwright");
const assert = require("node:assert");

const BASE_URL = "http://127.0.0.1:8000";

async function run() {
  const browser = await chromium.launch({ headless: true, channel: "msedge" });
  const consoleErrors = [];
  const pageErrors = [];

  try {
    const context = await browser.newContext({ viewport: { width: 1280, height: 800 } });
    const page = await context.newPage();
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });
    page.on("pageerror", (err) => pageErrors.push(err.message));

    console.log("1. Navigating to /pencarian (Desktop 1280x800)...");
    await page.goto(`${BASE_URL}/pencarian`, { waitUntil: "networkidle", timeout: 20000 });
    await page.waitForSelector("#search-input", { timeout: 10000 });
    await page.waitForSelector("#list li", { timeout: 10000 });

    // Check initial 206 total count text
    const bodyText = await page.locator("aside").innerText();
    assert.ok(bodyText.includes("206 rumah sakit ditemukan"), `Expected 206 hospitals initially, got: ${bodyText.slice(0, 200)}`);

    // 2. Test Autocomplete ("jan")
    console.log("2. Testing autocomplete for 'jan'...");
    const input = page.locator("#search-input");
    await input.fill("jan");
    await page.waitForSelector('[role="listbox"] [role="option"]', { timeout: 5000 });
    const optionsCount = await page.locator('[role="listbox"] [role="option"]').count();
    assert.ok(optionsCount >= 3, `Expected >= 3 autocomplete options for 'jan', got ${optionsCount}`);

    // Click first suggestion
    await page.locator('[role="listbox"] [role="option"] button').first().click();
    await page.waitForTimeout(600);
    await page.waitForSelector("#list li", { timeout: 10000 });

    // 3. Test Natural Language + Auto Filter Extraction ("RS kelas B di Medan yang punya ICU")
    console.log("3. Testing NL query + auto filter chips...");
    await input.fill("RS kelas B di Medan yang punya ICU");
    await page.waitForTimeout(600);
    await page.waitForFunction(
      () => document.body.innerText.includes("rumah sakit ditemukan") && !document.body.innerText.includes("Mencari rumah sakit..."),
      { timeout: 10000 }
    );
    const chipsCount = await page.locator('button[aria-label^="Hapus filter"]').count();
    assert.ok(chipsCount >= 3, `Expected >= 3 recognized filter chips, got ${chipsCount}`);

    // Remove one chip
    await page.locator('button[aria-label^="Hapus filter"]').first().click();
    await page.waitForTimeout(500);

    // 4. Test Typo Correction ("Jantng di Medn")
    console.log("4. Testing typo correction ('Jantng di Medn')...");
    await input.fill("Jantng di Medn");
    await page.waitForFunction(
      () => document.body.innerText.includes("Menampilkan hasil untuk") || document.body.innerText.includes("38 rumah sakit ditemukan"),
      { timeout: 10000 }
    );
    const textAfterTypo = await page.locator("aside").innerText();
    assert.ok(textAfterTypo.includes("38 rumah sakit ditemukan"), `Expected 38 results for 'Jantng di Medn', got: ${textAfterTypo.slice(0, 300)}`);

    // 5. Test Empty State ("xyzzy_tidak_ada_rs")
    console.log("5. Testing empty state...");
    await input.fill("xyzzy_tidak_ada_rs");
    await page.waitForFunction(() => document.body.innerText.includes("Tidak ada hasil"), { timeout: 10000 });

    // 6. Test Reset Filter + Pagination (no duplicates across pages)
    console.log("6. Testing Reset Filter & Pagination...");
    await page.locator("#reset").click();
    await page.waitForFunction(() => document.body.innerText.includes("206 rumah sakit ditemukan"), { timeout: 10000 });
    const page1Names = await page.locator("#list h3").allInnerTexts();
    await page.locator('button[aria-label="Halaman berikutnya"]').click();
    await page.waitForTimeout(200);
    const page2Names = await page.locator("#list h3").allInnerTexts();
    const overlap = page1Names.filter((n) => page2Names.includes(n));
    assert.strictEqual(overlap.length, 0, `Pagination duplicate found: ${overlap}`);

    // 7. Test Mobile Viewport (375x812) - search bar & autocomplete fit within viewport
    console.log("7. Testing Mobile viewport (375x812)...");
    await page.setViewportSize({ width: 375, height: 812 });
    await input.fill("Adam Malik");
    await page.waitForFunction(() => document.body.innerText.includes("1 rumah sakit ditemukan"), { timeout: 10000 });
    const searchBoxFits = await page.evaluate(() => {
      const el = document.querySelector("#search-input");
      const r = el.getBoundingClientRect();
      return r.left >= 0 && r.right <= window.innerWidth + 1;
    });
    assert.strictEqual(searchBoxFits, true, "Search input overflows mobile 375px viewport");

    // 8. Check zero console/page errors
    assert.strictEqual(consoleErrors.length, 0, `Console errors: ${consoleErrors.join("; ")}`);
    assert.strictEqual(pageErrors.length, 0, `Page errors: ${pageErrors.join("; ")}`);

    console.log("ALL BROWSER TESTS PASSED!");
  } finally {
    await browser.close();
  }
}

run().catch((err) => {
  console.error("BROWSER TEST FAILED:", err);
  process.exit(1);
});
