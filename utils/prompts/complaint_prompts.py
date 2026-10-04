COMPLAINT_GENERATION_PROMPT = """
Draft a professional grievance draft based only on the case facts below.

Rules:
- Do not invent facts, dates, amounts, transactions, communication, or regulatory sections.
- Keep user facts separate from regulatory references.
- Clearly label unsupported or unverified elements.
- Use simple and professional English or Hinglish where helpful.
- Conclude with a short note that the draft is AI-assisted and should be reviewed before submission.
""".strip()
