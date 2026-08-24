import { NavLink } from "react-router-dom";

const TABS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/portfolio", label: "Portfolio", end: false },
  { to: "/history", label: "History", end: false },
  { to: "/screener", label: "Screener", end: false },
];

function tabClassName({ isActive }) {
  return [
    "flex items-center h-full px-px text-[13.5px] font-semibold border-b-2 -mb-px",
    isActive
      ? "text-ink border-accent"
      : "text-ink-muted border-transparent hover:text-ink",
  ].join(" ");
}

export function NavTabs() {
  return (
    <nav className="flex flex-1 items-stretch gap-6" aria-label="Primary">
      {TABS.map((tab) => (
        <NavLink key={tab.to} to={tab.to} end={tab.end} className={tabClassName}>
          {tab.label}
        </NavLink>
      ))}
    </nav>
  );
}
