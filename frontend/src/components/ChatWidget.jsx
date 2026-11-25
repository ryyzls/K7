import useNaraConversation from './useNaraConversation';
import NaraRichResponse from './NaraRichResponse';
import NaraIcon from './NaraIcon';
import './NaraChat.css';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useApp } from '../context/AppContext';
import { cn } from '../utils';
import { formatChatDisplay } from '../utils/chatDisplay';

const HERO_ACTIONS = [
  { label: 'Cari Rumah Sakit', icon: 'apartment', prompt: 'Cari rumah sakit di Medan' },
  { label: 'RS Terdekat', icon: 'location_on', prompt: 'Rumah sakit terdekat dari lokasi saya' },
  { label: 'Layanan Medis', icon: 'stethoscope', prompt: 'Rumah sakit dengan layanan penyakit dalam di Medan' },
  { label: 'Bandingkan RS', icon: 'compare_arrows', prompt: 'Bandingkan RS Hermina Medan dengan Columbia Asia Medan' },
  { label: 'Jam Operasional', icon: 'schedule', prompt: 'Jam operasional rumah sakit' },
  { label: 'Cari IGD', icon: 'local_hospital', prompt: 'Rumah sakit dengan IGD 24 jam' },
];

function extractHospitalBadges(hospital) {
  const badges = [];
  const facs = Array.isArray(hospital.fasilitas) ? hospital.fasilitas : [];
  const lays = Array.isArray(hospital.layanan) ? hospital.layanan : [];
  for (const item of [...facs, ...lays]) {
    if (!item) continue;
    const short = item.length > 18 ? item.split('(')[0].trim() : item;
    if (short && !badges.includes(short)) {
      badges.push(short);
    }
    if (badges.length >= 2) break;
  }
  return badges;
}

function MessageBubble({ message, onQuickReply, onMinimize }) {
  const isUser = message.role === 'user';
  return (
    <div className={cn('nara-message flex gap-2', isUser ? 'justify-end' : 'justify-start items-start')}>
      {!isUser ? (
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white p-0.5 shadow-sm">
          <img src="/images/cari-sehat-icon.png" alt="" className="h-full w-full rounded-full object-contain" />
        </span>
      ) : null}

      <div className={cn('max-w-[86%] space-y-2', isUser && 'flex flex-col items-end')}>
        <div
          className={cn(
            'rounded-2xl px-3.5 py-2.5 text-[12.5px] leading-relaxed shadow-sm',
            isUser
              ? 'rounded-br-md bg-[#0e7c71] text-white'
              : message.emergency
                ? 'rounded-bl-md border border-rose-300/40 bg-rose-950/70 text-rose-50 backdrop-blur-sm'
                : 'rounded-bl-md border border-white/15 bg-white/10 text-slate-100 backdrop-blur-sm',
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.text}</p>
          ) : (
            <div className="chat-markdown chat-markdown-dark">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  strong: ({ children }) => {
                    const label = String(children);
                    const icon = /^Fasilitas Penunjang/.test(label) ? 'fa-building'
                      : /^Layanan terlapor/.test(label) ? 'fa-stethoscope' : null;
                    return (
                      <strong>
                        {icon ? <i className={`fa-solid ${icon} mr-1.5 text-teal-200`} aria-hidden="true" /> : null}
                        {children}
                      </strong>
                    );
                  },
                  a: ({ href = '', children, ...props }) => {
                    if (href.startsWith('/')) {
                      const target = href.replace(/^\/rs\/([^/?#]+)/, '/rumah-sakit/$1');
                      return (
                        <Link to={target} onClick={onMinimize} {...props}>
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
                {formatChatDisplay(message.text)}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {message.hospitals?.length ? (
          <div className="w-full space-y-2">
            {message.hospitals.slice(0, 5).map((hospital) => {
              const badges = extractHospitalBadges(hospital);
              return (
                <Link
                  key={hospital.id}
                  to={`/rumah-sakit/${encodeURIComponent(hospital.id)}`}
                  onClick={onMinimize}
                  className="nara-card flex items-center gap-2.5 rounded-xl bg-white p-2.5 text-slate-800 shadow-sm transition hover:bg-teal-50/95 hover:shadow-md"
                >
                  {hospital.foto ? (
                    <img
                      src={hospital.foto}
                      alt=""
                      loading="lazy"
                      className="h-12 w-14 shrink-0 rounded-lg object-cover"
                      onError={(event) => {
                        event.currentTarget.style.display = 'none';
                      }}
                    />
                  ) : (
                    <span className="flex h-12 w-14 shrink-0 items-center justify-center rounded-lg bg-teal-50 text-teal-800">
                      <NaraIcon className="material-symbols-outlined text-[20px]">local_hospital</NaraIcon>
                    </span>
                  )}
                  <span className="min-w-0 flex-1">
                    <span className="line-clamp-1 block text-[12px] font-bold text-slate-900">
                      {hospital.nama}
                    </span>
                    <span className="mt-0.5 block text-[10.5px] text-slate-500">
                      Kelas {hospital.kelas || '—'} • {hospital.kabkota || 'Sumatera Utara'}
                    </span>
                    {badges.length > 0 && (
                      <span className="mt-1 flex flex-wrap gap-1">
                        {badges.map((b) => (
                          <span
                            key={b}
                            className="inline-block rounded-full border border-teal-200/80 bg-teal-50 px-2 py-0.5 text-[9.5px] font-semibold text-teal-800"
                          >
                            {b}
                          </span>
                        ))}
                      </span>
                    )}
                  </span>
                  <NaraIcon className="material-symbols-outlined shrink-0 text-[18px] text-slate-400" aria-hidden="true">
                    chevron_right
                  </NaraIcon>
                </Link>
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
                className="rounded-full border border-white/20 bg-white/10 px-3 py-1 text-[10.5px] font-medium text-teal-50 backdrop-blur-sm transition hover:bg-white/20"
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
  const {
    open,setOpen,expanded,setExpanded,messages,input,changeInput,loading,state,location,locating,
    bottomRef,inputRef,scrollRef,nearBottom,send,enableLocation,minimizeChat,closeChat,
    history,historyOpen,setHistoryOpen,newConversation,selectHistory,deleteConversation,
    comparison,toggleComparison,commands,paletteIndex,chooseCommand,onInputKey,
  }=useNaraConversation(toast);

  return (
    <>
      {open ? (
        <div className="fixed inset-0 z-[80] flex items-end justify-end bg-slate-950/35 p-0 backdrop-blur-[2px] sm:pointer-events-none sm:bg-transparent sm:p-5 sm:backdrop-blur-0">
          <section
            className={cn(
              'nara-panel nara-glass pointer-events-auto flex h-[88vh] w-full animate-slide-up flex-col overflow-hidden rounded-t-2xl border border-teal-300/25 text-white shadow-2xl sm:rounded-2xl',
              expanded
                ? 'nara-expanded sm:h-[700px] sm:max-h-[calc(100vh-40px)] sm:w-[540px]'
                : 'sm:h-[630px] sm:max-h-[calc(100vh-40px)] sm:w-[410px]',
            )}
            role="dialog"
            aria-modal="false" aria-label="Tanya NARA"
            aria-labelledby="chat-title"
          >
            {/* Header */}
            <header className="nara-header flex items-center justify-between gap-3 border-b border-white/10 px-4 py-3.5">
              <div className="flex items-center gap-2.5">
                <span className="relative flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-white p-0.5 shadow-sm">
                  <img src="/images/cari-sehat-icon.png" alt="" className="h-full w-full rounded-full object-contain" />
                  <span className="absolute -bottom-0.5 -right-0.5 h-2.5 w-2.5 rounded-full border-2 border-[#0b3c3c] bg-emerald-400" />
                </span>
                <div>
                  <h2 id="chat-title" className="font-heading text-sm font-bold leading-none text-white">
                    NARA
                  </h2>
                  <p className="mt-1 text-[10.5px] text-teal-100/80">Asisten pencarian rumah sakit</p>
                </div>
              </div>

              <div className="flex items-center gap-1.5">
                <button onClick={()=>setHistoryOpen(v=>!v)} aria-label="Riwayat percakapan"><NaraIcon>history</NaraIcon></button>
                <button disabled={loading} onClick={newConversation} aria-label="Percakapan baru"><NaraIcon>add</NaraIcon></button>
                <button
                  type="button"
                  onClick={minimizeChat}
                  className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/15 bg-white/10 text-white transition hover:bg-white/20"
                  title="Perkecil asisten"
                  aria-label="Minimalkan NARA"
                >
                  <NaraIcon className="material-symbols-outlined text-[16px]">remove</NaraIcon>
                </button>
                <button
                  type="button"
                  onClick={() => setExpanded((v) => !v)}
                  className="hidden h-7 w-7 items-center justify-center rounded-lg border border-white/15 bg-white/10 text-white transition hover:bg-white/20 sm:flex"
                  title={expanded ? 'Ukuran standar' : 'Perbesar jendela asisten'}
                  aria-label={expanded ? 'Perkecil chat' : 'Perbesar chat'}
                >
                  <NaraIcon className="material-symbols-outlined text-[15px]">
                    {expanded ? 'close_fullscreen' : 'open_in_new'}
                  </NaraIcon>
                </button>
                <button
                  type="button"
                  onClick={closeChat}
                  className="flex h-7 w-7 items-center justify-center rounded-lg border border-white/15 bg-white/10 text-white transition hover:bg-white/20"
                  title="Minimalkan NARA"
                  aria-label="Tutup asisten"
                >
                  <NaraIcon className="material-symbols-outlined text-[16px]">close</NaraIcon>
                </button>
              </div>
            </header>

            {historyOpen&&<nav className="nara-history" aria-label="Daftar percakapan"><small>Riwayat hanya selama halaman ini terbuka.</small><div><button disabled={loading} onClick={()=>deleteConversation()}>Hapus percakapan aktif</button></div>{history.map(h=><div key={h.id}><button disabled={loading} onClick={()=>selectHistory(h)}>{h.title}</button><button disabled={loading} aria-label={`Hapus ${h.title}`} onClick={()=>deleteConversation(h.id)}>×</button></div>)}</nav>}
            {/* Scrollable Body */}
            <div ref={scrollRef} onScroll={e=>{const el=e.currentTarget;nearBottom.current=el.scrollHeight-el.scrollTop-el.clientHeight<90;}} className="nara-scroll flex-1 space-y-3.5 overflow-y-auto px-4 py-4 scrollbar-thin">
              {/* Welcome Hero & 2x3 Quick Action Grid */}
              {!messages.length&&<div className="nara-welcome pb-1 text-center">
                <h3 className="font-heading text-[15.5px] font-bold text-white">
                  Apa yang bisa NARA bantu?
                </h3>
                <p className="mx-auto mt-1 max-w-[300px] text-[11px] leading-relaxed text-teal-100/75">
                  Cari rumah sakit, layanan medis, dan informasi kesehatan sesuai kebutuhan Anda.
                </p>

                <div className="mt-3.5 grid grid-cols-2 gap-2 text-left">
                  {HERO_ACTIONS.map((act) => (
                    <button
                      key={act.label}
                      type="button"
                      onClick={() => send(act.prompt)}
                      className="flex items-center gap-2 rounded-full border border-teal-300/25 bg-[#0c4a49]/70 px-3 py-1.5 text-[11.5px] font-medium text-white transition hover:border-teal-200/45 hover:bg-[#0f5c5a]"
                    >
                      <NaraIcon className="material-symbols-outlined text-[15px] text-teal-200" aria-hidden="true">
                        {act.icon}
                      </NaraIcon>
                      <span className="truncate">{act.label}</span>
                    </button>
                  ))}
                </div>
              </div>}

              {messages.map((message) => (
                <div key={message.id}><MessageBubble
                  message={message}
                  onQuickReply={send}
                  onMinimize={minimizeChat}
                /><NaraRichResponse message={message} send={send} toggleComparison={toggleComparison} loading={loading} toast={toast}/></div>
              ))}

              {loading ? (
                <div role="status" className="nara-typing flex items-center gap-2">
                  <span className="flex h-7 w-7 items-center justify-center rounded-full bg-white p-0.5">
                    <img src="/images/cari-sehat-icon.png" alt="" className="h-full w-full rounded-full object-contain" />
                  </span>
                  <span className="flex items-center gap-1 rounded-2xl rounded-bl-md border border-white/15 bg-white/10 px-3.5 py-3 backdrop-blur-sm">
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-200 [animation-delay:-0.2s]" />
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-200 [animation-delay:-0.1s]" />
                    <i className="h-1.5 w-1.5 animate-bounce rounded-full bg-teal-200" />
                  </span>
                </div>
              ) : null}

              <div ref={bottomRef} />
            </div>

            <div className="nara-filters" aria-label="Filter aktif">{(state?.active_filters||[]).map(f=><button key={f.id} disabled={loading} onClick={()=>send(`Hapus ${f.field==='class'?'kelas '+f.value:f.label}`)}>{f.label} ×</button>)}</div>
            {comparison.length>0&&<div className="nara-filters">{comparison.map(h=><button key={h.id} onClick={()=>toggleComparison(h)}>{h.nama} ×</button>)}<button disabled={loading||comparison.length<2} onClick={()=>send(`Bandingkan ${comparison.map(h=>h.id).join(' ')}`)}>Bandingkan {comparison.length} RS</button></div>}
            {/* Bottom Input Bar */}
            <div className="nara-footer border-t border-white/10 bg-black/15 p-3 backdrop-blur-md">
              <form
                className="flex items-center gap-2"
                onSubmit={(event) => {
                  event.preventDefault();
                  send(input);
                }}
              >
                {commands.length>0&&<div className="nara-palette" role="listbox" aria-label="Perintah NARA">{commands.map((c,i)=><button type="button" role="option" aria-selected={i===paletteIndex} className={i===paletteIndex?'selected':''} key={c[0]} onClick={()=>chooseCommand(c)}><strong>{c[0]}</strong><span>{c[1]}</span></button>)}</div>}
                <button
                  type="button"
                  onClick={enableLocation}
                  className={cn(
                    'relative flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border transition',
                    location
                      ? 'border-emerald-400/50 bg-emerald-500/20 text-emerald-200'
                      : 'border-white/20 bg-white/10 text-white hover:bg-white/20',
                  )}
                  title={location ? 'Lokasi GPS aktif' : 'Aktifkan lokasi untuk mencari RS terdekat'}
                  aria-label="Lokasi" disabled={loading||locating}
                >
                  <NaraIcon className={cn('material-symbols-outlined text-[20px]', locating && 'animate-pulse')}>
                    {location ? 'my_location' : 'location_on'}
                  </NaraIcon>
                </button>

                <textarea
                  ref={inputRef}
                  rows={1}
                  value={input}
                  maxLength={4000}
                  onChange={(event) => changeInput(event.target.value)}
                  onKeyDown={onInputKey}
                  placeholder="Tanyakan rumah sakit atau layanan medis..."
                  className="h-10 max-h-24 flex-1 resize-none overflow-hidden rounded-xl border border-white/20 bg-white/10 px-3 py-2.5 text-[12px] leading-tight text-white placeholder:truncate placeholder:text-teal-100/60 outline-none transition focus:border-teal-300/60 focus:bg-white/15"
                  aria-label="Pesan untuk NARA"
                />

                <button
                  type="submit"
                  disabled={loading || !input.trim()}
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-[#0e7c71] text-white shadow-sm transition hover:bg-[#119386] disabled:cursor-not-allowed disabled:opacity-45"
                  aria-label="Kirim pesan"
                >
                  <NaraIcon className="material-symbols-outlined text-[19px]">send</NaraIcon>
                </button>
              </form>
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
        aria-label="Buka Tanya NARA"
        aria-expanded={open}
      >
        <img src="/images/cari-sehat-icon.png" alt="" className="h-11 w-11 rounded-full bg-white object-contain" />
      </button>
    </>
  );
}
