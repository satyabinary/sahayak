import { useEffect, useState } from "react";
import type { GrievanceCase, Language } from "./api";

const emptyCase: GrievanceCase = {
  investor_name: null,
  broker_name: null,
  intermediary_type: null,
  issue_category: null,
  incident_date: null,
  amount_involved: null,
  transaction_details: null,
  complaint_already_filed: null,
  complaint_date: null,
  complaint_reference: null,
  response_received: null,
  evidence_available: [],
  requested_resolution: null,
  description: null,
};

function getStoredCase(): GrievanceCase {
  try {
    return { ...emptyCase, ...JSON.parse(localStorage.getItem("sangyan.case") ?? "{}") } as GrievanceCase;
  } catch {
    return emptyCase;
  }
}

export function useSangyanState() {
  const [caseData, setCaseData] = useState<GrievanceCase>(getStoredCase);
  const [language, setLanguage] = useState<Language>(
    (localStorage.getItem("sangyan.language") as Language | null) ?? "hinglish",
  );
  const [sessionId] = useState(() => {
    const existing = localStorage.getItem("sangyan.session");
    if (existing) return existing;
    const created = crypto.randomUUID();
    localStorage.setItem("sangyan.session", created);
    return created;
  });

  useEffect(() => localStorage.setItem("sangyan.case", JSON.stringify(caseData)), [caseData]);
  useEffect(() => localStorage.setItem("sangyan.language", language), [language]);

  return { caseData, setCaseData, language, setLanguage, sessionId };
}

export { emptyCase };
