export function cn(...values) {
  return values.filter(Boolean).join(' ');
}

export function formatNumber(value) {
  return new Intl.NumberFormat('id-ID').format(Number(value) || 0);
}

export function telHref(phone) {
  if (!phone) return '';
  const first = String(phone).split(/[;,/]/)[0].replace(/[^\d+]/g, '');
  return first ? `tel:${first}` : '';
}

export function websiteHref(url) {
  if (!url || url === 'Belum tersedia') return '';
  const value = String(url).trim();
  if (/[\u0000-\u0020<>]/.test(value)) return '';
  if (/^[a-z][a-z\d+.-]*:/i.test(value) && !/^https?:\/\//i.test(value)) return '';
  try {
    const parsed = new URL(/^https?:\/\//i.test(value) ? value : `https://${value}`);
    return ['http:', 'https:'].includes(parsed.protocol) && parsed.hostname && !parsed.username && !parsed.password ? parsed.href : '';
  } catch { return ''; }
}

export function emailHref(email) {
  if (!email || email === 'Belum tersedia') return '';
  const value=String(email).trim();
  return /^[^\s@?&#<>]+@[^\s@?&#<>]+\.[^\s@?&#<>]+$/.test(value) ? `mailto:${value}` : '';
}

export function mapsSearchUrl(hospital) {
  if (hospital?.lat != null && hospital?.lon != null) {
    return `https://www.google.com/maps/search/?api=1&query=${hospital.lat},${hospital.lon}`;
  }
  const query = [hospital?.nama, hospital?.alamat, hospital?.kabkota].filter(Boolean).join(', ');
  return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`;
}

export function directionsUrl(hospital, origin = null, mode = 'driving') {
  const params = new URLSearchParams({ api: '1', travelmode: mode });
  if (hospital?.lat != null && hospital?.lon != null) {
    params.set('destination', `${hospital.lat},${hospital.lon}`);
  } else {
    params.set('destination', encodeURIComponent(hospital?.alamat || hospital?.nama || ''));
  }
  if (origin) params.set('origin', `${origin[0]},${origin[1]}`);
  return `https://www.google.com/maps/dir/?${params.toString()}`;
}

export function openStreetMapUrl(hospital) {
  if (hospital?.lat == null || hospital?.lon == null) return '';
  return `https://www.openstreetmap.org/?mlat=${hospital.lat}&mlon=${hospital.lon}#map=17/${hospital.lat}/${hospital.lon}`;
}

export function haversineKm(lat1, lon1, lat2, lon2) {
  const R = 6371;
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

export function isBpjs(hospital) {
  return Boolean(hospital?.bpjs);
}

export function hasService(hospital, keyword) {
  const needle = keyword.toLowerCase();
  return (hospital?.layanan || []).some((item) => item.toLowerCase().includes(needle));
}

export function servicesAndFacilities(hospital) {
  return [...(hospital?.layanan || []), ...(hospital?.fasilitas || [])];
}

export function sortHospitals(items, sortBy) {
  const copy = [...items];
  if (sortBy === 'nama') {
    copy.sort((a, b) => String(a.nama).localeCompare(String(b.nama), 'id'));
  } else if (sortBy === 'kelas') {
    copy.sort(
      (a, b) =>
        String(a.kelas || 'Z').localeCompare(String(b.kelas || 'Z')) ||
        String(a.nama).localeCompare(String(b.nama), 'id'),
    );
  } else if (sortBy === 'wilayah') {
    copy.sort(
      (a, b) =>
        String(a.kabkota || 'Z').localeCompare(String(b.kabkota || 'Z'), 'id') ||
        String(a.nama).localeCompare(String(b.nama), 'id'),
    );
  }
  return copy;
}

export function pageList(current, total) {
  if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1);
  const pages = [1];
  if (current > 3) pages.push('…');
  for (let page = Math.max(2, current - 1); page <= Math.min(total - 1, current + 1); page += 1) {
    pages.push(page);
  }
  if (current < total - 2) pages.push('…');
  pages.push(total);
  return pages;
}

export function buildQuery(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') search.set(key, String(value));
  });
  return search.toString();
}

export function classBadge(kelas) {
  return `Kelas ${kelas || '—'}`;
}

export function displayRegion(region) {
  return region || 'Wilayah belum tersedia';
}

export function excerpt(text, max = 220) {
  if (!text) return '';
  const clean = String(text).replace(/\s+/g, ' ').trim();
  return clean.length > max ? `${clean.slice(0, max).trim()}…` : clean;
}

export function todayISO() {
  return new Date().toISOString().slice(0, 10);
}
