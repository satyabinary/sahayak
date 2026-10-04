import { ExternalLink, FileText } from "lucide-react";
import type { Source } from "../api";

export function SourceCards({ sources }: { sources: Source[] }) {
  if (!sources.length) return null;
  return (
    <details className="source-disclosure">
      <summary><FileText size={15} /> Official sources <span>{sources.length}</span></summary>
      <div className="source-list">
        {sources.map((source, index) => (
          <a key={`${source.source_url}-${source.page_number}-${index}`} className="source-item" href={source.source_url ?? undefined} target="_blank" rel="noreferrer">
            <span className="source-item-icon"><FileText size={16} /></span>
            <span className="source-item-copy"><b>{source.source_name}</b><small>{source.document_title ?? "Official source"}{source.page_number ? ` · Page ${source.page_number}` : ""}</small></span>
            <ExternalLink size={14} />
          </a>
        ))}
      </div>
    </details>
  );
}
