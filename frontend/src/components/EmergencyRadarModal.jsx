import { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

import { Link, useNavigate } from 'react-router-dom';

import { getEmergencyRadar, getFilterOptions } from '../api';

import { getUserPosition } from './LeafletMap';

import { telHref } from '../utils';



export default function EmergencyRadarModal({ open, onClose }) {

  const navigate = useNavigate();

  const [items, setItems] = useState([]);

  const [loading, setLoading] = useState(false);

  const [gpsActive, setGpsActive] = useState(false);

  const [gpsNote, setGpsNote] = useState('');

  const [kabkota, setKabkota] = useState('');

  const [regions, setRegions] = useState([]);



  const fetchRadar = async ({ lat = null, lon = null, region = '' } = {}) => {

    setLoading(true);

    try {

      const res = await getEmergencyRadar({

        lat: lat ?? undefined,

        lon: lon ?? undefined,

        kabkota: region || undefined,

        limit: 5,

      });

      setItems(res.items || []);

      setGpsActive(Boolean(res.gps_aktif));

    } catch {

      setItems([]);

    } finally {

      setLoading(false);

    }

  };



  useEffect(() => {

    if (!open) return;

    getFilterOptions()

      .then((d) => setRegions(d.kabkota || []))

      .catch(() => {});



    setGpsNote('Mendeteksi lokasi GPS untuk mengurutkan IGD terdekat...');

    getUserPosition()

      .then(([lat, lon]) => {

        setGpsNote('Lokasi GPS aktif • diurutkan berdasarkan jarak terdekat.');

        fetchRadar({ lat, lon, region: kabkota });

      })

      .catch(() => {

        setGpsNote('GPS tidak aktif • menampilkan RS rujukan IGD & ICU utama.');

        fetchRadar({ region: kabkota });

      });

  }, [open]);



  if (!open) return null;



  return createPortal(

    <div

      className="fixed inset-0 z-[2000] flex animate-fade-in items-center justify-center bg-slate-950/65 p-4 backdrop-blur-xs"

      role="dialog"

      aria-modal="true"

      aria-label="Radar Darurat IGD & Ketersediaan Bed ICU"

      onMouseDown={(e) => {

        if (e.target === e.currentTarget) onClose();

      }}

    >

      <div className="max-h-[90vh] w-full max-w-2xl animate-zoom-in overflow-y-auto rounded-3xl border border-rose-200 bg-white shadow-modal">

        <div className="bg-gradient-to-r from-rose-700 via-rose-600 to-red-600 px-6 py-5 text-white">

          <div className="flex items-start justify-between gap-3">

            <div>

              <span className="inline-flex items-center gap-1.5 rounded-full bg-white/15 px-3 py-1 text-[11px] font-bold uppercase tracking-wider">

                <span className="h-2 w-2 animate-ping rounded-full bg-white" />

                Radar Darurat IGD &amp; ICU Live

              </span>

              <h2 className="mt-2 text-xl font-extrabold">

                Fasilitas Gawat Darurat &amp; Ketersediaan ICU

              </h2>

              <p className="mt-1 text-xs text-rose-100">{gpsNote}</p>

            </div>

            <button

              type="button"

              onClick={onClose}

              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white/15 text-white transition hover:bg-white/25"

              aria-label="Tutup radar darurat"

            >

              <span className="material-symbols-outlined text-[18px]">close</span>

            </button>

          </div>



          <div className="mt-4 flex flex-wrap items-center gap-2">

            <a

              href="tel:119"

              className="inline-flex items-center gap-1.5 rounded-full bg-white px-4 py-2 text-xs font-extrabold text-rose-700 shadow-sm transition hover:bg-rose-50"

            >

              <span className="material-symbols-outlined text-[16px]">emergency_share</span>

              Panggil Ambulans Nasional 119

            </a>



            <select

              value={kabkota}

              onChange={(e) => {

                const val = e.target.value;

                setKabkota(val);

                fetchRadar({ region: val });

              }}

              className="rounded-full border border-white/25 bg-rose-800/60 px-3.5 py-2 text-xs font-semibold text-white outline-none"

              aria-label="Filter wilayah darurat"

            >

              <option value="">Semua Kabupaten/Kota</option>

              {regions.map((r) => (

                <option key={r} value={r}>

                  {r}

                </option>

              ))}

            </select>

          </div>

        </div>



        <div className="space-y-3 p-5">

          {loading ? (

            <div className="space-y-3">

              {[1, 2, 3].map((i) => (

                <div key={i} className="h-24 animate-pulse rounded-2xl bg-slate-100" />

              ))}

            </div>

          ) : !items.length ? (

            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-6 text-center text-xs text-slate-500">

              Tidak ditemukan fasilitas IGD pada filter wilayah tersebut.

            </div>

          ) : (

            items.map((rs, idx) => {

              const phone = telHref(rs.telepon);

              return (

                <div

                  key={rs.id}

                  className="rounded-2xl border border-slate-200 bg-white p-4 shadow-card transition hover:border-rose-300"

                >

                  <div className="flex flex-wrap items-start justify-between gap-2">

                    <div className="min-w-0 flex-1">

                      <div className="flex flex-wrap items-center gap-1.5">

                        <span className="rounded-full bg-rose-600 px-2 py-0.5 text-[10px] font-extrabold text-white">

                          #{idx + 1}

                        </span>

                        <span className="rounded-full bg-slate-100 px-2.5 py-0.5 text-[10.5px] font-bold text-slate-700">

                          Kelas {rs.kelas || '—'}

                        </span>

                        {rs.bpjs ? (

                          <span className="rounded-full bg-emerald-50 px-2.5 py-0.5 text-[10.5px] font-bold text-emerald-700">

                            BPJS

                          </span>

                        ) : null}

                        {gpsActive && rs.jarak_km != null ? (

                          <span className="rounded-full bg-toba-mist px-2.5 py-0.5 text-[10.5px] font-extrabold text-toba-dark">

                            {rs.jarak_km} km (~{rs.estimasi_menit} mnt)

                          </span>

                        ) : null}

                      </div>



                      <h3 className="mt-1.5 text-sm font-extrabold text-slate-900">{rs.nama}</h3>

                      <p className="mt-0.5 text-xs text-slate-500">

                        {rs.kabkota} • {rs.alamat}

                      </p>

                    </div>



                    <div className="flex shrink-0 gap-2 text-center">

                      <div className="rounded-xl border border-rose-200 bg-rose-50 px-3 py-1.5">

                        <p className="text-[10px] font-bold text-rose-700">Sisa ICU</p>

                        <p className="text-base font-extrabold text-rose-900">{rs.sisa_icu}</p>

                      </div>

                      <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-3 py-1.5">

                        <p className="text-[10px] font-bold text-emerald-700">Bed Umum</p>

                        <p className="text-base font-extrabold text-emerald-900">

                          {rs.sisa_bed_total}

                        </p>

                      </div>

                    </div>

                  </div>



                  <div className="mt-3.5 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">

                    <button

                      type="button"

                      onClick={() => {

                        onClose();

                        navigate(`/peta?rs=${encodeURIComponent(rs.id)}&route=1`);

                      }}

                      className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-full bg-rose-600 px-4 py-2 text-xs font-bold text-white transition hover:bg-rose-700"

                    >

                      <span className="material-symbols-outlined text-[15px]">directions</span>

                      Rute Cepat ke IGD

                    </button>



                    {phone ? (

                      <a

                        href={phone}

                        className="inline-flex items-center justify-center gap-1.5 rounded-full border border-rose-200 bg-rose-50 px-3.5 py-2 text-xs font-bold text-rose-700 transition hover:bg-rose-100"

                      >

                        <span className="material-symbols-outlined text-[15px]">call</span>

                        {rs.telepon}

                      </a>

                    ) : null}



                    <Link

                      to={`/rumah-sakit/${encodeURIComponent(rs.id)}`}

                      onClick={onClose}

                      className="inline-flex items-center justify-center rounded-full border border-slate-200 px-3.5 py-2 text-xs font-bold text-slate-700 transition hover:bg-slate-50"

                    >

                      Detail

                    </Link>

                  </div>

                </div>

              );

            })

          )}

        </div>

      </div>

    </div>,

    document.body,

  );

}

