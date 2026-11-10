import { useState } from "react";
import { Outlet } from "react-router-dom";
import Navbar from "./Navbar";
import Sidebar from "./Sidebar";

export default function AppLayout() {
  const [navOpen, setNavOpen] = useState(false);
  return (
    <div className="min-h-screen lg:pl-60">
      <a href="#content" className="sr-only focus:not-sr-only focus:fixed focus:left-2 focus:top-2 focus:z-50 focus:rounded focus:bg-accent focus:px-3 focus:py-2 focus:text-accent-fg">
        Skip to content
      </a>
      <Sidebar open={navOpen} onNavigate={() => setNavOpen(false)} />
      <Navbar onMenu={() => setNavOpen(true)} />
      <main id="content" className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
        <Outlet />
      </main>
    </div>
  );
}
