import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';
import { useApp } from '../context/AppContext';

const DEMO_ACCOUNTS = [
  { username: 'pasien_demo', label: 'Budi Santoso (pasien_demo)' },
  { username: 'rizal_medan', label: 'Fahri Arizal (rizal_medan)' },
  { username: 'siti_aminah', label: 'Siti Aminah (siti_aminah)' },
];

export default function LoginModal() {
  const { loginOpen, closeLogin, login, registerAndLogin } = useApp();
  const [mode, setMode] = useState('login');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const [ident, setIdent] = useState('');
  const [password, setPassword] = useState('');

  const [regForm, setRegForm] = useState({
    username: '',
    email: '',
    nama_lengkap: '',
    no_telp: '',
    password: '',
  });

  useEffect(() => {
    if (!loginOpen) return undefined;
    setError('');
    const onKeyDown = (event) => {
      if (event.key === 'Escape') closeLogin();
    };
    document.addEventListener('keydown', onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [loginOpen, closeLogin]);

  if (!loginOpen) return null;

  const handleLogin = async (event) => {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError('');
    try {
      await login(ident.trim(), password);
      setIdent('');
      setPassword('');
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegister = async (event) => {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setError('');
    try {
      await registerAndLogin({
        username: regForm.username.trim(),
        email: regForm.email.trim(),
        nama_lengkap: regForm.nama_lengkap.trim(),
        no_telp: regForm.no_telp.trim() || null,
        password: regForm.password,
      });
      setRegForm({ username: '', email: '', nama_lengkap: '', no_telp: '', password: '' });
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex animate-fade-in items-center justify-center bg-slate-950/60 p-4 backdrop-blur-overlay sm:p-6"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) closeLogin();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className="modal-shadow relative max-h-[92vh] w-full max-w-[480px] animate-zoom-in overflow-y-auto rounded-[28px] bg-white p-6 transition-all sm:p-8"
      >
        <button
          type="button"
          onClick={closeLogin}
          aria-label="Tutup jendela"
          className="absolute right-5 top-5 flex h-9 w-9 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-800"
        >
          <span className="material-symbols-outlined text-[20px]">close</span>
        </button>

        <div className="mb-4 flex items-center gap-3">
          <img
            src="/images/cari-sehat-icon.png"
            alt=""
            className="h-11 w-11 rounded-xl object-cover shadow-soft"
          />
          <div>
            <h2 id="modal-title" className="font-heading text-xl font-extrabold text-slate-900">
              Akun Pasien CariSehat
            </h2>
            <p className="text-xs text-slate-500">
              Terhubung ke PostgreSQL (Reservasi Poli, Favorit &amp; Ulasan RS)
            </p>
          </div>
        </div>

        <div className="mb-5 grid grid-cols-2 rounded-xl bg-slate-100 p-1">
          <button
            type="button"
            onClick={() => {
              setMode('login');
              setError('');
            }}
            className={`rounded-lg py-2 text-xs font-bold transition ${
              mode === 'login'
                ? 'bg-white text-brand-navy shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Masuk
          </button>
          <button
            type="button"
            onClick={() => {
              setMode('register');
              setError('');
            }}
            className={`rounded-lg py-2 text-xs font-bold transition ${
              mode === 'register'
                ? 'bg-white text-brand-navy shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Daftar Baru
          </button>
        </div>

        {error ? (
          <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-3.5 py-2.5 text-xs font-medium text-rose-700">
            {error}
          </div>
        ) : null}

        {mode === 'login' ? (
          <form onSubmit={handleLogin} className="space-y-3.5">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">
                Username atau Email
              </label>
              <input
                type="text"
                required
                value={ident}
                onChange={(e) => setIdent(e.target.value)}
                placeholder="Contoh: pasien_demo"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:border-brand-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Kata Sandi</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Masukkan kata sandi"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2.5 text-sm focus:border-brand-blue focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-full bg-brand-navy py-3 text-sm font-semibold text-white transition hover:bg-brand-blue disabled:opacity-50"
            >
              {submitting ? 'Memproses...' : 'Masuk ke Akun'}
            </button>

            <div className="rounded-xl border border-slate-200 bg-slate-50 p-3">
              <p className="mb-2 text-[11px] font-semibold text-slate-600">
                Isi cepat akun demo MSBD (password: <code>Demo1234!</code>):
              </p>
              <div className="flex flex-wrap gap-1.5">
                {DEMO_ACCOUNTS.map((acc) => (
                  <button
                    key={acc.username}
                    type="button"
                    onClick={() => {
                      setIdent(acc.username);
                      setPassword('Demo1234!');
                    }}
                    className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-brand-navy transition hover:border-brand-blue hover:bg-blue-50"
                  >
                    {acc.label}
                  </button>
                ))}
              </div>
            </div>
          </form>
        ) : (
          <form onSubmit={handleRegister} className="space-y-3">
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Nama Lengkap</label>
              <input
                type="text"
                required
                minLength={2}
                value={regForm.nama_lengkap}
                onChange={(e) => setRegForm({ ...regForm, nama_lengkap: e.target.value })}
                placeholder="Nama sesuai KTP"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-brand-blue focus:outline-none"
              />
            </div>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">Username</label>
                <input
                  type="text"
                  required
                  minLength={3}
                  pattern="^[A-Za-z0-9_.-]+$"
                  value={regForm.username}
                  onChange={(e) => setRegForm({ ...regForm, username: e.target.value })}
                  placeholder="huruf/angka/_"
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-brand-blue focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-xs font-semibold text-slate-700">No. Telepon</label>
                <input
                  type="tel"
                  value={regForm.no_telp}
                  onChange={(e) => setRegForm({ ...regForm, no_telp: e.target.value })}
                  placeholder="0812xxxxxxxx"
                  className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-brand-blue focus:outline-none"
                />
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">Email</label>
              <input
                type="email"
                required
                value={regForm.email}
                onChange={(e) => setRegForm({ ...regForm, email: e.target.value })}
                placeholder="nama@email.com"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-brand-blue focus:outline-none"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs font-semibold text-slate-700">
                Kata Sandi (min. 6 karakter)
              </label>
              <input
                type="password"
                required
                minLength={6}
                value={regForm.password}
                onChange={(e) => setRegForm({ ...regForm, password: e.target.value })}
                placeholder="Minimal 6 karakter"
                className="w-full rounded-xl border border-slate-300 px-3.5 py-2 text-sm focus:border-brand-blue focus:outline-none"
              />
            </div>
            <button
              type="submit"
              disabled={submitting}
              className="w-full rounded-full bg-brand-navy py-3 text-sm font-semibold text-white transition hover:bg-brand-blue disabled:opacity-50"
            >
              {submitting ? 'Mendaftarkan...' : 'Daftar & Masuk'}
            </button>
          </form>
        )}
      </div>
    </div>,
    document.body,
  );
}
