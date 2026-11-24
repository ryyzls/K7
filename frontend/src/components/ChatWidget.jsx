import { useEffect, useRef, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChat } from '../api';
import { QUICK_PROMPTS } from '../constants';
import { getUserPosition } from './LeafletMap';
import { useApp } from '../context/AppContext';
import { cn } from '../utils';

const GREETING =
  'Selamat datang di **CariSehat**. Saya siap membantu mencarikan rumah sakit, layanan spesialis, kelas perawatan, dan fasilitas rujukan di Sumatera Utara.\n\nCoba tanyakan: *“Rumah sakit kelas A di Medan”* atau *“RS BPJS anak di Deli Serdang”*.';

const INTENT_LABELS = {
  search: 'Pencarian Fasilitas',
  nearest: 'Lokasi Terdekat',
  detail: 'Profil Rumah Sakit',
  compare: 'Perbandingan RS',
  emergency: 'Informasi Darurat',
  bpjs: 'Layanan BPJS',
  greeting: 'Panduan CariSehat',
};

function formatIntentBadge(intent, count) {
  const key = String(intent || '').toLowerCase();
  const label = INTENT_LABELS[key] || 'Direktori RS Sumut';
  return count > 0 ? `${label} • ${count} RS` : label;
}

function AssistantAvatar({ size = 'sm' }) {
  const dim = size === 'lg' ? 'h-9 w-9' : 'h-7 w-7';
  const iconSize = size === 'lg' ? 'text-[19px]' : 'text-[15px]';
  return (
    <span
      className={cn(
        'relative flex shrink-0 items-center justify-center rounded-full bg-gradient-to-br from-[#0F766E] to-[#094E48] text-white ring-1 ring-black/5 shadow-sm',
        dim,
      )}
    >
      <span className={cn('material-symbols-outlined', iconSize)}>support_agent</span>
    </span>
  );
}

function MessageBubble({ message, onQuickReply, onClose, onRouteHospital, onToggleCompare, isCompared }) {
  const isUser = message.role === 'user';
  return (
    <div className={cn('flex gap-2.5', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser ? (
        <div className="mt-0.5">
          <AssistantAvatar size="sm" />
        </div>
      ) : null}

      <div className={cn('max-w-[86%] space-y-1.5', isUser && 'flex flex-col items-end')}>
        {!isUser && message.metaBadge ? (
          <span className="inline-flex items-center gap-1 rounded-full bg-teal-50/90 px-2.5 py-0.5 text-[10px] font-semibold text-[#0B5E57] ring-1 ring-teal-600/15">
            <span className="h-1.5 w-1.5 rounded-full bg-teal-500" />
            {message.metaBadge}
          </span>
        ) : null}

        <div
          className={cn(
            'rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed',
            isUser
              ? 'rounded-br-sm bg-gradient-to-br from-[#0F766E] to-[#0B5E57] text-white shadow-sm'
              : message.emergency
                ? 'rounded-bl-sm border border-rose-200 bg-rose-50/95 text-rose-900 shadow-sm'
                : 'rounded-bl-sm border border-slate-200/80 bg-white text-slate-700 shadow-[0_2px_8px_-2px_rgba(15,23,42,0.06)]',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.text}</p>
          ) : (
            <div className="chat-markdown">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href = '', children, ...props }) => {
                    if (href.startsWith('/')) {
                      const target = href.replace(/^\/rs\/([^/?#]+)/, '/rumah-sakit/$1');
                      return (
                        <Link to={target} onClick={onClose} {...props}>
                          {children}
                        </Link>
                      );
                    }
                    return (
                      <a href={href} target="_blank" rel="noopener noreferrer" {...props}>
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {message.text}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {message.hospitals?.length ? (
          <div className="w-full space-y-2 pt-0.5">
            {message.hospitals.slice(0, 5).map((hospital) => {
              const compared = isCompared(hospital.id);
              return (
                <div
                  key={hospital.id}
                  className="rounded-2xl border border-slate-200/80 bg-white p-2.5 shadow-[0_2px_10px_-3px_rgba(15,23,42,0.07)] transition hover:border-teal-600/40"
                >
                  <div className="flex items-center gap-2.5">
                    {hospital.foto ? (
                      <img
                        src={hospital.foto}
                        alt=""
                        loading="lazy"
                        className="h-10 w-10 shrink-0 rounded-xl object-cover"
                        onError={(event) => {
                          event.currentTarget.style.display = 'none';
                        }}
                      />
                    ) : (
                      <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-teal-50 text-[#0D6B63]">
                        <span className="material-symbols-outlined text-[18px]">local_hospital</span>
                      </span>
                    )}
                    <div className="min-w-0 flex-1">
                      <p className="line-clamp-1 text-[12px] font-bold text-slate-800">
                        {hospital.nama}
                      </p>
                      <p className="text-[10.5px] text-slate-500">
                        Kelas {hospital.kelas || '—'} • {hospital.kabkota || 'Sumatera Utara'}
                      </p>
                    </div>
                  </div>

                  <div className="mt-2 flex items-center gap-1.5 border-t border-slate-100 pt-2">
                    <Link
                      to={`/rumah-sakit/${encodeURIComponent(hospital.id)}`}
                      onClick={onClose}
                      className="flex-1 rounded-full border border-slate-200 px-2.5 py-1 text-center text-[10.5px] font-semibold text-slate-700 transition hover:border-teal-600 hover:text-[#0B5E57]"
                    >
                      Detail
                    </Link>
                    <button
                      type="button"
                      onClick={() => onRouteHospital(hospital)}
                      className="flex-1 rounded-full bg-teal-50 px-2.5 py-1 text-[10.5px] font-semibold text-[#0B5E57] transition hover:bg-teal-100/80"
                    >
                      Rute
                    </button>
                    <button
                      type="button"
                      onClick={() => onToggleCompare(hospital.id)}
                      className={cn(
                        'flex-1 rounded-full px-2.5 py-1 text-[10.5px] font-semibold transition',
                        compared
                          ? 'bg-[#0D6B63] text-white'
                          : 'bg-slate-100 text-slate-700 hover:bg-slate-200/80',
                      )}
                    >
                      {compared ? 'Dipilih' : '+ Banding'}
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        ) : null}

        {message.quickReplies?.length ? (
          <div className="flex flex-wrap gap-1.5 pt-0.5">
            {message.quickReplies.slice(0, 5).map((reply) => (
              <button
                key={reply}
                type="button"
                onClick={() => onQuickReply(reply)}
                className="rounded-full border border-teal-600/20 bg-white px-3 py-1 text-[10.5px] font-medium text-[#0B5E57] shadow-2xs transition hover:border-teal-600/40 hover:bg-teal-50/70"
              >
                {reply}
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function ChatWidget() {
  const navigate = useNavigate();
  const { toast, toggleCompare, isCompared } = useApp();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      text: GREETING,
      metaBadge: 'Asisten CariSehat',
      quickReplies: QUICK_PROMPTS.slice(0, 3),
    },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [state, setState] = useState(null);
  const [location, setLocation] = useState(null);
  const [locating, setLocating] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    if (open) {
      window.setTimeout(() => bottomRef.current?.scrollIntoView({ behavior: 'smooth' }), 60);
      window.setTimeout(() => inputRef.current?.focus(), 180);
    }
  }, [open]);

  useEffect(() => {
    const openChat = () => setOpen(true);
    window.addEventListener('carisehat:open-chat', openChat);
    return () => window.removeEventListener('carisehat:open-chat', openChat);
  }, []);

  useEffect(() => {
    if (open) bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading, open]);

  const send = async (text) => {
    const trimmed = String(text || '').trim();
    if (!trimmed || loading) return;
    const userMessage = { id: `${Date.now()}-u`, role: 'user', text: trimmed };
    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setLoading(true);

    try {
      const payloadMessages = nextMessages
        .filter((message) => message.id !== 'welcome')
        .map((message) => ({ role: message.role, text: message.text }));
      const response = await sendChat({
        messages: payloadMessages,
        state: state || undefined,
        lat: location?.[0],
        lon: location?.[1],
        location_status: location ? 'granted' : 'unknown',
      });
      setState(response.state || null);
      const count = Array.isArray(response.hospitals) ? response.hospitals.length : 0;

      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-a`,
          role: 'assistant',
          text: response.text || 'Tidak ada balasan dari asisten.',
          hospitals: response.hospitals || [],
          quickReplies: response.quick_replies || [],
          emergency: Boolean(response.is_emergency),
          metaBadge: formatIntentBadge(response.intent, count),
        },
      ]);
      if (response.is_emergency) {
        toast('Situasi darurat terdeteksi. Segera hubungi 119 atau IGD terdekat.', 'info');
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-e`,
          role: 'assistant',
          text: `Maaf, layanan asisten sedang tidak dapat dijangkau. Silakan coba beberapa saat lagi. (${error.message})`,
          quickReplies: [],
          metaBadge: 'Koneksi terganggu',
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const enableLocation = async () => {
    if (locating) return;
    setLocating(true);
    try {
      const position = await getUserPosition();
      setLocation(position);
      toast('Lokasi aktif. Pencarian “RS terdekat” akan menggunakan posisi Anda.', 'success');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      setLocating(false);
    }
  };

  const handleRouteHospital = (hospital) => {
    setOpen(false);
    navigate(`/peta?rs=${encodeURIComponent(hospital.id)}&route=1`);
  };

  return (
    <>
      {open ? (
        <div
          className="fixed inset-0 z-[80] flex items-end justify-end bg-slate-950/25 p-0 backdrop-blur-[2px] sm:pointer-events-none sm:bg-transparent sm:p-5 sm:backdrop-blur-none"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) setOpen(false);
          }}
        >
          <section
            className="pointer-events-auto flex h-[84vh] w-full animate-slide-up flex-col overflow-hidden rounded-t-3xl border border-slate-200/90 bg-[#F7F9FB] shadow-[0_24px_60px_-12px_rgba(15,23,42,0.24),0_4px_16px_-4px_rgba(15,23,42,0.08)] sm:h-[600px] sm:max-h-[calc(100vh-44px)] sm:w-[400px] sm:rounded-3xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="chat-title"
          >
            <header className="flex items-center justify-between gap-3 bg-gradient-to-r from-[#0B5E57] via-[#0D6B63] to-[#117A71] px-4 py-3.5 text-white">
              <div className="flex items-center gap-3">
                <span className="relative flex h-9 w-9 items-center justify-center rounded-2xl bg-white/15 ring-1 ring-white/25 backdrop-blur-sm">
                  <span className="material-symbols-outlined text-[20px]">support_agent</span>
                  <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-[#0D6B63] bg-emerald-300" />
                </span>
                <div>
                  <h2 id="chat-title" className="text-[13.5px] font-bold tracking-tight leading-none">
                    Tanya CariSehat
                  </h2>
                  <p className="mt-1 text-[10.5px] text-teal-100/90">
                    Panduan Direktori RS Sumatera Utara
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={enableLocation}
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full ring-1 transition',
                    location
                      ? 'bg-white/25 text-white ring-white/30'
                      : 'bg-white/10 text-white/90 ring-white/15 hover:bg-white/20',
                  )}
                  title={location ? 'Lokasi aktif' : 'Aktifkan lokasi untuk pencarian terdekat'}
                  aria-label="Aktifkan lokasi"
                >
                  <span className={cn('material-symbols-outlined text-[16px]', locating && 'animate-pulse')}>
                    {location ? 'my_location' : 'location_searching'}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 text-white/90 ring-1 ring-white/15 transition hover:bg-white/20"
                  aria-label="Perkecil asisten"
                  title="Tutup panel"
                >
                  <span className="material-symbols-outlined text-[18px]">keyboard_arrow_down</span>
                </button>
              </div>
            </header>

            <div className="flex-1 space-y-3.5 overflow-y-auto px-3.5 py-4 scrollbar-thin">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onQuickReply={send}
                  onClose={() => setOpen(false)}
                  onRouteHospital={handleRouteHospital}
                  onToggleCompare={toggleCompare}
                  isCompared={isCompared}
                />
              ))}

              {loading ? (
                <div className="flex items-center gap-2.5">
                  <AssistantAvatar size="sm" />
                  <span className="flex items-center gap-1 rounded-2xl rounded-bl-sm border border-slate-200/80 bg-white px-3.5 py-3 shadow-2xs">
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#0D6B63] [animation-delay:-0.2s]" />
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#0D6B63] [animation-delay:-0.1s]" />
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-[#0D6B63]" />
                  </span>
                </div>
              ) : null}

              <div ref={bottomRef} />
            </div>

            <div className="border-t border-slate-200/80 bg-white/95 p-3 backdrop-blur-sm">
              {!location ? (
                <button
                  type="button"
                  onClick={enableLocation}
                  className="mb-2 flex w-full items-center justify-center gap-1.5 rounded-xl bg-slate-50 py-1.5 text-[10.5px] font-medium text-slate-600 ring-1 ring-slate-200/70 transition hover:bg-teal-50/70 hover:text-[#0B5E57]"
                >
                  <span className="material-symbols-outlined text-[14px]">near_me</span>
                  Aktifkan lokasi untuk mencari RS terdekat
                </button>
              ) : (
                <p className="mb-2 flex items-center justify-center gap-1.5 text-[10.5px] font-semibold text-[#0B5E57]">
                  <span className="material-symbols-outlined text-[14px]">my_location</span>
                  Lokasi aktif untuk pencarian terdekat
                </p>
              )}

              <form
                className="flex items-end gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  send(input);
                }}
              >
                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' && !event.shiftKey) {
                      event.preventDefault();
                      send(input);
                    }
                  }}
                  placeholder="Tanya rumah sakit, layanan, atau wilayah..."
                  className="max-h-24 min-h-[42px] flex-1 resize-none rounded-2xl border border-slate-200 bg-slate-50/80 px-3.5 py-2.5 text-[13px] outline-none transition focus:border-[#0D6B63] focus:bg-white focus:ring-2 focus:ring-teal-600/15"
                  aria-label="Pesan untuk asisten"
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-[#0F766E] to-[#0B5E57] text-white shadow-sm transition hover:brightness-105 disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Kirim pesan"
                >
                  <span className="material-symbols-outlined text-[19px]">send</span>
                </button>
              </form>
              <p className="mt-1.5 text-center text-[9.5px] text-slate-400">
                Panduan direktori layanan kesehatan. Bukan pengganti diagnosis medis; hubungi 119 untuk darurat.
              </p>
            </div>
          </section>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className={cn(
          'group fixed bottom-4 right-4 z-[70] inline-flex items-center gap-2.5 rounded-full bg-gradient-to-br from-[#0F766E] via-[#0D6B63] to-[#094E48] p-1.5 pr-4 text-white ring-1 ring-white/25 shadow-[0_14px_30px_-6px_rgba(9,78,72,0.45),0_4px_12px_-2px_rgba(15,23,42,0.12)] transition-all duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] hover:-translate-y-0.5 hover:shadow-[0_18px_36px_-6px_rgba(9,78,72,0.55),0_6px_16px_-2px_rgba(15,23,42,0.16)] active:translate-y-0 max-sm:p-2.5',
          open && 'pointer-events-none scale-90 opacity-0',
        )}
        aria-label="Buka asisten CariSehat"
        aria-expanded={open}
      >
        <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-white/15 ring-1 ring-white/20 backdrop-blur-sm transition-transform duration-300 group-hover:scale-105">
          <span className="material-symbols-outlined text-[20px]">forum</span>
          <span className="absolute -right-0.5 -top-0.5 flex h-2.5 w-2.5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-300 opacity-75" />
            <span className="relative inline-flex h-2.5 w-2.5 rounded-full border-[1.5px] border-[#0D6B63] bg-emerald-300" />
          </span>
        </span>
        <span className="hidden text-[12.5px] font-semibold tracking-tight text-white/95 sm:inline">
          Tanya Asisten
        </span>
      </button>
    </>
  );
}