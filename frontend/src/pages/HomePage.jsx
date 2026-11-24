import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAllHospitals, getFilterOptions } from '../api';
import { KELAS_COLOR, SPECIALTIES, HOME_IMAGES } from '../constants';
import HospitalCard from '../components/HospitalCard';
import LeafletMap from '../components/LeafletMap';
import SearchAutocomplete from '../components/SearchAutocomplete';
import SiteHeader from '../components/SiteHeader';
import { EditorialFooter } from '../components/Footer';

const FEATURED_IDS = ['rs-171', 'rs-157', 'rs-008', 'rs-003', 'rs-011', 'rs-025'];

function SpecialtyCard({ item }) {
  return (
    <Link
      to={`/pencarian?layanan=${encodeURIComponent(item.service)}`}
      className="group relative block aspect-square overflow-hidden rounded-2xl bg-slate-200 shadow-sm transition-shadow duration-150 hover:shadow-md"
    >
      <img
        src={item.image}
        alt={item.title}
        loading="lazy"
        className="absolute inset-0 h-full w-full object-cover object-center"
        onError={(event) => {
          event.currentTarget.style.display = 'none';
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-900/35 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 flex flex-col justify-end p-5">
        <h3 className="text-lg font-semibold leading-tight text-white">{item.title}</h3>
        <p className="mt-1 text-xs font-medium text-white/80">{item.note}</p>
        <span className="mt-2 inline-flex items-center gap-2 text-xs font-medium text-white">
          Jelajahi
          <span className="material-symbols-outlined text-sm">arrow_forward</span>
        </span>
      </div>
    </Link>
  );
}

export default function HomePage() {
  const navigate = useNavigate();
  const [hospitals, setHospitals] = useState([]);
  const [options, setOptions] = useState({ kabkota: [], layanan: [] });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [query, setQuery] = useState('');

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

  const stats = useMemo(() => {
    const regions = new Set(hospitals.map((hospital) => hospital.kabkota).filter(Boolean));
    return {
      total: hospitals.length,
      regions: regions.size,
      bpjs: hospitals.filter((hospital) => hospital.bpjs).length,
    };
  }, [hospitals]);

  const featured = useMemo(() => {
    if (!hospitals.length) return [];
    const byId = new Map(hospitals.map((hospital) => [hospital.id, hospital]));
    const picks = FEATURED_IDS.map((id) => byId.get(id)).filter(Boolean);
    if (picks.length >= 6) return picks;
    const seen = new Set(picks.map((hospital) => hospital.id));
    return [...picks, ...hospitals.filter((hospital) => !seen.has(hospital.id))].slice(0, 6);
  }, [hospitals]);

  const goSearch = (raw) => {
    const text = String(raw ?? query).trim();
    const params = new URLSearchParams();
    if (text) params.set('q', text);
    navigate(`/pencarian${params.toString() ? `?${params.toString()}` : ''}`);
  };

  return (
    <div className="min-h-screen bg-white">
      <SiteHeader active="beranda" />

      {/* Split Editorial Hero + Live Geospasial Map Above the Fold */}
      <section className="border-b border-slate-200 bg-stone-50">
        <div className="mx-auto grid max-w-[1400px] grid-cols-1 items-center gap-8 px-4 py-8 sm:px-6 lg:grid-cols-12 lg:gap-10 lg:py-12">
          {/* Kolom Kiri: Pencarian Rumah Sakit */}
          <div className="lg:col-span-6">
            <h1 className="text-4xl font-medium leading-[1.08] tracking-tight text-slate-900 sm:text-[44px] lg:text-[56px]">
              Cari dan petakan rumah sakit di <span className="text-toba-dark">Sumatera Utara</span>
            </h1>

            <p className="mt-4 max-w-xl text-base leading-7 text-slate-600">
              Cari rumah sakit, layanan poliklinik, status BPJS, dan rute di kabupaten/kota
              Sumatera Utara.
            </p>

            <div className="mt-6">
              <SearchAutocomplete
                compact
                value={query}
                onChange={setQuery}
                onSubmit={goSearch}
                onSelectHospital={(h) => navigate(`/rumah-sakit/${encodeURIComponent(h.id)}`)}
                onSelectService={(srv) => {
                  if (srv.layanan) {
                    navigate(`/pencarian?layanan=${encodeURIComponent(srv.layanan)}`);
                  } else {
                    goSearch(srv.query);
                  }
                }}
                onSelectRegion={(reg) =>
                  navigate(`/pencarian?kabkota=${encodeURIComponent(reg)}`)
                }
                hospitals={hospitals}
                options={options}
                placeholder="Cari rumah sakit, layanan, atau kota"
                buttonLabel="Cari"
              />
            </div>

            {/* Filter & Pencarian Cepat */}
            <div className="mt-4 flex flex-wrap items-center gap-x-3 gap-y-2">
              <span className="text-xs font-medium text-slate-500">
                Pencarian cepat
              </span>
              {[
                { label: 'RSUP H. Adam Malik', params: { q: 'rsup ham' } },
                { label: 'Cuci Darah BPJS', params: { q: 'cuci darah bpjs' } },
                { label: 'Kelas A', params: { kelas: 'A' } },
                { label: 'Kelas B', params: { kelas: 'B' } },
                { label: 'IGD 24 Jam', params: { layanan: 'UGD 24 Jam' } },
                { label: 'Medan', params: { kabkota: 'Kota Medan' } },
              ].map((item) => (
                <Link
                  key={item.label}
                  to={`/pencarian?${new URLSearchParams(item.params).toString()}`}
                  className="text-xs font-medium text-slate-700 underline-offset-4 transition-colors duration-150 hover:text-toba-dark hover:underline"
                >
                  {item.label}
                </Link>
              ))}
            </div>

            {/* Ringkasan Statistik */}
            <div className="mt-6 grid grid-cols-3 gap-3 border-t border-slate-200/80 pt-5">
              <div>
                <p className="text-2xl font-medium tabular-nums text-slate-900">
                  {loading ? '—' : stats.total}
                </p>
                <p className="text-xs text-slate-500">Rumah sakit</p>
              </div>
              <div>
                <p className="text-2xl font-medium tabular-nums text-slate-900">
                  {loading ? '—' : stats.bpjs}
                </p>
                <p className="text-xs text-slate-500">Menerima BPJS</p>
              </div>
              <div>
                <p className="text-2xl font-medium tabular-nums text-slate-900">
                  {loading ? '—' : stats.regions}
                </p>
                <p className="text-xs text-slate-500">Kabupaten/kota</p>
              </div>
            </div>
          </div>

          {/* Kolom Kanan: Peta Geospasial Langsung */}
          <div className="lg:col-span-6">
            <div className="relative h-[368px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm sm:h-[432px]">
              <LeafletMap
                hospitals={hospitals}
                fit
                showZoom
                showLocate
                onSelect={(item) => navigate(`/rumah-sakit/${encodeURIComponent(item.id)}`)}
                className="h-full w-full"
              />

              {/* Legenda Ringkas & CTA Peta Penuh */}
              <div className="pointer-events-none absolute inset-x-3 bottom-3 z-[500] flex flex-wrap items-center justify-between gap-2">
                <div className="pointer-events-auto flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-medium text-slate-700">
                  {(['A', 'B', 'C', 'D']).map((k) => (
                    <span key={k} className="inline-flex items-center gap-1">
                      <span
                        className="h-2 w-2 rounded-full"
                        style={{ backgroundColor: KELAS_COLOR[k] || '#64748B' }}
                      />
                      {k}
                    </span>
                  ))}
                </div>

                <Link
                  to="/peta"
                  className="pointer-events-auto inline-flex items-center gap-2 rounded-lg bg-toba-dark px-4 py-2 text-xs font-semibold text-white transition-colors duration-150 hover:bg-toba"
                >
                  <span className="material-symbols-outlined text-base">open_in_full</span>
                  Buka peta dan rute
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Specialties */}
      <section className="border-b border-slate-200 bg-white py-16">
        <div className="mx-auto max-w-[1360px] px-6 lg:px-10">
          <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <h2 className="text-2xl font-semibold leading-tight text-slate-900 sm:text-3xl">
                Jelajahi layanan medis
              </h2>
              <p className="mt-2 max-w-2xl text-sm text-slate-500">
                Jelajahi layanan klinis dan fasilitas pendukung di rumah sakit Sumatera Utara.
              </p>
            </div>
            <Link
              to="/pencarian"
              className="inline-flex w-fit items-center gap-2 rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 transition-colors duration-150 hover:border-toba hover:text-toba-dark"
            >
              Lihat semua
              <span className="material-symbols-outlined text-base">arrow_forward</span>
            </Link>
          </div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {SPECIALTIES.map((item) => (
              <SpecialtyCard key={item.title} item={item} />
            ))}
          </div>
        </div>
      </section>

      {/* Editorial 1 */}
      <section className="border-b border-slate-200 bg-white py-16">
        <div className="mx-auto max-w-[1120px] px-6">
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-16">
            <div className="flex flex-col justify-center lg:col-span-5">
              <h2 className="text-3xl font-medium leading-tight text-slate-900 md:text-4xl">
                Bandingkan rumah sakit berdasarkan layanan dan fasilitas
              </h2>
              <p className="mt-4 text-base leading-relaxed text-slate-600">
                Bandingkan hingga 3 rumah sakit berdasarkan kelas, status BPJS, layanan medis,
                jadwal poliklinik, dan kuota kamar.
              </p>
              <div className="mt-6">
                <Link
                  to="/pencarian"
                  className="inline-flex items-center justify-center rounded-lg border border-toba px-5 py-3 text-sm font-medium text-toba-dark transition-colors duration-150 hover:bg-toba hover:text-white"
                >
                  Mulai bandingkan RS
                </Link>
              </div>
            </div>
            <div className="lg:col-span-7">
              <div className="relative mx-auto h-[340px] w-full max-w-2xl overflow-hidden rounded-2xl bg-slate-100 sm:h-[380px]">
                <img
                  src={HOME_IMAGES.editorialOne}
                  alt="Bangunan rumah sakit dengan fasilitas modern"
                  loading="lazy"
                  className="h-full w-full object-cover object-center"
                  onError={(event) => {
                    event.currentTarget.style.display = 'none';
                  }}
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/75 to-transparent p-5 pt-16">
                  <p className="text-sm font-medium text-white/80">
                    Informasi rumah sakit
                  </p>
                  <p className="mt-1 text-lg font-semibold text-white">
                    Profil, layanan, jadwal poliklinik, dan ulasan dalam satu tampilan.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Directory */}
      <section id="direktori-rumah-sakit" className="border-b border-slate-200 bg-white py-16">
        <div className="mx-auto max-w-[1160px] px-6">
          <div className="mb-9 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div className="max-w-2xl">
              <h2 className="text-3xl font-medium leading-tight text-slate-900 md:text-4xl">
                Direktori rumah sakit
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                Rumah sakit di kabupaten dan kota Sumatera Utara.
              </p>
            </div>
            <Link
              to="/pencarian"
              className="inline-flex w-fit shrink-0 items-center gap-2 rounded-lg border border-toba bg-white px-5 py-2.5 text-sm font-medium text-toba-dark transition-colors duration-150 hover:bg-toba-mist"
            >
              <span>Lihat semua rumah sakit ({stats.total})</span>
              <span className="material-symbols-outlined text-base">arrow_forward</span>
            </Link>
          </div>

          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center">
              <p className="text-sm font-semibold text-rose-700">Direktori belum dapat dimuat.</p>
              <p className="mt-1 text-xs text-rose-600">{error}</p>
              <button
                type="button"
                onClick={load}
                className="mt-4 rounded-lg bg-rose-700 px-5 py-2 text-sm font-medium text-white transition-colors duration-150 hover:bg-rose-800"
              >
                Coba lagi
              </button>
            </div>
          ) : loading ? (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {Array.from({ length: 6 }).map((_, index) => (
                <div
                  key={index}
                  className="overflow-hidden rounded-2xl border border-slate-200 bg-white"
                >
                  <div className="h-48 bg-slate-100" />
                  <div className="space-y-3 p-5">
                    <div className="h-4 w-3/4 rounded bg-slate-100" />
                    <div className="h-3 w-1/2 rounded bg-slate-100" />
                    <div className="h-3 w-full rounded bg-slate-100" />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
              {featured.map((hospital) => (
                <HospitalCard
                  key={hospital.id}
                  hospital={hospital}
                  onRoute={(item) => navigate(`/peta?rs=${encodeURIComponent(item.id)}&route=1`)}
                />
              ))}
            </div>
          )}
        </div>
      </section>

      <EditorialFooter />
    </div>
  );
}
