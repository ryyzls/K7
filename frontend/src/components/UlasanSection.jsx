import { useEffect, useState } from 'react';
import { getHospitalReviews, submitHospitalReview } from '../api';
import { useApp } from '../context/AppContext';

export default function UlasanSection({ hospital }) {
  const { isAuthenticated, token, openLogin, toast } = useApp();
  const [reviews, setReviews] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [rating, setRating] = useState(5);
  const [komentar, setKomentar] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadReviews = () => {
    setLoading(true);
    getHospitalReviews(hospital.id, 1, 20)
      .then((res) => {
        setReviews(res.ulasan || []);
        setTotal(res.total || 0);
      })
      .catch(() => setReviews([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadReviews();
  }, [hospital.id]);

  const avgRating = reviews.length
    ? (reviews.reduce((sum, item) => sum + Number(item.rating || 0), 0) / reviews.length).toFixed(2)
    : null;

  const handleSubmit = async (event) => {
    event.preventDefault();
    if (!isAuthenticated) {
      openLogin();
      return;
    }
    if (submitting) return;
    setSubmitting(true);
    try {
      await submitHospitalReview(
        hospital.id,
        { rating: Number(rating), komentar: komentar.trim() },
        token,
      );
      setKomentar('');
      toast('Ulasan Anda berhasil disimpan ke PostgreSQL.', 'success');
      loadReviews();
    } catch (err) {
      toast(`Gagal mengirim ulasan: ${err.message}`, 'error');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="animate-fade-in space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-[#0F172A]">
            Ulasan &amp; Penilaian Pasien
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Pengalaman layanan pasien yang terverifikasi pada basis data CariSehat.
          </p>
        </div>
        {avgRating ? (
          <div className="flex items-center gap-2 rounded-2xl border border-amber-200 bg-amber-50 px-4 py-2">
            <span className="material-symbols-outlined text-[22px] text-amber-500">star</span>
            <div>
              <p className="text-base font-extrabold text-slate-900">{avgRating} / 5.00</p>
              <p className="text-[11px] text-slate-600">Dari {total} ulasan</p>
            </div>
          </div>
        ) : null}
      </div>

      <form onSubmit={handleSubmit} className="rounded-2xl border border-slate-200 bg-slate-50 p-5">
        <h3 className="text-sm font-bold text-slate-900">Tulis atau Perbarui Ulasan Anda</h3>
        {!isAuthenticated ? (
          <div className="mt-3 flex flex-wrap items-center justify-between gap-3 rounded-xl border border-blue-100 bg-white p-3.5">
            <p className="text-xs text-slate-600">
              Masuk sebagai pasien untuk memberikan penilaian bintang dan ulasan pada rumah sakit ini.
            </p>
            <button
              type="button"
              onClick={openLogin}
              className="rounded-full bg-brand-navy px-4 py-2 text-xs font-semibold text-white hover:bg-brand-blue"
            >
              Masuk Akun Pasien
            </button>
          </div>
        ) : (
          <div className="mt-3 space-y-3">
            <div className="flex items-center gap-1.5">
              <span className="mr-1 text-xs font-semibold text-slate-700">Rating:</span>
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => setRating(star)}
                  className={`rounded-lg px-2.5 py-1 text-xs font-bold transition ${
                    rating >= star
                      ? 'bg-amber-400 text-slate-950'
                      : 'border border-slate-200 bg-white text-slate-500'
                  }`}
                >
                  ★ {star}
                </button>
              ))}
            </div>
            <div>
              <textarea
                rows={3}
                required
                minLength={5}
                maxLength={1000}
                value={komentar}
                onChange={(e) => setKomentar(e.target.value)}
                placeholder="Bagikan pengalaman pelayanan poli, IGD, kebersihan fasilitas, atau keramahan tenaga medis..."
                className="w-full rounded-xl border border-slate-300 bg-white p-3 text-sm focus:border-brand-blue focus:outline-none"
              />
            </div>
            <div className="flex justify-end">
              <button
                type="submit"
                disabled={submitting}
                className="rounded-full bg-brand-navy px-5 py-2 text-xs font-semibold text-white transition hover:bg-brand-blue disabled:opacity-50"
              >
                {submitting ? 'Menyimpan...' : 'Kirim Ulasan'}
              </button>
            </div>
          </div>
        )}
      </form>

      {loading ? (
        <div className="h-24 animate-pulse rounded-xl bg-slate-100" />
      ) : !reviews.length ? (
        <p className="rounded-xl border border-slate-200 bg-white p-5 text-sm text-slate-500">
          Belum ada ulasan untuk rumah sakit ini. Jadilah pasien pertama yang memberikan penilaian!
        </p>
      ) : (
        <div className="space-y-3">
          {reviews.map((item) => (
            <div key={item.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-navy text-xs font-bold text-white">
                    {item.nama_pengguna?.charAt(0) || 'P'}
                  </span>
                  <div>
                    <p className="text-xs font-bold text-slate-900">{item.nama_pengguna}</p>
                    <p className="text-[11px] text-slate-400">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID') : ''}
                    </p>
                  </div>
                </div>
                <span className="rounded-full bg-amber-50 px-2.5 py-1 text-xs font-bold text-amber-700">
                  {'★'.repeat(item.rating)} ({item.rating}/5)
                </span>
              </div>
              <p className="mt-2.5 text-sm leading-relaxed text-slate-700">{item.komentar}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
