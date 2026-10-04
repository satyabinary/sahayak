import importlib


def test_project_modules_import():
    modules = [
        "app",
        "utils.config",
        "utils.ai.gemini_client",
        "utils.ai.vision_engine",
        "utils.rag.ingestion",
        "utils.pdf.pdf_generator",
    ]
    for module_name in modules:
        importlib.import_module(module_name)
