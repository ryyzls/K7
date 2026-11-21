import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { getAllHospitals } from '../api';
import { SPECIALTIES, HOME_IMAGES } from '../constants';
import HospitalCard from '../components/HospitalCard';
import LeafletMap from '../components/LeafletMap';
import SiteHeader from '../components/SiteHeader';
import { EditorialFooter } from '../components/Footer';

const FEATURED_IDS = ['rs-171', 'rs-157', 'rs-008', 'rs-003', 'rs-011', 'rs-025'];

function SpecialtyCard({ item }) {
  return (
    <Link
      to={`/pencarian?layanan=${encodeURIComponent(item.service)}`}
      className="group relative block aspect-square overflow-hidden rounded-2xl bg-slate-900 shadow-sm transition-all duration-300 hover:shadow-lg"
    >
      <img
        src={item.image}
        alt={item.title}
        loading="lazy"
        className="absolute inset-0 h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-105"
        onError={(event) => {
          event.currentTarget.style.display = 'none';
        }}
      />
      <div className="absolute inset-0 bg-gradient-to-t from-slate-950/90 via-slate-900/35 to-transparent" />
      <div className="absolute inset-x-0 bottom-0 flex flex-col justify-end p-5">
        <h3 className="font-sans text-lg font-bold leading-tight text-white">{item.title}</h3>
        <p className="mt-1 text-[11px] font-medium text-white/70">{item.note}</p>
        <span className="mt-2 inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-300">
          Jelajahi
          <span className="material-symbols-outlined text-[14px]">arrow_forward</span>
        </span>
      </div>
    </Link>
  );
}

export default function HomePage() {
  const navigate = useNavigate();
  const [hospitals, setHospitals] = useState([]);
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
  }, []);

  const stats = useMemo(() => {
    const regions = new Set(hospitals.map((hospital) => hospital.kabkota).filter(Boolean));
    return {
      total: hospitals.length || 206,
      regions: regions.size || 33,
      classA: hospitals.filter((hospital) => hospital.kelas === 'A').length || 3,
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

  const goSearch = (event) => {
    event.preventDefault();
    const params = new URLSearchParams();
    if (query.trim()) params.set('q', query.trim());
    navigate(`/pencarian${params.toString() ? `?${params.toString()}` : ''}`);
  };

  return (
    <div className="min-h-screen bg-[#FAFAF9]">
      <SiteHeader active="beranda" />

      {/* Hero */}
      <section className="relative flex min-h-[500px] flex-col justify-between overflow-hidden bg-slate-950 text-white sm:min-h-[560px]">
        <img
          src={HOME_IMAGES.hero}
          alt="Fasilitas rumah sakit modern di Sumatera Utara"
          className="absolute inset-0 h-full w-full object-cover object-center"
          onError={(event) => {
            event.currentTarget.style.display = 'none';
          }}
        />
        <div className="absolute inset-0 bg-gradient-to-b from-slate-950/90 via-slate-950/65 to-slate-950/90" />
        <div className="absolute inset-0 bg-[radial-gradient(circle_at_75%_20%,rgba(0,87,184,0.25),transparent_50%)]" />

        <div className="relative z-10 mx-auto flex w-full max-w-[1360px] flex-1 flex-col justify-center px-6 py-16 lg:px-10">
          <div className="max-w-3xl">
            <h1 className="font-serif-editorial text-[38px] font-normal leading-[1.08] tracking-tight sm:text-[52px] lg:text-[60px]">
              Temukan perawatan yang tepat,
              <br className="hidden sm:block" /> di fasilitas yang tepercaya.
            </h1>

            <p className="mt-5 max-w-2xl text-sm leading-relaxed text-slate-200/85 sm:text-base">
              Direktori semantik 206 rumah sakit di 33 kabupaten/kota Sumatera Utara. Cari berdasarkan
              kelas, layanan, wilayah, lalu hubungkan data RDF dengan peta dan asisten pintar.
            </p>

            <form
              onSubmit={goSearch}
              className="mt-7 flex flex-col gap-2 rounded-2xl border border-white/15 bg-white/10 p-2 backdrop-blur-md sm:flex-row sm:items-center"
            >
              <div className="relative flex-1">
                <span className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-white/55">
                  <span className="material-symbols-outlined text-[20px]">search</span>
                </span>
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Cari rumah sakit, layanan, atau wilayah..."
                  className="w-full rounded-xl border border-transparent bg-transparent py-3 pl-12 pr-4 text-sm text-white outline-none placeholder:text-white/50 focus:border-white/30 focus:bg-white/5"
                  aria-label="Cari rumah sakit"
                />
              </div>
              <button
                type="submit"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/25 bg-brand-navy px-6 py-3 text-sm font-bold text-white shadow-md transition hover:bg-brand-blue"
              >
                Cari sekarang
                <span className="material-symbols-outlined text-[18px]">arrow_forward</span>
              </button>
            </form>

            <div className="mt-4 flex flex-wrap items-center gap-2">
              <span className="text-[10.5px] font-semibold uppercase tracking-wide text-white/45">
                Cepat:
              </span>
              {[
                { label: 'Kelas A', params: { kelas: 'A' } },
                { label: 'IGD 24 Jam', params: { layanan: 'UGD 24 Jam' } },
                { label: 'BPJS', params: { bpjs: '1' } },
                { label: 'Kota Medan', params: { kabkota: 'Kota Medan' } },
              ].map((item) => (
                <Link
                  key={item.label}
                  to={`/pencarian?${new URLSearchParams(item.params).toString()}`}
                  className="rounded-full border border-white/20 bg-white/5 px-3 py-1 text-[11px] font-medium text-white/85 backdrop-blur transition hover:border-white/40 hover:bg-white/10"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </div>

      </section>

      {/* Specialties */}
      <section className="border-b border-slate-200 bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-[1360px] px-6 lg:px-10">
          <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div>
              <h2 className="font-sans text-[26px] font-bold leading-snug tracking-tight text-slate-900 sm:text-[32px]">
                Jelajahi Layanan Medis
              </h2>
              <p className="mt-1.5 max-w-2xl text-sm text-slate-500">
                Temukan fasilitas kesehatan terakreditasi berdasarkan ketersediaan layanan klinis dan teknologi
                pendukung.
              </p>
            </div>
            <Link
              to="/pencarian"
              className="inline-flex w-fit items-center gap-1.5 rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-emerald-600 hover:text-emerald-700"
            >
              Lihat semua
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
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
        <div className="mx-auto max-w-[1080px] px-6">
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-16">
            <div className="flex flex-col justify-center lg:col-span-5">
              <h2 className="font-serif-editorial text-[32px] font-normal leading-tight tracking-tight text-brand-navy md:text-[38px]">
                Kesehatan Anda, prioritas kami.
              </h2>
              <p className="mt-4 text-[15px] leading-relaxed text-slate-600">
                Bandingkan rumah sakit berdasarkan kelas, jenis, layanan, dan status BPJS. Semua informasi
                tersaji dalam satu pengalaman pencarian yang tenang dan terstruktur.
              </p>
              <div className="mt-6">
                <Link
                  to="/pencarian"
                  className="inline-flex items-center justify-center rounded-full border-[1.5px] border-brand-blue bg-white px-6 py-2.5 text-sm font-semibold text-brand-blue transition hover:bg-slate-50"
                >
                  Temukan layanan kesehatan
                </Link>
              </div>
            </div>
            <div className="lg:col-span-7">
              <div className="relative mx-auto h-[360px] w-full max-w-2xl overflow-hidden rounded-2xl bg-slate-100 sm:h-[420px]">
                <img
                  src={HOME_IMAGES.editorialOne}
                  alt="Bangunan rumah sakit dengan fasilitas modern"
                  loading="lazy"
                  className="h-full w-full object-cover object-center"
                  onError={(event) => {
                    event.currentTarget.style.display = 'none';
                  }}
                />
                <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-slate-950/70 to-transparent p-5 pt-16">
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-white/70">
                    Data master faskes
                  </p>
                  <p className="mt-1 font-serif-editorial text-lg text-white">
                    Profil, layanan, dan fasilitas dalam satu halaman.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Editorial 2 */}
      <section className="border-b border-slate-200 bg-white py-16">
        <div className="mx-auto max-w-[1080px] px-6">
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12 lg:gap-16">
            <div className="order-2 lg:order-1 lg:col-span-6">
              <div className="relative mx-auto aspect-[4/3] w-full max-w-lg overflow-hidden rounded-2xl bg-slate-100">
                <img
                  src={HOME_IMAGES.editorialTwo}
                  alt="Rumah sakit rujukan di Sumatera Utara"
                  loading="lazy"
                  className="h-full w-full object-cover object-center"
                  onError={(event) => {
                    event.currentTarget.style.display = 'none';
                  }}
                />
                <span className="absolute bottom-4 left-4 inline-flex items-center gap-1.5 rounded-full bg-white/95 px-3 py-1.5 text-[10.5px] font-bold text-slate-800 shadow-sm backdrop-blur">
                  <span className="material-symbols-outlined text-[14px] text-emerald-600">verified_user</span>
                  Terverifikasi Kemenkes RI
                </span>
              </div>
            </div>
            <div className="order-1 flex flex-col justify-center lg:order-2 lg:col-span-6">
              <h2 className="font-serif-editorial text-[32px] font-normal leading-tight tracking-tight text-brand-navy md:text-[38px]">
                Bingung memilih layanan yang tepat?
              </h2>
              <p className="mt-4 text-[15px] leading-relaxed text-slate-600">
                Gunakan asisten semantik untuk bertanya dengan bahasa sehari-hari. Asisten membaca data RDF
                dan mengembalikan rumah sakit yang relevan, lengkap dengan tautan profil dan rute.
              </p>
              <div className="mt-6 flex flex-wrap gap-2.5">
                <button
                  type="button"
                  onClick={() => window.dispatchEvent(new Event('carisehat:open-chat'))}
                  className="inline-flex items-center gap-1.5 rounded-full border-[1.5px] border-brand-blue bg-white px-6 py-2.5 text-sm font-semibold text-brand-blue transition hover:bg-slate-50"
                >
                  <span className="material-symbols-outlined text-[17px]">chat</span>
                  Tanya asisten
                </button>
                <Link
                  to="/peta"
                  className="inline-flex items-center gap-1.5 rounded-full bg-brand-navy px-6 py-2.5 text-sm font-semibold text-white transition hover:bg-brand-blue"
                >
                  <span className="material-symbols-outlined text-[17px]">map</span>
                  Buka peta
                </Link>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Directory */}
      <section id="direktori-rumah-sakit" className="border-b border-slate-200 bg-white py-16 lg:py-20">
        <div className="mx-auto max-w-[1120px] px-6">
          <div className="mb-9 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div className="max-w-2xl">
              <h2 className="font-serif-editorial text-[32px] font-normal leading-tight tracking-tight text-slate-900 md:text-[38px]">
                Direktori Rumah Sakit &amp; Layanan Kesehatan
              </h2>
              <p className="mt-2 text-sm text-slate-500">
                Pilihan fasilitas rujukan utama dari dataset semantik Sumatera Utara.
              </p>
            </div>
            <Link
              to="/pencarian"
              className="inline-flex w-fit shrink-0 items-center gap-2 rounded-full border border-brand-blue bg-white px-5 py-2.5 text-xs font-semibold text-brand-blue shadow-none transition hover:bg-slate-50"
            >
              <span>Lihat semua rumah sakit ({stats.total})</span>
              <span className="material-symbols-outlined text-[16px]">arrow_forward</span>
            </Link>
          </div>

          {error ? (
            <div className="rounded-2xl border border-rose-200 bg-rose-50 p-6 text-center">
              <p className="text-sm font-semibold text-rose-700">Direktori belum dapat dimuat.</p>
              <p className="mt-1 text-xs text-rose-600">{error}</p>
              <button
                type="button"
                onClick={load}
                className="mt-4 rounded-full bg-rose-600 px-5 py-2 text-xs font-semibold text-white transition hover:bg-rose-700"
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
                  <div className="h-[185px] animate-pulse bg-slate-100" />
                  <div className="space-y-3 p-5">
                    <div className="h-4 w-3/4 animate-pulse rounded bg-slate-100" />
                    <div className="h-3 w-1/2 animate-pulse rounded bg-slate-100" />
                    <div className="h-3 w-full animate-pulse rounded bg-slate-100" />
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

      {/* Map teaser */}
      <section className="border-b border-slate-200 bg-[#F4F6F9] py-16 lg:py-20">
        <div className="mx-auto max-w-[1240px] px-6">
          <div className="overflow-hidden rounded-3xl border border-slate-200 bg-brand-navy shadow-floating">
            <div className="grid grid-cols-1 lg:grid-cols-2">
              <div className="flex flex-col justify-center p-7 text-white sm:p-10 lg:p-12">
                <h2 className="font-serif-editorial text-[30px] font-normal leading-tight tracking-tight sm:text-[36px]">
                  Lihat rumah sakit dalam konteks wilayahnya.
                </h2>
                <p className="mt-4 max-w-md text-sm leading-relaxed text-slate-300">
                  Peta interaktif menampilkan sebaran fasilitas berdasarkan kelas, dilengkapi rute perjalanan
                  dari lokasi Anda melalui OpenStreetMap.
                </p>
                <div className="mt-6 flex flex-wrap gap-2.5">
                  <Link
                    to="/peta"
                    className="inline-flex items-center gap-1.5 rounded-full bg-white px-5 py-2.5 text-xs font-bold text-brand-navy transition hover:bg-emerald-50"
                  >
                    <span className="material-symbols-outlined text-[16px]">explore</span>
                    Jelajahi peta
                  </Link>
                  <Link
                    to="/pencarian"
                    className="inline-flex items-center gap-1.5 rounded-full border border-white/25 px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-white/10"
                  >
                    Cari berdasarkan wilayah
                  </Link>
                </div>
              </div>
              <div className="relative min-h-[320px] border-t border-white/10 lg:min-h-[430px] lg:border-l lg:border-t-0">
                <LeafletMap
                  hospitals={hospitals}
                  fit
                  showZoom={false}
                  className="absolute inset-0"
                />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-white py-16">
        <div className="mx-auto flex max-w-[1080px] flex-col items-center justify-between gap-6 rounded-3xl border border-slate-200 bg-[#FAFAF9] px-7 py-9 text-center sm:px-10 lg:flex-row lg:text-left">
          <div>
            <h2 className="font-serif-editorial text-[28px] font-normal leading-tight text-brand-navy sm:text-[32px]">
              Mulai dari kebutuhan Anda hari ini.
            </h2>
            <p className="mt-2 max-w-xl text-sm leading-relaxed text-slate-500">
              Cari fasilitas, bandingkan layanan, lalu buka rute perjalanan. Semua dalam satu direktori
              semantik.
            </p>
          </div>
          <div className="flex shrink-0 flex-wrap justify-center gap-2.5">
            <Link
              to="/pencarian"
              className="inline-flex items-center gap-1.5 rounded-full bg-brand-navy px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-blue"
            >
              Mulai pencarian
              <span className="material-symbols-outlined text-[17px]">arrow_forward</span>
            </Link>
            <Link
              to="/peta"
              className="inline-flex items-center gap-1.5 rounded-full border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Lihat peta
            </Link>
          </div>
        </div>
      </section>

      <EditorialFooter />
    </div>
  );
}
