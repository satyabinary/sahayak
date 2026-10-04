from utils.pdf.pdf_generator import generate_pdf


def test_generate_pdf_returns_bytes():
    content = "Investor grievance draft\n\nHello world"
    payload = generate_pdf(content)
    assert isinstance(payload, bytes)
    assert len(payload) > 0
