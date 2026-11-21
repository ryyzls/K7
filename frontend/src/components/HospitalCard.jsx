import { Link } from 'react-router-dom';
import { cn, telHref } from '../utils';

function initials(name) {
  return String(name || 'RS')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join('')
    .toUpperCase();
}

export default function HospitalCard({
  hospital,
  onRoute,
  compact = false,
  className = '',
  showSave = false,
  onSave,
  saved = false,
}) {
  const layanan = hospital.layanan || [];
  const fasilitas = hospital.fasilitas || [];
  const tags = [...new Set([...layanan, ...fasilitas])];
  const shown = tags.slice(0, compact ? 2 : 3);
  const detailHref = `/rumah-sakit/${encodeURIComponent(hospital.id)}`;
  const phone = telHref(hospital.telepon);

  return (
    <article
      className={cn(
        'group flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:shadow-floating',
        className,
      )}
    >
      <div className={cn('relative w-full overflow-hidden bg-slate-100', compact ? 'h-40' : 'h-[185px]')}>
        {hospital.foto ? (
          <img
            src={hospital.foto}
            alt={hospital.nama}
            loading="lazy"
            className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-105"
            onError={(event) => {
              event.currentTarget.style.display = 'none';
            }}
          />
        ) : null}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/55 via-slate-900/5 to-transparent" />

        <span className="absolute right-3 top-3 rounded-full border border-white/30 bg-white/95 px-2.5 py-0.5 text-[11px] font-semibold text-slate-800 shadow-sm backdrop-blur">
          Kelas {hospital.kelas || '—'}
        </span>

        {hospital.bpjs ? (
          <span className="absolute left-3 top-3 inline-flex items-center gap-1 rounded-full bg-emerald-600/95 px-2.5 py-0.5 text-[10px] font-bold uppercase tracking-wide text-white shadow-sm backdrop-blur">
            <span className="material-symbols-outlined text-[12px]">verified</span>
            BPJS
          </span>
        ) : (
          <span className="absolute left-3 top-3 rounded-full bg-slate-900/70 px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-white backdrop-blur">
            Konfirmasi BPJS
          </span>
        )}

        <div className="absolute bottom-3 left-3 flex items-center gap-1.5 text-[11px] font-medium text-white/90">
          <span className="material-symbols-outlined text-[15px]">location_on</span>
          <span className="line-clamp-1">{hospital.kabkota || 'Sumatera Utara'}</span>
        </div>

        {showSave ? (
          <button
            type="button"
            onClick={onSave}
            className={cn(
              'absolute bottom-2.5 right-3 flex h-8 w-8 items-center justify-center rounded-full border backdrop-blur transition-colors',
              saved
                ? 'border-rose-200 bg-rose-50 text-rose-600'
                : 'border-white/40 bg-white/85 text-slate-600 hover:text-rose-600',
            )}
            aria-label={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
            title={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
          >
            <span
              className={cn('material-symbols-outlined text-[17px]', saved && 'material-symbols-filled')}
            >
              favorite
            </span>
          </button>
        ) : null}

        {!hospital.foto ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/85 text-lg font-extrabold text-brand-navy shadow-sm">
              {initials(hospital.nama)}
            </span>
          </div>
        ) : null}
      </div>

      <div className="flex flex-1 flex-col justify-between p-5">
        <div>
          <div className="mb-1.5 flex items-start gap-2">
            <h3 className="line-clamp-2 flex-1 text-[17px] font-bold leading-snug text-slate-900">
              <Link to={detailHref} className="transition-colors hover:text-brand-blue">
                {hospital.nama}
              </Link>
            </h3>
          </div>

          <div className="mb-2 flex items-center justify-between gap-2 text-xs text-slate-500">
            <span className="truncate">
              {hospital.jenis || 'Rumah Sakit'} • {hospital.kabkota || 'Wilayah belum tersedia'}
            </span>
            {hospital.bpjs ? (
              <span className="inline-flex shrink-0 items-center gap-0.5 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-semibold text-emerald-600">
                <span className="material-symbols-outlined text-[12px]">check_circle</span>
                BPJS
              </span>
            ) : null}
          </div>

          <p className="mb-4 line-clamp-1 text-xs text-slate-500">
            {hospital.alamat || 'Alamat belum tersedia'}
          </p>

          {shown.length ? (
            <div className="flex flex-wrap gap-1.5">
              {shown.map((tag) => (
                <span
                  key={tag}
                  className="rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-medium text-slate-600"
                >
                  {tag}
                </span>
              ))}
              {tags.length > shown.length ? (
                <span className="rounded-md bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-500">
                  +{tags.length - shown.length}
                </span>
              ) : null}
            </div>
          ) : null}
        </div>

        <div className="mt-4 flex items-center gap-2.5 border-t border-slate-100 pt-4">
          <Link
            to={detailHref}
            className="inline-flex flex-1 items-center justify-center gap-1 rounded-full border border-slate-300 px-3 py-2 text-xs font-semibold text-slate-800 transition hover:bg-slate-50"
          >
            <span className="material-symbols-outlined text-[14px]">info</span>
            Lihat Detail
          </Link>
          {phone ? (
            <a
              href={phone}
              className="inline-flex items-center justify-center gap-1 rounded-full border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-600 transition hover:bg-slate-50"
              title={`Telepon ${hospital.telepon}`}
              aria-label={`Telepon ${hospital.nama}`}
            >
              <span className="material-symbols-outlined text-[14px]">call</span>
            </a>
          ) : null}
          <button
            type="button"
            onClick={() => onRoute?.(hospital)}
            className="inline-flex items-center justify-center gap-1 rounded-full bg-brand-blue px-4 py-2 text-xs font-semibold text-white transition hover:bg-brand-navy disabled:cursor-not-allowed disabled:opacity-50"
            disabled={hospital.lat == null || hospital.lon == null}
            title={hospital.lat == null ? 'Koordinat belum tersedia' : 'Buka rute ke rumah sakit'}
          >
            <span className="material-symbols-outlined text-[14px]">directions</span>
            Rute
          </button>
        </div>
      </div>
    </article>
  );
}
