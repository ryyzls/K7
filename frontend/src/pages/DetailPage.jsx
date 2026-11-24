import { useEffect, useMemo, useState, useRef } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getHospital, getHospitalAlternatives } from '../api';
import { colorOf } from '../components/HospitalCard';
import KnowledgeGraphModal from '../components/KnowledgeGraphModal';

const DESC = {
  A: 'Subspesialis luas',
  B: 'Spesialis lengkap',
  C: 'Spesialis dasar',
  D: 'Pelayanan dasar',
};

function formatWebsiteLabel(url) {
  if (!url) return '';
  try {
    const u = new URL(url.startsWith('http') ? url : `https://${url}`);
    return u.hostname.replace(/^www\./, '');
  } catch {
    return url.replace(/^https?:\/\/(www\.)?/, '').replace(/\/.*$/, '');
  }
}

export default function DetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [hospital, setHospital] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Alternatives state
  const [alternatives, setAlternatives] = useState([]);
  const [loadingAlts, setLoadingAlts] = useState(false);
  const [altsMessage, setAltsMessage] = useState('');

  // Active quicknav section
  const [activeNav, setActiveNav] = useState('sec-profil');

  // Booking simulation form states
  const [bookingFormData, setBookingFormData] = useState({
    nama_pasien: '',
    no_telp: '',
    jenis_kamar: '',
    tanggal_masuk: '',
    catatan: '',
  });
  const [bookingLoading, setBookingLoading] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);

  // Check booking states
  const [checkCode, setCheckCode] = useState('');
  const [checkLoading, setCheckLoading] = useState(false);
  const [checkResult, setCheckResult] = useState(null);
  const [checkError, setCheckError] = useState(null);

  // Carousel index
  const [slideIndex, setSlideIndex] = useState(0);

  // Knowledge Graph Modal
  const [showKG, setShowKG] = useState(false);

  // Leaflet map container ref
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);

  useEffect(() => {
    let isMounted = true;
    setLoading(true);
    setError(null);

    getHospital(id)
      .then((data) => {
        if (!isMounted) return;
        setHospital(data);
        setLoading(false);
      })
      .catch((err) => {
        if (!isMounted) return;
        setError(err.message || 'Gagal memuat detail rumah sakit');
        setLoading(false);
      });

    return () => {
      isMounted = false;
    };
  }, [id]);

  // Load alternatives (maksimal 3 RS terdekat & setara)
  useEffect(() => {
    if (!id) return;
    setLoadingAlts(true);
    getHospitalAlternatives(id, 3)
      .then((res) => {
        if (res.has_alternatives && res.alternatives?.length) {
          setAlternatives(res.alternatives.slice(0, 3));
        } else {
          setAlternatives([]);
          setAltsMessage(res.message || 'Tidak ada rumah sakit alternatif serupa di wilayah ini.');
        }
      })
      .catch(() => {
        setAlternatives([]);
        setAltsMessage('Rekomendasi alternatif tidak dapat dimuat saat ini.');
      })
      .finally(() => setLoadingAlts(false));
  }, [id]);

  // Gallery photos
  const photos = useMemo(() => {
    if (!hospital) return [];
    return [...new Set([...(hospital.galeri || []), hospital.foto].filter(Boolean))];
  }, [hospital]);

  // Initialize Leaflet mini-map in #sec-lokasi
  useEffect(() => {
    if (!hospital || hospital.lat == null || hospital.lon == null || !mapContainerRef.current) {
      return;
    }

    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }

    if (window.L) {
      const L = window.L;
      const map = L.map(mapContainerRef.current, {
        scrollWheelZoom: false,
      }).setView([hospital.lat, hospital.lon], 15);

      L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        attribution: '&copy; OpenStreetMap',
      }).addTo(map);

      const marker = L.marker([hospital.lat, hospital.lon]).addTo(map);
      marker.bindPopup(`<b>${hospital.nama}</b><br>${hospital.alamat || hospital.kabkota || ''}`).openPopup();

      mapInstanceRef.current = map;
      setTimeout(() => map.invalidateSize(), 300);
    }

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [hospital]);

  // Handle Quicknav click
  const scrollToSection = (sectionId) => {
    setActiveNav(sectionId);
    const element = document.getElementById(sectionId);
    if (element) {
      element.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  };

  // Schedule logic
  const scheduleData = useMemo(() => {
    if (!hospital) return [];
    const isVitaInsani = hospital.id === 'rs-199' || (hospital.nama || '').toLowerCase().includes('vita insani');
    if (isVitaInsani) {
      return [
        { hari: 'Senin', jam: '08:00 - 20:00' },
        { hari: 'Selasa', jam: '08:00 - 20:00' },
        { hari: 'Rabu', jam: '08:00 - 20:00' },
        { hari: 'Kamis', jam: '08:00 - 20:00' },
        { hari: 'Jumat', jam: '08:00 - 20:00' },
        { hari: 'Sabtu', jam: '08:00 - 15:00' },
        { hari: 'Minggu', jam: 'Tutup' },
      ];
    }
    if (hospital.jam_operasional?.jadwal_harian?.length) {
      return hospital.jam_operasional.jadwal_harian;
    }
    const units = hospital.jam_operasional?.unit_operasional || [];
    let defaultHours = '08:00 - 16:00';
    for (const u of units) {
      if (u.unit && (u.unit.toLowerCase().includes('poli') || u.unit.toLowerCase().includes('rawat jalan'))) {
        if (u.jadwal_deskripsi) defaultHours = u.jadwal_deskripsi;
        break;
      }
    }
    return [
      { hari: 'Senin', jam: defaultHours },
      { hari: 'Selasa', jam: defaultHours },
      { hari: 'Rabu', jam: defaultHours },
      { hari: 'Kamis', jam: defaultHours },
      { hari: 'Jumat', jam: defaultHours },
      { hari: 'Sabtu', jam: '08:00 - 12:00' },
      { hari: 'Minggu', jam: 'Tutup' },
    ];
  }, [hospital]);

  // Spesialisasi logic
  const spesialisasiList = useMemo(() => {
    if (!hospital) return [];
    const isVitaInsani = hospital.id === 'rs-199' || (hospital.nama || '').toLowerCase().includes('vita insani');
    if (isVitaInsani) return ['Konseling Kesehatan Mental', 'Psikologi'];
    if (Array.isArray(hospital.spesialisasi) && hospital.spesialisasi.length) {
      return hospital.spesialisasi;
    }
    return [];
  }, [hospital]);

  // Fasilitas logic
  const fasilitasList = useMemo(() => {
    if (!hospital) return [];
    const isVitaInsani = hospital.id === 'rs-199' || (hospital.nama || '').toLowerCase().includes('vita insani');
    if (isVitaInsani) return ['Layanan Kesehatan Rumah'];
    if (Array.isArray(hospital.fasilitas) && hospital.fasilitas.length) {
      return hospital.fasilitas;
    }
    if (hospital.fasilitas_medis_berbukti?.fasilitas_diagnostik_terlapor?.length) {
      return hospital.fasilitas_medis_berbukti.fasilitas_diagnostik_terlapor;
    }
    return [];
  }, [hospital]);

  // Handle Booking Submission
  const handleBookingSubmit = async (e) => {
    e.preventDefault();
    setBookingLoading(true);
    setBookingResult(null);

    try {
      const payload = {
        ...bookingFormData,
        rs_id: hospital.id,
        nama_rs: hospital.nama,
      };
      const res = await fetch('/api/booking', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Gagal membuat reservasi');
      }
      setBookingResult({ success: true, data });
      setBookingFormData({
        nama_pasien: '',
        no_telp: '',
        jenis_kamar: '',
        tanggal_masuk: '',
        catatan: '',
      });
    } catch (err) {
      setBookingResult({ success: false, error: err.message });
    } finally {
      setBookingLoading(false);
    }
  };

  // Handle Check Booking
  const handleCheckBooking = async (e) => {
    e.preventDefault();
    if (!checkCode.trim()) return;
    setCheckLoading(true);
    setCheckResult(null);
    setCheckError(null);

    try {
      const res = await fetch(`/api/booking/${encodeURIComponent(checkCode.trim())}`);
      if (res.status === 404) {
        setCheckError('Kode booking tidak ditemukan.');
        return;
      }
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Gagal mengecek kode booking');
      }
      setCheckResult(data);
    } catch (err) {
      setCheckError(err.message);
    } finally {
      setCheckLoading(false);
    }
  };

  // Handle Cancel Booking
  const handleCancelBooking = async (code) => {
    if (!window.confirm(`Batalkan booking ${code}?`)) return;
    try {
      const res = await fetch(`/api/booking/${encodeURIComponent(code)}`, {
        method: 'DELETE',
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || 'Gagal membatalkan');
      }
      alert('Booking berhasil dibatalkan');
      setCheckResult((prev) => (prev ? { ...prev, status: 'dibatalkan' } : null));
    } catch (err) {
      alert('Gagal membatalkan: ' + err.message);
    }
  };

  if (loading) {
    return (
      <div className="d-sheet">
        <header className="d-head">
          <div className="d-head-inner">
            <Link className="brand" to="/">
              <img className="brand-image" src="/images/cari-sehat-logo.png" alt="Cari Sehat" width="190" height="64" />
            </Link>
          </div>
        </header>
        <div className="d-body" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
          <div className="spin" style={{ margin: '0 auto 1rem', width: 28, height: 28, borderWidth: 3 }} />
          <p style={{ color: 'var(--mute)' }}>Memuat detail rumah sakit...</p>
        </div>
      </div>
    );
  }

  if (error || !hospital) {
    return (
      <div className="d-sheet">
        <header className="d-head">
          <div className="d-head-inner">
            <Link className="brand" to="/">
              <img className="brand-image" src="/images/cari-sehat-logo.png" alt="Cari Sehat" width="190" height="64" />
            </Link>
            <button className="d-back" type="button" onClick={() => navigate(-1)}>
              <i className="fa-solid fa-arrow-left" aria-hidden="true" />
              <span>Kembali</span>
            </button>
          </div>
        </header>
        <div className="d-body" style={{ textAlign: 'center', padding: '5rem 1rem' }}>
          <h2 style={{ color: 'var(--emergency)' }}>Data tidak ditemukan</h2>
          <p style={{ color: 'var(--mute)' }}>{error || 'Rumah sakit yang diminta tidak tersedia dalam katalog.'}</p>
          <Link className="btn btn-primary" to="/pencarian" style={{ marginTop: '1rem' }}>
            Kembali ke Katalog
          </Link>
        </div>
      </div>
    );
  }

  const c = colorOf(hospital.kelas);
  const isIgd24 =
    (hospital.igd_24jam_terlapor &&
      (hospital.igd_24jam_terlapor.buka_24_jam || hospital.igd_24jam_terlapor.igd_24jam_terlapor)) ||
    hospital.igd_tersedia;
  const igdText = isIgd24 ? 'Buka 24 Jam' : 'Belum tersedia';
  const telLink = hospital.telepon ? `tel:${hospital.telepon.replace(/[^0-9+]/g, '')}` : '';

  return (
    <div className="d-sheet" style={{ '--c': c }}>
      {/* Site Header */}
      <header className="d-head">
        <div className="d-head-inner">
          <Link className="brand" to="/" aria-label="CariSehat, Beranda">
            <img className="brand-image" src="/images/cari-sehat-logo.png" alt="Cari Sehat" width="190" height="64" />
          </Link>
          <nav className="d-site-nav" aria-label="Navigasi utama">
            <Link to="/">Beranda</Link>
            <Link to="/pencarian" aria-current="page">Cari Rumah Sakit</Link>
            <Link to="/peta">Peta</Link>
            <a href="/#about">Tentang</a>
          </nav>
          <div style={{ display: 'flex', gap: '0.6rem', alignItems: 'center' }}>
            <button
              className="btn btn-ghost"
              type="button"
              onClick={() => setShowKG(true)}
              title="Eksplorasi Graf Pengetahuan Semantik"
            >
              <i className="fa-solid fa-circle-nodes" aria-hidden="true" style={{ color: 'var(--toba)' }} />
              <span>Graf Pengetahuan</span>
            </button>
            <button
              className="d-back"
              type="button"
              onClick={() => navigate(-1)}
              aria-label="Kembali ke katalog rumah sakit"
            >
              <i className="fa-solid fa-arrow-left" aria-hidden="true" />
              <span>Kembali</span>
            </button>
          </div>
        </div>
      </header>

      <div className="d-body">
        <div className="d-body-inner">
          {/* Hero Header */}
          <div className="d-hero" style={{ overflow: 'hidden' }}>
            {/* Gallery / Carousel */}
            {photos.length > 0 && (
              <div className="hospital-carousel" aria-label="Galeri foto rumah sakit" style={{ height: 260, maxHeight: 260, width: '100%', overflow: 'hidden' }}>
                <div className="hospital-slides" tabIndex={0} style={{ width: '100%', height: '100%' }}>
                  {photos.map((src, i) => (
                    <img
                      key={i}
                      src={src}
                      alt={`Foto ${i + 1} ${hospital.nama}`}
                      loading={i === 0 ? 'eager' : 'lazy'}
                      style={{
                        display: i === slideIndex ? 'block' : 'none',
                        width: '100%',
                        height: 260,
                        maxHeight: 260,
                        objectFit: 'cover',
                      }}
                      onError={(e) => {
                        e.currentTarget.style.display = 'none';
                      }}
                    />
                  ))}
                </div>
                {photos.length > 1 && (
                  <div className="carousel-controls">
                    <button
                      type="button"
                      aria-label="Foto sebelumnya"
                      onClick={() => setSlideIndex((prev) => (prev - 1 + photos.length) % photos.length)}
                    >
                      &#10094;
                    </button>
                    <output>{slideIndex + 1} / {photos.length}</output>
                    <button
                      type="button"
                      aria-label="Foto berikutnya"
                      onClick={() => setSlideIndex((prev) => (prev + 1) % photos.length)}
                    >
                      &#10095;
                    </button>
                  </div>
                )}
              </div>
            )}

            <div className="d-hero-top">
              <div className="d-pills">
                <span className="badge" title={DESC[hospital.kelas] || 'Kelas Rumah Sakit'}>
                  Kelas {hospital.kelas || '?'}
                </span>
                <span className="pill">
                  <i className="fa-solid fa-hospital" aria-hidden="true" /> {hospital.jenis || 'Rumah Sakit'}
                </span>
                {hospital.bpjs ? (
                  <span className="pill pill-bpjs">Menerima BPJS Kesehatan</span>
                ) : (
                  <span className="pill pill-warn">
                    <i className="fa-solid fa-triangle-exclamation" aria-hidden="true" /> Konfirmasi BPJS ke Rumah Sakit
                  </span>
                )}
              </div>
              <h2 id="d-title">{hospital.nama}</h2>
              <p className="d-hero-sub">
                <i className="fa-solid fa-location-dot" aria-hidden="true" /> {hospital.kabkota}, Provinsi Sumatera Utara
              </p>
              {hospital.website && (
                <div className="rs-website" style={{ margin: '0.4rem 0 1.2rem', fontSize: '0.9rem' }}>
                  <a href={hospital.website} target="_blank" rel="noopener noreferrer" title={hospital.website}>
                    <i className="fa-solid fa-globe" aria-hidden="true" /> {formatWebsiteLabel(hospital.website)}{' '}
                    <i className="fa-solid fa-arrow-up-right-from-square" aria-hidden="true" style={{ fontSize: '0.75rem', opacity: 0.75 }} />
                  </a>
                </div>
              )}
            </div>

            <div className="d-hero-actions">
              {hospital.lat != null && hospital.lon != null && (
                <button
                  className="btn btn-primary"
                  type="button"
                  onClick={() => scrollToSection('sec-lokasi')}
                >
                  <i className="fa-solid fa-diamond-turn-right" aria-hidden="true" /> Petunjuk Rute Cepat
                </button>
              )}
              {telLink && (
                <a className="btn btn-ghost" href={telLink}>
                  <i className="fa-solid fa-phone" aria-hidden="true" /> Hubungi Hotline
                </a>
              )}
            </div>
          </div>

          {/* Sticky Quick Navigation */}
          <div className="d-quicknav" role="tablist">
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-profil' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-profil')}
            >
              <i className="fa-solid fa-clipboard-list" aria-hidden="true" /> Profil
            </button>
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-jam' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-jam')}
            >
              <i className="fa-solid fa-clock" aria-hidden="true" /> Jam &amp; IGD
            </button>
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-spesialisasi' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-spesialisasi')}
            >
              <i className="fa-solid fa-stethoscope" aria-hidden="true" /> Spesialisasi
            </button>
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-fasilitas' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-fasilitas')}
            >
              <i className="fa-solid fa-hospital-user" aria-hidden="true" /> Fasilitas Medis
            </button>
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-alternatif' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-alternatif')}
            >
              <i className="fa-solid fa-arrows-split-up-and-left" aria-hidden="true" /> Alternatif
            </button>
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-booking' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-booking')}
            >
              <i className="fa-solid fa-bed" aria-hidden="true" /> Booking Simulasi
            </button>
            <button
              type="button"
              className={`d-navpill ${activeNav === 'sec-lokasi' ? 'active' : ''}`}
              onClick={() => scrollToSection('sec-lokasi')}
            >
              <i className="fa-solid fa-location-dot" aria-hidden="true" /> Lokasi Peta
            </button>
          </div>

          {/* Detail Content Grid */}
          <div className="d-detail-grid">
            <div className="d-main-column">
              {/* Section 1: Profil */}
              <section id="sec-profil" className="d-card">
                <div className="d-card-head">
                  <h3>
                    <i className="fa-solid fa-clipboard-list" aria-hidden="true" /> Profil &amp; Informasi Rumah Sakit
                  </h3>
                </div>
                <div className="info-grid">
                  <div className="info-item">
                    <i className="fa-solid fa-hospital" aria-hidden="true" style={{ fontSize: '1.15rem', color: 'var(--toba)' }} />
                    <div>
                      <small>Klasifikasi &amp; Tipe</small>
                      <strong>
                        Kelas {hospital.kelas || 'Belum terklasifikasi'}{' '}
                        <span style={{ display: 'inline-block', width: '0.8rem' }} /> Rumah Sakit {hospital.jenis}
                      </strong>
                    </div>
                  </div>
                  <div className="info-item">
                    <i className="fa-solid fa-truck-medical" aria-hidden="true" style={{ fontSize: '1.15rem', color: 'var(--emergency)' }} />
                    <div>
                      <small>Instalasi Gawat Darurat (IGD)</small>
                      <strong style={{ color: 'var(--emergency)' }}>{igdText}</strong>
                    </div>
                  </div>
                </div>
              </section>

              {/* Section 2: Jam Operasional & IGD */}
              <section id="sec-jam" className="d-card">
                <div className="d-card-head">
                  <h3>
                    <i className="fa-solid fa-clock" aria-hidden="true" /> Jam Operasional &amp; Poliklinik
                  </h3>
                </div>
                <div style={{ marginTop: '.8rem' }}>
                  <div style={{ marginBottom: '1.2rem', paddingBottom: '.8rem', borderBottom: '1px solid #f1f5f9' }}>
                    <div style={{ fontSize: '.85rem', color: 'var(--mute)', marginBottom: '.2rem' }}>Instalasi Gawat Darurat (IGD)</div>
                    <div style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--ink)' }}>{igdText}</div>
                  </div>
                  <div className="schedule-table">
                    {scheduleData.map((d, idx) => (
                      <div key={idx} className="schedule-row">
                        <span className="schedule-day">{d.hari}</span>
                        <span className={`schedule-time ${d.jam === 'Tutup' ? 'closed' : ''}`}>{d.jam}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </section>

              {/* Section 3: Spesialisasi */}
              <section id="sec-spesialisasi" className="d-card">
                <div className="d-card-head">
                  <h3>
                    <i className="fa-solid fa-stethoscope" aria-hidden="true" /> Spesialisasi
                  </h3>
                </div>
                <div style={{ marginTop: '.8rem' }}>
                  {spesialisasiList.length ? (
                    <ul
                      className="clean-bullet-list"
                      style={{
                        listStyleType: 'disc',
                        paddingLeft: '1.5rem',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '0.6rem 2rem',
                        margin: 0,
                      }}
                    >
                      {spesialisasiList.map((s, idx) => (
                        <li key={idx} style={{ display: 'list-item', listStyleType: 'disc', color: 'var(--ink)' }}>
                          {s}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ margin: 0, color: 'var(--mute)', fontSize: '0.88rem' }}>Belum tersedia</p>
                  )}
                </div>
              </section>

              {/* Section 4: Fasilitas Medis */}
              <section id="sec-fasilitas" className="d-card">
                <div className="d-card-head">
                  <h3>
                    <i className="fa-solid fa-hospital-user" aria-hidden="true" /> Fasilitas Medis
                  </h3>
                </div>
                <div style={{ marginTop: '.8rem' }}>
                  {fasilitasList.length ? (
                    <ul
                      className="clean-bullet-list"
                      style={{
                        listStyleType: 'disc',
                        paddingLeft: '1.5rem',
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '0.6rem 2rem',
                        margin: 0,
                      }}
                    >
                      {fasilitasList.map((f, idx) => (
                        <li key={idx} style={{ display: 'list-item', listStyleType: 'disc', color: 'var(--ink)' }}>
                          {f}
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p style={{ margin: 0, color: 'var(--mute)', fontSize: '0.88rem' }}>Belum tersedia</p>
                  )}
                </div>
              </section>

              {/* Section: Alternatif Rumah Sakit (3 Rekomendasi Terdekat & Setara) */}
              <section id="sec-alternatif" className="d-card">
                <div className="d-card-head">
                  <h3>
                    <i className="fa-solid fa-arrows-split-up-and-left" aria-hidden="true" /> Rumah Sakit Alternatif Terdekat &amp; Setara
                  </h3>
                </div>
                <div style={{ marginTop: '.8rem' }}>
                  {loadingAlts ? (
                    <div style={{ padding: '1rem', textAlign: 'center', color: 'var(--mute)' }}>
                      <div className="spin" style={{ display: 'inline-block', marginRight: '0.5rem' }} />
                      Memuat alternatif rumah sakit...
                    </div>
                  ) : alternatives.length > 0 ? (
                    <div
                      className="d-alternatives-grid"
                      style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
                        gap: '1rem',
                      }}
                    >
                      {alternatives.slice(0, 3).map((alt) => {
                        const foto = alt.foto || `/images/rs/${alt.id}/foto_1.jpg`;
                        return (
                          <article key={alt.id} className="alt-card">
                            <div className="alt-card-thumb">
                              <img
                                src={foto}
                                alt={alt.nama}
                                loading="lazy"
                                onError={(e) => {
                                  e.currentTarget.parentElement.style.display = 'none';
                                }}
                              />
                            </div>
                            <div className="alt-card-header">
                              <h4>{alt.nama}</h4>
                              <span className="alt-kelas-badge">Kelas {alt.kelas}</span>
                            </div>
                            <p className="alt-meta">
                              <i className="fa-solid fa-location-dot" aria-hidden="true" /> {alt.kabkota}
                            </p>
                            <div className="alt-actions">
                              <Link className="btn btn-ghost btn-sm" to={`/rumah-sakit/${encodeURIComponent(alt.id)}`}>
                                Lihat Detail
                              </Link>
                              <button
                                type="button"
                                className="btn-compare-sm"
                                onClick={() => navigate(`/pencarian?compare=${encodeURIComponent(alt.id)}`)}
                                title="Bandingkan langsung dengan rumah sakit ini"
                              >
                                <i className="fa-solid fa-code-compare" aria-hidden="true" /> <span>Bandingkan</span>
                              </button>
                            </div>
                          </article>
                        );
                      })}
                    </div>
                  ) : (
                    <p style={{ margin: 0, color: 'var(--mute)', fontSize: '0.88rem' }}>{altsMessage}</p>
                  )}
                </div>
              </section>

              {/* Section: Reservasi Rawat Inap (Simulasi) */}
              <section id="sec-booking" className="d-card">
                <div className="d-card-head">
                  <h3>
                    <i className="fa-solid fa-bed" aria-hidden="true" /> Reservasi Kamar Rawat Inap
                  </h3>
                  <span className="d-card-badge sim-badge">Simulasi PostgreSQL</span>
                </div>
                <div className="sim-banner">
                  <span className="sim-tag">SIMULASI AKADEMIK</span>
                  <p>
                    Pemesanan kamar rawat inap ini merupakan demo interaktif Tugas Besar MSBD berbasis PostgreSQL. Data pemesanan tercatat di basis data lokal dan tidak diteruskan ke sistem rumah sakit asli.
                  </p>
                </div>

                <form onSubmit={handleBookingSubmit} className="booking-form-grid">
                  <div className="form-row">
                    <label>
                      Nama Pasien
                      <input
                        name="nama_pasien"
                        placeholder="Nama lengkap pasien"
                        required
                        value={bookingFormData.nama_pasien}
                        onChange={(e) => setBookingFormData({ ...bookingFormData, nama_pasien: e.target.value })}
                      />
                    </label>
                    <label>
                      Nomor WhatsApp / HP
                      <input
                        name="no_telp"
                        type="tel"
                        placeholder="08xxxxxxxxxx"
                        required
                        value={bookingFormData.no_telp}
                        onChange={(e) => setBookingFormData({ ...bookingFormData, no_telp: e.target.value })}
                      />
                    </label>
                  </div>
                  <div className="form-row">
                    <label>
                      Jenis Kamar Rawat Inap
                      <select
                        name="jenis_kamar"
                        required
                        value={bookingFormData.jenis_kamar}
                        onChange={(e) => setBookingFormData({ ...bookingFormData, jenis_kamar: e.target.value })}
                      >
                        <option value="">-- Pilih Jenis Kamar --</option>
                        <option value="VIP">VIP</option>
                        <option value="Kelas I">Kelas I</option>
                        <option value="Kelas II">Kelas II</option>
                        <option value="Kelas III">Kelas III</option>
                        <option value="ICU">ICU (Intensive Care Unit)</option>
                      </select>
                    </label>
                    <label>
                      Tanggal Rencana Masuk
                      <input
                        name="tanggal_masuk"
                        type="date"
                        required
                        min={new Date().toISOString().split('T')[0]}
                        value={bookingFormData.tanggal_masuk}
                        onChange={(e) => setBookingFormData({ ...bookingFormData, tanggal_masuk: e.target.value })}
                      />
                    </label>
                  </div>
                  <label>
                    Catatan Medis Khusus / Kebutuhan (Opsional)
                    <textarea
                      name="catatan"
                      placeholder="Contoh: Memerlukan kursi roda, riwayat alergi..."
                      rows="2"
                      value={bookingFormData.catatan}
                      onChange={(e) => setBookingFormData({ ...bookingFormData, catatan: e.target.value })}
                    />
                  </label>
                  <button type="submit" className="btn btn-primary btn-submit-booking" disabled={bookingLoading}>
                    {bookingLoading ? (
                      <>
                        <div className="spin" style={{ marginRight: '0.4rem' }} /> Memproses...
                      </>
                    ) : (
                      <>
                        <i className="fa-solid fa-bed" aria-hidden="true" /> Konfirmasi Reservasi Kamar (Simulasi)
                      </>
                    )}
                  </button>
                </form>

                {bookingResult && (
                  <div
                    style={{
                      marginTop: '.9rem',
                      padding: '.8rem 1rem',
                      borderRadius: 10,
                      background: bookingResult.success ? 'var(--toba-mist)' : '#fee2e2',
                      border: `1px solid ${bookingResult.success ? '#99f6e4' : '#fca5a5'}`,
                      color: bookingResult.success ? 'var(--toba-d)' : '#991b1b',
                    }}
                  >
                    {bookingResult.success ? (
                      <div>
                        <strong>Reservasi Berhasil Dibuat!</strong>
                        <p style={{ margin: '0.3rem 0 0', fontSize: '0.85rem' }}>
                          Kode Booking: <b>{bookingResult.data?.kode_booking}</b>. Simpan kode ini untuk mengecek status reservasi Anda.
                        </p>
                      </div>
                    ) : (
                      <div>
                        <strong>Gagal:</strong> {bookingResult.error}
                      </div>
                    )}
                  </div>
                )}

                <hr style={{ border: 0, borderTop: '1px solid var(--line)', margin: '1.4rem 0' }} />

                <div className="check-booking-box">
                  <h4>
                    <i className="fa-solid fa-magnifying-glass" aria-hidden="true" /> Cek Status Kode Pemesanan
                  </h4>
                  <p style={{ fontSize: '.82rem', marginBottom: '.6rem', color: 'var(--mute)' }}>
                    Sudah pernah membuat reservasi simulasi? Masukkan kode booking untuk mengecek data.
                  </p>
                  <form onSubmit={handleCheckBooking} className="check-booking-form">
                    <input
                      name="kode_cek"
                      placeholder="Masukkan kode (contoh: BK-20261117-XXXXXXXX)"
                      required
                      value={checkCode}
                      onChange={(e) => setCheckCode(e.target.value)}
                    />
                    <button type="submit" className="btn btn-ghost" disabled={checkLoading}>
                      {checkLoading ? 'Memeriksa...' : 'Cek Status'}
                    </button>
                  </form>

                  {checkError && (
                    <div style={{ marginTop: '.7rem', color: '#be123c', fontSize: '.85rem' }}>
                      <i className="fa-solid fa-circle-xmark" aria-hidden="true" /> {checkError}
                    </div>
                  )}

                  {checkResult && (
                    <div
                      style={{
                        marginTop: '.7rem',
                        background: '#f8fafc',
                        border: '1px solid var(--line)',
                        borderRadius: 10,
                        padding: '.8rem',
                        fontSize: '.85rem',
                      }}
                    >
                      <strong>
                        {checkResult.status === 'dibatalkan' && (
                          <i className="fa-solid fa-circle-xmark" aria-hidden="true" style={{ color: '#be123c', marginRight: 4 }} />
                        )}
                        Booking {checkResult.kode_booking}
                      </strong>
                      <div style={{ marginTop: '.4rem', display: 'grid', gap: '.2rem' }}>
                        <span>
                          <i className="fa-solid fa-user" aria-hidden="true" /> {checkResult.nama_pasien}{' '}
                          <span style={{ display: 'inline-block', width: '0.8rem' }} />{' '}
                          <i className="fa-solid fa-phone" aria-hidden="true" /> {checkResult.no_telp}
                        </span>
                        <span>
                          <i className="fa-solid fa-hospital" aria-hidden="true" /> {checkResult.nama_rs}
                        </span>
                        <span>
                          <i className="fa-solid fa-bed" aria-hidden="true" /> {checkResult.jenis_kamar}{' '}
                          <span style={{ display: 'inline-block', width: '0.8rem' }} />{' '}
                          <i className="fa-solid fa-calendar-days" aria-hidden="true" /> Masuk: {checkResult.tanggal_masuk}
                        </span>
                        <span
                          style={{
                            color:
                              checkResult.status === 'dikonfirmasi'
                                ? '#059669'
                                : checkResult.status === 'dibatalkan'
                                  ? '#be123c'
                                  : '#d97706',
                            fontWeight: 600,
                          }}
                        >
                          Status: {checkResult.status?.toUpperCase()}
                        </span>
                      </div>
                      {checkResult.status === 'menunggu' && (
                        <button
                          type="button"
                          className="btn btn-ghost"
                          style={{ marginTop: '.5rem', color: '#be123c', borderColor: '#be123c' }}
                          onClick={() => handleCancelBooking(checkResult.kode_booking)}
                        >
                          Batalkan Booking
                        </button>
                      )}
                    </div>
                  )}
                </div>
              </section>
            </div>

            {/* Side Column */}
            <aside className="d-side-column">
              <section id="sec-contact" className="d-card">
                <div className="d-card-head">
                  <h3>Informasi Kontak</h3>
                </div>
                <div className="info-grid" style={{ gridTemplateColumns: '1fr' }}>
                  <div className="info-item">
                    <i className="fa-solid fa-location-dot" aria-hidden="true" style={{ color: 'var(--toba)', fontSize: '1.15rem' }} />
                    <div>
                      <small>Alamat</small>
                      <span>{hospital.alamat || 'Belum tersedia'}</span>
                    </div>
                  </div>
                  <div className="info-item">
                    <i className="fa-solid fa-phone" aria-hidden="true" style={{ color: 'var(--toba)', fontSize: '1.15rem' }} />
                    <div>
                      <small>Telepon</small>
                      {hospital.telepon ? (
                        <a href={telLink}>{hospital.telepon}</a>
                      ) : (
                        <span style={{ color: 'var(--mute)' }}>Belum tersedia</span>
                      )}
                    </div>
                  </div>
                  <div className="info-item">
                    <i
                      className="fa-solid fa-envelope"
                      aria-hidden="true"
                      style={{ color: hospital.email ? 'var(--toba)' : 'var(--mute)', fontSize: '1.15rem' }}
                    />
                    <div>
                      <small>Email</small>
                      {hospital.email ? (
                        <a href={`mailto:${hospital.email}`}>{hospital.email}</a>
                      ) : (
                        <span style={{ color: 'var(--mute)' }}>Belum tersedia</span>
                      )}
                    </div>
                  </div>
                  <div className="info-item">
                    <i
                      className="fa-solid fa-globe"
                      aria-hidden="true"
                      style={{ color: hospital.website ? 'var(--toba)' : 'var(--mute)', fontSize: '1.15rem' }}
                    />
                    <div>
                      <small>Website Resmi</small>
                      {hospital.website ? (
                        <a
                          href={hospital.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={hospital.website}
                          style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem' }}
                        >
                          <span>{formatWebsiteLabel(hospital.website)}</span>
                          <i className="fa-solid fa-arrow-up-right-from-square" aria-hidden="true" style={{ fontSize: '0.75rem', opacity: 0.75 }} />
                        </a>
                      ) : (
                        <span style={{ color: 'var(--mute)' }}>Belum tersedia</span>
                      )}
                    </div>
                  </div>
                </div>
                {hospital.lat != null && hospital.lon != null && (
                  <button
                    className="btn btn-primary"
                    style={{ width: '100%', justifyContent: 'center', marginTop: '0.85rem' }}
                    type="button"
                    onClick={() => scrollToSection('sec-lokasi')}
                  >
                    <i className="fa-solid fa-diamond-turn-right" aria-hidden="true" /> Lihat Rute di Peta
                  </button>
                )}
              </section>

              <section className="d-card">
                <div className="d-card-head">
                  <h3>Booking Simulasi</h3>
                </div>
                <p style={{ fontSize: '.82rem', color: 'var(--mute)', margin: 0, lineHeight: 1.5 }}>
                  Simulasi pemesanan kamar rawat inap untuk keperluan akademik MSBD.
                </p>
                <button
                  type="button"
                  className="btn btn-ghost"
                  style={{ width: '100%', justifyContent: 'center', marginTop: '0.85rem' }}
                  onClick={() => scrollToSection('sec-booking')}
                >
                  Booking Sekarang
                </button>
              </section>
            </aside>
          </div>

          {/* Section 5: Lokasi Peta (Full Width) */}
          <section id="sec-lokasi" className="d-card" style={{ marginTop: '1.25rem' }}>
            <div className="d-card-head">
              <h3>
                <i className="fa-solid fa-location-dot" aria-hidden="true" /> Lokasi Peta
              </h3>
            </div>
            {hospital.lat != null && hospital.lon != null ? (
              <>
                <div
                  ref={mapContainerRef}
                  style={{
                    width: '100%',
                    height: 380,
                    borderRadius: 14,
                    overflow: 'hidden',
                    border: '1px solid var(--line)',
                    background: '#e2e8f0',
                  }}
                />
                <div style={{ display: 'flex', gap: '.6rem', marginTop: '1rem', flexWrap: 'wrap' }}>
                  <button
                    className="btn btn-primary"
                    type="button"
                    onClick={() => navigate(`/peta?lat=${hospital.lat}&lon=${hospital.lon}&destId=${hospital.id}`)}
                  >
                    <i className="fa-solid fa-diamond-turn-right" aria-hidden="true" /> Panduan Rute ke Rumah Sakit Ini
                  </button>
                  <a
                    className="btn btn-ghost"
                    href={`https://www.openstreetmap.org/?mlat=${hospital.lat}&mlon=${hospital.lon}#map=17/${hospital.lat}/${hospital.lon}`}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <i className="fa-solid fa-arrow-up-right-from-square" aria-hidden="true" /> Buka di OpenStreetMap
                  </a>
                </div>
              </>
            ) : (
              <p style={{ margin: 0, color: 'var(--mute)' }}>Koordinat lokasi rumah sakit belum tersedia.</p>
            )}
          </section>
        </div>
      </div>

      {/* Knowledge Graph Modal */}
      {showKG && (
        <KnowledgeGraphModal hospitalId={hospital.id} onClose={() => setShowKG(false)} />
      )}
    </div>
  );
}
