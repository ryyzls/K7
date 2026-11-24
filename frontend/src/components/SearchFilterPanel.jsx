import { useEffect, useMemo, useState } from 'react';
import { createPortal } from 'react-dom';
import { KELAS_DESCRIPTION, KELAS_OPTIONS, JENIS_OPTIONS } from '../constants';
import { cn } from '../utils';

const EMPTY = {
  q: '',
  kelas: '',
  jenis: '',
  kabkota: '',
  layanan: '',
  bpjs: false,
};

export function countActiveFilters(filters = {}) {
  return ['q', 'kelas', 'jenis', 'kabkota', 'layanan'].filter((key) => filters[key]).length + (filters.bpjs ? 1 : 0);
}

export default function SearchFilterPanel({ open, onClose, filters = EMPTY, options = {}, onApply, onReset }) {
  const [draft, setDraft] = useState({ ...EMPTY, ...filters });

  useEffect(() => {
    if (open) setDraft({ ...EMPTY, ...filters });
  }, [open, filters]);

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

  const activeCount = useMemo(() => countActiveFilters(draft), [draft]);
  if (!open) return null;

  const set = (key, value) => setDraft((current) => ({ ...current, [key]: value }));

  return createPortal(
    <div
      className="fixed inset-0 z-[90] flex animate-fade-in justify-end bg-slate-950/45 backdrop-blur-overlay"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <aside
        className="flex h-full w-full max-w-[440px] animate-slide-up flex-col bg-white shadow-modal sm:animate-zoom-in"
        role="dialog"
        aria-modal="true"
        aria-labelledby="filter-title"
      >
        <header className="flex items-start justify-between gap-3 border-b border-slate-200 bg-toba-mist/60 px-5 py-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-toba">
              Direktori Rumah Sakit
            </p>
            <h2 id="filter-title" className="mt-0.5 text-xl font-extrabold text-slate-900">
              Filter Pencarian
            </h2>
            <p className="mt-1 text-xs text-slate-500">
              {activeCount ? `${activeCount} filter aktif diterapkan` : 'Saring berdasarkan kelas, wilayah, dan layanan'}
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-9 w-9 items-center justify-center rounded-full bg-white text-slate-500 ring-1 ring-slate-200 transition hover:bg-slate-100 hover:text-slate-800"
            aria-label="Tutup panel filter"
          >
            <span className="material-symbols-outlined text-[20px]">close</span>
          </button>
        </header>

        <div className="flex-1 space-y-6 overflow-y-auto px-5 py-5 scrollbar-thin">
          <label className="block">
            <span className="mb-1.5 block text-xs font-bold text-slate-700">Kata kunci atau layanan</span>
            <div className="relative">
              <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                <span className="material-symbols-outlined text-[18px]">search</span>
              </span>
              <input
                value={draft.q}
                onChange={(event) => set('q', event.target.value)}
                placeholder="Nama rumah sakit, alamat, atau layanan..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 py-2.5 pl-10 pr-3 text-sm outline-none transition focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/15"
              />
            </div>
          </label>

          <fieldset>
            <legend className="mb-2 text-xs font-bold text-slate-700">Kelas rumah sakit</legend>
            <div className="grid grid-cols-5 gap-1.5">
              <button
                type="button"
                onClick={() => set('kelas', '')}
                className={cn(
                  'rounded-xl border px-2 py-2 text-xs font-semibold transition',
                  !draft.kelas
                    ? 'border-toba bg-toba text-white'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                )}
              >
                Semua
              </button>
              {KELAS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => set('kelas', draft.kelas === option.value ? '' : option.value)}
                  title={KELAS_DESCRIPTION[option.value]}
                  className={cn(
                    'rounded-xl border px-2 py-2 text-xs font-bold transition',
                    draft.kelas === option.value
                      ? 'border-toba bg-toba text-white'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                  )}
                >
                  {option.value}
                </button>
              ))}
            </div>
          </fieldset>

          <fieldset>
            <legend className="mb-2 text-xs font-bold text-slate-700">Jenis rumah sakit</legend>
            <div className="grid grid-cols-3 gap-1.5">
              <button
                type="button"
                onClick={() => set('jenis', '')}
                className={cn(
                  'rounded-xl border px-2 py-2 text-xs font-semibold transition',
                  !draft.jenis
                    ? 'border-toba bg-toba text-white'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                )}
              >
                Semua
              </button>
              {JENIS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => set('jenis', draft.jenis === option.value ? '' : option.value)}
                  className={cn(
                    'rounded-xl border px-2 py-2 text-xs font-semibold transition',
                    draft.jenis === option.value
                      ? 'border-toba bg-toba text-white'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                  )}
                >
                  {option.value}
                </button>
              ))}
            </div>
          </fieldset>

          <label className="block">
            <span className="mb-1.5 block text-xs font-bold text-slate-700">Kabupaten / Kota</span>
            <select
              value={draft.kabkota}
              onChange={(event) => set('kabkota', event.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-800 outline-none transition focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/15"
            >
              <option value="">Semua wilayah Sumatera Utara</option>
              {(options.kabkota || []).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="block">
            <span className="mb-1.5 block text-xs font-bold text-slate-700">Layanan &amp; Spesialisasi Medis</span>
            <select
              value={draft.layanan}
              onChange={(event) => set('layanan', event.target.value)}
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm text-slate-800 outline-none transition focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/15"
            >
              <option value="">Semua layanan klinis</option>
              {(options.layanan || []).map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>

          <label className="flex cursor-pointer items-start gap-3 rounded-xl border border-slate-200 bg-toba-mist/50 p-3.5">
            <input
              type="checkbox"
              checked={draft.bpjs}
              onChange={(event) => set('bpjs', event.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-slate-300 text-toba focus:ring-toba"
            />
            <span>
              <span className="block text-sm font-bold text-slate-800">Hanya menerima BPJS</span>
              <span className="mt-0.5 block text-[11px] leading-relaxed text-slate-500">
                Tampilkan fasilitas yang tercatat menerima pasien BPJS Kesehatan.
              </span>
            </span>
          </label>
        </div>

        <footer className="flex items-center gap-2 border-t border-slate-200 px-5 py-4">
          <button
            type="button"
            onClick={() => {
              setDraft({ ...EMPTY });
              onReset?.();
            }}
            className="rounded-full border border-slate-300 px-4 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={() => onApply({ ...draft })}
            className="flex flex-1 items-center justify-center gap-1.5 rounded-full bg-toba px-4 py-2.5 text-xs font-bold text-white transition hover:bg-toba-dark"
          >
            <span className="material-symbols-outlined text-[16px]">tune</span>
            Terapkan filter
            {activeCount ? (
              <span className="ml-1 rounded-full bg-white/20 px-1.5 text-[10px]">{activeCount}</span>
            ) : null}
          </button>
        </footer>
      </aside>
    </div>,
    document.body,
  );
}
