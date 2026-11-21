import { useApp } from '../context/AppContext';
import { cn } from '../utils';

export default function Toasts() {
  const { toasts } = useApp();

  return (
    <div
      className="pointer-events-none fixed bottom-5 left-1/2 z-[120] flex w-full max-w-md -translate-x-1/2 flex-col gap-2 px-4"
      aria-live="polite"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          className={cn(
            'pointer-events-auto flex animate-slide-up items-start gap-2.5 rounded-xl border px-4 py-3 text-sm shadow-floating backdrop-blur-md',
            toast.tone === 'success' && 'border-emerald-200 bg-emerald-50/95 text-emerald-900',
            toast.tone === 'error' && 'border-rose-200 bg-rose-50/95 text-rose-900',
            toast.tone === 'warning' && 'border-amber-200 bg-amber-50/95 text-amber-900',
            (!toast.tone || toast.tone === 'info') && 'border-slate-200 bg-white/95 text-slate-800',
          )}
        >
          <span
            className={cn(
              'material-symbols-outlined mt-0.5 text-[19px]',
              toast.tone === 'success' && 'text-emerald-600',
              toast.tone === 'error' && 'text-rose-600',
              toast.tone === 'warning' && 'text-amber-600',
              (!toast.tone || toast.tone === 'info') && 'text-brand-blue',
            )}
          >
            {toast.tone === 'error'
              ? 'error'
              : toast.tone === 'success'
                ? 'check_circle'
                : toast.tone === 'warning'
                  ? 'warning'
                  : 'info'}
          </span>
          <span className="flex-1 leading-relaxed">{toast.message}</span>
        </div>
      ))}
    </div>
  );
}
