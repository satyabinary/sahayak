import { FormEvent, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { ArrowUp, BookOpenCheck, LoaderCircle, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import type { Language } from "../api";
import { requestIepfGuidance } from "../api";
import { PageHeading } from "../components/PageHeading";
import { Markdown } from "../components/Markdown";
import { SourceCards } from "../components/SourceCards";

export function IepfPage({ language }: { language: Language }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<{ answer: string; sources: Awaited<ReturnType<typeof requestIepfGuidance>>["sources"] } | null>(null);
  const mutation = useMutation({
    mutationFn: () => requestIepfGuidance(question.trim(), language),
    onSuccess: (data) => setAnswer(data),
    onError: (error) => toast.error(error instanceof Error ? error.message : "IEPF guidance could not be retrieved."),
  });
  function submit(event: FormEvent) { event.preventDefault(); if (question.trim()) mutation.mutate(); }
  return (
    <div className="content-page iepf-page">
      <PageHeading eyebrow="OFFICIAL-SOURCE GUIDANCE" title="Unclaimed investments & IEPF" description="Ask about unclaimed dividends, shares, or the IEPF process. Answers are generated only when relevant retrieved evidence is available." />
      <div className="iepf-banner"><span><BookOpenCheck size={23} /></span><div><b>Start with your situation</b><p>Describe the kind of investment or information you’re looking for. Avoid sharing full account numbers or identity documents.</p></div></div>
      <section className="panel-card iepf-card">
        <form onSubmit={submit}><label className="field"><span>Your question</span><textarea rows={4} value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="For example: I have an unclaimed dividend. Where can I find official IEPF instructions?" disabled={mutation.isPending} /></label><div className="iepf-submit-row"><span><ShieldCheck size={14} /> We’ll check available official sources</span><button className="button button-primary" disabled={!question.trim() || mutation.isPending}>{mutation.isPending ? <><LoaderCircle size={15} className="spin" /> Checking…</> : <>Get guidance <ArrowUp size={15} /></>}</button></div></form>
        {answer && <div className="iepf-answer"><div className="eyebrow">GUIDANCE</div><Markdown content={answer.answer} /><SourceCards sources={answer.sources} /></div>}
      </section>
    </div>
  );
}
