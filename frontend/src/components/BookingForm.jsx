import { useEffect, useMemo, useRef, useState } from 'react';
import { createBooking, deleteBooking, getBookingStatus, getRoomAvailability } from '../api';
import { todayISO } from '../utils';
import { useApp } from '../context/AppContext';

const ROOM_TYPES = ['VIP', 'Kelas I', 'Kelas II', 'Kelas III', 'ICU'];

const EMPTY = {
  nama_pasien: '',
  no_telp: '',
  jenis_kamar: '',
  tanggal_masuk: '',
  tanggal_keluar: '',
  catatan: '',
};

function formatRupiahStatus(status) {
  const map = {
    menunggu: { label: 'Menunggu', className: 'bg-amber-50 text-amber-700 border-amber-200' },
    dikonfirmasi: { label: 'Dikonfirmasi', className: 'bg-emerald-50 text-emerald-700 border-emerald-200' },
    dibatalkan: { label: 'Dibatalkan', className: 'bg-rose-50 text-rose-700 border-rose-200' },
  };
  return map[status] || { label: status || '—', className: 'bg-slate-50 text-slate-700 border-slate-200' };
}

export default function BookingForm({ hospital }) {
  const { toast } = useApp();
  const [form, setForm] = useState({ ...EMPTY, tanggal_masuk: todayISO() });
  const [submitting, setSubmitting] = useState(false);
  const [result, setResult] = useState(null);
  const operationRef = useRef({ body: '', key: '' });

  const [checkOpen, setCheckOpen] = useState(false);
  const [checkCode, setCheckCode] = useState('');
  const [checkPhone, setCheckPhone] = useState('');
  const [checking, setChecking] = useState(false);
  const [checkResult, setCheckResult] = useState(null);
  const [checkError, setCheckError] = useState('');
  const [cancelling, setCancelling] = useState(false);

  const handleCancelBooking = async () => {
    if (!checkResult?.kode_booking) return;
    const kode = checkResult.kode_booking;
    if (!window.confirm(`Batalkan pemesanan kamar dengan kode ${kode}?`)) return;
    setCancelling(true);
    try {
      await deleteBooking(kode);
      setCheckResult((prev) => (prev ? { ...prev, status: 'dibatalkan' } : null));
      toast('Pemesanan kamar berhasil dibatalkan.', 'success');
    } catch (err) {
      toast(err.message || 'Gagal membatalkan pemesanan', 'error');
    } finally {
      setCancelling(false);
    }
  };
  const [availability, setAvailability] = useState(null);

  const minDate = useMemo(() => todayISO(), []);
  const set = (key, value) => setForm((current) => ({ ...current, [key]: value }));

  // Sisa kuota kamar dari SQL (digabung dengan RS dari RDF via rs_id)
  useEffect(() => {
    if (!form.tanggal_masuk) return undefined;
    if (form.tanggal_keluar && form.tanggal_keluar < form.tanggal_masuk) return undefined;
    let cancelled = false;
    getRoomAvailability(hospital.id, form.tanggal_masuk, form.tanggal_keluar || undefined)
      .then((data) => {
        if (!cancelled) setAvailability(Object.fromEntries(data.items.map((item) => [item.jenis_kamar, item])));
      })
      .catch(() => {
        if (!cancelled) setAvailability(null);
      });
    return () => {
      cancelled = true;
    };
  }, [hospital.id, form.tanggal_masuk, form.tanggal_keluar, result]);

  const submit = async (event) => {
    event.preventDefault();
    if (submitting) return;
    setSubmitting(true);
    setResult(null);

    const payload = {
      kode_rs: hospital.id,
      nama_rs: hospital.nama,
      nama_pasien: form.nama_pasien.trim(),
      no_telp: form.no_telp.trim(),
      jenis_kamar: form.jenis_kamar,
      tanggal_masuk: form.tanggal_masuk,
      tanggal_keluar: form.tanggal_keluar || null,
      catatan: form.catatan.trim() || null,
    };

    try {
      const body = JSON.stringify(payload);
      if (operationRef.current.body !== body || !operationRef.current.key) {
        operationRef.current = { body, key: crypto.randomUUID() };
      }
      const response = await createBooking(payload, operationRef.current.key);
      setResult(response);
      setForm({ ...EMPTY, tanggal_masuk: minDate });
      operationRef.current = { body: '', key: '' };
      toast('Reservasi simulasi berhasil dibuat.', 'success');
    } catch (error) {
      toast(`Gagal membuat booking: ${error.message}`, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  const checkStatus = async (event) => {
    event.preventDefault();
    setChecking(true);
    setCheckError('');
    setCheckResult(null);
    try {
      const response = await getBookingStatus(checkCode.trim().toUpperCase(), { phone: checkPhone.trim() });
      setCheckResult(response);
    } catch (error) {
      if (error.status === 403) {
        setCheckError('Kode booking dan nomor telepon pemesan tidak cocok.');
      } else if (error.status === 404) {
        setCheckError('Kode booking tidak ditemukan.');
      } else {
        setCheckError(error.message);
      }
    } finally {
      setChecking(false);
    }
  };

  const status = checkResult ? formatRupiahStatus(checkResult.status) : null;

  return (
    <div className="space-y-4">
      <div className="flex items-start gap-3 rounded-xl border border-blue-100 bg-blue-50/70 p-3.5">
        <span className="material-symbols-outlined mt-0.5 text-[20px] text-brand-blue">science</span>
        <p className="text-[11.5px] leading-relaxed text-slate-600">
          <strong className="font-bold text-slate-800">Simulasi akademik.</strong> Reservasi ini disimpan
          pada basis data PostgreSQL lokal untuk demonstrasi Tugas Besar MSBD dan tidak diteruskan ke sistem
          rumah sakit asli.
        </p>
      </div>

      {result ? (
        <div className="animate-fade-in rounded-xl border border-emerald-200 bg-emerald-50 p-4">
          <div className="flex items-center gap-2 text-sm font-bold text-emerald-700">
            <span className="material-symbols-outlined text-[20px]">check_circle</span>
            Reservasi berhasil dicatat
          </div>
          <p className="mt-2 text-xs text-slate-600">Kode booking simulasi Anda:</p>
          <div className="mt-1 flex items-center gap-2">
            <code className="rounded-lg border border-emerald-200 bg-white px-3 py-1.5 text-[13px] font-bold tracking-wide text-slate-900">
              {result.kode_booking}
            </code>
            <button
              type="button"
              onClick={() => {
                navigator.clipboard?.writeText(result.kode_booking);
                toast('Kode booking disalin.', 'success');
              }}
              className="rounded-lg border border-emerald-200 bg-white px-2.5 py-1.5 text-[11px] font-semibold text-emerald-700 transition hover:bg-emerald-100"
            >
              Salin
            </button>
          </div>
          <p className="mt-2 text-[11px] text-slate-500">
            {result.jenis_kamar} • Masuk {result.tanggal_masuk} • Status: {result.status}
          </p>
          <p className="mt-1 text-[10.5px] text-slate-400">
            Simpan kode ini. Untuk mengecek status, gunakan kode booking beserta nomor telepon pemesan.
          </p>
        </div>
      ) : null}

      <form onSubmit={submit} className="grid gap-3.5 sm:grid-cols-2">
        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">Nama pasien</span>
          <input
            required
            value={form.nama_pasien}
            onChange={(event) => set('nama_pasien', event.target.value)}
            placeholder="Nama lengkap pasien"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">WhatsApp / telepon</span>
          <input
            required
            type="tel"
            value={form.no_telp}
            onChange={(event) => set('no_telp', event.target.value)}
            placeholder="08xxxxxxxxxx"
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">Jenis kamar</span>
          <select
            required
            value={form.jenis_kamar}
            onChange={(event) => set('jenis_kamar', event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
          >
            <option value="">Pilih jenis kamar</option>
            {ROOM_TYPES.map((room) => {
              const info = availability?.[room];
              const full = info && info.sisa <= 0;
              return (
                <option key={room} value={room} disabled={full}>
                  {room}
                  {info ? (full ? ' — penuh' : ` — sisa ${info.sisa} kamar`) : ''}
                </option>
              );
            })}
          </select>
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">Tanggal rencana masuk</span>
          <input
            required
            type="date"
            min={minDate}
            value={form.tanggal_masuk}
            onChange={(event) => set('tanggal_masuk', event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
          />
        </label>

        <label className="block">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Tanggal rencana keluar <span className="font-normal text-slate-400">(opsional)</span>
          </span>
          <input
            type="date"
            min={form.tanggal_masuk || minDate}
            value={form.tanggal_keluar}
            onChange={(event) => set('tanggal_keluar', event.target.value)}
            className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
          />
        </label>

        {availability ? (
          <div className="flex flex-wrap gap-1.5 sm:col-span-2" aria-label="Ketersediaan kamar">
            {ROOM_TYPES.map((room) => {
              const info = availability[room];
              if (!info) return null;
              return (
                <span
                  key={room}
                  className={`rounded-full border px-2.5 py-1 text-[10.5px] font-semibold ${
                    info.sisa > 0
                      ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
                      : 'border-rose-200 bg-rose-50 text-rose-700'
                  }`}
                >
                  {room}: {info.sisa > 0 ? `${info.sisa}/${info.kapasitas} tersedia` : 'penuh'}
                </span>
              );
            })}
          </div>
        ) : null}

        <label className="block sm:col-span-2">
          <span className="mb-1 block text-xs font-semibold text-slate-700">
            Catatan khusus <span className="font-normal text-slate-400">(opsional)</span>
          </span>
          <textarea
            rows={2}
            value={form.catatan}
            onChange={(event) => set('catatan', event.target.value)}
            placeholder="Contoh: memerlukan kursi roda, riwayat alergi..."
            className="w-full resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-sm outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
          />
        </label>

        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center gap-2 rounded-full bg-brand-navy px-5 py-3 text-sm font-semibold text-white transition hover:bg-brand-blue disabled:cursor-not-allowed disabled:opacity-60 sm:col-span-2"
        >
          {submitting ? (
            <>
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
              Memproses reservasi...
            </>
          ) : (
            <>
              <span className="material-symbols-outlined text-[18px]">bed</span>
              Konfirmasi Reservasi Kamar (Simulasi)
            </>
          )}
        </button>
      </form>

      <div className="border-t border-slate-100 pt-3">
        <button
          type="button"
          onClick={() => setCheckOpen((current) => !current)}
          className="flex w-full items-center justify-between gap-2 text-left"
        >
          <span className="flex items-center gap-1.5 text-xs font-bold text-slate-700">
            <span className="material-symbols-outlined text-[17px] text-slate-400">manage_search</span>
            Cek status kode pemesanan
          </span>
          <span className="material-symbols-outlined text-[18px] text-slate-400">
            {checkOpen ? 'expand_less' : 'expand_more'}
          </span>
        </button>

        {checkOpen ? (
          <div className="mt-3 animate-fade-in space-y-2.5">
            <p className="text-[11px] leading-relaxed text-slate-500">
              Masukkan kode booking dan nomor telepon yang dipakai saat memesan.
            </p>
            <form onSubmit={checkStatus} className="grid gap-2 sm:grid-cols-2">
              <input
                value={checkCode}
                onChange={(event) => setCheckCode(event.target.value)}
                placeholder="Kode booking (BK-...)"
                required
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs uppercase outline-none focus:border-brand-blue focus:bg-white"
              />
              <input
                value={checkPhone}
                onChange={(event) => setCheckPhone(event.target.value)}
                placeholder="Nomor telepon pemesan"
                type="tel"
                required
                className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs outline-none focus:border-brand-blue focus:bg-white"
              />
              <button
                type="submit"
                disabled={checking}
                className="inline-flex items-center justify-center gap-1.5 rounded-full border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-50 disabled:opacity-60 sm:col-span-2"
              >
                {checking ? 'Mencari...' : 'Cek status'}
              </button>
            </form>

            {checkError ? (
              <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-[11px] text-rose-700">
                {checkError}
              </p>
            ) : null}

            {checkResult ? (
              <div className="rounded-xl border border-slate-200 bg-slate-50 p-3 text-[11.5px] text-slate-600">
                <div className="flex items-center justify-between gap-2">
                  <strong className="text-slate-800">{checkResult.kode_booking}</strong>
                  <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${status.className}`}>
                    {status.label}
                  </span>
                </div>
                <p className="mt-1.5">
                  {checkResult.nama_pasien} • {checkResult.no_telp}
                </p>
                <p>{checkResult.nama_rs}</p>
                <p>
                  {checkResult.jenis_kamar} • Masuk {checkResult.tanggal_masuk}
                </p>
                {checkResult.status !== 'dibatalkan' && (
                  <div className="mt-2.5 pt-2 border-t border-slate-200/80 flex justify-end">
                    <button
                      type="button"
                      onClick={handleCancelBooking}
                      disabled={cancelling}
                      className="inline-flex items-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-xs font-semibold text-rose-700 transition hover:bg-rose-100 disabled:opacity-50"
                    >
                      <span className="material-symbols-outlined text-[15px]">cancel</span>
                      {cancelling ? 'Membatalkan...' : 'Batalkan Pemesanan'}
                    </button>
                  </div>
                )}
              </div>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
