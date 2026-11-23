import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  cancelPoliklinikReservasi,
  getAllHospitals,
  getPatientDashboard,
  removeFavoriteRs,
} from '../api';
import { useApp } from '../context/AppContext';
import SiteHeader from '../components/SiteHeader';
import { MinimalFooter } from '../components/Footer';

export default function DashboardPage() {
  const { isAuthenticated, token, openLogin, toast } = useApp();
  const [data, setData] = useState(null);
  const [rsMap, setRsMap] = useState({});
  const [loading, setLoading] = useState(true);

  const loadDashboard = async () => {
    if (!token) {
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      const [dash, hospitals] = await Promise.all([
        getPatientDashboard(token),
        getAllHospitals().catch(() => []),
      ]);
      setData(dash);
      setRsMap(Object.fromEntries((hospitals || []).map((h) => [h.id, h])));
    } catch (err) {
      toast(`Gagal memuat dashboard: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [token]);

  const handleCancelRes = async (kode) => {
    try {
      await cancelPoliklinikReservasi(kode, token);
      toast(`Reservasi ${kode} berhasil dibatalkan.`, 'info');
      loadDashboard();
    } catch (err) {
      toast(err.message, 'error');
    }
  };

  const handleRemoveFav = async (rsId) => {
    try {
      await removeFavoriteRs(rsId, token);
      toast('Rumah sakit dihapus dari favorit.', 'info');
      loadDashboard();
    } catch (err) {
      toast(err.message, 'error');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50">
        <SiteHeader active="dashboard" />
        <main className="mx-auto flex w-full max-w-lg flex-1 flex-col items-center justify-center px-4 py-16 text-center">
          <span className="material-symbols-outlined text-[54px] text-brand-navy">account_circle</span>
          <h1 className="mt-3 font-heading text-2xl font-extrabold text-slate-900">
            Dashboard Pasien CariSehat
          </h1>
          <p className="mt-2 text-sm text-slate-600">
            Masuk untuk melihat tiket antrean poliklinik, daftar rumah sakit favorit, riwayat ulasan,
            dan booking kamar rawat inap Anda.
          </p>
          <button
            type="button"
            onClick={openLogin}
            className="mt-6 rounded-full bg-brand-navy px-6 py-3 text-xs font-semibold text-white transition hover:bg-brand-blue"
          >
            Masuk / Daftar Akun Pasien
          </button>
        </main>
        <MinimalFooter />
      </div>
    );
  }

  const stats = data?.statistik || {};

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <SiteHeader active="dashboard" />
      <main className="mx-auto w-full max-w-[1280px] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h1 className="font-heading text-2xl font-extrabold text-slate-900 sm:text-3xl">
              Dashboard Pasien — {data?.profil?.nama_lengkap}
            </h1>
            <p className="text-xs text-slate-500">
              @{data?.profil?.username} · {data?.profil?.email} (Data dari View{' '}
              <code>v_ringkasan_aktivitas_user</code> &amp; SQLAlchemy ORM)
            </p>
          </div>
          <Link
            to="/pencarian"
            className="rounded-full bg-brand-navy px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue"
          >
            + Cari Rumah Sakit
          </Link>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-2xl bg-white" />
            ))}
          </div>
        ) : (
          <>
            <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-5">
              {[
                { label: 'RS Favorit', val: stats.total_favorit ?? 0, icon: 'favorite' },
                { label: 'Ulasan Dikirim', val: stats.total_ulasan ?? 0, icon: 'reviews' },
                { label: 'Total Antrean Poli', val: stats.total_reservasi_poli ?? 0, icon: 'medical_information' },
                { label: 'Antrean Aktif', val: stats.antrean_poli_aktif ?? 0, icon: 'confirmation_number' },
                { label: 'Booking Kamar', val: stats.total_booking_kamar ?? 0, icon: 'bed' },
              ].map((s) => (
                <div key={s.label} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
                  <span className="material-symbols-outlined text-[20px] text-brand-blue">{s.icon}</span>
                  <p className="mt-2 text-2xl font-extrabold text-slate-900">{s.val}</p>
                  <p className="text-xs text-slate-500">{s.label}</p>
                </div>
              ))}
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              <section className="space-y-4 lg:col-span-7">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="text-base font-bold text-slate-900">Riwayat Reservasi Poliklinik</h2>
                  {!data?.riwayat_poliklinik?.length ? (
                    <p className="mt-3 text-xs text-slate-500">
                      Belum ada reservasi poliklinik. Buka halaman detail RS dan pilih tab Poliklinik.
                    </p>
                  ) : (
                    <div className="mt-3 space-y-3">
                      {data.riwayat_poliklinik.map((r) => (
                        <div
                          key={r.id}
                          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3.5"
                        >
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="rounded bg-brand-navy px-2 py-0.5 font-mono text-[11px] font-bold text-white">
                                Antrean #{r.nomor_antrean}
                              </span>
                              <span className="font-mono text-xs font-bold text-slate-700">
                                {r.kode_reservasi}
                              </span>
                              <span className="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-bold uppercase text-brand-blue">
                                {r.status}
                              </span>
                            </div>
                            <p className="mt-1 text-xs font-bold text-slate-900">
                              {rsMap[r.rs_id]?.nama || r.rs_id}
                            </p>
                            <p className="text-[11px] text-slate-600">
                              {r.nama_dokter} ({r.spesialisasi}) · Tanggal: {r.tanggal}
                            </p>
                          </div>
                          {r.status === 'menunggu' || r.status === 'dikonfirmasi' ? (
                            <button
                              type="button"
                              onClick={() => handleCancelRes(r.kode_reservasi)}
                              className="rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-600 hover:bg-rose-50"
                            >
                              Batalkan
                            </button>
                          ) : null}
                        </div>
                      ))}
                    </div>
                  )}
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="text-base font-bold text-slate-900">Ulasan Rumah Sakit Saya</h2>
                  {!data?.ulasan_saya?.length ? (
                    <p className="mt-3 text-xs text-slate-500">Anda belum mengirim ulasan rumah sakit.</p>
                  ) : (
                    <div className="mt-3 space-y-3">
                      {data.ulasan_saya.map((u) => (
                        <div key={u.id} className="rounded-xl border border-slate-100 bg-slate-50 p-3.5">
                          <div className="flex items-center justify-between gap-2">
                            <Link
                              to={`/rumah-sakit/${u.rs_id}`}
                              className="text-xs font-bold text-brand-navy hover:underline"
                            >
                              {rsMap[u.rs_id]?.nama || u.rs_id}
                            </Link>
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-bold text-amber-600">
                                {'★'.repeat(u.rating)}
                              </span>
                              <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                                {u.status_moderasi}
                              </span>
                            </div>
                          </div>
                          <p className="mt-1.5 text-xs text-slate-700">{u.komentar}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </section>

              <aside className="space-y-4 lg:col-span-5">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                  <h2 className="text-base font-bold text-slate-900">Rumah Sakit Favorit</h2>
                  {!data?.favorit_rs?.length ? (
                    <p className="mt-3 text-xs text-slate-500">
                      Belum ada rumah sakit favorit tersimpan pada akun ini.
                    </p>
                  ) : (
                    <div className="mt-3 space-y-2.5">
                      {data.favorit_rs.map((f) => (
                        <div
                          key={f.rs_id}
                          className="flex items-center justify-between gap-2 rounded-xl border border-slate-100 bg-slate-50 p-3"
                        >
                          <div className="min-w-0">
                            <Link
                              to={`/rumah-sakit/${f.rs_id}`}
                              className="block truncate text-xs font-bold text-brand-navy hover:underline"
                            >
                              {rsMap[f.rs_id]?.nama || f.rs_id}
                            </Link>
                            <p className="text-[11px] text-slate-500">
                              {rsMap[f.rs_id]?.kabkota || 'Sumatera Utara'}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleRemoveFav(f.rs_id)}
                            className="shrink-0 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-rose-600 hover:bg-rose-50"
                          >
                            Hapus
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </aside>
            </div>
          </>
        )}
      </main>
      <MinimalFooter />
    </div>
  );
}
