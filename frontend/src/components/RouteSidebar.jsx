import { useEffect, useState } from 'react';

const modes = [['driving','Mobil','directions_car'],['foot','Jalan kaki','directions_walk'],['motorcycle','Motor','two_wheeler']];
const distance = n => n < 1000 ? `${Math.round(n)} m` : `${(n/1000).toLocaleString('id-ID',{maximumFractionDigits:1})} km`;
const duration = n => { const m=Math.round(n/60); return m<60?`${m} mnt`:`${Math.floor(m/60)} j ${m%60} mnt`; };
function turn(type){const t=String(type).toLowerCase();if(t.includes('turnaround')||t.includes('uturn'))return 'u_turn_left';if(t.includes('right'))return 'turn_right';if(t.includes('left'))return 'turn_left';if(t.includes('reach'))return 'flag';if(t.includes('roundabout'))return 'roundabout_right';return 'straight';}

export default function RouteSidebar({hospital,mode,info,error,onMode,onClose}) {
  const [address,setAddress]=useState('Menentukan titik berangkat');
  const lat=info?.origin?.[0],lon=info?.origin?.[1];
  useEffect(()=>{
    if(!Number.isFinite(lat)||!Number.isFinite(lon)){setAddress('Menentukan titik berangkat');return;}
    setAddress(`${lat.toFixed(5)}, ${lon.toFixed(5)}`);
    const controller=new AbortController();
    const timeout=setTimeout(()=>controller.abort(),8000);
    const params=new URLSearchParams({lat:lat.toFixed(5),lon:lon.toFixed(5),limit:'1'});
    fetch(`https://photon.komoot.io/reverse?${params}`,{signal:controller.signal,credentials:'omit'})
      .then(response=>response.ok?response.json():null).then(data=>{
        const p=data?.features?.[0]?.properties;
        if(!p||controller.signal.aborted)return;
        const text=[...new Set([p.street?[p.street,p.housenumber].filter(Boolean).join(' '):p.name,p.district,p.city||p.county,p.state].filter(Boolean))].join(', ');
        if(text)setAddress(text);
      }).catch(()=>{}).finally(()=>clearTimeout(timeout));
    return()=>{controller.abort();clearTimeout(timeout);};
  },[lat,lon]);
  return <aside className="parity-route-sidebar" aria-label="Panduan perjalanan">
    <header><button type="button" onClick={onClose} aria-label="Kembali dari panduan rute"><span className="material-symbols-outlined">arrow_back</span></button><h1>Panduan Rute</h1></header>
    <div className="parity-route-modes">{modes.map(([id,label,icon])=><button key={id} type="button" aria-pressed={mode===id} onClick={()=>onMode(id)}><span className="material-symbols-outlined">{icon}</span>{label}</button>)}</div>
    <div className="parity-route-places">
      <div><span className="material-symbols-outlined">radio_button_unchecked</span><div><small>Titik berangkat</small><strong>{error&&!info?'Lokasi belum tersedia':address}</strong></div></div>
      <div><span className="material-symbols-outlined">location_on</span><div><small>Tujuan</small><strong>{hospital.nama}</strong></div></div>
    </div>
    <section className="parity-route-summary" aria-live="polite">
      {error?<p role="alert">{error}</p>:info?<><h2>Rute perjalanan</h2><p>{distance(info.distance)} <span className="ml-3">{duration(info.time)}</span></p></>:<p>Menghitung rute dari lokasi Anda...</p>}
      <p className="parity-route-note">Estimasi tanpa kondisi lalu lintas langsung. Pilihan motor membuka Google Maps.</p>
    </section>
    {!!info?.instructions?.length&&<ol className="parity-route-steps" aria-label="Petunjuk perjalanan">{info.instructions.map((step,i)=><li key={i}><span className="material-symbols-outlined" aria-hidden="true">{turn(step.type)}</span><span>{step.text}</span><small>{distance(step.distance||0)}</small></li>)}</ol>}
  </aside>;
}
