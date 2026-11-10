import { useMemo, useState, type ReactNode } from "react";
import { cn } from "../../utils/cn";
import { Skeleton } from "./Feedback";

export interface Column<T> {
  key: string;
  header: string;
  align?: "left" | "right";
  render?: (row: T) => ReactNode;
  /** Provide this to make the column sortable. */
  sortValue?: (row: T) => number | string;
}

interface Props<T> {
  columns: Column<T>[];
  rows: T[];
  rowKey: (row: T) => string;
  loading?: boolean;
  empty?: string;
  onRowClick?: (row: T) => void;
}

export default function DataTable<T>({ columns, rows, rowKey, loading, empty = "Nothing to show.", onRowClick }: Props<T>) {
  const [sort, setSort] = useState<{ key: string; dir: "asc" | "desc" } | null>(null);

  const sorted = useMemo(() => {
    const col = columns.find((c) => c.key === sort?.key);
    if (!sort || !col?.sortValue) return rows;
    const get = col.sortValue;
    const sign = sort.dir === "asc" ? 1 : -1;
    return [...rows].sort((a, b) => {
      const x = get(a);
      const y = get(b);
      return (x < y ? -1 : x > y ? 1 : 0) * sign;
    });
  }, [rows, columns, sort]);

  const toggle = (key: string) =>
    setSort((s) => (s?.key === key ? (s.dir === "asc" ? { key, dir: "desc" } : null) : { key, dir: "asc" }));

  return (
    <div className="overflow-x-auto">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            {columns.map((c) => {
              const active = sort?.key === c.key;
              return (
                <th
                  key={c.key}
                  scope="col"
                  aria-sort={active ? (sort!.dir === "asc" ? "ascending" : "descending") : undefined}
                  className={cn("px-3 py-2 font-medium text-muted", c.align === "right" ? "text-right" : "text-left")}
                >
                  {c.sortValue ? (
                    <button type="button" onClick={() => toggle(c.key)} className="inline-flex items-center gap-1 hover:text-ink">
                      {c.header}
                      <span aria-hidden="true" className="text-xs">{active ? (sort!.dir === "asc" ? "▲" : "▼") : ""}</span>
                    </button>
                  ) : (
                    c.header
                  )}
                </th>
              );
            })}
          </tr>
        </thead>
        <tbody>
          {loading && rows.length === 0 &&
            Array.from({ length: 4 }).map((_, i) => (
              <tr key={i} className="border-t border-rule">
                {columns.map((c) => (
                  <td key={c.key} className="px-3 py-3"><Skeleton className="h-4 w-full" /></td>
                ))}
              </tr>
            ))}
          {!loading && rows.length === 0 && (
            <tr className="border-t border-rule">
              <td colSpan={columns.length} className="px-3 py-6 text-center text-muted">{empty}</td>
            </tr>
          )}
          {sorted.map((row) => (
            <tr
              key={rowKey(row)}
              onClick={onRowClick ? () => onRowClick(row) : undefined}
              className={cn("border-t border-rule", onRowClick && "cursor-pointer hover:bg-panel2")}
            >
              {columns.map((c) => (
                <td key={c.key} className={cn("num px-3 py-2.5", c.align === "right" ? "text-right" : "text-left")}>
                  {c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? "n/a")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
