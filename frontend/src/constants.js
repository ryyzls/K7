export const KELAS_COLOR = {
  A: '#BE123C',
  B: '#0284C7',
  C: '#059669',
  D: '#64748B',
};

export const KELAS_DESCRIPTION = {
  A: 'Subspesialis luas',
  B: 'Spesialis lengkap',
  C: 'Spesialis dasar',
  D: 'Pelayanan dasar',
};

export const KELAS_OPTIONS = [
  { value: 'A', label: 'Kelas A' },
  { value: 'B', label: 'Kelas B' },
  { value: 'C', label: 'Kelas C' },
  { value: 'D', label: 'Kelas D' },
];

export const JENIS_OPTIONS = [
  { value: 'Umum', label: 'Rumah Sakit Umum' },
  { value: 'Khusus', label: 'Rumah Sakit Khusus' },
];

export const SERVICE_META = {
  'UGD 24 Jam': { icon: 'emergency', tone: 'red' },
  Ambulans: { icon: 'ambulance', tone: 'red' },
  Radiologi: { icon: 'radiology', tone: 'blue' },
  'Radiologi Toraks': { icon: 'radiology', tone: 'blue' },
  Laboratorium: { icon: 'science', tone: 'violet' },
  Bedah: { icon: 'surgical', tone: 'blue' },
  'Bedah Katarak': { icon: 'visibility', tone: 'sky' },
  'Bedah Mulut': { icon: 'dentistry', tone: 'sky' },
  Anestesi: { icon: 'monitor_heart', tone: 'rose' },
  Apotek: { icon: 'medication', tone: 'emerald' },
  Farmasi: { icon: 'medication', tone: 'emerald' },
  'Dialisis / Cuci Darah': { icon: 'water_drop', tone: 'blue' },
  'Gigi dan Mulut': { icon: 'dentistry', tone: 'sky' },
  Imunisasi: { icon: 'vaccines', tone: 'emerald' },
  'Kebidanan dan Kandungan': { icon: 'pregnant_woman', tone: 'rose' },
  'Kesehatan Anak': { icon: 'child_care', tone: 'amber' },
  'Kesehatan Jiwa / Psikiatri': { icon: 'psychology', tone: 'violet' },
  'Kesehatan Mata': { icon: 'visibility', tone: 'sky' },
  Ortodonti: { icon: 'dentistry', tone: 'sky' },
  'Pelayanan Medik Umum': { icon: 'stethoscope', tone: 'emerald' },
  'Penyakit Dalam': { icon: 'monitor_heart', tone: 'red' },
  'Psikologi Klinis': { icon: 'psychology', tone: 'violet' },
  'Pulmonologi dan Kedokteran Respirasi': { icon: 'pulmonology', tone: 'blue' },
  'Rawat Inap': { icon: 'bed', tone: 'navy' },
  'Rawat Inap Dasar': { icon: 'bed', tone: 'navy' },
  Refraksi: { icon: 'visibility', tone: 'sky' },
  'Rehabilitasi Medik': { icon: 'accessibility_new', tone: 'emerald' },
  Subspesialis: { icon: 'neurology', tone: 'violet' },
};

export const FACILITY_ICON = {
  Ambulans: 'ambulance',
  Apotek: 'medication',
  Farmasi: 'medication',
  'Instalasi Farmasi': 'medication',
  'ICU / ICCU': 'monitor_heart',
  'ICU / ICCU / NICU': 'monitor_heart',
  ICU: 'monitor_heart',
  'Instalasi Gawat Darurat': 'emergency',
  'Instalasi Gawat Darurat Psikiatri': 'psychology',
  'Kamar Operasi': 'surgical',
  'Kamar Bersalin': 'pregnant_woman',
  'Ruang Rawat Inap': 'bed',
  'Ruang Rawat Inap Dasar': 'bed',
  Laboratorium: 'science',
  'Laboratorium Klinik': 'science',
  'Laboratorium Dasar': 'science',
  'Poliklinik Mata': 'visibility',
  'Unit Hemodialisa': 'water_drop',
  'Kamar Bedah Mata': 'visibility',
  'Klinik Gigi Spesialis': 'dentistry',
  'Radiologi Gigi': 'radiology',
};

export const SPECIALTIES = [
  {
    title: 'Radiologi & Imaging',
    service: 'Radiologi',
    image: '/images/rs/rs-005/foto_1.jpg',
    note: 'Pemeriksaan pencitraan medis',
  },
  {
    title: 'Kesehatan Anak',
    service: 'Kesehatan Anak',
    image: '/images/template/specialty-pediatrics.jpg',
    note: 'Perawatan pediatri',
  },
  {
    title: 'Kesehatan Jiwa',
    service: 'Kesehatan Jiwa / Psikiatri',
    image: '/images/rs/rs-025/foto_1.jpg',
    note: 'Layanan psikiatri',
  },
  {
    title: 'Bedah & Tindakan',
    service: 'Bedah',
    image: '/images/rs/rs-014/foto_1.jpg',
    note: 'Tindakan bedah terencana',
  },
];

export const QUICK_PROMPTS = [
  'Rumah Sakit kelas A di Medan',
  'Rumah sakit jiwa Sumut',
  'Rumah Sakit Mata di Medan',
  'Rumah Sakit di Deli Serdang',
  'Rumah Sakit Khusus Ibu dan Anak',
  'RS terdekat dari saya',
];

export const HOME_IMAGES = {
  hero: '/images/rs/rs-157/foto_1.jpg',
  editorialOne: '/images/rs/rs-019/foto_1.jpg',
  editorialTwo: '/images/rs/rs-171/foto_1.jpg',
};
