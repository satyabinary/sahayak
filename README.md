# Sangyan Sahayak

## AI Investor Protection Assistant

Sangyan Sahayak is an AI-assisted investor-protection platform designed to make grievance redressal and investor-procedure guidance easier for first-time investors, senior citizens, homemakers, and other retail investors who may find financial and regulatory workflows difficult to navigate.

The platform combines a modern React/TypeScript web application with a FastAPI backend and the existing Python AI services for chat, vision extraction, RAG retrieval, complaint drafting, and PDF generation.

The core idea is simple:

> **Understand the investor's problem → retrieve relevant official guidance → explain the next step clearly → collect the required case information → prepare a structured complaint draft.**

The assistant supports Hindi, Hinglish, and English interaction. General conversation can be handled directly by Gemini, while questions involving SEBI procedures, grievances, demat accounts, nomination, or IEPF are routed through the official-source knowledge base before Gemini generates the grounded response.

---

## Table of Contents

1. [What Sangyan Sahayak Does](#what-sangyan-sahayak-does)
2. [Core Features](#core-features)
3. [Who It Is For](#who-it-is-for)
4. [System Architecture](#system-architecture)
5. [Application Flow](#application-flow)
6. [Project Structure](#project-structure)
7. [Technology Stack](#technology-stack)
8. [Prerequisites](#prerequisites)
9. [Environment Configuration](#environment-configuration)
10. [Installation on Windows](#installation-on-windows)
11. [Knowledge Base Setup](#knowledge-base-setup)
12. [Running the Application](#running-the-application)
13. [Using the Application](#using-the-application)
14. [Feature Workflows](#feature-workflows)
15. [API Overview](#api-overview)
16. [RAG and Knowledge Base](#rag-and-knowledge-base)
17. [Vision-Based DP Detail Extraction](#vision-based-dp-detail-extraction)
18. [Complaint Generation and PDF](#complaint-generation-and-pdf)
19. [Developer Diagnostics](#developer-diagnostics)
20. [Testing](#testing)
21. [Security and Privacy](#security-and-privacy)
22. [Important Limitations](#important-limitations)
23. [Troubleshooting](#troubleshooting)
24. [Demo Flow for Judges](#demo-flow-for-judges)
25. [Development Notes](#development-notes)
26. [License](#license)

---

# What Sangyan Sahayak Does

Investor-protection workflows can involve multiple concepts at once: intermediary complaints, SEBI procedures, demat terminology, nomination, supporting documents, and formal complaint drafting.

Sangyan Sahayak brings these tasks into one guided application.

A typical workflow is:

```text
Investor problem
      ↓
Ask Sangyan
      ↓
Understand the situation
      ↓
Retrieve relevant official guidance
      ↓
Explain the next step in simple language
      ↓
Extract difficult account details when required
      ↓
Build the grievance case
      ↓
Generate complaint draft
      ↓
Generate downloadable PDF
      ↓
User reviews and submits through the appropriate official process
```

The system is intentionally **AI-assisted rather than fully autonomous**. It does not submit complaints to protected portals, automate OTP/CAPTCHA, or claim that a grievance has been filed when the user has not actually submitted it.

---

# Core Features

## 1. Ask Sangyan — AI Investor Assistant

Users can interact in:

- English
- Hindi
- Hinglish

The assistant handles general conversation directly and uses the regulatory knowledge base for questions involving investor-protection procedures.

Examples:

```text
"Hi"
"Mera broker response nahi de raha, mujhe kya karna chahiye?"
"Nominee kaise add kar sakta hu?"
"SEBI complaint kaise karte hain?"
"IEPF ke liye mujhe kya documents chahiye?"
```

For regulatory/procedural questions, relevant official-source material is retrieved before Gemini generates the response.

---

## 2. Official-Source RAG

The regulatory assistant uses retrieval-augmented generation (RAG).

The knowledge pipeline is:

```text
Official source URLs / official local documents
                ↓
        Document extraction
                ↓
            Chunking
                ↓
          Source hashing
                ↓
        Gemini embeddings
                ↓
            ChromaDB
                ↓
       Query embedding + retrieval
                ↓
       Grounded Gemini prompt
                ↓
       Answer + source metadata
```

The knowledge base is populated only from sources explicitly listed in:

```text
knowledge_base/sources.yaml
```

The sync process fetches explicitly configured HTTPS URLs on configured official domains, extracts HTML/PDF content, hashes source content, and avoids re-embedding unchanged sources.

A failed or empty sync is **not** treated as verified regulatory guidance.

---

## 3. Vision-Based DP Detail Extraction

Users can upload a broker/depository screenshot or statement.

Gemini Vision attempts to identify:

- Broker Name
- DP ID
- Client ID
- Depository

The result is returned as structured data and shown in editable fields so the user can verify it before using it.

The workflow is:

```text
Upload screenshot
      ↓
Validate file
      ↓
Temporary processing file
      ↓
Gemini Vision
      ↓
Structured extraction
      ↓
User verification
      ↓
Case data
```

Temporary screenshots are removed after extraction.

---

## 4. Grievance / Case Workflow

The application can collect structured case information such as:

- investor details
- intermediary/broker
- issue category
- incident details
- amount involved
- previous complaint/contact
- complaint reference
- response received
- evidence
- requested resolution

The intention is to move from an unstructured user story to a structured case that can be reviewed before a complaint draft is generated.

---

## 5. Complaint Draft Generation

The system converts structured case information into a formal complaint draft.

The draft can include:

- subject
- investor details
- intermediary/entity details
- summary of the issue
- chronology
- detailed grievance
- previous actions taken
- response received
- requested resolution
- supporting documents
- relevant regulatory references where supported by retrieved source material

The AI must not invent dates, amounts, transactions, regulatory sections, or other factual details supplied by the user.

---

## 6. Complaint PDF Generation

The backend uses FPDF2 to create a downloadable complaint document.

The system supports Unicode/Devanagari-aware PDF generation using an installed compatible font and HarfBuzz shaping where configured.

For Hindi/Indic-script PDF output, the host must have a suitable font or the application must be configured through:

```env
PDF_UNICODE_FONT=C:\path\to\font.ttf
```

---

## 7. IEPF Guidance

The application provides an IEPF guidance workflow using the same official-source approach.

It is designed to explain the relevant process and information rather than automate a protected government submission.

---

# Who It Is For

Sangyan Sahayak is designed especially for:

### First-Time Investors

Users who know that something has gone wrong but are unsure which process or institution they should approach.

### Senior Citizens

Users who benefit from simpler terminology, larger and clearer UI elements, and conversational step-by-step guidance.

### Homemakers / Retail Investors

Users who may not regularly interact with financial infrastructure and need a practical explanation rather than a technical document dump.

---

# System Architecture

The current application uses a React/TypeScript frontend and FastAPI backend while preserving the existing Python AI, RAG, vision, and PDF services.

```text
                         ┌──────────────────────────┐
                         │   React / TypeScript     │
                         │      Web Frontend        │
                         └────────────┬─────────────┘
                                      │
                                  REST API
                                      │
                                      ▼
                         ┌──────────────────────────┐
                         │        FastAPI           │
                         │      backend/api.py      │
                         └────────────┬─────────────┘
                                      │
             ┌────────────────────────┼─────────────────────────┐
             │                        │                         │
             ▼                        ▼                         ▼
       Chat / Text               Vision Engine              PDF Service
             │                        │                         │
             ▼                        ▼                         ▼
          Gemini                 Gemini Vision               FPDF2
             │
             ▼
       Regulatory intent
             │
             ▼
      Query embedding
             │
             ▼
          ChromaDB
             │
             ▼
      Retrieved context
             │
             ▼
      Grounded Gemini
             │
             ▼
      Response + Sources
```

The Streamlit application remains available as a fallback/reference interface.

---

# Application Flow

## General Conversation

```text
User message
    ↓
Chat engine
    ↓
General conversation detected
    ↓
Gemini text generation
    ↓
Assistant response
```

## Regulatory / Procedural Question

```text
User question
    ↓
Chat engine
    ↓
Regulatory/procedural route
    ↓
Query embedding
    ↓
ChromaDB retrieval
    ↓
Relevant source context
    ↓
Grounded Gemini prompt
    ↓
Answer + source metadata
```

## Screenshot Extraction

```text
Image upload
    ↓
FastAPI
    ↓
Vision service
    ↓
Gemini multimodal analysis
    ↓
Structured DP information
    ↓
Frontend review
```

## Complaint Generation

```text
Chat/case data
      +
Vision-extracted information
      +
Relevant regulatory context
      ↓
Complaint generation service
      ↓
Structured complaint draft
      ↓
PDF generator
      ↓
Downloadable PDF
```

---

# Project Structure

The repository is organized so that the frontend, API layer, AI services, RAG system, prompts, and document generation logic remain separated.

```text
sangyan-sahayak/
│
├── backend/
│   └── api.py                         # FastAPI application and API routes
│
├── frontend/
│   ├── src/                           # React + TypeScript application
│   ├── package.json
│   └── ...
│
├── utils/
│   ├── ai/
│   │   ├── text_engine.py             # Chat / grounded answer / complaint logic
│   │   ├── vision_engine.py           # Screenshot extraction
│   │   └── voice_engine.py             # Reserved/placeholder voice layer
│   │
│   ├── rag/
│   │   ├── document_loader.py
│   │   ├── chunker.py
│   │   ├── embeddings.py
│   │   ├── vector_store.py
│   │   └── retriever.py
│   │
│   ├── prompts/
│   │   ├── chat prompts
│   │   ├── vision prompts
│   │   ├── RAG prompts
│   │   └── complaint prompts
│   │
│   └── pdf/
│       └── pdf_generator.py            # FPDF2 complaint PDF generation
│
├── knowledge_base/
│   ├── sources.yaml                    # Explicit official-source registry
│   └── sync.py                         # Knowledge-base synchronization
│
├── data/
│   └── sebi_docs/                      # Optional local official source documents
│
├── app.py                              # Streamlit fallback/reference UI
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
└── tests/
```

The exact implementation may contain additional files; the important architectural separation is:

```text
Frontend → API → Services → Gemini/RAG/Vision/PDF
```

---

# Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript |
| API | FastAPI |
| AI | Google Gemini API |
| RAG | LangChain + ChromaDB |
| Embeddings | Gemini embedding model |
| Vision | Gemini multimodal processing |
| PDF | FPDF2 |
| Image handling | Pillow / Python image processing |
| Document parsing | pypdf / HTML extraction |
| Configuration | python-dotenv |
| Testing | pytest |
| Fallback UI | Streamlit |

The architecture is designed so the AI/provider layer is isolated from the web UI and can be updated without rewriting the entire product.

---

# Prerequisites

Before running the project locally, install:

- Python 3.10 or later
- Node.js 20 or later
- npm
- Git
- A Gemini API key with access to the configured text-generation and embedding models
- Network access to the official source URLs listed in `knowledge_base/sources.yaml`

For Hindi/Indic-script complaint PDFs, a suitable Devanagari-capable `.ttf` font may also be required.

---

# Environment Configuration

Create a local `.env` file in the project root.

**Do not commit `.env` to GitHub.**

Start from:

```powershell
Copy-Item .env.example .env
```

Example configuration:

```env
GEMINI_API_KEY=your_real_key
GEMINI_MODEL=gemini-3.8-flash
GEMINI_EMBEDDING_MODEL=gemini-embedding-001

CHAT_MAX_OUTPUT_TOKENS=1200

CHROMA_PERSIST_DIRECTORY=./data/chroma
TOP_K_RETRIEVAL=6
MAX_UPLOAD_MB=10

APP_ENV=development
LOG_LEVEL=INFO

CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173

# Optional for Indic-script PDFs
PDF_UNICODE_FONT=
```

## Environment variables

### `GEMINI_API_KEY`

The private Gemini API credential used by the backend.

### `GEMINI_MODEL`

The Gemini text/multimodal model configured for generation.

### `GEMINI_EMBEDDING_MODEL`

The embedding model used to build and query the knowledge base.

### `CHAT_MAX_OUTPUT_TOKENS`

Maximum response length available to chat generation.

### `CHROMA_PERSIST_DIRECTORY`

Persistent local directory used by ChromaDB.

### `TOP_K_RETRIEVAL`

Number of relevant source chunks returned for a regulatory query.

### `MAX_UPLOAD_MB`

Maximum permitted screenshot/upload size.

### `APP_ENV`

Application environment, for example `development` or `test`.

### `LOG_LEVEL`

Logging level. Use `DEBUG` only when troubleshooting.

### `CORS_ORIGINS`

Comma-separated frontend origins allowed by FastAPI.

### `PDF_UNICODE_FONT`

Optional path to a compatible Unicode/Devanagari font for generated PDFs.

---

# Installation on Windows

Open PowerShell in the project root.

## Step 1 — Create a virtual environment

```powershell
python -m venv .venv
```

## Step 2 — Activate it

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, configure your local execution policy as appropriate for your environment, or activate the environment from a supported terminal.

## Step 3 — Install Python dependencies

```powershell
pip install -r requirements.txt
```

## Step 4 — Create `.env`

```powershell
Copy-Item .env.example .env
```

Then edit `.env` and add your Gemini API key.

## Step 5 — Install frontend dependencies

```powershell
Set-Location frontend
npm install
Set-Location ..
```

At this point both the Python and React dependencies are available.

---

# Knowledge Base Setup

The regulatory knowledge base is a critical part of Sangyan Sahayak.

## Source registry

Configured official sources are stored in:

```text
knowledge_base/sources.yaml
```

Only explicitly configured HTTPS URLs on approved official domains should be added to the registry.

## Synchronize sources

Run:

```powershell
python -m knowledge_base.sync
```

The sync process:

1. Reads the configured source registry.
2. Fetches the explicitly listed official URLs.
3. Extracts text from HTML and PDF content where supported.
4. Preserves source metadata.
5. Hashes source content.
6. Skips unchanged material.
7. Creates embeddings for new/changed chunks.
8. Stores embeddings in ChromaDB.
9. Reports successful and failed sources.

## Important rule

A failed sync must **never** be replaced with automatically generated summaries and then treated as verified regulatory material.

If an official source is unavailable, the sync report should show that failure.

---

# Running the Application

Sangyan Sahayak currently supports the modern React frontend through FastAPI and also retains the Streamlit app as a fallback/reference interface.

## Run the FastAPI backend

From the project root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.api:app --reload --host 127.0.0.1 --port 8000
```

Backend:

```text
http://localhost:8000
```

Swagger / interactive API documentation:

```text
http://localhost:8000/docs
```

## Run the React frontend

Open a second PowerShell window:

```powershell
Set-Location frontend
npm run dev
```

Open:

```text
http://localhost:5173
```

## Configure another API origin

Create:

```text
frontend/.env.local
```

and set:

```env
VITE_API_BASE_URL=https://your-api-host
```

Never place Gemini credentials or other provider secrets in frontend environment variables.

---

# Run the Streamlit Fallback

The original Streamlit interface remains available for fallback/reference use.

From the project root:

```powershell
streamlit run app.py
```

The Streamlit application uses the same core AI/RAG services and is useful for troubleshooting or validating the backend behavior independently of the React frontend.

---

# Using the Application

## 1. Ask Sangyan

Open the Ask Sangyan section and enter a question.

### General question

Example:

```text
hi
```

The assistant can respond directly through Gemini without requiring regulatory retrieval.

### Regulatory question

Example:

```text
Nominee kaise add kar sakta hu?
```

The application retrieves relevant official material first and then generates a grounded response with source metadata.

---

## 2. File a Grievance

Open the grievance workflow and enter the information requested by the assistant/form.

The system is designed to collect enough structured information to understand the case without requiring the user to know legal terminology.

Typical information includes:

```text
Investor details
↓
Broker/intermediary
↓
Issue
↓
Amount / transaction details
↓
Previous complaint/contact
↓
Response received
↓
Evidence
↓
Requested resolution
```

Review the collected information before generating the final complaint draft.

---

## 3. Extract DP Details

Open the DP-details extraction workflow.

1. Upload a clear screenshot or statement.
2. Wait for Gemini Vision processing.
3. Review the extracted values.
4. Correct any field that is incorrect.
5. Use the verified values in the grievance case.

Supported extraction fields include:

```text
Broker Name
DP ID
Client ID
Depository
```

Never assume an AI-extracted value is correct without verification.

---

## 4. Generate Complaint Draft

Once the case information is complete:

1. Review the case summary.
2. Generate the complaint draft.
3. Check the factual content.
4. Review the regulatory references and sources.
5. Edit any user-specific details where required.
6. Generate/download the PDF.

The complaint should represent the user's actual facts and should not introduce invented dates, values, events, or regulatory provisions.

---

## 5. IEPF Guidance

Open the IEPF guidance workflow for questions related to the IEPF process.

The assistant uses the configured official-source knowledge base and presents procedural guidance with source context where available.

---

# Feature Workflows

## Chat and RAG Workflow

```text
User message
    ↓
Chat engine
    ↓
Intent / routing
    ├── General conversation → Gemini
    └── Regulatory/procedural → Query embedding
                                  ↓
                                ChromaDB
                                  ↓
                         Retrieved source context
                                  ↓
                         Grounded Gemini prompt
                                  ↓
                           Answer + citations
```

## Vision Workflow

```text
Upload image
    ↓
FastAPI upload endpoint
    ↓
Temporary file
    ↓
Vision engine
    ↓
Gemini multimodal model
    ↓
Structured result
    ↓
Frontend review/edit
```

## Complaint Workflow

```text
Chat / form information
           +
Verified DP details
           +
Relevant regulatory context
           ↓
Complaint draft service
           ↓
User review
           ↓
FPDF2
           ↓
Downloadable PDF
```

---

# API Overview

The exact implementation may expose additional endpoints, but the application is structured around API routes for health, chat, vision, complaint generation, sources, knowledge-base status, and IEPF guidance.

The main backend entry point is:

```text
backend/api.py
```

Interactive OpenAPI documentation is available at:

```text
http://localhost:8000/docs
```

Typical API capabilities include:

| Capability | Purpose |
|---|---|
| Health | Check backend availability |
| Chat | Generate general or grounded assistant responses |
| Vision extraction | Process screenshot and extract DP details |
| Grievance | Store/process structured case information |
| Complaint generation | Create complaint draft |
| Complaint PDF | Generate downloadable PDF |
| Sources | Expose knowledge-base source metadata |
| Knowledge-base status | Inspect indexing state |
| IEPF guidance | Provide official-source procedural guidance |

The frontend communicates with the backend using the configured API origin rather than calling Gemini directly.

---

# RAG and Knowledge Base

## Why RAG is used

Regulatory and procedural guidance can change. The application therefore does not rely only on the language model's built-in knowledge for questions where current official guidance matters.

Instead:

```text
Question
  ↓
Retrieve relevant official material
  ↓
Pass evidence to Gemini
  ↓
Generate a grounded response
```

## Sources

The project is designed around authoritative materials such as:

- SEBI SCORES information
- SEBI grievance guidance
- SEBI investor guidance
- SEBI nomination guidance
- IEPF-related official material
- other verified official documents explicitly added to the source registry

## Citation behavior

Retrieved metadata is surfaced with responses where available so the user can inspect the supporting source.

## Failure behavior

If the knowledge base does not contain enough verified material, the system should not manufacture a regulatory answer.

Instead, it should make the limitation clear and direct the user toward current official instructions.

---

# Vision-Based DP Detail Extraction

The Vision module sends the uploaded image to the configured Gemini multimodal service and asks for structured investor/depository information.

The intended response includes:

```json
{
  "broker_name": "...",
  "depository": "...",
  "dp_id": "...",
  "client_id": "...",
  "confidence": {},
  "warnings": []
}
```

The exact internal schema may differ as the application evolves; the frontend and backend should remain aligned on the active schema.

## Verification rule

The user must verify extracted account identifiers before using them in a complaint.

AI extraction is an assistance mechanism, not a source of truth.

---

# Complaint Generation and PDF

The complaint-generation layer converts the structured case into a readable formal draft.

The generator should preserve user-provided facts and avoid fabricated details.

The PDF layer uses FPDF2 and supports configured Unicode/Indic-script fonts.

## Hindi/Indic-script PDF setup

If a complaint contains Hindi/Devanagari text and the host does not have a suitable configured font, install a compatible `.ttf` file and set:

```env
PDF_UNICODE_FONT=C:\path\to\font.ttf
```

The application uses HarfBuzz shaping where configured so Indic-script rendering can be handled correctly.

---

# Developer Diagnostics

Developer diagnostics are available when:

```env
APP_ENV=development
```

or:

```env
APP_ENV=test
```

In the Streamlit fallback, enable **Developer diagnostics** from the sidebar.

Diagnostics can report:

- Chroma collection name
- stored document count
- whether a sample embedding exists
- safe sample metadata
- resolved persistence path
- Gemini connectivity check
- knowledge-base sync status
- top retrieval checks

Normal users should not see internal debug information.

## Debug logging

Temporarily set:

```env
LOG_LEVEL=DEBUG
```

Then restart the application.

Debug logs are designed to include safe operational information such as:

- short query digest
- character count
- route
- retrieval count
- retrieval score
- source metadata
- provider call status

They should not log:

- API keys
- full user questions
- retrieved document text
- embedding vectors
- Gemini responses
- sensitive investor data

---

# Testing

Run the test suite from the project root:

```powershell
pytest
```

The normal unit tests do not require a paid live Gemini call.

For live provider checks, use the developer-only diagnostic controls or an explicit integration test path configured for your environment.

## Recommended manual smoke test

After starting backend and frontend:

```text
1. Open Home
2. Open Ask Sangyan
3. Send "hi"
4. Ask a regulatory question
5. Verify source display
6. Open DP Details
7. Upload a test screenshot
8. Verify extracted fields
9. Open Grievance
10. Build a case
11. Generate complaint draft
12. Generate PDF
13. Verify the downloaded PDF
14. Open IEPF Guidance
```

---

# Security and Privacy

Sangyan Sahayak handles potentially sensitive investor information. The project therefore follows basic privacy and secret-management principles.

## API keys

Never commit:

```text
.env
```

Never place `GEMINI_API_KEY` in the browser/frontend code.

The Gemini key must remain on the backend.

## Uploaded screenshots

Screenshots are processed using temporary files and are removed after extraction.

Do not upload passwords, OTPs, or unnecessary sensitive documents.

## Logging

Operational logs avoid storing sensitive investor data and provider secrets.

## Browser-side state

The current application keeps the active case/chat in browser-side state where applicable, while the API keeps case state in server memory during its process lifetime.

This behavior should be considered when deploying the application to multiple instances or persistent environments.

## CORS

Configure:

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

For a deployed system, replace local origins with the actual frontend origin and use HTTPS.

---

# Important Limitations

## No automatic SCORES submission

The application does **not** submit grievances to the official SCORES portal.

It does not:

- automate OTP
- bypass CAPTCHA
- automate protected portal authentication
- claim a complaint was submitted when it was not

The user's final submission remains under the user's control.

## AI is not a legal or financial adviser

Sangyan Sahayak provides educational/procedural assistance.

It should not be treated as:

- legal advice
- investment advice
- a guaranteed interpretation of a user's legal rights
- a guarantee of complaint resolution
- a guarantee of refund or compensation

## Source availability

Official websites may deny automated downloads, change their structure, or become temporarily unavailable.

Always inspect the knowledge-base sync report and source citations before relying on a response.

## Current state storage

Case state is kept in server memory during the API process lifetime and in browser-side state for the active session.

A production multi-user deployment would require an explicit persistent and secure state layer.

---

# Troubleshooting

## 1. `GEMINI_API_KEY` is missing

Check `.env`:

```env
GEMINI_API_KEY=your_real_key
```

Restart the backend after changing environment variables.

---

## 2. Gemini returns a rate-limit/quota error

Check:

- Gemini project/API configuration
- selected model
- model quota/rate limits
- billing/tier status where applicable
- whether multiple processes are using the same project/key

The application surfaces a user-friendly provider error instead of exposing raw credentials.

---

## 3. Regulatory answers say there is not enough source material

Run:

```powershell
python -m knowledge_base.sync
```

Then inspect the sync output and developer diagnostics.

Confirm that:

- official URLs are reachable
- documents were successfully extracted
- ChromaDB contains indexed chunks
- embeddings are available
- the configured persistence directory is correct

Do not replace missing official material with generated summaries.

---

## 4. Vision extraction does not work

Check:

- screenshot format
- file size
- backend logs
- Gemini Vision availability
- whether the API receives the multipart file
- whether the temporary image file can be read

Retry with a clear JPG/PNG screenshot containing the relevant account/depository information.

---

## 5. PDF contains broken Hindi characters

Install/configure a suitable Unicode/Devanagari font and set:

```env
PDF_UNICODE_FONT=C:\path\to\font.ttf
```

Restart the backend and regenerate the PDF.

---

## 6. Frontend cannot connect to the API

Check that the backend is running at:

```text
http://localhost:8000
```

and the frontend is configured to use:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Also verify `CORS_ORIGINS` in the backend `.env`.

---

## 7. Streamlit works but React does not

Use the Streamlit application as a backend/reference diagnostic surface:

```powershell
streamlit run app.py
```

If Streamlit works while React does not, inspect the FastAPI route and frontend API integration before changing the underlying AI/RAG services.

---

# Demo Flow for Judges

A recommended end-to-end demonstration is:

## Step 1 — Start with a real user problem

Enter:

```text
Mera broker response nahi de raha aur mera fund return nahi hua.
```

Show how Sangyan Sahayak asks for the next relevant information instead of giving an unexplained block of legal text.

## Step 2 — Ask a regulatory/procedural question

Example:

```text
Nominee kaise add kar sakta hu?
```

Show the grounded answer and its official sources.

## Step 3 — Extract account information

Open **Extract DP Details**.

Upload a broker statement/screenshot.

Show:

```text
Broker Name
DP ID
Client ID
Depository
```

Then manually verify/edit the extracted values.

## Step 4 — Build the grievance

Move to the grievance workflow and show the collected case information.

## Step 5 — Generate the complaint

Generate the formal complaint draft.

## Step 6 — Generate the PDF

Download the FPDF2-generated complaint document.

## Step 7 — Explain the safety boundary

End by explaining:

> Sangyan Sahayak prepares and guides; the investor remains in control of the final submission.

---

# Development Notes

## Keep provider access isolated

Gemini requests should remain in the backend AI/provider layer. The React frontend should communicate with the FastAPI API and should never call Gemini directly.

## Keep RAG grounded

Regulatory answers should use retrieved official context wherever the question is procedural or regulatory.

## Keep prompts separate

Prompt definitions should remain in the dedicated prompts modules rather than being scattered throughout UI code.

## Keep temporary data temporary

Uploaded screenshots and generated runtime artifacts should not be treated as permanent application data unless a secure persistence design is explicitly introduced.

## Keep the Streamlit fallback available

The Streamlit application is useful as a fallback/reference UI while the React/FastAPI application is being developed and tested.

---

# GitHub / Hackathon Repository Guidance

The repository is intended to contain the complete source code required to understand and reproduce the project.

Include:

```text
Source code
Frontend
Backend
AI services
RAG implementation
Prompts
PDF generator
Tests
Documentation
.env.example
```

Do **not** commit:

```text
.env
Gemini API keys
.venv
node_modules
runtime uploads
personal investor screenshots
generated private complaint PDFs
local Chroma runtime files
```

Judges should be able to clone the repository, install dependencies, configure their own Gemini key, build the knowledge base, start the API, and start the frontend.

---

# License

Add the project's chosen license here before public release.

For hackathon submission, ensure the license is consistent with any third-party dependencies, downloaded source documents, fonts, and other redistributed assets used by the project.

---

# Sangyan Sahayak — Project Summary

Sangyan Sahayak combines conversational AI, official-source retrieval, multimodal document understanding, structured grievance building, and complaint-document generation into one investor-protection workflow.

The project is designed around a simple principle:

> **Make investor-protection procedures easier to understand, easier to prepare for, and easier to act on — without removing the user's control over the final decision or submission.**
