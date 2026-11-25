// Presentation only: keep the original response and conversation context intact.
const REPETITIVE_NOTE = 'Layanan bersumber dari laporan SIRS, bukan verifikasi operasional atau ketersediaan saat ini. Label klinis yang belum direview ditahan. Fasilitas dan BPJS dari data lama belum terverifikasi. Sumber dan tanggal tersedia pada halaman detail. Chatbot ini bukan untuk diagnosis medis.';

export function formatChatDisplay(text) {
  return String(text || '')
    .replaceAll(REPETITIVE_NOTE, '')
    .replace(/[\p{Extended_Pictographic}\uFE0F\u200D]/gu, '')
    .replace(/^[ \t]+/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}
