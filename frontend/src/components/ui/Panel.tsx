import type { ReactNode } from "react";
import { cn } from "../../utils/cn";

interface PanelProps {
  title?: string;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
  flush?: boolean;
}

/** A bordered region. One quiet border, no shadow. */
export default function Panel({ title, action, children, className, flush }: PanelProps) {
  return (
    <section className={cn("rounded-md border border-rule bg-panel", className)}>
      {title && (
        <header className="flex items-center justify-between gap-3 border-b border-rule px-4 py-3">
          <h2 className="font-serif text-lg font-medium">{title}</h2>
          {action}
        </header>
      )}
      <div className={flush ? "" : "p-4"}>{children}</div>
    </section>
  );
}
