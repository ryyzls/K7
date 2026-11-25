"""NARA 3 deterministic orchestration. All hospital facts come from existing services."""
from __future__ import annotations

import asyncio
import copy
import json
import math
import re
import time
from collections import OrderedDict
from app.services import hybrid_search as hs, hospital_repo, sparql_service as sp
from app.services.chatbot.planning import (
    QueryPlan, Condition, normalize_message, is_emergency, parse_condition, leaves, prune, combine,
)
from app.services.chatbot.resolver import resolve_hospital_name, clean_hospital_query, extract_attribute
from app.services.chatbot.formatters import haversine_distance
from app.services.comparison_service import compare_hospitals
from app.services.alternatives_service import find_alternatives
from app.services.enrichment_service import get_hospital_enrichment
from app.services.dbpedia_service import get_dbpedia_info

TOOLS = {'search': hs.search, 'detail': sp.get_hospital, 'compare': compare_hospitals,
         'alternatives': find_alternatives, 'region': get_dbpedia_info}
QUICK = ['Cari RS di Medan', 'RS terdekat', 'Cari layanan jantung', 'Cari IGD']
_search_cache = OrderedDict()


async def search_plan(runner, plan, snap):
    # Cache only pre-distance evidence. Coordinates and conversation text are never cached.
    def canonical(c):
        if c is None: return None
        if c.op in ('and','or'):
            children=[]
            def flatten(node):
                if node.op==c.op:
                    for child in node.children: flatten(child)
                else: children.append(canonical(node))
            flatten(c)
            return [c.op, sorted(children,key=lambda v:json.dumps(v,sort_keys=True))]
        return [c.op,c.field,c.value,[canonical(child) for child in c.children]]
    key = (snap['time'], json.dumps([canonical(plan.condition),plan.sorting,plan.limit,sorted(plan.excluded_ids),plan.intent],sort_keys=True))
    cached = _search_cache.get(key)
    if cached and time.monotonic() - cached[0] < 30:
        return copy.deepcopy(cached[1])
    result = await runner.run('search', planned_tree=plan.condition.tree() if plan.condition else None, limit=500)
    _search_cache[key] = (time.monotonic(), copy.deepcopy(result))
    while len(_search_cache) > 64: _search_cache.popitem(last=False)
    return result


class ToolRunner:
    def __init__(self): self.calls = 0

    async def run(self, name, *args, **kwargs):
        self.calls += 1
        if self.calls > 8:
            raise ValueError('Tool budget exceeded')
        return await asyncio.wait_for(TOOLS[name](*args, **kwargs), timeout=15)


def reply(text, state, kind='text', hospitals=None, **extra):
    hospitals = hospitals or []
    quick = ['Nomor teleponnya?', 'Jam operasionalnya?', 'Ada alternatif lain?'] if len(hospitals) == 1 else ['Yang pertama tadi', 'Bandingkan yang pertama dan kedua', 'Tampilkan tiga saja'] if len(hospitals) > 1 else QUICK
    return dict(text=text, state=state, kind=kind, hospitals=hospitals,
                is_emergency=kind == 'emergency', quick_replies=quick,
                data_note='Data CariSehat; ketersediaan layanan bukan informasi real-time.', **extra)


def filters(condition):
    output = []
    def walk(c, path='0', negative=False):
        if not c: return
        if c.op in ('atom', 'text'):
            label = c.value
            if c.field == 'hours':
                parts = c.value.split(':')
                if parts[0] == 'day': label = ('Poliklinik ' if parts[1]=='poliklinik' else 'Pendaftaran ' if parts[1]=='pendaftaran' else 'Reguler ' if parts[1]=='reguler' else '') + 'buka hari ' + parts[-1]
                elif parts[0] == 'open_now': label = 'Buka sekarang'
                elif parts[0] == 'closes_ge': label = f'Poliklinik buka sampai jam {parts[-2]} {parts[-1]}'
                elif parts[0] == 'morning': label = 'Pendaftaran pagi'
            output.append({'id': path, 'field': c.field or 'hospital', 'value': c.value,
                           'label': ('Selain ' if negative else '') + label})
        for i, child in enumerate(c.children): walk(child, f'{path}.{i}', negative or c.op == 'not')
    walk(condition)
    return output


async def process(user_text, lat=None, lon=None, history=None, state=None, location_status=None, seed=None):
    # No shared conversation memory or raw-message logging. Client state contains public filters/IDs only.
    if not isinstance(user_text, str) or not user_text.strip() or len(user_text) > 4000:
        return reply('NARA membantu mencari rumah sakit. Masukkan pesan antara 1 dan 4000 karakter.', {}, 'error')
    text = normalize_message(user_text)
    if is_emergency(text):
        return reply('Segera cari pertolongan medis melalui IGD atau hubungi layanan darurat 119. Jangan menunggu hasil pencarian rumah sakit.',
                     {'last_intent': 'EMERGENCY'}, 'emergency')
    if re.search(r'[<>"\\{}\[\]*+$^|;\']|\b(select|union|where|insert|delete|drop|construct)\b', text):
        return reply('Masukkan pertanyaan pencarian rumah sakit atau layanan medis.', {}, 'clarification')
    try:
        if len(json.dumps(state or {})) > 16000: raise ValueError('State too large')
        previous = QueryPlan.model_validate((state or {}).get('plan', {}))
    except (ValueError, TypeError, AttributeError):
        return reply('Konteks tidak valid. Mulai percakapan baru.', {}, 'error')
    current = {'plan': previous.model_dump(), 'last_hospital_ids': [], 'active_filters': filters(previous.condition)}
    # Accept identifiers only; never accept client-supplied hospital facts.
    ids = (state or {}).get('last_hospital_ids', [])
    if not isinstance(ids, list) or len(ids) > 20 or any(not isinstance(x, str) or not re.fullmatch(r'rs-\d{3}', x) for x in ids):
        return reply('Konteks rumah sakit tidak valid.', {}, 'error')
    current['last_hospital_ids'] = ids[:]
    result_ids = (state or {}).get('last_result_ids', ids)
    if not isinstance(result_ids, list) or len(result_ids)>20 or any(not isinstance(x,str) or not re.fullmatch(r'rs-\d{3}',x) for x in result_ids):
        return reply('Konteks hasil tidak valid.', {}, 'error')
    current['last_result_ids'] = result_ids[:]
    if re.search(r'\b(reset|mulai ulang|percakapan baru|hapus semua filter)\b', text):
        return reply('Percakapan baru. Sebutkan rumah sakit, wilayah, atau layanan yang dicari.', {}, 'text')
    if re.fullmatch(r'(halo|hai|hi|helo|hello|selamat (pagi|siang|sore|malam))[!. ]*', text):
        return reply('Halo, saya NARA. Cari rumah sakit, layanan medis, atau informasi rumah sakit di Sumatera Utara.', {**current, 'last_intent': 'GREETING'})
    if re.search(r'^(terima kasih|makasih|thanks|thank you)\b', text):
        return reply('Sama-sama.', {**current, 'last_intent': 'GRATITUDE'})
    if re.fullmatch(r'(bye|dadah|sampai jumpa|selamat tinggal)[!. ]*', text):
        return reply('Sampai jumpa.', {**current, 'last_intent': 'FAREWELL'})
    if text in ('bantuan', '/bantuan') or re.search(r'cara (pakai|menggunakan|mencari)|kamu (siapa|bisa.*apa)|apa itu carisehat', text):
        return reply('Saya NARA, asisten pencarian rumah sakit CariSehat. Coba “RS di Medan dengan ICU”, pilih hasil, lalu tanyakan kontak atau jadwalnya. Gunakan / untuk melihat perintah.', {**current, 'last_intent': 'FAQ'})
    if 'terbaik' in text or 'rating' in text:
        return reply('Kriteria apa yang Anda perlukan: layanan, fasilitas, kelas, atau lokasi? CariSehat tidak memuat rating kualitas pelayanan.', {**current, 'last_intent': 'RATING_INQUIRY'}, 'clarification')
    if re.search(r'\b(jakarta|bandung|surabaya|luar sumatera utara)\b', text):
        return reply('Cakupan CariSehat hanya rumah sakit di Sumatera Utara.', {**current, 'last_intent': 'OUT_OF_SCOPE'})
    # Guard: hanya untuk murah/bagus standalone (bukan "lebih bagus kalau ada X" yang merupakan preferensi)
    if re.search(r'\b(murah|saya butuh dokter)\b', text) or (re.search(r'\bbagus\b', text) and not re.search(r'\blebih bagus kalau\b', text)):
        return reply('Sebutkan wilayah dan layanan yang Anda perlukan. Data biaya dan rating kualitas belum tersedia.', {**current, 'last_intent': 'KLARIFIKASI'}, 'clarification')
    if re.search(r'lebih lengkap|sesuai dengan kebutuhan|mau berobat', text):
        return reply('Sebutkan wilayah, layanan, atau fasilitas yang diperlukan. Untuk membandingkan fasilitas, pilih dua atau tiga rumah sakit.', {**current, 'last_intent':'KLARIFIKASI'}, 'clarification')
    # Symptoms already past/negative/hypothetical must never fall through to legacy emergency matching.
    if re.search(r'nyeri|sesak|stroke|pingsan|obat|dosis|diagnos|demam|sakit kepala|apakah saya', text) and not re.search(r'\b(rs|rumah sakit|cari|dokter|layanan|poli)\b', text):
        return reply('NARA membantu mencari rumah sakit dan layanan, bukan menentukan diagnosis atau obat. Sebutkan wilayah atau layanan yang Anda cari.', {**current, 'last_intent': 'OUT_OF_SCOPE'})
    runner = ToolRunner()
    try:
        return await asyncio.wait_for(_execute(text, current, previous, runner, lat, lon), 25)
    except ValueError as exc:
        # Validation messages are controlled; no stacktrace or source data in user response.
        return reply(str(exc) if str(exc).startswith(('Gunakan', 'Tanda', 'Data', 'Masukkan')) else 'Kriteria belum dapat diproses. Sederhanakan pertanyaan tanpa menghapus kebutuhan utama.', current, 'clarification')
    except Exception:
        return reply('Sumber data rumah sakit sedang tidak dapat diakses. Coba kembali; filter Anda tetap tersimpan.', current, 'error', retryable=True)


async def _execute(text, current, previous, runner, lat, lon):
    regional = re.match(r'^(?:info|profil|tentang) (?:wilayah|kota|kabupaten) (.+?)[?.]*$', text)
    if regional:
        try:
            info = await runner.run('region', regional[1])
        except Exception:
            info = None
        available = info and info.get('status') == 'ok'
        return reply('Informasi wilayah dari DBpedia.' if available else 'Informasi wilayah belum dapat diakses. Pencarian rumah sakit tetap dapat digunakan.', current, 'region', regional_info=info if available else None)
    attr = extract_attribute(text)
    if re.search(r'email|surel', text): attr = 'email'
    if re.search(r'website|situs|webnya', text): attr = 'website'
    if re.search(r'telepon|telp|kontak|nomor', text): attr = 'telepon'
    if re.search(r'jam|jadwal|bukanya', text) and not re.search(r'24 jam|buka sekarang|buka hari', text): attr = 'jam_buka'
    if re.search(r'direktur', text): attr = 'direktur'
    search_request = bool(re.search(r'\b(cari|tambah|hapus|ganti|ubah|maksud saya|kelas [abcd]|yang (?:punya|ada|memiliki)|ada dokter|di .*yang|(?:rumah sakit|rs) (?:di|dengan|untuk|selain))\b', text))
    if search_request or re.search(r'24 jam|buka sekarang|buka hari|terdekat|paling dekat', text): attr = None
    if re.search(r'spesialisasi', text): attr = 'layanan'
    if re.match(r'^apakah rs .+buka sekarang',text): attr = 'jam_buka'
    ids = current['last_hospital_ids']
    ordinals = {'pertama': 0, 'kedua': 1, 'ketiga': 2, 'keempat': 3, 'kelima': 4}
    result_ids = current.get('last_result_ids', ids)
    selected = [result_ids[index] for word, index in ordinals.items() if re.search(r'\b'+word+r'\b', text) and index < len(result_ids)]
    explicit_id = re.fullmatch(r'(?:detail|bandingkan) (rs-\d{3})(?: (rs-\d{3}))?(?: (rs-\d{3}))?', text)
    if explicit_id: selected = [x for x in explicit_id.groups() if x]
    compare = bool(re.search(r'banding|perbandingan|\bvs\b', text))
    alternative = bool(re.search(r'alternatif|yang mirip|yang lain|bukan yang itu|selain rumah sakit ini', text))
    # Resolve names only for attribute/detail/comparison requests. Search criteria go to shared search first.
    all_hospitals = hospital_repo.get_all_hospitals()
    if compare and not selected:
        chunks = re.split(r'\s+(?:dan|dengan|vs)\s+', re.sub(r'^.*?(?:bandingkan|banding|perbandingan)\s*', '', text))
        for chunk in chunks[:3]:
            resolved = resolve_hospital_name(chunk, all_hospitals)
            if resolved.get('status') == 'dominant': selected.append(resolved['target_rs']['id'])
    resolved = None
    if attr or alternative or re.match(r'^(detail|profil|info)\b', text):
        cleaned = clean_hospital_query(text)
        cleaned = re.sub(r'\b(email|website|situs|resmi|bukanya|sampai|berapa|alternatif|mirip|jam|nomor|siapa|direktur|besok|poliklinik|buka|selain|spesialisasi|sekarang)\b', ' ', cleaned).strip()
        if cleaned and not re.fullmatch(r'(nya|rs|itu|ini|yang|lain|tadi|ada|lagi|saja|dan| )+', cleaned):
            resolved = resolve_hospital_name(cleaned, all_hospitals)
            if resolved.get('status') == 'dominant': selected = [resolved['target_rs']['id']]
            elif resolved.get('status') == 'disambiguate':
                choices = resolved.get('candidates', [])[:5]
                return reply('Rumah sakit mana yang dimaksud?', current, 'clarification', choices)
        if not selected and len(ids) == 1: selected = ids[:]
    if compare and selected:
        if len(set(selected)) < 2:
            return reply('Pilih dua atau tiga rumah sakit untuk dibandingkan.', current, 'clarification')
        data = await runner.run('compare', selected[:3])
        current.update(last_intent='COMPARE', last_hospital_ids=selected[:3], last_result_ids=selected[:3])
        return reply('Perbandingan berdasarkan data yang tercatat.', current, 'comparison', data['hospitals'], comparison=data)
    if selected and not compare and not alternative:
        h = await runner.run('detail', selected[0])
        if not h: return reply('Rumah sakit tidak ditemukan.', current, 'empty')
        current.update(last_intent='ATRIBUT' if attr else 'DETAIL', last_hospital_ids=[h['id']])
        enrichment = get_hospital_enrichment(h['id'])
        if re.search(r'punya|memiliki|ada', text) and not attr in ('telepon','email','website','alamat','jam_buka'):
            snap = await hs.snapshot()
            _, atoms, _, _, _ = hs.parse(text.strip('?.'), snap)
            requirements = [a for a in atoms if a.field in ('service','facility','concept')]
            if requirements:
                condition = None
                for atom in requirements: condition = combine(condition, Condition(op='atom',field=atom.field,value=atom.value))
                evidence = await runner.run('search', planned_tree=condition.tree(), limit=500)
                known = h['id'] in {item['id'] for item in evidence['items']}
                labels = ', '.join(a.value for a in requirements)
                answer = f'{labels} tercatat dalam data rumah sakit ini.' if known else f'{labels}: Belum tersedia bukti yang memenuhi kriteria di data CariSehat; bukan berarti layanan tersebut tidak ada.'
                return reply(answer,current,'detail',[h])
        if attr in ('jarak', 'rute'):
            if lat is None or lon is None:
                return reply('Aktifkan lokasi untuk menghitung jarak garis lurus ke rumah sakit ini.', current, 'location_request', [h])
            if h.get('lat') is None or h.get('lon') is None or h.get('sumber_koordinat') not in ('osm','jalan','nama'):
                return reply('Koordinat rumah sakit belum memadai untuk menghitung jarak.', current, 'detail', [h])
            distance = haversine_distance(lat,lon,h['lat'],h['lon'])
            h = {**h, 'distance_km': distance}
            return reply(f'Jarak garis lurus ke {h["nama"]}: {distance:.1f} km; bukan jarak perjalanan.',current,'detail',[h])
        if attr == 'jam_buka':
            return reply('Jadwal tercatat per unit; bukan kepastian buka real-time. Jadwal dokter yang belum tercatat: Belum tersedia.', current, 'hours', [h], hours=enrichment.get('jam_operasional', {}))
        if attr in ('telepon', 'email', 'website', 'alamat', 'kelas', 'pemilik', 'jenis', 'bpjs', 'direktur'):
            value = h.get(attr)
            # Fallback to hospital_repo for contact fields where SPARQL construct may not join website graph
            if value in (None, '') and attr in ('telepon', 'email', 'website'):
                repo_h = hospital_repo.get_hospital_by_id(h['id'])
                if repo_h:
                    value = repo_h.get(attr)
            return reply(f"{attr.capitalize()}: {value if value not in (None, '') else 'Belum tersedia'}.", current, 'contact' if attr in ('telepon','email','website') else 'detail', [h])
        if attr in ('layanan', 'fasilitas', 'icu'):
            values = h.get('layanan', []) if attr == 'layanan' else h.get('fasilitas', [])
            label = 'Layanan tercatat' if attr == 'layanan' else 'Fasilitas tercatat (perlu konfirmasi rumah sakit)'
            return reply(f"{label}: {', '.join(values) or 'Belum tersedia'}.", current, 'detail', [h])
        return reply(f"{h['nama']} — {h.get('kabkota') or 'Belum tersedia'}, kelas {h.get('kelas') or 'Belum tersedia'}.", current, 'detail', [h])
    if attr and not selected and not re.search(r'\b(cari|yang punya|yang ada)\b', text):
        return reply('Pilih rumah sakit atau sebutkan namanya terlebih dahulu untuk melihat informasi '+('jam/jadwal yang tercatat.' if attr=='jam_buka' else 'yang diminta.'), {**current,'last_intent':'JAM_BUKA_INQUIRY' if attr=='jam_buka' else 'KLARIFIKASI'}, 'clarification')

    snap = await hs.snapshot()
    plan = previous.model_copy(deep=True)
    nearest = bool(re.search(r'terdekat|paling dekat|dekat (saya|sini)|sekitar saya', text))
    limit_match = re.search(r'\b(\d{1,2}|satu|dua|tiga|empat|lima|sepuluh)\s*(?:rs|rumah sakit|saja|hasil)', text)
    numbers = {'satu':1,'dua':2,'tiga':3,'empat':4,'lima':5,'sepuluh':10}
    limit = min(20, max(1, numbers.get(limit_match[1], int(limit_match[1]) if limit_match[1].isdigit() else 5))) if limit_match else None

    # --- Preference detection: "kalau bisa X", "lebih bagus kalau ada X", "utamakan X" ---
    # These signal optional criteria, not mandatory. Mandatory part comes before the preference phrase.
    pref_match = re.search(
        r'\b(?:kalau bisa|lebih bagus kalau ada|lebih bagus kalau|utamakan|lebih baik kalau ada|lebih baik kalau)\b(.+)$',
        text
    )
    pref_text = pref_match.group(1).strip() if pref_match else None
    mandatory_text = text[:pref_match.start()].strip() if pref_match else text

    operation = 'remove' if re.match(r'^(hapus|hilangkan|tanpa filter|gausah)', text) else 'replace' if re.search(r'\b(ganti|ubah|maksud saya|bukan medan)\b', text) else 'add' if re.match(r'^(yang|kelas|tambah|kalau|dan|urutkan|tampilkan|\d|tiga|dua|lima|ada yang)', text) else 'new'
    if nearest and len(text.split()) < 8 or limit_match and len(text.split()) < 6: operation = 'add'

    def clean_search(raw):
        t = re.sub(r'\b(?:carikan|tolong|dong|dong ya|ga|gak|bisa|saja|berapa|eh|ganti|ubah|ke|tambah|tambahkan|juga|hapus|hilangkan|tampilkan|urutkan|paling|terdekat|dekat|dari lokasi saya|lokasi saya|nomor teleponnya|terus kasih)\b', ' ', raw)
        t = re.sub(r'\b(?:satu|dua|tiga|empat|lima|sepuluh|\d{1,2})\s*(?=rs|rumah sakit|hasil|$)', '', t.strip())
        t = re.sub(r'\b(?:bandingkan fasilitasnya|bandingkan|kasih kontaknya|hasil)\b', ' ', t)
        t = re.sub(r'\b(?:saya|mau|cari|rekomendasikan|untuk|pemeriksaan|fasilitas|apa|jadi|maksud|sekitar)\b', ' ', t)
        t = re.sub(r'\s+', ' ', t).strip(' .,?!')
        if limit_match:
            t = re.sub(r'\b(?:satu|dua|tiga|empat|lima|sepuluh|\d{1,2})\b', '', t).strip()
        return t

    search_text = clean_search(mandatory_text)

    if operation == 'replace' and previous.sorting == 'distance' and (current.get('pending') == 'location' or not (lat is not None and lon is not None)):
        plan.sorting = 'relevance'
    if alternative:
        source_id = (selected or ids or [None])[0]
        if not source_id: return reply('Pilih rumah sakit sebagai acuan alternatif.', current, 'clarification')
        # Mandatory criteria still go through the shared search. Never relax them for similarity.
        # A prior name query identifies the reference, not a mandatory alternative name.
        if plan.condition and plan.condition.op == 'text': plan.condition = None
        result = await search_plan(runner, plan, snap)
        allowed = {h['id'] for h in result['items']}
        alternatives = await runner.run('alternatives', source_id, limit=5, allowed_ids=allowed)
        candidates = alternatives.get('alternatives', [])
        hospitals = [h for h in candidates if h.get('id') in allowed and h.get('id') != source_id][:plan.limit]
        current.update(last_intent='ALTERNATIVES', last_hospital_ids=[h['id'] for h in hospitals])
        return reply(f'Ditemukan {len(hospitals)} alternatif yang sesuai filter aktif.', current, 'alternatives', hospitals)
    if operation == 'new':
        plan = QueryPlan()
    plan.operation = operation
    plan.intent = 'COMPARE' if compare else 'SEARCH_NEARBY' if nearest else 'SEARCH_FILTER'
    if limit: plan.limit = limit
    if nearest: plan.sorting = 'distance'
    if re.search(r'urut.*nama|abjad', text): plan.sorting = 'name'; search_text = ''
    node = None
    if search_text not in ('', 'rs', 'rumah sakit', 'yang', 'yang saja', 'yang dekat', 'cari rs', 'cari rumah sakit', 'cari'):
        node = parse_condition(search_text, snap)
    if operation == 'remove':
        values = {(c.field, c.value) for c in leaves(node)}
        plan.condition = prune(plan.condition, lambda c: (c.field, c.value) in values)
    elif operation == 'replace':
        fields = {c.field for c in leaves(node)}
        plan.condition = combine(prune(plan.condition, lambda c: c.field in fields), node)
    else:
        plan.condition = combine(plan.condition, node)

    # Store parsed preferences in plan for downstream ranking & oracle checks
    pref_labels: list[str] = []
    pref_node = None
    if pref_text:
        pref_search = clean_search(pref_text)
        if pref_search:
            try:
                pref_node = parse_condition(pref_search, snap)
                if pref_node:
                    pref_labels = [c.value for c in leaves(pref_node) if c.op == 'atom']
            except Exception:
                pref_node = None
    plan.preferences = pref_labels

    plan = QueryPlan.model_validate(plan.model_dump())
    current.update(plan=plan.model_dump(), active_filters=filters(plan.condition), last_intent='SEARCH_NEARBY' if plan.sorting == 'distance' else 'SEARCH_FILTER')
    if plan.sorting == 'distance' and not (lat is not None and lon is not None and math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
        current['pending'] = 'location'
        return reply('Aktifkan lokasi dengan tombol Lokasi, atau ketik wilayah secara manual. Jarak memerlukan posisi Anda.', current, 'location_request')
    if not plan.condition and not nearest and not limit and operation == 'new':
        return reply('Sebutkan nama rumah sakit, wilayah, layanan, atau fasilitas yang dicari.', current, 'clarification')
    if plan.condition and all(c.op == 'text' for c in leaves(plan.condition)) and not re.search(r'\b(rs|rumah sakit|cari|layanan|dokter)\b', text):
        # No weak fuzzy hospital matches for arbitrary conversational sentences.
        cleaned = clean_hospital_query(search_text)
        if not any(hs.name_score(cleaned, row) >= 700 for row in snap['rows'].values()):
            return reply('NARA berfokus pada pencarian rumah sakit dan layanan kesehatan di Sumatera Utara.', {**current, 'last_intent':'OUT_OF_SCOPE'})
    result = await search_plan(runner, plan, snap)
    hospitals = result['items']
    # Identity verification against source snapshot, after the shared SPARQL mandatory filter execution.
    hospitals = [h for h in hospitals if h.get('uri') in snap['rows'] and h['id'] == h['uri'].rsplit('/',1)[-1] and h['id'] not in plan.excluded_ids]
    note = ''
    if plan.sorting == 'distance':
        valid = []
        for h in hospitals:
            if h.get('lat') is not None and h.get('lon') is not None and h.get('sumber_koordinat') in ('osm', 'jalan', 'nama'):
                h = dict(h); h['distance_km'] = haversine_distance(lat, lon, h['lat'], h['lon']); valid.append(h)
        hospitals = sorted(valid, key=lambda h: h['distance_km'])
        note = ' Jarak garis lurus, hanya di antara rumah sakit dengan koordinat memadai; bukan jarak perjalanan.'
    elif plan.sorting == 'name': hospitals.sort(key=lambda h: h['nama'].casefold())

    # --- Preference-based re-ranking: preferred hospitals bubble to top ---
    # This is ONLY a re-ordering of mandatory results; no mandatory filter is relaxed.
    if pref_node and hospitals:
        pref_result = await search_plan(runner, QueryPlan(condition=pref_node), snap)
        preferred_ids = {h['id'] for h in pref_result['items'] if h.get('uri') in snap['rows']}
        # Stable partition: preferred first, then others
        preferred = [h for h in hospitals if h['id'] in preferred_ids]
        rest = [h for h in hospitals if h['id'] not in preferred_ids]
        hospitals = preferred + rest
        if pref_labels:
            note += f' Diutamakan: {", ".join(pref_labels)}.'

    total = len(hospitals)
    hospitals = hospitals[:plan.limit]
    current.update(last_hospital_ids=[h['id'] for h in hospitals], last_result_ids=[h['id'] for h in hospitals], pending=None)
    if compare and len(hospitals) >= 2:
        data = await runner.run('compare', [h['id'] for h in hospitals[:3]])
        current['last_intent'] = 'COMPARE'
        return reply(f'Perbandingan {min(3, len(hospitals))} rumah sakit sesuai kriteria.'+note, current, 'comparison', hospitals, comparison=data)
    name_query = plan.condition and any(c.op == 'text' for c in leaves(plan.condition)) and not any(c.field in ('service','facility','class','hours','owner') for c in leaves(plan.condition)) and not re.search(r'\b(selain|bukan|jalan|johor)\b', text)
    if hospitals and name_query and len(hospitals) == 1:
        current['last_intent'] = 'DETAIL'
    if not hospitals and name_query: current['last_intent'] = 'NOT_FOUND'
    message = f'Ditemukan {total} rumah sakit sesuai kriteria. Menampilkan {len(hospitals)}.' if total else 'Rumah sakit tidak ditemukan untuk seluruh kriteria tersebut. Pilih filter yang ingin dihapus atau diubah.'
    labels = [c.value for c in leaves(plan.condition) if c.op=='atom' and c.field in ('service','facility','region')]
    if labels: message += ' Kriteria: '+', '.join(dict.fromkeys(labels))+'.'
    if re.search(r'\bjalan\b', text): message += ' Lokasi berdasarkan alamat yang tercatat; jarak memerlukan posisi Anda.'
    if hospitals and name_query:
        message = '\n'.join(h['nama'] for h in hospitals)
        if len(hospitals) > 1:
            current['last_intent'] = 'DISAMBIGUASI'
            message = 'Pilih rumah sakit yang dimaksud:\n' + message
    if any(c.field == 'hours' for c in leaves(plan.condition)): note += ' Jadwal statis dalam WIB, bukan status operasional real-time.'
    return reply(message+note, current, 'hospital_list' if total else 'empty', hospitals, total=total,
                 active_filters=filters(plan.condition))
