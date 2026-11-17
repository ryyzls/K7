// Live DOM, fully intercepted booking transport: NEVER writes production bookings.
const assert = require('node:assert/strict');
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async()=>{
  const browser=await chromium.launch({headless:true});
  try {
    const page=await browser.newPage({reducedMotion:'reduce'});
    const requests=[];
    await page.route('**/api/booking',async route=>{
      const request=route.request();
      assert.equal(request.method(),'POST');
      requests.push({key:request.headers()['idempotency-key'],body:request.postDataJSON()});
      if(requests.length===1) return route.abort('failed');
      if(requests.length===2) return route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({detail:'Synthetic unavailable'})});
      await new Promise(r=>setTimeout(r,200));
      return route.fulfill({status:201,contentType:'application/json',body:JSON.stringify({kode_booking:'SYNTHETIC-NOT-STORED',jenis_kamar:'VIP',tanggal_masuk:'2099-01-01'})});
    });
    await page.goto('http://127.0.0.1:8000');
    await page.waitForSelector('.card');
    await page.locator('#list .card-main').first().click();
    const form=page.locator('#booking-form');
    async function fill(name){
      await form.locator('[name=nama_pasien]').fill(name);
      await form.locator('[name=no_telp]').fill('000000');
      await form.locator('[name=jenis_kamar]').selectOption('VIP');
      await form.locator('[name=tanggal_masuk]').fill('2099-01-01');
    }
    async function submit(twice=false){
      await form.evaluate((f,twice)=>{f.requestSubmit();if(twice)f.requestSubmit()},twice);
      await page.waitForFunction(()=>!document.querySelector('#booking-form button[type=submit]').disabled);
    }
    await fill('SYNTHETIC A');await submit();await submit();
    assert.equal(requests.length,2);assert.equal(requests[0].key,requests[1].key);
    assert.match(requests[0].key,/^[a-f0-9-]{36}$/);
    console.log('PASS network failure + 503 retry retains key');
    await fill('SYNTHETIC B');await submit(true);
    assert.equal(requests.length,3);assert.notEqual(requests[1].key,requests[2].key);
    console.log('PASS changed payload gets new key; simultaneous submit sends once');
    await fill('SYNTHETIC B');await submit();
    assert.equal(requests.length,4);assert.notEqual(requests[2].key,requests[3].key);
    console.log('PASS new operation after success gets new key; no production writes');
  } finally {await browser.close()}
})().catch(e=>{console.error(e.stack);process.exitCode=1});
