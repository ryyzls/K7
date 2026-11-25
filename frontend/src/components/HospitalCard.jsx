import { memo } from 'react';
import { Link, useNavigate } from 'react-router-dom';

const COLOR_MAP = {
  A: '#be123c',
  B: '#0284c7',
  C: '#059669',
  D: '#64748b',
};

export function colorOf(kelas) {
  return COLOR_MAP[kelas] || '#0f766e';
}

export default memo(function HospitalCard({
  hospital,
  onRoute,
  compact = false,
  className = '',
  showSave = false,
  onSave,
  saved = false,
  compareSelected = false,
  onCompareToggle,
  isSelected = false,
}) {
  const navigate = useNavigate();
  const c = colorOf(hospital.kelas);
  const detailUrl = `/rumah-sakit/${encodeURIComponent(hospital.id)}`;

  return (
    <article
      className={`card ${isSelected ? 'on' : ''} ${className}`}
      data-id={hospital.id}
      data-hospital-id={hospital.id}
      style={{ '--c': c }}
    >
      <div className="card-thumb" style={{ '--c': c }}>
        <div className="thumb-pattern" aria-hidden="true" />
        {hospital.foto && (
          <img
            className="card-thumb-img"
            src={hospital.foto}
            alt={hospital.nama}
            loading="lazy"
            decoding="async"
            onError={(e) => {
              e.currentTarget.style.display = 'none';
            }}
          />
        )}
      </div>

      <button
        type="button"
        className="card-main text-left"
        data-act="select"
        data-id={hospital.id}
        onClick={() => navigate(detailUrl)}
      >
        <h3 className="card-name">{hospital.nama}</h3>
        <div className="card-meta">
          <i className="fa-solid fa-location-dot" style={{ fontSize: '0.8rem', color: 'var(--mute)' }} aria-hidden="true" />
          <span>{hospital.kabkota || 'Wilayah tidak tersedia'}</span>
        </div>
        <div className="addr">
          <span>{hospital.alamat || 'Alamat belum tersedia'}</span>
        </div>
      </button>

      <div className="card-actions">
        <div className="card-facts">
          <span>
            {hospital.kelas ? `Kelas ${hospital.kelas}` : 'Kelas —'}
            <small>Kelas<br />Rumah&nbsp;Sakit</small>
          </span>
          <span>
            {hospital.jenis || '—'}
            <small>Jenis<br />Rumah&nbsp;Sakit</small>
          </span>
        </div>
        <div className="card-btn-group">
          {onCompareToggle && (
            <button
              className={`btn btn-compare ${compareSelected ? 'on' : ''}`}
              type="button"
              aria-pressed={compareSelected}
              onClick={(e) => {
                e.stopPropagation();
                onCompareToggle(hospital.id);
              }}
              title="Pilih untuk perbandingan"
            >
              <i className="fa-solid fa-code-compare" aria-hidden="true" />{' '}
              <span>{compareSelected ? 'Dipilih' : 'Bandingkan'}</span>
            </button>
          )}
          <Link className="btn btn-primary" to={detailUrl}>
            Lihat Detail
          </Link>
          {onRoute && hospital.lat != null && hospital.lon != null && (
            <button
              type="button"
              className="btn btn-ghost"
              onClick={(e) => {
                e.stopPropagation();
                onRoute(hospital);
              }}
            >
              Rute
            </button>
          )}
        </div>
      </div>
    </article>
  );
});
