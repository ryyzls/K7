const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request(path, options = {}) {
  const { token, headers: customHeaders, ...rest } = options;
  const res = await fetch(`${API_BASE}${path}`, {
    ...rest,
    headers: {
      Accept: 'application/json',
      ...(rest.body ? { 'Content-Type': 'application/json' } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(customHeaders || {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const payload = await res.json();
      if (payload?.detail) {
        detail = Array.isArray(payload.detail)
          ? payload.detail.map((d) => d.msg || JSON.stringify(d)).join('; ')
          : payload.detail;
      }
    } catch {
      /* ignore non-JSON errors */
    }
    const error = new Error(detail);
    error.status = res.status;
    throw error;
  }

  return res.json();
}

function cleanParams(params) {
  const search = new URLSearchParams();
  Object.entries(params || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      search.set(key, String(value));
    }
  });
  return search;
}

export async function searchHospitals(params = {}) {
  const search = cleanParams(params);
  return request(`/api/search?${search.toString()}`);
}

export async function getFilterOptions() {
  return request('/api/filters');
}

export async function getMapConfig() {
  return request('/api/config/maps');
}

export async function sendChat(payload) {
  return request('/api/chat', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function getCityInfo(cityName) {
  return request(`/api/external/city/${encodeURIComponent(cityName)}`);
}

export async function createBooking(payload, idempotencyKey) {
  return request('/api/booking', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
  });
}

export async function getBookingStatus(code, { phone = '', accessKey = '' } = {}) {
  const query = phone ? `?no_telp=${encodeURIComponent(phone)}` : '';
  return request(`/api/booking/${encodeURIComponent(code)}${query}`, {
    headers: accessKey ? { 'X-Booking-Key': accessKey } : {},
  });
}

export async function getRoomAvailability(kodeRs, masuk, keluar) {
  const search = cleanParams({ tanggal_masuk: masuk, tanggal_keluar: keluar });
  return request(`/api/availability/${encodeURIComponent(kodeRs)}?${search.toString()}`);
}

export async function getConsultationSchedule(kodeRs, tanggal) {
  const search = cleanParams({ tanggal });
  return request(`/api/konsultasi/${encodeURIComponent(kodeRs)}?${search.toString()}`);
}

export async function createConsultation(payload, idempotencyKey) {
  return request('/api/konsultasi/reservasi', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
  });
}

/* === Modul MSBD: Auth Pasien, Poliklinik, Favorit, Ulasan & Peringkat RS === */

export async function registerPatient(payload) {
  return request('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function loginPatient(payload) {
  return request('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify(payload),
  });
}

export async function logoutPatient(token) {
  return request('/api/auth/logout', {
    method: 'POST',
    token,
  });
}

export async function getPatientDashboard(token) {
  return request('/api/pasien/dashboard', { token });
}

export async function getPoliklinikByRs(rsId) {
  return request(`/api/poliklinik/${encodeURIComponent(rsId)}`);
}

export async function createPoliklinikReservasi(payload, idempotencyKey, token) {
  return request('/api/poliklinik/reservasi', {
    method: 'POST',
    body: JSON.stringify(payload),
    token,
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
  });
}

export async function cancelPoliklinikReservasi(kodeReservasi, token) {
  return request(`/api/pasien/reservasi/${encodeURIComponent(kodeReservasi)}/batal`, {
    method: 'PATCH',
    token,
  });
}

export async function addFavoriteRs(rsId, catatan, token) {
  return request(`/api/pasien/favorit/${encodeURIComponent(rsId)}`, {
    method: 'POST',
    body: JSON.stringify({ catatan: catatan || null }),
    token,
  });
}

export async function removeFavoriteRs(rsId, token) {
  return request(`/api/pasien/favorit/${encodeURIComponent(rsId)}`, {
    method: 'DELETE',
    token,
  });
}

export async function submitHospitalReview(rsId, payload, token) {
  return request(`/api/rs/${encodeURIComponent(rsId)}/ulasan`, {
    method: 'POST',
    body: JSON.stringify(payload),
    token,
  });
}

export async function getHospitalReviews(rsId, page = 1, limit = 10) {
  const search = cleanParams({ page, limit });
  return request(`/api/rs/${encodeURIComponent(rsId)}/ulasan?${search.toString()}`);
}

export async function getHospitalRankings(minUlasan = 1, limit = 30) {
  const search = cleanParams({ min_ulasan: minUlasan, limit });
  return request(`/api/rs-peringkat?${search.toString()}`);
}

let allHospitalsPromise = null;

export function getAllHospitals(force = false) {
  if (!force && allHospitalsPromise) return allHospitalsPromise;

  allHospitalsPromise = searchHospitals({ limit: 500 })
    .then((data) => data.items || [])
    .catch((error) => {
      allHospitalsPromise = null;
      throw error;
    });

  return allHospitalsPromise;
}

export { API_BASE };
