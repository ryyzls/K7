const {readFileSync} = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const html = readFileSync(require('node:path').join(__dirname, '../frontend/index.html'), 'utf8');
// Parse every inline script, then exercise the actual chat request handler.
for(const match of html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)) new vm.Script(match[1]);
const source = html.slice(html.indexOf('const SUGGEST ='), html.indexOf('/* ============ Event ============ */'));
const elements = new Map();
const $ = id => {
  if(!elements.has(id)) elements.set(id, {addEventListener(){}, innerHTML:'', textContent:''});
  return elements.get(id);
};
let gpsCalls = 0, payload, reply = {text:'hasil', state:{offset:5}, quick_replies:['Lihat lainnya']};
const ctx = vm.createContext({$, esc:s=>s, console, userCoords:null,
  navigator:{geolocation:{getCurrentPosition(ok){gpsCalls++;ok({coords:{latitude:3.59,longitude:98.67}});}}},
  customElements:{whenDefined:()=>Promise.resolve()},
  fetch:async (_url, options)=>{payload=JSON.parse(options.body);return {ok:true,json:async()=>reply};}
});
(async()=>{
  vm.runInContext(source, ctx);
  await Promise.resolve();
  let closed=0;
  const signals={onResponse(){},onClose(){closed++;}};
  const ask = text => $('#chat-element').request.handler({messages:[{role:'user',text}]}, signals);
  await ask('RS terdekat dari saya');
  assert.equal(payload.lat,3.59);
  assert.equal(payload.lon,98.67);
  assert.equal(gpsCalls,1);
  assert.match($('#suggest').innerHTML,/Lihat lainnya/);
  await ask('Lihat lainnya');
  assert.equal(payload.state.offset,5);
  assert.equal(payload.history.length,2);
  assert.equal(payload.lat,undefined);
  assert.equal(gpsCalls,1);
  ctx.userCoords=null;
  await ask('berapa jarak ke RS Adam Malik?');
  assert.equal(payload.lat,3.59);
  assert.equal(payload.lon,98.67);
  assert.equal(gpsCalls,2);
  ctx.userCoords=null;
  ctx.navigator.geolocation.getCurrentPosition=(_ok,fail)=>fail({code:1});
  await ask('RS terdekat');
  assert.equal(payload.location_status,'denied');
  assert.equal(payload.lat,undefined);
  ctx.fetch=async()=>{throw new Error('offline');};
  await ask('Cari RS');
  assert.equal(closed,5);
  assert.equal($('#chat-status-label').textContent,'Asisten direktori rumah sakit');
  console.log('Chat frontend: GPS, denied permission, history/state, quick replies, error completion and script syntax passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
