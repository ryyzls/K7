const fs = require('node:fs'), vm = require('node:vm'), assert = require('node:assert/strict');
const html = fs.readFileSync(require('node:path').join(__dirname, '../frontend/index.html'), 'utf8');
for(const m of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) new vm.Script(m[1]);
const context = vm.createContext({URL, IC:{web:'<svg aria-hidden="true"></svg>'}, esc:s=>String(s).replaceAll('&','&amp;').replaceAll('"','&quot;').replaceAll('<','&lt;')});
vm.runInContext(html.slice(html.indexOf('function officialWebsiteUrl'), html.indexOf('/* ============ Util & state')), context);
const valid = {website:'https://rsham.go.id/',website_status:'verified',website_evidence:'https://rsham.go.id/profil/hubungi-kami',website_checked_at:'2026-11-19'};
const rendered = context.renderOfficialWebsite(valid);
assert.match(rendered,/Website Resmi RS/);
assert.match(rendered,/target="_blank" rel="noopener noreferrer"/);
for(const website of ['javascript:alert(1)','data:text/html,test','//evil.com','http://localhost','http://127.0.0.1','http://[::1]','http://2130706433','https://user@example.com']) {
  assert.doesNotMatch(context.renderOfficialWebsite({...valid,website}),/<a /);
}
for(const status of ['needs_review','unreviewed','not_found',undefined]) {
  const result=context.renderOfficialWebsite({...valid,website_status:status});
  assert.doesNotMatch(result,/<a /);
  assert.match(result,/Website resmi belum tersedia/);
}
const location=html.indexOf('${esc(h.kabkota)}, Provinsi Sumatera Utara');
const website=html.indexOf('${renderOfficialWebsite(h)}',location);
const route=html.indexOf('Petunjuk Rute Cepat',location);
const phone=html.indexOf('Hubungi Hotline',location);
assert.ok(location < website && website < route && route < phone);
assert.match(html, /\.rs-website a:focus-visible/);
assert.match(html, /\.rs-website\s*\{[^}]*overflow-wrap:\s*anywhere/);
assert.match(html.slice(website,phone),/data-act="route"/);
console.log('Website UI: URL/status gates, placement, tab security, focus/mobile CSS, route/hotline markup and JS syntax passed.');
