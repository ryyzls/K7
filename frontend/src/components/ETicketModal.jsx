import { useMemo, useState } from 'react';
import { createPortal } from 'react-dom';

import { Link } from 'react-router-dom';

import { checkUnifiedTicket } from '../api';

import { buildQrMatrix } from '../utils/qrSvg';

import { useApp } from '../context/AppContext';



export function QrCodeSvg({ value, size = 136 }) {

  const matrix = useMemo(() => buildQrMatrix(value), [value]);

  const dim = matrix.length;

  return (

    <svg

      width={size}

      height={size}

      viewBox={`-2 -2 ${dim + 4} ${dim + 4}`}

      shapeRendering="crispEdges"

      className="rounded-xl border border-slate-200 bg-white p-1.5 shadow-sm"

      aria-label={`QR Code ${value}`}

    >

      <rect x={-2} y={-2} width={dim + 4} height={dim + 4} fill="#FFFFFF" />

      {matrix.map((row, r) =>

        row.map((cell, c) =>

          cell ? <rect key={`${r}-${c}`} x={c} y={r} width={1} height={1} fill="#0F172A" /> : null,

        ),

      )}

    </svg>

  );

}



export function ETicketCard({ ticket, onClose }) {

  const { toast } = useApp();

  if (!ticket) return null;



  const code = ticket.kode_tiket || ticket.kode_booking;

  const isPoli = ticket.tipe === 'poliklinik' || ticket.nomor_antrean != null;

  const statusMap = {

    dikonfirmasi: { label: 'Dikonfirmasi', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },

    simulasi_terdaftar: { label: 'Antrean Aktif', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' },

    menunggu: { label: 'Menunggu Verifikasi', cls: 'bg-amber-50 text-amber-800 border-amber-200' },

    dibatalkan: { label: 'Dibatalkan', cls: 'bg-rose-50 text-rose-700 border-rose-200' },

    selesai: { label: 'Selesai', cls: 'bg-slate-100 text-slate-700 border-slate-200' },

  };

  const st = statusMap[ticket.status] || {

    label: ticket.status || 'Terdaftar',

    cls: 'bg-toba-mist text-toba-dark border-toba/25',

  };



  return (

    <div className="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-card">

      <div className="ulos" aria-hidden="true" />

      <div className="bg-gradient-to-r from-toba-dark to-toba px-5 py-4 text-white">

        <div className="flex items-center justify-between gap-2">

          <span className="inline-flex items-center gap-1.5 text-[11px] font-bold uppercase tracking-wider text-teal-100">

            <span className="material-symbols-outlined text-[16px]">qr_code_2</span>

            {isPoli ? 'E-Ticket Antrean Poliklinik' : 'E-Ticket Reservasi Kamar'}

          </span>

          <span className={`rounded-full border px-2.5 py-0.5 text-[10.5px] font-bold ${st.cls}`}>

            {st.label}

          </span>

        </div>

        <h3 className="mt-1.5 text-base font-extrabold leading-snug">{ticket.nama_rs}</h3>

      </div>



      <div className="p-5">

        <div className="flex flex-col items-center gap-4 sm:flex-row">

          <div className="shrink-0 text-center">

            <QrCodeSvg value={code} size={132} />

            <p className="mt-1.5 font-mono text-[11px] font-bold tracking-wider text-slate-700">

              {code}

            </p>

          </div>



          <div className="w-full flex-1 space-y-2.5 text-xs">

            {ticket.nomor_antrean != null ? (

              <div className="inline-flex items-baseline gap-2 rounded-xl bg-toba-mist px-3.5 py-2">

                <span className="text-[11px] font-semibold text-toba-dark">Nomor Antrean</span>

                <span className="text-2xl font-extrabold text-toba-dark">#{ticket.nomor_antrean}</span>

              </div>

            ) : null}



            <div>

              <p className="text-[10.5px] font-semibold uppercase tracking-wide text-slate-400">Pasien</p>

              <p className="font-bold text-slate-900">{ticket.nama_pasien}</p>

            </div>



            <div>

              <p className="text-[10.5px] font-semibold uppercase tracking-wide text-slate-400">Layanan</p>

              <p className="font-bold text-slate-800">{ticket.layanan}</p>

              {ticket.detail_sekunder ? (

                <p className="text-[11px] text-slate-500">{ticket.detail_sekunder}</p>

              ) : null}

            </div>

          </div>

        </div>



        <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-dashed border-slate-200 pt-4">

          <button

            type="button"

            onClick={() => {

              navigator.clipboard?.writeText(code);

              toast('Kode tiket disalin ke clipboard.', 'success');

            }}

            className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-full bg-toba px-4 py-2 text-xs font-bold text-white transition hover:bg-toba-dark"

          >

            <span className="material-symbols-outlined text-[15px]">content_copy</span>

            Salin Kode

          </button>



          <button

            type="button"

            onClick={() => window.print()}

            className="inline-flex items-center justify-center gap-1.5 rounded-full border border-slate-300 bg-white px-4 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-50"

          >

            <span className="material-symbols-outlined text-[15px]">print</span>

            Cetak

          </button>



          {ticket.rs_id ? (

            <Link

              to={`/rumah-sakit/${encodeURIComponent(ticket.rs_id)}`}

              onClick={onClose}

              className="inline-flex items-center justify-center gap-1 rounded-full border border-toba/30 bg-toba-mist px-3.5 py-2 text-xs font-bold text-toba-dark transition hover:bg-toba-soft"

            >

              Profil RS

            </Link>

          ) : null}

        </div>

      </div>

    </div>

  );

}



export default function ETicketModal({ open, onClose }) {

  const [kode, setKode] = useState('');

  const [noTelp, setNoTelp] = useState('');

  const [loading, setLoading] = useState(false);

  const [error, setError] = useState('');

  const [ticket, setTicket] = useState(null);



  if (!open) return null;



  const handleLookup = async (e) => {

    e.preventDefault();

    if (loading) return;

    setLoading(true);

    setError('');

    setTicket(null);

    try {

      const res = await checkUnifiedTicket(kode.trim().toUpperCase(), noTelp.trim());

      setTicket(res);

    } catch (err) {

      setError(err.message || 'Tiket tidak ditemukan.');

    } finally {

      setLoading(false);

    }

  };



  return createPortal(

    <div

      className="fixed inset-0 z-[2000] flex animate-fade-in items-center justify-center bg-slate-950/60 p-4 backdrop-blur-xs"

      role="dialog"

      aria-modal="true"

      aria-label="Cek E-Ticket & Status Booking"

      onMouseDown={(e) => {

        if (e.target === e.currentTarget) onClose();

      }}

    >

      <div className="max-h-[90vh] w-full max-w-lg animate-zoom-in overflow-y-auto rounded-3xl border border-slate-200 bg-white p-6 shadow-modal">

        <div className="flex items-start justify-between gap-3">

          <div>

            <span className="inline-flex items-center gap-1.5 rounded-full bg-toba-mist px-3 py-1 text-[11px] font-bold text-toba-dark">

              <span className="material-symbols-outlined text-[14px]">confirmation_number</span>

              Pelacak E-Ticket CariSehat

            </span>

            <h2 className="mt-2 text-xl font-extrabold text-slate-900">

              Cek Status Booking &amp; Antrean Poli

            </h2>

            <p className="mt-1 text-xs text-slate-500">

              Masukkan kode booking kamar (<code>BK-...</code>) atau kode tiket poliklinik (

              <code>POL-...</code>) beserta nomor telepon pemesan.

            </p>

          </div>

          <button

            type="button"

            onClick={onClose}

            className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-slate-100 text-slate-500 transition hover:bg-slate-200"

            aria-label="Tutup"

          >

            <span className="material-symbols-outlined text-[18px]">close</span>

          </button>

        </div>



        <form onSubmit={handleLookup} className="mt-5 space-y-3">

          <div className="grid gap-3 sm:grid-cols-2">

            <label className="block">

              <span className="mb-1 block text-xs font-bold text-slate-700">Kode Tiket / Booking</span>

              <input

                required

                value={kode}

                onChange={(e) => setKode(e.target.value)}

                placeholder="BK-2026... atau POL-..."

                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 font-mono text-xs uppercase outline-none transition focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/15"

              />

            </label>

            <label className="block">

              <span className="mb-1 block text-xs font-bold text-slate-700">No. Telepon Pemesan</span>

              <input

                required

                type="tel"

                value={noTelp}

                onChange={(e) => setNoTelp(e.target.value)}

                placeholder="08xxxxxxxxxx"

                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs outline-none transition focus:border-toba focus:bg-white focus:ring-2 focus:ring-toba/15"

              />

            </label>

          </div>



          <button

            type="submit"

            disabled={loading}

            className="flex w-full items-center justify-center gap-2 rounded-full bg-toba px-5 py-3 text-xs font-bold text-white shadow-sm transition hover:bg-toba-dark disabled:opacity-60"

          >

            <span className="material-symbols-outlined text-[17px]">search</span>

            {loading ? 'Memeriksa database...' : 'Tampilkan E-Ticket QR'}

          </button>

        </form>



        {error ? (

          <div className="mt-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-xs font-medium text-rose-700">

            {error}

          </div>

        ) : null}



        {ticket ? (

          <div className="mt-5 animate-fade-in">

            <ETicketCard ticket={ticket} onClose={onClose} />

          </div>

        ) : null}

      </div>

    </div>,

    document.body,

  );

}

