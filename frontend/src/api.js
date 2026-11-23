const API_BASE = import.meta.env.VITE_API_BASE || '';

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      Accept: 'application/json',
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...(options.headers || {}),
    },
  });

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const payload = await res.json();
      if (payload?.detail) detail = payload.detail;
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

export async function compareHospitals(ids) {
  const search = cleanParams({ ids: ids.join(',') });
  return request(`/api/compare?${search.toString()}`);
}

export async function getHospital(rsId) {
  return request(`/api/hospitals/${encodeURIComponent(rsId)}`);
}

export async function getHospitalOperationalHours(rsId) {
  return request(`/api/hospitals/${encodeURIComponent(rsId)}/operational-hours`);
}

export async function getHospitalAlternatives(rsId, limit = 4) {
  const search = cleanParams({ limit });
  return request(`/api/hospitals/${encodeURIComponent(rsId)}/alternatives?${search.toString()}`);
}

export async function deleteBooking(kode) {
  return request(`/api/booking/${encodeURIComponent(kode)}`, {
    method: 'DELETE',
  });
}

let allHospitalsPromise = null;

/**
 * The dataset contains ~206 records, so one cached request is cheaper than
 * re-fetching the same collection for the home and detail screens.
 */
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
