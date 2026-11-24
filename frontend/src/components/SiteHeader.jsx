import { useEffect, useState } from 'react';
import EmergencyRadarModal from './EmergencyRadarModal';

import ETicketModal from './ETicketModal';


import { useLocation, useNavigate } from 'react-router-dom';

import { useApp } from '../context/AppContext';

import { cn } from '../utils';

import { BrandMark } from './BrandMark';



export default function SiteHeader({ active = '' }) {

  const navigate = useNavigate();

  const location = useLocation();

  const { user, openLogin, logout, compareIds, setCompareModalOpen } = useApp();

  const [menuOpen, setMenuOpen] = useState(false);

  const [accountOpen, setAccountOpen] = useState(false);

  const [radarOpen, setRadarOpen] = useState(false);

  const [ticketOpen, setTicketOpen] = useState(false);



  useEffect(() => {

    setMenuOpen(false);

    setAccountOpen(false);

  }, [location.pathname, location.search]);



  const navItems = [

    { label: 'Beranda', to: '/', id: 'beranda' },

    { label: 'Direktori', to: '/pencarian', id: 'direktori' },

    { label: 'Peta', to: '/peta', id: 'peta' },

    { label: 'Peringkat RS', to: '/peringkat', id: 'peringkat' },

    ...(user ? [{ label: 'Dashboard Pasien', to: '/dashboard', id: 'dashboard' }] : []),

  ];



  return (

    <>

      <header className="sticky top-0 z-[1200] shrink-0 border-b border-slate-200 bg-white">

      <div className="mx-auto flex h-16 max-w-[1400px] items-center justify-between gap-3 px-4 lg:px-6">

        <div className="shrink-0">

          <BrandMark compact />

        </div>



        <nav className="hidden items-center gap-1 lg:flex" aria-label="Navigasi utama">

          {navItems.map((item) => (

            <button

              key={item.id}

              type="button"

              onClick={() => navigate(item.to)}

              className={cn(

                'rounded-full px-3.5 py-2 text-sm font-semibold transition-colors duration-150',

                active === item.id

                  ? 'bg-toba-mist text-toba-dark ring-1 ring-toba/25'

                  : 'text-slate-600 hover:bg-slate-100 hover:text-toba-dark',

              )}

            >

              {item.label}

            </button>

          ))}

        </nav>



        <div className="flex shrink-0 items-center gap-2">

          <button

            type="button"

            onClick={() => setRadarOpen(true)}

            className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3 py-2 text-xs font-bold text-rose-700 transition hover:bg-rose-600 hover:text-white"

            title="Radar Darurat IGD & Sisa Bed ICU Terdekat"

          >

            <span className="material-symbols-outlined text-[16px]">emergency</span>

            <span className="hidden md:inline">Darurat IGD</span>

          </button>



          <button

            type="button"

            onClick={() => setTicketOpen(true)}

            className="inline-flex items-center gap-1.5 rounded-full border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-toba hover:text-toba-dark"

            title="Cek E-Ticket Booking Kamar atau Antrean Poli"

          >

            <span className="material-symbols-outlined text-[16px] text-toba">qr_code_2</span>

            <span className="hidden sm:inline">Cek Tiket</span>

          </button>

          {compareIds.length > 0 ? (

            <button

              type="button"

              onClick={() => setCompareModalOpen(true)}

              className="inline-flex items-center gap-2 rounded-full border border-toba/30 bg-toba-mist px-3 py-2 text-xs font-medium text-toba-dark transition-colors duration-150 hover:bg-toba-soft"

              title="Buka matriks perbandingan rumah sakit"

              aria-label={`Bandingkan ${compareIds.length} rumah sakit`}

            >

              <span className="material-symbols-outlined text-base">compare</span>

              <span className="hidden sm:inline">Bandingkan ({compareIds.length})</span>

            </button>

          ) : null}



          {!user ? (

            <button

              type="button"

              onClick={openLogin}

              className="inline-flex items-center gap-2 rounded-full bg-toba px-4 py-2 text-xs font-semibold text-white shadow-sm transition-colors duration-150 hover:bg-toba-dark"

            >

              <span className="material-symbols-outlined text-base">person</span>

              <span className="hidden sm:inline">Masuk / Registrasi</span>

              <span className="sm:hidden">Masuk</span>

            </button>

          ) : (

            <div className="relative">

              <button

                type="button"

                onClick={() => setAccountOpen((current) => !current)}

                className="flex h-9 w-9 items-center justify-center rounded-full bg-toba text-xs font-bold text-white shadow-sm"

                aria-label="Menu akun"

              >

                {user.name?.charAt(0) || user.nama_lengkap?.charAt(0) || 'C'}

              </button>

              {accountOpen && (

                <div className="absolute right-0 top-11 w-56 animate-fade-in rounded-xl border border-slate-200 bg-white p-2 shadow-floating">

                  <p className="px-2 py-1.5 text-xs font-medium text-slate-500">

                    Akun Pasien

                  </p>

                  <p className="px-2 pb-2 text-xs text-slate-600">

                    {user.nama_lengkap || user.name} (@{user.username || 'pasien'})

                  </p>

                  <button

                    type="button"

                    onClick={() => navigate('/dashboard')}

                    className="mb-1 w-full rounded-lg px-2 py-2 text-left text-xs font-semibold text-toba-dark hover:bg-toba-mist"

                  >

                    Dashboard Pasien

                  </button>

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

            className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-600 transition-colors duration-150 hover:bg-slate-50 lg:hidden"

            onClick={() => setMenuOpen((current) => !current)}

            aria-label="Buka menu navigasi"

            aria-expanded={menuOpen}

          >

            <span className="material-symbols-outlined text-lg">

              {menuOpen ? 'close' : 'menu'}

            </span>

          </button>

        </div>

      </div>



      {menuOpen && (

        <div className="border-t border-slate-100 bg-white px-4 py-3 shadow-soft lg:hidden">

          <div className="grid gap-1">

            {navItems.map((item) => (

              <button

                key={item.id}

                type="button"

                onClick={() => navigate(item.to)}

                className={cn(

                  'rounded-lg px-3 py-2 text-left text-sm font-semibold',

                  active === item.id ? 'bg-toba-mist text-toba-dark' : 'text-slate-600',

                )}

              >

                {item.label}

              </button>

            ))}

          </div>

        </div>

      )}



      {/* Pita Tenun Motif Ulos Batak khas Sumatera Utara */}

      <div className="ulos" aria-hidden="true" />

        </header>

      <EmergencyRadarModal open={radarOpen} onClose={() => setRadarOpen(false)} />

      <ETicketModal open={ticketOpen} onClose={() => setTicketOpen(false)} />

    </>

  );

}

