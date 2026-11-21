import { Link } from 'react-router-dom';

export function MinimalFooter() {
  return (
    <footer className="w-full border-t border-slate-200 bg-white py-9">
      <div className="mx-auto max-w-[1280px] px-5 md:px-12">
        <div className="flex flex-col items-start justify-between gap-4 border-b border-slate-200 pb-6 md:flex-row md:items-center">
          <div className="flex flex-col gap-1">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-heading text-base font-semibold text-brand-navy">CariSehat</span>
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                W3C RDF/OWL Standard Compliant
              </span>
            </div>
            <p className="max-w-xl text-xs leading-relaxed text-slate-500">
              Jejaring data semantik fasilitas pelayanan kesehatan nasional yang menghubungkan ontologi
              klinis, kapasitas faskes rujukan, dan interoperabilitas sistem kesehatan.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {['SPARQL 1.1 Endpoint', 'FHIR / RDF Mappings', 'Schema.org Linked'].map((item) => (
              <span
                key={item}
                className="rounded border border-slate-200 bg-slate-50 px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide text-slate-500"
              >
                {item}
              </span>
            ))}
          </div>
        </div>
        <div className="flex flex-col items-center justify-between gap-3 pt-5 text-center sm:flex-row sm:text-left">
          <p className="text-xs text-slate-500">
            © {new Date().getFullYear()} CariSehat. Inisiatif Data Terbuka Semantik Kesehatan Sumatera
            Utara.
          </p>
          <div className="flex items-center gap-5 text-[11px] font-semibold text-slate-500">
            <Link to="/sparql" className="transition-colors hover:text-brand-blue">
              Dokumentasi URI
            </Link>
            <a href="/data/hospitals.rdf" className="transition-colors hover:text-brand-blue">
              Unduh RDF
            </a>
            <a href="/api/health" className="transition-colors hover:text-brand-blue">
              Status Triplestore
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}

export function EditorialFooter() {
  return (
    <footer className="w-full border-t border-slate-200 bg-[#F4F6F9] font-sans text-[13px] text-slate-700">
      <div className="mx-auto max-w-[1360px] px-6 py-14 lg:px-10">
        <div className="grid grid-cols-1 gap-8 border-b border-slate-200 pb-10 md:grid-cols-2 lg:grid-cols-6">
          <div className="lg:col-span-2">
            <div className="mb-4 flex items-center gap-3">
              <img
                src="/images/cari-sehat-icon.png"
                alt="CariSehat"
                className="h-9 w-9 rounded-xl object-cover"
              />
              <span className="font-serif-editorial text-[21px] font-semibold text-brand-navy">
                CariSehat
              </span>
            </div>
            <p className="mb-4 max-w-sm font-light leading-relaxed text-slate-600">
              Direktori semantik rumah sakit se-Sumatera Utara. Menghubungkan 206 fasilitas kesehatan,
              33 kabupaten/kota, dan data rujukan dalam satu pengalaman pencarian.
            </p>
            <div className="space-y-1 text-[12px] text-slate-500">
              <p>Fakultas Ilmu Komputer — Tugas Besar MSBD &amp; Web Semantik</p>
              <p>Sumatera Utara, Indonesia</p>
            </div>
          </div>

          <div>
            <h4 className="mb-3 text-[11px] font-bold uppercase tracking-wider text-slate-900">
              Layanan
            </h4>
            <ul className="space-y-2 text-slate-600">
              <li>
                <Link to="/pencarian?layanan=UGD%2024%20Jam" className="hover:text-brand-blue">
                  IGD 24 Jam
                </Link>
              </li>
              <li>
                <Link to="/pencarian?layanan=Radiologi" className="hover:text-brand-blue">
                  Radiologi &amp; Imaging
                </Link>
              </li>
              <li>
                <Link to="/pencarian?layanan=Kesehatan%20Anak" className="hover:text-brand-blue">
                  Kesehatan Anak
                </Link>
              </li>
              <li>
                <Link to="/pencarian?layanan=Kesehatan%20Jiwa%20%2F%20Psikiatri" className="hover:text-brand-blue">
                  Kesehatan Jiwa
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-[11px] font-bold uppercase tracking-wider text-slate-900">
              Jelajahi
            </h4>
            <ul className="space-y-2 text-slate-600">
              <li>
                <Link to="/pencarian" className="hover:text-brand-blue">
                  Direktori Rumah Sakit
                </Link>
              </li>
              <li>
                <Link to="/peta" className="hover:text-brand-blue">
                  Peta Persebaran
                </Link>
              </li>
              <li>
                <Link to="/pencarian?bpjs=1" className="hover:text-brand-blue">
                  Fasilitas BPJS
                </Link>
              </li>
              <li>
                <Link to="/#direktori-rumah-sakit" className="hover:text-brand-blue">
                  Rumah Sakit Terbaru
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-[11px] font-bold uppercase tracking-wider text-slate-900">
              Data Semantik
            </h4>
            <ul className="space-y-2 text-slate-600">
              <li>
                <a href="/sparql" target="_blank" rel="noopener noreferrer" className="hover:text-brand-blue">
                  SPARQL Studio
                </a>
              </li>
              <li>
                <a href="/data/hospitals.rdf" className="hover:text-brand-blue">
                  Dataset RDF
                </a>
              </li>
              <li>
                <a href="/docs" target="_blank" rel="noopener noreferrer" className="hover:text-brand-blue">
                  Dokumentasi API
                </a>
              </li>
              <li>
                <a href="/api/health" className="hover:text-brand-blue">
                  Status Layanan
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="mb-3 text-[11px] font-bold uppercase tracking-wider text-slate-900">
              Tentang
            </h4>
            <ul className="space-y-2 text-slate-600">
              <li>
                <a href="https://www.kemkes.go.id" target="_blank" rel="noopener noreferrer" className="hover:text-brand-blue">
                  Kemenkes RI
                </a>
              </li>
              <li>
                <a href="https://www.openstreetmap.org" target="_blank" rel="noopener noreferrer" className="hover:text-brand-blue">
                  OpenStreetMap
                </a>
              </li>
              <li>
                <a href="https://dbpedia.org" target="_blank" rel="noopener noreferrer" className="hover:text-brand-blue">
                  DBpedia
                </a>
              </li>
              <li>
                <a href="https://www.w3.org/2001/sw/" target="_blank" rel="noopener noreferrer" className="hover:text-brand-blue">
                  W3C Semantic Web
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between gap-4 border-b border-slate-200 py-6 md:flex-row">
          <div className="flex items-center gap-3 text-[11px] font-semibold uppercase tracking-wide text-slate-700">
            <span className="material-symbols-outlined text-[18px] text-emerald-600">
              verified_user
            </span>
            Data master Kemenkes &amp; BPJS SatuSehat
          </div>
          <div className="flex flex-wrap items-center justify-center gap-5 text-[11px] text-slate-500">
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-emerald-600">public</span>
              Linked Open Data
            </span>
            <span className="flex items-center gap-1">
              <span className="material-symbols-outlined text-[16px] text-sky-600">security</span>
              Read-only SPARQL
            </span>
          </div>
        </div>

        <div className="flex flex-col items-center justify-between gap-3 pt-6 text-xs text-slate-500 md:flex-row">
          <p>© {new Date().getFullYear()} CariSehat — Proyek Akademik Web Semantik.</p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a href="/docs" className="hover:underline">
              Dokumentasi
            </a>
            <a href="/api/health" className="hover:underline">
              Status Sistem
            </a>
            <a href="/data/hospitals.rdf" className="hover:underline">
              Lisensi Data
            </a>
            <a href="https://www.openstreetmap.org/copyright" className="hover:underline">
              Atribusi OSM
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
}
