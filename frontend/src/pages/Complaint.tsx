import { useEffect, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Download, FileCheck2, FileText, LoaderCircle, WandSparkles } from "lucide-react";
import { toast } from "sonner";
import { downloadComplaintPdf, generateComplaint, type Source } from "../api";
import type { useSangyanState } from "../state";
import { PageHeading } from "../components/PageHeading";
import { SourceCards } from "../components/SourceCards";

type Props = ReturnType<typeof useSangyanState>;
const DRAFT_KEY = "sangyan.complaint-draft";

export function ComplaintPage({ caseData, sessionId }: Props) {
  const [draft, setDraft] = useState(() => localStorage.getItem(DRAFT_KEY) ?? "");
  const [sources, setSources] = useState<Source[]>([]);
  const [verified, setVerified] = useState(false);
  useEffect(() => localStorage.setItem(DRAFT_KEY, draft), [draft]);
  const create = useMutation({
    mutationFn: () => generateComplaint(sessionId, caseData),
    onSuccess: (result) => { setDraft(result.draft); setSources(result.sources); setVerified(result.verified_sources_available); },
    onError: (error) => toast.error(error instanceof Error ? error.message : "The complaint draft could not be generated."),
  });
  const download = useMutation({
    mutationFn: () => downloadComplaintPdf(draft),
    onSuccess: (blob) => { const url = URL.createObjectURL(blob); const link = document.createElement("a"); link.href = url; link.download = "sangyan-complaint-draft.pdf"; link.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000); toast.success("Your PDF draft is ready."); },
    onError: (error) => toast.error(error instanceof Error ? error.message : "The PDF could not be created."),
  });
  const hasFacts = Boolean(caseData.description || caseData.issue_category || caseData.broker_name);

  return (
    <div className="content-page">
      <PageHeading eyebrow="REVIEW BEFORE YOU SEND" title="Complaint draft" description="Generate a reviewable draft from your case details. It will use retrieved official evidence where available." />
      {!hasFacts && <div className="helper-callout draft-reminder"><FileText size={17} /><span>For a more useful draft, <a href="/grievance">add your grievance details first</a>. You can still start a draft now.</span></div>}
      <section className="panel-card complaint-card">
        <div className="complaint-toolbar"><div><span className="document-icon"><FileCheck2 size={18} /></span><span><b>Your editable draft</b><small>{verified ? "Based on available official evidence" : "Review and verify before use"}</small></span></div><button className="button button-primary" onClick={() => create.mutate()} disabled={create.isPending}>{create.isPending ? <><LoaderCircle size={15} className="spin" /> Preparing…</> : <><WandSparkles size={15} /> Generate draft</>}</button></div>
        <textarea className="draft-editor" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Your complaint draft will appear here. Add your case details first for a grounded draft." aria-label="Edit complaint draft" />
        {draft && <div className="complaint-actions"><span className="draft-disclaimer">Please check every fact and any official instructions before submitting.</span><button className="button button-quiet" onClick={() => download.mutate()} disabled={download.isPending}>{download.isPending ? <LoaderCircle size={15} className="spin" /> : <Download size={15} />} Download as PDF</button></div>}
        {sources.length > 0 && <SourceCards sources={sources} />}
        {draft && !verified && <div className="helper-callout source-warning">The available official-source evidence was insufficient. This draft is not verified procedural guidance; check the relevant official SEBI/intermediary instructions.</div>}
      </section>
    </div>
  );
}
