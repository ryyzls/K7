import { Link } from 'react-router-dom';

export default function CompareModal({
  open = true,
  data,
  compareData,
  onClose,
  onRemove,
}) {
  const d = compareData || data;
  if (!open || !d || !d.hospitals || !d.hospitals.length) return null;

  const hs = d.hospitals || [];
  const matrix = d.comparison_matrix || {};
  const shared = matrix.shared_services || [];

  return (
    <div
      id="compare-modal-wrap"
      className="compare-modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="compare-modal-title"
    >
      <div className="compare-modal-dialog">
        <div className="compare-modal-head">
          <div>
            <h2 id="compare-modal-title">
              <i className="fa-solid fa-code-compare" aria-hidden="true" /> Perbandingan Rumah Sakit
            </h2>
            <p className="compare-modal-sub">
              Membandingkan secara faktual 2 rumah sakit berdasarkan data Kemenkes RI &amp; SIRS.
            </p>
          </div>
          <button
            type="button"
            className="btn-close-compare"
            id="btn-close-compare"
            aria-label="Tutup perbandingan"
            onClick={onClose}
          >
            &times;
          </button>
        </div>

        <div id="compare-modal-content" className="compare-modal-body">
          <div className="compare-table-wrap">
            <table className="compare-table">
              <thead>
                <tr>
                  <th className="attr-col">Rumah Sakit</th>
                  {hs.map((h) => (
                    <th key={h.id} className="rs-col">
                      <div className="compare-card-top">
                        <h3>{h.nama}</h3>
                        <div style={{ display: 'flex', gap: '.35rem', alignItems: 'center', flexWrap: 'wrap', margin: '.25rem 0' }}>
                          <span
                            style={{
                              fontSize: '.72rem',
                              fontWeight: 700,
                              padding: '.15rem .45rem',
                              borderRadius: 99,
                              background: '#e2e8f0',
                              color: 'var(--ink-soft)',
                            }}
                          >
                            Kelas {h.kelas}
                          </span>
                          <span style={{ fontSize: '.72rem', color: 'var(--mute)' }}>{h.jenis}</span>
                        </div>
                        {onRemove && (
                          <button
                            type="button"
                            className="btn btn-ghost"
                            style={{ fontSize: '.72rem', padding: '.2rem .4rem', width: 'fit-content' }}
                            onClick={() => onRemove(h.id)}
                          >
                            Hapus
                          </button>
                        )}
                      </div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <th className="attr-col">Kode Kemenkes</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      <strong>{h.kode_kemenkes || 'Belum tersedia'}</strong>
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Wilayah &amp; Alamat</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      <strong>{h.kabkota}</strong>
                      <p style={{ margin: '.25rem 0 0', fontSize: '.78rem', color: 'var(--ink-soft)' }}>
                        {h.alamat || 'Alamat belum tersedia'}
                      </p>
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Kontak Telepon</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      {h.telepon && h.telepon !== 'Belum tersedia' ? (
                        <a href={`tel:${h.telepon.replace(/[^0-9+]/g, '')}`}>
                          <i className="fa-solid fa-phone" aria-hidden="true" /> {h.telepon}
                        </a>
                      ) : (
                        <span style={{ color: 'var(--mute)' }}>Belum tersedia</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Website Resmi RS</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      {h.website_resmi?.url ? (
                        <a
                          href={h.website_resmi.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--toba)', textDecoration: 'underline', fontWeight: 700 }}
                        >
                          <i className="fa-solid fa-globe" aria-hidden="true" /> Buka Website
                        </a>
                      ) : (
                        <span style={{ color: 'var(--mute)' }}>Belum tersedia</span>
                      )}
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Gawat Darurat (UGD)</th>
                  {hs.map((h) => {
                    const u = Array.isArray(h.semua_layanan_sirs)
                      ? h.semua_layanan_sirs.some((x) => x.toLowerCase().includes('gawat darurat') || x.toLowerCase().includes('ugd'))
                      : false;
                    return (
                      <td key={h.id}>
                        {u ? (
                          <span style={{ color: 'var(--emergency)', fontWeight: 600 }}>
                            UGD 24 Jam
                          </span>
                        ) : (
                          <span style={{ color: 'var(--mute)' }}>Tidak tercatat di SIRS</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <th className="attr-col">Spesialisasi Medis (SIRS)</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.25rem' }}>
                        {(h.spesialisasi_sirs || []).map((s, idx) => (
                          <span key={idx} className="chip lay" style={{ fontSize: '.72rem', padding: '.15rem .45rem' }}>
                            {s}
                          </span>
                        ))}
                        {(!h.spesialisasi_sirs || !h.spesialisasi_sirs.length) && (
                          <span style={{ color: 'var(--mute)' }}>Belum ada catatan spesialisasi</span>
                        )}
                      </div>
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Layanan Diagnostik</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.25rem' }}>
                        {(h.layanan_terkurasi || []).map((l, idx) => (
                          <span
                            key={idx}
                            className="chip lay"
                            style={{ fontSize: '.72rem', padding: '.15rem .45rem', background: '#F8FAFC' }}
                          >
                            {l}
                          </span>
                        ))}
                        {(!h.layanan_terkurasi || !h.layanan_terkurasi.length) && (
                          <span style={{ color: 'var(--mute)' }}>Belum ada catatan diagnostik</span>
                        )}
                      </div>
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Fasilitas Fisik</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '.25rem' }}>
                        {(h.fasilitas || []).map((f, idx) => (
                          <span
                            key={idx}
                            className="chip fas-chip"
                            style={{ fontSize: '.72rem', padding: '.15rem .45rem' }}
                          >
                            {f}
                          </span>
                        ))}
                        {(!h.fasilitas || !h.fasilitas.length) && (
                          <span style={{ color: 'var(--mute)' }}>Belum tersedia</span>
                        )}
                      </div>
                    </td>
                  ))}
                </tr>
                <tr>
                  <th className="attr-col">Status BPJS</th>
                  {hs.map((h) => {
                    const bpjsOk = h.bpjs_info?.menerima_bpjs || h.bpjs;
                    return (
                      <td key={h.id}>
                        {bpjsOk ? (
                          <span style={{ color: '#0f766e', fontWeight: 600 }}>Menerima BPJS</span>
                        ) : (
                          <span style={{ color: '#b45309' }}>Konfirmasi ke RS</span>
                        )}
                      </td>
                    );
                  })}
                </tr>
                <tr>
                  <th className="attr-col">Profil Lengkap</th>
                  {hs.map((h) => (
                    <td key={h.id}>
                      <Link
                        className="btn btn-primary"
                        style={{ fontSize: '.74rem', padding: '.3rem .65rem' }}
                        to={`/rumah-sakit/${encodeURIComponent(h.id)}`}
                        onClick={onClose}
                      >
                        Lihat Detail Faskes
                      </Link>
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
