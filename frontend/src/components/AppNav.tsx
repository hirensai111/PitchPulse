import { NavLink } from "react-router-dom";

export function AppNav() {
  const linkClass = ({ isActive }: { isActive: boolean }) =>
    `text-sm font-medium transition-colors ${
      isActive
        ? "text-slate-900 border-b-2 border-slate-900 pb-0.5"
        : "text-slate-500 hover:text-slate-800"
    }`;

  return (
    <nav className="border-b border-slate-200 bg-white">
      <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
        <NavLink to="/" className="text-lg font-bold text-slate-900 tracking-tight">
          IPL Event Predictor
        </NavLink>
        <div className="flex items-center gap-6">
          <NavLink to="/" className={linkClass} end>
            Predict
          </NavLink>
          <NavLink to="/track-record" className={linkClass}>
            Track Record
          </NavLink>
          <NavLink to="/about" className={linkClass}>
            About
          </NavLink>
        </div>
      </div>
    </nav>
  );
}
