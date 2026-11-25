import { useEffect, useId, useRef, useState } from 'react';
import { getSearchSuggestions } from '../api';

export default function SearchAutocomplete({ value, onChange, onChoose, ...props }) {
  const [items, setItems] = useState([]);
  const [active, setActive] = useState(-1);
  const [visible, setVisible] = useState(false);
  const focused = useRef(false);
  const generation = useRef(0);
  const listId = useId();
  useEffect(() => {
    const request = ++generation.current;
    const controller = new AbortController();
    setItems([]); setActive(-1);
    if (value.trim().length < 2) return () => controller.abort();
    const timer = setTimeout(() => {
      getSearchSuggestions(value, controller.signal).then(data => {
        if (request !== generation.current || controller.signal.aborted) return;
        setItems(data.items || []); setVisible(focused.current);
      }).catch(() => {});
    }, 300);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [value]);
  const choose = item => {
    generation.current += 1;
    setVisible(false); setItems([]); setActive(-1);
    onChange(item.value); onChoose?.(item.value);
  };
  return <div style={{ position: 'relative', flex: 1, minWidth: 0 }}>
    <input {...props} value={value} maxLength={240} autoComplete="off" role="combobox"
      aria-autocomplete="list" aria-expanded={visible && items.length > 0} aria-controls={listId}
      aria-activedescendant={visible && active >= 0 ? `${listId}-${active}` : undefined}
      onChange={e => { setVisible(true); onChange(e.target.value); }}
      onFocus={() => { focused.current = true; setVisible(true); }}
      onBlur={() => { focused.current = false; setVisible(false); }}
      onKeyDown={e => {
        if (e.key === 'Escape') { generation.current++; setVisible(false); setActive(-1); e.preventDefault(); }
        if (!visible || !items.length) return;
        if (e.key === 'ArrowDown') { e.preventDefault(); setActive(x => (x + 1) % items.length); }
        if (e.key === 'ArrowUp') { e.preventDefault(); setActive(x => (x <= 0 ? items.length - 1 : x - 1)); }
        if (e.key === 'Enter' && active >= 0) { e.preventDefault(); choose(items[active]); }
      }} />
    {visible && items.length > 0 && <ul id={listId} role="listbox" aria-label="Saran pencarian"
      className="absolute left-0 right-0 z-50 mt-1 max-h-64 overflow-auto rounded-xl border border-slate-200 bg-white p-1 shadow-lg">
      {items.map((item, i) => <li key={`${item.kind}-${item.value}`} id={`${listId}-${i}`} role="option" aria-selected={i === active}>
        <button type="button" onMouseDown={e => e.preventDefault()} onClick={() => choose(item)}
          className={`w-full rounded-lg px-3 py-2 text-left text-sm ${i === active ? 'bg-teal-50 text-teal-800' : 'text-slate-700 hover:bg-slate-50'}`}>{item.label}</button>
      </li>)}
    </ul>}
  </div>;
}
