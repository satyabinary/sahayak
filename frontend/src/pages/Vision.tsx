import { useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Check, FileImage, ImagePlus, LoaderCircle, RotateCcw, UploadCloud } from "lucide-react";
import { toast } from "sonner";
import { extractImage, getHealth } from "../api";
import { PageHeading } from "../components/PageHeading";

type Extraction = Awaited<ReturnType<typeof extractImage>>;

export function VisionPage() {
  const health = useQuery({ queryKey: ["health"], queryFn: getHealth });
  const maxUploadMb = health.data?.max_upload_mb ?? 10;
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [result, setResult] = useState<Extraction | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const mutation = useMutation({
    mutationFn: extractImage,
    onSuccess: (data) => { setResult(data); toast.success("Screenshot details extracted. Please verify before using."); },
    onError: (error) => toast.error(error instanceof Error ? error.message : "Screenshot extraction failed."),
  });

  function chooseFile(selected?: File) {
    if (!selected) return;
    if (!["image/jpeg", "image/png"].includes(selected.type)) { toast.error("Please choose a JPG or PNG image."); return; }
    if (selected.size > maxUploadMb * 1024 * 1024) { toast.error(`Please choose an image smaller than ${maxUploadMb} MB.`); return; }
    setFile(selected);
    setResult(null);
    setPreview(URL.createObjectURL(selected));
  }

  const fields: [keyof Pick<Extraction, "broker_name" | "depository" | "dp_id" | "client_id">, string][] = [
    ["broker_name", "Broker name"], ["depository", "Depository"], ["dp_id", "DP ID"], ["client_id", "Client ID"],
  ];

  return (
    <div className="content-page">
      <PageHeading eyebrow="SCREENSHOT ASSIST" title="Extract your DP details" description="Upload a broker or depository screenshot. We’ll try to identify the visible account details for you." />
      <div className="vision-layout">
        <section className="panel-card upload-panel">
          <div className="card-title-row"><div><div className="eyebrow">UPLOAD IMAGE</div><h2>Your screenshot</h2></div><span className="upload-limit">Up to {maxUploadMb} MB</span></div>
          {!file ? <button className="drop-zone" onClick={() => inputRef.current?.click()} onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); chooseFile(event.dataTransfer.files[0]); }}><span className="upload-cloud"><UploadCloud size={24} /></span><b>Drop an image here, or <u>browse files</u></b><small>JPG or PNG · Maximum 10 MB</small></button> : <div className="image-preview-card"><img src={preview ?? ""} alt="Uploaded broker screenshot preview" /><div className="preview-file"><FileImage size={16} /><span><b>{file.name}</b><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></span><button className="icon-button" aria-label="Remove image" onClick={() => { setFile(null); setPreview(null); setResult(null); }}><RotateCcw size={15} /></button></div></div>}
          <input ref={inputRef} className="visually-hidden" type="file" accept="image/jpeg,image/png" onChange={(event) => chooseFile(event.target.files?.[0])} />
          {file && <button className="button button-primary extract-button" disabled={mutation.isPending} onClick={() => mutation.mutate(file)}>{mutation.isPending ? <><LoaderCircle size={16} className="spin" /> Analyzing screenshot…</> : <><ImagePlus size={16} /> Identify details</>}</button>}
          {mutation.isPending && <div className="processing-steps"><span className="processing-active"><i /> Reading broker information</span><span><i /> Identifying DP details</span></div>}
          <p className="upload-privacy">Your image is sent to the configured AI service for processing and is removed from the server afterward. Don’t upload passwords or OTPs.</p>
        </section>
        <section className="panel-card extraction-panel">
          <div className="card-title-row"><div><div className="eyebrow">EXTRACTED INFORMATION</div><h2>Review the details</h2></div>{result && <span className="verified-badge"><Check size={13} /> Extracted</span>}</div>
          {!result ? <div className="empty-extraction"><span><ImagePlus size={22} /></span><b>Nothing extracted yet</b><p>Choose a screenshot to see the identified details here. Please verify each value before using it.</p></div> : <>
            <div className="extraction-fields">{fields.map(([key, label]) => <label className="field" key={key}><span>{label}</span><input value={result[key] ?? ""} onChange={(event) => setResult({ ...result, [key]: event.target.value || null })} placeholder="Not identified" />{result.confidence[key] !== undefined && <small className="confidence-text">Confidence: {Math.round(result.confidence[key] * 100)}%</small>}</label>)}</div>
            {result.warnings.length > 0 && <div className="helper-callout">{result.warnings.join(" ")}</div>}
            <div className="verify-note"><Check size={15} /> Please verify these details against your official statement before using them.</div>
          </>}
        </section>
      </div>
    </div>
  );
}
