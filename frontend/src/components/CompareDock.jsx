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
  const isComplete = activeIds.length === 2;

  return (
    <div id="compare-dock" className="compare-dock" role="region" aria-label="Menu perbandingan rumah sakit">
      <div className="compare-dock-info">
        <i className="fa-solid fa-code-compare" aria-hidden="true" />
        <span id="compare-dock-text">{activeIds.length}/2 RS dipilih</span>
      </div>

      <div id="compare-dock-items" className="compare-dock-pills">
        {activeIds.map((id) => (
          <span key={id} className="compare-dock-pill" title={names.get(id) || id}>
            <span className="compare-dock-pill-name">{names.get(id) || id}</span>
            <button
              type="button"
              onClick={() => onRemove && onRemove(id)}
              title="Hapus dari perbandingan"
              aria-label={`Hapus ${names.get(id) || id} dari perbandingan`}
            >
              &times;
            </button>
          </span>
        ))}
      </div>

      <div className="compare-dock-actions">
        <button
          type="button"
          id="btn-dock-open-compare"
          className="btn btn-compare-now"
          disabled={!isComplete}
          onClick={isComplete ? handleOpen : undefined}
          title={isComplete ? 'Bandingkan 2 rumah sakit sekarang' : 'Pilih 1 rumah sakit lagi untuk membandingkan'}
        >
          Bandingkan Sekarang
        </button>
        {handleClear && (
          <button
            type="button"
            id="btn-dock-clear"
            className="btn btn-compare-reset"
            onClick={handleClear}
            title="Bersihkan perbandingan"
          >
            Reset
          </button>
        )}
      </div>
    </div>
  );
}
