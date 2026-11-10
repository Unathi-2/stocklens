import { NavLink, Route, Routes } from "react-router-dom";
import Placeholder from "./pages/Placeholder";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/markets", label: "Markets" },
  { to: "/watchlist", label: "Watchlist" },
  { to: "/portfolio", label: "Portfolio" },
  { to: "/analysis", label: "Analysis" },
  { to: "/risk", label: "Risk" },
  { to: "/forecast", label: "Forecast" },
  { to: "/settings", label: "Settings" },
];

export default function App() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 border-r border-slate-800 p-4">
        <div className="mb-6 text-lg font-bold tracking-wide">STOCKLENS</div>
        <nav className="flex flex-col gap-1">
          {nav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.to === "/"}
              className={({ isActive }) =>
                `rounded px-3 py-2 text-sm ${isActive ? "bg-slate-800 text-white" : "text-slate-400 hover:text-white"}`
              }
            >
              {n.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <main className="flex-1 p-8">
        <Routes>
          <Route path="/" element={<Placeholder title="Market Overview" note="JSE and US indices arrive in Phase 6." />} />
          <Route path="/markets" element={<Placeholder title="Markets" />} />
          <Route path="/stocks/:symbol" element={<Placeholder title="Stock" />} />
          <Route path="/watchlist" element={<Placeholder title="Watchlist" />} />
          <Route path="/portfolio" element={<Placeholder title="Portfolio" />} />
          <Route path="/analysis" element={<Placeholder title="Analysis" />} />
          <Route path="/risk" element={<Placeholder title="Risk" />} />
          <Route path="/forecast" element={<Placeholder title="Forecast" />} />
          <Route path="/settings" element={<Placeholder title="Settings" />} />
        </Routes>
      </main>
    </div>
  );
}
