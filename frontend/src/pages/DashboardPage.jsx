import { useEffect, useMemo, useState } from 'react';
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

const STATUS_STYLE = {
  menunggu: { label: 'Menunggu Konfirmasi', cls: 'bg-amber-50 text-amber-800 ring-1 ring-amber-200' },
  dikonfirmasi: { label: 'Dikonfirmasi', cls: 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200' },
  selesai: { label: 'Selesai', cls: 'bg-slate-100 text-slate-700 ring-1 ring-slate-200' },
  dibatalkan: { label: 'Dibatalkan', cls: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200' },
  disetujui: { label: 'Ditampilkan', cls: 'bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200' },
  ditolak: { label: 'Ditolak', cls: 'bg-rose-50 text-rose-700 ring-1 ring-rose-200' },
};

function StatusBadge({ status }) {
  const key = String(status || '').toLowerCase();
  const meta = STATUS_STYLE[key] || {
    label: status || '—',
    cls: 'bg-slate-100 text-slate-700 ring-1 ring-slate-200',
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-[11px] font-semibold ${meta.cls}`}>
      {meta.label}
    </span>
  );
}

export default function DashboardPage() {
  const { isAuthenticated, token, openLogin, toast } = useApp();
  const [data, setData] = useState(null);
  const [rsMap, setRsMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('semua');

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
      toast(`Gagal memuat data akun: ${err.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDashboard();
  }, [token]);

  const copyCode = (code) => {
    if (!code) return;
    navigator.clipboard?.writeText(code).then(
      () => toast(`Kode ${code} disalin ke papan klip.`, 'success'),
      () => toast(`Kode: ${code}`, 'info'),
    );
  };

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
      toast('Rumah sakit dihapus dari daftar favorit.', 'info');
      loadDashboard();
    } catch (err) {
      toast(err.message, 'error');
    }
  };

  const stats = data?.statistik || {};
  const poliList = data?.riwayat_poliklinik || [];
  const kamarList = data?.riwayat_kamar || [];
  const ulasanList = data?.ulasan_saya || [];
  const favoritList = data?.favorit_rs || [];

  const tabs = useMemo(
    () => [
      { id: 'semua', label: 'Semua Aktivitas' },
      { id: 'poli', label: 'Antrean Poliklinik', count: poliList.length },
      { id: 'kamar', label: 'Booking Kamar', count: kamarList.length },
      { id: 'favorit', label: 'RS Favorit', count: favoritList.length },
      { id: 'ulasan', label: 'Ulasan Saya', count: ulasanList.length },
    ],
    [poliList.length, kamarList.length, favoritList.length, ulasanList.length],
  );

  if (!isAuthenticated) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50">
        <SiteHeader active="dashboard" />
        <main className="mx-auto flex w-full max-w-md flex-1 flex-col items-center justify-center px-5 py-16 text-center">
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-brand-navy/10 text-brand-navy">
            <span className="material-symbols-outlined text-[30px]">person</span>
          </div>
          <h1 className="mt-4 font-heading text-2xl font-extrabold tracking-tight text-slate-900">
            Ruang Pasien CariSehat
          </h1>
          <p className="mt-2 text-sm leading-relaxed text-slate-600">
            Masuk ke akun pasien untuk memantau nomor antrean poliklinik, status pemesanan kamar
            rawat inap, daftar rumah sakit pilihan, dan ulasan Anda.
          </p>
          <button
            type="button"
            onClick={openLogin}
            className="mt-6 rounded-full bg-brand-navy px-6 py-3 text-xs font-semibold text-white transition hover:bg-brand-blue"
          >
            Masuk atau Daftar Akun
          </button>
        </main>
        <MinimalFooter />
      </div>
    );
  }

  const showPoli = activeTab === 'semua' || activeTab === 'poli';
  const showKamar = activeTab === 'semua' || activeTab === 'kamar';
  const showFavorit = activeTab === 'semua' || activeTab === 'favorit';
  const showUlasan = activeTab === 'semua' || activeTab === 'ulasan';

  return (
    <div className="flex min-h-screen flex-col bg-[#F8FAFC]">
      <SiteHeader active="dashboard" />

      <main className="mx-auto w-full max-w-[1280px] flex-1 px-4 py-8 sm:px-6 lg:px-8">
        {/* Header Profil Pasien */}
        <div className="mb-6 flex flex-wrap items-center justify-between gap-4 rounded-2xl border border-slate-200/90 bg-white p-5 sm:p-6">
          <div className="flex items-center gap-4">
            <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-brand-navy text-base font-extrabold text-white">
              {String(data?.profil?.nama_lengkap || 'P')
                .split(/\s+/)
                .filter(Boolean)
                .slice(0, 2)
                .map((w) => w[0])
                .join('')
                .toUpperCase()}
            </div>
            <div>
              <h1 className="font-heading text-xl font-extrabold tracking-tight text-slate-900 sm:text-2xl">
                {data?.profil?.nama_lengkap || 'Akun Pasien'}
              </h1>
              <p className="mt-0.5 text-xs text-slate-500">
                @{data?.profil?.username} · {data?.profil?.email}
                {data?.profil?.no_telp ? ` · ${data.profil.no_telp}` : ''}
              </p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Link
              to="/peta"
              className="rounded-full border border-slate-200 bg-white px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50"
            >
              Peta Rumah Sakit
            </Link>
            <Link
              to="/pencarian"
              className="rounded-full bg-brand-navy px-4 py-2 text-xs font-semibold text-white transition hover:bg-brand-blue"
            >
              + Cari Layanan RS
            </Link>
          </div>
        </div>

        {loading ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-2xl border border-slate-200 bg-white" />
            ))}
          </div>
        ) : (
          <>
            {/* Ringkasan Statistik */}
            <div className="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-5">
              {[
                { label: 'Antrean Aktif', val: stats.antrean_poli_aktif ?? 0, icon: 'confirmation_number', accent: 'text-brand-blue' },
                { label: 'Total Antrean Poli', val: stats.total_reservasi_poli ?? 0, icon: 'medical_information', accent: 'text-slate-700' },
                { label: 'Booking Kamar', val: stats.total_booking_kamar ?? kamarList.length, icon: 'bed', accent: 'text-emerald-700' },
                { label: 'RS Favorit', val: stats.total_favorit ?? 0, icon: 'favorite', accent: 'text-rose-600' },
                { label: 'Ulasan Dikirim', val: stats.total_ulasan ?? 0, icon: 'rate_review', accent: 'text-amber-600' },
              ].map((s) => (
                <div key={s.label} className="rounded-2xl border border-slate-200/90 bg-white p-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-medium text-slate-500">{s.label}</span>
                    <span className={`material-symbols-outlined text-[19px] ${s.accent}`}>{s.icon}</span>
                  </div>
                  <p className="mt-2 font-heading text-2xl font-extrabold tabular-nums text-slate-900">
                    {s.val}
                  </p>
                </div>
              ))}
            </div>

            {/* Navigasi Tab */}
            <div className="mb-6 flex flex-wrap gap-1.5 border-b border-slate-200 pb-3">
              {tabs.map((tab) => {
                const active = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    className={`inline-flex items-center gap-1.5 rounded-full px-3.5 py-1.5 text-xs font-semibold transition ${
                      active
                        ? 'bg-brand-navy text-white'
                        : 'bg-white text-slate-600 ring-1 ring-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <span>{tab.label}</span>
                    {tab.count != null ? (
                      <span
                        className={`rounded-full px-1.5 py-0.2 text-[10px] tabular-nums ${
                          active ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
                        }`}
                      >
                        {tab.count}
                      </span>
                    ) : null}
                  </button>
                );
              })}
            </div>

            <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
              {/* Kolom Utama: Poliklinik, Booking Kamar & Ulasan */}
              <div className={`space-y-6 ${showFavorit ? 'lg:col-span-8' : 'lg:col-span-12'}`}>
                {showPoli ? (
                  <section className="rounded-2xl border border-slate-200/90 bg-white p-5">
                    <div className="flex items-center justify-between gap-2">
                      <h2 className="font-heading text-base font-bold text-slate-900">
                        Antrean &amp; Reservasi Poliklinik
                      </h2>
                      <span className="text-xs text-slate-500">{poliList.length} riwayat</span>
                    </div>

                    {!poliList.length ? (
                      <div className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-5 text-center">
                        <p className="text-xs text-slate-600">
                          Belum ada reservasi jadwal poliklinik.
                        </p>
                        <Link
                          to="/pencarian"
                          className="mt-2 inline-block text-xs font-semibold text-brand-blue hover:underline"
                        >
                          Pilih rumah sakit dan jadwal dokter →
                        </Link>
                      </div>
                    ) : (
                      <div className="mt-4 space-y-3">
                        {poliList.map((r) => {
                          const rs = rsMap[r.rs_id];
                          return (
                            <div
                              key={r.id}
                              className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-200/80 bg-slate-50/60 p-4"
                            >
                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-2">
                                  <span className="rounded-md bg-brand-navy px-2 py-0.5 font-mono text-[11px] font-bold text-white">
                                    No. Antrean #{r.nomor_antrean}
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => copyCode(r.kode_tiket || r.kode_reservasi)}
                                    title="Salin kode reservasi"
                                    className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-0.5 font-mono text-[11px] font-semibold text-slate-700 hover:bg-slate-100"
                                  >
                                    <span>{r.kode_tiket || r.kode_reservasi}</span>
                                    <span className="material-symbols-outlined text-[13px] text-slate-400">
                                      content_copy
                                    </span>
                                  </button>
                                  <StatusBadge status={r.status} />
                                </div>

                                <Link
                                  to={`/rumah-sakit/${encodeURIComponent(r.rs_id)}`}
                                  className="mt-2 block text-sm font-bold text-slate-900 hover:text-brand-blue hover:underline"
                                >
                                  {rs?.nama || r.rs_id}
                                </Link>
                                <p className="mt-0.5 text-xs text-slate-600">
                                  {r.nama_dokter || 'Dokter Poliklinik'}
                                  {r.spesialisasi ? ` · ${r.spesialisasi}` : ''} · Kunjungan:{' '}
                                  <strong className="font-semibold text-slate-800">{r.tanggal}</strong>
                                </p>
                              </div>

                              {r.status === 'menunggu' || r.status === 'dikonfirmasi' ? (
                                <button
                                  type="button"
                                  onClick={() => handleCancelRes(r.kode_reservasi)}
                                  className="rounded-lg border border-rose-200 bg-white px-3 py-1.5 text-xs font-semibold text-rose-600 transition hover:bg-rose-50"
                                >
                                  Batalkan
                                </button>
                              ) : null}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </section>
                ) : null}

                {showKamar ? (
                  <section className="rounded-2xl border border-slate-200/90 bg-white p-5">
                    <div className="flex items-center justify-between gap-2">
                      <h2 className="font-heading text-base font-bold text-slate-900">
                        Riwayat Booking Kamar Rawat Inap
                      </h2>
                      <span className="text-xs text-slate-500">{kamarList.length} riwayat</span>
                    </div>

                    {!kamarList.length ? (
                      <div className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-5 text-center">
                        <p className="text-xs text-slate-600">
                          Belum ada riwayat pemesanan kamar rawat inap pada akun ini.
                        </p>
                      </div>
                    ) : (
                      <div className="mt-4 space-y-3">
                        {kamarList.map((b) => {
                          const rs = rsMap[b.rs_id];
                          return (
                            <div
                              key={b.id}
                              className="flex flex-wrap items-start justify-between gap-3 rounded-xl border border-slate-200/80 bg-slate-50/60 p-4"
                            >
                              <div className="min-w-0 flex-1">
                                <div className="flex flex-wrap items-center gap-2">
                                  <button
                                    type="button"
                                    onClick={() => copyCode(b.kode_booking)}
                                    title="Salin kode booking"
                                    className="inline-flex items-center gap-1 rounded-md border border-slate-200 bg-white px-2 py-0.5 font-mono text-[11px] font-bold text-slate-800 hover:bg-slate-100"
                                  >
                                    <span>{b.kode_booking}</span>
                                    <span className="material-symbols-outlined text-[13px] text-slate-400">
                                      content_copy
                                    </span>
                                  </button>
                                  <span className="rounded-md bg-slate-200/80 px-2 py-0.5 text-[11px] font-semibold text-slate-800">
                                    Kamar {b.jenis_kamar}
                                  </span>
                                  <StatusBadge status={b.status} />
                                </div>

                                <Link
                                  to={`/rumah-sakit/${encodeURIComponent(b.rs_id)}`}
                                  className="mt-2 block text-sm font-bold text-slate-900 hover:text-brand-blue hover:underline"
                                >
                                  {rs?.nama || b.rs_id}
                                </Link>
                                <p className="mt-0.5 text-xs text-slate-600">
                                  Masuk: <strong className="font-semibold text-slate-800">{b.tanggal_masuk}</strong>
                                  {b.tanggal_keluar ? ` · Keluar: ${b.tanggal_keluar}` : ''}
                                </p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </section>
                ) : null}

                {showUlasan ? (
                  <section className="rounded-2xl border border-slate-200/90 bg-white p-5">
                    <div className="flex items-center justify-between gap-2">
                      <h2 className="font-heading text-base font-bold text-slate-900">
                        Ulasan Rumah Sakit Saya
                      </h2>
                      <span className="text-xs text-slate-500">{ulasanList.length} ulasan</span>
                    </div>

                    {!ulasanList.length ? (
                      <p className="mt-3 text-xs text-slate-500">
                        Anda belum menulis ulasan untuk rumah sakit mana pun.
                      </p>
                    ) : (
                      <div className="mt-4 space-y-3">
                        {ulasanList.map((u) => (
                          <div key={u.id} className="rounded-xl border border-slate-200/80 bg-slate-50/60 p-4">
                            <div className="flex flex-wrap items-center justify-between gap-2">
                              <Link
                                to={`/rumah-sakit/${encodeURIComponent(u.rs_id)}`}
                                className="text-xs font-bold text-brand-navy hover:underline"
                              >
                                {rsMap[u.rs_id]?.nama || u.rs_id}
                              </Link>
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-bold text-amber-500" aria-label={`Rating ${u.rating} dari 5`}>
                                  {'★'.repeat(u.rating)}
                                  <span className="text-slate-300">{'★'.repeat(Math.max(0, 5 - u.rating))}</span>
                                </span>
                                <StatusBadge status={u.status_moderasi} />
                              </div>
                            </div>
                            <p className="mt-2 text-xs leading-relaxed text-slate-700">{u.komentar}</p>
                          </div>
                        ))}
                      </div>
                    )}
                  </section>
                ) : null}
              </div>

              {/* Kolom Samping: Rumah Sakit Favorit */}
              {showFavorit ? (
                <aside className="lg:col-span-4">
                  <div className="rounded-2xl border border-slate-200/90 bg-white p-5">
                    <div className="flex items-center justify-between gap-2">
                      <h2 className="font-heading text-base font-bold text-slate-900">
                        Rumah Sakit Favorit
                      </h2>
                      <span className="text-xs text-slate-500">{favoritList.length} RS</span>
                    </div>

                    {!favoritList.length ? (
                      <div className="mt-4 rounded-xl border border-dashed border-slate-200 bg-slate-50/70 p-4 text-center">
                        <p className="text-xs text-slate-500">
                          Belum ada rumah sakit yang disimpan ke daftar favorit.
                        </p>
                      </div>
                    ) : (
                      <div className="mt-4 space-y-2.5">
                        {favoritList.map((f) => {
                          const rs = rsMap[f.rs_id];
                          return (
                            <div
                              key={f.rs_id}
                              className="flex items-center justify-between gap-2.5 rounded-xl border border-slate-200/80 bg-slate-50/60 p-3"
                            >
                              <div className="min-w-0">
                                <Link
                                  to={`/rumah-sakit/${encodeURIComponent(f.rs_id)}`}
                                  className="block truncate text-xs font-bold text-brand-navy hover:underline"
                                >
                                  {rs?.nama || f.rs_id}
                                </Link>
                                <p className="mt-0.5 truncate text-[11px] text-slate-500">
                                  {rs?.kabkota || 'Sumatera Utara'}
                                  {rs?.kelas ? ` · Kelas ${rs.kelas}` : ''}
                                </p>
                              </div>
                              <button
                                type="button"
                                onClick={() => handleRemoveFav(f.rs_id)}
                                className="shrink-0 rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-[11px] font-semibold text-rose-600 transition hover:bg-rose-50"
                              >
                                Hapus
                              </button>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                </aside>
              ) : null}
            </div>
          </>
        )}
      </main>
      <MinimalFooter />
    </div>
  );
}
