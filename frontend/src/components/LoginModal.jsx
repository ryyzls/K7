import { useEffect } from 'react';
import { createPortal } from 'react-dom';
import { useApp } from '../context/AppContext';

function GoogleIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        fill="#4285F4"
      />
      <path
        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        fill="#34A853"
      />
      <path
        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z"
        fill="#FBBC05"
      />
      <path
        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z"
        fill="#EA4335"
      />
    </svg>
  );
}

function FacebookIcon() {
  return (
    <svg className="h-5 w-5 shrink-0" fill="#1877F2" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
  );
}

function Emblem() {
  return (
    <div className="flex justify-center pb-6 pt-2">
      <div className="relative flex h-16 w-16 items-center justify-center sm:h-20 sm:w-20">
        <img
          src="/images/cari-sehat-icon.png"
          alt=""
          className="h-full w-full rounded-2xl object-cover shadow-soft"
        />
        <span className="absolute -bottom-1 -right-1 flex h-7 w-7 items-center justify-center rounded-full border-2 border-white bg-emerald-500 text-white">
          <span className="material-symbols-outlined text-[15px]">health_and_safety</span>
        </span>
      </div>
    </div>
  );
}

export default function LoginModal() {
  const { loginOpen, closeLogin, login } = useApp();

  useEffect(() => {
    if (!loginOpen) return undefined;
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
        className="modal-shadow relative w-full max-w-[480px] animate-zoom-in rounded-[32px] bg-white p-7 transition-all sm:rounded-[36px] sm:p-10"
      >
        <button
          type="button"
          onClick={closeLogin}
          aria-label="Tutup jendela"
          className="absolute right-6 top-6 flex h-10 w-10 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition-colors hover:bg-slate-200 hover:text-slate-800 focus:outline-none focus:ring-2 focus:ring-slate-300"
        >
          <span className="material-symbols-outlined text-[21px]">close</span>
        </button>

        <Emblem />

        <div className="mb-8 px-2 text-center">
          <h2
            id="modal-title"
            className="mb-2 font-heading text-[23px] font-extrabold leading-[1.28] tracking-tight text-slate-900 sm:text-[27px]"
          >
            Untuk menjelajahi faskes lengkap, masuk atau daftar gratis
          </h2>
          <p className="mx-auto max-w-sm text-sm leading-relaxed text-slate-500 sm:text-[14.5px]">
            Akses ketersediaan IGD, rujukan BPJS, serta rekam faskes favorit Anda dalam satu akun.
          </p>
        </div>

        <div className="mb-6 space-y-3 sm:space-y-3.5">
          <button
            type="button"
            onClick={() => login('Google')}
            className="flex h-[52px] w-full items-center justify-center gap-3.5 rounded-full bg-slate-100 px-6 text-[15px] font-semibold text-slate-800 transition-all hover:bg-slate-200/90 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2 sm:h-[54px] sm:text-base"
          >
            <GoogleIcon />
            <span>Lanjutkan dengan Google</span>
          </button>
          <button
            type="button"
            onClick={() => login('Facebook')}
            className="flex h-[52px] w-full items-center justify-center gap-3.5 rounded-full bg-slate-100 px-6 text-[15px] font-semibold text-slate-800 transition-all hover:bg-slate-200/90 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2 sm:h-[54px] sm:text-base"
          >
            <FacebookIcon />
            <span>Lanjutkan dengan Facebook</span>
          </button>
          <button
            type="button"
            onClick={() => login('Email')}
            className="flex h-[52px] w-full items-center justify-center gap-3.5 rounded-full bg-slate-100 px-6 text-[15px] font-semibold text-slate-800 transition-all hover:bg-slate-200/90 active:scale-[0.99] focus:outline-none focus:ring-2 focus:ring-slate-300 focus:ring-offset-2 sm:h-[54px] sm:text-base"
          >
            <span className="material-symbols-outlined text-[21px] text-slate-700">mail</span>
            <span>Lanjutkan dengan email</span>
          </button>
        </div>

        <p className="mb-4 rounded-xl border border-amber-200 bg-amber-50 px-3 py-2 text-center text-[11px] leading-relaxed text-amber-700">
          Mode demo akademik: pilih salah satu metode untuk masuk sebagai pengguna simulasi. Tidak ada
          kredensial yang dikirim ke server.
        </p>

        <footer className="px-4 text-center">
          <p className="text-xs leading-relaxed text-slate-500 sm:text-[13px]">
            Dengan melanjutkan ke CariSehat, Anda menyetujui{' '}
            <a
              className="font-medium text-slate-800 underline underline-offset-2 transition-colors hover:text-brand-navy"
              href="#terms"
            >
              Ketentuan Layanan
            </a>{' '}
            dan{' '}
            <a
              className="font-medium text-slate-800 underline underline-offset-2 transition-colors hover:text-brand-navy"
              href="#privacy"
            >
              Kebijakan Privasi
            </a>
            .
          </p>
        </footer>
      </div>
    </div>,
    document.body,
  );
}
