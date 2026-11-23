import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { getAllHospitals, getFilterOptions } from '../api';
import { colorOf } from '../components/HospitalCard';
import LeafletMap, { translateInstruction } from '../components/LeafletMap';

const MODES = [
  { id: 'driving', label: 'Mobil', icon: 'fa-car' },
  { id: 'motorcycle', label: 'Motor', icon: 'fa-motorcycle' },
  { id: 'foot', label: 'Jalan Kaki', icon: 'fa-person-walking' },
];

function formatDistance(meters) {
  if (meters == null) return '—';
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} km`;
}

function formatDuration(seconds) {
  if (seconds == null) return '—';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} mnt`;
  return `${Math.floor(minutes / 60)} j ${minutes % 60} mnt`;
}

export default function MapPage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [hospitals, setHospitals] = useState([]);
  const [options, setOptions] = useState({ kabkota: [] });
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState(searchParams.get('q') || '');
  const [kelasFilter, setKelasFilter] = useState(searchParams.get('kelas') || '');
  const [kabFilter, setKabFilter] = useState(searchParams.get('kabkota') || '');

  const [selectedId, setSelectedId] = useState(searchParams.get('rs') || searchParams.get('destId') || '');
  const [routeActive, setRouteActive] = useState(searchParams.get('route') === '1' || Boolean(searchParams.get('destId')));
  const [routeMode, setRouteMode] = useState(searchParams.get('mode') || 'driving');

  const [routeInfo, setRouteInfo] = useState(null);
  const [routeError, setRouteError] = useState('');

  // Fetch hospitals and filter options
  useEffect(() => {
    setLoading(true);
    getAllHospitals()
      .then((items) => {
        setHospitals(items);
        setLoading(false);
      })
      .catch(() => setLoading(false));

    getFilterOptions()
      .then((data) => {
        setOptions({ kabkota: data.kabkota || [] });
      })
      .catch(() => {});
  }, []);

  // Escape key handler
  useEffect(() => {
    const onKeyDown = (e) => {
      if (e.key === 'Escape') {
        if (routeActive) {
          setRouteActive(false);
          setRouteInfo(null);
        } else if (selectedId) {
          setSelectedId('');
        } else {
          navigate(-1);
        }
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [routeActive, selectedId, navigate]);

  // Filter hospitals for list
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    return hospitals.filter((h) => {
      if (kelasFilter && h.kelas !== kelasFilter) return false;
      if (kabFilter && h.kabkota !== kabFilter) return false;
      if (q) {
        const target = `${h.nama} ${h.kabkota || ''} ${h.alamat || ''}`.toLowerCase();
        if (!target.includes(q)) return false;
      }
      return true;
    });
  }, [hospitals, query, kelasFilter, kabFilter]);

  const selectedHospital = useMemo(() => {
    return hospitals.find((h) => h.id === selectedId) || null;
  }, [hospitals, selectedId]);

  const startRoute = (h) => {
    setSelectedId(h.id);
    setRouteActive(true);
    setRouteInfo(null);
    setRouteError('');
  };

  const handleFocusHospital = (h) => {
    setSelectedId(h.id);
  };

  // If in route mode, render Dennis's .route-page
  if (routeActive && selectedHospital) {
    return (
      <section className="route-page" aria-label="Panduan rute rumah sakit">
        <aside className="route-sidebar">
          <button
            type="button"
            className="btn btn-ghost"
            onClick={() => {
              setRouteActive(false);
              setRouteInfo(null);
            }}
          >
            <i className="fa-solid fa-arrow-left" aria-hidden="true" /> Kembali ke Peta
          </button>

          <h1>Petunjuk Rute</h1>

          <div className="route-place">
            <small>Lokasi Keberangkatan</small>
            <strong>Lokasi Anda (GPS / Otomatis)</strong>
          </div>

          <div className="route-place">
            <small>Tujuan Rumah Sakit</small>
            <strong>{selectedHospital.nama}</strong>
            <span style={{ fontSize: '0.82rem', color: 'var(--mute)', display: 'block', marginTop: 2 }}>
              {selectedHospital.kabkota}, Sumatera Utara
            </span>
          </div>

          {/* Travel modes */}
          <div className="route-modes">
            {MODES.map((m) => (
              <button
                key={m.id}
                type="button"
                aria-pressed={routeMode === m.id}
                onClick={() => setRouteMode(m.id)}
              >
                <i className={`fa-solid ${m.icon}`} aria-hidden="true" style={{ fontSize: '1.2rem', marginBottom: 4 }} />
                <span>{m.label}</span>
              </button>
            ))}
          </div>

          {/* Route Summary */}
          {routeInfo ? (
            <div className="route-summary">
              <span>{formatDistance(routeInfo.distance)}</span>
              <span>{formatDuration(routeInfo.duration)}</span>
            </div>
          ) : routeError ? (
            <div style={{ padding: '0.8rem', background: '#fee2e2', borderRadius: 8, color: '#991b1b', margin: '1rem 0', fontSize: '0.85rem' }}>
              <i className="fa-solid fa-triangle-exclamation" /> {routeError}
            </div>
          ) : (
            <div style={{ padding: '1rem 0', textAlign: 'center', color: 'var(--mute)', fontSize: '0.85rem' }}>
              <span className="spin" style={{ display: 'inline-block', marginRight: 6 }} /> Menghitung rute tercepat...
            </div>
          )}

          {/* Turn-by-Turn Instructions */}
          {routeInfo?.instructions?.length > 0 && (
            <div style={{ marginTop: '1.25rem' }}>
              <h3 style={{ fontSize: '0.92rem', fontWeight: 800, margin: '0 0 0.8rem', color: 'var(--ink)' }}>
                Petunjuk Arah Belokan
              </h3>
              <ol style={{ listStyle: 'none', padding: 0, margin: 0, display: 'grid', gap: '0.6rem' }}>
                {routeInfo.instructions.map((step, idx) => (
                  <li
                    key={idx}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '0.65rem',
                      fontSize: '0.82rem',
                      padding: '0.5rem 0.6rem',
                      borderRadius: 8,
                      background: idx % 2 === 0 ? '#f8fafc' : '#fff',
                      border: '1px solid #f1f5f9',
                    }}
                  >
                    <span
                      style={{
                        minWidth: 22,
                        height: 22,
                        borderRadius: '50%',
                        background: 'var(--toba-mist)',
                        color: 'var(--toba-d)',
                        display: 'grid',
                        placeItems: 'center',
                        fontSize: '0.72rem',
                        fontWeight: 800,
                        flexShrink: 0,
                      }}
                    >
                      {idx + 1}
                    </span>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, color: 'var(--ink)' }}>{translateInstruction(step.text)}</div>
                      {step.distance > 0 && (
                        <div style={{ fontSize: '0.74rem', color: 'var(--mute)', marginTop: 2 }}>
                          {formatDistance(step.distance)}
                        </div>
                      )}
                    </div>
                  </li>
                ))}
              </ol>
            </div>
          )}

          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.6rem' }}>
            <Link
              className="btn btn-primary"
              style={{ flex: 1 }}
              to={`/rumah-sakit/${encodeURIComponent(selectedHospital.id)}`}
            >
              Lihat Detail RS
            </Link>
          </div>
        </aside>

        {/* Route Map Host */}
        <div className="route-map-host">
          <LeafletMap
            hospitals={[]}
            selectedId={null}
            showPopup={false}
            routeTarget={selectedHospital}
            routeMode={routeMode}
            onRouteInfo={(info) => {
              setRouteInfo(info);
              setRouteError('');
            }}
            onRouteError={(err) => setRouteError(err.message || 'Gagal menghitung rute')}
            className="w-full h-full"
          />
        </div>
      </section>
    );
  }

  // Fullscreen hospital map page (openHospitalMap layout)
  return (
    <section className="hospital-map-page" id="hospital-map-page" aria-label="Jelajahi rumah sakit melalui peta">
      {/* Sidebar */}
      <aside className="hospital-map-sidebar">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '0.5rem' }}>
          <button type="button" className="btn btn-ghost" id="hospital-map-back" onClick={() => navigate(-1)}>
            <i className="fa-solid fa-arrow-left" aria-hidden="true" /> Kembali
          </button>
          <Link to="/pencarian" className="btn btn-ghost" style={{ fontSize: '0.76rem' }}>
            Katalog
          </Link>
        </div>

        <h2>Peta Rumah Sakit</h2>
        <p id="hospital-map-count" role="status" style={{ fontSize: '0.82rem', color: 'var(--mute)', margin: '0 0 10px' }}>
          {loading ? 'Memuat data peta...' : `${filtered.length} rumah sakit dalam hasil pencarian`}
        </p>

        <input
          id="hospital-map-search"
          type="search"
          placeholder="Cari nama atau wilayah..."
          aria-label="Cari rumah sakit di peta"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {/* Filter pills */}
        <div style={{ display: 'flex', gap: '0.35rem', overflowX: 'auto', paddingBottom: '0.5rem', marginBottom: '0.8rem' }}>
          <button
            type="button"
            className={`btn ${!kelasFilter ? 'btn-primary' : 'btn-ghost'}`}
            style={{ padding: '0.25rem 0.6rem', fontSize: '0.74rem' }}
            onClick={() => setKelasFilter('')}
          >
            Semua
          </button>
          {['A', 'B', 'C', 'D'].map((k) => (
            <button
              key={k}
              type="button"
              className={`btn ${kelasFilter === k ? 'btn-primary' : 'btn-ghost'}`}
              style={{ padding: '0.25rem 0.6rem', fontSize: '0.74rem' }}
              onClick={() => setKelasFilter(kelasFilter === k ? '' : k)}
            >
              Kelas {k}
            </button>
          ))}
        </div>

        {/* Hospital Card List in Sidebar */}
        <div id="hospital-map-list" style={{ overflowY: 'auto', flex: 1, paddingRight: 4 }}>
          {filtered.length === 0 ? (
            <p style={{ color: 'var(--mute)', fontSize: '0.85rem' }}>Tidak ada rumah sakit yang sesuai.</p>
          ) : (
            filtered.map((h) => (
              <article key={h.id} className="map-hospital-card">
                {h.foto && (
                  <img
                    src={h.foto}
                    alt={h.nama}
                    loading="lazy"
                    onError={(e) => {
                      e.currentTarget.style.display = 'none';
                    }}
                  />
                )}
                <h3>{h.nama}</h3>
                <p>{h.kabkota || 'Wilayah belum tersedia'}</p>
                <p>Kelas {h.kelas || 'belum tersedia'}</p>
                <div className="map-hospital-actions">
                  {h.lat != null && h.lon != null && (
                    <button
                      className="btn btn-ghost"
                      type="button"
                      onClick={() => handleFocusHospital(h)}
                    >
                      Lihat di peta
                    </button>
                  )}
                  <Link className="btn btn-primary" to={`/rumah-sakit/${encodeURIComponent(h.id)}`}>
                    Lihat Detail
                  </Link>
                  {h.lat != null && h.lon != null && (
                    <button
                      className="btn btn-ghost"
                      type="button"
                      onClick={() => startRoute(h)}
                      title="Petunjuk Rute"
                    >
                      <i className="fa-solid fa-diamond-turn-right" aria-hidden="true" /> Rute
                    </button>
                  )}
                </div>
              </article>
            ))
          )}
        </div>
      </aside>

      {/* Map Canvas */}
      <div id="hospital-map-canvas" aria-label="Peta persebaran rumah sakit">
        <LeafletMap
          hospitals={filtered}
          selectedId={selectedId}
          onSelect={(h) => setSelectedId(h ? h.id : '')}
          fit
          className="w-full h-full rounded-[22px] overflow-hidden"
        />
      </div>
    </section>
  );
}
