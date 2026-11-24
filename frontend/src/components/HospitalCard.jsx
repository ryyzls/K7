import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useApp } from '../context/AppContext';
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
  const { toggleCompare, isCompared } = useApp();
  const [showSecondary, setShowSecondary] = useState(false);

  const detailHref = `/rumah-sakit/${encodeURIComponent(hospital.id)}`;
  const phone = telHref(hospital.telepon);
  const web = websiteHref(hospital.website);
  const hasCoordinates = hospital.lat != null && hospital.lon != null;
  const layanan = hospital.layanan || [];
  const fasilitas = hospital.fasilitas || [];
  const tags = [...new Set([...layanan, ...fasilitas])];
  const hasSecondaryActions = Boolean(phone || web || (hasCoordinates && onRoute) || tags.length > 3);
  const compared = isCompared(hospital.id);

  return (
    <article
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200/90 bg-white shadow-card transition-all duration-300 hover:-translate-y-0.5 hover:border-toba/35 hover:shadow-floating',
        className,
      )}
    >
      {/* Photo Header */}
      <div className={cn('relative w-full overflow-hidden bg-slate-100', compact ? 'h-40' : 'h-48')}>
        <Link to={detailHref} className="block h-full w-full focus:outline-none" tabIndex={-1}>
          {hospital.foto ? (
            <img
              src={hospital.foto}
              alt={hospital.nama}
              loading="lazy"
              className="h-full w-full object-cover object-center transition-transform duration-500 ease-out group-hover:scale-105"
              onError={(event) => {
                event.currentTarget.style.display = 'none';
              }}
            />
          ) : null}
          <div className="absolute inset-0 bg-gradient-to-t from-slate-950/65 via-slate-900/15 to-transparent" />

          {!hospital.foto ? (
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-white/95 text-lg font-bold text-toba-dark shadow-sm">
                {initials(hospital.nama)}
              </span>
            </div>
          ) : null}
        </Link>

        {/* Top Badges */}
        <div className="pointer-events-none absolute left-3.5 right-3.5 top-3.5 z-10 flex items-center justify-between">
          {hospital.bpjs ? (
            <span className="pointer-events-auto inline-flex items-center gap-1 rounded-full bg-emerald-600/95 px-2.5 py-1 text-[11px] font-bold text-white shadow-sm backdrop-blur-sm">
              <span className="material-symbols-outlined text-[14px]">check_circle</span>
              BPJS
            </span>
          ) : (
            <span />
          )}

          <div className="pointer-events-auto flex items-center gap-1.5">
            <span className="rounded-full bg-white/95 px-2.5 py-1 text-[11px] font-bold text-slate-800 shadow-sm backdrop-blur-sm">
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
                  'flex h-8 w-8 items-center justify-center rounded-full shadow-sm backdrop-blur-sm transition-all hover:scale-105',
                  saved
                    ? 'bg-rose-500 text-white'
                    : 'bg-white/95 text-slate-600 hover:text-rose-600',
                )}
                aria-label={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
                title={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
              >
                <span
                  className={cn('material-symbols-outlined text-[16px]', saved && 'material-symbols-filled')}
                >
                  favorite
                </span>
              </button>
            ) : null}
          </div>
        </div>

        {/* Desktop Hover Action Pill */}
        {phone || web || (hasCoordinates && onRoute) ? (
          <div className="absolute inset-x-3.5 bottom-3 z-10 hidden translate-y-2 items-center justify-between gap-2 rounded-full border border-white/20 bg-slate-900/85 px-3.5 py-1.5 text-white opacity-0 backdrop-blur-md transition-all duration-200 group-hover:translate-y-0 group-hover:opacity-100 md:flex">
            <span className="text-[11px] font-semibold text-slate-200">Aksi Cepat</span>
            <div className="flex items-center gap-1.5">
              {phone ? (
                <a
                  href={phone}
                  onClick={(e) => e.stopPropagation()}
                  className="flex h-7 w-7 items-center justify-center rounded-full bg-white/15 text-white transition-colors hover:bg-toba"
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
                  className="flex h-7 w-7 items-center justify-center rounded-full bg-white/15 text-white transition-colors hover:bg-toba"
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
                  className="flex h-7 w-7 items-center justify-center rounded-full bg-white/15 text-white transition-colors hover:bg-toba"
                  title="Buka rute navigasi"
                  aria-label={`Rute ke ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-[14px]">directions</span>
                </button>
              ) : null}
            </div>
          </div>
        ) : null}
      </div>

      {/* Card Body */}
      <div className="flex flex-1 flex-col justify-between p-5">
        <div>
          <h3 className="line-clamp-2 font-heading text-base font-bold leading-snug text-slate-900 transition-colors duration-150 group-hover:text-toba-dark">
            <Link to={detailHref} className="focus:outline-none">
              {hospital.nama}
            </Link>
          </h3>

          <div className="mt-2.5 flex items-start gap-1.5 text-xs text-slate-500">
            <span className="material-symbols-outlined mt-0.5 shrink-0 text-[16px] text-toba">
              location_on
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-semibold text-slate-700">
                {hospital.kabkota || 'Sumatera Utara'}
              </p>
              <p className="mt-0.5 line-clamp-1 text-xs text-slate-500">
                {hospital.alamat || hospital.jenis || 'Rumah Sakit'}
              </p>
            </div>
          </div>

          {/* Direct Service & Facility Pills */}
          {tags.length > 0 ? (
            <div className="mt-3.5 flex flex-wrap gap-1.5">
              {tags.slice(0, 3).map((tag) => (
                <span
                  key={tag}
                  className="rounded-full border border-slate-200/90 bg-slate-50 px-2.5 py-0.5 text-[11px] font-medium text-slate-600"
                >
                  {tag}
                </span>
              ))}
              {tags.length > 3 ? (
                <span className="rounded-full bg-toba-mist px-2.5 py-0.5 text-[11px] font-semibold text-toba-dark">
                  +{tags.length - 3} layanan
                </span>
              ) : null}
            </div>
          ) : null}

          {showSecondary ? (
            <div className="mt-3.5 animate-fade-in space-y-2 rounded-xl border border-slate-100 bg-slate-50/90 p-3 text-xs">
              {hospital.telepon ? (
                <div className="flex items-center justify-between text-slate-600">
                  <span className="flex items-center gap-1.5 text-slate-500">
                    <span className="material-symbols-outlined text-[15px]">call</span>
                    Telepon:
                  </span>
                  <a href={phone} className="font-semibold text-toba-dark hover:underline">
                    {hospital.telepon}
                  </a>
                </div>
              ) : null}
              {tags.length > 3 ? (
                <div className="flex flex-wrap gap-1 border-t border-slate-200/60 pt-2">
                  {tags.slice(3, 8).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-full border border-slate-200 bg-white px-2 py-0.5 text-[11px] text-slate-600"
                    >
                      {tag}
                    </span>
                  ))}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        {/* Primary CTA Row */}
        <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4">
          <Link
            to={detailHref}
            className="group/btn inline-flex flex-1 items-center justify-center gap-1.5 rounded-full border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 transition-all duration-150 hover:border-toba hover:bg-toba hover:text-white"
          >
            <span>Lihat Detail</span>
            <span className="material-symbols-outlined text-[15px] transition-transform duration-150 group-hover/btn:translate-x-0.5">
              arrow_forward
            </span>
          </Link>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggleCompare(hospital.id);
            }}
            className={cn(
              'inline-flex items-center justify-center gap-1.5 rounded-full border px-3.5 py-2 text-xs font-semibold transition-all duration-150',
              compared
                ? 'border-toba bg-toba text-white shadow-sm'
                : 'border-toba/25 bg-toba-mist/80 text-toba-dark hover:bg-toba-soft',
            )}
            aria-pressed={compared}
            title={compared ? 'Hapus dari perbandingan' : 'Tambahkan ke perbandingan RS'}
          >
            <span className="material-symbols-outlined text-[15px]">
              {compared ? 'check' : 'compare'}
            </span>
            <span>{compared ? 'Dipilih' : 'Bandingkan'}</span>
          </button>

          {hasSecondaryActions ? (
            <button
              type="button"
              onClick={() => setShowSecondary((prev) => !prev)}
              className={cn(
                'flex h-8 w-8 shrink-0 items-center justify-center rounded-full border transition-colors duration-150',
                showSecondary
                  ? 'border-toba bg-toba/10 text-toba-dark'
                  : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700',
              )}
              title={showSecondary ? 'Tutup info tambahan' : 'Tampilkan info tambahan'}
              aria-label="Info tambahan"
              aria-expanded={showSecondary}
            >
              <span className="material-symbols-outlined text-[16px]">
                {showSecondary ? 'expand_less' : 'more_horiz'}
              </span>
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
