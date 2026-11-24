import { useEffect, useMemo, useRef, useState } from 'react';
import { ETicketCard } from './ETicketModal';


import { createPoliklinikReservasi, getPoliklinikByRs } from '../api';

import { useApp } from '../context/AppContext';

import { todayISO } from '../utils';



const HARI_LABEL = ['', 'Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu'];



export default function PoliklinikSection({ hospital }) {

  const { user, token, toast } = useApp();

  const [data, setData] = useState(null);

  const [loading, setLoading] = useState(true);

  const [selectedJadwal, setSelectedJadwal] = useState(null);

  const [form, setForm] = useState({

    nama_pasien: user?.nama_lengkap || '',

    no_telp: user?.no_telp || '',

    tanggal: todayISO(),

    keluhan: '',

  });

  const [submitting, setSubmitting] = useState(false);

  const [ticket, setTicket] = useState(null);

  const idemRef = useRef({ body: '', key: '' });



  useEffect(() => {

    if (user) {

      setForm((prev) => ({

        ...prev,

        nama_pasien: prev.nama_pasien || user.nama_lengkap || '',

        no_telp: prev.no_telp || user.no_telp || '',

      }));

    }

  }, [user]);



  const loadPoli = () => {

    setLoading(true);

    getPoliklinikByRs(hospital.id)

      .then((res) => setData(res))

      .catch(() => setData({ poliklinik: [] }))

      .finally(() => setLoading(false));

  };



  useEffect(() => {

    loadPoli();

  }, [hospital.id]);



  const minDate = useMemo(() => todayISO(), []);



  const submitReservasi = async (event) => {

    event.preventDefault();

    if (!selectedJadwal || submitting) return;

    setSubmitting(true);

    setTicket(null);



    const payload = {

      jadwal_id: selectedJadwal.id,

      nama_pasien: form.nama_pasien.trim(),

      no_telp: form.no_telp.trim(),

      tanggal: form.tanggal,

      keluhan: form.keluhan.trim() || null,

    };



    try {

      const serialized = JSON.stringify(payload);

      if (idemRef.current.body !== serialized || !idemRef.current.key) {

        idemRef.current = { body: serialized, key: crypto.randomUUID() };

      }

      const res = await createPoliklinikReservasi(payload, idemRef.current.key, token || undefined);

      setTicket({

        ...res,

        nama_poli: selectedJadwal.nama_poli,

        nama_dokter: selectedJadwal.nama_dokter,

        tanggal: payload.tanggal,

        jam: `${selectedJadwal.jam_mulai} - ${selectedJadwal.jam_selesai}`,

      });

      idemRef.current = { body: '', key: '' };

      toast(`Antrean poli berhasil dibuat (No. Antrean ${res.nomor_antrean}).`, 'success');

      loadPoli();

    } catch (err) {

      toast(`Reservasi gagal: ${err.message}`, 'error');

    } finally {

      setSubmitting(false);

    }

  };



  if (loading) {

    return (

      <div className="space-y-3">

        <div className="h-24 animate-pulse rounded-xl bg-slate-100" />

        <div className="h-24 animate-pulse rounded-xl bg-slate-100" />

      </div>

    );

  }



  const poliklinikList = data?.poliklinik || [];



  return (

    <div className="animate-fade-in space-y-6">

      <div>

        <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">

          Poliklinik &amp; Jadwal Konsultasi Dokter

        </h2>

        <p className="mt-1 text-sm text-slate-500">

          Pilih jadwal dokter poliklinik di <strong>{hospital.nama}</strong>. Nomor antrean dan kuota

          divalidasi secara atomik melalui <code>sp_buat_reservasi_poliklinik</code>.

        </p>

      </div>



      {ticket ? (

        <div className="animate-fade-in">

          <ETicketCard

            ticket={{

              tipe: 'poliklinik',

              kode_tiket: ticket.kode_tiket || ticket.kode_reservasi,

              kode_booking: ticket.kode_reservasi,

              status: ticket.status,

              rs_id: hospital.id,

              nama_rs: hospital.nama,

              nama_pasien: form.nama_pasien || user?.nama_lengkap || 'Pasien',

              layanan: ticket.nama_poli,

              detail_sekunder: `${ticket.nama_dokter} ? ${ticket.tanggal} (${ticket.jam})`,

              nomor_antrean: ticket.nomor_antrean,

            }}

          />

        </div>

      ) : null}



      {selectedJadwal ? (

        <form

          onSubmit={submitReservasi}

          className="rounded-2xl border-2 border-brand-navy/20 bg-blue-50/40 p-5 shadow-sm"

        >

          <div className="mb-4 flex items-start justify-between gap-3">

            <div>

              <span className="rounded-full bg-brand-navy px-2.5 py-0.5 text-[10.5px] font-bold text-white">

                Form Antrean Poliklinik

              </span>

              <h3 className="mt-1.5 text-base font-bold text-slate-900">

                {selectedJadwal.nama_poli} — {selectedJadwal.nama_dokter}

              </h3>

              <p className="text-xs text-slate-600">

                Praktik: {HARI_LABEL[selectedJadwal.hari]} ({selectedJadwal.jam_mulai}–

                {selectedJadwal.jam_selesai}) · Kuota sesi: {selectedJadwal.kuota_per_sesi} pasien

              </p>

            </div>

            <button

              type="button"

              onClick={() => setSelectedJadwal(null)}

              className="rounded-lg border border-slate-200 bg-white px-2.5 py-1 text-xs font-semibold text-slate-600 hover:bg-slate-50"

            >

              Tutup

            </button>

          </div>



          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">

            <div>

              <label className="mb-1 block text-xs font-semibold text-slate-700">Nama Pasien</label>

              <input

                type="text"

                required

                minLength={2}

                value={form.nama_pasien}

                onChange={(e) => setForm({ ...form, nama_pasien: e.target.value })}

                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"

              />

            </div>

            <div>

              <label className="mb-1 block text-xs font-semibold text-slate-700">No. Telepon</label>

              <input

                type="tel"

                required

                minLength={8}

                value={form.no_telp}

                onChange={(e) => setForm({ ...form, no_telp: e.target.value })}

                placeholder="0812xxxxxxxx"

                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"

              />

            </div>

            <div>

              <label className="mb-1 block text-xs font-semibold text-slate-700">

                Tanggal Kunjungan

              </label>

              <input

                type="date"

                required

                min={minDate}

                value={form.tanggal}

                onChange={(e) => setForm({ ...form, tanggal: e.target.value })}

                className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"

              />

            </div>

          </div>



          <div className="mt-3">

            <label className="mb-1 block text-xs font-semibold text-slate-700">

              Keluhan Singkat (Opsional)

            </label>

            <input

              type="text"

              maxLength={500}

              value={form.keluhan}

              onChange={(e) => setForm({ ...form, keluhan: e.target.value })}

              placeholder="Contoh: Kontrol rutin tekanan darah / konsultasi gejala"

              className="w-full rounded-xl border border-slate-300 bg-white px-3 py-2 text-sm"

            />

          </div>



          <div className="mt-4 flex flex-wrap items-center justify-between gap-2">

            <p className="text-[11px] text-slate-500">

              {user

                ? `Terhubung ke akun: ${user.nama_lengkap} (@${user.username})`

                : 'Tips: Masuk akun pasien agar tiket otomatis tersimpan di Dashboard Anda.'}

            </p>

            <button

              type="submit"

              disabled={submitting}

              className="rounded-full bg-brand-navy px-5 py-2.5 text-xs font-semibold text-white transition hover:bg-brand-blue disabled:opacity-50"

            >

              {submitting ? 'Memproses Antrean...' : 'Ambil Nomor Antrean'}

            </button>

          </div>

        </form>

      ) : null}



      {!poliklinikList.length ? (

        <div className="rounded-xl border border-slate-200 bg-slate-50 p-5 text-sm text-slate-500">

          Belum ada unit poliklinik terdaftar untuk rumah sakit ini.

        </div>

      ) : (

        <div className="space-y-4">

          {poliklinikList.map((poli) => (

            <div

              key={poli.id}

              className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:border-slate-300"

            >

              <div className="flex flex-wrap items-start justify-between gap-2">

                <div>

                  <div className="flex flex-wrap items-center gap-2">

                    <span className="rounded-md bg-blue-50 px-2 py-0.5 font-mono text-[11px] font-bold text-brand-blue">

                      {poli.kode_poli}

                    </span>

                    <h3 className="text-base font-bold text-slate-900">{poli.nama_poli}</h3>

                  </div>

                  <p className="mt-1 text-xs text-slate-500">

                    {poli.lokasi_ruangan || 'Gedung Rawat Jalan'} ·{' '}

                    {poli.jam_operasional || '08:00 - 15:00 WIB'}

                  </p>

                </div>

                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700">

                  Sisa kuota hari ini: {poli.sisa_hari_ini} / {poli.kuota_harian}

                </span>

              </div>



              {poli.jadwal_dokter?.length ? (

                <div className="mt-4 grid grid-cols-1 gap-2.5 sm:grid-cols-2">

                  {poli.jadwal_dokter.map((j) => (

                    <div

                      key={j.id}

                      className="flex items-center justify-between gap-3 rounded-xl border border-slate-100 bg-slate-50 p-3"

                    >

                      <div className="min-w-0">

                        <p className="truncate text-xs font-bold text-slate-900">{j.nama_dokter}</p>

                        <p className="text-[11px] text-slate-600">

                          {HARI_LABEL[j.hari]} · {j.jam_mulai}–{j.jam_selesai} (Kuota:{' '}

                          {j.kuota_per_sesi})

                        </p>

                      </div>

                      <button

                        type="button"

                        onClick={() => {

                          setSelectedJadwal({

                            ...j,

                            nama_poli: poli.nama_poli,

                          });

                          setTicket(null);

                        }}

                        className="shrink-0 rounded-full bg-brand-navy px-3 py-1.5 text-[11px] font-semibold text-white transition hover:bg-brand-blue"

                      >

                        Daftar Poli

                      </button>

                    </div>

                  ))}

                </div>

              ) : (

                <p className="mt-3 text-xs italic text-slate-400">

                  Jadwal praktik dokter untuk unit poliklinik ini belum tersedia.

                </p>

              )}

            </div>

          ))}

        </div>

      )}

    </div>

  );

}

