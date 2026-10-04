import { useQuery } from "@tanstack/react-query";
import { ArrowUpRight, BookOpenCheck, LoaderCircle, ShieldCheck } from "lucide-react";
import { getSources } from "../api";
import { PageHeading } from "../components/PageHeading";

export function SourcesPage() {
  const sources = useQuery({ queryKey: ["sources"], queryFn: getSources });
  return (
    <div className="content-page">
      <PageHeading eyebrow="TRANSPARENCY & TRUST" title="Official sources" description="Procedural guidance is grounded in official material retrieved from this source library. A source may be listed even when its content has not yet been indexed." />
      <div className="source-status-banner"><span className="status-icon"><ShieldCheck size={19} /></span><div><b>Grounded, with source links</b><p>When official material supports an answer, you can open the cited source. We don’t present unindexed material as evidence.</p></div></div>
      {sources.isError && <div className="service-error">Official source records could not be loaded. Check that the API is running.</div>}
      <div className="official-source-grid">{sources.data?.sources.map((source) => <article className="official-source-card" key={source.id}><div className="official-source-top"><span className="source-logo"><BookOpenCheck size={18} /></span><span className={`index-badge ${source.indexed ? "is-indexed" : "not-indexed"}`}>{source.indexed ? "Available for retrieval" : "Registry entry"}</span></div><h3>{source.name}</h3><p>{source.indexed ? "Available for grounded retrieval when relevant to your question." : "Official source is registered, but its content is not currently indexed."}</p><a href={source.url} target="_blank" rel="noreferrer">Visit official website <ArrowUpRight size={14} /></a></article>)}</div>
      {sources.isLoading && <div className="loading-state"><LoaderCircle size={18} className="spin" /> Loading sources…</div>}
      <div className="source-integrity-note"><ShieldCheck size={16} /><span>We do not create placeholder documents or present unindexed websites as retrieval evidence. If sources are insufficient, the assistant will say so.</span></div>
    </div>
  );
}
