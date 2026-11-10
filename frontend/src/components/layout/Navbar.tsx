import Icon from "../ui/Icon";
import SearchBar from "../ui/SearchBar";
import ApiStatus from "./ApiStatus";
import { useTheme } from "../../theme";

export default function Navbar({ onMenu }: { onMenu: () => void }) {
  const { theme, toggle } = useTheme();
  return (
    <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b border-rule bg-bg/90 px-4 backdrop-blur sm:px-6">
      <button
        type="button"
        onClick={onMenu}
        aria-label="Open navigation"
        className="rounded p-1.5 text-muted hover:bg-panel2 hover:text-ink lg:hidden"
      >
        <Icon name="menu" size={20} />
      </button>
      <div className="max-w-md flex-1">
        <SearchBar />
      </div>
      <div className="ml-auto flex items-center gap-3">
        <span className="hidden sm:block"><ApiStatus /></span>
        <button
          type="button"
          onClick={toggle}
          aria-label={theme === "dark" ? "Switch to light theme" : "Switch to dark theme"}
          className="rounded p-1.5 text-muted hover:bg-panel2 hover:text-ink"
        >
          <Icon name={theme === "dark" ? "sun" : "moon"} size={18} />
        </button>
      </div>
    </header>
  );
}
