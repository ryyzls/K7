import { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';

export function buildGraph(bindings) {
  const nodes = new Map(), edges = [];
  const short = value => value.split(/[\/#]/).filter(Boolean).pop();
  for (const row of bindings) {
    if (!row.s || !row.p || !row.o) continue;
    for (const term of [row.s, row.o]) {
      const key = `${term.type}:${term.value}`;
      nodes.set(key, {id:key,label:term.type==='literal'?term.value:short(term.value),
        shape:'box',margin:10,font:{face:'Plus Jakarta Sans',size:12},
        color:{background:term.type==='literal'?'#f0fdfa':'#e0f2fe',border:'#0f766e'}});
    }
    edges.push({from:`${row.s.type}:${row.s.value}`,to:`${row.o.type}:${row.o.value}`,
      label:short(row.p.value),arrows:'to',font:{size:10}});
  }
  return {nodes:[...nodes.values()],edges};
}

export default function KnowledgeGraphModal({ hospital, open, onClose }) {
  const containerRef = useRef(null);
  const networkRef = useRef(null);
  const [bindings,setBindings]=useState([]);
  const [status,setStatus]=useState('');

  useEffect(()=>{
    if(!open || !hospital?.uri)return;
    const controller=new AbortController();
    setBindings([]);setStatus('Memuat relasi RDF...');
    const value=JSON.stringify(hospital.uri);
    const query=`PREFIX hf: <http://carisehat.id/ontology/>
      SELECT DISTINCT ?s ?p ?o WHERE {
        ?root a hf:RumahSakit . FILTER(STR(?root) = ${value})
        { BIND(?root AS ?s) ?s ?p ?o }
        UNION { ?root hf:beradaDiKabupatenKota ?s . ?s ?p ?o }
        UNION { GRAPH ?g { ?root ?link ?s . FILTER(isBlank(?s)) ?s ?p ?o } }
        UNION { GRAPH ?g { BIND(?root AS ?s) ?s ?p ?o } }
      } ORDER BY ?s ?p ?o LIMIT 160`;
    fetch('/sparql/query',{method:'POST',headers:{'Content-Type':'application/sparql-query',Accept:'application/sparql-results+json'},body:query,signal:controller.signal})
      .then(async r=>{if(!r.ok)throw new Error('Graf belum dapat dimuat');return r.json();})
      .then(data=>{if(!controller.signal.aborted){setBindings(data.results?.bindings||[]);setStatus(window.vis?'':'Pustaka graf belum tersedia');}})
      .catch(e=>{if(!controller.signal.aborted)setStatus(e.message);});
    return()=>controller.abort();
  },[open,hospital?.uri]);

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
    const graph = buildGraph(bindings);
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
  }, [open, hospital, bindings]);

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
              W3C Network • Vis.js
            </p>
            <h2 id="graph-title" className="mt-0.5 font-heading text-lg font-bold leading-snug text-slate-900">
              Graf Pengetahuan: {hospital.nama}
            </h2>
            <p className="mt-0.5 text-xs text-slate-500">
              Relasi RDF/OWL antara fasilitas, wilayah, layanan, dan data tertaut.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200 hover:text-slate-800"
            aria-label="Tutup graf pengetahuan"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </header>

        <div className="relative flex-1 bg-slate-50">
          <div ref={containerRef} className="h-full w-full" data-graph-nodes={buildGraph(bindings).nodes.length} />
          {status && <p role="status" className="absolute left-4 top-4 bg-white p-3">{status}</p>}
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
          <span>Geser untuk menjelajah, gulir untuk memperbesar.</span>
          <a
            href={`/rs/${encodeURIComponent(hospital.id)}`}
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold text-brand-blue hover:underline"
          >
            Buka halaman semantik RDF
          </a>
        </footer>
      </section>
    </div>,
    document.body,
  );
}
