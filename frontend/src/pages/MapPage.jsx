import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { getAllHospitals, getFilterOptions } from '../api';
import { KELAS_OPTIONS } from '../constants';
import { cn, haversineKm, telHref } from '../utils';
import { useApp } from '../context/AppContext';
import SiteHeader from '../components/SiteHeader';
import LeafletMap, { getUserPosition } from '../components/LeafletMap';

const MODES = [
  { id: 'driving', label: 'Mobil', icon: 'directions_car' },
  { id: 'foot', label: 'Jalan kaki', icon: 'directions_walk' },
  { id: 'motorcycle', label: 'Motor', icon: 'two_wheeler' },
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
  const { toast } = useApp();
  const [searchParams, setSearchParams] = useSearchParams();
  const [hospitals, setHospitals] = useState([]);
  const [options, setOptions] = useState({ kabkota: [], layanan: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [routeInfo, setRouteInfo] = useState(null);
  const [routeError, setRouteError] = useState('');
  const [locating, setLocating] = useState(false);

  const selectedId = searchParams.get('rs') || '';
  const routeActive = searchParams.get('route') === '1';
  const routeMode = searchParams.get('mode') || 'driving';
  const kelas = searchParams.get('kelas') || '';
  const kabkota = searchParams.get('kabkota') || '';
  const query = searchParams.get('q') || '';

  const load = () => {
    setLoading(true);
    setError('');
    getAllHospitals()
      .then((items) => setHospitals(items))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    getFilterOptions()
      .then((data) => setOptions({ kabkota: data.kabkota || [], layanan: data.layanan || [] }))
      .catch(() => {});
  }, []);

  useEffect(() => {
    setRouteInfo(null);
    setRouteError('');
  }, [selectedId, routeMode, routeActive]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return hospitals.filter((hospital) => {
      if (kelas && hospital.kelas !== kelas) return false;
      if (kabkota && hospital.kabkota !== kabkota) return false;
      if (needle) {
        const haystack = `${hospital.nama} ${hospital.kabkota || ''} ${hospital.alamat || ''} ${(hospital.layanan || []).join(' ')}`.toLowerCase();
        if (!haystack.includes(needle)) return false;
      }
      return true;
    });
  }, [hospitals, kelas, kabkota, query]);

  const selected = useMemo(
    () => hospitals.find((hospital) => hospital.id === selectedId) || null,
    [hospitals, selectedId],
  );

  const updateParams = (patch) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(patch).forEach(([key, value]) => {
      if (value === '' || value == null || value === false) next.delete(key);
      else next.set(key, value === true ? '1' : String(value));
    });
    setSearchParams(next, { replace: true });
  };

  const selectHospital = (hospital, { route = false } = {}) => {
    updateParams({ rs: hospital.id, route: route ? '1' : searchParams.get('route') });
    if (window.innerWidth < 1024) setSidebarOpen(false);
  };

  const startRoute = (hospital) => {
    if (!hospital) return;
    updateParams({ rs: hospital.id, route: '1', mode: routeMode });
  };

  const changeMode = (mode) => {
    if (mode === 'motorcycle') {
      if (selected) {
        const params = new URLSearchParams({
          api: '1',
          destination: `${selected.lat},${selected.lon}`,
          travelmode: 'two-wheeler',
        });
        window.open(`https://www.google.com/maps/dir/?${params.toString()}`, '_blank', 'noopener');
      }
      return;
    }
    updateParams({ mode });
  };

  const findNearest = async () => {
    if (locating) return;
    setLocating(true);
    try {
      const position = await getUserPosition();
      const candidates = hospitals.filter(
        (hospital) =>
          hospital.lat != null &&
          hospital.lon != null &&
          [...(hospital.layanan || []), ...(hospital.fasilitas || [])].some((item) =>
            /igd|ugd|gawat darurat|ambulans/i.test(item),
          ),
      );
      const pool = candidates.length ? candidates : hospitals.filter((h) => h.lat != null && h.lon != null);
      if (!pool.length) {
        toast('Tidak ada rumah sakit berkoordinat yang dapat dihitung.', 'error');
        return;
      }
      const nearest = pool
        .map((hospital) => ({
          hospital,
          distance: haversineKm(position[0], position[1], hospital.lat, hospital.lon),
        }))
        .sort((a, b) => a.distance - b.distance)[0];
      toast(`Rumah sakit terdekat: ${nearest.hospital.nama} (${nearest.distance.toFixed(1)} km).`, 'success');
      updateParams({
        rs: nearest.hospital.id,
        route: '1',
        mode: 'driving',
        kelas: '',
        kabkota: '',
        q: '',
      });
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setLocating(false);
    }
  };

  const activeFilterCount = [kelas, kabkota, query].filter(Boolean).length;

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <SiteHeader active="peta" />

      <main className="relative flex-1">
        <div className="relative flex h-[calc(100vh-4rem)] w-full overflow-hidden">
          {/* Sidebar */}
          <aside
            className={cn(
              'absolute inset-y-0 left-0 z-30 flex w-[342px] max-w-[92vw] flex-col border-r border-slate-200 bg-white shadow-floating transition-transform duration-300 lg:static lg:z-auto lg:shadow-none',
              sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
            )}
            aria-label="Daftar rumah sakit pada peta"
          >
            <div className="border-b border-slate-200 p-4">
              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-brand-blue">
                    Peta persebaran
                  </p>
                  <h1 className="mt-0.5 font-heading text-lg font-extrabold text-brand-navy">
                    Rumah Sakit Sumatera Utara
                  </h1>
                  <p className="mt-0.5 text-[11px] text-slate-500">
                    {loading ? 'Memuat titik...' : `${filtered.length} fasilitas ditampilkan`}
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setSidebarOpen(false)}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-slate-500 lg:hidden"
                  aria-label="Tutup daftar"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>

              <div className="relative mt-3">
                <span className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
                  <span className="material-symbols-outlined text-[18px]">search</span>
                </span>
                <input
                  value={query}
                  onChange={(event) => updateParams({ q: event.target.value, rs: '' })}
                  placeholder="Cari nama, alamat, atau layanan..."
                  className="w-full rounded-full border border-slate-200 bg-slate-100 py-2 pl-9 pr-8 text-xs outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
                  aria-label="Cari rumah sakit di peta"
                />
                {query ? (
                  <button
                    type="button"
                    onClick={() => updateParams({ q: '' })}
                    className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-700"
                    aria-label="Hapus pencarian"
                  >
                    <span className="material-symbols-outlined text-[16px]">close</span>
                  </button>
                ) : null}
              </div>

              <div className="mt-2.5 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                <button
                  type="button"
                  onClick={() => updateParams({ kelas: '' })}
                  className={cn(
                    'shrink-0 rounded-full border px-2.5 py-1 text-[10.5px] font-semibold transition',
                    !kelas
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
                    onClick={() => updateParams({ kelas: option.value, rs: '' })}
                    className={cn(
                      'shrink-0 rounded-full border px-2.5 py-1 text-[10.5px] font-bold transition',
                      kelas === option.value
                        ? 'border-brand-navy bg-brand-navy text-white'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                    )}
                  >
                    Kelas {option.value}
                  </button>
                ))}
              </div>

              <div className="mt-2 flex items-center gap-2">
                <select
                  value={kabkota}
                  onChange={(event) => updateParams({ kabkota: event.target.value, rs: '' })}
                  className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[11px] text-slate-700 outline-none focus:border-brand-blue"
                  aria-label="Filter wilayah"
                >
                  <option value="">Semua wilayah</option>
                  {options.kabkota.map((region) => (
                    <option key={region} value={region}>
                      {region}
                    </option>
                  ))}
                </select>
                {activeFilterCount ? (
                  <button
                    type="button"
                    onClick={() => updateParams({ kelas: '', kabkota: '', q: '', rs: '' })}
                    className="shrink-0 rounded-lg px-2 py-1.5 text-[10.5px] font-semibold text-rose-600 hover:bg-rose-50"
                  >
                    Reset
                  </button>
                ) : null}
              </div>

              <button
                type="button"
                onClick={findNearest}
                disabled={locating}
                className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl bg-emerald-50 px-3 py-2 text-[11px] font-bold text-emerald-700 ring-1 ring-emerald-200 transition hover:bg-emerald-100 disabled:opacity-60"
              >
                <span className={cn('material-symbols-outlined text-[16px]', locating && 'animate-spin')}>
                  {locating ? 'progress_activity' : 'near_me'}
                </span>
                {locating ? 'Mendeteksi lokasi...' : 'Cari RS terdekat dari lokasi saya'}
              </button>
            </div>

            <div className="flex-1 overflow-y-auto scrollbar-thin">
              {loading ? (
                <div className="space-y-2 p-3">
                  {Array.from({ length: 5 }).map((_, index) => (
                    <div key={index} className="flex gap-2 rounded-xl border border-slate-100 p-2">
                      <div className="h-14 w-14 animate-pulse rounded-lg bg-slate-100" />
                      <div className="flex-1 space-y-2 py-1">
                        <div className="h-3 w-4/5 animate-pulse rounded bg-slate-100" />
                        <div className="h-2.5 w-1/2 animate-pulse rounded bg-slate-100" />
                      </div>
                    </div>
                  ))}
                </div>
              ) : error ? (
                <div className="p-5 text-center">
                  <span className="material-symbols-outlined text-[34px] text-rose-300">wifi_off</span>
                  <p className="mt-2 text-xs font-semibold text-slate-700">Peta belum dapat dimuat.</p>
                  <p className="mt-1 text-[11px] text-slate-500">{error}</p>
                  <button
                    type="button"
                    onClick={load}
                    className="mt-3 rounded-full bg-brand-navy px-4 py-2 text-[11px] font-semibold text-white"
                  >
                    Coba lagi
                  </button>
                </div>
              ) : filtered.length ? (
                <ul className="space-y-1 p-2">
                  {filtered.map((hospital) => {
                    const active = hospital.id === selectedId;
                    const phone = telHref(hospital.telepon);
                    return (
                      <li key={hospital.id}>
                        <button
                          type="button"
                          onClick={() => selectHospital(hospital)}
                          className={cn(
                            'flex w-full items-start gap-2.5 rounded-xl border p-2 text-left transition',
                            active
                              ? 'border-brand-blue/40 bg-blue-50/70'
                              : 'border-transparent hover:border-slate-200 hover:bg-slate-50',
                          )}
                        >
                          {hospital.foto ? (
                            <img
                              src={hospital.foto}
                              alt=""
                              loading="lazy"
                              className="h-14 w-14 shrink-0 rounded-lg object-cover"
                              onError={(event) => {
                                event.currentTarget.style.display = 'none';
                              }}
                            />
                          ) : (
                            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-brand-navy">
                              <span className="material-symbols-outlined text-[20px]">local_hospital</span>
                            </span>
                          )}
                          <span className="min-w-0 flex-1">
                            <span className="line-clamp-1 block text-[11.5px] font-bold text-slate-800">
                              {hospital.nama}
                            </span>
                            <span className="mt-0.5 flex items-center gap-1 text-[10px] text-slate-500">
                              <span className="material-symbols-outlined text-[11px]">location_on</span>
                              <span className="truncate">{hospital.kabkota || 'Sumatera Utara'}</span>
                            </span>
                            <span className="mt-1 flex flex-wrap items-center gap-1">
                              <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[9px] font-bold text-slate-600">
                                Kelas {hospital.kelas || '—'}
                              </span>
                              {hospital.bpjs ? (
                                <span className="rounded bg-emerald-50 px-1.5 py-0.5 text-[9px] font-bold text-emerald-700">
                                  BPJS
                                </span>
                              ) : null}
                              {active ? (
                                <span className="inline-flex items-center gap-0.5 text-[9px] font-bold text-brand-blue">
                                  <span className="material-symbols-outlined text-[11px]">checked</span>
                                  Dipilih
                                </span>
                              ) : null}
                            </span>
                          </span>
                          <span className="flex flex-col gap-1">
                            <span
                              className="material-symbols-outlined text-[15px] text-slate-400"
                              aria-hidden="true"
                            >
                              chevron_right
                            </span>
                            {phone ? (
                              <a
                                href={phone}
                                onClick={(event) => event.stopPropagation()}
                                className="material-symbols-outlined text-[15px] text-slate-400 hover:text-emerald-600"
                                aria-label={`Telepon ${hospital.nama}`}
                              >
                                call
                              </a>
                            ) : null}
                          </span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              ) : (
                <div className="p-6 text-center">
                  <span className="material-symbols-outlined text-[34px] text-slate-300">location_off</span>
                  <p className="mt-2 text-xs font-semibold text-slate-700">Tidak ada titik yang cocok.</p>
                  <p className="mt-1 text-[11px] text-slate-500">
                    Ubah kata kunci atau filter kelas/wilayah.
                  </p>
                </div>
              )}
            </div>

            {selected ? (
              <div className="border-t border-slate-200 bg-white p-3">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-2.5">
                  <p className="line-clamp-1 text-[11.5px] font-bold text-slate-900">{selected.nama}</p>
                  <p className="text-[10px] text-slate-500">
                    Kelas {selected.kelas || '—'} • {selected.kabkota || 'Sumatera Utara'}
                  </p>
                  <div className="mt-2 flex gap-1.5">
                    <Link
                      to={`/rumah-sakit/${encodeURIComponent(selected.id)}`}
                      className="flex flex-1 items-center justify-center gap-1 rounded-full border border-slate-300 bg-white px-2 py-1.5 text-[10.5px] font-semibold text-slate-700 transition hover:bg-slate-100"
                    >
                      <span className="material-symbols-outlined text-[13px]">info</span>
                      Detail
                    </Link>
                    <button
                      type="button"
                      onClick={() => startRoute(selected)}
                      disabled={selected.lat == null || selected.lon == null}
                      className="flex flex-1 items-center justify-center gap-1 rounded-full bg-brand-blue px-2 py-1.5 text-[10.5px] font-semibold text-white transition hover:bg-brand-navy disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-[13px]">directions</span>
                      Rute
                    </button>
                  </div>
                </div>
              </div>
            ) : null}
          </aside>

          {/* Map */}
          <div className="relative flex-1">
            <LeafletMap
              hospitals={filtered}
              selectedId={selectedId}
              onSelect={selectHospital}
              fit
              routeTarget={routeActive && selected ? selected : null}
              routeMode={routeMode}
              onRouteInfo={setRouteInfo}
              onRouteError={(err) => {
                setRouteError(err.message);
                toast(err.message, 'error');
              }}
              className="h-full"
            />

            {/* Mobile sidebar toggle */}
            {!sidebarOpen ? (
              <button
                type="button"
                onClick={() => setSidebarOpen(true)}
                className="absolute left-3 top-3 z-20 inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-2 text-[11px] font-bold text-brand-navy shadow-floating lg:hidden"
              >
                <span className="material-symbols-outlined text-[16px]">list</span>
                Daftar ({filtered.length})
              </button>
            ) : null}

            {/* Map legend */}
            <div className="pointer-events-none absolute bottom-4 right-3 z-20 hidden rounded-xl border border-slate-200 bg-white/95 px-3 py-2 text-[9.5px] font-semibold text-slate-600 shadow-sm backdrop-blur sm:block">
              <p className="mb-1 text-[9px] uppercase tracking-wider text-slate-400">Kelas RS</p>
              <div className="flex flex-wrap gap-x-2.5 gap-y-1">
                {[
                  { label: 'A', color: '#BE123C' },
                  { label: 'B', color: '#0284C7' },
                  { label: 'C', color: '#059669' },
                  { label: 'D', color: '#64748B' },
                ].map((item) => (
                  <span key={item.label} className="flex items-center gap-1">
                    <i className="h-2 w-2 rounded-full" style={{ background: item.color }} />
                    {item.label}
                  </span>
                ))}
              </div>
            </div>

            {/* Route panel */}
            {routeActive && selected ? (
              <div className="absolute bottom-4 left-3 right-3 z-20 animate-slide-up sm:right-auto sm:w-[360px]">
                <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-modal">
                  <div className="flex items-start justify-between gap-2 border-b border-slate-100 px-4 py-3">
                    <div className="min-w-0">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-brand-blue">
                        Panduan perjalanan
                      </p>
                      <p className="mt-0.5 line-clamp-1 text-xs font-bold text-slate-900">
                        {selected.nama}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => updateParams({ route: '' })}
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200"
                      aria-label="Tutup rute"
                    >
                      <span className="material-symbols-outlined text-[16px]">close</span>
                    </button>
                  </div>
                  <div className="flex gap-1 border-b border-slate-100 p-2">
                    {MODES.map((mode) => (
                      <button
                        key={mode.id}
                        type="button"
                        onClick={() => changeMode(mode.id)}
                        className={cn(
                          'flex flex-1 flex-col items-center gap-0.5 rounded-lg px-1 py-1.5 text-[9.5px] font-semibold transition',
                          routeMode === mode.id
                            ? 'bg-brand-navy text-white'
                            : 'text-slate-600 hover:bg-slate-100',
                        )}
                      >
                        <span className="material-symbols-outlined text-[17px]">{mode.icon}</span>
                        {mode.label}
                      </button>
                    ))}
                  </div>
                  <div className="p-3.5">
                    {routeError ? (
                      <p className="text-[11px] leading-relaxed text-rose-600">{routeError}</p>
                    ) : routeInfo ? (
                      <div className="flex items-center justify-between gap-2">
                        <div>
                          <p className="text-[10px] text-slate-500">Estimasi perjalanan</p>
                          <p className="mt-0.5 text-lg font-extrabold text-slate-900">
                            {formatDuration(routeInfo.time)}
                          </p>
                        </div>
                        <div className="text-right">
                          <p className="text-[10px] text-slate-500">Jarak</p>
                          <p className="mt-0.5 text-sm font-bold text-brand-blue">
                            {formatDistance(routeInfo.distance)}
                          </p>
                        </div>
                      </div>
                    ) : (
                      <p className="flex items-center gap-1.5 text-[11px] text-slate-500">
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-200 border-t-brand-blue" />
                        Menghitung rute dari lokasi Anda...
                      </p>
                    )}
                    <p className="mt-2 text-[9.5px] leading-relaxed text-slate-400">
                      Estimasi tanpa kondisi lalu lintas langsung. Pilihan motor membuka Google Maps.
                    </p>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Selected quick card on map (desktop) */}
            {selected && !routeActive ? (
              <div className="absolute left-3 top-3 z-20 hidden w-[300px] animate-fade-in rounded-2xl border border-slate-200 bg-white/95 p-3 shadow-floating backdrop-blur sm:block">
                <div className="flex gap-2.5">
                  {selected.foto ? (
                    <img
                      src={selected.foto}
                      alt=""
                      className="h-16 w-16 shrink-0 rounded-xl object-cover"
                      onError={(event) => {
                        event.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : null}
                  <div className="min-w-0">
                    <p className="line-clamp-2 text-[12px] font-bold leading-snug text-slate-900">
                      {selected.nama}
                    </p>
                    <p className="mt-0.5 text-[10px] text-slate-500">
                      Kelas {selected.kelas || '—'} • {selected.kabkota || 'Sumatera Utara'}
                    </p>
                  </div>
                </div>
                <div className="mt-2.5 flex gap-1.5">
                  <Link
                    to={`/rumah-sakit/${encodeURIComponent(selected.id)}`}
                    className="flex flex-1 items-center justify-center gap-1 rounded-full border border-slate-300 px-2 py-1.5 text-[10.5px] font-semibold text-slate-700 transition hover:bg-slate-50"
                  >
                    Lihat detail
                  </Link>
                  <button
                    type="button"
                    onClick={() => startRoute(selected)}
                    className="flex flex-1 items-center justify-center gap-1 rounded-full bg-brand-navy px-2 py-1.5 text-[10.5px] font-semibold text-white transition hover:bg-brand-blue"
                  >
                    <span className="material-symbols-outlined text-[13px]">directions</span>
                    Rute
                  </button>
                </div>
              </div>
            ) : null}

            {/* Back to search */}
            <Link
              to="/pencarian"
              className="absolute right-3 top-3 z-20 inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white/95 px-3 py-1.5 text-[10.5px] font-semibold text-slate-700 shadow-sm backdrop-blur transition hover:bg-white"
            >
              <span className="material-symbols-outlined text-[14px]">tune</span>
              Pencarian lanjutan
            </Link>
          </div>
        </div>
      </main>
    </div>
  );
}
