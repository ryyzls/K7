import { useState } from 'react';
import LeafletMap from './LeafletMap';

export default function NaraRichResponse({message,send,toggleComparison,loading,toast}) {
  const [map,setMap]=useState(false);
  if(message.role==='user')return null;
  const hospitals=message.hospitals||[];
  const mapped=hospitals.filter(h=>h.lat!=null&&h.lon!=null&&['osm','jalan','nama'].includes(h.sumber_koordinat));
  const columns=message.comparison?.hospitals||[];
  const copy=async()=>{try{await navigator.clipboard.writeText(message.text);toast('Jawaban disalin.','success');}catch{toast('Pilih teks untuk menyalin manual.','info');}};
  return <div className="nara-rich">
    <div className="nara-replies"><button onClick={copy} aria-label="Salin jawaban">Salin</button>{message.retry&&<button disabled={loading} onClick={()=>send(message.retry)}>Coba lagi</button>}</div>
    {columns.length>0&&<div className="nara-table"><table><thead><tr><th>Atribut</th>{columns.map(h=><th key={h.id}>{h.nama}</th>)}</tr></thead><tbody>{[['kelas','Kelas'],['kabkota','Wilayah'],['alamat','Alamat'],['telepon','Telepon'],['semua_layanan_sirs','Layanan tercatat'],['fasilitas','Fasilitas tercatat']].map(([k,label])=><tr key={k}><th>{label}</th>{columns.map(h=><td key={h.id}>{Array.isArray(h[k])?h[k].join(', ')||'Belum tersedia':h[k]||'Belum tersedia'}</td>)}</tr>)}</tbody></table><small>Data tercatat, bukan ketersediaan real-time. Fasilitas perlu dikonfirmasi kepada RS.</small></div>}
    {message.kind==='hours'&&<Schedule value={message.hours}/>}
    {hospitals.length>0&&<div className="nara-replies">{hospitals.map((h,i)=><span key={h.id}><button disabled={loading} onClick={()=>send(`Detail ${h.id}`)} title={h.nama}>Bahas RS {i+1}</button> <button disabled={loading} onClick={()=>toggleComparison(h)} title={h.nama}>Bandingkan RS {i+1}</button>{h.distance_km!=null&&<small> {Number(h.distance_km).toFixed(1)} km garis lurus</small>}</span>)}</div>}
    {mapped.length>0&&<><button className="nara-chip" onClick={()=>setMap(v=>!v)}>{map?'Tutup peta':'Lihat peta'}</button>{map&&<LeafletMap hospitals={mapped} showLocate={false} className="nara-map"/>}<div className="nara-replies">{mapped.map((h,i)=><a key={h.id} target="_blank" rel="noopener noreferrer" href={`https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(`${h.lat},${h.lon}`)}`}>Navigasi RS {i+1}</a>)}</div></>}
    {message.regional_info?.abstract&&<p>{message.regional_info.abstract}</p>}
  </div>;
}
function Schedule({value}) {
  const rows=[];
  const visit=(v,path='')=>{if(!v||typeof v!=='object')return;for(const[k,item]of Object.entries(v)){if(/status|verified|confidence|sumber|source|url|catatan|realtime/i.test(k))continue;if(typeof item==='object')visit(item,`${path} ${Array.isArray(v)?'':k}`);else if(typeof item==='string'&&item&&/hari|jam|buka|tutup|unit|open|close|day|jadwal/i.test(`${path} ${k}`))rows.push([`${path} ${k}`.replaceAll('_',' '),item]);}};visit(value);
  return <dl className="nara-hours">{rows.length?rows.map(([k,v],i)=><div key={i}><dt>{k}</dt><dd>{v}</dd></div>):<p>Jam operasional: Belum tersedia.</p>}</dl>;
}
