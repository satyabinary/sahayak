from utils.prompts.complaint_prompts import COMPLAINT_GENERATION_PROMPT
from utils.prompts.rag_prompts import RAG_RESPONSE_PROMPT
from utils.prompts.system_prompts import ASSISTANT_DISCLAIMER, SYSTEM_PROMPT


def test_prompt_contents_are_present():
    assert "Do not invent facts" in COMPLAINT_GENERATION_PROMPT
    assert "official source" in RAG_RESPONSE_PROMPT.lower()
    assert "Sangyan Sahayak" in SYSTEM_PROMPT
    assert "verify karein" in ASSISTANT_DISCLAIMER
