import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { getFilterOptions, searchHospitals } from '../api';
import { KELAS_OPTIONS } from '../constants';
import { cn, pageList, sortHospitals } from '../utils';
import { useApp } from '../context/AppContext';
import SiteHeader from '../components/SiteHeader';
import HospitalCard from '../components/HospitalCard';
import LeafletMap from '../components/LeafletMap';
import SearchFilterPanel, { countActiveFilters } from '../components/SearchFilterPanel';
import { MinimalFooter } from '../components/Footer';

const PER_PAGE = 12;

function SkeletonGrid() {
  return (
    <div className="grid grid-cols-1 gap-5 sm:grid-cols-2">
      {Array.from({ length: 6 }).map((_, index) => (
        <div key={index} className="overflow-hidden rounded-2xl border border-slate-200 bg-white">
          <div className="h-[185px] animate-pulse bg-slate-100" />
          <div className="space-y-3 p-5">
            <div className="h-4 w-4/5 animate-pulse rounded bg-slate-100" />
            <div className="h-3 w-1/2 animate-pulse rounded bg-slate-100" />
            <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
            <div className="h-8 w-full animate-pulse rounded-full bg-slate-100" />
          </div>
        </div>
      ))}
    </div>
  );
}

export default function SearchPage() {
  const navigate = useNavigate();
  const { toggleFavorite, isFavorite } = useApp();
  const [searchParams, setSearchParams] = useSearchParams();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [options, setOptions] = useState({ kabkota: [], layanan: [] });
  const [filterOpen, setFilterOpen] = useState(false);
  const [showMap, setShowMap] = useState(true);
  const resultsRef = useRef(null);

  const filters = useMemo(
    () => ({
      q: searchParams.get('q') || '',
      kelas: searchParams.get('kelas') || '',
      jenis: searchParams.get('jenis') || '',
      kabkota: searchParams.get('kabkota') || '',
      layanan: searchParams.get('layanan') || '',
      bpjs: searchParams.get('bpjs') === '1',
    }),
    [searchParams],
  );

  const sort = searchParams.get('sort') || 'relevan';
  const page = Math.max(1, Number(searchParams.get('page')) || 1);
  const filterKey = `${filters.q}|${filters.kelas}|${filters.jenis}|${filters.kabkota}|${filters.layanan}`;
  const activeCount = countActiveFilters(filters);

  useEffect(() => {
    getFilterOptions()
      .then((data) => setOptions({ kabkota: data.kabkota || [], layanan: data.layanan || [] }))
      .catch(() => {
        /* filters stay empty; search still works */
      });
  }, []);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');

    searchHospitals({
      q: filters.q,
      kelas: filters.kelas,
      jenis: filters.jenis,
      kabkota: filters.kabkota,
      layanan: filters.layanan,
      limit: 500,
    })
      .then((data) => {
        if (cancelled) return;
        setItems(data.items || []);
      })
      .catch((err) => {
        if (cancelled) return;
        setItems([]);
        setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [filterKey, retry]);

  const filtered = useMemo(() => {
    const base = filters.bpjs ? items.filter((hospital) => hospital.bpjs) : items;
    return sortHospitals(base, sort);
  }, [items, filters.bpjs, sort]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const currentPage = Math.min(page, totalPages);
  const pageItems = filtered.slice((currentPage - 1) * PER_PAGE, currentPage * PER_PAGE);

  const updateParams = (patch, { resetPage = true } = {}) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(patch).forEach(([key, value]) => {
      if (value === '' || value === null || value === undefined || value === false) next.delete(key);
      else next.set(key, value === true ? '1' : String(value));
    });
    if (resetPage) next.delete('page');
    setSearchParams(next);
  };

  const applyFilters = (draft) => {
    updateParams(
      {
        q: draft.q.trim(),
        kelas: draft.kelas,
        jenis: draft.jenis,
        kabkota: draft.kabkota,
        layanan: draft.layanan,
        bpjs: draft.bpjs ? '1' : '',
      },
      { resetPage: true },
    );
    setFilterOpen(false);
    window.setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 80);
  };

  const resetFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  const goPage = (nextPage) => {
    const next = new URLSearchParams(searchParams);
    if (nextPage <= 1) next.delete('page');
    else next.set('page', String(nextPage));
    setSearchParams(next);
    window.setTimeout(() => resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }), 40);
  };

  const chips = [
    filters.q && { key: 'q', label: `“${filters.q}”` },
    filters.kelas && { key: 'kelas', label: `Kelas ${filters.kelas}` },
    filters.jenis && { key: 'jenis', label: `RS ${filters.jenis}` },
    filters.kabkota && { key: 'kabkota', label: filters.kabkota },
    filters.layanan && { key: 'layanan', label: filters.layanan },
    filters.bpjs && { key: 'bpjs', label: 'BPJS' },
  ].filter(Boolean);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <SiteHeader
        active="direktori"
        initialQuery={filters.q}
        onFilterClick={() => setFilterOpen(true)}
        filterActive={activeCount > 0}
      />

      <main className="flex-1">
        {/* Page header */}
        <section className="border-b border-slate-200 bg-white">
          <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
            <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-end">
              <div>
                <div className="mb-1 flex items-center gap-2 text-[10.5px] font-bold uppercase tracking-[0.15em] text-brand-blue">
                  <span className="h-2 w-2 rounded-full bg-brand-blue" />
                  Wilayah faskes terverifikasi
                </div>
                <h1 className="font-heading text-2xl font-extrabold tracking-tight text-brand-navy md:text-3xl">
                  Direktori Rumah Sakit Sumatera Utara
                </h1>
                <p className="mt-1 text-sm text-slate-500">
                  {loading ? (
                    'Memuat data rumah sakit...'
                  ) : activeCount > 0 ? (
                    <>
                      Menampilkan{' '}
                      <span className="font-bold text-brand-navy">{filtered.length} rumah sakit</span> dari
                      katalog semantik Kemenkes RI &amp; BPJS SatuSehat.
                    </>
                  ) : (
                    <>
                      Menampilkan{' '}
                      <span className="font-bold text-brand-navy">seluruh rumah sakit</span> dari
                      katalog semantik Kemenkes RI &amp; BPJS SatuSehat.
                    </>
                  )}
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-2.5">
                <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs">
                  <span className="font-medium text-slate-500">Urutkan</span>
                  <select
                    value={sort}
                    onChange={(event) => updateParams({ sort: event.target.value })}
                    className="cursor-pointer bg-transparent text-xs font-bold text-brand-navy outline-none"
                    aria-label="Urutkan hasil"
                  >
                    <option value="relevan">Paling relevan</option>
                    <option value="nama">Nama A–Z</option>
                    <option value="kelas">Kelas</option>
                    <option value="wilayah">Wilayah</option>
                  </select>
                </label>

                <button
                  type="button"
                  onClick={() => updateParams({ bpjs: filters.bpjs ? '' : '1' })}
                  className={cn(
                    'inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-bold transition',
                    filters.bpjs
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-200 hover:text-emerald-700',
                  )}
                  aria-pressed={filters.bpjs}
                >
                  <span className="material-symbols-outlined text-[15px]">verified</span>
                  BPJS aktif
                </button>

                <button
                  type="button"
                  onClick={() => setShowMap((current) => !current)}
                  className={cn(
                    'hidden items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-bold transition lg:inline-flex',
                    showMap
                      ? 'border-brand-blue bg-blue-50 text-brand-blue'
                      : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50',
                  )}
                  aria-pressed={showMap}
                >
                  <span className="material-symbols-outlined text-[15px]">map</span>
                  Peta
                </button>
              </div>
            </div>

            <div className="mt-5 flex flex-wrap items-center gap-2">
              <button
                type="button"
                onClick={() => setFilterOpen(true)}
                className="inline-flex items-center gap-1.5 rounded-full bg-brand-navy px-3.5 py-1.5 text-[11px] font-semibold text-white transition hover:bg-brand-blue lg:hidden"
              >
                <span className="material-symbols-outlined text-[14px]">tune</span>
                Filter
                {activeCount ? (
                  <span className="rounded-full bg-white/20 px-1.5 text-[10px]">{activeCount}</span>
                ) : null}
              </button>

              <span className="text-[10.5px] font-bold uppercase tracking-wide text-slate-400">
                Kelas:
              </span>
              <button
                type="button"
                onClick={() => updateParams({ kelas: '' })}
                className={cn(
                  'rounded-full border px-3 py-1 text-[11px] font-semibold transition',
                  !filters.kelas
                    ? 'border-brand-navy bg-brand-navy text-white'
                    : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                )}
              >
                Semua
              </button>
              {KELAS_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => updateParams({ kelas: option.value })}
                  className={cn(
                    'rounded-full border px-3 py-1 text-[11px] font-bold transition',
                    filters.kelas === option.value
                      ? 'border-brand-navy bg-brand-navy text-white'
                      : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                  )}
                >
                  {option.value}
                </button>
              ))}

              {chips.length ? (
                <button
                  type="button"
                  onClick={resetFilters}
                  className="ml-auto inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 transition hover:text-rose-600"
                >
                  <span className="material-symbols-outlined text-[14px]">close</span>
                  Reset semua
                </button>
              ) : null}
            </div>

            {chips.length ? (
              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                {chips.map((chip) => (
                  <button
                    key={chip.key}
                    type="button"
                    onClick={() => updateParams({ [chip.key]: '' })}
                    className="inline-flex items-center gap-1 rounded-full border border-blue-100 bg-blue-50 px-2.5 py-1 text-[10.5px] font-semibold text-brand-blue transition hover:bg-blue-100"
                  >
                    {chip.label}
                    <span className="material-symbols-outlined text-[13px]">close</span>
                  </button>
                ))}
              </div>
            ) : null}
          </div>
        </section>

        <section ref={resultsRef} className="scroll-mt-20">
          <div className="mx-auto max-w-7xl px-4 py-7 sm:px-6 lg:px-8">
            {error ? (
              <div className="rounded-2xl border border-rose-200 bg-white p-10 text-center shadow-card">
                <span className="material-symbols-outlined text-[40px] text-rose-400">wifi_off</span>
                <h2 className="mt-2 font-heading text-lg font-bold text-slate-900">
                  Server belum terhubung
                </h2>
                <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                  Pastikan backend dan Fuseki berjalan, lalu coba lagi. Detail: {error}
                </p>
                <button
                  type="button"
                  onClick={() => setRetry((current) => current + 1)}
                  className="mt-5 rounded-full bg-brand-navy px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-brand-blue"
                >
                  Coba lagi
                </button>
              </div>
            ) : loading ? (
              <div className={cn('grid gap-6', showMap ? 'lg:grid-cols-12' : '')}>
                <div className={showMap ? 'lg:col-span-7 xl:col-span-8' : ''}>
                  <SkeletonGrid />
                </div>
                {showMap ? (
                  <div className="hidden lg:col-span-5 lg:block xl:col-span-4">
                    <div className="h-[calc(100vh-110px)] animate-pulse rounded-2xl border border-slate-200 bg-white" />
                  </div>
                ) : null}
              </div>
            ) : pageItems.length ? (
              <div className={cn('grid gap-6', showMap ? 'lg:grid-cols-12' : '')}>
                <div className={showMap ? 'lg:col-span-7 xl:col-span-8' : ''}>
                  <div
                    className={cn(
                      'grid grid-cols-1 gap-5 sm:grid-cols-2',
                      !showMap && 'lg:grid-cols-3',
                    )}
                  >
                    {pageItems.map((hospital) => (
                      <HospitalCard
                        key={hospital.id}
                        hospital={hospital}
                        showSave
                        saved={isFavorite(hospital.id)}
                        onSave={() => toggleFavorite(hospital.id)}
                        onRoute={(item) =>
                          navigate(`/peta?rs=${encodeURIComponent(item.id)}&route=1`)
                        }
                      />
                    ))}
                  </div>

                  {totalPages > 1 ? (
                    <div className="mt-8 flex items-center justify-center border-t border-slate-200 pt-6">
                      <div className="flex items-center gap-1.5">
                        <button
                          type="button"
                          onClick={() => goPage(currentPage - 1)}
                          disabled={currentPage === 1}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                          aria-label="Halaman sebelumnya"
                        >
                          <span className="material-symbols-outlined text-[17px]">chevron_left</span>
                        </button>
                        {pageList(currentPage, totalPages).map((entry, index) =>
                          entry === '…' ? (
                            <span key={`gap-${index}`} className="px-1 text-xs text-slate-400">
                              …
                            </span>
                          ) : (
                            <button
                              key={entry}
                              type="button"
                              onClick={() => goPage(entry)}
                              className={cn(
                                'flex h-8 min-w-8 items-center justify-center rounded-lg border px-2 text-xs font-semibold transition',
                                entry === currentPage
                                  ? 'border-brand-navy bg-brand-navy text-white'
                                  : 'border-slate-200 bg-white text-slate-600 hover:bg-slate-50',
                              )}
                              aria-current={entry === currentPage ? 'page' : undefined}
                            >
                              {entry}
                            </button>
                          ),
                        )}
                        <button
                          type="button"
                          onClick={() => goPage(currentPage + 1)}
                          disabled={currentPage === totalPages}
                          className="inline-flex h-8 w-8 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
                          aria-label="Halaman berikutnya"
                        >
                          <span className="material-symbols-outlined text-[17px]">chevron_right</span>
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>

                {showMap ? (
                  <aside className="hidden lg:col-span-5 lg:block xl:col-span-4">
                    <div className="sticky top-20 overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">
                      <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3">
                        <div>
                          <p className="text-[10px] font-bold uppercase tracking-wider text-brand-blue">
                            Sebaran hasil
                          </p>
                          <p className="text-xs font-semibold text-slate-700">
                            {filtered.filter((item) => item.lat != null).length} titik terpetakan
                          </p>
                        </div>
                        <Link
                          to={`/peta?${new URLSearchParams({
                            ...(filters.kabkota ? { kabkota: filters.kabkota } : {}),
                            ...(filters.kelas ? { kelas: filters.kelas } : {}),
                          }).toString()}`}
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-brand-blue hover:underline"
                        >
                          Perbesar
                          <span className="material-symbols-outlined text-[14px]">open_in_full</span>
                        </Link>
                      </div>
                      <div className="h-[calc(100vh-190px)] min-h-[420px]">
                        <LeafletMap
                          hospitals={filtered}
                          fit
                          showLocate
                          className="h-full"
                        />
                      </div>
                    </div>
                  </aside>
                ) : null}
              </div>
            ) : (
              <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center shadow-card">
                <span className="material-symbols-outlined text-[48px] text-slate-300">
                  location_off
                </span>
                <h2 className="mt-3 font-heading text-lg font-bold text-slate-900">
                  Tidak ada hasil yang cocok
                </h2>
                <p className="mx-auto mt-1 max-w-md text-sm text-slate-500">
                  Coba ubah kata kunci, kelas, atau wilayah. Anda juga dapat mereset seluruh filter untuk
                  melihat semua fasilitas.
                </p>
                <div className="mt-5 flex flex-wrap justify-center gap-2">
                  <button
                    type="button"
                    onClick={resetFilters}
                    className="rounded-full bg-brand-navy px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-brand-blue"
                  >
                    Reset filter
                  </button>
                  <button
                    type="button"
                    onClick={() => setFilterOpen(true)}
                    className="rounded-full border border-slate-300 px-5 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    Buka panel filter
                  </button>
                </div>
              </div>
            )}
          </div>
        </section>
      </main>

      <MinimalFooter />

      <SearchFilterPanel
        open={filterOpen}
        onClose={() => setFilterOpen(false)}
        filters={filters}
        options={options}
        onApply={applyFilters}
        onReset={resetFilters}
      />
    </div>
  );
}
