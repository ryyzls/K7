import { useEffect, useMemo, useRef, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { compareHospitals, getFilterOptions, searchHospitals } from '../api';
import { sortHospitals } from '../utils';
import HospitalCard from '../components/HospitalCard';
import CompareDock from '../components/CompareDock';
import CompareModal from '../components/CompareModal';

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
  const [error, setError] = useState(false);
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

  // Fetch hospitals whenever search filters change
  useEffect(() => {
    let active = true;
    setLoading(true);
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
      q,
      kabkota,
      kelas,
      jenis,
      layanan,
    })
      .then((data) => {
        if (!active) return;
        setItems(data.items || []);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setError(true);
        setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [q, kabkota, kelas, jenis, layanan, sort, currentPage, perPage]);

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
        if (prev.length >= 3) {
          alert('Maksimal membandingkan 3 rumah sakit sekaligus.');
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
                {loading ? (
                  <>
                    <span className="spin" />
                    <span>Mencari rumah sakit...</span>
                  </>
                ) : error ? (
                  <span className="text-rose-600 font-semibold">
                    <i className="fa-solid fa-triangle-exclamation" /> Koneksi ke backend terputus
                  </span>
                ) : (
                  <span>
                    <b>{sortedItems.length}</b> rumah sakit ditemukan{' '}
                    {sortedItems.length > perPage && (
                      <>
                        halaman <b>{validPage}</b>/<b>{totalPages}</b>
                      </>
                    )}
                  </span>
                )}
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
                <option value="kelas">Kelas (A &rarr; D)</option>
              </select>
            </label>
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
              <input
                id="search-input"
                type="search"
                placeholder="Cari nama rumah sakit, layanan, alamat, atau spesialis..."
                value={q}
                onChange={(e) => {
                  setQ(e.target.value);
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
                <button
                  className="link-btn"
                  id="reset"
                  type="button"
                  onClick={handleResetFilters}
                  title="Bersihkan semua filter"
                >
                  Reset Filter
                </button>
              )}
            </div>
          </form>

          {/* Hospital Card List */}
          {loading ? (
            <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
              <div className="spin" style={{ margin: '0 auto 1rem', width: 28, height: 28, borderWidth: 3 }} />
              <p style={{ color: 'var(--mute)' }}>Memuat katalog rumah sakit...</p>
            </div>
          ) : error ? (
            <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
              <h3 style={{ color: 'var(--emergency)', fontWeight: 800 }}>Server belum terhubung</h3>
              <p style={{ color: 'var(--mute)' }}>Pastikan backend API berjalan, lalu coba lagi.</p>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => setCurrentPage((p) => p)}
                style={{ marginTop: '1rem' }}
              >
                Coba Lagi
              </button>
            </div>
          ) : pageItems.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '4rem 1rem' }}>
              <h3 style={{ fontWeight: 800 }}>Tidak ada hasil</h3>
              <p style={{ color: 'var(--mute)' }}>
                Tidak ada rumah sakit yang cocok dengan filter yang dipilih. Coba ubah kata kunci atau reset filter.
              </p>
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
            <ul id="list" className="hospital-grid" aria-label="Daftar katalog rumah sakit">
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

              <div className="pagination-info" id="pg-info">
                Halaman <b>{validPage}</b> dari <b>{totalPages}</b> (Total <b>{sortedItems.length}</b> RS)
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
