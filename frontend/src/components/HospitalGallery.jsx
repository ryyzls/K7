import { useEffect, useRef, useState } from 'react';

export default function HospitalGallery({ hospital }) {
  const photos = [...new Set([...(hospital.galeri || []), hospital.foto].filter(Boolean))];
  const [index, setIndex] = useState(0);
  const [paused, setPaused] = useState(false);
  const touch = useRef(null);
  useEffect(() => setIndex(0), [hospital.id]);
  useEffect(() => {
    if (photos.length < 2 || paused) return;
    const timer = setInterval(() => setIndex(i => (i + 1) % photos.length), 4000);
    return () => clearInterval(timer);
  }, [photos.length, paused, index]);
  const move = step => setIndex(i => (i + step + photos.length) % photos.length);
  if (!photos.length) return <div className="parity-gallery-empty">Photo rumah sakit belum tersedia</div>;
  return <section className="parity-gallery" aria-label="Galeri foto rumah sakit"
    onMouseEnter={() => setPaused(true)} onMouseLeave={() => setPaused(false)}
    onFocus={() => setPaused(true)} onBlur={e => { if (!e.currentTarget.contains(e.relatedTarget)) setPaused(false); }}
    onTouchStart={e => { touch.current = e.touches[0].clientX; }}
    onTouchEnd={e => { if (touch.current !== null && Math.abs(e.changedTouches[0].clientX - touch.current) > 40) move(e.changedTouches[0].clientX < touch.current ? 1 : -1); touch.current = null; }}
    tabIndex={0} onKeyDown={e => { if (['ArrowLeft','ArrowRight'].includes(e.key)) { e.preventDefault(); move(e.key === 'ArrowLeft' ? -1 : 1); } }}>
    <img src={photos[index % photos.length]} alt={`${hospital.nama}, foto ${index + 1}`} />
    {photos.length > 1 && <>
      <button type="button" className="parity-gallery-prev" aria-label="Foto sebelumnya" onClick={() => move(-1)}><span className="material-symbols-outlined" aria-hidden="true">chevron_left</span></button>
      <output>{index + 1} / {photos.length}</output>
      <button type="button" className="parity-gallery-next" aria-label="Foto berikutnya" onClick={() => move(1)}><span className="material-symbols-outlined" aria-hidden="true">chevron_right</span></button>
    </>}
  </section>;
}
