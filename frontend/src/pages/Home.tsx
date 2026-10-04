import { Link } from "react-router-dom";
import { ArrowRight, ArrowUpRight, BookOpenCheck, FileText, MessageCircle, ShieldCheck, Sparkles, Upload } from "lucide-react";

const actions = [
  { to: "/ask", icon: MessageCircle, title: "Ask a question", text: "Get clear, grounded investor guidance." },
  { to: "/grievance", icon: ShieldCheck, title: "Understand my grievance", text: "Work through your case one step at a time." },
  { to: "/dp-details", icon: Upload, title: "Extract DP details", text: "Read broker details from a screenshot." },
  { to: "/iepf", icon: BookOpenCheck, title: "IEPF guidance", text: "Explore official unclaimed investment guidance." },
];

export function HomePage() {
  return (
    <div className="home-page">
      <section className="welcome-banner">
        <div className="welcome-copy">
          <div className="hero-kicker"><span className="sparkle"><Sparkles size={13} /></span> YOUR INVESTOR SUPPORT COMPANION</div>
          <h1>Good to have you here.<br /><em>Let’s find your next step.</em></h1>
          <p>Clear, considerate help with investor questions and grievances — grounded in official information.</p>
          <div className="welcome-actions"><Link className="button button-light" to="/ask">Start a conversation <ArrowRight size={16} /></Link><Link className="hero-text-link" to="/sources">See how we work <ArrowUpRight size={15} /></Link></div>
        </div>
        <div className="hero-art" aria-hidden="true"><div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" /><div className="hero-seal"><ShieldCheck size={58} strokeWidth={1.15} /></div><div className="hero-note note-top">Grounded guidance <span>✓</span></div><div className="hero-note note-bottom">One step at a time <span>↗</span></div></div>
      </section>

      <section className="section-block">
        <div className="section-title"><div><div className="eyebrow">HOW CAN WE HELP?</div><h2>Choose where to begin</h2></div><span className="soft-label">Your pace, your choice</span></div>
        <div className="action-grid">
          {actions.map(({ to, icon: Icon, title, text }, index) => <Link to={to} className={`action-card action-card-${index}`} key={to}><span className="action-icon"><Icon size={19} /></span><span className="action-arrow"><ArrowUpRight size={17} /></span><h3>{title}</h3><p>{text}</p></Link>)}
        </div>
      </section>

      <section className="home-bottom-grid">
        <div className="gentle-note"><div className="note-icon"><Sparkles size={17} /></div><div><b>Support, without the overwhelm</b><p>We’ll ask only for details that help identify a useful next step. You stay in control of what you share.</p></div></div>
        <div className="kb-status-card"><div className="kb-card-icon"><FileText size={17} /></div><div className="kb-card-text"><b>Official source library</b><p>See the official material used to support procedural guidance.</p></div><Link to="/sources" aria-label="View official sources"><ArrowRight size={17} /></Link></div>
      </section>
      <div className="home-disclaimer">Information is educational and procedural — not legal or financial advice. Always confirm requirements with the relevant official source.</div>
    </div>
  );
}
