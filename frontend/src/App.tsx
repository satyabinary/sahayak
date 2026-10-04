import { lazy, Suspense, useState } from "react";
import { Link, NavLink, Route, Routes, useLocation } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Activity, ArrowUpRight, BriefcaseBusiness, ChevronDown, CircleHelp, FileText, Landmark, Menu, MessageCircle, ShieldCheck, Upload } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";
import { getHealth } from "./api";
import { useSangyanState } from "./state";
const HomePage = lazy(() => import("./pages/Home").then((module) => ({ default: module.HomePage })));
const ChatPage = lazy(() => import("./pages/Chat").then((module) => ({ default: module.ChatPage })));
const GrievancePage = lazy(() => import("./pages/Grievance").then((module) => ({ default: module.GrievancePage })));
const VisionPage = lazy(() => import("./pages/Vision").then((module) => ({ default: module.VisionPage })));
const ComplaintPage = lazy(() => import("./pages/Complaint").then((module) => ({ default: module.ComplaintPage })));
const IepfPage = lazy(() => import("./pages/Iepf").then((module) => ({ default: module.IepfPage })));
const SourcesPage = lazy(() => import("./pages/Sources").then((module) => ({ default: module.SourcesPage })));

const navigation = [
  { to: "/", label: "Overview", icon: Activity, end: true },
  { to: "/ask", label: "Ask Sangyan", icon: MessageCircle },
  { to: "/grievance", label: "Grievance", icon: BriefcaseBusiness },
  { to: "/dp-details", label: "Extract DP details", icon: Upload },
  { to: "/complaint", label: "Complaint draft", icon: FileText },
  { to: "/iepf", label: "IEPF guidance", icon: Landmark },
  { to: "/sources", label: "Official sources", icon: ShieldCheck },
];

export default function App() {
  const state = useSangyanState();
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth, refetchInterval: 30_000 });
  const [menuOpen, setMenuOpen] = useState(false);
  const location = useLocation();
  const connected = health.data?.status === "ok";

  return (
    <div className="app-shell">
      <aside className={`sidebar ${menuOpen ? "sidebar-open" : ""}`}>
        <Link to="/" className="brand" onClick={() => setMenuOpen(false)}>
          <span className="brand-mark"><Landmark size={23} strokeWidth={1.7} /></span>
          <span><b>Sangyan</b><small>SAHAYAK</small></span>
        </Link>
        <div className="nav-caption">YOUR WORKSPACE</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navigation.map(({ to, label, icon: Icon, end }) => (
            <NavLink key={to} to={to} end={end} className={({ isActive }) => `nav-link ${isActive ? "active" : ""}`} onClick={() => setMenuOpen(false)}>
              <Icon size={18} strokeWidth={1.8} /><span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <div className="trust-card"><div className="trust-icon"><ShieldCheck size={17} /></div><b>Grounded in official guidance</b><p>We use official sources for procedural guidance and show where information comes from.</p><Link to="/sources">Explore sources <ArrowUpRight size={13} /></Link></div>
          <div className="sidebar-foot"><span>Educational guidance only</span><CircleHelp size={15} /></div>
        </div>
      </aside>
      {menuOpen && <button className="mobile-scrim" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <main className="main-area">
        <header className="topbar">
          <button className="mobile-menu icon-button" aria-label="Open navigation" onClick={() => setMenuOpen(true)}><Menu size={20} /></button>
          <div className="crumb"><span>Workspace</span><ChevronDown size={14} /><b>{navigation.find((item) => item.to === location.pathname)?.label ?? "Sangyan"}</b></div>
          <div className="top-actions">
            <label className="language-select"><span>Language</span><select value={state.language} onChange={(event) => state.setLanguage(event.target.value as typeof state.language)} aria-label="Response language"><option value="hinglish">Hinglish</option><option value="hindi">Hindi</option><option value="english">English</option></select><ChevronDown size={13} /></label>
            <span className={`connection ${connected ? "connected" : "disconnected"}`}><i />{health.isLoading ? "Connecting" : connected ? "Connected" : "Service unavailable"}</span>
          </div>
        </header>
        <AnimatePresence mode="wait">
          <motion.div key={location.pathname} className="page-frame" initial={{ opacity: 0, y: 7 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -4 }} transition={{ duration: 0.16 }}>
            <Suspense fallback={<div className="loading-state"><span className="spin"><Activity size={17} /></span> Loading workspace…</div>}>
              <Routes>
              <Route path="/" element={<HomePage />} />
              <Route path="/ask" element={<ChatPage {...state} />} />
              <Route path="/grievance" element={<GrievancePage {...state} />} />
              <Route path="/dp-details" element={<VisionPage />} />
              <Route path="/complaint" element={<ComplaintPage {...state} />} />
              <Route path="/iepf" element={<IepfPage language={state.language} />} />
              <Route path="/sources" element={<SourcesPage />} />
              <Route path="*" element={<HomePage />} />
              </Routes>
            </Suspense>
          </motion.div>
        </AnimatePresence>
        <footer className="page-footer"><span>© Sangyan Sahayak</span><span>Not legal or financial advice · Verify instructions with official sources</span></footer>
      </main>
    </div>
  );
}
