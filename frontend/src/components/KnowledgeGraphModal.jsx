import { useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';

function buildGraph(hospital) {
  const nodes = [
    {
      id: 'rs',
      label: `${hospital.nama}\n(Kelas ${hospital.kelas || '—'})`,
      color: { background: '#012D61', border: '#00193B' },
      font: { color: '#ffffff', size: 14, face: 'Newsreader', bold: true },
      shape: 'box',
      margin: 14,
      shadow: true,
    },
    {
      id: 'kab',
      label: hospital.kabkota || 'Sumatera Utara',
      color: { background: '#0057B8', border: '#00275B' },
      font: { color: '#ffffff', size: 12, face: 'Newsreader' },
      shape: 'ellipse',
    },
    {
      id: 'reg',
      label: 'Standar Permenkes No. 3/2020',
      color: { background: '#F1F5F9', border: '#CBD5E1' },
      font: { color: '#0F172A', size: 10, face: 'Newsreader' },
      shape: 'box',
    },
  ];
  const edges = [
    {
      from: 'rs',
      to: 'kab',
      label: 'Wilayah Administratif',
      arrows: 'to',
      font: { size: 9, color: '#64748B', face: 'Newsreader' },
    },
    {
      from: 'rs',
      to: 'reg',
      label: 'Acuan Klasifikasi',
      arrows: 'to',
      font: { size: 9, color: '#64748B', face: 'Newsreader' },
    },
  ];

  if (hospital.jenis) {
    nodes.push({
      id: 'jenis',
      label: `RS ${hospital.jenis}`,
      color: { background: '#EEF2FF', border: '#6366F1' },
      font: { color: '#312E81', size: 11, face: 'Newsreader' },
      shape: 'box',
      margin: 8,
    });
    edges.push({
      from: 'rs',
      to: 'jenis',
      label: 'Kategori RS',
      arrows: 'to',
      font: { size: 9, color: '#4F46E5', face: 'Newsreader' },
    });
  }

  if (hospital.bpjs) {
    nodes.push({
      id: 'bpjs',
      label: 'Menerima BPJS Kesehatan',
      color: { background: '#D1FAE5', border: '#059669' },
      font: { color: '#047857', size: 11, bold: true, face: 'Newsreader' },
      shape: 'box',
      margin: 8,
    });
    edges.push({
      from: 'rs',
      to: 'bpjs',
      label: 'Jaminan Kesehatan',
      arrows: 'to',
      font: { size: 9, color: '#059669', face: 'Newsreader' },
    });
  }

  (hospital.layanan || []).slice(0, 7).forEach((service, index) => {
    const id = `lay_${index}`;
    nodes.push({
      id,
      label: service,
      color: { background: '#ECFDF5', border: '#0F766E' },
      font: { color: '#0F172A', size: 10, face: 'Newsreader' },
      shape: 'box',
    });
    edges.push({
      from: 'rs',
      to: id,
      label: 'Layanan Medis',
      arrows: 'to',
      font: { size: 8, color: '#0F766E', face: 'Newsreader' },
    });
  });

  (hospital.fasilitas || []).slice(0, 5).forEach((facility, index) => {
    const id = `fas_${index}`;
    nodes.push({
      id,
      label: facility,
      color: { background: '#FEF3C7', border: '#D97706' },
      font: { color: '#0F172A', size: 10, face: 'Newsreader' },
      shape: 'box',
    });
    edges.push({
      from: 'rs',
      to: id,
      label: 'Fasilitas Penunjang',
      arrows: 'to',
      font: { size: 8, color: '#D97706', face: 'Newsreader' },
    });
  });

  return { nodes, edges };
}

export default function KnowledgeGraphModal({ hospital, open, onClose }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    const previous = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previous;
    };
  }, [open, onClose]);

  useEffect(() => {
    if (!open || !hospital || !containerRef.current || !window.vis) return undefined;
    const graph = buildGraph(hospital);
    const data = {
      nodes: new window.vis.DataSet(graph.nodes),
      edges: new window.vis.DataSet(graph.edges),
    };
    networkRef.current = new window.vis.Network(containerRef.current, data, {
      physics: {
        solver: 'forceAtlas2Based',
        forceAtlas2Based: {
          gravitationalConstant: -45,
          centralGravity: 0.012,
          springLength: 110,
          springConstant: 0.08,
        },
        stabilization: { iterations: 180 },
      },
      interaction: {
        hover: true,
        tooltipDelay: 200,
        navigationButtons: true,
        zoomView: true,
      },
      nodes: { borderWidth: 1.5 },
      edges: { smooth: { type: 'continuous' } },
    });

    return () => {
      networkRef.current?.destroy();
      networkRef.current = null;
    };
  }, [open, hospital]);

  if (!open || !hospital) return null;

  return createPortal(
    <div
      className="fixed inset-0 z-[95] flex animate-fade-in items-center justify-center bg-slate-950/65 p-4 backdrop-blur-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="graph-title"
        className="flex h-[min(86vh,720px)] w-full max-w-[980px] animate-zoom-in flex-col overflow-hidden rounded-2xl bg-white shadow-modal"
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 px-5 py-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-brand-blue">
              Diagram Layanan Interaktif
            </p>
            <h2 id="graph-title" className="mt-0.5 font-heading text-lg font-bold leading-snug text-slate-900">
              Peta Relasi Layanan: {hospital.nama}
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Visualisasi hubungan antara rumah sakit, wilayah cakupan, layanan medis, dan fasilitas penunjang.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200 hover:text-slate-800"
            aria-label="Tutup diagram relasi"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </header>

        <div className="relative flex-1 bg-slate-50">
          <div ref={containerRef} className="h-full w-full" />
          <div className="pointer-events-none absolute bottom-3 left-3 flex flex-wrap gap-2 rounded-xl border border-slate-200 bg-white/95 px-3 py-2 text-[10px] font-semibold text-slate-600 shadow-sm backdrop-blur">
            <span className="flex items-center gap-1">
              <i className="h-2 w-2 rounded-full bg-brand-navy" /> Rumah sakit
            </span>
            <span className="flex items-center gap-1">
              <i className="h-2 w-2 rounded-full bg-brand-blue" /> Wilayah
            </span>
            <span className="flex items-center gap-1">
              <i className="h-2 w-2 rounded-full bg-emerald-500" /> Layanan
            </span>
            <span className="flex items-center gap-1">
              <i className="h-2 w-2 rounded-full bg-amber-500" /> Fasilitas
            </span>
          </div>
        </div>

        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-slate-200 px-5 py-3 text-[11px] text-slate-500">
          <span>Geser kanvas untuk menjelajah, gulir untuk memperbesar tampilan.</span>
          <a
            href={`/rumah-sakit/${encodeURIComponent(hospital.id)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-brand-blue hover:underline"
          >
            Buka profil lengkap rumah sakit →
          </a>
        </footer>
      </section>
    </div>,
    document.body,
  );
}