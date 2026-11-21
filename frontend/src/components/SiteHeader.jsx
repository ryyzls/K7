import { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import { cn } from '../utils';
import { BrandMark } from './BrandMark';

function SearchField({ initialQuery = '', compact = false, onSubmit, autoFocus = false }) {
  const [value, setValue] = useState(initialQuery);
  const inputRef = useRef(null);

  useEffect(() => {
    setValue(initialQuery);
  }, [initialQuery]);

  useEffect(() => {
    if (autoFocus) inputRef.current?.focus();
  }, [autoFocus]);

  return (
    <form
      className="relative flex w-full items-center"
      onSubmit={(event) => {
        event.preventDefault();
        onSubmit?.(value.trim());
      }}
      role="search"
    >
      <span className="pointer-events-none absolute left-3.5 flex items-center text-slate-400">
        <span className="material-symbols-outlined text-[19px]">search</span>
      </span>
      <input
        ref={inputRef}
        value={value}
        onChange={(event) => setValue(event.target.value)}
        className={cn(
          'w-full rounded-full border border-transparent bg-slate-100 pl-10 pr-10 font-medium text-slate-800 outline-none transition-all placeholder:text-slate-400 hover:bg-slate-200/80 focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/20',
          compact ? 'py-2 text-xs' : 'py-2.5 text-sm',
        )}
        placeholder="Cari rumah sakit, spesialisasi, atau lokasi..."
        type="search"
        aria-label="Cari rumah sakit, spesialisasi, atau lokasi"
      />
      {value ? (
        <button
          type="button"
          className="absolute right-3 flex items-center text-slate-400 transition-colors hover:text-slate-700"
          onClick={() => {
            setValue('');
            inputRef.current?.focus();
          }}
          title="Hapus pencarian"
          aria-label="Hapus pencarian"
        >
          <span className="material-symbols-outlined text-[18px]">close</span>
        </button>
      ) : null}
    </form>
  );
}

export default function SiteHeader({
  active = '',
  initialQuery = '',
  showSearch = true,
  onFilterClick = null,
  filterActive = false,
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, openLogin, logout } = useApp();
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountOpen, setAccountOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
    setAccountOpen(false);
  }, [location.pathname, location.search]);

  const goSearch = (value) => {
    const params = new URLSearchParams(location.pathname === '/pencarian' ? location.search : '');
    if (value) params.set('q', value);
    else params.delete('q');
    params.delete('page');
    navigate(`/pencarian${params.toString() ? `?${params.toString()}` : ''}`);
  };

  const navItems = [
    { label: 'Beranda', to: '/', id: 'beranda' },
    { label: 'Direktori', to: '/pencarian', id: 'direktori' },
    { label: 'Peta', to: '/peta', id: 'peta' },
  ];

  return (
    <header className="sticky top-0 z-40 h-16 shrink-0 border-b border-slate-200 bg-white/95 backdrop-blur-md">
      <div className="mx-auto flex h-full max-w-[1400px] items-center justify-between gap-3 px-4 lg:px-6">
        <div className="shrink-0">
          <BrandMark compact />
        </div>

        {showSearch && (
          <div className="hidden max-w-2xl flex-1 items-center gap-2.5 md:flex">
            <SearchField initialQuery={initialQuery} onSubmit={goSearch} />
            <button
              type="button"
              onClick={onFilterClick}
              className={cn(
                'inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full border px-4 py-2.5 text-xs font-semibold shadow-sm transition-colors',
                filterActive
                  ? 'border-brand-blue bg-brand-blue text-white'
                  : 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200/80',
              )}
              title="Buka panel filter"
            >
              <span className="material-symbols-outlined text-[16px]">tune</span>
              <span>Filter</span>
            </button>
          </div>
        )}

        <nav className="hidden items-center gap-1 lg:flex" aria-label="Navigasi utama">
          {navItems.map((item) => (
            <button
              key={item.id}
              type="button"
              onClick={() => navigate(item.to)}
              className={cn(
                'rounded-full px-3 py-2 text-sm font-medium transition-colors',
                active === item.id
                  ? 'bg-slate-100 text-brand-navy'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-brand-navy',
              )}
            >
              {item.label}
            </button>
          ))}
        </nav>

        <div className="flex shrink-0 items-center gap-2">
          {!user ? (
            <button
              type="button"
              onClick={openLogin}
              className="inline-flex items-center gap-1.5 rounded-full bg-brand-navy px-4 py-2 text-xs font-semibold text-white shadow-sm transition-all hover:bg-[#021f42]"
            >
              <span className="material-symbols-outlined text-[16px]">person</span>
              <span className="hidden sm:inline">Masuk / Registrasi</span>
              <span className="sm:hidden">Masuk</span>
            </button>
          ) : (
            <div className="relative">
              <button
                type="button"
                onClick={() => setAccountOpen((current) => !current)}
                className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-navy text-xs font-bold text-white shadow-sm"
                aria-label="Menu akun"
              >
                {user.name?.charAt(0) || 'C'}
              </button>
              {accountOpen && (
                <div className="absolute right-0 top-11 w-52 animate-fade-in rounded-xl border border-slate-200 bg-white p-2 shadow-floating">
                  <p className="px-2 py-1.5 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
                    Sesi simulasi
                  </p>
                  <p className="px-2 pb-2 text-xs text-slate-600">Masuk via {user.provider}</p>
                  <button
                    type="button"
                    onClick={logout}
                    className="w-full rounded-lg px-2 py-2 text-left text-xs font-semibold text-rose-600 hover:bg-rose-50"
                  >
                    Keluar
                  </button>
                </div>
              )}
            </div>
          )}
          <button
            type="button"
            className="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 text-slate-600 lg:hidden"
            onClick={() => setMenuOpen((current) => !current)}
            aria-label="Buka menu navigasi"
            aria-expanded={menuOpen}
          >
            <span className="material-symbols-outlined text-[20px]">
              {menuOpen ? 'close' : 'menu'}
            </span>
          </button>
        </div>
      </div>

      {menuOpen && (
        <div className="border-t border-slate-100 bg-white px-4 py-3 shadow-soft lg:hidden">
          {showSearch && (
            <div className="mb-3 md:hidden">
              <SearchField initialQuery={initialQuery} onSubmit={goSearch} compact />
            </div>
          )}
          <div className="grid gap-1">
            {navItems.map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() => navigate(item.to)}
                className={cn(
                  'rounded-lg px-3 py-2 text-left text-sm font-semibold',
                  active === item.id ? 'bg-slate-100 text-brand-navy' : 'text-slate-600',
                )}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </header>
  );
}
