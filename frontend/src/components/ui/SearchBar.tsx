import { useEffect, useId, useRef, useState, type KeyboardEvent } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../../services/api";
import { useDebounce } from "../../hooks/useDebounce";
import type { Company } from "../../types/api";
import Icon from "./Icon";
import Badge from "./Badge";
import { cn } from "../../utils/cn";

export default function SearchBar() {
  const navigate = useNavigate();
  const listId = useId();
  const boxRef = useRef<HTMLDivElement>(null);
  const [query, setQuery] = useState("");
  const debounced = useDebounce(query, 250);
  const [results, setResults] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [failed, setFailed] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);

  useEffect(() => {
    const q = debounced.trim();
    if (!q) {
      setResults([]);
      setFailed(false);
      return;
    }
    let cancelled = false;
    setLoading(true);
    api
      .searchStocks(q)
      .then((r) => {
        if (cancelled) return;
        setResults(r.data);
        setFailed(false);
        setActive(0);
      })
      .catch(() => {
        if (!cancelled) {
          setResults([]);
          setFailed(true);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [debounced]);

  useEffect(() => {
    const onDown = (e: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDown);
    return () => document.removeEventListener("mousedown", onDown);
  }, []);

  const choose = (c: Company) => {
    setOpen(false);
    setQuery("");
    navigate(`/stocks/${encodeURIComponent(c.symbol)}?exchange=${encodeURIComponent(c.exchange)}`);
  };

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => Math.max(i - 1, 0));
    } else if (e.key === "Enter" && results[active]) {
      e.preventDefault();
      choose(results[active]);
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  const showList = open && query.trim().length > 0;

  return (
    <div ref={boxRef} className="relative w-full">
      <Icon name="search" size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-muted" />
      <input
        type="search"
        role="combobox"
        aria-label="Search stocks and indices"
        aria-expanded={showList}
        aria-controls={listId}
        aria-autocomplete="list"
        placeholder="Search by name or symbol"
        value={query}
        onChange={(e) => {
          setQuery(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={onKeyDown}
        className="w-full rounded border border-rule bg-panel py-1.5 pl-9 pr-3 text-sm placeholder:text-muted"
      />
      {showList && (
        <ul
          id={listId}
          role="listbox"
          className="absolute left-0 right-0 top-full z-50 mt-1 max-h-80 overflow-auto rounded-md border border-rule bg-panel shadow-lg"
        >
          {loading && results.length === 0 && <li className="px-3 py-2 text-sm text-muted">Searching</li>}
          {failed && <li className="px-3 py-2 text-sm text-down">Search is unavailable. Check that the backend is running.</li>}
          {!loading && !failed && results.length === 0 && (
            <li className="px-3 py-2 text-sm text-muted">No match for "{query.trim()}"</li>
          )}
          {results.map((c, i) => (
            <li
              key={`${c.symbol}-${c.exchange}`}
              role="option"
              aria-selected={i === active}
              onMouseEnter={() => setActive(i)}
              onMouseDown={(e) => {
                e.preventDefault();
                choose(c);
              }}
              className={cn("flex cursor-pointer items-center justify-between gap-3 px-3 py-2", i === active && "bg-panel2")}
            >
              <span className="min-w-0">
                <span className="font-medium">{c.symbol}</span>
                <span className="ml-2 truncate text-sm text-muted">{c.name}</span>
              </span>
              <Badge>{c.exchange}</Badge>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
