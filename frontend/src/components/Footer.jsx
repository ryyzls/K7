import { Link } from 'react-router-dom';

export function MinimalFooter() {
  return (
    <footer className="w-full border-t border-slate-200 bg-white py-6">
      <div className="mx-auto flex max-w-[1280px] flex-col items-center justify-between gap-3 px-5 text-xs text-slate-500 sm:flex-row md:px-12">
        <p className="font-medium text-slate-600">
          © {new Date().getFullYear()} CariSehat. Direktori Layanan Kesehatan Sumatera Utara.
        </p>
        <p className="text-xs text-slate-400">
          Informasi kontak, layanan, dan fasilitas rumah sakit.
        </p>
      </div>
    </footer>
  );
}

export function EditorialFooter() {
  return (
    <footer className="w-full border-t border-slate-200 bg-stone-50 font-sans text-sm text-slate-700">
      <div className="mx-auto max-w-[1360px] px-6 py-12 lg:px-10">
        <div className="grid grid-cols-1 gap-8 border-b border-slate-200/80 pb-10 md:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <div className="mb-4 flex items-center gap-3">
              <img
                src="/images/cari-sehat-icon.png"
                alt="CariSehat"
                className="h-9 w-9 rounded-lg object-contain"
              />
              <span className="font-serif-editorial text-xl font-semibold text-brand-navy">
                CariSehat
              </span>
            </div>
            <p className="max-w-md leading-relaxed text-slate-600">
              Direktori 206 rumah sakit di 33 kabupaten/kota Sumatera Utara dengan informasi kelas,
              status BPJS, layanan, jadwal poliklinik, dan kuota kamar.
            </p>
          </div>

          <div>
            <h4 className="mb-3 text-xs font-medium text-slate-900">
              Layanan utama
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

          <div>
            <h4 className="mb-3 text-xs font-medium text-slate-900">
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

        <div className="flex flex-col items-center justify-between gap-3 pt-6 text-xs text-slate-500 sm:flex-row">
          <p>© {new Date().getFullYear()} CariSehat. Hak cipta dilindungi.</p>
          <p className="text-xs text-slate-400">
            Platform Informasi Rumah Sakit Sumatera Utara
          </p>
        </div>
      </div>
    </footer>
  );
}