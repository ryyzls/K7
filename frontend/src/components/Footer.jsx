import { Link } from 'react-router-dom';

export function MinimalFooter() {
  return (
    <footer className="w-full border-t border-slate-200 bg-white py-6">
      <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-3 px-5 text-xs text-slate-500 sm:flex-row md:px-12">
        <p className="font-medium text-slate-600">
          © {new Date().getFullYear()} CariSehat. Direktori Layanan Kesehatan Sumatera Utara.
        </p>
        <p className="text-[11px] text-slate-400">
          Informasi kontak, fasilitas, dan rujukan rumah sakit terintegrasi.
        </p>
      </div>
    </footer>
  );
}

export function EditorialFooter() {
  return (
    <footer className="w-full border-t border-slate-200 bg-[#F4F6F9] font-sans text-[13px] text-slate-700">
      <div className="mx-auto max-w-[1360px] px-6 py-12 lg:px-10">
        <div className="grid grid-cols-1 gap-8 border-b border-slate-200/80 pb-10 md:grid-cols-2 lg:grid-cols-4">
          {/* Brand Info */}
          <div className="lg:col-span-2">
            <div className="mb-4 flex items-center gap-3">
              <img
                src="/images/cari-sehat-icon.png"
                alt="CariSehat"
                className="h-9 w-9 rounded-xl object-cover shadow-sm"
              />
              <span className="font-sans text-[21px] font-bold tracking-tight text-brand-navy">
                CariSehat
              </span>
            </div>
            <p className="max-w-md font-light leading-relaxed text-slate-600">
              Direktori resmi layanan rumah sakit se-Sumatera Utara. Menghubungkan 206 fasilitas
              kesehatan, 33 kabupaten/kota, dan informasi rujukan dalam satu platform pencarian yang
              mudah, cepat, dan akurat.
            </p>
          </div>

          {/* Layanan */}
          <div>
            <h4 className="mb-3 text-[11px] font-bold uppercase tracking-wider text-slate-900">
              Layanan Utama
            </h4>
            <ul className="space-y-2.5 text-slate-600">
              <li>
                <Link to="/pencarian?layanan=UGD%2024%20Jam" className="transition hover:text-brand-blue">
                  IGD 24 Jam
                </Link>
              </li>
              <li>
                <Link to="/pencarian?layanan=Radiologi" className="transition hover:text-brand-blue">
                  Radiologi &amp; Imaging
                </Link>
              </li>
              <li>
                <Link to="/pencarian?layanan=Kesehatan%20Anak" className="transition hover:text-brand-blue">
                  Kesehatan Anak
                </Link>
              </li>
              <li>
                <Link
                  to="/pencarian?layanan=Kesehatan%20Jiwa%20%2F%20Psikiatri"
                  className="transition hover:text-brand-blue"
                >
                  Kesehatan Jiwa
                </Link>
              </li>
            </ul>
          </div>

          {/* Jelajahi */}
          <div>
            <h4 className="mb-3 text-[11px] font-bold uppercase tracking-wider text-slate-900">
              Jelajahi
            </h4>
            <ul className="space-y-2.5 text-slate-600">
              <li>
                <Link to="/pencarian" className="transition hover:text-brand-blue">
                  Direktori Rumah Sakit
                </Link>
              </li>
              <li>
                <Link to="/peta" className="transition hover:text-brand-blue">
                  Peta Persebaran
                </Link>
              </li>
              <li>
                <Link to="/pencarian?bpjs=1" className="transition hover:text-brand-blue">
                  Fasilitas BPJS Kesehatan
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Copyright */}
        <div className="flex flex-col items-center justify-between gap-3 pt-6 text-xs text-slate-500 sm:flex-row">
          <p>© {new Date().getFullYear()} CariSehat. Hak cipta dilindungi.</p>
          <p className="text-[11.5px] text-slate-400">
            Platform Informasi Rumah Sakit Sumatera Utara
          </p>
        </div>
      </div>
    </footer>
  );
}
