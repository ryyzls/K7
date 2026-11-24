const SYMPTOM_MAPPINGS = [
  {
    pattern: /\b(?:cuci\s*darah|hemodialisa|hemodialisis|dialisis|gagal\s*ginjal)\b/i,
    label: 'Hemodialisa (Cuci Darah)',
    serviceKeywords: ['hemodialisa', 'hemodialisis', 'dialisis', 'ginjal'],
  },
  {
    pattern: /\b(?:katarak|rabun|periksa\s*mata|sakit\s*mata|optik|retina|glaukoma|mata)\b/i,
    label: 'Poliklinik Mata',
    serviceKeywords: ['mata'],
  },
  {
    pattern: /\b(?:sakit\s*gigi|gigi\s*bungsu|tambal\s*gigi|cabut\s*gigi|behel|ortodonti|mulut|gigi)\b/i,
    label: 'Poliklinik Gigi & Mulut',
    serviceKeywords: ['gigi'],
  },
  {
    pattern: /\b(?:melahirkan|persalinan|hamil|kehamilan|usg|kandungan|kebidanan|obgyn|ponek|caesar|sesar)\b/i,
    label: 'Kebidanan & Kandungan',
    serviceKeywords: ['kebidanan', 'kandungan', 'obgyn', 'ponek'],
  },
  {
    pattern: /\b(?:patah\s*tulang|tulang|sendi|keseleo|ortopedi|bedah\s*tulang)\b/i,
    label: 'Ortopedi & Tulang',
    serviceKeywords: ['ortopedi', 'bedah'],
  },
  {
    pattern: /\b(?:nyeri\s*dada|serangan\s*jantung|jantung|kardio|ekg|ekokardiografi|kateterisasi)\b/i,
    label: 'Jantung & Pembuluh Darah',
    serviceKeywords: ['jantung', 'kardio'],
  },
  {
    pattern: /\b(?:tbc|tuberkulosis|sesak\s*napas|asma|batuk\s*darah|paru|respirasi)\b/i,
    label: 'Paru & Pernapasan',
    serviceKeywords: ['paru'],
  },
  {
    pattern: /\b(?:stroke|saraf|syaraf|kejang|epilepsi|migrain|vertigo)\b/i,
    label: 'Saraf (Neurologi)',
    serviceKeywords: ['saraf', 'neurologi'],
  },
  {
    pattern: /\b(?:kejiwaan|jiwa|depresi|stres|cemas|psikiater|psikolog|psikiatri)\b/i,
    label: 'Kesehatan Jiwa',
    serviceKeywords: ['jiwa', 'psikiatri', 'psikologi'],
  },
  {
    pattern: /\b(?:telinga|hidung|tenggorokan|tht|pendengaran|sinus)\b/i,
    label: 'THT-KL',
    serviceKeywords: ['tht'],
  },
  {
    pattern: /\b(?:kulit|kelamin|alergi\s*kulit|dermatologi)\b/i,
    label: 'Kulit & Kelamin',
    serviceKeywords: ['kulit'],
  },
  {
    pattern: /\b(?:diabetes|gula\s*darah|hipertensi|darah\s*tinggi|lambung|maag|penyakit\s*dalam|internis)\b/i,
    label: 'Penyakit Dalam',
    serviceKeywords: ['penyakit dalam', 'dalam'],
  },
  {
    pattern: /\b(?:imunisasi|tumbuh\s*kembang|demam\s*anak|bayi|nicu|picu|perinatologi|anak)\b/i,
    label: 'Kesehatan Anak',
    serviceKeywords: ['anak', 'nicu', 'picu', 'perinatologi'],
  },
  {
    pattern: /\b(?:fisioterapi|rehabilitasi|rehab\s*medik|terapi\s*wicara)\b/i,
    label: 'Rehabilitasi Medik',
    serviceKeywords: ['rehabilitasi', 'fisioterapi'],
  },
  {
    pattern: /\b(?:igd|ugd|gawat\s*darurat|kecelakaan|darurat|ambulans)\b/i,
    label: 'Instalasi Gawat Darurat (IGD)',
    serviceKeywords: ['ugd', 'igd', 'gawat darurat', 'darurat'],
  },
  {
    pattern: /\b(?:ct\s*scan|mri|rontgen|usg|radiologi)\b/i,
    label: 'Radiologi & Pencitraan',
    serviceKeywords: ['radiologi', 'ct scan', 'mri'],
  },
  {
    pattern: /\b(?:cek\s*darah|laboratorium|patologi|lab)\b/i,
    label: 'Laboratorium Klinik',
    serviceKeywords: ['laboratorium', 'patologi'],
  },
  {
    pattern: /\b(?:operasi|bedah)\b/i,
    label: 'Pelayanan Bedah',
    serviceKeywords: ['bedah', 'operasi'],
  },
  {
    pattern: /\b(?:icu|ruang\s*intensif|iccu)\b/i,
    label: 'Perawatan Intensif (ICU)',
    serviceKeywords: ['icu', 'intensif'],
  },
];

const REGION_PATTERNS = [
  { pattern: /\b(?:kota\s+)?medan\b/i, keywords: ['kota medan', 'medan'] },
  { pattern: /\b(?:kota\s+)?binjai\b/i, keywords: ['kota binjai', 'binjai'] },
  { pattern: /\b(?:kota\s+)?pematang\s*siantar|siantar\b/i, keywords: ['pematangsiantar', 'pematang siantar'] },
  { pattern: /\b(?:kota\s+)?tebing\s*tinggi\b/i, keywords: ['tebing tinggi'] },
  { pattern: /\b(?:kota\s+)?sibolga\b/i, keywords: ['sibolga'] },
  { pattern: /\b(?:kota\s+)?tanjung\s*balai|tanjungbalai\b/i, keywords: ['tanjungbalai', 'tanjung balai'] },
  { pattern: /\b(?:kota\s+)?padang\s*sidempuan|padangsidimpuan|sidimpuan\b/i, keywords: ['padangsidimpuan', 'padang sidempuan'] },
  { pattern: /\b(?:kota\s+)?gunungsitoli|gunung\s*sitoli\b/i, keywords: ['gunungsitoli', 'gunung sitoli'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?deli\s*serdang|lubuk\s*pakam\b/i, keywords: ['deli serdang'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?karo|kabanjahe|berastagi\b/i, keywords: ['karo'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?toba|balige\b/i, keywords: ['toba'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?samosir|pangururan\b/i, keywords: ['samosir'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?simalungun|raya|perdagangan\b/i, keywords: ['simalungun'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?langkat|stabat\b/i, keywords: ['langkat'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?asahan|kisaran\b/i, keywords: ['asahan'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?serdang\s*bedagai|sergai|sei\s*rampah\b/i, keywords: ['serdang bedagai'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?batu\s*bara|limapuluh\b/i, keywords: ['batu bara', 'batubara'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?labuhan\s*batu|labuhanbatu|rantau\s*prapat|rantauprapat\b/i, keywords: ['labuhanbatu', 'labuhan batu'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?dairi|sidikalang\b/i, keywords: ['dairi'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?tapanuli\s*utara|tarutung\b/i, keywords: ['tapanuli utara'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?tapanuli\s*tengah|pandan\b/i, keywords: ['tapanuli tengah'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?tapanuli\s*selatan|sipirok\b/i, keywords: ['tapanuli selatan'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?mandailing\s*natal|madina|panyabungan\b/i, keywords: ['mandailing natal'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?humbang\s*hasundutan|doloksanggul\b/i, keywords: ['humbang hasundutan'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?pakpak\s*bharat|salak\b/i, keywords: ['pakpak bharat'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?padang\s*lawas\s*utara|gunung\s*tua\b/i, keywords: ['padang lawas utara'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?padang\s*lawas|sibuhuan\b/i, keywords: ['padang lawas'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?nias\s*selatan|teluk\s*dalam\b/i, keywords: ['nias selatan'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?nias\s*utara\b/i, keywords: ['nias utara'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?nias\s*barat\b/i, keywords: ['nias barat'] },
  { pattern: /\b(?:kab(?:upaten)?\.?\s+)?nias\b/i, keywords: ['nias'] },
];

const HOSPITAL_NAME_HINTS = [
  { pattern: /\b(?:adam\s*malik|ham|rsup\s*ham)\b/i, label: 'RSUP H. Adam Malik' },
  { pattern: /\b(?:pirngadi|dr\s*pirngadi)\b/i, label: 'RSUD Dr. Pirngadi Medan' },
  { pattern: /\b(?:murni\s*teguh|mtmh)\b/i, label: 'RSU Murni Teguh Memorial' },
  { pattern: /\b(?:columbia\s*asia|cam)\b/i, label: 'RS Columbia Asia Medan' },
  { pattern: /\b(?:siloam|dhirga\s*surya)\b/i, label: 'RS Siloam Dhirga Surya' },
  { pattern: /\b(?:elisabeth|elisabet|santa\s*elisabeth)\b/i, label: 'RS Santa Elisabeth Medan' },
  { pattern: /\b(?:hermina)\b/i, label: 'RSU Hermina Medan' },
  { pattern: /\b(?:royal\s*prima)\b/i, label: 'RSU Royal Prima' },
  { pattern: /\b(?:djoelham)\b/i, label: 'RSUD Dr. R.M. Djoelham Binjai' },
  { pattern: /\b(?:djasamen\s*saragih)\b/i, label: 'RSUD Dr. Djasamen Saragih Siantar' },
  { pattern: /\b(?:fl\s*tobing)\b/i, label: 'RSUD Dr. Ferdinand Lumban Tobing' },
  { pattern: /\b(?:hkbp\s*balige)\b/i, label: 'RSU HKBP Balige' },
  { pattern: /\b(?:usu|chairuddin)\b/i, label: 'RS Pendidikan USU' },
  { pattern: /\b(?:polda|bhayangkara)\b/i, label: 'RS Bhayangkara Tk. II Medan' },
  { pattern: /\b(?:ildrem)\b/i, label: 'RS Jiwa Prof. Dr. M. Ildrem' },
];

function matchRegionOption(keywords, kabkotaOptions = []) {
  if (!kabkotaOptions.length) return '';
  for (const kw of keywords) {
    const exact = kabkotaOptions.find((opt) => opt.toLowerCase() === kw.toLowerCase());
    if (exact) return exact;
  }
  for (const kw of keywords) {
    const partial = kabkotaOptions.find((opt) => opt.toLowerCase().includes(kw.toLowerCase()));
    if (partial) return partial;
  }
  return '';
}

function matchServiceOption(serviceKeywords, layananOptions = []) {
  if (!layananOptions.length) return '';
  for (const kw of serviceKeywords) {
    const exact = layananOptions.find((opt) => opt.toLowerCase() === kw.toLowerCase());
    if (exact) return exact;
  }
  const matches = layananOptions.filter((opt) =>
    serviceKeywords.some((kw) => opt.toLowerCase().includes(kw.toLowerCase())),
  );
  return matches.length === 1 ? matches[0] : '';
}

export function parseNaturalQuery(rawQuery, options = {}) {
  const original = String(rawQuery || '').trim();
  if (!original) {
    return {
      original: '',
      residualQuery: '',
      kelas: '',
      bpjs: false,
      kabkota: '',
      layananOption: '',
      serviceKeywords: [],
      serviceLabel: '',
      detectedTags: [],
    };
  }

  let working = ` ${original} `;
  let kelas = '';
  let bpjs = false;
  let kabkota = '';
  let layananOption = '';
  let serviceKeywords = [];
  let serviceLabel = '';
  const detectedTags = [];

  // 1. Cek petunjuk nama rumah sakit spesifik (untuk pill info, tetap biarkan di residualQuery)
  const nameHint = HOSPITAL_NAME_HINTS.find((item) => item.pattern.test(working));
  if (nameHint && original.toLowerCase() !== nameHint.label.toLowerCase()) {
    detectedTags.push({
      label: nameHint.label,
      tone: 'bg-toba-mist text-toba-dark border-toba/30',
    });
  }

  // 2. Ekstraksi Kelas RS (contoh: "kelas B", "tipe A", "kls C")
  const kelasRegex = /\b(?:kelas|kls|tipe)\s*([a-dA-D])\b/i;
  const kelasMatch = working.match(kelasRegex);
  if (kelasMatch) {
    kelas = kelasMatch[1].toUpperCase();
    working = working.replace(kelasRegex, ' ');
    detectedTags.push({
      label: `Kelas ${kelas}`,
      tone: 'bg-amber-50 text-amber-800 border-amber-200',
    });
  }

  // 3. Ekstraksi Kepesertaan BPJS
  const bpjsRegex = /\b(?:menerima\s+)?(?:bpjs(?:\s+kesehatan)?|jkn|kis|askes)\b/i;
  if (bpjsRegex.test(working)) {
    bpjs = true;
    working = working.replace(bpjsRegex, ' ');
    detectedTags.push({
      label: 'BPJS Kesehatan',
      tone: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    });
  }

  // 4. Ekstraksi Kabupaten / Kota Sumatera Utara
  for (const reg of REGION_PATTERNS) {
    if (reg.pattern.test(working)) {
      const resolvedRegion = matchRegionOption(reg.keywords, options.kabkota || []);
      kabkota = resolvedRegion || reg.keywords[0];
      working = working.replace(reg.pattern, ' ');
      detectedTags.push({
        label: resolvedRegion || kabkota,
        tone: 'bg-sky-50 text-sky-800 border-sky-200',
      });
      break;
    }
  }

  // 5. Ekstraksi Keluhan Awam / Layanan Medis
  for (const sym of SYMPTOM_MAPPINGS) {
    if (sym.pattern.test(working)) {
      serviceKeywords = sym.serviceKeywords;
      serviceLabel = sym.label;
      layananOption = matchServiceOption(sym.serviceKeywords, options.layanan || []);
      working = working.replace(sym.pattern, ' ');
      detectedTags.push({
        label: sym.label,
        tone: 'bg-indigo-50 text-indigo-800 border-indigo-200',
      });
      break;
    }
  }

  // 6. Bersihkan kata penghubung / generik sisa jika sudah ada kriteria terstruktur
  const hasStructured = Boolean(kelas || bpjs || kabkota || serviceKeywords.length);
  let residual = working
    .replace(/\b(?:di|ke|yang|untuk|dengan|area|wilayah|sekitar|daerah)\b/gi, ' ')
    .replace(/\s+/g, ' ')
    .trim();

  if (hasStructured && /^(?:rs|rsu|rsud|rsup|rsia|rumah\s+sakit)$/i.test(residual)) {
    residual = '';
  }

  return {
    original,
    residualQuery: residual,
    kelas,
    bpjs,
    kabkota,
    layananOption,
    serviceKeywords,
    serviceLabel,
    detectedTags,
  };
}

export function matchesServiceKeywords(hospital, serviceKeywords = []) {
  if (!serviceKeywords.length) return true;
  const pool = [...(hospital.layanan || []), ...(hospital.fasilitas || [])]
    .join(' ')
    .toLowerCase();
  return serviceKeywords.some((kw) => pool.includes(kw.toLowerCase()));
}

export function buildAutocompleteSuggestions(query, hospitals = [], options = {}) {
  const q = String(query || '').trim().toLowerCase();
  if (q.length < 2) {
    return { hospitals: [], services: [], regions: [], hasAny: false };
  }

  // 1. Saran Rumah Sakit (maksimal 5)
  const hospitalMatches = [];
  for (const h of hospitals) {
    const nama = String(h.nama || '').toLowerCase();
    const kab = String(h.kabkota || '').toLowerCase();
    const alamat = String(h.alamat || '').toLowerCase();
    let score = 0;
    if (nama.startsWith(q)) score = 100;
    else if (nama.includes(q)) score = 85;
    else if (HOSPITAL_NAME_HINTS.some((hint) => hint.pattern.test(q) && hint.pattern.test(nama))) score = 95;
    else if (kab.includes(q) || alamat.includes(q)) score = 50;

    if (score > 0) {
      hospitalMatches.push({ hospital: h, score });
    }
  }
  hospitalMatches.sort((a, b) => b.score - a.score || a.hospital.nama.localeCompare(b.hospital.nama));

  // 2. Saran Layanan & Keluhan (maksimal 4)
  const serviceMatches = [];
  const seenServices = new Set();

  for (const sym of SYMPTOM_MAPPINGS) {
    if (sym.pattern.test(q) || sym.label.toLowerCase().includes(q)) {
      if (!seenServices.has(sym.label)) {
        seenServices.add(sym.label);
        serviceMatches.push({
          label: sym.label,
          query: q,
          layanan: matchServiceOption(sym.serviceKeywords, options.layanan || []),
        });
      }
    }
  }

  for (const srv of options.layanan || []) {
    if (srv.toLowerCase().includes(q) && !seenServices.has(srv)) {
      seenServices.add(srv);
      serviceMatches.push({
        label: srv,
        query: '',
        layanan: srv,
      });
    }
  }

  // 3. Saran Kabupaten / Kota (maksimal 3)
  const regionMatches = (options.kabkota || [])
    .filter((reg) => reg.toLowerCase().includes(q))
    .slice(0, 3);

  const topHospitals = hospitalMatches.slice(0, 5).map((item) => item.hospital);
  const topServices = serviceMatches.slice(0, 4);

  return {
    hospitals: topHospitals,
    services: topServices,
    regions: regionMatches,
    hasAny: topHospitals.length > 0 || topServices.length > 0 || regionMatches.length > 0,
  };
}

export function computeSmartFallback(allHospitals = [], effectiveFilters = {}) {
  if (!allHospitals.length) return null;

  // Kasus 1: Wilayah dipilih + Kelas tertentu dipilih, namun 0 hasil -> tampilkan RS lain di wilayah tsb + RS kelas tsb di Sumut
  if (effectiveFilters.kabkota && effectiveFilters.kelas) {
    const sameRegionOtherClass = allHospitals.filter(
      (h) =>
        h.kabkota === effectiveFilters.kabkota &&
        (!effectiveFilters.bpjs || h.bpjs),
    );
    const sameClassOtherRegion = allHospitals.filter(
      (h) =>
        h.kelas === effectiveFilters.kelas &&
        (!effectiveFilters.bpjs || h.bpjs),
    );
    const combined = [...sameRegionOtherClass, ...sameClassOtherRegion];
    const unique = Array.from(new Map(combined.map((h) => [h.id, h])).values()).slice(0, 6);
    if (unique.length) {
      return {
        title: `Belum tersedia RS Kelas ${effectiveFilters.kelas} di ${effectiveFilters.kabkota}`,
        description: `Berikut fasilitas kesehatan yang tersedia di ${effectiveFilters.kabkota} serta rumah sakit rujukan Kelas ${effectiveFilters.kelas} di Sumatera Utara.`,
        items: unique,
      };
    }
  }

  // Kasus 2: Wilayah dipilih + Layanan spesifik dipilih -> tampilkan semua RS di wilayah tsb
  if (effectiveFilters.kabkota && (effectiveFilters.layanan || effectiveFilters.serviceKeywords?.length)) {
    const inRegion = allHospitals
      .filter((h) => h.kabkota === effectiveFilters.kabkota && (!effectiveFilters.bpjs || h.bpjs))
      .slice(0, 6);
    if (inRegion.length) {
      return {
        title: `Layanan spesifik tersebut belum tercatat di ${effectiveFilters.kabkota}`,
        description: `Menampilkan rumah sakit yang beroperasi di ${effectiveFilters.kabkota} sebagai alternatif terdekat.`,
        items: inRegion,
      };
    }
  }

  // Kasus 3: Filter umum lainnya -> tampilkan RS rujukan utama di Sumut
  const fallbackPool = allHospitals
    .filter((h) => (effectiveFilters.bpjs ? h.bpjs : true))
    .slice(0, 6);

  if (!fallbackPool.length) return null;
  return {
    title: 'Menampilkan rekomendasi rumah sakit rujukan di Sumatera Utara',
    description: 'Tidak ditemukan kecocokan persis untuk seluruh kombinasi filter yang dipilih.',
    items: fallbackPool,
  };
}
