import { useEffect, useRef, useState } from 'react';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { sendChat } from '../api';
import { QUICK_PROMPTS } from '../constants';
import { getUserPosition } from './LeafletMap';
import { useApp } from '../context/AppContext';
import { cn } from '../utils';

const GREETING =
  'Selamat datang di **CariSehat**. Saya asisten semantik yang dapat membantu menemukan rumah sakit, layanan, kelas, dan wilayah di Sumatera Utara.\n\nCoba tanyakan: *“Rumah Sakit kelas A di Medan”* atau *“Rumah sakit jiwa Sumut”*.';

function MessageBubble({ message, onQuickReply, onClose }) {
  const isUser = message.role === 'user';
  return (
    <div className={cn('flex gap-2', isUser ? 'justify-end' : 'justify-start')}>
      {!isUser ? (
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-navy text-white shadow-sm">
          <span className="material-symbols-outlined text-[16px]">smart_toy</span>
        </span>
      ) : null}

      <div className={cn('max-w-[86%] space-y-2', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'rounded-2xl px-3.5 py-2.5 text-[13px] leading-relaxed shadow-sm',
            isUser
              ? 'rounded-br-md bg-brand-navy text-white'
              : message.emergency
                ? 'rounded-bl-md border border-rose-200 bg-rose-50 text-rose-900'
                : 'rounded-bl-md border border-slate-200 bg-white text-slate-700',
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
                      return (
                        <Link to={href} onClick={onClose} {...props}>
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
          <div className="w-full space-y-1.5">
            {message.hospitals.slice(0, 5).map((hospital) => (
              <Link
                key={hospital.id}
                to={`/rumah-sakit/${encodeURIComponent(hospital.id)}`}
                onClick={onClose}
                className="flex items-center gap-2.5 rounded-xl border border-slate-200 bg-white p-2 transition hover:border-brand-blue/40 hover:bg-blue-50/40"
              >
                {hospital.foto ? (
                  <img
                    src={hospital.foto}
                    alt=""
                    loading="lazy"
                    className="h-10 w-10 shrink-0 rounded-lg object-cover"
                    onError={(event) => {
                      event.currentTarget.style.display = 'none';
                    }}
                  />
                ) : (
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-brand-navy">
                    <span className="material-symbols-outlined text-[18px]">local_hospital</span>
                  </span>
                )}
                <span className="min-w-0 flex-1">
                  <span className="line-clamp-1 block text-[11.5px] font-bold text-slate-800">
                    {hospital.nama}
                  </span>
                  <span className="block text-[10px] text-slate-500">
                    Kelas {hospital.kelas || '—'} • {hospital.kabkota || 'Sumatera Utara'}
                  </span>
                </span>
                <span className="material-symbols-outlined text-[16px] text-slate-400">chevron_right</span>
              </Link>
            ))}
          </div>
        ) : null}

        {message.quickReplies?.length ? (
          <div className="flex flex-wrap gap-1.5">
            {message.quickReplies.slice(0, 5).map((reply) => (
              <button
                key={reply}
                type="button"
                onClick={() => onQuickReply(reply)}
                className="rounded-full border border-brand-blue/25 bg-blue-50 px-2.5 py-1 text-[10.5px] font-semibold text-brand-blue transition hover:bg-blue-100"
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
  const { toast } = useApp();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { id: 'welcome', role: 'assistant', text: GREETING, quickReplies: QUICK_PROMPTS.slice(0, 3) },
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
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-a`,
          role: 'assistant',
          text: response.text || 'Tidak ada balasan dari asisten.',
          hospitals: response.hospitals || [],
          quickReplies: response.quick_replies || [],
          emergency: Boolean(response.is_emergency),
        },
      ]);
      if (response.is_emergency) {
        toast('Asisten mendeteksi situasi darurat. Hubungi 119 atau IGD terdekat.', 'info');
      }
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: `${Date.now()}-e`,
          role: 'assistant',
          text: `Maaf, asisten belum dapat dihubungi. Pastikan backend berjalan. **${error.message}**`,
          quickReplies: [],
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
      toast('Lokasi aktif. Pertanyaan “RS terdekat” akan memakai posisi Anda.', 'success');
    } catch (error) {
      toast(error.message, 'error');
    } finally {
      setLocating(false);
    }
  };

  return (
    <>
      {open ? (
        <div className="fixed inset-0 z-[80] flex items-end justify-end bg-slate-950/30 p-0 backdrop-blur-[2px] sm:bg-transparent sm:p-5 sm:backdrop-blur-0">
          <section
            className="flex h-[86vh] w-full animate-slide-up flex-col overflow-hidden rounded-t-2xl border border-slate-200 bg-slate-50 shadow-modal sm:h-[610px] sm:max-h-[calc(100vh-40px)] sm:w-[400px] sm:rounded-2xl"
            role="dialog"
            aria-modal="true"
            aria-labelledby="chat-title"
          >
            <header className="flex items-center justify-between gap-3 bg-brand-navy px-4 py-3.5 text-white">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-9 w-9 items-center justify-center rounded-full bg-white/15">
                  <span className="material-symbols-outlined text-[20px]">smart_toy</span>
                  <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-brand-navy bg-emerald-400" />
                </span>
                <div>
                  <h2 id="chat-title" className="font-heading text-sm font-bold leading-none">
                    Tanya CariSehat
                  </h2>
                  <p className="mt-1 text-[10px] text-blue-100/80">Asisten semantik • rule-based RDF</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5">
                <button
                  type="button"
                  onClick={enableLocation}
                  className={cn(
                    'flex h-8 w-8 items-center justify-center rounded-full transition',
                    location ? 'bg-emerald-500/25 text-emerald-200' : 'bg-white/10 hover:bg-white/20',
                  )}
                  title={location ? 'Lokasi aktif' : 'Aktifkan lokasi untuk pencarian terdekat'}
                  aria-label="Aktifkan lokasi"
                >
                  <span className={cn('material-symbols-outlined text-[17px]', locating && 'animate-pulse')}>
                    {location ? 'my_location' : 'location_searching'}
                  </span>
                </button>
                <button
                  type="button"
                  onClick={() => setOpen(false)}
                  className="flex h-8 w-8 items-center justify-center rounded-full bg-white/10 transition hover:bg-white/20"
                  aria-label="Tutup asisten"
                >
                  <span className="material-symbols-outlined text-[18px]">close</span>
                </button>
              </div>
            </header>

            <div className="flex-1 space-y-3 overflow-y-auto px-3.5 py-4 scrollbar-thin">
              {messages.map((message) => (
                <MessageBubble
                  key={message.id}
                  message={message}
                  onQuickReply={send}
                  onClose={() => setOpen(false)}
                />
              ))}

              {loading ? (
                <div className="flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-navy text-white">
                    <span className="material-symbols-outlined text-[16px]">smart_toy</span>
                  </span>
                  <span className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-slate-200 bg-white px-3.5 py-3 shadow-sm">
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-blue [animation-delay:-0.2s]" />
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-blue [animation-delay:-0.1s]" />
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-brand-blue" />
                  </span>
                </div>
              ) : null}

              <div ref={bottomRef} />
            </div>

            <div className="border-t border-slate-200 bg-white p-3">
              {!location ? (
                <button
                  type="button"
                  onClick={enableLocation}
                  className="mb-2 flex w-full items-center justify-center gap-1.5 rounded-lg bg-slate-50 py-1.5 text-[10.5px] font-semibold text-slate-500 transition hover:bg-slate-100"
                >
                  <span className="material-symbols-outlined text-[14px]">near_me</span>
                  Aktifkan lokasi untuk mencari RS terdekat
                </button>
              ) : (
                <p className="mb-2 flex items-center justify-center gap-1.5 text-[10.5px] font-semibold text-emerald-600">
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
                  className="max-h-24 min-h-[42px] flex-1 resize-none rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-[13px] outline-none transition focus:border-brand-blue focus:bg-white focus:ring-2 focus:ring-brand-blue/15"
                  aria-label="Pesan untuk asisten"
                />
                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="flex h-[42px] w-[42px] shrink-0 items-center justify-center rounded-xl bg-brand-navy text-white transition hover:bg-brand-blue disabled:cursor-not-allowed disabled:opacity-40"
                  aria-label="Kirim pesan"
                >
                  <span className="material-symbols-outlined text-[20px]">send</span>
                </button>
              </form>
              <p className="mt-1.5 text-center text-[9.5px] text-slate-400">
                Asisten akademik. Bukan pengganti diagnosis atau layanan darurat. Hubungi 119 bila perlu.
              </p>
            </div>
          </section>
        </div>
      ) : null}

      <button
        type="button"
        onClick={() => setOpen((current) => !current)}
        className={cn(
          'fixed bottom-5 right-5 z-[70] flex h-14 w-14 items-center justify-center rounded-full bg-brand-navy text-white shadow-floating transition-all hover:scale-105 hover:bg-brand-blue',
          open && 'hidden',
        )}
        aria-label="Buka asisten CariSehat"
        aria-expanded={open}
      >
        <span className="material-symbols-outlined text-[26px]">chat</span>
        <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full border-2 border-white bg-emerald-500 text-[8px] font-bold">
          AI
        </span>
      </button>
    </>
  );
}
