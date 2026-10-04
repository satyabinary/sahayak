import { useState } from "react";
import { Link } from "react-router-dom";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, Check, CircleHelp, FileText, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { saveCase } from "../api";
import type { useSangyanState } from "../state";
import { PageHeading } from "../components/PageHeading";

const steps = ["What happened?", "Entity details", "Transaction", "Previous complaint", "Evidence", "Resolution", "Review"];
const schema = z.object({
  investor_name: z.string().optional(),
  broker_name: z.string().optional(),
  intermediary_type: z.string().optional(),
  issue_category: z.string().optional(),
  incident_date: z.string().optional(),
  amount_involved: z.string().optional(),
  transaction_details: z.string().optional(),
  complaint_already_filed: z.string().optional(),
  complaint_date: z.string().optional(),
  complaint_reference: z.string().optional(),
  response_received: z.string().optional(),
  evidence_available: z.string().optional(),
  requested_resolution: z.string().optional(),
  description: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;
type Props = ReturnType<typeof useSangyanState>;

export function GrievancePage({ caseData, setCaseData, sessionId }: Props) {
  const [step, setStep] = useState(0);
  const form = useForm<FormValues>({ resolver: zodResolver(schema), defaultValues: {
    investor_name: caseData.investor_name ?? "",
    broker_name: caseData.broker_name ?? "",
    intermediary_type: caseData.intermediary_type ?? "",
    issue_category: caseData.issue_category ?? "",
    incident_date: caseData.incident_date ?? "",
    amount_involved: caseData.amount_involved ?? "",
    transaction_details: caseData.transaction_details ?? "",
    complaint_already_filed: caseData.complaint_already_filed === null ? "" : String(caseData.complaint_already_filed),
    complaint_date: caseData.complaint_date ?? "",
    complaint_reference: caseData.complaint_reference ?? "",
    response_received: caseData.response_received ?? "",
    evidence_available: caseData.evidence_available.join(", "),
    requested_resolution: caseData.requested_resolution ?? "",
    description: caseData.description ?? "",
  } });
  const save = useMutation({ mutationFn: () => saveCase(sessionId, caseData), onSuccess: () => toast.success("Your case details are saved on this device."), onError: () => toast.error("Could not sync with the service. Your details remain saved locally.") });

  function nextStep() {
    if (step === 0 && !form.getValues("description")?.trim()) {
      form.setError("description", { message: "Please briefly describe what happened." });
      return;
    }
    const values = form.getValues();
    const { complaint_already_filed, evidence_available, ...rest } = values;
    const next = {
      ...caseData,
      ...Object.fromEntries(Object.entries(rest).map(([key, value]) => [key, value?.trim() || null])),
      complaint_already_filed: complaint_already_filed === "" || complaint_already_filed === undefined ? null : complaint_already_filed === "true",
      evidence_available: evidence_available?.split(",").map((item) => item.trim()).filter(Boolean) ?? [],
    };
    setCaseData(next);
    if (step < steps.length - 1) setStep((current) => current + 1);
    else save.mutate();
  }

  const input = (name: keyof FormValues, label: string, placeholder?: string) => (
    <label className="field"><span>{label}</span><input type="text" placeholder={placeholder} {...form.register(name)} />{form.formState.errors[name]?.message && <small className="field-error">{form.formState.errors[name]?.message}</small>}</label>
  );
  const area = (name: keyof FormValues, label: string, placeholder?: string) => (
    <label className="field"><span>{label}</span><textarea rows={4} placeholder={placeholder} {...form.register(name)} />{form.formState.errors[name]?.message && <small className="field-error">{form.formState.errors[name]?.message}</small>}</label>
  );

  return (
    <div className="content-page">
      <PageHeading eyebrow="GUIDED CASE INTAKE" title="Let’s understand your grievance" description="We’ll take this one step at a time. Share only what you’re comfortable sharing." />
      <div className="wizard-layout">
        <aside className="wizard-aside"><div className="wizard-progress-title"><span>YOUR PROGRESS</span><b>Step {step + 1} <small>of {steps.length}</small></b></div><div className="progress-track"><span style={{ width: `${((step + 1) / steps.length) * 100}%` }} /></div><div className="step-list">{steps.map((name, index) => <button type="button" key={name} disabled={index > step} className={`step-item ${index === step ? "current" : ""} ${index < step ? "completed" : ""}`} onClick={() => index <= step && setStep(index)}><span>{index < step ? <Check size={14} /> : index + 1}</span>{name}</button>)}</div><div className="privacy-note"><ShieldCheck size={16} /><span>Your details are saved locally and sent to the API when you continue to a draft. Don’t include OTPs or passwords.</span></div></aside>
        <section className="wizard-card">
          <div className="wizard-card-top"><div className="step-kicker">STEP {String(step + 1).padStart(2, "0")}</div><h2>{steps[step]}</h2><p>{[
            "A short description helps us understand what kind of support might be relevant.",
            "Tell us who the issue is with. You can leave anything unknown blank.",
            "Approximate details are fine; preserve what you know as accurately as possible.",
            "Knowing what has already happened helps us avoid repeating steps.",
            "List any records you have. You don’t need to upload them here.",
            "What would a helpful resolution look like for you?",
            "Review your details before moving on to a complaint draft.",
          ][step]}</p></div>
          <div className="wizard-fields">
            {step === 0 && <>{area("description", "What happened?", "For example: my broker has not returned funds and I have not received a response…")}<div className="field-row">{input("issue_category", "Issue category", "e.g. funds not returned")}</div></>}
            {step === 1 && <><div className="field-row">{input("investor_name", "Your name", "Name as you would use in a complaint")}{input("broker_name", "Broker / intermediary name", "Enter the entity name")}</div><label className="field"><span>Intermediary type</span><select {...form.register("intermediary_type")}><option value="">Select if known</option><option value="Stock broker">Stock broker</option><option value="Depository participant">Depository participant</option><option value="Mutual fund">Mutual fund</option><option value="Other">Other / not sure</option></select></label></>}
            {step === 2 && <><div className="field-row">{input("amount_involved", "Approximate amount involved", "e.g. ₹ 10,000")}{input("incident_date", "When did this happen?", "Keep the date or time period as you know it")}</div>{area("transaction_details", "Transaction or account details", "Only include details relevant to the issue. Avoid passwords and OTPs.")}</>}
            {step === 3 && <><label className="field"><span>Have you already raised a complaint with the intermediary?</span><select {...form.register("complaint_already_filed")}><option value="">Select an answer</option><option value="true">Yes</option><option value="false">No</option></select></label>{form.watch("complaint_already_filed") === "true" && <div className="field-row">{input("complaint_reference", "Complaint / ticket reference", "If you received one")}{input("complaint_date", "When did you raise it?", "Keep the date as you know it")}</div>}{area("response_received", "Have you received a response?", "Optional — share what they said, or that you are still waiting.")}</>}
            {step === 4 && <>{input("evidence_available", "What evidence do you have?", "Separate items with commas — email, statement, ticket…")}<div className="helper-callout"><CircleHelp size={16} />You can note supporting records such as emails, statements, screenshots, or ticket confirmations. Do not upload account credentials.</div></>}
            {step === 5 && <>{area("requested_resolution", "What outcome are you seeking?", "For example, return of funds or a written explanation…")}</>}
            {step === 6 && <div className="review-grid">{[
              ["Your name", caseData.investor_name], ["Broker / intermediary", caseData.broker_name], ["Issue", caseData.issue_category], ["What happened", caseData.description], ["Amount", caseData.amount_involved], ["Incident date", caseData.incident_date], ["Previous complaint", caseData.complaint_already_filed === null ? null : caseData.complaint_already_filed ? "Yes" : "No"], ["Reference", caseData.complaint_reference], ["Evidence", caseData.evidence_available.join(", ")], ["Requested resolution", caseData.requested_resolution],
            ].map(([label, value]) => <div className="review-item" key={String(label)}><small>{label}</small><p>{value || <span className="muted">Not provided</span>}</p></div>)}</div>}
          </div>
          <div className="wizard-actions">{step > 0 ? <button className="button button-quiet" onClick={() => setStep((current) => current - 1)}><ArrowLeft size={15} /> Back</button> : <Link to="/ask" className="button button-quiet"><MessageCircleIcon /> Ask instead</Link>}{step < steps.length - 1 ? <button className="button button-primary" onClick={nextStep}>Continue <ArrowRight size={15} /></button> : <><button className="button button-quiet" onClick={() => setStep(0)}><FileText size={15} /> Edit details</button><Link to="/complaint" className="button button-primary" onClick={() => save.mutate()}>Continue to draft <ArrowRight size={15} /></Link></>}</div>
        </section>
      </div>
    </div>
  );
}

function MessageCircleIcon() { return <CircleHelp size={15} />; }
