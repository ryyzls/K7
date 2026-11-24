import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { getAllHospitals, getHospitalRankings } from '../api';
import SiteHeader from '../components/SiteHeader';
import { MinimalFooter } from '../components/Footer';

function rankBadgeStyle(rank) {
  if (rank === 1) return 'bg-amber-500 text-white ring-4 ring-amber-100';
  if (rank === 2) return 'bg-slate-600 text-white ring-4 ring-slate-100';
  if (rank === 3) return 'bg-amber-800 text-white ring-4 ring-amber-50';
  return 'bg-brand-navy text-white';
}

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
    <div className="flex min-h-screen flex-col bg-[#F8FAFC]">
      <SiteHeader active="peringkat" />
      <main className="mx-auto w-full max-w-[1280px] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-amber-100/90 px-3 py-1 text-xs font-bold text-amber-900">
            <span className="material-symbols-outlined text-[15px]">leaderboard</span>
            Indeks Kepuasan &amp; Reputasi Pasien
          </span>
          <h1 className="mt-2 font-heading text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
            Peringkat Rumah Sakit Sumatera Utara
          </h1>
          <p className="mt-1 max-w-2xl text-sm text-slate-600">
            Urutan disusun secara berkala berdasarkan rata-rata penilaian pasien terverifikasi serta
            tingkat penyimpanan favorit oleh pengunjung.
          </p>
        </div>

        {loading ? (
          <div className="space-y-3">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-2xl border border-slate-200 bg-white" />
            ))}
          </div>
        ) : !rankings.length ? (
          <div className="rounded-2xl border border-slate-200 bg-white p-10 text-center">
            <p className="text-sm font-semibold text-slate-700">Belum ada ulasan terverifikasi</p>
            <p className="mt-1 text-xs text-slate-500">
              Peringkat akan tampil setelah ulasan pasien pada profil rumah sakit disetujui.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {rankings.map((row) => {
              const rs = rsMap[row.rs_id];
              const rank = Number(row.peringkat_rating || 0);
              return (
                <div
                  key={row.rs_id}
                  className="flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200/90 bg-white p-5 transition hover:border-brand-blue/40"
                >
                  <div className="flex items-center gap-4">
                    <div
                      className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl font-heading text-lg font-extrabold tabular-nums ${rankBadgeStyle(rank)}`}
                    >
                      #{rank}
                    </div>
                    {rs?.foto ? (
                      <img
                        src={rs.foto}
                        alt=""
                        loading="lazy"
                        className="hidden h-12 w-12 shrink-0 rounded-xl object-cover sm:block"
                        onError={(e) => {
                          e.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : null}
                    <div>
                      <Link
                        to={`/rumah-sakit/${encodeURIComponent(row.rs_id)}`}
                        className="text-base font-bold text-slate-900 hover:text-brand-blue hover:underline"
                      >
                        {rs?.nama || row.rs_id}
                      </Link>
                      <p className="mt-0.5 text-xs text-slate-500">
                        {rs?.kabkota || 'Sumatera Utara'} · Kelas {rs?.kelas || '—'}
                        {rs?.jenis ? ` · RS ${rs.jenis}` : ''}
                      </p>
                    </div>
                  </div>

                  <div className="flex flex-wrap items-center gap-3">
                    <div className="rounded-xl border border-amber-200/80 bg-amber-50/80 px-3.5 py-2 text-center">
                      <p className="text-sm font-extrabold tabular-nums text-amber-800">
                        ★ {Number(row.rata_rating).toFixed(2)}
                      </p>
                      <p className="text-[10.5px] text-slate-600">{row.total_ulasan} ulasan</p>
                    </div>
                    <div className="rounded-xl border border-rose-200/80 bg-rose-50/80 px-3.5 py-2 text-center">
                      <p className="text-sm font-extrabold tabular-nums text-rose-700">
                        ♥ {row.total_favorit}
                      </p>
                      <p className="text-[10.5px] text-slate-600">
                        Favorit #{row.peringkat_terpopuler}
                      </p>
                    </div>
                    <Link
                      to={`/rumah-sakit/${encodeURIComponent(row.rs_id)}`}
                      className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
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