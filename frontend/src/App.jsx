import { useEffect } from 'react';
import { Link, Route, Routes, useLocation } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import LoginModal from './components/LoginModal';
import Toasts from './components/Toasts';
import ChatWidget from './components/ChatWidget';
import HomePage from './pages/HomePage';
import SearchPage from './pages/SearchPage';
import DashboardPage from './pages/DashboardPage';
import RankingPage from './pages/RankingPage';
import DetailPage from './pages/DetailPage';
import MapPage from './pages/MapPage';

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: 'instant' });
  }, [pathname]);
  return null;
}

function NotFound() {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-slate-50 px-6 text-center">
      <span className="material-symbols-outlined text-[64px] text-slate-300">explore_off</span>
      <p className="mt-3 text-[10.5px] font-bold uppercase tracking-[0.16em] text-brand-blue">
        404
      </p>
      <h1 className="mt-1 font-heading text-3xl font-extrabold text-brand-navy">
        Halaman tidak ditemukan
      </h1>
      <p className="mt-2 max-w-md text-sm text-slate-500">
        Tautan yang Anda buka tidak tersedia. Kembali ke beranda atau mulai pencarian rumah sakit.
      </p>
      <div className="mt-6 flex gap-2">
        <Link
          to="/"
          className="rounded-full border border-slate-300 bg-white px-5 py-2.5 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
        >
          Beranda
        </Link>
        <Link
          to="/pencarian"
          className="rounded-full bg-brand-navy px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-brand-blue"
        >
          Cari rumah sakit
        </Link>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/pencarian" element={<SearchPage />} />
        <Route path="/rumah-sakit/:id" element={<DetailPage />} />
        <Route path="/rs/:id" element={<DetailPage />} />
        <Route path="/peta" element={<MapPage />} />
        <Route path="/peringkat" element={<RankingPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
      <LoginModal />
      <Toasts />
      <ChatWidget />
    </AppProvider>
  );
}


