import { Link } from 'react-router-dom';
import { cn } from '../utils';

export function BrandMark({ dark = false, compact = false, subtitle = 'Direktori Rumah Sakit Sumut' }) {
  return (
    <Link
      to="/"
      className={cn(
        'group flex items-center gap-2.5 focus:outline-none',
        dark ? 'text-white' : 'text-toba-dark',
      )}
      aria-label="CariSehat, beranda"
    >
      <span
        className={cn(
          'flex shrink-0 items-center justify-center overflow-hidden rounded-xl border bg-white p-1 shadow-sm',
          compact ? 'h-9 w-9 border-toba/25' : 'h-10 w-10 border-toba/25',
        )}
      >
        <img
          src="/images/cari-sehat-icon.png"
          alt="Logo CariSehat"
          className="h-full w-full object-contain"
        />
      </span>
      <span className="flex flex-col">
        <span
          className={cn(
            'font-extrabold leading-none tracking-tight',
            compact ? 'text-lg' : 'text-[20px]',
          )}
        >
          Cari<span className={dark ? 'text-toba-soft' : 'text-toba'}>Sehat</span>
        </span>
        {!compact && (
          <span
            className={cn(
              'mt-1 text-[10px] font-semibold uppercase tracking-[0.14em]',
              dark ? 'text-toba-soft/80' : 'text-slate-400',
            )}
          >
            {subtitle}
          </span>
        )}
      </span>
    </Link>
  );
}
