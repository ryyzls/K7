import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { getAllHospitals, getFilterOptions } from '../api';
import { KELAS_COLOR, KELAS_OPTIONS } from '../constants';
import { cn, haversineKm, telHref } from '../utils';
import { useApp } from '../context/AppContext';
import SiteHeader from '../components/SiteHeader';
import LeafletMap, { getUserPosition } from '../components/LeafletMap';

const MODES = [
  { id: 'driving', label: 'Mobil', icon: 'directions_car' },
  { id: 'foot', label: 'Jalan kaki', icon: 'directions_walk' },
  { id: 'motorcycle', label: 'Motor', icon: 'two_wheeler' },
];

const TILE_MODES = [
  { id: 'osm', label: 'Peta Jalan', icon: 'map' },
  { id: 'topo', label: 'Topografi', icon: 'terrain' },
  { id: 'satellite', label: 'Satelit', icon: 'satellite_alt' },
];

const RADIUS_OPTIONS = [
  { value: 0, label: 'Semua Jarak' },
  { value: 5, label: '≤ 5 km' },
  { value: 10, label: '≤ 10 km' },
  { value: 25, label: '≤ 25 km' },
];

function formatDistance(meters) {
  if (meters == null) return '—';
  if (meters < 1000) return `${Math.round(meters)} m`;
  return `${(meters / 1000).toLocaleString('id-ID', { maximumFractionDigits: 1 })} km`;
}

function formatDuration(seconds) {
  if (seconds == null) return '—';
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `~${minutes} mnt`;
  return `~${Math.floor(minutes / 60)} j ${minutes % 60} mnt`;
}

function googleMapsDirUrl(hospital) {
  if (!hospital || hospital.lat == null || hospital.lon == null) return '#';
  const params = new URLSearchParams({
    api: '1',
    destination: `${hospital.lat},${hospital.lon}`,
  });
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

function wazeDirUrl(hospital) {
  if (!hospital || hospital.lat == null || hospital.lon == null) return '#';
  return `https://waze.com/ul?ll=${hospital.lat},${hospital.lon}&navigate=yes`;
}

function buildTieredReferrals(sourceHospital, allHospitals) {
  if (!sourceHospital || sourceHospital.lat == null || sourceHospital.lon == null) return [];
  const tier = String(sourceHospital.kelas || '').toUpperCase();
  const targetClasses =
    tier === 'D' ? ['C', 'B', 'A'] : tier === 'C' ? ['B', 'A'] : tier === 'B' ? ['A'] : ['A'];

  const links = [];
  targetClasses.forEach((targetClass) => {
    const candidates = allHospitals
      .filter(
        (h) =>
          h.id !== sourceHospital.id &&
          String(h.kelas || '').toUpperCase() === targetClass &&
          h.lat != null &&
          h.lon != null,
      )
      .map((h) => ({
        hospital: h,
        distanceKm: haversineKm(sourceHospital.lat, sourceHospital.lon, h.lat, h.lon),
      }))
      .sort((a, b) => a.distanceKm - b.distanceKm);

    if (candidates.length) {
      const best = candidates[0];
      links.push({
        from: [sourceHospital.lat, sourceHospital.lon],
        to: [best.hospital.lat, best.hospital.lon],
        target: best.hospital,
        tierLabel:
          tier === 'A'
            ? 'Rujukan Tersier Setara (Kelas A)'
            : `Rujukan Tingkat Lanjut • Kelas ${targetClass}`,
        distanceKm: best.distanceKm,
      });
    }
  });

  return links;
}

export default function MapPage() {
  const { toast, toggleCompare, isCompared } = useApp();
  const [searchParams, setSearchParams] = useSearchParams();
  const [hospitals, setHospitals] = useState([]);
  const [options, setOptions] = useState({ kabkota: [], layanan: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [routeInfo, setRouteInfo] = useState(null);
  const [routeError, setRouteError] = useState('');
  const [stepsExpanded, setStepsExpanded] = useState(true);
  const [locating, setLocating] = useState(false);
  const [tileMode, setTileMode] = useState('osm');
  const [userPos, setUserPos] = useState(null);
  const [radiusKm, setRadiusKm] = useState(0);
  const [bpjsOnly, setBpjsOnly] = useState(false);
  const [drivingEstimates, setDrivingEstimates] = useState({});
  const [pendingBounds, setPendingBounds] = useState(null);
  const [activeBounds, setActiveBounds] = useState(null);
  const [referralMode, setReferralMode] = useState(false);

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
    setStepsExpanded(true);
  }, [selectedId, routeMode, routeActive]);

  useEffect(() => {
    setReferralMode(false);
  }, [selectedId]);

  useEffect(() => {
    if (!routeActive && !referralMode) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') {
        if (referralMode) {
          setReferralMode(false);
        } else {
          const next = new URLSearchParams(searchParams);
          next.delete('route');
          setSearchParams(next, { replace: true });
        }
      }
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [routeActive, referralMode, searchParams, setSearchParams]);

  // Fetch real driving ETA via OSRM Table API for the 8 closest hospitals when GPS is active
  useEffect(() => {
    if (!userPos || !hospitals.length) return undefined;
    const nearestEight = hospitals
      .filter((h) => h.lat != null && h.lon != null)
      .map((h) => ({
        h,
        km: haversineKm(userPos[0], userPos[1], h.lat, h.lon),
      }))
      .sort((a, b) => a.km - b.km)
      .slice(0, 8);

    if (!nearestEight.length) return undefined;

    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 6500);
    const coords = [
      `${userPos[1]},${userPos[0]}`,
      ...nearestEight.map((item) => `${item.h.lon},${item.h.lat}`),
    ].join(';');

    fetch(
      `https://router.project-osrm.org/table/v1/driving/${coords}?sources=0&annotations=duration,distance`,
      { signal: controller.signal },
    )
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (!data || data.code !== 'Ok') return;
        const durations = data.durations?.[0] || [];
        const distances = data.distances?.[0] || [];
        const nextMap = {};
        nearestEight.forEach((item, idx) => {
          const dur = durations[idx + 1];
          const dist = distances[idx + 1];
          if (dur != null) {
            nextMap[item.h.id] = { durationSec: dur, distanceM: dist };
          }
        });
        setDrivingEstimates(nextMap);
      })
      .catch(() => {})
      .finally(() => window.clearTimeout(timer));

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [userPos, hospitals]);

  const enriched = useMemo(() => {
    return hospitals.map((hospital) => {
      const distKm =
        userPos && hospital.lat != null && hospital.lon != null
          ? haversineKm(userPos[0], userPos[1], hospital.lat, hospital.lon)
          : null;
      return {
        ...hospital,
        distKm,
        eta: drivingEstimates[hospital.id] || null,
      };
    });
  }, [hospitals, userPos, drivingEstimates]);

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();
    const list = enriched.filter((hospital) => {
      if (kelas && hospital.kelas !== kelas) return false;
      if (kabkota && hospital.kabkota !== kabkota) return false;
      if (bpjsOnly && !hospital.bpjs) return false;
      if (radiusKm > 0 && userPos) {
        if (hospital.distKm == null || hospital.distKm > radiusKm) return false;
      }
      if (activeBounds && hospital.lat != null && hospital.lon != null) {
        if (
          hospital.lat < activeBounds.south ||
          hospital.lat > activeBounds.north ||
          hospital.lon < activeBounds.west ||
          hospital.lon > activeBounds.east
        ) {
          return false;
        }
      }
      if (needle) {
        const haystack = `${hospital.nama} ${hospital.kabkota || ''} ${hospital.alamat || ''} ${(hospital.layanan || []).join(' ')}`.toLowerCase();
        if (!haystack.includes(needle)) return false;
      }
      return true;
    });

    if (userPos) {
      return [...list].sort((a, b) => (a.distKm ?? 9999) - (b.distKm ?? 9999));
    }
    return list;
  }, [enriched, kelas, kabkota, bpjsOnly, radiusKm, userPos, activeBounds, query]);

  const selected = useMemo(
    () => enriched.find((hospital) => hospital.id === selectedId) || null,
    [enriched, selectedId],
  );

  const referralLinks = useMemo(() => {
    if (!referralMode || !selected) return [];
    return buildTieredReferrals(selected, enriched);
  }, [referralMode, selected, enriched]);

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
    setReferralMode(false);
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

  const activateLocationAndNearest = async (autoSelectNearest = true) => {
    if (locating) return;
    setLocating(true);
    try {
      const position = await getUserPosition();
      setUserPos(position);
      setActiveBounds(null);
      setPendingBounds(null);
      if (autoSelectNearest) {
        const candidates = hospitals.filter(
          (hospital) =>
            hospital.lat != null &&
            hospital.lon != null &&
            [...(hospital.layanan || []), ...(hospital.fasilitas || [])].some((item) =>
              /igd|ugd|gawat darurat|ambulans/i.test(item),
            ),
        );
        const pool = candidates.length ? candidates : hospitals.filter((h) => h.lat != null && h.lon != null);
        if (pool.length) {
          const nearest = pool
            .map((hospital) => ({
              hospital,
              distance: haversineKm(position[0], position[1], hospital.lat, hospital.lon),
            }))
            .sort((a, b) => a.distance - b.distance)[0];
          toast(`Lokasi aktif. RS terdekat: ${nearest.hospital.nama} (${nearest.distance.toFixed(1)} km).`, 'success');
          updateParams({
            rs: nearest.hospital.id,
            route: '1',
            mode: 'driving',
            kelas: '',
            kabkota: '',
            q: '',
          });
        }
      } else {
        toast('Lokasi GPS aktif. Daftar rumah sakit diurutkan dari yang terdekat.', 'success');
      }
    } catch (err) {
      toast(err.message, 'error');
    } finally {
      setLocating(false);
    }
  };

  const handleRadiusChange = async (nextRadius) => {
    if (nextRadius > 0 && !userPos) {
      try {
        setLocating(true);
        const pos = await getUserPosition();
        setUserPos(pos);
        setActiveBounds(null);
        setPendingBounds(null);
        setRadiusKm(nextRadius);
        toast(`Menampilkan RS dalam radius ${nextRadius} km dari lokasi Anda.`, 'success');
      } catch (err) {
        toast(err.message, 'error');
      } finally {
        setLocating(false);
      }
      return;
    }
    setRadiusKm(nextRadius);
  };

  const applyViewportSearch = () => {
    if (!pendingBounds) return;
    setActiveBounds(pendingBounds);
    setPendingBounds(null);
    updateParams({ kabkota: '', rs: '' });
  };

  const activeFilterCount = [kelas, kabkota, query, bpjsOnly, radiusKm > 0, activeBounds].filter(Boolean).length;
  const steps = routeInfo?.steps || [];

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <SiteHeader active="peta" />

      <main className="relative flex-1">
        <div className="relative flex h-[calc(100vh-4.35rem)] w-full overflow-hidden">
          {/* Sidebar Daftar & Kontrol Geospasial */}
          <aside
            className={cn(
              'absolute inset-y-0 left-0 z-30 flex w-[364px] max-w-[92vw] flex-col border-r border-slate-200 bg-white shadow-floating transition-transform duration-300 lg:static lg:z-auto lg:shadow-none',
              sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
            )}
            aria-label="Daftar rumah sakit pada peta"
          >
            <div className="border-b border-slate-200 p-4">
              <div className="mb-3 flex items-center justify-between">
                <Link
                  to="/"
                  className="group inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-1 text-[11px] font-semibold text-slate-600 shadow-sm transition hover:border-toba hover:bg-toba-mist hover:text-toba-dark"
                >
                  <span className="material-symbols-outlined text-[15px] transition-transform group-hover:-translate-x-1">
                    arrow_back
                  </span>
                  <span>Beranda</span>
                </Link>

                <button
                  type="button"
                  onClick={() => setBpjsOnly((prev) => !prev)}
                  className={cn(
                    'inline-flex items-center gap-1 rounded-full border px-2.5 py-1 text-[10.5px] font-bold transition',
                    bpjsOnly
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-700'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:border-emerald-200',
                  )}
                >
                  <span className="material-symbols-outlined text-[13px]">verified</span>
                  BPJS
                </button>
              </div>

              <div className="flex items-start justify-between gap-2">
                <div>
                  <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-toba">
                    Peta &amp; Rute Fasilitas
                  </p>
                  <h1 className="mt-0.5 text-lg font-extrabold text-slate-900">
                    Peta Rumah Sakit Sumut
                  </h1>
                  <p className="mt-0.5 text-[11px] text-slate-500">
                    {loading
                      ? 'Memuat lokasi...'
                      : `${filtered.length} fasilitas${activeBounds ? ' di area layar' : userPos ? ' • urut terdekat' : ''}`}
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
                  placeholder="Cari nama RS, wilayah, atau layanan..."
                  className="w-full rounded-full border border-slate-200 bg-slate-100 py-2 pl-9 pr-8 text-xs outline-none transition focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/15"
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

              {/* Filter Kelas */}
              <div className="mt-2.5 flex items-center gap-1.5 overflow-x-auto no-scrollbar">
                <button
                  type="button"
                  onClick={() => updateParams({ kelas: '' })}
                  className={cn(
                    'shrink-0 rounded-full border px-2.5 py-1 text-[10.5px] font-semibold transition',
                    !kelas
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
                    onClick={() => updateParams({ kelas: kelas === option.value ? '' : option.value, rs: '' })}
                    className={cn(
                      'shrink-0 rounded-full border px-2.5 py-1 text-[10.5px] font-bold transition',
                      kelas === option.value
                        ? 'border-toba bg-toba text-white'
                        : 'border-slate-200 bg-white text-slate-600 hover:border-slate-300',
                    )}
                  >
                    Kelas {option.value}
                  </button>
                ))}
              </div>

              {/* Filter Wilayah & Reset */}
              <div className="mt-2 flex items-center gap-2">
                <select
                  value={kabkota}
                  onChange={(event) => {
                    setActiveBounds(null);
                    setPendingBounds(null);
                    updateParams({ kabkota: event.target.value, rs: '' });
                  }}
                  className="min-w-0 flex-1 rounded-lg border border-slate-200 bg-slate-50 px-2.5 py-1.5 text-[11px] text-slate-700 outline-none focus:border-toba"
                  aria-label="Filter wilayah"
                >
                  <option value="">Semua wilayah Sumatera Utara</option>
                  {options.kabkota.map((region) => (
                    <option key={region} value={region}>
                      {region}
                    </option>
                  ))}
                </select>
                {activeFilterCount ? (
                  <button
                    type="button"
                    onClick={() => {
                      updateParams({ kelas: '', kabkota: '', q: '', rs: '' });
                      setBpjsOnly(false);
                      setRadiusKm(0);
                      setActiveBounds(null);
                      setPendingBounds(null);
                      setReferralMode(false);
                    }}
                    className="shrink-0 rounded-lg px-2 py-1.5 text-[10.5px] font-semibold text-rose-600 hover:bg-rose-50"
                  >
                    Reset
                  </button>
                ) : null}
              </div>

              {/* Filter Radius GPS */}
              <div className="mt-2.5 flex items-center gap-1 overflow-x-auto no-scrollbar">
                <span className="mr-1 shrink-0 text-[10px] font-bold uppercase tracking-wider text-slate-400">
                  Radius:
                </span>
                {RADIUS_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => handleRadiusChange(opt.value)}
                    className={cn(
                      'shrink-0 rounded-full border px-2.5 py-0.5 text-[10px] font-bold transition',
                      radiusKm === opt.value
                        ? 'border-toba bg-toba-mist text-toba-dark'
                        : 'border-slate-200 bg-white text-slate-500 hover:border-slate-300',
                    )}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>

              <button
                type="button"
                onClick={() => activateLocationAndNearest(true)}
                disabled={locating}
                className="mt-3 flex w-full items-center justify-center gap-1.5 rounded-xl bg-toba px-3 py-2 text-[11px] font-bold text-white shadow-sm transition hover:bg-toba-dark disabled:opacity-60"
              >
                <span className={cn('material-symbols-outlined text-[16px]', locating && 'animate-spin')}>
                  {locating ? 'progress_activity' : 'near_me'}
                </span>
                {locating ? 'Mendeteksi lokasi...' : 'Rute ke RS IGD Terdekat'}
              </button>
            </div>

            {/* List RS */}
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
                  <button
                    type="button"
                    onClick={load}
                    className="mt-3 rounded-full bg-toba px-4 py-2 text-[11px] font-semibold text-white"
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
                              ? 'border-toba/50 bg-toba-mist/85 shadow-sm'
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
                            <span className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg bg-toba-mist text-toba">
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
                              {hospital.distKm != null ? (
                                <span className="rounded bg-toba-mist px-1.5 py-0.5 text-[9px] font-extrabold text-toba-dark">
                                  {hospital.distKm.toFixed(1)} km
                                </span>
                              ) : null}
                              {hospital.eta?.durationSec != null ? (
                                <span className="rounded bg-amber-50 px-1.5 py-0.5 text-[9px] font-bold text-amber-800">
                                  {formatDuration(hospital.eta.durationSec)}
                                </span>
                              ) : null}
                            </span>
                          </span>
                          <span className="flex flex-col gap-1">
                            <span className="material-symbols-outlined text-[15px] text-slate-400" aria-hidden="true">
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
                  <p className="mt-2 text-xs font-semibold text-slate-700">
                    Tidak ada rumah sakit dalam kriteria/area ini.
                  </p>
                </div>
              )}
            </div>
          </aside>

          {/* Kanvas Peta + Kontrol Mengambang */}
          <div className="relative flex-1">
            <LeafletMap
              hospitals={filtered}
              selectedId={selectedId}
              onSelect={selectHospital}
              fit={!activeBounds}
              tileMode={tileMode}
              userLocation={userPos}
              radiusKm={radiusKm}
              referralLinks={referralLinks}
              onLocate={(pos) => {
                if (pos) setUserPos(pos);
              }}
              onUserViewportChange={(bounds) => setPendingBounds(bounds)}
              routeTarget={routeActive && selected ? selected : null}
              routeMode={routeMode}
              onRouteInfo={setRouteInfo}
              onRouteError={(err) => {
                setRouteError(err.message);
                toast(err.message, 'error');
              }}
              className="h-full"
            />

            {/* Floating Top-Left: Map Layer Switcher + Mobile List Button */}
            <div className="absolute left-3 top-3 z-20 flex flex-wrap items-center gap-2">
              {!sidebarOpen ? (
                <button
                  type="button"
                  onClick={() => setSidebarOpen(true)}
                  className="inline-flex items-center gap-1.5 rounded-full bg-white px-3.5 py-2 text-[11px] font-bold text-toba-dark shadow-floating lg:hidden"
                >
                  <span className="material-symbols-outlined text-[16px]">list</span>
                  Daftar ({filtered.length})
                </button>
              ) : null}

              <div
                className="inline-flex items-center gap-1 rounded-full border border-slate-200/90 bg-white/95 p-1 shadow-floating backdrop-blur"
                role="group"
                aria-label="Pilih jenis tampilan peta"
              >
                {TILE_MODES.map((m) => (
                  <button
                    key={m.id}
                    type="button"
                    onClick={() => setTileMode(m.id)}
                    className={cn(
                      'inline-flex items-center gap-1 rounded-full px-3 py-1 text-[11px] font-bold transition',
                      tileMode === m.id
                        ? 'bg-toba text-white shadow-sm'
                        : 'text-slate-600 hover:bg-slate-100',
                    )}
                  >
                    <span className="material-symbols-outlined text-[14px]">{m.icon}</span>
                    <span className="hidden sm:inline">{m.label}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Floating Top-Center: "Cari di Area Peta Ini" */}
            {pendingBounds || activeBounds ? (
              <div className="absolute left-1/2 top-14 z-20 flex -translate-x-1/2 items-center gap-1.5 sm:top-3">
                {pendingBounds ? (
                  <button
                    type="button"
                    onClick={applyViewportSearch}
                    className="inline-flex items-center gap-1.5 rounded-full border border-toba/30 bg-white px-4 py-2 text-[11px] font-extrabold text-toba-dark shadow-floating transition hover:bg-toba hover:text-white"
                  >
                    <span className="material-symbols-outlined text-[15px]">travel_explore</span>
                    Cari di area peta ini
                  </button>
                ) : null}
                {activeBounds ? (
                  <button
                    type="button"
                    onClick={() => {
                      setActiveBounds(null);
                      setPendingBounds(null);
                    }}
                    className="inline-flex items-center gap-1 rounded-full bg-slate-900/85 px-3 py-2 text-[11px] font-bold text-white shadow-floating backdrop-blur transition hover:bg-slate-900"
                  >
                    <span>Area peta aktif</span>
                    <span className="material-symbols-outlined text-[14px]">close</span>
                  </button>
                ) : null}
              </div>
            ) : null}

            {/* Floating Bottom-Left (kanvas peta): Legenda Kelas Interaktif.
                Disembunyikan saat kartu RS terpilih / panel rute tampil di posisi yang sama. */}
            <div
              className={cn(
                'pointer-events-auto absolute bottom-4 left-4 z-20 hidden rounded-2xl border border-slate-200/90 bg-white/95 p-3 shadow-floating backdrop-blur',
                selected ? 'sm:hidden' : 'sm:block',
              )}
            >
              <p className="text-[10px] font-extrabold uppercase tracking-wider text-slate-400">
                Legenda Kelas RS
              </p>
              <div className="mt-2 flex flex-col gap-1.5">
                {KELAS_OPTIONS.map((opt) => {
                  const active = kelas === opt.value;
                  return (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => updateParams({ kelas: active ? '' : opt.value, rs: '' })}
                      className={cn(
                        'flex items-center justify-between gap-3 rounded-lg px-2 py-1 text-[11px] font-bold transition',
                        active ? 'bg-toba-mist text-toba-dark ring-1 ring-toba/30' : 'text-slate-700 hover:bg-slate-50',
                      )}
                    >
                      <span className="flex items-center gap-2">
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ backgroundColor: KELAS_COLOR[opt.value] || '#64748B' }}
                        />
                        Kelas {opt.value}
                      </span>
                      <span className="text-[10px] font-medium text-slate-400">
                        {hospitals.filter((h) => h.kelas === opt.value).length}
                      </span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Floating Selected Hospital Card + Rujukan Berjenjang + Navigasi Eksternal */}
            {selected && !routeActive ? (
              <div className="absolute bottom-4 left-3 right-3 z-20 animate-slide-up sm:right-auto sm:w-[410px]">
                <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-modal">
                  <div className="flex items-start gap-3 p-3.5">
                    {selected.foto ? (
                      <img
                        src={selected.foto}
                        alt={selected.nama}
                        className="h-16 w-16 shrink-0 rounded-xl bg-slate-100 object-cover"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : null}
                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-1">
                        <p className="line-clamp-2 text-xs font-extrabold text-slate-900">
                          {selected.nama}
                        </p>
                        <button
                          type="button"
                          onClick={() => {
                            setReferralMode(false);
                            updateParams({ rs: '' });
                          }}
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-slate-400 hover:bg-slate-100 hover:text-slate-700"
                          aria-label="Tutup pratinjau"
                        >
                          <span className="material-symbols-outlined text-[15px]">close</span>
                        </button>
                      </div>
                      <p className="mt-0.5 text-[11px] text-slate-500">
                        Kelas {selected.kelas || '—'} • {selected.kabkota || 'Sumatera Utara'}
                        {selected.distKm != null ? ` • ${selected.distKm.toFixed(1)} km` : ''}
                        {selected.eta?.durationSec != null
                          ? ` (${formatDuration(selected.eta.durationSec)})`
                          : ''}
                      </p>
                      <p className="mt-0.5 line-clamp-1 text-[10.5px] text-slate-400">
                        {selected.alamat}
                      </p>
                    </div>
                  </div>

                  {/* Panel Jaringan Rujukan Berjenjang BPJS */}
                  {referralMode && referralLinks.length > 0 ? (
                    <div className="border-t border-slate-100 bg-toba-mist/55 px-3.5 py-2.5">
                      <div className="mb-1.5 flex items-center justify-between">
                        <span className="text-[10px] font-extrabold uppercase tracking-wider text-toba-dark">
                          Jaringan Rujukan Berjenjang
                        </span>
                        <button
                          type="button"
                          onClick={() => setReferralMode(false)}
                          className="text-[10px] font-bold text-slate-500 hover:text-slate-800"
                        >
                          Sembunyikan
                        </button>
                      </div>
                      <div className="space-y-1.5">
                        {referralLinks.map((link) => (
                          <button
                            key={link.target.id}
                            type="button"
                            onClick={() => {
                              setReferralMode(false);
                              selectHospital(link.target);
                            }}
                            className="flex w-full items-center justify-between gap-2 rounded-xl border border-toba/20 bg-white px-2.5 py-1.5 text-left transition hover:border-toba"
                          >
                            <div className="min-w-0">
                              <p className="text-[9.5px] font-bold text-toba">{link.tierLabel}</p>
                              <p className="truncate text-[11px] font-extrabold text-slate-900">
                                {link.target.nama}
                              </p>
                            </div>
                            <span className="shrink-0 rounded-full bg-toba-mist px-2 py-0.5 text-[10px] font-extrabold text-toba-dark">
                              {link.distanceKm.toFixed(1)} km →
                            </span>
                          </button>
                        ))}
                      </div>
                    </div>
                  ) : null}

                  <div className="flex flex-wrap items-center gap-1.5 border-t border-slate-100 bg-slate-50 px-3.5 py-2.5">
                    <button
                      type="button"
                      onClick={() => startRoute(selected)}
                      disabled={selected.lat == null || selected.lon == null}
                      className="flex flex-1 items-center justify-center gap-1 rounded-full bg-toba px-3 py-2 text-[11px] font-bold text-white transition hover:bg-toba-dark disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-[15px]">directions</span>
                      Rute
                    </button>

                    <button
                      type="button"
                      onClick={() => setReferralMode((prev) => !prev)}
                      className={cn(
                        'flex items-center justify-center gap-1 rounded-full px-3 py-2 text-[11px] font-bold transition',
                        referralMode
                          ? 'bg-amber-600 text-white'
                          : 'border border-amber-300 bg-amber-50 text-amber-900 hover:bg-amber-100',
                      )}
                      title="Tampilkan garis rujukan ke RS tingkat lanjut terdekat"
                    >
                      <span className="material-symbols-outlined text-[14px]">account_tree</span>
                      Rujukan
                    </button>

                    <button
                      type="button"
                      onClick={() => toggleCompare(selected.id)}
                      className={cn(
                        'flex items-center justify-center gap-1 rounded-full px-3 py-2 text-[11px] font-bold transition',
                        isCompared(selected.id)
                          ? 'bg-toba-dark text-white'
                          : 'border border-toba/30 bg-white text-toba-dark hover:bg-toba-mist',
                      )}
                    >
                      <span className="material-symbols-outlined text-[14px]">compare</span>
                      {isCompared(selected.id) ? 'Dipilih' : '+ Banding'}
                    </button>

                    <Link
                      to={`/rumah-sakit/${encodeURIComponent(selected.id)}`}
                      className="flex items-center justify-center rounded-full border border-slate-300 bg-white px-3 py-2 text-[11px] font-bold text-slate-700 transition hover:bg-slate-100"
                    >
                      Profil
                    </Link>
                  </div>

                  {/* Bar Handoff Navigasi HP */}
                  <div className="flex items-center justify-between border-t border-slate-200/70 bg-white px-3.5 py-2 text-[10.5px]">
                    <span className="font-semibold text-slate-400">Buka navigasi di:</span>
                    <div className="flex items-center gap-2">
                      <a
                        href={googleMapsDirUrl(selected)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 font-bold text-toba-dark hover:underline"
                      >
                        Google Maps
                        <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                      </a>
                      <span className="text-slate-300">|</span>
                      <a
                        href={wazeDirUrl(selected)}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 font-bold text-sky-700 hover:underline"
                      >
                        Waze
                        <span className="material-symbols-outlined text-[12px]">open_in_new</span>
                      </a>
                    </div>
                  </div>
                </div>
              </div>
            ) : null}

            {/* Route Panel + Turn-by-Turn Bahasa Indonesia */}
            {routeActive && selected ? (
              <div className="absolute bottom-4 left-3 right-3 z-20 animate-slide-up sm:right-auto sm:w-[405px]">
                <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-modal">
                  <div className="flex items-start justify-between gap-2 border-b border-slate-100 bg-toba-mist/60 px-4 py-3">
                    <div className="min-w-0">
                      <p className="text-[10px] font-bold uppercase tracking-wider text-toba">
                        Panduan Rute • Tekan Esc untuk tutup
                      </p>
                      <p className="mt-0.5 line-clamp-1 text-xs font-extrabold text-slate-900">
                        {selected.nama}
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => updateParams({ route: '' })}
                      className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-slate-500 ring-1 ring-slate-200 transition hover:bg-slate-100"
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
                            ? 'bg-toba text-white'
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
                      <>
                        <div className="flex items-center justify-between gap-2">
                          <div>
                            <p className="text-[10px] text-slate-500">Estimasi perjalanan</p>
                            <p className="mt-0.5 text-lg font-extrabold text-slate-900">
                              {formatDuration(routeInfo.time).replace('~', '')}
                            </p>
                          </div>
                          <div className="text-right">
                            <p className="text-[10px] text-slate-500">Jarak tempuh</p>
                            <p className="mt-0.5 text-sm font-bold text-toba">
                              {formatDistance(routeInfo.distance)}
                            </p>
                          </div>
                        </div>

                        {steps.length > 0 ? (
                          <div className="mt-3 border-t border-slate-100 pt-2.5">
                            <button
                              type="button"
                              onClick={() => setStepsExpanded((prev) => !prev)}
                              className="flex w-full items-center justify-between text-[11px] font-bold text-toba-dark"
                            >
                              <span>Petunjuk Belok Demi Belok ({steps.length} langkah)</span>
                              <span className="material-symbols-outlined text-[16px]">
                                {stepsExpanded ? 'expand_less' : 'expand_more'}
                              </span>
                            </button>

                            {stepsExpanded ? (
                              <ol className="mt-2 max-h-40 space-y-1.5 overflow-y-auto pr-1 text-[11px] scrollbar-thin">
                                {steps.map((s) => (
                                  <li
                                    key={s.step}
                                    className="flex items-start justify-between gap-2 rounded-lg bg-slate-50 px-2.5 py-1.5"
                                  >
                                    <span className="text-slate-700">
                                      <strong className="mr-1.5 text-toba">{s.step}.</strong>
                                      {s.instruction}
                                    </span>
                                    <span className="shrink-0 font-semibold text-slate-400">
                                      {formatDistance(s.distance)}
                                    </span>
                                  </li>
                                ))}
                              </ol>
                            ) : null}
                          </div>
                        ) : null}

                        <div className="mt-3 flex items-center gap-2 border-t border-slate-100 pt-2.5">
                          <a
                            href={googleMapsDirUrl(selected)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex flex-1 items-center justify-center gap-1 rounded-full border border-slate-300 bg-white px-3 py-1.5 text-[11px] font-bold text-slate-700 transition hover:bg-slate-50"
                          >
                            Google Maps
                            <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                          </a>
                          <a
                            href={wazeDirUrl(selected)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="flex flex-1 items-center justify-center gap-1 rounded-full border border-sky-200 bg-sky-50 px-3 py-1.5 text-[11px] font-bold text-sky-800 transition hover:bg-sky-100"
                          >
                            Waze
                            <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                          </a>
                        </div>
                      </>
                    ) : (
                      <p className="flex items-center gap-1.5 text-[11px] text-slate-500">
                        <span className="h-3.5 w-3.5 animate-spin rounded-full border-2 border-slate-200 border-t-toba" />
                        Menghitung rute dari lokasi Anda...
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ) : null}
          </div>
        </div>
      </main>
    </div>
  );
}
