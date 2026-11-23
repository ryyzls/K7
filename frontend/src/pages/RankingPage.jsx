import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAllHospitals, getHospitalRankings } from '../api';
import SiteHeader from '../components/SiteHeader';
import { MinimalFooter } from '../components/Footer';

export default function RankingPage() {
  const [rankings, setRankings] = useState([]);
  const [rsMap, setRsMap] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getHospitalRankings(1, 50), getAllHospitals().catch(() => [])])
      .then(([rankRes, hospitals]) => {
        setRankings(rankRes.peringkat || []);
        setRsMap(Object.fromEntries((hospitals || []).map((h) => [h.id, h])));
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <SiteHeader active="peringkat" />
      <main className="mx-auto w-full max-w-[1280px] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-3 py-1 text-xs font-bold text-amber-800">
            <span className="material-symbols-outlined text-[15px]">leaderboard</span>
            Analitik PostgreSQL Window Function (v_peringkat_rs)
          </span>
          <h1 className="mt-2 font-heading text-2xl font-extrabold text-slate-900 sm:text-3xl">
            Peringkat &amp; Reputasi Rumah Sakit Sumatera Utara
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Pemeringkatan otomatis menggunakan fungsi analitik <code>DENSE_RANK()</code> berdasarkan
            rata-rata rating pasien dan jumlah favorit.
          </p>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-2xl bg-white" />
            ))}
          </div>
        ) : !rankings.length ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-8 text-center text-sm text-slate-500">
            Belum ada data ulasan rumah sakit yang terverifikasi.
          </div>
        ) : (
          <div className="space-y-3">
            {rankings.map((row) => {
              const rs = rsMap[row.rs_id];
              return (
                <div
                  key={row.rs_id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-brand-blue/40"
                >
                  <div className="flex items-center gap-4">
                    <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-navy font-heading text-lg font-extrabold text-white">
                      #{row.peringkat_rating}
                    </div>
                    <div>
                      <Link
                        to={`/rumah-sakit/${row.rs_id}`}
                        className="text-base font-bold text-slate-900 hover:text-brand-blue hover:underline"
                      >
                        {rs?.nama || row.rs_id}
                      </Link>
                      <p className="text-xs text-slate-500">
                        {rs?.kabkota || 'Sumatera Utara'} · Kelas {rs?.kelas || '—'} · RS{' '}
                        {rs?.jenis || '—'}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-4">
                    <div className="rounded-xl bg-amber-50 px-3.5 py-2 text-center">
                      <p className="text-sm font-extrabold text-amber-700">
                        ★ {Number(row.rata_rating).toFixed(2)}
                      </p>
                      <p className="text-[10.5px] text-slate-600">{row.total_ulasan} ulasan</p>
                    </div>
                    <div className="rounded-xl bg-rose-50 px-3.5 py-2 text-center">
                      <p className="text-sm font-extrabold text-rose-700">♥ {row.total_favorit}</p>
                      <p className="text-[10.5px] text-slate-600">
                        Populer #{row.peringkat_terpopuler}
                      </p>
                    </div>
                    <Link
                      to={`/rumah-sakit/${row.rs_id}`}
                      className="rounded-full border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50"
                    >
                      Lihat Poli &amp; Ulasan
                    </Link>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
      <MinimalFooter />
    </div>
  );
}
