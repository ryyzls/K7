"""Normalize sourced schedules, without inventing missing hours or closed days."""
import re
from urllib.parse import urlsplit

DAYS = ['Senin', 'Selasa', 'Rabu', 'Kamis', 'Jumat', 'Sabtu', 'Minggu']
UNIT_NAMES = {'reguler': 'Jam Reguler', 'poliklinik_rawat_jalan': 'Poliklinik Rawat Jalan',
              'pendaftaran': 'Pendaftaran Pasien'}


def day_indexes(value):
    value = str(value or '').lower().replace('jum\u2019at', 'jumat').replace("jum'at", 'jumat')
    found = [(match.start(), index) for index, day in enumerate(DAYS)
             for match in re.finditer(day.lower(), value)]
    found.sort()
    if len(found) == 2 and re.search(r'[-–—]|sampai|s/d', value):
        start, end = found[0][1], found[1][1]
        return list(range(start, end + 1)) if start <= end else list(range(start, 7)) + list(range(end + 1))
    return sorted({index for _, index in found})


def source_url(value):
    try:
        url = urlsplit(str(value or ''))
        return url.scheme in ('https', 'http') and bool(url.hostname) and not url.username
    except ValueError:
        return False


def normalize_unit(records):
    values = [set() for _ in DAYS]
    facts = []
    for row in records:
        source = row.get('source_url') or row.get('sumber')
        if not source_url(source):
            continue
        indexes = row.get('hari_angka')
        if indexes is None:
            indexes = day_indexes(row.get('hari'))
        indexes = [i for i in indexes if isinstance(i, int) and 0 <= i < 7]
        start, end = row.get('jam_buka'), row.get('jam_tutup')
        valid = lambda t: bool(re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d|24:00', str(t or '')))
        closed = re.search(r'tutup|libur', str(row.get('keterangan', '')), re.I)
        if valid(start) and valid(end):
            label = f'{start} – {end}'
        elif closed:
            label = 'Tutup'
        else:
            continue
        for index in indexes:
            values[index].add(label)
        facts.append({**row, 'source_url': source})
    return {
        'jadwal_harian': [{'hari': day, 'jam': next(iter(values[i])) if len(values[i]) == 1 else 'Belum tersedia'}
                          for i, day in enumerate(DAYS)],
        'facts': facts,
        'conflicting_days': [DAYS[i] for i, value in enumerate(values) if len(value) > 1],
    }


def schedules(rs_id, code, info, candidates):
    grouped = {key: [] for key in UNIT_NAMES}
    for unit in info.get('unit_operasional', []):
        name = unit.get('unit', '').lower()
        key = 'pendaftaran' if 'daftar' in name else 'poliklinik_rawat_jalan' if 'poli' in name else None
        if key and source_url(unit.get('sumber')):
            for row in unit.get('jadwal') or []:
                grouped[key].append({**row, 'source_url': unit['sumber'],
                                     'status_verifikasi': unit.get('status_verifikasi'),
                                     'checked_at': unit.get('checked_at')})
    authoritative = {key for key, rows in grouped.items() if rows}
    for row in candidates:
        if row.get('id_carisehat') != rs_id or str(row.get('kode_kemenkes')) != str(code):
            continue
        if row.get('status') not in ('VERIFIED_OFFICIAL', 'CORROBORATED', 'CANDIDATE', 'REVIEW_REQUIRED'):
            continue
        name = row.get('unit_type', '').lower()
        key = 'pendaftaran' if 'daftar' in name or 'loket' in name else 'poliklinik_rawat_jalan' if 'poli' in name else 'reguler' if name in ('umum', 'rs') else None
        if key and key not in authoritative:
            grouped[key].append(row)
    return {key: {'unit': UNIT_NAMES[key], **normalize_unit(rows)} for key, rows in grouped.items()}
