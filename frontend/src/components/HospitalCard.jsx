import { useState } from 'react';
import { Link } from 'react-router-dom';
import { cn, telHref, websiteHref } from '../utils';

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
  const [showSecondary, setShowSecondary] = useState(false);
  const detailHref = `/rumah-sakit/${encodeURIComponent(hospital.id)}`;
  const phone = telHref(hospital.telepon);
  const web = websiteHref(hospital.website);
  const hasCoordinates = hospital.lat != null && hospital.lon != null;
  const layanan = hospital.layanan || [];
  const fasilitas = hospital.fasilitas || [];
  const tags = [...new Set([...layanan, ...fasilitas])];
  const hasSecondaryActions = Boolean(phone || web || (hasCoordinates && onRoute) || tags.length);

  return (
    <article
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-card transition-all duration-300 hover:-translate-y-1 hover:border-slate-300 hover:shadow-floating',
        className,
      )}
    >
      {/* Photo Header */}
      <div className={cn('relative w-full overflow-hidden bg-slate-100', compact ? 'h-40' : 'h-[190px]')}>
        {hospital.foto ? (
          <img
            src={hospital.foto}
            alt={hospital.nama}
            loading="lazy"
            className="h-full w-full object-cover object-center transition-transform duration-500 group-hover:scale-[1.03]"
            onError={(event) => {
              event.currentTarget.style.display = 'none';
            }}
          />
        ) : null}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-slate-900/10 to-transparent" />

        {/* Top Badges (Minimal & Non-intrusive) */}
        <div className="absolute left-3.5 right-3.5 top-3.5 flex items-center justify-between pointer-events-none">
          {hospital.bpjs ? (
            <span className="pointer-events-auto inline-flex items-center gap-1 rounded-full bg-emerald-700/90 px-2.5 py-0.5 text-[10.5px] font-semibold text-white shadow-sm backdrop-blur-sm">
              <span className="material-symbols-outlined text-[13px]">check_circle</span>
              BPJS
            </span>
          ) : (
            <span />
          )}

          <div className="pointer-events-auto flex items-center gap-1.5">
            <span className="rounded-full border border-white/40 bg-white/95 px-2.5 py-0.5 text-[11px] font-semibold text-slate-800 shadow-sm backdrop-blur-sm">
              Kelas {hospital.kelas || '—'}
            </span>

            {showSave ? (
              <button
                type="button"
                onClick={(e) => {
                  e.preventDefault();
                  e.stopPropagation();
                  onSave?.();
                }}
                className={cn(
                  'flex h-7 w-7 items-center justify-center rounded-full border shadow-sm backdrop-blur-sm transition-colors',
                  saved
                    ? 'border-rose-200 bg-rose-50 text-rose-600'
                    : 'border-white/40 bg-white/90 text-slate-600 hover:text-rose-600',
                )}
                aria-label={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
                title={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
              >
                <span
                  className={cn('material-symbols-outlined text-[15px]', saved && 'material-symbols-filled')}
                >
                  favorite
                </span>
              </button>
            ) : null}
          </div>
        </div>

        {/* Desktop Hover Action Pill: Floating Quick Actions */}
        {hasSecondaryActions ? (
          <div className="absolute inset-x-3.5 bottom-3 hidden md:flex items-center justify-between gap-2 rounded-xl border border-white/30 bg-slate-900/85 px-3 py-1.5 text-white shadow-lg backdrop-blur-md opacity-0 translate-y-1.5 transition-all duration-300 group-hover:opacity-100 group-hover:translate-y-0">
            <span className="text-[11px] font-medium text-slate-300">Aksi Cepat:</span>
            <div className="flex items-center gap-1">
              {phone ? (
                <a
                  href={phone}
                  onClick={(e) => e.stopPropagation()}
                  className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/15 text-white transition hover:bg-emerald-600"
                  title={`Telepon: ${hospital.telepon}`}
                  aria-label={`Telepon ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-[14px]">call</span>
                </a>
              ) : null}
              {web ? (
                <a
                  href={web}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/15 text-white transition hover:bg-sky-600"
                  title={`Kunjungi Website: ${hospital.nama}`}
                  aria-label={`Website ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-[14px]">language</span>
                </a>
              ) : null}
              {hasCoordinates && onRoute ? (
                <button
                  type="button"
                  onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    onRoute?.(hospital);
                  }}
                  className="flex h-7 w-7 items-center justify-center rounded-lg bg-white/15 text-white transition hover:bg-brand-blue"
                  title="Buka rute navigasi"
                  aria-label={`Rute ke ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-[14px]">directions</span>
                </button>
              ) : null}
            </div>
          </div>
        ) : null}

        {!hospital.foto ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/85 text-lg font-extrabold text-brand-navy shadow-sm">
              {initials(hospital.nama)}
            </span>
          </div>
        ) : null}
      </div>

      {/* Card Body with Generous Padding */}
      <div className="flex flex-1 flex-col justify-between p-6">
        <div>
          {/* Hospital Name (Clear, Readable) */}
          <h3 className="line-clamp-2 text-[17px] font-bold leading-snug text-slate-900 transition-colors group-hover:text-brand-blue">
            <Link to={detailHref} className="focus:outline-none">
              {hospital.nama}
            </Link>
          </h3>

          {/* Location Focus (Clean, Spacious) */}
          <div className="mt-3 flex items-start gap-2 text-xs text-slate-500">
            <span className="material-symbols-outlined text-[17px] text-brand-blue shrink-0 mt-0.5">
              location_on
            </span>
            <div className="min-w-0 flex-1">
              <p className="font-semibold text-slate-700 truncate">
                {hospital.kabkota || 'Sumatera Utara'}
              </p>
              <p className="mt-0.5 line-clamp-1 text-[11.5px] text-slate-400">
                {hospital.alamat || hospital.jenis || 'Rumah Sakit'}
              </p>
            </div>
          </div>

          {/* Click State Disclosure: Secondary Details (Kontak, Fasilitas) */}
          {showSecondary ? (
            <div className="mt-4 space-y-2.5 rounded-xl border border-slate-100 bg-slate-50/90 p-3.5 text-xs animate-fade-in">
              {hospital.telepon ? (
                <div className="flex items-center justify-between text-slate-600">
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <span className="material-symbols-outlined text-[14px]">call</span>
                    Telepon:
                  </span>
                  <a href={phone} className="font-medium text-brand-blue hover:underline">
                    {hospital.telepon}
                  </a>
                </div>
              ) : null}
              {hospital.website ? (
                <div className="flex items-center justify-between text-slate-600">
                  <span className="flex items-center gap-1.5 text-slate-400">
                    <span className="material-symbols-outlined text-[14px]">language</span>
                    Website:
                  </span>
                  <a
                    href={web}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="max-w-[140px] truncate font-medium text-brand-blue hover:underline"
                  >
                    Buka situs resmi
                  </a>
                </div>
              ) : null}
              {tags.length ? (
                <div className="flex flex-wrap gap-1 pt-1.5 border-t border-slate-200/50">
                  {tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md border border-slate-200/60 bg-white px-2 py-0.5 text-[10.5px] text-slate-600"
                    >
                      {tag}
                    </span>
                  ))}
                  {tags.length > 3 ? (
                    <span className="rounded-md border border-slate-200/60 bg-white px-2 py-0.5 text-[10.5px] font-medium text-slate-500">
                      +{tags.length - 3} lagi
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        {/* Primary CTA Row */}
        <div className="mt-6 flex items-center gap-2 border-t border-slate-100 pt-4">
          <Link
            to={detailHref}
            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-slate-900 py-2.5 px-4 text-xs font-semibold text-white shadow-sm transition hover:bg-brand-blue"
          >
            <span>Lihat Detail</span>
            <span className="material-symbols-outlined text-[15px]">arrow_forward</span>
          </Link>

          {/* Secondary Info Toggle (Click State for Mobile & Quick Glance) */}
          {hasSecondaryActions ? (
            <button
              type="button"
              onClick={() => setShowSecondary((prev) => !prev)}
              className={cn(
                'flex h-[38px] w-[38px] shrink-0 items-center justify-center rounded-xl border transition-colors',
                showSecondary
                  ? 'border-brand-blue bg-brand-blue/10 text-brand-blue'
                  : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700',
              )}
              title={showSecondary ? 'Tutup info tambahan' : 'Tampilkan kontak & opsi tambahan'}
              aria-label="Info tambahan"
              aria-expanded={showSecondary}
            >
              <span className="material-symbols-outlined text-[17px]">
                {showSecondary ? 'expand_less' : 'more_horiz'}
              </span>
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
