export default function CompareDock({
  ids,
  comparedIds,
  hospitals = [],
  onOpen,
  onOpenCompare,
  onRemove,
  onClear,
  onClose,
}) {
  const activeIds = comparedIds || ids || [];
  if (!activeIds.length) return null;

  const names = new Map(hospitals.map((h) => [h.id, h.nama]));
  const handleOpen = onOpenCompare || onOpen;
  const handleClear = onClear || onClose;

  return (
    <div id="compare-dock" className="compare-dock" role="region" aria-label="Menu perbandingan rumah sakit">
      <div className="compare-dock-count">
        <i className="fa-solid fa-code-compare" aria-hidden="true" />
        <span id="compare-dock-text">{activeIds.length}/3 RS dipilih</span>
      </div>

      <div id="compare-dock-items" className="compare-dock-pills">
        {activeIds.map((id) => (
          <span key={id} className="compare-dock-pill">
            <span>{names.get(id) || id}</span>
            <button
              type="button"
              onClick={() => onRemove && onRemove(id)}
              title="Hapus"
              aria-label={`Hapus ${names.get(id) || id} dari perbandingan`}
            >
              &times;
            </button>
          </span>
        ))}
      </div>

      <div className="compare-dock-actions">
        {activeIds.length >= 2 && handleOpen && (
          <button
            type="button"
            className="btn btn-primary"
            style={{ padding: '0.35rem 0.75rem', fontSize: '0.78rem' }}
            onClick={handleOpen}
          >
            Bandingkan Sekarang
          </button>
        )}
        {handleClear && (
          <button
            type="button"
            className="btn btn-ghost"
            style={{ color: '#fff', borderColor: 'rgba(255,255,255,.3)', padding: '0.35rem 0.65rem', fontSize: '0.78rem' }}
            onClick={handleClear}
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
