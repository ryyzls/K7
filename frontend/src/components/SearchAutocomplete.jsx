import { useEffect, useMemo, useRef, useState } from 'react';
import { cn } from '../utils';
import { buildAutocompleteSuggestions } from '../smartSearch';

export default function SearchAutocomplete({
  value = '',
  onChange,
  onSubmit,
  onSelectHospital,
  onSelectService,
  onSelectRegion,
  hospitals = [],
  options = {},
  placeholder = 'Cari nama rumah sakit, poliklinik, keluhan, atau wilayah...',
  buttonLabel = 'Cari Rumah Sakit',
  compact = false,
}) {
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef(null);

  const suggestions = useMemo(
    () => buildAutocompleteSuggestions(value, hospitals, options),
    [value, hospitals, options],
  );

  const flatItems = useMemo(() => {
    const list = [];
    suggestions.hospitals.forEach((h) => list.push({ type: 'hospital', data: h }));
    suggestions.services.forEach((s) => list.push({ type: 'service', data: s }));
    suggestions.regions.forEach((r) => list.push({ type: 'region', data: r }));
    return list;
  }, [suggestions]);

  useEffect(() => {
    setActiveIndex(-1);
  }, [value]);

  useEffect(() => {
    const handleOutside = (event) => {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setOpen(false);
      }
    };
    document.addEventListener('mousedown', handleOutside);
    return () => document.removeEventListener('mousedown', handleOutside);
  }, []);

  const chooseFlatItem = (item) => {
    if (!item) return;
    setOpen(false);
    if (item.type === 'hospital') {
      onSelectHospital?.(item.data);
    } else if (item.type === 'service') {
      onSelectService?.(item.data);
    } else if (item.type === 'region') {
      onSelectRegion?.(item.data);
    }
  };

  const handleKeyDown = (event) => {
    if (!open || !flatItems.length) {
      if (event.key === 'Enter') {
        setOpen(false);
      }
      return;
    }

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((prev) => (prev + 1) % flatItems.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((prev) => (prev <= 0 ? flatItems.length - 1 : prev - 1));
    } else if (event.key === 'Enter' && activeIndex >= 0) {
      event.preventDefault();
      chooseFlatItem(flatItems[activeIndex]);
    } else if (event.key === 'Escape') {
      setOpen(false);
    }
  };

  let cursor = -1;

  return (
    <div ref={containerRef} className="relative w-full">
      <form
        onSubmit={(event) => {
          event.preventDefault();
          setOpen(false);
          onSubmit?.(value);
        }}
        className={cn(
          'flex flex-col gap-2 sm:flex-row sm:items-center',
          compact
            ? 'rounded-xl border border-slate-200 bg-white p-2 shadow-card'
            : '',
        )}
      >
        <div className="relative flex-1">
          <span
            className={cn(
              'pointer-events-none absolute top-1/2 -translate-y-1/2 text-slate-400',
              compact ? 'left-4' : 'left-3.5',
            )}
          >
            <span className="material-symbols-outlined text-lg">search</span>
          </span>
          <input
            type="text"
            value={value}
            onFocus={() => setOpen(true)}
            onChange={(event) => {
              onChange?.(event.target.value);
              setOpen(true);
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className={cn(
              'w-full text-sm font-medium text-slate-900 outline-none transition-colors duration-150 placeholder:text-slate-400',
              compact
                ? 'rounded-lg bg-transparent py-3 pl-11 pr-9'
                : 'rounded-full border border-slate-200 bg-slate-50 py-3 pl-10 pr-10 hover:bg-slate-100/70 focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/20',
            )}
            aria-label={placeholder}
            autoComplete="off"
          />
          {value ? (
            <button
              type="button"
              onClick={() => {
                onChange?.('');
                setOpen(false);
              }}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 text-slate-400 transition hover:text-slate-700"
              aria-label="Hapus teks pencarian"
            >
              <span className="material-symbols-outlined text-lg">close</span>
            </button>
          ) : null}
        </div>

        <button
          type="submit"
          className={cn(
            'inline-flex items-center justify-center gap-2 bg-toba font-semibold text-white shadow-sm transition-colors duration-150 hover:bg-toba-dark',
            compact ? 'rounded-lg px-6 py-3 text-sm' : 'rounded-full px-6 py-3 text-xs',
          )}
        >
          <span className="material-symbols-outlined text-base">search</span>
          <span>{buttonLabel}</span>
        </button>
      </form>

      {/* Dropdown Saran Instan Terkelompok */}
      {open && suggestions.hasAny ? (
        <div
          className="absolute left-0 right-0 top-[calc(100%+8px)] z-50 max-h-[400px] overflow-y-auto rounded-2xl border border-slate-200 bg-white p-2 shadow-modal scrollbar-thin"
          role="listbox"
        >
          {suggestions.hospitals.length > 0 ? (
            <div className="mb-2">
              <p className="px-3 py-1 text-xs font-medium text-slate-500">
                Rumah sakit
              </p>
              {suggestions.hospitals.map((h) => {
                cursor += 1;
                const idx = cursor;
                return (
                  <button
                    key={h.id}
                    type="button"
                    onClick={() => chooseFlatItem({ type: 'hospital', data: h })}
                    className={cn(
                      'flex w-full items-center justify-between gap-3 rounded-xl px-3 py-2 text-left transition-colors duration-150',
                      activeIndex === idx ? 'bg-toba-mist text-toba-dark' : 'hover:bg-slate-50',
                    )}
                  >
                    <div className="flex min-w-0 items-center gap-2.5">
                      <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-toba-mist text-toba">
                        <span className="material-symbols-outlined text-lg">local_hospital</span>
                      </span>
                      <div className="min-w-0">
                        <p className="truncate text-xs font-medium text-slate-900">{h.nama}</p>
                        <p className="truncate text-xs text-slate-500">
                          {h.kabkota || 'Sumatera Utara'}
                        </p>
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-1">
                      <span className="rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">
                        Kelas {h.kelas || '—'}
                      </span>
                      {h.bpjs ? (
                        <span className="rounded bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700">
                          BPJS
                        </span>
                      ) : null}
                    </div>
                  </button>
                );
              })}
            </div>
          ) : null}

          {suggestions.services.length > 0 ? (
            <div className="mb-2 border-t border-slate-100 pt-2">
              <p className="px-3 py-1 text-xs font-medium text-slate-500">
                Layanan dan keluhan medis
              </p>
              {suggestions.services.map((srv) => {
                cursor += 1;
                const idx = cursor;
                return (
                  <button
                    key={srv.label}
                    type="button"
                    onClick={() => chooseFlatItem({ type: 'service', data: srv })}
                    className={cn(
                      'flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left transition-colors duration-150',
                      activeIndex === idx ? 'bg-toba-mist text-toba-dark' : 'hover:bg-slate-50',
                    )}
                  >
                    <span className="flex items-center gap-2 text-xs font-semibold text-slate-800">
                      <span className="material-symbols-outlined text-base text-toba">
                        medical_services
                      </span>
                      {srv.label}
                    </span>
                    <span className="text-xs font-medium text-toba-dark">Cari layanan</span>
                  </button>
                );
              })}
            </div>
          ) : null}

          {suggestions.regions.length > 0 ? (
            <div className="border-t border-slate-100 pt-2">
              <p className="px-3 py-1 text-xs font-medium text-slate-500">
                Kabupaten/kota
              </p>
              {suggestions.regions.map((reg) => {
                cursor += 1;
                const idx = cursor;
                return (
                  <button
                    key={reg}
                    type="button"
                    onClick={() => chooseFlatItem({ type: 'region', data: reg })}
                    className={cn(
                      'flex w-full items-center justify-between gap-2 rounded-xl px-3 py-2 text-left transition-colors duration-150',
                      activeIndex === idx ? 'bg-toba-mist text-toba-dark' : 'hover:bg-slate-50',
                    )}
                  >
                    <span className="flex items-center gap-2 text-xs font-semibold text-slate-800">
                      <span className="material-symbols-outlined text-base text-slate-500">
                        location_on
                      </span>
                      {reg}
                    </span>
                    <span className="text-xs font-medium text-slate-600">Lihat rumah sakit</span>
                  </button>
                );
              })}
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
}
