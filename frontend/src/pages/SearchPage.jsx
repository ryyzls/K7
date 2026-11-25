import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { compareHospitals, getFilterOptions, searchHospitals } from '../api';
import { sortHospitals } from '../utils';
import HospitalCard from '../components/HospitalCard';
import CompareDock from '../components/CompareDock';
import CompareModal from '../components/CompareModal';
import SearchAutocomplete from '../components/SearchAutocomplete';

const STORAGE_KEY = 'carisehat_filter_ctx';

function readStoredContext() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function writeStoredContext(ctx) {
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(ctx));
  } catch {
    // Ignore storage errors
  }
}

export default function SearchPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  // Load initial from params or sessionStorage
  const storedCtx = useMemo(() => readStoredContext(), []);

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState(false);
  const [searchMeta, setSearchMeta] = useState({});
  const [omit, setOmit] = useState([]);
  const [retryTick, setRetryTick] = useState(0);
  const hasLoadedRef = useRef(false);
  const [debouncedQ, setDebouncedQ] = useState(searchParams.get('q') || storedCtx.q || '');
  const [options, setOptions] = useState({ kabkota: [], layanan: [] });

  // Filters state
  const [q, setQ] = useState(searchParams.get('q') || storedCtx.q || '');
  const [kabkota, setKabkota] = useState(searchParams.get('kabkota') || storedCtx.kabkota || '');
  const [kelas, setKelas] = useState(searchParams.get('kelas') || storedCtx.kelas || '');
  const [jenis, setJenis] = useState(searchParams.get('jenis') || storedCtx.jenis || '');
  const [layanan, setLayanan] = useState(searchParams.get('layanan') || storedCtx.layanan || '');
  const [sort, setSort] = useState(searchParams.get('sort') || storedCtx.sort || 'relevan');
  const [currentPage, setCurrentPage] = useState(Number(searchParams.get('page')) || storedCtx.page || 1);
  const [perPage, setPerPage] = useState(Number(searchParams.get('perPage')) || storedCtx.perPage || 20);

  // Compare state
  const [compareIds, setCompareIds] = useState(() => {
    const p = searchParams.get('compare');
    return p ? p.split(',').map((s) => s.trim()).filter(Boolean) : [];
  });
  const [compareData, setCompareData] = useState(null);
  const [showCompareModal, setShowCompareModal] = useState(false);

  // Fetch filter options once
  useEffect(() => {
    getFilterOptions()
      .then((data) => {
        setOptions({
          kabkota: data.kabkota || [],
          layanan: data.layanan || [],
        });
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    setOmit((prev) => (prev.length > 0 ? [] : prev));
    const timer = setTimeout(() => setDebouncedQ(q), 300);
    return () => clearTimeout(timer);
  }, [q]);

  const omitKey = omit.join('|');

  // Fetch hospitals whenever search filters change (keepPreviousData pattern)
  useEffect(() => {
    let active = true;
    const controller = new AbortController();
    if (!hasLoadedRef.current) {
      setLoading(true);
    } else {
      setIsUpdating(true);
    }
    setError(false);

    // Save to sessionStorage
    writeStoredContext({
      q,
      kabkota,
      kelas,
      jenis,
      layanan,
      sort,
      page: currentPage,
      perPage,
    });

    searchHospitals({
      q: debouncedQ,
      omit: omitKey,
      kabkota,
      kelas,
      jenis,
      layanan,
      limit: 500,
    }, controller.signal)
      .then((data) => {
        if (!active) return;
        hasLoadedRef.current = true;
        setItems(data.items || []);
        setSearchMeta(data);
        setError(false);
        setLoading(false);
        setIsUpdating(false);
      })
      .catch((err) => {
        if (!active || err?.name === 'AbortError' || controller.signal.aborted) return;
        if (!hasLoadedRef.current) {
          setItems([]);
          setSearchMeta({});
        }
        setError(true);
        setLoading(false);
        setIsUpdating(false);
      });

    return () => {
      active = false;
      controller.abort();
    };
  }, [debouncedQ, kabkota, kelas, jenis, layanan, omitKey, retryTick]);

  // Restore scroll position when returning to /pencarian
  useEffect(() => {
    if (loading) return;
    try {
      const saved = sessionStorage.getItem('carisehat_search_scroll');
      if (saved) {
        const y = Number(saved);
        sessionStorage.removeItem('carisehat_search_scroll');
        if (Number.isFinite(y) && y > 0) {
          requestAnimationFrame(() => window.scrollTo({ top: y, behavior: 'instant' }));
        }
      }
    } catch {
      // ignore storage errors
    }
  }, [loading]);

  // Save scroll position when navigating away from /pencarian
  useEffect(() => {
    const saveScroll = () => {
      try {
        sessionStorage.setItem('carisehat_search_scroll', String(window.scrollY));
      } catch {
        // ignore
      }
    };
    return () => saveScroll();
  }, []);

  // Sync compare URL param with compareIds
  useEffect(() => {
    const p = searchParams.get('compare');
    if (p) {
      const ids = p.split(',').map((s) => s.trim()).filter(Boolean);
      if (ids.length > 0) {
        setCompareIds(ids);
      }
    }
  }, [searchParams]);

  // Fetch compare matrix when compareIds has at least 2 hospitals
  useEffect(() => {
    if (compareIds.length < 2) {
      setCompareData(null);
      return;
    }
    let cancelled = false;
    compareHospitals(compareIds)
      .then((data) => {
        if (!cancelled) {
          setCompareData(data);
          setShowCompareModal(true);
        }
      })
      .catch(() => {
        if (!cancelled) {
          setCompareData(null);
          setShowCompareModal(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [compareIds]);

  const handleToggleCompare = (id) => {
    setCompareIds((prev) => {
      let updated;
      if (prev.includes(id)) {
        updated = prev.filter((x) => x !== id);
      } else {
        if (prev.length >= 2) {
          alert('Maksimal membandingkan 2 rumah sakit sekaligus.');
          return prev;
        }
        updated = [...prev, id];
      }
      return updated;
    });
  };

  const handleRemoveCompare = (id) => {
    setCompareIds((prev) => prev.filter((x) => x !== id));
  };

  const handleClearCompare = () => {
    setCompareIds([]);
    setCompareData(null);
    setShowCompareModal(false);
  };

  const handleOpenCompareModal = () => {
    if (compareIds.length < 2) {
      alert('Pilih minimal 2 rumah sakit untuk dibandingkan.');
      return;
    }
    if (compareData) {
      setShowCompareModal(true);
    } else {
      compareHospitals(compareIds).then((data) => {
        setCompareData(data);
        setShowCompareModal(true);
      });
    }
  };

  // Reset all filters
  const handleResetFilters = () => {
    setQ('');
    setKabkota('');
    setKelas('');
    setJenis('');
    setLayanan('');
    setSort('relevan');
    setCurrentPage(1);
    setSearchParams({});
    try {
      sessionStorage.removeItem(STORAGE_KEY);
    } catch {}
  };

  // Sorted items
  const sortedItems = useMemo(() => {
    return sortHospitals(items, sort);
  }, [items, sort]);

  // Paginated items
  const totalPages = Math.max(1, Math.ceil(sortedItems.length / perPage));
  const validPage = Math.min(Math.max(1, currentPage), totalPages);
  const startIdx = (validPage - 1) * perPage;
  const pageItems = sortedItems.slice(startIdx, startIdx + perPage);

  const hasFilter = Boolean(q || kabkota || kelas || jenis || layanan);

  return (
    <div className="min-h-screen bg-white">
      {/* Navbar */}
      <header className="d-head">
        <div className="d-head-inner">
          <Link className="brand" to="/" aria-label="CariSehat, Beranda">
            <img className="brand-image" src="/images/cari-sehat-logo.png" alt="Cari Sehat" width="190" height="64" />
          </Link>
          <nav className="d-site-nav" aria-label="Menu utama">
            <Link to="/">Beranda</Link>
            <Link to="/pencarian" aria-current="page">Cari Rumah Sakit</Link>
            <Link to="/peta">Peta</Link>
            <a href="/#about">Tentang</a>
          </nav>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
            <Link className="btn btn-ghost" to="/peta">
              <i className="fa-solid fa-map-location-dot" aria-hidden="true" style={{ color: 'var(--toba)' }} />
              <span>Buka Peta</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Explorer Catalog Main */}
      <main id="explorer">
        <aside>
          <div className="explorer-header">
            <div className="catalog-title">
              <h2>Daftar Rumah Sakit</h2>
              <div id="status" aria-live="polite">
                {loading || isUpdating ? (
                  <span className="inline-flex items-center gap-2 text-slate-500">
                    <span className="spin" />
                    <span>{loading ? 'Memuat rumah sakit...' : 'Memperbarui hasil...'}</span>
                  </span>
                ) : error ? (
                  <span className="text-rose-600 font-semibold">
                    <i className="fa-solid fa-triangle-exclamation" /> Koneksi ke backend terputus
                  </span>
                ) : null}
              </div>
            </div>

            <label className="sort-control" htmlFor="sort">
              Urutkan:
              <select
                id="sort"
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value);
                  setCurrentPage(1);
                }}
                aria-label="Urutkan hasil katalog"
              >
                <option value="relevan">Relevansi</option>
                <option value="nama">Nama Rumah Sakit (A-Z)</option>
                <option value="kelas">Kelas (A ke D)</option>
              </select>
            </label>
          </div>

          <div aria-live="polite" className="search-meta-bar space-y-2 text-sm text-slate-600">
            {!loading && !error && (
              <p className="font-medium text-slate-700">
                {items.length} rumah sakit ditemukan
                {isUpdating && <span className="ml-2 text-xs font-normal text-slate-400">(memperbarui...)</span>}
              </p>
            )}
            {error && items.length > 0 && (
              <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-xs text-rose-700">
                <span>Gagal memperbarui hasil pencarian. Menampilkan hasil sebelumnya.</span>
                <button
                  type="button"
                  onClick={() => setRetryTick((t) => t + 1)}
                  className="rounded-lg bg-rose-600 px-2.5 py-1 font-semibold text-white hover:bg-rose-700"
                >
                  Coba Lagi
                </button>
              </div>
            )}
            {searchMeta.corrections?.length > 0 && <p>Menampilkan hasil untuk {searchMeta.corrections.map(c => c.to).join(', ')}.</p>}
            {searchMeta.did_you_mean?.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span>Apakah maksud Anda:</span>
                {searchMeta.did_you_mean.map((term) => (
                  <button
                    key={term}
                    type="button"
                    onClick={() => {
                      setQ(term);
                      setDebouncedQ(term);
                      setCurrentPage(1);
                    }}
                    className="rounded-full border border-slate-300 bg-white px-3 py-0.5 text-xs font-semibold text-teal-800 hover:bg-teal-50"
                  >
                    {term}
                  </button>
                ))}
              </div>
            )}
            {searchMeta.notices?.map(notice => <p key={notice}>{notice}</p>)}
            <div className="flex flex-wrap gap-2">
              {searchMeta.recognized_filters?.map(filter => <button type="button" key={filter.id}
                onClick={() => setOmit(values => [...values, filter.id])}
                aria-label={`Hapus filter ${filter.label}`}
                className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-teal-800">
                {filter.label} <i className="fa-solid fa-xmark ml-1" aria-hidden="true" />
              </button>)}
            </div>
          </div>
          {/* Filters Form */}
          <form className="filters" onSubmit={(e) => e.preventDefault()} role="search" aria-label="Filter katalog rumah sakit">
            <div className="search" style={{ position: 'relative' }}>
              <i
                className="fa-solid fa-magnifying-glass"
                style={{
                  position: 'absolute',
                  left: '1rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  color: 'var(--mute)',
                }}
                aria-hidden="true"
              />
              <SearchAutocomplete
                id="search-input"
                type="search"
                placeholder="Cari nama rumah sakit, lokasi, layanan, atau fasilitas..."
                value={q}
                onChange={(value) => {
                  setQ(value);
                  setCurrentPage(1);
                }}
                onChoose={(value) => {
                  setQ(value);
                  setDebouncedQ(value);
                  setCurrentPage(1);
                }}
                style={{ paddingLeft: '2.5rem' }}
                aria-label="Cari nama rumah sakit"
              />
            </div>

            <div className="filter-grid">
              <label>
                Kabupaten/kota
                <select
                  id="kab"
                  value={kabkota}
                  onChange={(e) => {
                    setKabkota(e.target.value);
                    setCurrentPage(1);
                  }}
                  aria-label="Pilih kabupaten atau kota"
                >
                  <option value="">Semua Wilayah (33 Kab/Kota)</option>
                  {options.kabkota.map((k) => (
                    <option key={k} value={k}>
                      {k}
                    </option>
                  ))}
                </select>
              </label>

              <label>
                Kelas Rumah Sakit
                <select
                  id="kelas"
                  value={kelas}
                  onChange={(e) => {
                    setKelas(e.target.value);
                    setCurrentPage(1);
                  }}
                  aria-label="Pilih kelas rumah sakit"
                >
                  <option value="">Semua Kelas</option>
                  <option value="A">Kelas A</option>
                  <option value="B">Kelas B</option>
                  <option value="C">Kelas C</option>
                  <option value="D">Kelas D</option>
                </select>
              </label>

              <label>
                Jenis Rumah Sakit
                <select
                  id="jenis"
                  value={jenis}
                  onChange={(e) => {
                    setJenis(e.target.value);
                    setCurrentPage(1);
                  }}
                  aria-label="Pilih jenis rumah sakit"
                >
                  <option value="">Semua Jenis Rumah Sakit</option>
                  <option value="Umum">Rumah Sakit Umum (RSU)</option>
                  <option value="Khusus">Rumah Sakit Khusus (RSK)</option>
                </select>
              </label>

              <label>
                Layanan Medis
                <select
                  id="lay"
                  value={layanan}
                  onChange={(e) => {
                    setLayanan(e.target.value);
                    setCurrentPage(1);
                  }}
                  aria-label="Pilih layanan medis"
                >
                  <option value="">Semua Layanan Spesialisasi</option>
                  {options.layanan.map((l) => (
                    <option key={l} value={l}>
                      {l}
                    </option>
                  ))}
                </select>
              </label>

              {hasFilter && (
                <div className="filter-reset-row">
                  <button
                    className="link-btn"
                    id="reset"
                    type="button"
                    onClick={handleResetFilters}
                    title="Bersihkan semua filter"
                  >
                    Reset Filter
                  </button>
                </div>
              )}
            </div>
          </form>

          {/* Hospital Card List */}
          {loading && items.length === 0 ? (
            <ul className="hospital-grid" aria-label="Memuat katalog rumah sakit" aria-busy="true">
              {Array.from({ length: 6 }, (_, idx) => (
                <li key={idx} className="card skeleton-card" aria-hidden="true">
                  <div className="card-thumb skeleton-box" />
                  <div className="p-4 space-y-3">
                    <div className="skeleton-line w-3/4" />
                    <div className="skeleton-line w-1/2" />
                    <div className="skeleton-line w-full" />
                  </div>
                </li>
              ))}
            </ul>
          ) : error && items.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
              <h3 style={{ color: 'var(--emergency)', fontWeight: 800 }}>Server belum terhubung</h3>
              <p style={{ color: 'var(--mute)' }}>Pastikan backend API berjalan, lalu coba lagi.</p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setRetryTick((t) => t + 1)}
                style={{ marginTop: '1rem' }}
              >
                Coba Lagi
              </button>
            </div>
          ) : !loading && !isUpdating && pageItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
              <h3 style={{ fontWeight: 800 }}>Tidak ada hasil</h3>
              <p style={{ color: 'var(--mute)' }}>
                Tidak ada rumah sakit yang cocok dengan filter yang dipilih. Coba ubah kata kunci atau reset filter.
              </p>
              {searchMeta.did_you_mean?.length > 0 && (
                <div className="mt-3 flex flex-wrap justify-center items-center gap-2 text-sm">
                  <span className="text-slate-500">Apakah maksud Anda:</span>
                  {searchMeta.did_you_mean.map((term) => (
                    <button
                      key={term}
                      type="button"
                      onClick={() => {
                        setQ(term);
                        setDebouncedQ(term);
                        setCurrentPage(1);
                      }}
                      className="rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold text-teal-800 hover:bg-teal-100"
                    >
                      {term}
                    </button>
                  ))}
                </div>
              )}
              <button
                type="button"
                className="btn btn-ghost"
                onClick={handleResetFilters}
                style={{ marginTop: '1rem' }}
              >
                Reset Filter
              </button>
            </div>
          ) : (
            <ul
              id="list"
              className={`hospital-grid ${isUpdating ? 'is-updating' : ''}`}
              aria-label="Daftar katalog rumah sakit"
              aria-busy={isUpdating}
            >
              {pageItems.map((h) => (
                <li key={h.id}>
                  <HospitalCard
                    hospital={h}
                    compareSelected={compareIds.includes(h.id)}
                    onCompareToggle={handleToggleCompare}
                  />
                </li>
              ))}
            </ul>
          )}

          {/* Pagination Bar */}
          {!loading && sortedItems.length > 0 && (
            <div className="pagination-bar" id="pagination">
              <div className="per-page-wrap">
                <span>Tampilkan</span>
                <select
                  id="per-page"
                  value={String(perPage)}
                  onChange={(e) => {
                    setPerPage(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  aria-label="Jumlah Rumah Sakit per halaman"
                >
                  <option value="10">10</option>
                  <option value="20">20</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                </select>
                <span>Rumah Sakit per halaman</span>
              </div>

              <div className="pagination-controls" id="pg-controls">
                <button
                  type="button"
                  className="pg-btn"
                  disabled={validPage <= 1}
                  onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                  aria-label="Halaman sebelumnya"
                >
                  &larr;
                </button>

                {Array.from({ length: totalPages }, (_, i) => i + 1)
                  .filter((p) => p === 1 || p === totalPages || Math.abs(p - validPage) <= 1)
                  .map((p, idx, arr) => (
                    <span key={p} style={{ display: 'inline-flex', alignItems: 'center' }}>
                      {idx > 0 && arr[idx - 1] !== p - 1 && <span style={{ padding: '0 4px', color: 'var(--mute)' }}>...</span>}
                      <button
                        type="button"
                        className={`pg-btn ${p === validPage ? 'active' : ''}`}
                        onClick={() => setCurrentPage(p)}
                      >
                        {p}
                      </button>
                    </span>
                  ))}

                <button
                  type="button"
                  className="pg-btn"
                  disabled={validPage >= totalPages}
                  onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                  aria-label="Halaman berikutnya"
                >
                  &rarr;
                </button>
              </div>
            </div>
          )}
        </aside>
      </main>

      {/* Floating Compare Dock */}
      <CompareDock
        comparedIds={compareIds}
        hospitals={items}
        onRemove={handleRemoveCompare}
        onClear={handleClearCompare}
        onOpenCompare={handleOpenCompareModal}
      />

      {/* Compare Modal Dialog */}
      <CompareModal
        open={showCompareModal}
        compareData={compareData}
        onClose={() => setShowCompareModal(false)}
        onRemove={handleRemoveCompare}
      />
    </div>
  );
}
