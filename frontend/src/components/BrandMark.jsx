import { Link } from 'react-router-dom';
import { cn } from '../utils';

export function BrandMark({ dark = false, compact = false, subtitle = 'Sistem Temu Medis Semantik' }) {
  return (
    <Link
      to="/"
      className={cn(
        'group flex items-center gap-2.5 focus:outline-none',
        dark ? 'text-white' : 'text-brand-navy',
      )}
      aria-label="CariSehat, beranda"
    >
      <span
        className={cn(
          'flex shrink-0 items-center justify-center overflow-hidden rounded-full shadow-md',
          compact ? 'h-9 w-9' : 'h-10 w-10',
          dark ? 'bg-white' : 'bg-gradient-to-tr from-brand-navy to-brand-blue',
        )}
      >
        <img
          src="/images/cari-sehat-icon.png"
          alt=""
          className={cn('h-full w-full object-cover', dark ? 'opacity-100' : 'brightness-0 invert')}
        />
      </span>
      <span className="flex flex-col">
        <span
          className={cn(
            'font-heading font-extrabold leading-none tracking-tight',
            compact ? 'text-lg' : 'text-[20px]',
          )}
        >
          Cari<span className={dark ? 'text-emerald-300' : 'text-brand-blue'}>Sehat</span>
        </span>
        {!compact && (
          <span
            className={cn(
              'mt-1 text-[10px] font-semibold uppercase tracking-[0.14em]',
              dark ? 'text-slate-300' : 'text-slate-400',
            )}
          >
            {subtitle}
          </span>
        )}
      </span>
    </Link>
  );
}
