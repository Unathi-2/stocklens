import type { ReactNode } from "react";
import Button from "./Button";
import { cn } from "../../utils/cn";

export function LoadingSpinner({ label = "Loading" }: { label?: string }) {
  return (
    <span role="status" className="inline-flex items-center gap-2 text-sm text-muted">
      <svg className="h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="3" opacity="0.25" />
        <path d="M21 12a9 9 0 00-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      {label}
    </span>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cn("animate-pulse rounded bg-panel2", className)} />;
}

export function ErrorMessage({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-down px-4 py-3">
      <div>
        <p className="font-medium text-down">Could not load this data</p>
        <p className="mt-0.5 text-sm text-muted">{message}</p>
      </div>
      {onRetry && <Button onClick={onRetry}>Try again</Button>}
    </div>
  );
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="rounded-md border border-dashed border-rule px-6 py-10 text-center">
      <h3 className="font-serif text-xl">{title}</h3>
      {children && <p className="mx-auto mt-2 max-w-prose text-sm text-muted">{children}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
