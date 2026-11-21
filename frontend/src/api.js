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

export async function getBookingStatus(code, accessKey = '') {
  return request(`/api/booking/${encodeURIComponent(code)}`, {
    headers: accessKey ? { 'X-Booking-Key': accessKey } : {},
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
