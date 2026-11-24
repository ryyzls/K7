import { useState } from 'react'; import { Link } from 'react-router-dom'; import { useApp } from '../context/AppContext'; import { cn, telHref, websiteHref } from '../utils';  function initials(name) { return String(name || 'RS') .split(/\s+/) .filter(Boolean) .slice(0, 2) .map((word) => word[0]) .join('') .toUpperCase(); }  export default function HospitalCard({ hospital, onRoute, compact = false, className = '', showSave = false, onSave, saved = false, }) { const { toggleCompare, isCompared } = useApp(); const [showSecondary, setShowSecondary] = useState(false); const detailHref = `/rumah-sakit/${encodeURIComponent(hospital.id)}`;
  const phone = telHref(hospital.telepon);
  const web = websiteHref(hospital.website);
  const hasCoordinates = hospital.lat != null && hospital.lon != null;
  const layanan = hospital.layanan || [];
  const fasilitas = hospital.fasilitas || [];
  const tags = [...new Set([...layanan, ...fasilitas])];
  const hasSecondaryActions = Boolean(phone || web || (hasCoordinates && onRoute) || tags.length);
  const compared = isCompared(hospital.id);

  return (
    <article
      className={cn(
        'group relative flex flex-col overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition-shadow duration-150 hover:shadow-md',
        className,
      )}
    >
      {/* Photo Header */}
      <div className={cn('relative w-full overflow-hidden bg-slate-100', compact ? 'h-40' : 'h-48')}>
        {hospital.foto ? (
          <img
            src={hospital.foto}
            alt={hospital.nama}
            loading="lazy"
            className="h-full w-full object-cover object-center"
            onError={(event) => {
              event.currentTarget.style.display = 'none';
            }}
          />
        ) : null}
        <div className="absolute inset-0 bg-gradient-to-t from-slate-950/60 via-slate-900/10 to-transparent" />

        {/* Top Badges */}
        <div className="pointer-events-none absolute left-3.5 right-3.5 top-3.5 flex items-center justify-between">
          {hospital.bpjs ? (
            <span className="pointer-events-auto inline-flex items-center gap-1 rounded-md bg-emerald-800 px-2 py-1 text-xs font-medium text-white">
              <span className="material-symbols-outlined text-base">check_circle</span>
              BPJS
            </span>
          ) : (
            <span />
          )}

          <div className="pointer-events-auto flex items-center gap-2">
            <span className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-700">
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
                  'flex h-8 w-8 items-center justify-center rounded-lg border transition-colors duration-150',
                  saved
                    ? 'border-rose-200 bg-rose-50 text-rose-600'
                    : 'border-slate-200 bg-white text-slate-600 hover:text-rose-600',
                )}
                aria-label={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
                title={saved ? 'Hapus dari favorit' : 'Simpan ke favorit'}
              >
                <span
                  className={cn('material-symbols-outlined text-base', saved && 'material-symbols-filled')}
                >
                  favorite
                </span>
              </button>
            ) : null}
          </div>
        </div>

        {/* Desktop Hover Action Pill */}
        {hasSecondaryActions ? (
          <div className="absolute inset-x-3.5 bottom-3 hidden translate-y-2 items-center justify-between gap-2 rounded-lg border border-white/20 bg-slate-900/90 px-3 py-2 text-white opacity-0 transition-[opacity,transform] duration-150 group-hover:translate-y-0 group-hover:opacity-100 md:flex">
            <span className="text-xs font-medium text-slate-300">Aksi cepat</span>
            <div className="flex items-center gap-2">
              {phone ? (
                <a
                  href={phone}
                  onClick={(e) => e.stopPropagation()}
                  className="flex h-7 w-7 items-center justify-center rounded-md bg-white/15 text-white transition-colors duration-150 hover:bg-white/25"
                  title={`Telepon: ${hospital.telepon}`} aria-label={`Telepon ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-sm">call</span>
                </a>
              ) : null}
              {web ? (
                <a
                  href={web}
                  target="_blank"
                  rel="noopener noreferrer"
                  onClick={(e) => e.stopPropagation()}
                  className="flex h-7 w-7 items-center justify-center rounded-md bg-white/15 text-white transition-colors duration-150 hover:bg-white/25"
                  title={`Kunjungi Website: ${hospital.nama}`} aria-label={`Website ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-sm">language</span>
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
                  className="flex h-7 w-7 items-center justify-center rounded-md bg-white/15 text-white transition-colors duration-150 hover:bg-white/25"
                  title="Buka rute navigasi"
                  aria-label={`Rute ke ${hospital.nama}`}
                >
                  <span className="material-symbols-outlined text-sm">directions</span>
                </button>
              ) : null}
            </div>
          </div>
        ) : null}

        {!hospital.foto ? (
          <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
            <span className="flex h-14 w-14 items-center justify-center rounded-lg bg-white text-lg font-medium text-slate-800">
              {initials(hospital.nama)}
            </span>
          </div>
        ) : null}
      </div>

      {/* Card Body */}
      <div className="flex flex-1 flex-col justify-between p-5">
        <div>
          <h3 className="line-clamp-2 text-base font-semibold leading-snug text-slate-900 transition-colors duration-150 group-hover:text-toba-dark">
            <Link to={detailHref} className="focus:outline-none">
              {hospital.nama}
            </Link>
          </h3>

          <div className="mt-3 flex items-start gap-2 text-xs text-slate-500">
            <span className="material-symbols-outlined mt-0.5 shrink-0 text-base text-slate-500">
              location_on
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate font-medium text-slate-700">
                {hospital.kabkota || 'Sumatera Utara'}
              </p>
              <p className="mt-1 line-clamp-1 text-xs text-slate-500">
                {hospital.alamat || hospital.jenis || 'Rumah Sakit'}
              </p>
            </div>
          </div>

          {showSecondary ? (
            <div className="mt-4 animate-fade-in space-y-2 rounded-xl border border-slate-100 bg-slate-50 p-3 text-xs">
              {hospital.telepon ? (
                <div className="flex items-center justify-between text-slate-600">
                  <span className="flex items-center gap-2 text-slate-500">
                    <span className="material-symbols-outlined text-sm">call</span>
                    Telepon:
                  </span>
                  <a href={phone} className="font-medium text-toba hover:underline">
                    {hospital.telepon}
                  </a>
                </div>
              ) : null}
              {tags.length ? (
                <div className="flex flex-wrap gap-1 border-t border-slate-200/50 pt-2">
                  {tags.slice(0, 3).map((tag) => (
                    <span
                      key={tag}
                      className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs text-slate-600"
                    >
                      {tag}
                    </span>
                  ))}
                  {tags.length > 3 ? (
                    <span                     className="rounded-md border border-slate-200 bg-white px-2 py-1 text-xs font-medium text-slate-500">
                      +{tags.length - 3} lagi
                    </span>
                  ) : null}
                </div>
              ) : null}
            </div>
          ) : null}
        </div>

        {/* Primary CTA Row */}
        <div className="mt-5 flex items-center gap-2 border-t border-slate-100 pt-4">
          <Link
            to={detailHref}
            className="inline-flex flex-1 items-center justify-center gap-1 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-700 transition-colors duration-150 hover:border-toba hover:bg-toba-mist hover:text-toba-dark"
          >
            <span>Lihat Detail</span>
            <span className="material-symbols-outlined text-base text-slate-400">arrow_forward</span>
          </Link>

          <button
            type="button"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              toggleCompare(hospital.id);
            }}
            className={cn(
              'inline-flex items-center justify-center gap-1 rounded-lg border px-3 py-2 text-xs font-medium transition-colors duration-150',
              compared
                ? 'border-toba bg-toba text-white'
                : 'border-toba/25 bg-toba-mist/70 text-toba-dark hover:bg-toba-soft',
            )}
            aria-pressed={compared}
            title={compared ? 'Hapus dari perbandingan' : 'Tambahkan ke perbandingan RS'}
          >
            <span className="material-symbols-outlined text-base">
              {compared ? 'check' : 'compare'}
            </span>
            <span>{compared ? 'Dipilih' : 'Bandingkan'}</span>
          </button>

          {hasSecondaryActions ? (
            <button
              type="button"
              onClick={() => setShowSecondary((prev) => !prev)}
              className={cn(
                'flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border transition-colors duration-150',
                showSecondary
                  ? 'border-toba bg-toba/10 text-toba-dark'
                  : 'border-slate-200 bg-white text-slate-500 hover:bg-slate-50 hover:text-slate-700',
              )}
              title={showSecondary ? 'Tutup info tambahan' : 'Tampilkan info tambahan'}
              aria-label="Info tambahan"
              aria-expanded={showSecondary}
            >
              <span className="material-symbols-outlined text-base">
                {showSecondary ? 'expand_less' : 'more_horiz'}
              </span>
            </button>
          ) : null}
        </div>
      </div>
    </article>
  );
}
