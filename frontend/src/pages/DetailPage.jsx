import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { createPortal } from 'react-dom';
import { getAllHospitals } from '../api';
import { FACILITY_ICON, KELAS_DESCRIPTION, SERVICE_META } from '../constants';
import { useApp } from '../context/AppContext';
import {
  cn,
  directionsUrl,
  emailHref,
  mapsSearchUrl,
  openStreetMapUrl,
  telHref,
  websiteHref,
} from '../utils';
import SiteHeader from '../components/SiteHeader';
import LeafletMap from '../components/LeafletMap';
import BookingForm from '../components/BookingForm';
import { MinimalFooter } from '../components/Footer';

const TABS = [
  { id: 'profil', label: 'Profil', icon: 'clinical_notes' },
  { id: 'fasilitas', label: 'Layanan & Fasilitas', icon: 'stethoscope' },
  { id: 'booking', label: 'Booking Simulasi', icon: 'bed' },
];

function Gallery({ hospital }) {
  const photos = useMemo(
    () => [...new Set([...(hospital.galeri || []), hospital.foto].filter(Boolean))],
    [hospital],
  );
  const [lightbox, setLightbox] = useState(null);

  useEffect(() => {
    if (lightbox == null) return undefined;
    const onKeyDown = (event) => {
      if (event.key === 'Escape') setLightbox(null);
      if (event.key === 'ArrowRight') setLightbox((current) => (current + 1) % photos.length);
      if (event.key === 'ArrowLeft') setLightbox((current) => (current - 1 + photos.length) % photos.length);
    };
    document.addEventListener('keydown', onKeyDown);
    return () => document.removeEventListener('keydown', onKeyDown);
  }, [lightbox, photos.length]);

  if (!photos.length) {
    return (
      <div className="flex h-64 items-center justify-center rounded-2xl border border-slate-200 bg-slate-100 text-slate-400">
        <span className="material-symbols-outlined text-[48px]">image_not_supported</span>
      </div>
    );
  }

  return (
    <>
      {photos.length === 1 ? (
        <div className="overflow-hidden rounded-2xl md:h-[440px]">
          <button
            type="button"
            onClick={() => setLightbox(0)}
            className="group relative h-64 w-full overflow-hidden md:h-full"
          >
            <img
              src={photos[0]}
              alt={`${hospital.nama} — foto utama`}
              className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-[1.01]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/30 to-transparent opacity-0 transition group-hover:opacity-100" />
            <span className="absolute bottom-3 right-3 inline-flex items-center gap-1 rounded-lg border border-white/40 bg-white/90 px-2.5 py-1.5 text-[11px] font-semibold text-slate-800 opacity-0 shadow-sm backdrop-blur transition group-hover:opacity-100">
              <span className="material-symbols-outlined text-[15px]">zoom_in</span>
              Perbesar
            </span>
          </button>
        </div>
      ) : photos.length === 2 ? (
        <div className="grid grid-cols-1 gap-2 overflow-hidden rounded-2xl md:h-[440px] md:grid-cols-2 md:gap-2.5">
          {photos.slice(0, 2).map((src, index) => (
            <button
              key={index}
              type="button"
              onClick={() => setLightbox(index)}
              className="group relative h-64 overflow-hidden md:h-full"
            >
              <img
                src={src}
                alt={`${hospital.nama} — foto ${index + 1}`}
                className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-[1.015]"
              />
              <div className="absolute inset-0 bg-gradient-to-t from-slate-950/30 to-transparent opacity-0 transition group-hover:opacity-100" />
              <span className="absolute bottom-3 right-3 inline-flex items-center gap-1 rounded-lg border border-white/40 bg-white/90 px-2.5 py-1.5 text-[11px] font-semibold text-slate-800 opacity-0 shadow-sm backdrop-blur transition group-hover:opacity-100">
                <span className="material-symbols-outlined text-[15px]">zoom_in</span>
                Perbesar
              </span>
            </button>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-2 overflow-hidden rounded-2xl md:h-[440px] md:grid-cols-12 md:gap-2.5">
          <button
            type="button"
            onClick={() => setLightbox(0)}
            className="group relative h-64 overflow-hidden md:col-span-7 md:h-full"
          >
            <img
              src={photos[0]}
              alt={`${hospital.nama} — foto utama`}
              className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-[1.015]"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/30 to-transparent opacity-0 transition group-hover:opacity-100" />
            <span className="absolute bottom-3 right-3 inline-flex items-center gap-1 rounded-lg border border-white/40 bg-white/90 px-2.5 py-1.5 text-[11px] font-semibold text-slate-800 opacity-0 shadow-sm backdrop-blur transition group-hover:opacity-100">
              <span className="material-symbols-outlined text-[15px]">zoom_in</span>
              Perbesar
            </span>
          </button>

          <div className="grid h-40 grid-cols-2 gap-2 md:col-span-5 md:h-full md:grid-cols-1 md:gap-2.5">
            {[1, 2].map((index) => {
              const src = photos[index];
              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => setLightbox(index)}
                  className="group relative h-full overflow-hidden"
                >
                  <img
                    src={src}
                    alt={`${hospital.nama} — foto ${index + 1}`}
                    loading="lazy"
                    className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-[1.015]"
                  />
                  {index === 2 && photos.length > 3 ? (
                    <span className="absolute bottom-3 right-3 inline-flex items-center gap-1.5 rounded-lg border border-slate-200/60 bg-white/95 px-3 py-1.5 text-[11px] font-semibold text-slate-900 shadow-sm backdrop-blur">
                      <span className="material-symbols-outlined text-[15px]">grid_view</span>
                      Lihat semua {photos.length} foto
                    </span>
                  ) : null}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {lightbox != null
        ? createPortal(
            <div
              className="fixed inset-0 z-[95] flex animate-fade-in flex-col bg-slate-950/95"
              role="dialog"
              aria-modal="true"
              aria-label="Galeri foto rumah sakit"
              onMouseDown={(event) => {
                if (event.target === event.currentTarget) setLightbox(null);
              }}
            >
              <div className="flex items-center justify-between px-4 py-3 text-white">
                <p className="text-sm font-semibold">{hospital.nama}</p>
                <button
                  type="button"
                  onClick={() => setLightbox(null)}
                  className="flex h-9 w-9 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20"
                  aria-label="Tutup galeri"
                >
                  <span className="material-symbols-outlined text-[20px]">close</span>
                </button>
              </div>
              <div className="relative flex flex-1 items-center justify-center overflow-hidden p-4">
                <img
                  src={photos[lightbox]}
                  alt={`${hospital.nama} — foto ${lightbox + 1}`}
                  className="max-h-full max-w-full rounded-lg object-contain"
                />
                {photos.length > 1 ? (
                  <>
                    <button
                      type="button"
                      onClick={() =>
                        setLightbox((current) => (current - 1 + photos.length) % photos.length)
                      }
                      className="absolute left-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/15 text-white backdrop-blur transition hover:bg-white/25"
                      aria-label="Foto sebelumnya"
                    >
                      <span className="material-symbols-outlined">chevron_left</span>
                    </button>
                    <button
                      type="button"
                      onClick={() => setLightbox((current) => (current + 1) % photos.length)}
                      className="absolute right-3 flex h-10 w-10 items-center justify-center rounded-full bg-white/15 text-white backdrop-blur transition hover:bg-white/25"
                      aria-label="Foto berikutnya"
                    >
                      <span className="material-symbols-outlined">chevron_right</span>
                    </button>
                  </>
                ) : null}
              </div>
              <p className="pb-4 text-center text-xs text-white/70">
                {lightbox + 1} / {photos.length}
              </p>
            </div>,
            document.body,
          )
        : null}
    </>
  );
}

function InfoRow({ icon, label, children }) {
  return (
    <div className="flex items-start gap-3">
      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-brand-blue">
        <span className="material-symbols-outlined text-[19px]">{icon}</span>
      </span>
      <div className="min-w-0">
        <p className="text-[10.5px] font-semibold uppercase tracking-wide text-slate-400">{label}</p>
        <div className="mt-0.5 text-sm font-medium leading-snug text-slate-800">{children}</div>
      </div>
    </div>
  );
}

export default function DetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { toggleFavorite, isFavorite, toast } = useApp();
  const [hospital, setHospital] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState('profil');

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError('');
    setHospital(null);
    setTab('profil');

    getAllHospitals()
      .then((items) => {
        if (cancelled) return;
        const found = items.find((item) => item.id === id);
        if (found) setHospital(found);
        else setError('Rumah sakit tidak ditemukan.');
      })
      .catch((err) => {
        if (!cancelled) setError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <SiteHeader />
        <div className="mx-auto max-w-[1280px] px-4 py-10 sm:px-6 lg:px-8">
          <div className="h-9 w-2/3 animate-pulse rounded bg-slate-100" />
          <div className="mt-3 h-4 w-1/2 animate-pulse rounded bg-slate-100" />
          <div className="mt-7 h-[440px] animate-pulse rounded-2xl bg-slate-100" />
          <div className="mt-10 grid gap-10 lg:grid-cols-12">
            <div className="space-y-3 lg:col-span-8">
              <div className="h-7 w-1/2 animate-pulse rounded bg-slate-100" />
              <div className="h-4 w-full animate-pulse rounded bg-slate-100" />
              <div className="h-4 w-5/6 animate-pulse rounded bg-slate-100" />
            </div>
            <div className="h-72 animate-pulse rounded-2xl bg-slate-100 lg:col-span-4" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !hospital) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50">
        <SiteHeader />
        <div className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center px-5 py-20 text-center">
          <span className="material-symbols-outlined text-[54px] text-slate-300">domain_disabled</span>
          <h1 className="mt-3 font-heading text-2xl font-bold text-slate-900">
            Profil tidak dapat ditampilkan
          </h1>
          <p className="mt-2 text-sm text-slate-500">{error || 'Rumah sakit tidak ditemukan.'}</p>
          <div className="mt-6 flex gap-2">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="rounded-full border border-slate-300 bg-white px-5 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Kembali
            </button>
            <Link
              to="/pencarian"
              className="rounded-full bg-brand-navy px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-brand-blue"
            >
              Cari rumah sakit
            </Link>
          </div>
        </div>
        <MinimalFooter />
      </div>
    );
  }

  const layanan = hospital.layanan || [];
  const fasilitas = hospital.fasilitas || [];
  const phone = telHref(hospital.telepon);
  const web = websiteHref(hospital.website);
  const emailLink = emailHref(hospital.email);
  const hasEmergency = [...layanan, ...fasilitas].some((item) => /igd|ugd|gawat darurat|ambulans/i.test(item));
  const hasICU = fasilitas.some((item) => /icu|intensive/i.test(item));
  const saved = isFavorite(hospital.id);
  const featuredServices = layanan.slice(0, 6);

  const share = async () => {
    const url = window.location.href;
    try {
      if (navigator.share) {
        await navigator.share({ title: hospital.nama, text: `Profil ${hospital.nama} di CariSehat`, url });
      } else {
        await navigator.clipboard.writeText(url);
        toast('Tautan profil disalin.', 'success');
      }
    } catch {
      /* user cancelled share */
    }
  };

  return (
    <div className="min-h-screen bg-white">
      <SiteHeader active="direktori" initialQuery="" />

      <main className="mx-auto max-w-[1280px] px-4 pb-16 pt-5 sm:px-6 lg:px-8">
        <nav className="mb-4 flex items-center gap-1 text-[11px] text-slate-500" aria-label="Breadcrumb">
          <Link to="/" className="hover:text-brand-blue">
            Beranda
          </Link>
          <span className="material-symbols-outlined text-[14px] text-slate-300">chevron_right</span>
          <Link to="/pencarian" className="hover:text-brand-blue">
            Direktori
          </Link>
          <span className="material-symbols-outlined text-[14px] text-slate-300">chevron_right</span>
          <span className="truncate font-medium text-slate-700">{hospital.nama}</span>
        </nav>

        {/* Title */}
        <section className="flex flex-col gap-3 pb-6">
          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-1.5">
                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10.5px] font-bold text-slate-700">
                  Kelas {hospital.kelas || '—'}
                </span>
                <span className="rounded-full bg-blue-50 px-2.5 py-1 text-[10.5px] font-bold text-brand-blue">
                  RS {hospital.jenis || '—'}
                </span>
                {hospital.bpjs ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[10.5px] font-bold text-emerald-700">
                    <span className="material-symbols-outlined text-[13px]">check_circle</span>
                    Menerima BPJS
                  </span>
                ) : (
                  <span className="rounded-full bg-amber-50 px-2.5 py-1 text-[10.5px] font-bold text-amber-700">
                    Konfirmasi BPJS
                  </span>
                )}
                {hasEmergency ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-rose-50 px-2.5 py-1 text-[10.5px] font-bold text-rose-700">
                    <span className="material-symbols-outlined text-[13px]">emergency</span>
                    IGD tercatat
                  </span>
                ) : null}
              </div>

              <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-[#0F172A] sm:text-4xl lg:text-[42px]">
                {hospital.nama}
              </h1>

              <div className="mt-2 flex flex-wrap items-center gap-x-2.5 gap-y-1.5 text-sm text-slate-600">
                <span className="font-medium text-slate-700">
                  {KELAS_DESCRIPTION[hospital.kelas] || 'Klasifikasi rumah sakit'}
                </span>
                <span className="font-light text-slate-300">•</span>
                <span className="inline-flex items-center gap-1 text-slate-600">
                  <span className="material-symbols-outlined text-[16px] text-brand-blue">location_on</span>
                  {hospital.kabkota || 'Sumatera Utara'}
                </span>
                <span className="hidden font-light text-slate-300 sm:inline">•</span>
                <span className="hidden max-w-md truncate text-slate-500 sm:inline" title={hospital.alamat}>
                  {hospital.alamat}
                </span>
              </div>
            </div>

            <div className="flex shrink-0 items-center gap-2 self-start md:self-auto">
              <button
                type="button"
                onClick={share}
                className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50 hover:text-slate-950"
              >
                <span className="material-symbols-outlined text-[19px]">share</span>
                <span className="underline">Bagikan</span>
              </button>
              <button
                type="button"
                onClick={() => toggleFavorite(hospital.id)}
                className={cn(
                  'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition hover:bg-slate-50',
                  saved ? 'text-rose-600' : 'text-slate-700 hover:text-slate-950',
                )}
              >
                <span
                  className={cn('material-symbols-outlined text-[19px]', saved && 'material-symbols-filled')}
                >
                  favorite
                </span>
                <span className="underline">{saved ? 'Tersimpan' : 'Simpan'}</span>
              </button>
            </div>
          </div>
        </section>

        <Gallery hospital={hospital} />

        {/* Two column */}
        <section className="mt-9 grid grid-cols-1 items-start gap-9 lg:mt-11 lg:grid-cols-12 lg:gap-12">
          <div className="lg:col-span-8">
            {/* Tabs */}
            <div className="sticky top-16 z-20 -mx-4 mb-7 overflow-x-auto border-b border-slate-200 bg-white/95 px-4 backdrop-blur sm:mx-0 sm:px-0">
              <div className="flex min-w-max gap-1">
                {TABS.map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setTab(item.id)}
                    className={cn(
                      'inline-flex items-center gap-1.5 border-b-2 px-3.5 py-3 text-[12.5px] font-semibold transition',
                      tab === item.id
                        ? 'border-brand-navy text-brand-navy'
                        : 'border-transparent text-slate-500 hover:text-slate-800',
                    )}
                  >
                    <span className="material-symbols-outlined text-[17px]">{item.icon}</span>
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {tab === 'profil' ? (
              <div className="animate-fade-in space-y-8">
                <div className="space-y-3">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                      Tentang Rumah Sakit
                    </h2>
                    <div className="flex flex-wrap gap-1.5">
                      <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10.5px] font-semibold text-slate-700">
                        {layanan.length} layanan
                      </span>
                      <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10.5px] font-semibold text-emerald-700">
                        {fasilitas.length} fasilitas
                      </span>
                    </div>
                  </div>
                  <p className="max-w-3xl text-[14.5px] leading-relaxed text-slate-600">
                    <strong className="font-semibold text-slate-800">{hospital.nama}</strong> adalah rumah
                    sakit {String(hospital.jenis || '').toLowerCase()} kelas{' '}
                    {hospital.kelas || 'belum terklasifikasi'} yang berlokasi di{' '}
                    {hospital.kabkota || 'Sumatera Utara'}. Profil ini disusun dari katalog semantik
                    CariSehat dan mencakup layanan, fasilitas penunjang, kontak, serta koordinat
                    geospasial.
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-3">
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <span className="material-symbols-outlined text-[22px] text-brand-blue">domain</span>
                    <p className="mt-2 text-sm font-bold text-slate-900">
                      Kelas {hospital.kelas || '—'} · RS {hospital.jenis || '—'}
                    </p>
                    <p className="mt-0.5 text-[11px] leading-snug text-slate-500">
                      {KELAS_DESCRIPTION[hospital.kelas] || 'Klasifikasi sesuai data katalog'}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <span className="material-symbols-outlined text-[22px] text-emerald-600">
                      verified_user
                    </span>
                    <p className="mt-2 text-sm font-bold text-slate-900">
                      {hospital.bpjs ? 'Menerima BPJS' : 'Konfirmasi BPJS'}
                    </p>
                    <p className="mt-0.5 text-[11px] leading-snug text-slate-500">
                      {hospital.bpjs
                        ? 'Tercatat menerima pasien BPJS Kesehatan.'
                        : 'Status BPJS belum tercatat pada katalog.'}
                    </p>
                  </div>
                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                    <span className="material-symbols-outlined text-[22px] text-brand-blue">bed</span>
                    <p className="mt-2 text-sm font-bold text-slate-900">
                      {hasICU ? 'Fasilitas intensif' : hasEmergency ? 'IGD tercatat' : 'Fasilitas dasar'}
                    </p>
                    <p className="mt-0.5 text-[11px] leading-snug text-slate-500">
                      {hasICU
                        ? 'Data fasilitas mencantumkan ICU/perawatan intensif.'
                        : hasEmergency
                          ? 'Data layanan mencantumkan IGD/UGD atau ambulans.'
                          : 'Rincian fasilitas mengikuti data katalog.'}
                    </p>
                  </div>
                </div>

                <div className="border-t border-slate-100" />

                <div className="space-y-5">
                  <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                    <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                      Spesialisasi &amp; Layanan Unggulan
                    </h2>
                    <button
                      type="button"
                      onClick={() => setTab('fasilitas')}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-brand-blue hover:underline"
                    >
                      Semua layanan
                      <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
                    </button>
                  </div>

                  {featuredServices.length ? (
                    <div className="grid grid-cols-1 gap-3.5 md:grid-cols-2">
                      {featuredServices.map((service) => {
                        const meta = SERVICE_META[service] || { icon: 'medical_services' };
                        return (
                          <div
                            key={service}
                            className="flex items-start gap-3 rounded-xl border border-slate-200 bg-white p-4 transition hover:border-slate-300"
                          >
                            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-brand-blue">
                              <span className="material-symbols-outlined text-[20px]">{meta.icon}</span>
                            </span>
                            <div>
                              <h4 className="text-sm font-semibold leading-snug text-slate-900">
                                {service}
                              </h4>
                              <p className="mt-0.5 text-[11px] text-slate-500">
                                Layanan tercatat pada katalog semantik
                              </p>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                      Data rincian layanan belum tersedia untuk fasilitas ini.
                    </p>
                  )}
                </div>

                <div className="border-t border-slate-100" />

                <div className="space-y-5">
                  <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">
                    <div>
                      <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                        Lokasi Spesifik &amp; Akses
                      </h2>
                      <p className="mt-1 flex items-start gap-1.5 text-xs text-slate-500 sm:text-sm">
                        <span className="material-symbols-outlined mt-0.5 text-[16px] text-brand-blue">
                          location_on
                        </span>
                        <span>{hospital.alamat || 'Alamat belum tersedia'}</span>
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => navigate(`/peta?rs=${encodeURIComponent(hospital.id)}&route=1`)}
                      className="inline-flex w-fit items-center gap-1.5 rounded-full border border-slate-300 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
                    >
                      <span className="material-symbols-outlined text-[16px]">directions</span>
                      Petunjuk rute
                    </button>
                  </div>

                  <div className="relative h-72 overflow-hidden rounded-2xl border border-slate-200 shadow-sm lg:h-80">
                    {hospital.lat != null && hospital.lon != null ? (
                      <LeafletMap
                        hospitals={[hospital]}
                        selectedId={hospital.id}
                        fit={false}
                        className="h-full"
                      />
                    ) : (
                      <div className="map-grid-pattern flex h-full flex-col items-center justify-center text-slate-400">
                        <span className="material-symbols-outlined text-[42px]">location_off</span>
                        <p className="mt-2 text-xs font-medium">Koordinat peta belum tersedia.</p>
                      </div>
                    )}
                    {hospital.lat != null ? (
                      <div className="pointer-events-none absolute bottom-3 left-3 right-3 z-[500] flex items-center gap-2 rounded-lg border border-slate-800 bg-slate-950/90 px-3 py-1.5 font-mono text-[10.5px] text-slate-200 shadow-sm backdrop-blur sm:right-auto">
                        <span className="material-symbols-outlined text-[14px] text-emerald-400">
                          my_location
                        </span>
                        <span className="truncate">
                          {Number(hospital.lat).toFixed(6)}, {Number(hospital.lon).toFixed(6)}
                        </span>
                      </div>
                    ) : null}
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <a
                      href={directionsUrl(hospital)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5 transition hover:border-brand-blue/30 hover:bg-blue-50/40"
                    >
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-brand-blue">
                        <span className="material-symbols-outlined text-[20px]">directions_car</span>
                      </span>
                      <span>
                        <span className="block text-sm font-bold text-slate-900">Google Maps</span>
                        <span className="block text-[11px] leading-snug text-slate-500">
                          Navigasi kendaraan pribadi
                        </span>
                      </span>
                    </a>
                    <a
                      href={openStreetMapUrl(hospital) || mapsSearchUrl(hospital)}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5 transition hover:border-brand-blue/30 hover:bg-blue-50/40"
                    >
                      <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">
                        <span className="material-symbols-outlined text-[20px]">map</span>
                      </span>
                      <span>
                        <span className="block text-sm font-bold text-slate-900">OpenStreetMap</span>
                        <span className="block text-[11px] leading-snug text-slate-500">
                          Lihat titik pada peta terbuka
                        </span>
                      </span>
                    </a>
                  </div>

                  <div className="rounded-xl border border-slate-200 bg-slate-50 p-3.5 text-[11.5px] leading-relaxed text-slate-500">
                    <span className="mb-1 flex items-center gap-1 font-bold text-slate-700">
                      <span className="material-symbols-outlined text-[15px]">info</span>
                      Catatan akses
                    </span>
                    Informasi jadwal poli, ketersediaan kamar, dan akses darurat dapat berubah. Konfirmasikan
                    langsung kepada rumah sakit sebelum berkunjung.
                  </div>
                </div>
              </div>
            ) : null}

            {tab === 'fasilitas' ? (
              <div className="animate-fade-in space-y-7">
                <div>
                  <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                    Layanan Medis
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    {layanan.length} layanan tercatat pada katalog semantik.
                  </p>
                  {layanan.length ? (
                    <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                      {layanan.map((service) => {
                        const meta = SERVICE_META[service] || { icon: 'medical_services' };
                        return (
                          <div
                            key={service}
                            className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5"
                          >
                            <span className="material-symbols-outlined text-[19px] text-brand-blue">
                              {meta.icon}
                            </span>
                            <span className="text-[12.5px] font-medium text-slate-700">{service}</span>
                          </div>
                        );
                      })}
                    </div>
                  ) : (
                    <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                      Data layanan belum tersedia.
                    </p>
                  )}
                </div>

                <div className="border-t border-slate-100" />

                <div>
                  <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
                    Fasilitas Penunjang
                  </h2>
                  <p className="mt-1 text-sm text-slate-500">
                    {fasilitas.length} fasilitas tercatat pada katalog semantik.
                  </p>
                  {fasilitas.length ? (
                    <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">
                      {fasilitas.map((facility) => (
                        <div
                          key={facility}
                          className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5"
                        >
                          <span className="material-symbols-outlined text-[19px] text-emerald-600">
                            {FACILITY_ICON[facility] || 'check_circle'}
                          </span>
                          <span className="text-[12.5px] font-medium text-slate-700">{facility}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">
                      Data fasilitas belum tersedia.
                    </p>
                  )}
                </div>

                <div className="rounded-xl border border-blue-100 bg-blue-50/60 p-4 text-[11.5px] leading-relaxed text-slate-600">
                  <strong className="text-slate-800">Catatan data.</strong> Layanan dan fasilitas dapat
                  terbatas atau diturunkan dari jenis rumah sakit. Konfirmasikan ketersediaan terkini secara
                  langsung kepada rumah sakit.
                </div>
              </div>
            ) : null}

            {tab === 'booking' ? (
              <div className="animate-fade-in">
                <h2 className="mb-1 text-2xl font-bold tracking-tight text-[#0F172A]">
                  Reservasi Kamar Rawat Inap
                </h2>
                <p className="mb-5 text-sm text-slate-500">
                  Demo interaktif Tugas Besar MSBD berbasis PostgreSQL.
                </p>
                <BookingForm hospital={hospital} />
              </div>
            ) : null}
          </div>

          {/* Sidebar */}
          <aside className="lg:col-span-4">
            <div className="sticky top-24 space-y-4">
              <section className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm">
                <div className="flex flex-col gap-1.5">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <span className="relative flex h-2.5 w-2.5">
                        {hasEmergency ? (
                          <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                        ) : null}
                        <span
                          className={cn(
                            'relative inline-flex h-2.5 w-2.5 rounded-full',
                            hasEmergency ? 'bg-emerald-500' : 'bg-amber-500',
                          )}
                        />
                      </span>
                      <span className="text-sm font-bold text-slate-900">
                        {hasEmergency ? 'Layanan IGD tercatat' : 'Jam operasional'}
                      </span>
                    </div>
                    <span
                      className={cn(
                        'rounded-full px-2 py-0.5 text-[10px] font-semibold',
                        hasEmergency ? 'bg-emerald-50 text-emerald-700' : 'bg-amber-50 text-amber-700',
                      )}
                    >
                      {hasEmergency ? 'Siaga' : 'Konfirmasi'}
                    </span>
                  </div>
                  <p className="mt-1 flex items-center gap-1 text-[11px] text-slate-500">
                    <span className="material-symbols-outlined text-[14px] text-slate-400">location_on</span>
                    {hospital.kabkota || 'Sumatera Utara'}
                  </p>
                </div>

                <div className="my-4 border-t border-slate-100" />

                <div className="grid grid-cols-2 gap-2.5 text-center">
                  <div className="rounded-xl bg-slate-50 p-2.5">
                    <p className="text-[10px] font-medium text-slate-500">Kelas</p>
                    <p className="mt-0.5 text-base font-extrabold text-slate-900">{hospital.kelas || '—'}</p>
                  </div>
                  <div className="rounded-xl bg-slate-50 p-2.5">
                    <p className="text-[10px] font-medium text-slate-500">Jenis</p>
                    <p className="mt-0.5 text-sm font-extrabold text-slate-900">{hospital.jenis || '—'}</p>
                  </div>
                </div>

                <div className="mt-4 flex flex-col gap-2.5">
                  <button
                    type="button"
                    onClick={() => navigate(`/peta?rs=${encodeURIComponent(hospital.id)}&route=1`)}
                    disabled={hospital.lat == null || hospital.lon == null}
                    className="flex w-full items-center justify-center gap-2 rounded-full bg-brand-navy px-6 py-3 text-sm font-semibold text-white transition hover:bg-brand-blue disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    <span className="material-symbols-outlined text-[19px]">directions</span>
                    Petunjuk Rute
                  </button>
                  <button
                    type="button"
                    onClick={() => setTab('booking')}
                    className="flex w-full items-center justify-center gap-2 rounded-full border border-slate-300 bg-white px-6 py-2.5 text-sm font-semibold text-slate-800 transition hover:border-slate-800 hover:bg-slate-50"
                  >
                    <span className="material-symbols-outlined text-[18px]">bed</span>
                    Pesan kamar (simulasi)
                  </button>
                  {web ? (
                    <a
                      href={web}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-brand-blue"
                    >
                      <span className="material-symbols-outlined text-[16px]">language</span>
                      Situs resmi
                    </a>
                  ) : null}
                  {emailLink ? (
                    <a
                      href={emailLink}
                      className="flex w-full items-center justify-center gap-2 rounded-full border border-slate-200 bg-white px-6 py-2.5 text-xs font-semibold text-slate-600 transition hover:bg-slate-50 hover:text-brand-blue"
                    >
                      <span className="material-symbols-outlined text-[16px]">mail</span>
                      Kirim Email
                    </a>
                  ) : null}
                </div>

                {phone ? (
                  <div className="pt-4 text-center">
                    <a
                      href={phone}
                      className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 transition hover:text-slate-900"
                    >
                      <span className="material-symbols-outlined text-[16px] text-rose-600">call</span>
                      Hubungi: <strong className="text-slate-900">{hospital.telepon}</strong>
                    </a>
                  </div>
                ) : null}

                <div className="mt-4 flex items-center justify-center gap-1.5 border-t border-slate-100 pt-3 text-[10px] text-slate-400">
                  <span className="material-symbols-outlined text-[14px]">verified</span>
                  Data terverifikasi katalog semantik
                </div>
              </section>

              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                <h3 className="text-sm font-bold text-slate-900">Informasi Kontak</h3>
                <div className="mt-4 space-y-3.5">
                  <InfoRow icon="location_on" label="Alamat">
                    <span className="text-[12.5px] leading-relaxed">
                      {hospital.alamat || 'Alamat belum tersedia'}
                    </span>
                  </InfoRow>
                  <InfoRow icon="call" label="Telepon">
                    {phone ? (
                      <a href={phone} className="text-[12.5px] font-medium text-brand-blue hover:underline">
                        {hospital.telepon}
                      </a>
                    ) : (
                      <span className="text-[12.5px] text-slate-400">Belum tersedia</span>
                    )}
                  </InfoRow>
                  <InfoRow icon="mail" label="Email">
                    {emailLink ? (
                      <a href={emailLink} className="text-[12.5px] font-medium text-brand-blue hover:underline break-all">
                        {hospital.email}
                      </a>
                    ) : (
                      <span className="text-[12.5px] text-slate-400">Belum tersedia</span>
                    )}
                  </InfoRow>
                  <InfoRow icon="language" label="Website">
                    {web ? (
                      <a
                        href={web}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-[12.5px] font-medium text-brand-blue hover:underline break-all"
                      >
                        <span>{hospital.website.replace(/^https?:\/\//i, '').replace(/\/$/, '')}</span>
                        <span className="material-symbols-outlined text-[13px]">open_in_new</span>
                      </a>
                    ) : (
                      <span className="text-[12.5px] text-slate-400">Belum tersedia</span>
                    )}
                  </InfoRow>
                  <InfoRow icon="my_location" label="Koordinat">
                    <span className="text-[12px]">
                      {hospital.lat != null
                        ? `${Number(hospital.lat).toFixed(5)}, ${Number(hospital.lon).toFixed(5)}`
                        : 'Belum tersedia'}
                    </span>
                  </InfoRow>
                </div>
              </section>
            </div>
          </aside>
        </section>
      </main>

      <MinimalFooter />
    </div>
  );
}
