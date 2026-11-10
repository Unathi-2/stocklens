import { NavLink } from "react-router-dom";
import Icon, { type IconName } from "../ui/Icon";
import { cn } from "../../utils/cn";

const MAIN: { to: string; label: string; icon: IconName }[] = [
  { to: "/", label: "Dashboard", icon: "grid" },
  { to: "/markets", label: "Markets", icon: "bars" },
  { to: "/watchlist", label: "Watchlist", icon: "star" },
  { to: "/portfolio", label: "Portfolio", icon: "briefcase" },
  { to: "/analysis", label: "Analysis", icon: "activity" },
  { to: "/risk", label: "Risk", icon: "shield" },
  { to: "/forecast", label: "Forecast", icon: "trend" },
];
const FOOT: { to: string; label: string; icon: IconName }[] = [
  { to: "/design", label: "Design system", icon: "layers" },
  { to: "/settings", label: "Settings", icon: "sliders" },
];

function Item({ to, label, icon, onNavigate }: { to: string; label: string; icon: IconName; onNavigate: () => void }) {
  return (
    <NavLink
      to={to}
      end={to === "/"}
      onClick={onNavigate}
      className={({ isActive }) =>
        cn(
          "flex items-center gap-3 border-l-2 px-4 py-2 text-sm transition-colors",
          isActive ? "border-accent bg-panel2 font-medium text-ink" : "border-transparent text-muted hover:text-ink",
        )
      }
    >
      <Icon name={icon} />
      {label}
    </NavLink>
  );
}

export default function Sidebar({ open, onNavigate }: { open: boolean; onNavigate: () => void }) {
  return (
    <>
      {open && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={onNavigate} aria-hidden="true" />}
      <aside
        aria-label="Main navigation"
        className={cn(
          "fixed inset-y-0 left-0 z-40 flex w-60 flex-col border-r border-rule bg-panel transition-transform lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-14 items-center border-b border-rule px-4">
          <span className="font-serif text-2xl font-semibold tracking-tight">StockLens</span>
        </div>
        <nav className="flex flex-1 flex-col justify-between py-3">
          <div className="flex flex-col">
            {MAIN.map((i) => (
              <Item key={i.to} {...i} onNavigate={onNavigate} />
            ))}
          </div>
          <div className="flex flex-col border-t border-rule pt-3">
            {FOOT.map((i) => (
              <Item key={i.to} {...i} onNavigate={onNavigate} />
            ))}
          </div>
        </nav>
      </aside>
    </>
  );
}
