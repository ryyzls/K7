import { useEffect, useMemo, useState, useRef } from 'react';
import { Link, useNavigate, useParams } from 'react-router-dom';
import { getHospital, getHospitalAlternatives } from '../api';
import { colorOf } from '../components/HospitalCard';
import KnowledgeGraphModal from '../components/KnowledgeGraphModal';
import BookingForm from '../components/BookingForm';
import { websiteHref, emailHref } from '../utils';

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
      const popup = document.createElement('div');
      const title = document.createElement('strong');
      title.textContent = hospital.nama;
      const address = document.createElement('p');
      address.textContent = hospital.alamat || hospital.kabkota || '';
      popup.append(title, address);
      marker.bindPopup(popup).openPopup();

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

  const scheduleData = hospital?.jam_operasional?.jadwal_harian ||
    ['Senin','Selasa','Rabu','Kamis','Jumat','Sabtu','Minggu'].map(hari=>({hari,jam:'Belum tersedia'}));
  const spesialisasiList = hospital?.spesialisasi || [];
  const fasilitasList = [...new Set([
    ...(hospital?.fasilitas_medis_berbukti?.fasilitas_diagnostik_terlapor || []),
    ...(hospital?.fasilitas_medis_berbukti?.fasilitas_tempat_tidur_khusus || []).filter(f=>typeof f==='string'),
  ])];

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
                  <a href={websiteHref(hospital.website) || undefined} target="_blank" rel="noopener noreferrer" title={hospital.website}>
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
                  {[
                    ['Kode Kemenkes', hospital.kode_kemenkes],
                    ['Nama Rumah Sakit', hospital.nama],
                    ['Kabupaten/Kota', hospital.kabkota],
                    ['Alamat', hospital.alamat],
                    ['Direktur', hospital.direktur],
                    ['Kepemilikan', hospital.kepemilikan || hospital.pemilik],
                    ['Luas Tanah', hospital.luas_tanah],
                    ['Luas Bangunan', hospital.luas_bangunan],
                  ].map(([label,value])=><div className="info-item" key={label}><div><small>{label}</small><strong>{value ?? 'Belum tersedia'}</strong></div></div>)}
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
                  {(hospital.jam_operasional?.unit_operasional || [{unit:'Poliklinik Rawat Jalan',jadwal_harian:scheduleData}])
                    .filter(unit=>unit.jadwal_harian).map(unit=><div key={unit.unit} style={{marginBottom:'1.2rem'}}>
                      <h4 style={{marginBottom:'.6rem'}}>{unit.unit}</h4>
                      <div className="schedule-table">{unit.jadwal_harian.map(d=><div key={d.hari} className="schedule-row">
                        <span className="schedule-day">{d.hari}</span><span className={`schedule-time ${d.jam==='Tutup'?'closed':''}`}>{d.jam}</span>
                      </div>)}</div>
                    </div>)}
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
                    <i className="fa-solid fa-arrows-split-up-and-left" aria-hidden="true" /> Rumah Sakit Alternatif dengan Layanan Serupa
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
                                onClick={() => navigate(`/pencarian?compare=${encodeURIComponent(hospital.id)},${encodeURIComponent(alt.id)}`)}
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

                <BookingForm hospital={hospital} />
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
                        <a href={emailHref(hospital.email) || undefined}>{hospital.email}</a>
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
                          href={websiteHref(hospital.website) || undefined}
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
            {hospital.sumber_koordinat === 'kabkota' && <p>Koordinat perkiraan pusat wilayah, bukan lokasi pasti rumah sakit.</p>}
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
