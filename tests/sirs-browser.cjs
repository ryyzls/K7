const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({channel:'chrome',headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:900}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/api/booking**',r=>['GET','HEAD'].includes(r.request().method())?r.continue():r.abort());
  const results=[];
  try{
    await page.goto('http://127.0.0.1:8000/',{waitUntil:'domcontentloaded'});
    await page.locator('#list .card-main').first().waitFor({timeout:45000});
    const choices=await page.locator('#lay option').allTextContents();
    assert.equal(choices.length,36);
    assert.ok(!choices.includes('Pelayanan medik dasar / umum'));
    results.push('PASS 35 curated service choices; clinical labels withheld');
    const value=await page.locator('#lay option').nth(1).getAttribute('value');
    const responsePromise=page.waitForResponse(r=>r.url().includes('/api/search?') && new URL(r.url()).searchParams.get('layanan')===value);
    await page.locator('#lay').selectOption(value);
    const response=await responsePromise;
    assert.equal(response.status(),200);
    const data=await response.json();assert.ok(data.items.length);
    assert.ok(data.items.every(h=>h.layanan.includes(value)));
    await page.waitForFunction(()=>document.querySelectorAll('#list .card-main').length>0);
    await page.locator('#list .card-main').first().click();
    await page.locator('#detail.show').waitFor();
    const services=page.locator('#sec-layanan');
    assert.match(await services.textContent(),/SIRS/);
    await services.locator('summary').click();
    assert.ok(await services.locator('a[href^="https://sirs.kemkes.go.id/"]').count());
    assert.match(await services.textContent(),/belum diverifikasi operasional/);
    results.push('PASS live service filter and detail provenance');
    assert.ok(await page.evaluate(()=>typeof L !== 'undefined' && document.querySelector('#map .leaflet-pane')!==null));
    results.push('PASS Leaflet map initialized');
    const chat=await page.request.post('http://127.0.0.1:8000/api/chat',{data:{text:'layanan RS Umum Pusat H. Adam Malik'}});
    assert.equal(chat.status(),200);
    assert.match((await chat.json()).text,/SIRS/);
    results.push('PASS deterministic chatbot identifies reported SIRS source');
    assert.deepEqual(errors,[]);
    results.push('PASS no uncaught JavaScript errors');
  }catch(e){results.push('FAIL '+e.message);process.exitCode=1;}
  finally{await browser.close();fs.mkdirSync('docs/sirs-tests',{recursive:true});fs.writeFileSync('docs/sirs-tests/browser.json',JSON.stringify(results,null,2));console.log(results.join('\n'));}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
