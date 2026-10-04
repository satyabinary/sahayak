VISION_PROMPT = """
Analyze the uploaded screenshot.
Extract only values that are actually visible.
Do not invent missing values.
Return JSON with broker_name, depository, dp_id, client_id, confidence, evidence_text, warnings.
Set confidence values between 0 and 1.
If data is unclear, set values to null and record a warning.
""".strip()
