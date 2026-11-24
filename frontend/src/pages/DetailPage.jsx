import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';

import { createPortal } from 'react-dom';

import {

  getAllHospitals,

  getHospitalAlternatives,

  getHospitalOperationalHours,

} from '../api';

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

import PoliklinikSection from '../components/PoliklinikSection';

import UlasanSection from '../components/UlasanSection';

import KnowledgeGraphModal from '../components/KnowledgeGraphModal';

import { MinimalFooter } from '../components/Footer';



const QUICK_SECTIONS = [

  { id: 'sec-profil', label: 'Profil & IGD', icon: 'clinical_notes' },

  { id: 'sec-jam', label: 'Jam 7 Hari', icon: 'schedule' },

  { id: 'sec-poliklinik', label: 'Poliklinik', icon: 'medical_information' },

  { id: 'sec-spesialisasi', label: 'Layanan & Fasilitas', icon: 'stethoscope' },

  { id: 'sec-alternatif', label: 'RS Alternatif', icon: 'compare_arrows' },

  { id: 'sec-ulasan', label: 'Ulasan', icon: 'reviews' },

  { id: 'sec-booking', label: 'Booking Kamar', icon: 'bed' },

  { id: 'sec-lokasi', label: 'Lokasi & Peta', icon: 'location_on' },

];



const HARI_URUT = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'];



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

      <div className="grid grid-cols-1 gap-2.5 overflow-hidden rounded-2xl md:h-[340px] md:grid-cols-3">

        {photos.slice(0, 3).map((src, index) => (

          <button

            key={index}

            type="button"

            onClick={() => setLightbox(index)}

            className="group relative h-56 overflow-hidden md:h-full"

          >

            <img

              src={src}

              alt={`${hospital.nama} — foto ${index + 1}`}

              loading="lazy"

              className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-[1.02]"

            />

            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/35 to-transparent opacity-0 transition group-hover:opacity-100" />

            <span className="absolute bottom-3 right-3 inline-flex items-center gap-1 rounded-lg border border-white/40 bg-white/95 px-2.5 py-1 text-[11px] font-semibold text-slate-800 shadow-sm backdrop-blur">

              <span className="material-symbols-outlined text-[14px]">zoom_in</span>

              {index === 2 && photos.length > 3 ? `Semua (${photos.length})` : 'Perbesar'}

            </span>

          </button>

        ))}

      </div>



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

      <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-toba-mist text-toba">

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

  const {

    toggleFavorite,

    isFavorite,

    toggleCompare,

    isCompared,

    setCompareModalOpen,

    toast,

  } = useApp();



  const [hospital, setHospital] = useState(null);

  const [hoursData, setHoursData] = useState(null);

  const [alternatives, setAlternatives] = useState([]);

  const [loading, setLoading] = useState(true);

  const [error, setError] = useState('');

  const [activeSec, setActiveSec] = useState('sec-profil');

  const [kgOpen, setKgOpen] = useState(false);



  useEffect(() => {

    let cancelled = false;

    setLoading(true);

    setError('');

    setHospital(null);

    setHoursData(null);

    setAlternatives([]);

    setActiveSec('sec-profil');



    getAllHospitals()

      .then((items) => {

        if (cancelled) return;

        const found = items.find((item) => item.id === id);

        if (found) {

          setHospital(found);

          getHospitalOperationalHours(found.id)

            .then((h) => !cancelled && setHoursData(h))

            .catch(() => {});

          getHospitalAlternatives(found.id, 4)

            .then((alt) => !cancelled && setAlternatives(alt?.items || alt?.alternatives || []))

            .catch(() => {});

        } else {

          setError('Rumah sakit tidak ditemukan.');

        }

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



  useEffect(() => {

    if (!hospital) return undefined;

    const onScroll = () => {

      for (const sec of QUICK_SECTIONS) {

        const el = document.getElementById(sec.id);

        if (!el) continue;

        const rect = el.getBoundingClientRect();

        if (rect.top <= 170 && rect.bottom >= 120) {

          setActiveSec(sec.id);

          break;

        }

      }

    };

    window.addEventListener('scroll', onScroll, { passive: true });

    return () => window.removeEventListener('scroll', onScroll);

  }, [hospital]);



  const scrollToSection = (sectionId) => {

    setActiveSec(sectionId);

    const el = document.getElementById(sectionId);

    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });

  };



  if (loading) {

    return (

      <div className="min-h-screen bg-white">

        <SiteHeader active="direktori" />

        <div className="mx-auto max-w-[1280px] px-4 py-10 sm:px-6 lg:px-8">

          <div className="h-9 w-2/3 animate-pulse rounded bg-slate-100" />

          <div className="mt-3 h-4 w-1/2 animate-pulse rounded bg-slate-100" />

          <div className="mt-7 h-[340px] animate-pulse rounded-2xl bg-slate-100" />

        </div>

      </div>

    );

  }



  if (error || !hospital) {

    return (

      <div className="flex min-h-screen flex-col bg-slate-50">

        <SiteHeader active="direktori" />

        <div className="mx-auto flex w-full max-w-xl flex-1 flex-col items-center justify-center px-5 py-20 text-center">

          <span className="material-symbols-outlined text-[54px] text-slate-300">domain_disabled</span>

          <h1 className="mt-3 text-2xl font-extrabold text-slate-900">

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

              className="rounded-full bg-toba px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-toba-dark"

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

  const hasEmergency = [...layanan, ...fasilitas].some((item) =>

    /igd|ugd|gawat darurat|ambulans/i.test(item),

  );

  const hasICU = fasilitas.some((item) => /icu|intensive/i.test(item));

  const saved = isFavorite(hospital.id);

  const compared = isCompared(hospital.id);



  const dailySchedule = HARI_URUT.map((hari) => {

    const raw = hoursData?.schedule?.[hari] || hoursData?.days?.[hari] || hoursData?.[hari.toLowerCase()];

    if (typeof raw === 'string') return { hari, jam: raw };

    if (raw && typeof raw === 'object') {

      return {

        hari,

        jam: raw.jam || raw.hours || (raw.open && raw.close ? `${raw.open} – ${raw.close}` : 'Sesuai jadwal poliklinik'),

      };

    }

    return {

      hari,

      jam: hasEmergency ? 'Poliklinik: 08.00 – 14.00 WIB • IGD 24 Jam' : '08.00 – 14.00 WIB (Konfirmasi RS)',

    };

  });



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

      <SiteHeader active="direktori" />



      <main className="mx-auto max-w-[1280px] px-4 pb-16 pt-5 sm:px-6 lg:px-8">

        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">

          <button

            type="button"

            onClick={() => navigate(-1)}

            className="group inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 shadow-sm transition hover:border-toba hover:bg-toba-mist hover:text-toba-dark"

          >

            <span className="material-symbols-outlined text-[16px] transition-transform group-hover:-translate-x-1">

              arrow_back

            </span>

            <span>Kembali</span>

          </button>



          <div className="flex flex-wrap items-center gap-2">

            <button

              type="button"

              onClick={() => setKgOpen(true)}

              className="inline-flex items-center gap-1.5 rounded-full border border-toba/30 bg-toba-mist px-3.5 py-1.5 text-xs font-bold text-toba-dark transition hover:bg-toba-soft"

            >

              <span className="material-symbols-outlined text-[16px]">hub</span>

              Peta Keterkaitan Layanan

            </button>

            <button

              type="button"

              onClick={() => {

                toggleCompare(hospital.id);

                setCompareModalOpen(true);

              }}

              className={cn(

                'inline-flex items-center gap-1.5 rounded-full border px-3.5 py-1.5 text-xs font-bold transition',

                compared

                  ? 'border-toba bg-toba text-white'

                  : 'border-slate-200 bg-white text-slate-700 hover:border-toba hover:text-toba-dark',

              )}

            >

              <span className="material-symbols-outlined text-[16px]">compare</span>

              {compared ? 'Dalam Perbandingan' : 'Bandingkan RS'}

            </button>

          </div>

        </div>



        {/* Title */}

        <section className="flex flex-col gap-3 pb-6">

          <div className="flex flex-col justify-between gap-4 md:flex-row md:items-end">

            <div className="min-w-0">

              <div className="mb-2 flex flex-wrap items-center gap-1.5">

                <span className="rounded-full bg-slate-100 px-2.5 py-1 text-[10.5px] font-bold text-slate-700">

                  Kelas {hospital.kelas || '—'}

                </span>

                <span className="rounded-full bg-toba-mist px-2.5 py-1 text-[10.5px] font-bold text-toba-dark">

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

                    IGD 24 Jam / Tercatat

                  </span>

                ) : null}

              </div>



              <h1 className="text-3xl font-extrabold leading-tight tracking-tight text-slate-900 sm:text-4xl lg:text-[40px]">

                {hospital.nama}

              </h1>



              <div className="mt-2 flex flex-wrap items-center gap-x-2.5 gap-y-1.5 text-sm text-slate-600">

                <span className="font-semibold text-slate-700">

                  {KELAS_DESCRIPTION[hospital.kelas] || 'Klasifikasi rumah sakit'}

                </span>

                <span className="text-slate-300">•</span>

                <span className="inline-flex items-center gap-1 text-slate-600">

                  <span className="material-symbols-outlined text-[16px] text-toba">location_on</span>

                  {hospital.kabkota || 'Sumatera Utara'}

                </span>

                <span className="hidden text-slate-300 sm:inline">•</span>

                <span className="hidden max-w-md truncate text-slate-500 sm:inline" title={hospital.alamat}>

                  {hospital.alamat}

                </span>

              </div>

            </div>



            <div className="flex shrink-0 items-center gap-2 self-start md:self-auto">

              <button

                type="button"

                onClick={share}

                className="inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-slate-700 transition hover:bg-slate-50"

              >

                <span className="material-symbols-outlined text-[19px]">share</span>

                <span className="underline">Bagikan</span>

              </button>

              <button

                type="button"

                onClick={() => toggleFavorite(hospital.id)}

                className={cn(

                  'inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium transition hover:bg-slate-50',

                  saved ? 'text-rose-600' : 'text-slate-700',

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



        {/* Single-Page Smooth-Scroll Layout + Sidebar */}

        <section className="mt-9 grid grid-cols-1 items-start gap-9 lg:mt-11 lg:grid-cols-12 lg:gap-12">

          <div className="space-y-12 lg:col-span-8">

            {/* Sticky Quick-Nav Pills untuk Smooth Scroll */}

            <div className="sticky top-[70px] z-20 -mx-4 overflow-x-auto border-b border-slate-200 bg-white/95 px-4 py-2 backdrop-blur no-scrollbar sm:mx-0 sm:px-0">

              <div className="flex min-w-max gap-1.5">

                {QUICK_SECTIONS.map((item) => (

                  <button

                    key={item.id}

                    type="button"

                    onClick={() => scrollToSection(item.id)}

                    className={cn(

                      'inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-bold transition',

                      activeSec === item.id

                        ? 'bg-toba text-white shadow-sm'

                        : 'bg-slate-100 text-slate-600 hover:bg-toba-mist hover:text-toba-dark',

                    )}

                  >

                    <span className="material-symbols-outlined text-[15px]">{item.icon}</span>

                    {item.label}

                  </button>

                ))}

              </div>

            </div>



            {/* 1. Profil & Blok IGD */}

            <div id="sec-profil" className="scroll-mt-28 space-y-6">

              <div className="flex flex-wrap items-center justify-between gap-2">

                <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">

                  Profil &amp; Instalasi Gawat Darurat (IGD)

                </h2>

                <div className="flex flex-wrap gap-1.5">

                  <span className="rounded-full bg-toba-mist px-2.5 py-1 text-[10.5px] font-bold text-toba-dark">

                    {layanan.length} layanan medis

                  </span>

                  <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10.5px] font-bold text-emerald-700">

                    {fasilitas.length} fasilitas

                  </span>

                </div>

              </div>



              <p className="text-[14.5px] leading-relaxed text-slate-600">

                <strong className="font-semibold text-slate-800">{hospital.nama}</strong> adalah rumah

                sakit {String(hospital.jenis || '').toLowerCase()} kelas{' '}

                {hospital.kelas || 'belum terklasifikasi'} di{' '}

                {hospital.kabkota || 'Sumatera Utara'}. Seluruh profil terhubung dengan katalog semantik

                Informasi profil rumah sakit resmi, jadwal poliklinik, dan ulasan pasien.

              </p>



              {/* Blok IGD Dedicated */}

              <div className="rounded-2xl border border-rose-200/80 bg-rose-50/50 p-4 sm:p-5">

                <div className="flex flex-wrap items-center justify-between gap-2">

                  <div className="flex items-center gap-2.5">

                    <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-600 text-white shadow-sm">

                      <span className="material-symbols-outlined text-[20px]">emergency</span>

                    </span>

                    <div>

                      <h3 className="text-sm font-extrabold text-slate-900">

                        Instalasi Gawat Darurat (IGD)

                      </h3>

                      <p className="text-xs text-slate-600">

                        {hasEmergency

                          ? 'Layanan gawat darurat / ambulans tercatat pada data faskes.'

                          : 'Konfirmasikan kesiagaan IGD 24 jam secara langsung ke pihak rumah sakit.'}

                      </p>

                    </div>

                  </div>

                  <span className="rounded-full bg-white px-3 py-1 text-[11px] font-bold text-rose-700 ring-1 ring-rose-200">

                    {hasEmergency ? 'IGD Tercatat' : 'Perlu Konfirmasi'}

                  </span>

                </div>

              </div>



              <div className="grid gap-3 sm:grid-cols-3">

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">

                  <span className="material-symbols-outlined text-[22px] text-toba">domain</span>

                  <p className="mt-2 text-sm font-bold text-slate-900">

                    Kelas {hospital.kelas || '—'} · RS {hospital.jenis || '—'}

                  </p>

                  <p className="mt-0.5 text-[11px] text-slate-500">

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

                  <p className="mt-0.5 text-[11px] text-slate-500">

                    {hospital.bpjs

                      ? 'Tercatat menerima pasien BPJS Kesehatan.'

                      : 'Status BPJS belum tercatat pada katalog.'}

                  </p>

                </div>

                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">

                  <span className="material-symbols-outlined text-[22px] text-toba">bed</span>

                  <p className="mt-2 text-sm font-bold text-slate-900">

                    {hasICU ? 'Fasilitas intensif' : hasEmergency ? 'IGD tercatat' : 'Fasilitas dasar'}

                  </p>

                  <p className="mt-0.5 text-[11px] text-slate-500">

                    {hasICU

                      ? 'Data fasilitas mencantumkan ICU/perawatan intensif.'

                      : 'Rincian fasilitas mengikuti data katalog.'}

                  </p>

                </div>

              </div>

            </div>



            {/* 2. Jam Operasional 7 Hari */}

            <div id="sec-jam" className="scroll-mt-28 border-t border-slate-100 pt-8 space-y-4">

              <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">

                Jam Operasional (Senin – Minggu)

              </h2>

              <p className="text-sm text-slate-500">

                Jadwal acuan pelayanan unit dan poliklinik harian. Layanan darurat mengikuti kesiagaan IGD.

              </p>

              <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white">

                <div className="divide-y divide-slate-100">

                  {dailySchedule.map((row) => (

                    <div

                      key={row.hari}

                      className="flex flex-col justify-between gap-1 px-4 py-3 text-sm sm:flex-row sm:items-center"

                    >

                      <span className="font-bold text-slate-800">{row.hari}</span>

                      <span className="text-xs font-medium text-slate-600 sm:text-sm">{row.jam}</span>

                    </div>

                  ))}

                </div>

              </div>

            </div>



            {/* 3. Poliklinik & Antrean MSBD */}

            <div id="sec-poliklinik" className="scroll-mt-28 border-t border-slate-100 pt-8">

              <PoliklinikSection hospital={hospital} />

            </div>



            {/* 4. Spesialisasi & Fasilitas 2 Kolom */}

            <div id="sec-spesialisasi" className="scroll-mt-28 border-t border-slate-100 pt-8 space-y-6">

              <div>

                <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">

                  Spesialisasi &amp; Layanan Medis

                </h2>

                <p className="mt-1 text-sm text-slate-500">

                  {layanan.length} layanan tercatat pada katalog semantik.

                </p>

                {layanan.length ? (

                  <ul className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">

                    {layanan.map((service) => {

                      const meta = SERVICE_META[service] || { icon: 'medical_services' };

                      return (

                        <li

                          key={service}

                          className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5"

                        >

                          <span className="material-symbols-outlined text-[19px] text-toba">

                            {meta.icon}

                          </span>

                          <span className="text-[13px] font-medium text-slate-700">{service}</span>

                        </li>

                      );

                    })}

                  </ul>

                ) : (

                  <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">

                    Data layanan belum tersedia.

                  </p>

                )}

              </div>



              <div>

                <h3 className="text-xl font-bold tracking-tight text-slate-900">

                  Fasilitas Penunjang (2 Kolom)

                </h3>

                <p className="mt-1 text-sm text-slate-500">

                  {fasilitas.length} fasilitas tercatat pada katalog.

                </p>

                {fasilitas.length ? (

                  <ul className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">

                    {fasilitas.map((facility) => (

                      <li

                        key={facility}

                        className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2.5"

                      >

                        <span className="material-symbols-outlined text-[19px] text-emerald-600">

                          {FACILITY_ICON[facility] || 'check_circle'}

                        </span>

                        <span className="text-[13px] font-medium text-slate-700">{facility}</span>

                      </li>

                    ))}

                  </ul>

                ) : (

                  <p className="mt-4 rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">

                    Data fasilitas belum tersedia.

                  </p>

                )}

              </div>

            </div>



            {/* 5. RS Alternatif Terdekat & Setara */}

            <div id="sec-alternatif" className="scroll-mt-28 border-t border-slate-100 pt-8 space-y-4">

              <div className="flex items-center justify-between gap-2">

                <div>

                  <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">

                    RS Alternatif Terdekat &amp; Setara

                  </h2>

                  <p className="mt-1 text-sm text-slate-500">

                    Rekomendasi fasilitas setara/terdekat untuk dibuka atau dibandingkan langsung.

                  </p>

                </div>

              </div>



              {alternatives.length > 0 ? (

                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">

                  {alternatives.slice(0, 4).map((alt) => {

                    const altId = alt.id || alt.rs_id;

                    const inCmp = isCompared(altId);

                    return (

                      <div

                        key={altId}

                        className="flex flex-col justify-between rounded-2xl border border-slate-200 bg-white p-4 shadow-card"

                      >

                        <div className="flex gap-3">

                          {alt.foto ? (

                            <img

                              src={alt.foto}

                              alt={alt.nama}

                              loading="lazy"

                              className="h-16 w-16 shrink-0 rounded-xl object-cover bg-slate-100"

                              onError={(e) => {

                                e.currentTarget.style.display = 'none';

                              }}

                            />

                          ) : null}

                          <div className="min-w-0 flex-1">

                            <p className="line-clamp-1 text-sm font-bold text-slate-900">{alt.nama}</p>

                            <p className="mt-0.5 text-xs text-slate-500">

                              Kelas {alt.kelas || '—'} • {alt.kabkota || 'Sumatera Utara'}

                            </p>

                          </div>

                        </div>

                        <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3">

                          <Link

                            to={`/rumah-sakit/${encodeURIComponent(altId)}`}

                            className="flex-1 rounded-full border border-slate-200 px-3 py-1.5 text-center text-xs font-bold text-slate-700 transition hover:border-toba hover:text-toba-dark"

                          >

                            Lihat Detail

                          </Link>

                          <button

                            type="button"

                            onClick={() => toggleCompare(altId)}

                            className={cn(

                              'flex-1 rounded-full px-3 py-1.5 text-xs font-bold transition',

                              inCmp

                                ? 'bg-toba text-white'

                                : 'bg-toba-mist text-toba-dark hover:bg-toba-soft',

                            )}

                          >

                            {inCmp ? 'Dipilih' : 'Bandingkan'}

                          </button>

                        </div>

                      </div>

                    );

                  })}

                </div>

              ) : (

                <p className="rounded-xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-500">

                  Belum ada daftar alternatif tambahan untuk fasilitas ini.

                </p>

              )}

            </div>



            {/* 6. Ulasan Pasien MSBD */}

            <div id="sec-ulasan" className="scroll-mt-28 border-t border-slate-100 pt-8">

              <UlasanSection hospital={hospital} />

            </div>



            {/* 7. Reservasi Kamar Rawat Inap */}

            <div id="sec-booking" className="scroll-mt-28 border-t border-slate-100 pt-8">

              <h2 className="mb-1 text-2xl font-extrabold tracking-tight text-slate-900">

                Reservasi Kamar Rawat Inap

              </h2>

              <p className="mb-5 text-sm text-slate-500">

                Pemesanan kamar rawat inap dan cek ketersediaan ruang secara langsung.

              </p>

              <BookingForm hospital={hospital} />

            </div>



            {/* 8. Lokasi Spesifik & Akses */}

            <div id="sec-lokasi" className="scroll-mt-28 border-t border-slate-100 pt-8 space-y-5">

              <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-center">

                <div>

                  <h2 className="text-2xl font-extrabold tracking-tight text-slate-900">

                    Lokasi Spesifik &amp; Akses

                  </h2>

                  <p className="mt-1 flex items-start gap-1.5 text-xs text-slate-500 sm:text-sm">

                    <span className="material-symbols-outlined mt-0.5 text-[16px] text-toba">

                      location_on

                    </span>

                    <span>{hospital.alamat || 'Alamat belum tersedia'}</span>

                  </p>

                </div>

                <button

                  type="button"

                  onClick={() => navigate(`/peta?rs=${encodeURIComponent(hospital.id)}&route=1`)}

                  className="inline-flex w-fit items-center gap-1.5 rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-50"

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

              </div>



              <div className="grid gap-3 sm:grid-cols-2">

                <a

                  href={directionsUrl(hospital)}

                  target="_blank"

                  rel="noopener noreferrer"

                  className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5 transition hover:border-toba/30 hover:bg-toba-mist/50"

                >

                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-toba-mist text-toba">

                    <span className="material-symbols-outlined text-[20px]">directions_car</span>

                  </span>

                  <span>

                    <span className="block text-sm font-bold text-slate-900">Google Maps</span>

                    <span className="block text-[11px] text-slate-500">Navigasi kendaraan pribadi</span>

                  </span>

                </a>

                <a

                  href={openStreetMapUrl(hospital) || mapsSearchUrl(hospital)}

                  target="_blank"

                  rel="noopener noreferrer"

                  className="flex items-start gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5 transition hover:border-toba/30 hover:bg-toba-mist/50"

                >

                  <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-700">

                    <span className="material-symbols-outlined text-[20px]">map</span>

                  </span>

                  <span>

                    <span className="block text-sm font-bold text-slate-900">OpenStreetMap</span>

                    <span className="block text-[11px] text-slate-500">Lihat titik pada peta terbuka</span>

                  </span>

                </a>

              </div>

            </div>

          </div>



          {/* Sidebar */}

          <aside className="lg:col-span-4">

            <div className="sticky top-28 space-y-4">

              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">

                <div className="flex items-center justify-between gap-2">

                  <div className="flex items-center gap-2">

                    <span className="h-2.5 w-2.5 rounded-full bg-toba" />

                    <span className="text-sm font-bold text-slate-900">

                      {hasEmergency ? 'Layanan IGD tercatat' : 'Informasi faskes'}

                    </span>

                  </div>

                  <span className="rounded-full bg-toba-mist px-2.5 py-0.5 text-[10px] font-bold text-toba-dark">

                    Kelas {hospital.kelas || '—'}

                  </span>

                </div>

                <p className="mt-1 flex items-center gap-1 text-xs text-slate-500">

                  <span className="material-symbols-outlined text-[14px] text-toba">location_on</span>

                  {hospital.kabkota || 'Sumatera Utara'}

                </p>



                <div className="mt-4 flex flex-col gap-2.5">

                  <button

                    type="button"

                    onClick={() => navigate(`/peta?rs=${encodeURIComponent(hospital.id)}&route=1`)}

                    disabled={hospital.lat == null || hospital.lon == null}

                    className="flex w-full items-center justify-center gap-2 rounded-full bg-toba px-6 py-3 text-sm font-bold text-white transition hover:bg-toba-dark disabled:cursor-not-allowed disabled:opacity-50"

                  >

                    <span className="material-symbols-outlined text-[19px]">directions</span>

                    Petunjuk Rute

                  </button>

                  <button

                    type="button"

                    onClick={() => {

                      toggleCompare(hospital.id);

                      setCompareModalOpen(true);

                    }}

                    className="flex w-full items-center justify-center gap-2 rounded-full border border-toba/30 bg-toba-mist px-6 py-2.5 text-sm font-bold text-toba-dark transition hover:bg-toba-soft"

                  >

                    <span className="material-symbols-outlined text-[18px]">compare</span>

                    Bandingkan RS

                  </button>

                  <button

                    type="button"

                    onClick={() => scrollToSection('sec-booking')}

                    className="flex w-full items-center justify-center gap-2 rounded-full border border-slate-300 bg-white px-6 py-2.5 text-sm font-semibold text-slate-800 transition hover:bg-slate-50"

                  >

                    <span className="material-symbols-outlined text-[18px]">bed</span>

                    Pesan kamar

                  </button>

                </div>



                {phone ? (

                  <div className="mt-4 border-t border-slate-100 pt-3.5 text-center">

                    <a

                      href={phone}

                      className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-700 hover:text-toba-dark"

                    >

                      <span className="material-symbols-outlined text-[16px] text-rose-600">call</span>

                      Hubungi: <strong className="text-slate-900">{hospital.telepon}</strong>

                    </a>

                  </div>

                ) : null}

              </section>



              <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-card">

                <h3 className="text-sm font-bold text-slate-900">Informasi Kontak</h3>

                <div className="mt-4 space-y-3.5">

                  <InfoRow icon="location_on" label="Alamat">

                    <span className="text-[12.5px] leading-relaxed">

                      {hospital.alamat || 'Alamat belum tersedia'}

                    </span>

                  </InfoRow>

                  <InfoRow icon="call" label="Telepon">

                    {phone ? (

                      <a href={phone} className="text-[12.5px] font-semibold text-toba hover:underline">

                        {hospital.telepon}

                      </a>

                    ) : (

                      <span className="text-[12.5px] text-slate-400">Belum tersedia</span>

                    )}

                  </InfoRow>

                  <InfoRow icon="mail" label="Email">

                    {emailLink ? (

                      <a href={emailLink} className="text-[12.5px] font-semibold text-toba hover:underline break-all">

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

                        className="inline-flex items-center gap-1 text-[12.5px] font-semibold text-toba hover:underline break-all"

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



      <KnowledgeGraphModal hospital={hospital} open={kgOpen} onClose={() => setKgOpen(false)} />

      <MinimalFooter />

    </div>

  );

}

