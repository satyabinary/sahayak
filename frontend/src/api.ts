export type Language = "hinglish" | "hindi" | "english";

export type GrievanceCase = {
  investor_name: string | null;
  broker_name: string | null;
  intermediary_type: string | null;
  issue_category: string | null;
  incident_date: string | null;
  amount_involved: string | null;
  transaction_details: string | null;
  complaint_already_filed: boolean | null;
  complaint_date: string | null;
  complaint_reference: string | null;
  response_received: string | null;
  evidence_available: string[];
  requested_resolution: string | null;
  description: string | null;
};

export type Source = {
  source_name: string;
  source_url: string | null;
  document_title: string | null;
  page_number: number | null;
  section?: string | null;
  score?: number | null;
};

export type ChatReply = {
  answer: string;
  sources: Source[];
  case: GrievanceCase | null;
  pending_case_field: string | null;
};

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init);
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { error?: { message?: string }; detail?: string } | null;
    throw new Error(body?.error?.message ?? body?.detail ?? `Request failed (${response.status})`);
  }
  return response.json() as Promise<T>;
}

export function getHealth() {
  return request<{ status: string; service: string; max_upload_mb: number }>("/api/health");
}

export function sendChat(payload: {
  session_id: string;
  message: string;
  history: { role: string; content: string }[];
  language: Language;
  case: GrievanceCase;
  pending_case_field: string | null;
}) {
  return request<ChatReply>("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export function saveCase(sessionId: string, grievance: GrievanceCase) {
  return request<{ session_id: string; case: GrievanceCase }>("/api/grievance", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId, case: grievance }),
  });
}

export async function extractImage(file: File) {
  const form = new FormData();
  form.set("image", file);
  return request<{
    broker_name: string | null;
    depository: string | null;
    dp_id: string | null;
    client_id: string | null;
    confidence: Record<string, number>;
    evidence_text: string;
    warnings: string[];
  }>("/api/vision/extract", { method: "POST", body: form });
}

export function getSources() {
  return request<{
    sources: {
      id: string;
      name: string;
      url: string;
      type: string;
      indexed: boolean;
    }[];
  }>("/api/sources");
}

export function requestIepfGuidance(question: string, language: Language) {
  return request<{ answer: string; sources: Source[] }>(
    "/api/iepf/guidance",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, language }),
    },
  );
}

export function generateComplaint(sessionId: string, grievance: GrievanceCase) {
  return request<{ draft: string; sources: Source[]; verified_sources_available: boolean }>(
    "/api/complaint/draft",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, case: grievance }),
    },
  );
}

export async function downloadComplaintPdf(content: string) {
  const response = await fetch(`${API_BASE}/api/complaint/pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => null)) as { error?: { message?: string }; detail?: string } | null;
    throw new Error(body?.error?.message ?? body?.detail ?? `PDF generation failed (${response.status})`);
  }
  return response.blob();
}
