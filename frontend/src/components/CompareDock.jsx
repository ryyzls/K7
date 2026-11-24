import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { Link } from 'react-router-dom';
import {
  compareHospitalsApi,
  getAllHospitals,
  getHospitalReviews,
  getPoliklinikByRs,
} from '../api';
import { useApp } from '../context/AppContext';
import { cn } from '../utils';
import KnowledgeGraphModal from './KnowledgeGraphModal';

function CompareMatrixModal({ open, onClose, ids, onToggleId, onClearAll }) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [compareData, setCompareData] = useState(null);
  const [msbdEnrichment, setMsbdEnrichment] = useState({});
  const [kgHospital, setKgHospital] = useState(null);

  useEffect(() => {
    if (!open) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    if (!ids.length) {
      setCompareData(null);
      setMsbdEnrichment({});
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError('');

    Promise.all([
      compareHospitalsApi(ids),
      getAllHospitals().catch(() => []),
      Promise.all(
        ids.map(async (rsId) => {
          const [revRes, poliRes] = await Promise.all([
            getHospitalReviews(rsId, 1, 5).catch(() => null),
            getPoliklinikByRs(rsId).catch(() => null),
          ]);
          const poliList = Array.isArray(poliRes)
            ? poliRes
            : poliRes?.items || poliRes?.poliklinik || [];
          const totalKuota = poliList.reduce(
            (acc, p) => acc + (Number(p.kuota_tersedia ?? p.sisa_kuota ?? p.kuota ?? 0) || 0),
            0,
          );
          return [
            rsId,
            {
              avgRating: revRes?.rata_rata_rating ?? revRes?.average_rating ?? null,
              totalUlasan: revRes?.total ?? revRes?.total_ulasan ?? (revRes?.items?.length || 0),
              poliCount: poliList.length,
              totalKuota,
            },
          ];
        }),
      ),
    ])
      .then(([cmp, allHosp, msbdEntries]) => {
        if (cancelled) return;
        const hospMap = new Map((allHosp || []).map((h) => [h.id, h]));
        const enrichedHospitals = (cmp?.hospitals || []).map((h) => ({
          ...hospMap.get(h.id),
          ...h,
          foto: h.foto || hospMap.get(h.id)?.foto || '',
          alamat: h.alamat || hospMap.get(h.id)?.alamat || '',
        }));
        setCompareData({ ...cmp, hospitals: enrichedHospitals });
        setMsbdEnrichment(Object.fromEntries(msbdEntries));
      })
      .catch((err) => {
        if (!cancelled) setError(err.message || 'Gagal memuat data perbandingan.');
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [open, ids]);

  if (!open) return null;

  const hospitals = compareData?.hospitals || [];
  const sharedServices = compareData?.comparison_matrix?.shared_services || [];

  return createPortal(
    <div
      className="fixed inset-0 z-[95] flex animate-fade-in items-center justify-center bg-slate-950/65 p-3 backdrop-blur-overlay sm:p-5"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        role="dialog"
        aria-modal="true"
        aria-labelledby="compare-modal-title"
        className="flex max-h-[92vh] w-full max-w-[1140px] animate-zoom-in flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-modal"
      >
        <header className="flex items-start justify-between gap-4 border-b border-slate-200 bg-toba-mist/70 px-5 py-4">
          <div>
            <p className="text-xs font-medium text-toba-dark">
              Rumah sakit yang dibandingkan
            </p>
            <h2 id="compare-modal-title" className="mt-1 text-xl font-semibold text-slate-900">
              Perbandingan rumah sakit ({ids.length}/3)
            </h2>
          </div>
          <div className="flex items-center gap-2">
            {ids.length > 0 ? (
              <button
                type="button"
                onClick={onClearAll}
                className="rounded-full border border-slate-300 bg-white px-3 py-1.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
              >
                Kosongkan
              </button>
            ) : null}
            <button
              type="button"
              onClick={onClose}
              className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-slate-500 ring-1 ring-slate-200 transition hover:bg-slate-100 hover:text-slate-800"
              aria-label="Tutup matriks perbandingan"
            >
              <span className="material-symbols-outlined text-[20px]">close</span>
            </button>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto p-5 scrollbar-thin">
          {!ids.length ? (
            <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-10 text-center">
              <p className="text-sm font-bold text-slate-700">Belum ada rumah sakit yang dipilih.</p>
              <p className="mt-1 text-xs text-slate-500">
                Klik tombol <strong>Bandingkan</strong> pada kartu rumah sakit (maksimal 3 RS).
              </p>
            </div>
          ) : loading ? (
            <div className="py-14 text-center">
              <div className="mx-auto h-8 w-8 animate-spin rounded-full border-2 border-toba/25 border-t-toba" />
              <p className="mt-3 text-xs font-semibold text-slate-500">
                Memuat perbandingan fasilitas, ulasan &amp; kuota poliklinik...
              </p>
            </div>
          ) : error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center text-sm text-rose-700">
              {error}
            </div>
          ) : (
            <div className="space-y-6">
              {/* Dimensi 1 & 2: Identitas SIRS + Dimensi 3: Rating & Kuota MSBD + RDF */}
              <div className="overflow-x-auto rounded-2xl border border-slate-200">
                <table className="w-full min-w-[720px] border-collapse text-left text-xs">
                  <thead>
                    <tr className="border-b border-slate-200 bg-slate-50">
                      <th className="w-44 p-3.5 font-bold uppercase tracking-wider text-slate-500">
                        Dimensi / Atribut
                      </th>
                      {hospitals.map((h) => (
                        <th key={h.id} className="p-3.5 align-top">
                          <div className="flex items-start justify-between gap-2">
                            <div>
                              <Link
                                to={`/rumah-sakit/${encodeURIComponent(h.id)}`} onClick={onClose} className="text-sm font-extrabold text-toba-dark hover:underline" > {h.nama} </Link> <p className="mt-0.5 text-[11px] font-medium text-slate-500"> {h.kabkota} • Kode Kemenkes: {h.kode_kemenkes || '—'} </p> </div> <button type="button" onClick={() => onToggleId(h.id)} className="rounded-full px-2 py-0.5 text-[11px] font-bold text-slate-400 hover:bg-rose-50 hover:text-rose-600" title="Hapus dari perbandingan" > &times; </button> </div> </th> ))} </tr> </thead> <tbody className="divide-y divide-slate-100"> <tr> <td className="bg-slate-50/70 p-3.5 font-bold text-slate-700"> Kelas &amp; Jenis RS <span className="mt-0.5 block text-[10px] font-normal text-toba"> Data profil fasilitas </span> </td> {hospitals.map((h) => ( <td key={h.id} className="p-3.5 font-semibold text-slate-800"> Kelas {h.kelas || '—'} • {h.jenis || '—'} </td> ))} </tr>  <tr> <td className="bg-slate-50/70 p-3.5 font-bold text-slate-700"> Status BPJS <span className="mt-0.5 block text-[10px] font-normal text-slate-400"> Konfirmasi langsung ke RS </span> </td> {hospitals.map((h) => ( <td key={h.id} className="p-3.5"> {h.bpjs_info?.menerima_bpjs ? ( <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-[11px] font-bold text-emerald-700"> Tercatat BPJS </span> ) : ( <span className="inline-flex items-center gap-1 rounded-full bg-amber-50 px-2.5 py-0.5 text-[11px] font-bold text-amber-700"> Perlu konfirmasi </span> )} </td> ))} </tr>  <tr> <td className="bg-slate-50/70 p-3.5 font-bold text-slate-700"> Rating &amp; Kuota Poli <span className="mt-0.5 block text-[10px] font-normal text-toba"> Ulasan &amp; jadwal poli </span> </td> {hospitals.map((h) => { const m = msbdEnrichment[h.id] || {}; return ( <td key={h.id} className="p-3.5 text-slate-800"> <div className="flex flex-wrap items-center gap-2"> <span className="rounded-lg bg-amber-50 px-2 py-1 font-bold text-amber-800"> ★ {m.avgRating != null ? Number(m.avgRating).toFixed(1) : '—'} ({m.totalUlasan || 0} ulasan) </span> <span className="rounded-lg bg-toba-mist px-2 py-1 font-bold text-toba-dark"> {m.poliCount || 0} poli • {m.totalKuota || 0} kuota </span> </div> </td> ); })} </tr>  <tr> <td className="bg-slate-50/70 p-3.5 font-bold text-slate-700"> Layanan Medis Tersedia <span className="mt-0.5 block text-[10px] font-normal text-toba"> Poliklinik &amp; fasilitas </span> </td> {hospitals.map((h) => { const services = h.semua_layanan_sirs || []; return ( <td key={h.id} className="p-3.5 align-top"> {services.length ? ( <div className="flex flex-wrap gap-1"> {services.slice(0, 8).map((srv) => { const isShared = sharedServices.includes(srv); return ( <span key={srv} className={cn( 'rounded-md px-2 py-0.5 text-[10.5px] font-semibold', isShared ? 'bg-toba-soft text-toba-dark ring-1 ring-toba/30' : 'bg-slate-100 text-slate-700', )} title={isShared ? 'Layanan irisan antar RS terpilih' : 'Layanan RS'} > {srv} </span> ); })} {services.length > 8 ? ( <span className="rounded-md bg-slate-50 px-2 py-0.5 text-[10.5px] text-slate-500"> +{services.length - 8} lainnya </span> ) : null} </div> ) : ( <span className="text-slate-400">Belum tercatat</span> )} </td> ); })} </tr>  <tr> <td className="bg-slate-50/70 p-3.5 font-bold text-slate-700"> Jaringan &amp; Aksi </td> {hospitals.map((h) => ( <td key={h.id} className="p-3.5"> <div className="flex flex-wrap gap-1.5"> <button type="button" onClick={() => setKgHospital(h)} className="inline-flex items-center gap-1 rounded-full border border-toba/30 bg-toba-mist px-2.5 py-1 text-[11px] font-bold text-toba-dark hover:bg-toba-soft" > <span className="material-symbols-outlined text-[14px]">hub</span> Peta Layanan </button> <Link to={`/rumah-sakit/${encodeURIComponent(h.id)}`}
                              onClick={onClose}
                              className="inline-flex items-center gap-1 rounded-full bg-toba px-3 py-1 text-[11px] font-bold text-white hover:bg-toba-dark"
                            >
                              Profil Lengkap
                            </Link>
                          </div>
                        </td>
                      ))}
                    </tr>
                  </tbody>
                </table>
              </div>

              {sharedServices.length > 0 ? (
                <div className="rounded-xl border border-toba/20 bg-toba-mist/60 p-3.5">
                  <p className="text-[11px] font-bold uppercase tracking-wider text-toba-dark">
                    Irisan Layanan Bersama ({sharedServices.length})
                  </p>
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {sharedServices.map((srv) => (
                      <span
                        key={srv}
                        className="rounded-full bg-white px-2.5 py-1 text-[11px] font-semibold text-toba-dark ring-1 ring-toba/25"
                      >
                        {srv}
                      </span>
                    ))}
                  </div>
                </div>
              ) : null}

              {(compareData?.disclaimers || []).length > 0 ? (
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11px] text-slate-500">
                  {compareData.disclaimers.map((d, i) => (
                    <p key={i} className={i > 0 ? 'mt-1' : ''}>
                      • {d}
                    </p>
                  ))}
                </div>
              ) : null}
            </div>
          )}
        </div>
      </section>

      <KnowledgeGraphModal
        hospital={kgHospital}
        open={Boolean(kgHospital)}
        onClose={() => setKgHospital(null)}
      />
    </div>,
    document.body,
  );
}

export default function CompareDock() {
  const {
    compareIds,
    maxCompare,
    toggleCompare,
    clearCompare,
    compareModalOpen,
    setCompareModalOpen,
  } = useApp();
  const [nameMap, setNameMap] = useState({});

  useEffect(() => {
    if (!compareIds.length) return;
    getAllHospitals()
      .then((items) => {
        const next = {};
        (items || []).forEach((h) => {
          next[h.id] = h.nama;
        });
        setNameMap(next);
      })
      .catch(() => {});
  }, [compareIds.length]);

  return (
    <>
      {compareIds.length > 0 ? (
        <div
          className="fixed bottom-5 left-1/2 z-[65] flex max-w-[95vw] -translate-x-1/2 animate-slide-up items-center gap-3 rounded-full border border-white/20 bg-slate-900/95 px-4 py-2.5 text-white shadow-floating backdrop-blur-md"
          role="region"
          aria-label="Dock perbandingan rumah sakit"
        >
          <span className="shrink-0 text-xs font-extrabold text-toba-soft">
            {compareIds.length}/{maxCompare} RS
          </span>

          <div className="flex max-w-[44vw] items-center gap-1.5 overflow-x-auto no-scrollbar">
            {compareIds.map((id) => (
              <span
                key={id}
                className="inline-flex shrink-0 items-center gap-1 rounded-full bg-white/15 px-2.5 py-1 text-[11px] font-semibold"
              >
                <span className="max-w-[130px] truncate">{nameMap[id] || id}</span>
                <button
                  type="button"
                  onClick={() => toggleCompare(id)}
                  className="ml-0.5 font-bold text-white/80 hover:text-rose-300"
                  aria-label={`Hapus ${nameMap[id] || id}`}
                >
                  &times;
                </button>
              </span>
            ))}
          </div>

          <div className="flex shrink-0 items-center gap-1.5">
            <button
              type="button"
              onClick={() => setCompareModalOpen(true)}
              className="rounded-full bg-toba px-3.5 py-1.5 text-xs font-bold text-white transition hover:bg-toba-dark"
            >
              Bandingkan
            </button>
            <button
              type="button"
              onClick={clearCompare}
              className="rounded-full border border-white/25 px-2.5 py-1.5 text-[11px] font-semibold text-white/80 transition hover:bg-white/10"
            >
              Reset
            </button>
          </div>
        </div>
      ) : null}

      <CompareMatrixModal
        open={compareModalOpen}
        onClose={() => setCompareModalOpen(false)}
        ids={compareIds}
        onToggleId={toggleCompare}
        onClearAll={clearCompare}
      />
    </>
  );
}
