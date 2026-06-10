"""
NEXUS AI Platform - Full Implementation Guide PDF Generator
Uses ReportLab to produce a richly formatted technical PDF with Python code samples.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.lib.colors import HexColor
import os

# ─── Color Palette ────────────────────────────────────────────────────────────
NAVY      = HexColor("#0A1628")
BLUE      = HexColor("#1B3A6B")
MID_BLUE  = HexColor("#1E5FAD")
ACCENT    = HexColor("#00C8F0")
TEAL      = HexColor("#0891B2")
MINT      = HexColor("#10B981")
PURPLE    = HexColor("#7C3AED")
ORANGE    = HexColor("#F59E0B")
RED       = HexColor("#EF4444")
LIGHT     = HexColor("#CBD5E1")
MUTED     = HexColor("#64748B")
CARD_BG   = HexColor("#0D2137")
WHITE     = colors.white
BLACK     = colors.black
CODE_BG   = HexColor("#0F172A")
CODE_FG   = HexColor("#E2E8F0")
KEYWORD   = HexColor("#7DD3FC")
STRING    = HexColor("#86EFAC")
COMMENT   = HexColor("#64748B")

W, H = A4

# ─── Custom Flowables ─────────────────────────────────────────────────────────

class ColorBar(Flowable):
    """Full-width colored separator bar."""
    def __init__(self, color, height=4):
        super().__init__()
        self.color = color
        self.bar_height = height
        self.width = W - 4*cm

    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.rect(0, 0, self.width, self.bar_height, fill=1, stroke=0)

    def wrap(self, aW, aH):
        return (self.width, self.bar_height + 2)


class SectionBanner(Flowable):
    """Dark full-width section header banner."""
    def __init__(self, number, title, subtitle="", color=None):
        super().__init__()
        self.number = number
        self.title = title
        self.subtitle = subtitle
        self.color = color or TEAL
        self.width = W - 4*cm
        self.height = 52

    def draw(self):
        c = self.canv
        # Background
        c.setFillColor(NAVY)
        c.rect(0, 0, self.width, self.height, fill=1, stroke=0)
        # Left accent
        c.setFillColor(self.color)
        c.rect(0, 0, 6, self.height, fill=1, stroke=0)
        # Number badge
        c.setFillColor(self.color)
        c.roundRect(14, 12, 28, 28, 4, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(28, 21, self.number)
        # Title
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 16)
        c.drawString(52, 30, self.title)
        # Subtitle
        if self.subtitle:
            c.setFillColor(self.color)
            c.setFont("Helvetica", 9)
            c.drawString(52, 16, self.subtitle)

    def wrap(self, aW, aH):
        return (self.width, self.height + 8)


class InfoBox(Flowable):
    """Colored info/tip/warning box."""
    def __init__(self, label, text, color=None, width=None):
        super().__init__()
        self.label = label
        self.text = text
        self.box_color = color or MINT
        self._width = width or (W - 4*cm)
        self.height = 44

    def draw(self):
        c = self.canv
        c.setFillColor(HexColor("#0D2137"))
        c.roundRect(0, 0, self._width, self.height, 4, fill=1, stroke=0)
        c.setFillColor(self.box_color)
        c.roundRect(0, 0, 5, self.height, 2, fill=1, stroke=0)
        c.setFillColor(self.box_color)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(12, self.height - 14, self.label)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 8.5)
        # Word-wrap manually
        words = self.text.split()
        line = ""
        y = self.height - 27
        for word in words:
            test = line + " " + word if line else word
            if c.stringWidth(test, "Helvetica", 8.5) < self._width - 22:
                line = test
            else:
                c.drawString(12, y, line)
                y -= 11
                line = word
        if line:
            c.drawString(12, y, line)

    def wrap(self, aW, aH):
        # Estimate height
        return (self._width, self.height + 6)


def build_styles():
    base = getSampleStyleSheet()

    def s(name, **kw):
        return ParagraphStyle(name, **kw)

    styles = {
        "cover_title": s("cover_title",
            fontName="Helvetica-Bold", fontSize=34, textColor=WHITE,
            leading=40, alignment=TA_CENTER),
        "cover_sub": s("cover_sub",
            fontName="Helvetica", fontSize=15, textColor=ACCENT,
            leading=22, alignment=TA_CENTER),
        "cover_desc": s("cover_desc",
            fontName="Helvetica", fontSize=10, textColor=LIGHT,
            leading=16, alignment=TA_CENTER),
        "h1": s("h1",
            fontName="Helvetica-Bold", fontSize=20, textColor=ACCENT,
            spaceBefore=14, spaceAfter=6, leading=26),
        "h2": s("h2",
            fontName="Helvetica-Bold", fontSize=14, textColor=WHITE,
            spaceBefore=10, spaceAfter=4, leading=20,
            backColor=CARD_BG, leftIndent=8, rightIndent=8,
            borderPad=4),
        "h3": s("h3",
            fontName="Helvetica-Bold", fontSize=11, textColor=MINT,
            spaceBefore=8, spaceAfter=3, leading=15),
        "body": s("body",
            fontName="Helvetica", fontSize=9.5, textColor=LIGHT,
            leading=15, spaceAfter=4, alignment=TA_JUSTIFY),
        "bullet": s("bullet",
            fontName="Helvetica", fontSize=9.5, textColor=LIGHT,
            leading=14, leftIndent=14, spaceAfter=2,
            bulletIndent=4, bulletFontName="Helvetica"),
        "code": s("code",
            fontName="Courier", fontSize=8, textColor=CODE_FG,
            leading=12, leftIndent=10, rightIndent=10,
            backColor=CODE_BG, spaceAfter=2,
            borderPad=6),
        "code_comment": s("code_comment",
            fontName="Courier", fontSize=8, textColor=COMMENT,
            leading=12, leftIndent=10, backColor=CODE_BG),
        "tag": s("tag",
            fontName="Helvetica-Bold", fontSize=8, textColor=NAVY,
            backColor=ACCENT, alignment=TA_CENTER,
            leftIndent=4, rightIndent=4, borderPad=2),
        "table_header": s("table_header",
            fontName="Helvetica-Bold", fontSize=8.5, textColor=WHITE,
            alignment=TA_CENTER),
        "table_cell": s("table_cell",
            fontName="Helvetica", fontSize=8, textColor=LIGHT,
            leading=12),
        "caption": s("caption",
            fontName="Helvetica-Oblique", fontSize=8, textColor=MUTED,
            spaceAfter=6, alignment=TA_CENTER),
        "toc_entry": s("toc_entry",
            fontName="Helvetica", fontSize=10, textColor=LIGHT,
            leading=18, leftIndent=10),
        "toc_section": s("toc_section",
            fontName="Helvetica-Bold", fontSize=11, textColor=ACCENT,
            leading=20, leftIndent=0, spaceBefore=6),
    }
    return styles


def code_block(lines, styles):
    """Return list of Paragraph flowables for a code block."""
    result = []
    for line in lines:
        stripped = line.rstrip()
        if stripped.startswith("#"):
            result.append(Paragraph(stripped.replace(" ", "&nbsp;").replace("<", "&lt;").replace(">", "&gt;"), styles["code_comment"]))
        else:
            colored = stripped.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            result.append(Paragraph(colored.replace(" ", "&nbsp;") if stripped else "&nbsp;", styles["code"]))
    return result


# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE NUMBERING + HEADER/FOOTER
# ═══════════════════════════════════════════════════════════════════════════════

class PageTemplate:
    def __init__(self, doc):
        self.doc = doc

    def __call__(self, c, doc):
        c.saveState()
        # Header stripe
        c.setFillColor(NAVY)
        c.rect(0, H - 1.1*cm, W, 1.1*cm, fill=1, stroke=0)
        c.setFillColor(ACCENT)
        c.rect(0, H - 1.1*cm, W, 3, fill=1, stroke=0)
        c.setFillColor(WHITE)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(2*cm, H - 0.78*cm, "NEXUS AI Platform")
        c.setFont("Helvetica", 8)
        c.setFillColor(LIGHT)
        c.drawRightString(W - 2*cm, H - 0.78*cm, "Implementation Guide & Full Python Codebase")
        # Footer
        c.setFillColor(NAVY)
        c.rect(0, 0, W, 1.0*cm, fill=1, stroke=0)
        c.setFillColor(LIGHT)
        c.setFont("Helvetica", 7.5)
        c.drawString(2*cm, 0.38*cm, "Software Resonance Group Inc. · Confidential")
        c.setFillColor(ACCENT)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(W/2, 0.38*cm, f"Page {doc.page}")
        c.drawRightString(W - 2*cm, 0.38*cm, "nexus@srgtechinc.com")
        c.restoreState()


# ═══════════════════════════════════════════════════════════════════════════════
#  BUILD DOCUMENT
# ═══════════════════════════════════════════════════════════════════════════════

def build_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        topMargin=1.4*cm, bottomMargin=1.4*cm,
        leftMargin=2*cm, rightMargin=2*cm,
        title="NEXUS AI Platform — Implementation Guide",
        author="Software Resonance Group Inc.",
    )

    pt = PageTemplate(doc)
    story = []
    ST = build_styles()

    def sp(n=8):
        return Spacer(1, n)

    def hr(color=TEAL, thickness=1):
        return HRFlowable(width="100%", thickness=thickness, color=color, spaceAfter=6)

    # ──────────────────────────────────────────────────────────────────────────
    # COVER PAGE
    # ──────────────────────────────────────────────────────────────────────────
    story.append(sp(60))
    story.append(Paragraph("NEXUS", ST["cover_title"]))
    story.append(sp(4))
    story.append(Paragraph("Unified AI Platform for Higher Education", ST["cover_sub"]))
    story.append(sp(16))
    story.append(ColorBar(ACCENT, 3))
    story.append(sp(16))
    story.append(Paragraph(
        "Agentic Architecture · Full Python Codebase · End-to-End Implementation Guide",
        ST["cover_desc"]))
    story.append(sp(8))
    story.append(Paragraph(
        "From zero to production — Student AI Assistant, Faculty Copilot, "
        "Admin Intelligence, Multi-Agent Routing, LangGraph Workflows, "
        "Vector Search, Predictive Analytics & more.",
        ST["cover_desc"]))
    story.append(sp(40))

    meta_data = [
        ["Prepared by", "Software Resonance Group Inc."],
        ["Product", "NEXUS — The Unified AI Copilot for Higher Education"],
        ["Version", "1.0 — Initial Architecture Release"],
        ["Date", "June 2026"],
        ["Audience", "Engineering Teams, Solution Architects, Technical Leads"],
    ]
    tbl = Table(meta_data, colWidths=[4.5*cm, 12*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), CARD_BG),
        ("BACKGROUND", (1,0), (1,-1), NAVY),
        ("TEXTCOLOR", (0,0), (0,-1), ACCENT),
        ("TEXTCOLOR", (1,0), (1,-1), LIGHT),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME", (1,0), (1,-1), "Helvetica"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (1,0), (1,-1), [NAVY, CARD_BG]),
        ("GRID", (0,0), (-1,-1), 0.3, MUTED),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(tbl)
    story.append(PageBreak())

    # ──────────────────────────────────────────────────────────────────────────
    # TABLE OF CONTENTS
    # ──────────────────────────────────────────────────────────────────────────
    story.append(SectionBanner("", "TABLE OF CONTENTS", "What's inside this guide", ACCENT))
    story.append(sp(10))

    toc = [
        ("1", "Architecture Overview & Design Principles", TEAL),
        ("2", "Project Setup & Environment", MINT),
        ("3", "Core Agentic Framework — LangGraph Router", PURPLE),
        ("4", "User Story 1: AI Student Assistant", ACCENT),
        ("5", "User Story 2: Faculty Copilot (AI Lecturer)", ORANGE),
        ("6", "User Story 3: AI Administrative Copilot", MINT),
        ("7", "Vector Search & RAG Pipeline", TEAL),
        ("8", "Predictive Analytics — Dropout Risk Model", RED),
        ("9", "Multi-Agent Routing — Full Orchestration", PURPLE),
        ("10", "API Layer — FastAPI Backend", ACCENT),
        ("11", "Frontend Integration Notes", ORANGE),
        ("12", "Deployment — Docker & Kubernetes", TEAL),
        ("13", "Testing Strategy", MINT),
        ("14", "Roadmap & Next Steps", ACCENT),
    ]

    for num, title, color in toc:
        row_data = [[
            Paragraph(f'<font color="#{color.hexval()[2:]}"><b>{num}</b></font>', ST["body"]),
            Paragraph(title, ST["toc_entry"])
        ]]
        t = Table(row_data, colWidths=[1*cm, 14.5*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,-1), CARD_BG),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("LINEBELOW", (0,0), (-1,-1), 0.3, MUTED),
        ]))
        story.append(t)
        story.append(sp(2))

    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 1 — Architecture Overview
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("1", "ARCHITECTURE OVERVIEW & DESIGN PRINCIPLES",
        "Agentic multi-layer architecture for NEXUS", TEAL))
    story.append(sp(8))

    story.append(Paragraph("High-Level Architecture", ST["h2"]))
    story.append(sp(4))
    story.append(Paragraph(
        "NEXUS is built on a <b>Multi-Agent Agentic Architecture</b> with four distinct layers. "
        "Every user request — whether from a student, faculty member or administrator — enters "
        "through a unified API gateway, gets classified by the Master Orchestrator, "
        "and is routed to the most appropriate specialized agent. "
        "Agents share a common memory layer (Redis + Vector DB) and a common data lake.",
        ST["body"]))
    story.append(sp(6))

    arch_layers = [
        ["Layer", "Components", "Responsibility"],
        ["UI / Client", "React Web, Mobile PWA, Chat Widget, REST API clients",
         "Capture user intent across all channels"],
        ["Gateway", "FastAPI + OAuth2/JWT, Rate Limiter, Request Logger",
         "Auth, rate limiting, request routing to orchestrator"],
        ["Orchestration", "LangGraph Master Router, Intent Classifier, Context Engine",
         "NLP intent detection, agent selection, memory lookup"],
        ["Agent Pool", "Student Agent, Faculty Agent, Admin Agent, Search Agent, Analytics Agent",
         "Domain-specific task execution using tools & LLMs"],
        ["Data / Tools", "Pinecone Vector DB, PostgreSQL, Redis, Kafka, REST APIs",
         "Persistent storage, real-time streaming, external integrations"],
    ]

    col_ws = [3.2*cm, 7.5*cm, 5.8*cm]
    tbl = Table(arch_layers, colWidths=col_ws)
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), ACCENT),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CARD_BG, HexColor("#0A1E35")]),
        ("TEXTCOLOR", (0,1), (-1,-1), LIGHT),
        ("GRID", (0,0), (-1,-1), 0.4, MUTED),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(tbl)
    story.append(sp(10))

    story.append(Paragraph("Design Principles", ST["h2"]))
    story.append(sp(4))
    principles = [
        ("Single Entry Point", "One API gateway handles all user types. Role is detected via JWT claims."),
        ("Intent-First Routing", "Every request goes through NLP intent classification before reaching any agent."),
        ("Agent Specialization", "Each agent owns its domain fully — prompt, tools, memory, fallback logic."),
        ("Parallel Execution", "Multi-task requests dispatch agents concurrently via asyncio.gather()."),
        ("Stateful Memory", "Short-term (Redis), Long-term (Vector DB) and Episodic (PostgreSQL) memory layers."),
        ("Graceful Degradation", "Every agent has a fallback: rule-based response or human handoff."),
        ("Security by Default", "PII redaction, LLM guardrails, and RBAC on every agent call."),
    ]
    for name, desc in principles:
        story.append(Paragraph(
            f'<font color="#{MINT.hexval()[2:]}"><b>▸ {name}:</b></font>  {desc}',
            ST["bullet"]))
    story.append(sp(6))
    story.append(InfoBox("KEY INSIGHT",
        "NEXUS treats every user interaction as a task graph — not a single prompt. "
        "The LangGraph router builds a DAG of agent nodes, executes them in the right order "
        "(or in parallel), and assembles a unified response.", ACCENT))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 2 — Project Setup
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("2", "PROJECT SETUP & ENVIRONMENT",
        "Folder structure, dependencies, env variables", MINT))
    story.append(sp(8))

    story.append(Paragraph("Recommended Folder Structure", ST["h2"]))
    story.append(sp(4))
    folder_lines = [
        "nexus/",
        "├── agents/",
        "│   ├── __init__.py",
        "│   ├── base_agent.py          # Abstract agent interface",
        "│   ├── student_agent.py       # Student AI Assistant",
        "│   ├── faculty_agent.py       # Faculty Copilot",
        "│   ├── admin_agent.py         # Admin Intelligence",
        "│   ├── search_agent.py        # Semantic Search / RAG",
        "│   └── analytics_agent.py     # Predictive Analytics",
        "├── orchestrator/",
        "│   ├── router.py              # LangGraph multi-agent router",
        "│   ├── intent_classifier.py   # NLP classifier",
        "│   └── memory.py              # Short/Long-term memory manager",
        "├── api/",
        "│   ├── main.py                # FastAPI app entry point",
        "│   ├── auth.py                # JWT/OAuth2 middleware",
        "│   ├── routes/",
        "│   │   ├── chat.py            # /chat endpoint",
        "│   │   ├── analytics.py       # /analytics endpoint",
        "│   │   └── admin.py           # /admin endpoint",
        "├── models/",
        "│   ├── schemas.py             # Pydantic request/response models",
        "│   └── db_models.py           # SQLAlchemy ORM models",
        "├── services/",
        "│   ├── vector_store.py        # Pinecone / Weaviate wrapper",
        "│   ├── llm_client.py          # LLM abstraction (Groq / OpenAI)",
        "│   ├── guardrails.py          # LLM output safety checks",
        "│   └── notifications.py       # Alerts & push notifications",
        "├── data/",
        "│   ├── seed_data.py           # Initial DB seeding scripts",
        "│   └── migrations/            # Alembic migrations",
        "├── tests/",
        "│   ├── test_agents.py",
        "│   ├── test_router.py",
        "│   └── test_api.py",
        "├── docker/",
        "│   ├── Dockerfile",
        "│   └── docker-compose.yml",
        "├── .env.example",
        "├── requirements.txt",
        "└── README.md",
    ]
    story.extend(code_block(folder_lines, ST))
    story.append(sp(10))

    story.append(Paragraph("requirements.txt", ST["h2"]))
    story.append(sp(4))
    req_lines = [
        "# ── Core AI / LLM ─────────────────────────────",
        "langchain==0.2.16",
        "langchain-groq==0.1.9",
        "langgraph==0.2.28",
        "langchain-community==0.2.16",
        "openai==1.40.0",
        "",
        "# ── Vector Database ────────────────────────────",
        "pinecone-client==3.2.2",
        "sentence-transformers==3.0.1",
        "",
        "# ── Backend / API ──────────────────────────────",
        "fastapi==0.112.0",
        "uvicorn[standard]==0.30.6",
        "python-jose[cryptography]==3.3.0",
        "passlib[bcrypt]==1.7.4",
        "python-multipart==0.0.9",
        "",
        "# ── Database ───────────────────────────────────",
        "sqlalchemy==2.0.32",
        "asyncpg==0.29.0",
        "alembic==1.13.2",
        "redis==5.0.8",
        "",
        "# ── ML / Analytics ─────────────────────────────",
        "scikit-learn==1.5.1",
        "pandas==2.2.2",
        "numpy==1.26.4",
        "",
        "# ── Safety / Guardrails ────────────────────────",
        "guardrails-ai==0.5.0",
        "presidio-analyzer==2.2.354",
        "presidio-anonymizer==2.2.354",
        "",
        "# ── Utilities ──────────────────────────────────",
        "pydantic==2.8.2",
        "python-dotenv==1.0.1",
        "httpx==0.27.0",
        "celery==5.4.0",
        "kafka-python==2.0.2",
    ]
    story.extend(code_block(req_lines, ST))
    story.append(sp(10))

    story.append(Paragraph(".env Configuration", ST["h2"]))
    story.append(sp(4))
    env_lines = [
        "# ── LLM ──────────────────────────────────────────",
        "GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "LLM_MODEL=llama-3.3-70b-versatile",
        "FALLBACK_MODEL=gpt-4o-mini",
        "",
        "# ── Vector DB ─────────────────────────────────────",
        "PINECONE_API_KEY=pc-xxxxxxxxxxxxxxxxxxxxxxxx",
        "PINECONE_INDEX_NAME=nexus-knowledge-base",
        "PINECONE_ENVIRONMENT=us-east-1",
        "",
        "# ── Database ──────────────────────────────────────",
        "DATABASE_URL=postgresql+asyncpg://nexus:password@localhost/nexus_db",
        "REDIS_URL=redis://localhost:6379/0",
        "",
        "# ── Auth ──────────────────────────────────────────",
        "JWT_SECRET_KEY=your-super-secret-jwt-key-change-this",
        "JWT_ALGORITHM=HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES=480",
        "",
        "# ── App ───────────────────────────────────────────",
        "APP_ENV=development",
        "LOG_LEVEL=INFO",
        "MAX_AGENT_ITERATIONS=5",
        "AGENT_TIMEOUT_SECONDS=30",
    ]
    story.extend(code_block(env_lines, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 3 — Core Agentic Framework
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("3", "CORE AGENTIC FRAMEWORK — LANGGRAPH ROUTER",
        "Intent classification + multi-agent graph with LangGraph", PURPLE))
    story.append(sp(8))

    story.append(Paragraph("Base Agent Interface  (agents/base_agent.py)", ST["h2"]))
    story.append(sp(4))
    base_agent_code = [
        "# agents/base_agent.py",
        "from abc import ABC, abstractmethod",
        "from typing import Any, Dict, List, Optional",
        "from pydantic import BaseModel",
        "from langchain_groq import ChatGroq",
        "from langchain.schema import HumanMessage, SystemMessage",
        "from services.guardrails import check_output_safety",
        "from services.llm_client import get_llm",
        "import logging",
        "",
        "logger = logging.getLogger(__name__)",
        "",
        "",
        "class AgentInput(BaseModel):",
        "    user_id: str",
        "    role: str                     # student | faculty | admin",
        "    message: str",
        "    context: Dict[str, Any] = {}  # Memory / session context",
        "    session_id: str = ''",
        "",
        "",
        "class AgentOutput(BaseModel):",
        "    agent_name: str",
        "    response: str",
        "    confidence: float = 1.0",
        "    metadata: Dict[str, Any] = {}",
        "    requires_human: bool = False",
        "",
        "",
        "class BaseAgent(ABC):",
        "    '''Abstract base class for all NEXUS agents.'''",
        "",
        "    def __init__(self, name: str, system_prompt: str):",
        "        self.name = name",
        "        self.system_prompt = system_prompt",
        "        self.llm = get_llm()  # Returns configured ChatGroq",
        "",
        "    @abstractmethod",
        "    def get_tools(self) -> List[Any]:",
        "        '''Return list of LangChain tools this agent can use.'''",
        "        pass",
        "",
        "    @abstractmethod",
        "    async def execute(self, inp: AgentInput) -> AgentOutput:",
        "        '''Main execution method — must be implemented per agent.'''",
        "        pass",
        "",
        "    async def _call_llm(self, user_msg: str, context: str = '') -> str:",
        "        '''Helper: call the LLM with system + context + user message.'''",
        "        messages = [",
        "            SystemMessage(content=self.system_prompt),",
        "        ]",
        "        if context:",
        "            messages.append(HumanMessage(content=f'Context:\\n{context}'))",
        "        messages.append(HumanMessage(content=user_msg))",
        "        try:",
        "            result = await self.llm.ainvoke(messages)",
        "            raw = result.content",
        "            safe = await check_output_safety(raw)  # PII + safety check",
        "            return safe",
        "        except Exception as e:",
        "            logger.error(f'{self.name} LLM error: {e}')",
        "            return 'I encountered an issue. Please try again or contact support.'",
    ]
    story.extend(code_block(base_agent_code, ST))
    story.append(sp(10))

    story.append(Paragraph("Intent Classifier  (orchestrator/intent_classifier.py)", ST["h2"]))
    story.append(sp(4))
    intent_code = [
        "# orchestrator/intent_classifier.py",
        "from enum import Enum",
        "from typing import Tuple",
        "from langchain_groq import ChatGroq",
        "from langchain.schema import HumanMessage, SystemMessage",
        "import json, os",
        "",
        "",
        "class Intent(str, Enum):",
        "    STUDENT_QUERY    = 'student_query'     # Attendance, grades, schedule",
        "    STUDY_HELP       = 'study_help'         # Study plans, topics, quizzes",
        "    CAREER_GUIDANCE  = 'career_guidance'    # Placement, resume, jobs",
        "    CONTENT_CREATE   = 'content_create'     # Lesson plans, MCQs, assignments",
        "    GRADING_FEEDBACK = 'grading_feedback'   # Grade work, provide feedback",
        "    FACULTY_ANALYTICS= 'faculty_analytics'  # Class performance insights",
        "    ADMIN_REPORT     = 'admin_report'       # Institutional reports, KPIs",
        "    ADMIN_PREDICT    = 'admin_predict'       # Dropout risk, forecasting",
        "    ADMIN_WORKFLOW   = 'admin_workflow'     # Approvals, scheduling",
        "    SEARCH           = 'search'             # Knowledge base / policy lookup",
        "    UNKNOWN          = 'unknown'",
        "",
        "",
        "CLASSIFICATION_PROMPT = '''",
        "You are an intent classifier for a university AI platform.",
        "Given the user message and their role, return ONLY a JSON object:",
        "{",
        "  \"intent\": \"<intent_value>\",",
        "  \"confidence\": <0.0-1.0>,",
        "  \"entities\": {\"subject\": \"\", \"date\": \"\", \"student_id\": \"\"}",
        "}",
        "",
        "Intents: student_query, study_help, career_guidance, content_create,",
        "grading_feedback, faculty_analytics, admin_report, admin_predict,",
        "admin_workflow, search, unknown",
        "'''",
        "",
        "",
        "class IntentClassifier:",
        "    def __init__(self):",
        "        self.llm = ChatGroq(",
        "            model='llama-3.3-70b-versatile',",
        "            temperature=0,",
        "            api_key=os.getenv('GROQ_API_KEY')",
        "        )",
        "",
        "    async def classify(self, message: str, role: str) -> Tuple[Intent, float, dict]:",
        "        prompt = f'Role: {role}\\nMessage: {message}'",
        "        messages = [",
        "            SystemMessage(content=CLASSIFICATION_PROMPT),",
        "            HumanMessage(content=prompt)",
        "        ]",
        "        result = await self.llm.ainvoke(messages)",
        "        try:",
        "            data = json.loads(result.content.strip())",
        "            intent = Intent(data.get('intent', 'unknown'))",
        "            confidence = float(data.get('confidence', 0.5))",
        "            entities = data.get('entities', {})",
        "            return intent, confidence, entities",
        "        except Exception:",
        "            return Intent.UNKNOWN, 0.0, {}",
    ]
    story.extend(code_block(intent_code, ST))
    story.append(sp(10))

    story.append(Paragraph("LangGraph Multi-Agent Router  (orchestrator/router.py)", ST["h2"]))
    story.append(sp(4))
    story.append(InfoBox("HOW IT WORKS",
        "LangGraph builds a state machine graph. Each node is an agent or decision point. "
        "The router uses conditional edges to dispatch to the right agent(s), "
        "and asyncio.gather() for parallel multi-agent execution.", PURPLE))
    story.append(sp(6))
    router_code = [
        "# orchestrator/router.py",
        "from langgraph.graph import StateGraph, END",
        "from typing import TypedDict, List, Annotated",
        "import operator, asyncio",
        "from orchestrator.intent_classifier import IntentClassifier, Intent",
        "from orchestrator.memory import MemoryManager",
        "from agents.student_agent import StudentAgent",
        "from agents.faculty_agent import FacultyAgent",
        "from agents.admin_agent import AdminAgent",
        "from agents.search_agent import SearchAgent",
        "from agents.analytics_agent import AnalyticsAgent",
        "from agents.base_agent import AgentInput, AgentOutput",
        "",
        "",
        "# ── Graph State ───────────────────────────────────────────────────",
        "class NexusState(TypedDict):",
        "    user_id: str",
        "    role: str",
        "    message: str",
        "    session_id: str",
        "    intent: str",
        "    confidence: float",
        "    entities: dict",
        "    context: dict",
        "    agent_outputs: Annotated[List[AgentOutput], operator.add]",
        "    final_response: str",
        "",
        "",
        "# ── Agent Registry ────────────────────────────────────────────────",
        "INTENT_TO_AGENT = {",
        "    Intent.STUDENT_QUERY:    'student',",
        "    Intent.STUDY_HELP:       'student',",
        "    Intent.CAREER_GUIDANCE:  'student',",
        "    Intent.CONTENT_CREATE:   'faculty',",
        "    Intent.GRADING_FEEDBACK: 'faculty',",
        "    Intent.FACULTY_ANALYTICS:'faculty',",
        "    Intent.ADMIN_REPORT:     'admin',",
        "    Intent.ADMIN_PREDICT:    'analytics',",
        "    Intent.ADMIN_WORKFLOW:   'admin',",
        "    Intent.SEARCH:           'search',",
        "    Intent.UNKNOWN:          'search',",
        "}",
        "",
        "",
        "class NexusRouter:",
        "    def __init__(self):",
        "        self.classifier = IntentClassifier()",
        "        self.memory = MemoryManager()",
        "        self.agents = {",
        "            'student':   StudentAgent(),",
        "            'faculty':   FacultyAgent(),",
        "            'admin':     AdminAgent(),",
        "            'search':    SearchAgent(),",
        "            'analytics': AnalyticsAgent(),",
        "        }",
        "        self.graph = self._build_graph()",
        "",
        "    def _build_graph(self) -> StateGraph:",
        "        g = StateGraph(NexusState)",
        "",
        "        # Add nodes",
        "        g.add_node('classify',   self._classify_node)",
        "        g.add_node('load_ctx',   self._load_context_node)",
        "        g.add_node('student',    self._make_agent_node('student'))",
        "        g.add_node('faculty',    self._make_agent_node('faculty'))",
        "        g.add_node('admin',      self._make_agent_node('admin'))",
        "        g.add_node('search',     self._make_agent_node('search'))",
        "        g.add_node('analytics',  self._make_agent_node('analytics'))",
        "        g.add_node('synthesize', self._synthesize_node)",
        "",
        "        # Entry → classify → load context → route",
        "        g.set_entry_point('classify')",
        "        g.add_edge('classify', 'load_ctx')",
        "        g.add_conditional_edges('load_ctx', self._route_to_agent, {",
        "            'student':   'student',",
        "            'faculty':   'faculty',",
        "            'admin':     'admin',",
        "            'search':    'search',",
        "            'analytics': 'analytics',",
        "        })",
        "        for agent_name in ['student','faculty','admin','search','analytics']:",
        "            g.add_edge(agent_name, 'synthesize')",
        "        g.add_edge('synthesize', END)",
        "",
        "        return g.compile()",
        "",
        "    async def _classify_node(self, state: NexusState) -> NexusState:",
        "        intent, conf, entities = await self.classifier.classify(",
        "            state['message'], state['role']",
        "        )",
        "        return {**state, 'intent': intent, 'confidence': conf, 'entities': entities}",
        "",
        "    async def _load_context_node(self, state: NexusState) -> NexusState:",
        "        ctx = await self.memory.get_context(",
        "            state['user_id'], state['session_id']",
        "        )",
        "        return {**state, 'context': ctx}",
        "",
        "    def _route_to_agent(self, state: NexusState) -> str:",
        "        return INTENT_TO_AGENT.get(state['intent'], 'search')",
        "",
        "    def _make_agent_node(self, agent_name: str):",
        "        async def node(state: NexusState) -> NexusState:",
        "            agent = self.agents[agent_name]",
        "            inp = AgentInput(",
        "                user_id=state['user_id'], role=state['role'],",
        "                message=state['message'], context=state['context'],",
        "                session_id=state['session_id']",
        "            )",
        "            output = await agent.execute(inp)",
        "            await self.memory.save_interaction(",
        "                state['user_id'], state['message'], output.response",
        "            )",
        "            return {**state, 'agent_outputs': [output]}",
        "        return node",
        "",
        "    async def _synthesize_node(self, state: NexusState) -> NexusState:",
        "        outputs = state.get('agent_outputs', [])",
        "        if not outputs:",
        "            return {**state, 'final_response': 'No response generated.'}",
        "        # Single agent: return directly",
        "        if len(outputs) == 1:",
        "            return {**state, 'final_response': outputs[0].response}",
        "        # Multi-agent: merge responses",
        "        combined = '\\n\\n'.join(f'[{o.agent_name}]\\n{o.response}' for o in outputs)",
        "        return {**state, 'final_response': combined}",
        "",
        "    async def run(self, user_id: str, role: str, message: str,",
        "                  session_id: str = '') -> str:",
        "        initial_state = NexusState(",
        "            user_id=user_id, role=role, message=message,",
        "            session_id=session_id, intent='', confidence=0.0,",
        "            entities={}, context={}, agent_outputs=[], final_response=''",
        "        )",
        "        result = await self.graph.ainvoke(initial_state)",
        "        return result['final_response']",
    ]
    story.extend(code_block(router_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 4 — Student Agent
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("4", "USER STORY 1: AI STUDENT ASSISTANT",
        "24/7 academic support, study plans, attendance, schedule queries", ACCENT))
    story.append(sp(8))

    story.append(Paragraph("User Story", ST["h2"]))
    story.append(sp(4))
    story.append(Paragraph(
        '<i>"As a student, I want to ask Nexus anything about my academics — '
        'attendance, schedules, grades, fees, assignments, study plans — and get '
        'an instant, personalized answer at any time of day."</i>',
        ST["body"]))
    story.append(sp(8))

    story.append(Paragraph("Student Agent  (agents/student_agent.py)", ST["h2"]))
    story.append(sp(4))
    student_code = [
        "# agents/student_agent.py",
        "from langchain.tools import tool",
        "from langchain.agents import create_react_agent, AgentExecutor",
        "from langchain import hub",
        "from agents.base_agent import BaseAgent, AgentInput, AgentOutput",
        "from services.vector_store import VectorStore",
        "from models.schemas import StudentProfile",
        "from sqlalchemy.ext.asyncio import AsyncSession",
        "from services.db import get_student_data",
        "import asyncio",
        "",
        "",
        "STUDENT_SYSTEM_PROMPT = '''",
        "You are NEXUS, an AI Study Assistant for university students.",
        "You have access to real-time data about the student's:",
        "- Attendance, grades, assignments, timetable, fees",
        "- Course materials and past papers",
        "- Campus policies and procedures",
        "",
        "Always address the student by name. Be concise, warm, and helpful.",
        "If you cannot find data, say so clearly and suggest who to contact.",
        "'''",
        "",
        "",
        "# ── Tools ────────────────────────────────────────────────────────",
        "@tool",
        "async def get_attendance(student_id: str, subject: str = '') -> str:",
        "    '''Fetch student attendance. Optionally filter by subject.'''",
        "    data = await get_student_data(student_id, 'attendance', subject)",
        "    if not data:",
        "        return 'Attendance data not found.'",
        "    overall = data.get('overall_pct', 0)",
        "    subjects = data.get('by_subject', {})",
        "    result = f'Overall Attendance: {overall}%\\n'",
        "    for subj, pct in subjects.items():",
        "        status = '⚠ Low' if pct < 75 else '✓ OK'",
        "        result += f'  {subj}: {pct}% {status}\\n'",
        "    return result",
        "",
        "",
        "@tool",
        "async def get_upcoming_schedule(student_id: str) -> str:",
        "    '''Get next 7 days of classes, exams, and assignment deadlines.'''",
        "    data = await get_student_data(student_id, 'schedule')",
        "    if not data:",
        "        return 'Schedule not available.'",
        "    lines = ['Upcoming this week:']",
        "    for item in data.get('items', [])[:10]:",
        "        lines.append(f\"  {item['date']} | {item['type']}: {item['title']}\")",
        "    return '\\n'.join(lines)",
        "",
        "",
        "@tool",
        "async def generate_study_plan(student_id: str, subjects: str,",
        "                              exam_date: str) -> str:",
        "    '''Create a personalized study plan for given subjects and exam date.'''",
        "    profile = await get_student_data(student_id, 'performance')",
        "    weak_areas = profile.get('weak_topics', [])",
        "    prompt = (",
        "        f'Create a detailed 2-week study plan for: {subjects}.\\n'",
        "        f'Exam date: {exam_date}.\\n'",
        "        f'Student weak areas: {\", \".join(weak_areas)}.\\n'",
        "        f'Include: daily schedule, revision techniques, practice tests.'",
        "    )",
        "    return prompt  # Returned to LLM for generation",
        "",
        "",
        "@tool",
        "async def get_fee_status(student_id: str) -> str:",
        "    '''Check fee payment status and upcoming due dates.'''",
        "    data = await get_student_data(student_id, 'fees')",
        "    if not data:",
        "        return 'Fee information not found.'",
        "    return (",
        "        f\"Total: {data['total']} | Paid: {data['paid']} | \"",
        "        f\"Due: {data['due']} | Next due: {data['next_due_date']}\"",
        "    )",
        "",
        "",
        "@tool",
        "async def search_campus_kb(query: str) -> str:",
        "    '''Search the campus knowledge base for policies, procedures, info.'''",
        "    vs = VectorStore()",
        "    results = await vs.similarity_search(query, top_k=3,",
        "                                          namespace='campus_kb')",
        "    if not results:",
        "        return 'No relevant information found in the knowledge base.'",
        "    return '\\n\\n'.join([r['text'] for r in results])",
        "",
        "",
        "# ── Agent ────────────────────────────────────────────────────────",
        "class StudentAgent(BaseAgent):",
        "    def __init__(self):",
        "        super().__init__('StudentAgent', STUDENT_SYSTEM_PROMPT)",
        "",
        "    def get_tools(self):",
        "        return [get_attendance, get_upcoming_schedule,",
        "                generate_study_plan, get_fee_status, search_campus_kb]",
        "",
        "    async def execute(self, inp: AgentInput) -> AgentOutput:",
        "        tools = self.get_tools()",
        "        prompt = hub.pull('hwchase17/react')",
        "        agent = create_react_agent(self.llm, tools, prompt)",
        "        executor = AgentExecutor(",
        "            agent=agent, tools=tools,",
        "            max_iterations=5, handle_parsing_errors=True",
        "        )",
        "        enriched_msg = (",
        "            f\"Student ID: {inp.user_id}\\n\"",
        "            f\"Query: {inp.message}\"",
        "        )",
        "        try:",
        "            result = await executor.ainvoke({'input': enriched_msg})",
        "            return AgentOutput(",
        "                agent_name='StudentAgent',",
        "                response=result['output'],",
        "                confidence=0.9",
        "            )",
        "        except Exception as e:",
        "            fallback = await self._call_llm(inp.message)",
        "            return AgentOutput(",
        "                agent_name='StudentAgent', response=fallback, confidence=0.6",
        "            )",
    ]
    story.extend(code_block(student_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 5 — Faculty Copilot
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("5", "USER STORY 2: FACULTY COPILOT",
        "Lesson planning, MCQ generation, grading, student insights", ORANGE))
    story.append(sp(8))

    story.append(Paragraph("User Story", ST["h2"]))
    story.append(sp(4))
    story.append(Paragraph(
        '<i>"As a faculty member, I want to instantly generate lesson plans, '
        'quizzes, and assignments, get AI-graded work with feedback, and see '
        'at-risk students — so I can focus on teaching rather than admin tasks."</i>',
        ST["body"]))
    story.append(sp(8))

    story.append(Paragraph("Faculty Agent  (agents/faculty_agent.py)", ST["h2"]))
    story.append(sp(4))
    faculty_code = [
        "# agents/faculty_agent.py",
        "from langchain.tools import tool",
        "from langchain.agents import create_react_agent, AgentExecutor",
        "from langchain import hub",
        "from agents.base_agent import BaseAgent, AgentInput, AgentOutput",
        "from services.db import get_class_data, save_content",
        "from services.llm_client import get_llm",
        "import json",
        "",
        "",
        "FACULTY_SYSTEM_PROMPT = '''",
        "You are NEXUS, an AI Lecturer Copilot.",
        "Help faculty plan, teach, assess, and analyze — saving them hours weekly.",
        "Always generate structured, curriculum-aligned, academically rigorous content.",
        "When generating assessments, include answer keys and marking schemes.",
        "'''",
        "",
        "",
        "@tool",
        "async def generate_lesson_plan(",
        "    topic: str, subject: str, duration_minutes: int,",
        "    level: str = 'undergraduate'",
        ") -> str:",
        "    '''Generate a structured lesson plan with objectives, activities, resources.'''",
        "    llm = get_llm()",
        "    prompt = f'''",
        "Create a detailed lesson plan:",
        "Topic: {topic} | Subject: {subject}",
        "Duration: {duration_minutes} mins | Level: {level}",
        "",
        "Include:",
        "1. Learning Objectives (3-5 measurable outcomes)",
        "2. Introduction / Hook (5 min)",
        "3. Core Content Breakdown with timings",
        "4. Activities & Exercises",
        "5. Assessment Questions",
        "6. Resources & References",
        "7. Homework Assignment",
        "'''",
        "    result = await llm.ainvoke(prompt)",
        "    await save_content('lesson_plan', topic, result.content)",
        "    return result.content",
        "",
        "",
        "@tool",
        "async def generate_mcq_questions(",
        "    topic: str, count: int = 10, difficulty: str = 'medium'",
        ") -> str:",
        "    '''Generate MCQ questions with answer keys for a given topic.'''",
        "    llm = get_llm()",
        "    prompt = f'''",
        "Generate {count} MCQ questions on: {topic}",
        "Difficulty: {difficulty}",
        "Format each as:",
        "Q[N]. [Question]",
        "A) [Option]  B) [Option]  C) [Option]  D) [Option]",
        "Answer: [Letter] | Explanation: [1-sentence explanation]",
        "'''",
        "    result = await llm.ainvoke(prompt)",
        "    return result.content",
        "",
        "",
        "@tool",
        "async def grade_assignment(",
        "    submission_text: str, rubric: str, max_marks: int = 100",
        ") -> str:",
        "    '''AI-grade a student submission against a rubric.'''",
        "    llm = get_llm()",
        "    prompt = f'''",
        "Grade this student submission against the rubric.",
        "Return a JSON object:",
        "{{",
        "  'total_score': <int out of {max_marks}>,",
        "  'breakdown': {{'criterion': score, ...}},",
        "  'strengths': ['...'],",
        "  'improvements': ['...'],",
        "  'feedback': '<2-3 sentence feedback for the student>'",
        "}}",
        "",
        "Rubric: {rubric}",
        "Submission: {submission_text}",
        "'''",
        "    result = await llm.ainvoke(prompt)",
        "    return result.content",
        "",
        "",
        "@tool",
        "async def get_at_risk_students(faculty_id: str, course_id: str) -> str:",
        "    '''Identify at-risk students in a course based on attendance & grades.'''",
        "    data = await get_class_data(faculty_id, course_id, 'at_risk')",
        "    if not data:",
        "        return 'No at-risk data available.'",
        "    students = data.get('students', [])",
        "    if not students:",
        "        return 'No at-risk students identified. Great work!'",
        "    lines = [f'At-Risk Students in {course_id}:']",
        "    for s in students:",
        "        lines.append(",
        "            f\"  {s['name']} | Attendance: {s['attendance']}% | \"",
        "            f\"Avg Score: {s['avg_score']}% | Risk: {s['risk_level']}\"",
        "        )",
        "    return '\\n'.join(lines)",
        "",
        "",
        "class FacultyAgent(BaseAgent):",
        "    def __init__(self):",
        "        super().__init__('FacultyAgent', FACULTY_SYSTEM_PROMPT)",
        "",
        "    def get_tools(self):",
        "        return [generate_lesson_plan, generate_mcq_questions,",
        "                grade_assignment, get_at_risk_students]",
        "",
        "    async def execute(self, inp: AgentInput) -> AgentOutput:",
        "        tools = self.get_tools()",
        "        prompt = hub.pull('hwchase17/react')",
        "        agent = create_react_agent(self.llm, tools, prompt)",
        "        executor = AgentExecutor(",
        "            agent=agent, tools=tools, max_iterations=5",
        "        )",
        "        enriched = f'Faculty ID: {inp.user_id}\\nRequest: {inp.message}'",
        "        result = await executor.ainvoke({'input': enriched})",
        "        return AgentOutput(",
        "            agent_name='FacultyAgent', response=result['output']",
        "        )",
    ]
    story.extend(code_block(faculty_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 6 — Admin Copilot
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("6", "USER STORY 3: AI ADMINISTRATIVE COPILOT",
        "Enrollment forecasting, dropout prediction, compliance, resource scheduling", MINT))
    story.append(sp(8))

    story.append(Paragraph("Admin Agent  (agents/admin_agent.py)", ST["h2"]))
    story.append(sp(4))
    admin_code = [
        "# agents/admin_agent.py",
        "from langchain.tools import tool",
        "from langchain.agents import create_react_agent, AgentExecutor",
        "from langchain import hub",
        "from agents.base_agent import BaseAgent, AgentInput, AgentOutput",
        "from services.db import get_institutional_data",
        "from agents.analytics_agent import predict_dropout_risk",
        "",
        "",
        "ADMIN_SYSTEM_PROMPT = '''",
        "You are NEXUS, an AI Administrative Copilot for university leadership.",
        "Help administrators with: institutional analytics, enrollment, finances,",
        "compliance, resource planning, and strategic decision-making.",
        "Always cite data sources and confidence levels in your responses.",
        "'''",
        "",
        "",
        "@tool",
        "async def get_enrollment_analytics(period: str = 'current_semester') -> str:",
        "    '''Fetch enrollment statistics, trends, and forecasts.'''",
        "    data = await get_institutional_data('enrollment', period)",
        "    return (",
        "        f\"Total Students: {data['total']}\\n\"",
        "        f\"New Enrollments: {data['new']}\\n\"",
        "        f\"By Department: {data['by_dept']}\\n\"",
        "        f\"YoY Change: {data['yoy_pct']}%\\n\"",
        "        f\"Forecast Next Sem: {data['forecast']}\"",
        "    )",
        "",
        "",
        "@tool",
        "async def get_financial_overview(period: str = 'current') -> str:",
        "    '''Get fee collection, revenue, outstanding amounts, budget utilization.'''",
        "    data = await get_institutional_data('finance', period)",
        "    return (",
        "        f\"Fee Collection: {data['collected']} / {data['target']} \"",
        "        f\"({data['pct']}%)\\n\"",
        "        f\"Outstanding: {data['outstanding']}\\n\"",
        "        f\"Budget Utilization: {data['budget_used']}%\"",
        "    )",
        "",
        "",
        "@tool",
        "async def get_dropout_risk_report(department: str = 'all') -> str:",
        "    '''Get dropout risk summary by department with intervention recommendations.'''",
        "    data = await get_institutional_data('students', department)",
        "    students = data.get('students', [])",
        "    high_risk = [s for s in students if s.get('risk_score', 0) > 0.7]",
        "    return (",
        "        f'High-Risk Students: {len(high_risk)}\\n'",
        "        f'Avg Risk Score: {sum(s[\"risk_score\"] for s in students)/max(len(students),1):.2f}\\n'",
        "        f'Recommended: Immediate intervention for top {min(10,len(high_risk))} students'",
        "    )",
        "",
        "",
        "@tool",
        "async def generate_compliance_report(standard: str = 'NAAC') -> str:",
        "    '''Generate accreditation/compliance readiness report.'''",
        "    data = await get_institutional_data('compliance', standard)",
        "    return (",
        "        f'Compliance Standard: {standard}\\n'",
        "        f'Overall Score: {data[\"score\"]}%\\n'",
        "        f'Critical Gaps: {data[\"gaps\"]}\\n'",
        "        f'Next Audit: {data[\"next_audit\"]}'",
        "    )",
        "",
        "",
        "class AdminAgent(BaseAgent):",
        "    def __init__(self):",
        "        super().__init__('AdminAgent', ADMIN_SYSTEM_PROMPT)",
        "",
        "    def get_tools(self):",
        "        return [get_enrollment_analytics, get_financial_overview,",
        "                get_dropout_risk_report, generate_compliance_report]",
        "",
        "    async def execute(self, inp: AgentInput) -> AgentOutput:",
        "        tools = self.get_tools()",
        "        prompt = hub.pull('hwchase17/react')",
        "        agent = create_react_agent(self.llm, tools, prompt)",
        "        executor = AgentExecutor(agent=agent, tools=tools, max_iterations=5)",
        "        result = await executor.ainvoke({'input': inp.message})",
        "        return AgentOutput(agent_name='AdminAgent', response=result['output'])",
    ]
    story.extend(code_block(admin_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 7 — Vector Search & RAG
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("7", "VECTOR SEARCH & RAG PIPELINE",
        "Pinecone vector store, embedding, semantic retrieval", TEAL))
    story.append(sp(8))

    rag_code = [
        "# services/vector_store.py",
        "from pinecone import Pinecone, ServerlessSpec",
        "from sentence_transformers import SentenceTransformer",
        "from typing import List, Dict, Optional",
        "import os, uuid",
        "",
        "",
        "class VectorStore:",
        "    _instance = None  # Singleton",
        "",
        "    def __new__(cls):",
        "        if cls._instance is None:",
        "            cls._instance = super().__new__(cls)",
        "            cls._instance._init()",
        "        return cls._instance",
        "",
        "    def _init(self):",
        "        self.pc = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))",
        "        self.index_name = os.getenv('PINECONE_INDEX_NAME', 'nexus-kb')",
        "        self.model = SentenceTransformer('all-MiniLM-L6-v2')",
        "        # Create index if it doesn't exist",
        "        if self.index_name not in self.pc.list_indexes().names():",
        "            self.pc.create_index(",
        "                name=self.index_name, dimension=384,",
        "                metric='cosine',",
        "                spec=ServerlessSpec(cloud='aws', region='us-east-1')",
        "            )",
        "        self.index = self.pc.Index(self.index_name)",
        "",
        "    def embed(self, texts: List[str]) -> List[List[float]]:",
        "        return self.model.encode(texts, show_progress_bar=False).tolist()",
        "",
        "    async def upsert_documents(",
        "        self, docs: List[Dict], namespace: str = 'default'",
        "    ) -> int:",
        "        '''Embed and upsert documents into Pinecone.'''",
        "        vectors = []",
        "        texts = [d['text'] for d in docs]",
        "        embeddings = self.embed(texts)",
        "        for doc, emb in zip(docs, embeddings):",
        "            vectors.append({",
        "                'id': doc.get('id', str(uuid.uuid4())),",
        "                'values': emb,",
        "                'metadata': {",
        "                    'text': doc['text'],",
        "                    'source': doc.get('source', ''),",
        "                    'category': doc.get('category', ''),",
        "                    'created_at': doc.get('created_at', ''),",
        "                }",
        "            })",
        "        self.index.upsert(vectors=vectors, namespace=namespace)",
        "        return len(vectors)",
        "",
        "    async def similarity_search(",
        "        self, query: str, top_k: int = 5,",
        "        namespace: str = 'default',",
        "        filter: Optional[Dict] = None",
        "    ) -> List[Dict]:",
        "        '''Search by semantic similarity, return top_k results.'''",
        "        query_emb = self.embed([query])[0]",
        "        results = self.index.query(",
        "            vector=query_emb, top_k=top_k,",
        "            namespace=namespace, include_metadata=True,",
        "            filter=filter",
        "        )",
        "        return [",
        "            {",
        "                'text': m['metadata'].get('text', ''),",
        "                'source': m['metadata'].get('source', ''),",
        "                'score': m['score']",
        "            }",
        "            for m in results['matches']",
        "        ]",
        "",
        "",
        "# ── RAG Pipeline ─────────────────────────────────────────────────",
        "class RAGPipeline:",
        "    def __init__(self):",
        "        self.vs = VectorStore()",
        "        self.llm = get_llm()",
        "",
        "    async def answer(",
        "        self, question: str, namespace: str = 'campus_kb',",
        "        top_k: int = 4",
        "    ) -> str:",
        "        # 1. Retrieve relevant documents",
        "        docs = await self.vs.similarity_search(question, top_k, namespace)",
        "        if not docs:",
        "            return 'No relevant information found.'",
        "        # 2. Build context",
        "        context = '\\n\\n---\\n\\n'.join(",
        "            f\"[Source: {d['source']}]\\n{d['text']}\" for d in docs",
        "        )",
        "        # 3. Generate grounded answer",
        "        prompt = (",
        "            f'Answer the question using ONLY the context below.\\n'",
        "            f'If the answer is not in the context, say so clearly.\\n\\n'",
        "            f'Context:\\n{context}\\n\\n'",
        "            f'Question: {question}'",
        "        )",
        "        result = await self.llm.ainvoke(prompt)",
        "        return result.content",
    ]
    story.extend(code_block(rag_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 8 — Predictive Analytics
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("8", "PREDICTIVE ANALYTICS — DROPOUT RISK MODEL",
        "ML model for early student intervention", RED))
    story.append(sp(8))

    analytics_code = [
        "# agents/analytics_agent.py",
        "import numpy as np",
        "import pandas as pd",
        "from sklearn.ensemble import GradientBoostingClassifier",
        "from sklearn.preprocessing import StandardScaler",
        "from sklearn.pipeline import Pipeline",
        "import joblib, os",
        "from agents.base_agent import BaseAgent, AgentInput, AgentOutput",
        "from services.db import get_student_features",
        "",
        "",
        "MODEL_PATH = 'models/dropout_model.pkl'",
        "",
        "FEATURE_COLUMNS = [",
        "    'attendance_pct',       # Overall attendance percentage",
        "    'avg_score',            # Average score across all subjects",
        "    'assignment_completion',# % of assignments submitted on time",
        "    'gpa_trend',            # GPA change (positive = improving)",
        "    'days_since_login',     # Engagement proxy",
        "    'fee_outstanding_pct',  # Financial stress indicator",
        "    'num_failed_subjects',  # Academic risk",
        "    'library_visits',       # Engagement",
        "    'support_tickets',      # Distress signal",
        "]",
        "",
        "",
        "class DropoutRiskModel:",
        "    def __init__(self):",
        "        if os.path.exists(MODEL_PATH):",
        "            self.pipeline = joblib.load(MODEL_PATH)",
        "        else:",
        "            self.pipeline = Pipeline([",
        "                ('scaler', StandardScaler()),",
        "                ('clf', GradientBoostingClassifier(",
        "                    n_estimators=200, learning_rate=0.05,",
        "                    max_depth=4, random_state=42",
        "                ))",
        "            ])",
        "",
        "    def train(self, df: pd.DataFrame):",
        "        '''Train on historical data. df must have FEATURE_COLUMNS + 'dropped_out'.'''",
        "        X = df[FEATURE_COLUMNS].fillna(0)",
        "        y = df['dropped_out'].astype(int)",
        "        self.pipeline.fit(X, y)",
        "        joblib.dump(self.pipeline, MODEL_PATH)",
        "        print(f'Model trained on {len(df)} records, saved to {MODEL_PATH}')",
        "",
        "    def predict(self, features: dict) -> dict:",
        "        '''Predict dropout risk for one student.'''",
        "        row = [features.get(col, 0) for col in FEATURE_COLUMNS]",
        "        X = np.array([row])",
        "        prob = self.pipeline.predict_proba(X)[0][1]",
        "        risk_level = (",
        "            'CRITICAL' if prob > 0.75 else",
        "            'HIGH'     if prob > 0.55 else",
        "            'MEDIUM'   if prob > 0.35 else 'LOW'",
        "        )",
        "        top_factors = self._top_risk_factors(features)",
        "        return {",
        "            'risk_score': round(prob, 3),",
        "            'risk_level': risk_level,",
        "            'top_factors': top_factors,",
        "            'recommendation': self._get_recommendation(risk_level, top_factors)",
        "        }",
        "",
        "    def _top_risk_factors(self, features: dict) -> list:",
        "        '''Identify top contributing risk factors.'''",
        "        factors = []",
        "        if features.get('attendance_pct', 100) < 65:",
        "            factors.append('Low attendance (<65%)')",
        "        if features.get('avg_score', 100) < 50:",
        "            factors.append('Low academic performance')",
        "        if features.get('fee_outstanding_pct', 0) > 60:",
        "            factors.append('Significant fee arrears')",
        "        if features.get('days_since_login', 0) > 14:",
        "            factors.append('Low platform engagement')",
        "        if features.get('assignment_completion', 100) < 60:",
        "            factors.append('High missed assignments')",
        "        return factors[:3]",
        "",
        "    def _get_recommendation(self, level: str, factors: list) -> str:",
        "        if level == 'CRITICAL':",
        "            return 'Immediate counselor intervention required. Contact student today.'",
        "        elif level == 'HIGH':",
        "            return 'Schedule academic support session within 3 days.'",
        "        elif level == 'MEDIUM':",
        "            return 'Send automated nudge + monitor for 2 weeks.'",
        "        return 'Continue monitoring. Student appears on track.'",
        "",
        "",
        "# Singleton model instance",
        "_model = DropoutRiskModel()",
        "",
        "",
        "async def predict_dropout_risk(student_id: str) -> str:",
        "    '''Tool: predict dropout risk for a specific student.'''",
        "    features = await get_student_features(student_id)",
        "    result = _model.predict(features)",
        "    return (",
        "        f\"Student: {student_id}\\n\"",
        "        f\"Risk Level: {result['risk_level']} ({result['risk_score']*100:.1f}%)\\n\"",
        "        f\"Top Factors: {', '.join(result['top_factors']) or 'None'}\\n\"",
        "        f\"Recommendation: {result['recommendation']}\"",
        "    )",
        "",
        "",
        "class AnalyticsAgent(BaseAgent):",
        "    def __init__(self):",
        "        super().__init__('AnalyticsAgent', 'You are a predictive analytics assistant.')",
        "",
        "    def get_tools(self): return [predict_dropout_risk]",
        "",
        "    async def execute(self, inp: AgentInput) -> AgentOutput:",
        "        result = await predict_dropout_risk(inp.user_id)",
        "        return AgentOutput(agent_name='AnalyticsAgent', response=result)",
    ]
    story.extend(code_block(analytics_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 9 — Multi-Agent Parallel Routing
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("9", "MULTI-AGENT ROUTING — PARALLEL EXECUTION",
        "Handle complex queries that span multiple agents simultaneously", PURPLE))
    story.append(sp(8))

    story.append(Paragraph(
        "Some queries require more than one agent — e.g., an administrator asking "
        "'Show me enrollment trends AND dropout risk by department.' This requires "
        "the Analytics Agent AND the Admin Agent in parallel. LangGraph handles this "
        "natively via branching edges.", ST["body"]))
    story.append(sp(8))

    parallel_code = [
        "# orchestrator/parallel_router.py",
        "# Extension of router.py for multi-agent parallel dispatch",
        "from langgraph.graph import StateGraph, END",
        "from typing import TypedDict, List",
        "import asyncio",
        "from agents.base_agent import AgentInput, AgentOutput",
        "",
        "",
        "MULTI_INTENT_MAP = {",
        "    # If BOTH intents are detected, dispatch to BOTH agents",
        "    ('admin_report', 'admin_predict'): ['admin', 'analytics'],",
        "    ('student_query', 'study_help'):    ['student'],",
        "    ('content_create', 'grading_feedback'): ['faculty'],",
        "}",
        "",
        "",
        "class ParallelNexusRouter:",
        "    '''",
        "    Handles queries that need multiple agents.",
        "    Dispatches asyncio.gather() for true parallel execution.",
        "    '''",
        "",
        "    def __init__(self, agents: dict, classifier):",
        "        self.agents = agents",
        "        self.classifier = classifier",
        "",
        "    async def run_parallel(",
        "        self, user_id: str, role: str, message: str, session_id: str = ''",
        "    ) -> str:",
        "        # Step 1: Detect multiple intents",
        "        agent_names = await self._detect_agents(message, role)",
        "",
        "        if len(agent_names) == 1:",
        "            # Single agent path",
        "            inp = AgentInput(user_id=user_id, role=role,",
        "                             message=message, session_id=session_id)",
        "            out = await self.agents[agent_names[0]].execute(inp)",
        "            return out.response",
        "",
        "        # Step 2: Parallel execution",
        "        tasks = []",
        "        for name in agent_names:",
        "            inp = AgentInput(user_id=user_id, role=role,",
        "                             message=message, session_id=session_id)",
        "            tasks.append(self.agents[name].execute(inp))",
        "",
        "        outputs: List[AgentOutput] = await asyncio.gather(*tasks,",
        "                                                           return_exceptions=False)",
        "",
        "        # Step 3: Synthesize",
        "        return await self._synthesize(outputs, message)",
        "",
        "    async def _detect_agents(self, message: str, role: str) -> List[str]:",
        "        '''Use LLM to detect which agents are needed.'''",
        "        from services.llm_client import get_llm",
        "        import json",
        "        llm = get_llm()",
        "        prompt = (",
        "            f'Which of these agents are needed to answer this query?\\n'",
        "            f'Agents: student, faculty, admin, search, analytics\\n'",
        "            f'Role: {role}\\nQuery: {message}\\n'",
        "            f'Return ONLY a JSON array, e.g. [\"admin\", \"analytics\"]'",
        "        )",
        "        result = await llm.ainvoke(prompt)",
        "        try:",
        "            agents = json.loads(result.content.strip())",
        "            valid = [a for a in agents if a in self.agents]",
        "            return valid if valid else ['search']",
        "        except Exception:",
        "            return ['search']",
        "",
        "    async def _synthesize(self, outputs: List[AgentOutput], query: str) -> str:",
        "        '''Merge multiple agent outputs into one coherent response.'''",
        "        from services.llm_client import get_llm",
        "        llm = get_llm()",
        "        sections = '\\n\\n'.join(",
        "            f'=== {o.agent_name} ===\\n{o.response}' for o in outputs",
        "        )",
        "        prompt = (",
        "            f'Combine these agent responses into one clear, well-structured answer.\\n'",
        "            f'Original question: {query}\\n\\n'",
        "            f'Agent responses:\\n{sections}'",
        "        )",
        "        result = await llm.ainvoke(prompt)",
        "        return result.content",
    ]
    story.extend(code_block(parallel_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 10 — FastAPI Backend
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("10", "API LAYER — FASTAPI BACKEND",
        "Production-ready REST API with auth, streaming, and health checks", ACCENT))
    story.append(sp(8))

    api_code = [
        "# api/main.py",
        "from fastapi import FastAPI, Depends, HTTPException, status",
        "from fastapi.middleware.cors import CORSMiddleware",
        "from fastapi.responses import StreamingResponse",
        "from pydantic import BaseModel",
        "from typing import Optional",
        "import asyncio, json, uvicorn",
        "from api.auth import verify_token, TokenPayload",
        "from orchestrator.router import NexusRouter",
        "from orchestrator.parallel_router import ParallelNexusRouter",
        "",
        "",
        "app = FastAPI(",
        "    title='NEXUS AI Platform API',",
        "    description='Unified AI Copilot for Higher Education',",
        "    version='1.0.0'",
        ")",
        "",
        "app.add_middleware(CORSMiddleware, allow_origins=['*'],",
        "    allow_credentials=True, allow_methods=['*'], allow_headers=['*'])",
        "",
        "router = NexusRouter()",
        "",
        "",
        "class ChatRequest(BaseModel):",
        "    message: str",
        "    session_id: Optional[str] = ''",
        "    stream: bool = False",
        "",
        "",
        "class ChatResponse(BaseModel):",
        "    response: str",
        "    agent_used: str",
        "    session_id: str",
        "",
        "",
        "@app.post('/api/v1/chat', response_model=ChatResponse)",
        "async def chat(",
        "    req: ChatRequest,",
        "    token: TokenPayload = Depends(verify_token)",
        "):",
        "    '''Main chat endpoint — routes to appropriate agent(s).'''",
        "    try:",
        "        response = await router.run(",
        "            user_id=token.user_id,",
        "            role=token.role,",
        "            message=req.message,",
        "            session_id=req.session_id or token.user_id",
        "        )",
        "        return ChatResponse(",
        "            response=response,",
        "            agent_used='auto-routed',",
        "            session_id=req.session_id or token.user_id",
        "        )",
        "    except Exception as e:",
        "        raise HTTPException(status_code=500, detail=str(e))",
        "",
        "",
        "@app.get('/api/v1/health')",
        "async def health_check():",
        "    return {'status': 'healthy', 'version': '1.0.0'}",
        "",
        "",
        "@app.get('/api/v1/student/{student_id}/dashboard')",
        "async def student_dashboard(",
        "    student_id: str,",
        "    token: TokenPayload = Depends(verify_token)",
        "):",
        "    '''Returns pre-computed dashboard data for student UI.'''",
        "    if token.user_id != student_id and token.role != 'admin':",
        "        raise HTTPException(status_code=403, detail='Access denied')",
        "    from services.db import get_student_data",
        "    data = await get_student_data(student_id, 'dashboard')",
        "    return data",
        "",
        "",
        "if __name__ == '__main__':",
        "    uvicorn.run('api.main:app', host='0.0.0.0', port=8000, reload=True)",
    ]
    story.extend(code_block(api_code, ST))
    story.append(sp(10))

    story.append(Paragraph("Auth Middleware  (api/auth.py)", ST["h2"]))
    story.append(sp(4))
    auth_code = [
        "# api/auth.py",
        "from fastapi import Depends, HTTPException, status",
        "from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials",
        "from jose import JWTError, jwt",
        "from pydantic import BaseModel",
        "import os",
        "",
        "security = HTTPBearer()",
        "SECRET = os.getenv('JWT_SECRET_KEY')",
        "ALGO   = os.getenv('JWT_ALGORITHM', 'HS256')",
        "",
        "",
        "class TokenPayload(BaseModel):",
        "    user_id: str",
        "    role: str   # student | faculty | admin",
        "    email: str",
        "",
        "",
        "async def verify_token(",
        "    cred: HTTPAuthorizationCredentials = Depends(security)",
        ") -> TokenPayload:",
        "    try:",
        "        payload = jwt.decode(cred.credentials, SECRET, algorithms=[ALGO])",
        "        return TokenPayload(",
        "            user_id=payload['sub'],",
        "            role=payload.get('role', 'student'),",
        "            email=payload.get('email', '')",
        "        )",
        "    except JWTError:",
        "        raise HTTPException(",
        "            status_code=status.HTTP_401_UNAUTHORIZED,",
        "            detail='Invalid or expired token'",
        "        )",
    ]
    story.extend(code_block(auth_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 12 — Docker Deployment
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("12", "DEPLOYMENT — DOCKER & KUBERNETES",
        "Containerize and deploy NEXUS to production", TEAL))
    story.append(sp(8))

    story.append(Paragraph("Dockerfile", ST["h2"]))
    story.append(sp(4))
    docker_code = [
        "# docker/Dockerfile",
        "FROM python:3.11-slim",
        "",
        "WORKDIR /app",
        "",
        "# Install system dependencies",
        "RUN apt-get update && apt-get install -y \\",
        "    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*",
        "",
        "# Install Python dependencies",
        "COPY requirements.txt .",
        "RUN pip install --no-cache-dir -r requirements.txt",
        "",
        "# Copy application code",
        "COPY . .",
        "",
        "# Create non-root user",
        "RUN useradd -m -u 1000 nexus && chown -R nexus:nexus /app",
        "USER nexus",
        "",
        "EXPOSE 8000",
        "CMD [\"uvicorn\", \"api.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]",
    ]
    story.extend(code_block(docker_code, ST))
    story.append(sp(10))

    story.append(Paragraph("docker-compose.yml", ST["h2"]))
    story.append(sp(4))
    compose_code = [
        "# docker/docker-compose.yml",
        "version: '3.9'",
        "",
        "services:",
        "  nexus-api:",
        "    build: .",
        "    ports: ['8000:8000']",
        "    env_file: .env",
        "    depends_on: [postgres, redis]",
        "    restart: unless-stopped",
        "",
        "  postgres:",
        "    image: postgres:16-alpine",
        "    environment:",
        "      POSTGRES_DB: nexus_db",
        "      POSTGRES_USER: nexus",
        "      POSTGRES_PASSWORD: ${DB_PASSWORD}",
        "    volumes: ['pgdata:/var/lib/postgresql/data']",
        "    ports: ['5432:5432']",
        "",
        "  redis:",
        "    image: redis:7-alpine",
        "    ports: ['6379:6379']",
        "    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru",
        "",
        "  celery-worker:",
        "    build: .",
        "    command: celery -A services.tasks worker --loglevel=info",
        "    env_file: .env",
        "    depends_on: [redis, postgres]",
        "",
        "volumes:",
        "  pgdata:",
    ]
    story.extend(code_block(compose_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 13 — Testing
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("13", "TESTING STRATEGY",
        "Unit tests, agent tests, integration tests", MINT))
    story.append(sp(8))

    test_code = [
        "# tests/test_router.py",
        "import pytest, asyncio",
        "from orchestrator.router import NexusRouter",
        "from orchestrator.intent_classifier import IntentClassifier, Intent",
        "",
        "",
        "@pytest.mark.asyncio",
        "async def test_student_intent_classified():",
        "    clf = IntentClassifier()",
        "    intent, conf, _ = await clf.classify('What is my attendance?', 'student')",
        "    assert intent == Intent.STUDENT_QUERY",
        "    assert conf > 0.7",
        "",
        "",
        "@pytest.mark.asyncio",
        "async def test_faculty_content_intent():",
        "    clf = IntentClassifier()",
        "    intent, conf, _ = await clf.classify(",
        "        'Generate 10 MCQs on Operating Systems', 'faculty'",
        "    )",
        "    assert intent == Intent.CONTENT_CREATE",
        "",
        "",
        "@pytest.mark.asyncio",
        "async def test_router_end_to_end(mocker):",
        "    # Mock LLM and DB calls",
        "    mocker.patch('services.db.get_student_data',",
        "                 return_value={'overall_pct': 82, 'by_subject': {}})",
        "    router = NexusRouter()",
        "    response = await router.run(",
        "        user_id='STU001', role='student',",
        "        message='What is my current attendance?'",
        "    )",
        "    assert response",
        "    assert isinstance(response, str)",
        "    assert len(response) > 10",
        "",
        "",
        "# tests/test_dropout_model.py",
        "import numpy as np",
        "from agents.analytics_agent import DropoutRiskModel",
        "",
        "",
        "def test_high_risk_prediction():",
        "    model = DropoutRiskModel()",
        "    # Simulate a high-risk student",
        "    features = {",
        "        'attendance_pct': 42, 'avg_score': 38,",
        "        'assignment_completion': 30, 'gpa_trend': -0.8,",
        "        'days_since_login': 21, 'fee_outstanding_pct': 80,",
        "        'num_failed_subjects': 3, 'library_visits': 0, 'support_tickets': 4",
        "    }",
        "    # Train with dummy data first if model not saved",
        "    result = model.predict(features)",
        "    assert result['risk_level'] in ['HIGH', 'CRITICAL']",
        "",
        "",
        "def test_low_risk_prediction():",
        "    model = DropoutRiskModel()",
        "    features = {",
        "        'attendance_pct': 92, 'avg_score': 85,",
        "        'assignment_completion': 95, 'gpa_trend': 0.3,",
        "        'days_since_login': 1, 'fee_outstanding_pct': 5,",
        "        'num_failed_subjects': 0, 'library_visits': 12, 'support_tickets': 0",
        "    }",
        "    result = model.predict(features)",
        "    assert result['risk_level'] == 'LOW'",
    ]
    story.extend(code_block(test_code, ST))
    story.append(PageBreak())

    # ══════════════════════════════════════════════════════════════════════════
    # SECTION 14 — Roadmap
    # ══════════════════════════════════════════════════════════════════════════
    story.append(SectionBanner("14", "IMPLEMENTATION ROADMAP & NEXT STEPS",
        "12-week phased delivery plan", ACCENT))
    story.append(sp(8))

    roadmap = [
        ["Phase", "Duration", "Deliverables", "Key Code Files"],
        ["1 — Foundation", "Weeks 1–3",
         "Repo setup, DB schema, Auth, Base Agent interface, Intent Classifier",
         "base_agent.py, auth.py, intent_classifier.py, db_models.py"],
        ["2 — Student Agent", "Weeks 4–5",
         "Student Agent + all tools, RAG pipeline, Vector store seeded with campus KB",
         "student_agent.py, vector_store.py, RAGPipeline"],
        ["3 — Faculty Agent", "Weeks 6–7",
         "Faculty Copilot with lesson gen, MCQ, grading tools, Faculty dashboard API",
         "faculty_agent.py, api/routes/faculty.py"],
        ["4 — Admin + Analytics", "Weeks 8–9",
         "Admin Agent, Dropout ML model, Predictive analytics, Admin dashboards",
         "admin_agent.py, analytics_agent.py, DropoutRiskModel"],
        ["5 — Orchestration", "Weeks 10–11",
         "LangGraph router, parallel dispatch, memory (Redis + Pinecone), full API",
         "router.py, parallel_router.py, memory.py"],
        ["6 — Deploy & Harden", "Week 12",
         "Docker, K8s configs, guardrails, load testing, monitoring, go-live",
         "Dockerfile, docker-compose.yml, guardrails.py"],
    ]

    tbl = Table(roadmap, colWidths=[2.8*cm, 2.2*cm, 6.0*cm, 5.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NAVY),
        ("TEXTCOLOR", (0,0), (-1,0), ACCENT),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 8),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [CARD_BG, HexColor("#0A1E35")]),
        ("TEXTCOLOR", (0,1), (0,-1), MINT),
        ("TEXTCOLOR", (1,1), (-1,-1), LIGHT),
        ("FONTNAME", (0,1), (0,-1), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 0.3, MUTED),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ALIGN", (0,0), (-1,-1), "LEFT"),
    ]))
    story.append(tbl)
    story.append(sp(12))

    story.append(Paragraph("Immediate First Steps (Day 1)", ST["h3"]))
    steps = [
        "git init nexus && cd nexus && python -m venv .venv && source .venv/bin/activate",
        "pip install -r requirements.txt",
        "cp .env.example .env  # Fill in GROQ_API_KEY, PINECONE_API_KEY, DATABASE_URL",
        "Create PostgreSQL schema: alembic init alembic && alembic revision --autogenerate && alembic upgrade head",
        "Test the intent classifier: python -c \"from orchestrator.intent_classifier import IntentClassifier; ...\"",
        "Seed the vector store with campus documents: python data/seed_data.py",
        "Start the API: uvicorn api.main:app --reload",
        "Test with curl: curl -X POST http://localhost:8000/api/v1/chat -H 'Authorization: Bearer ...' -d '{\"message\": \"What is my attendance?\"}'",
    ]
    for i, step in enumerate(steps, 1):
        story.append(Paragraph(f"<b>{i}.</b>  {step}", ST["bullet"]))

    story.append(sp(10))
    story.append(InfoBox("TECH STACK SUMMARY",
        "LangGraph (orchestration) · LangChain + Groq llama-3.3-70b (LLM) · "
        "Pinecone (vector DB) · FastAPI (API) · PostgreSQL + Redis (data) · "
        "scikit-learn (ML) · Docker + K8s (deploy) · Guardrails AI (safety)",
        ACCENT))
    story.append(sp(8))

    # ── Final page
    story.append(PageBreak())
    story.append(sp(60))
    story.append(ColorBar(ACCENT, 3))
    story.append(sp(20))
    story.append(Paragraph("Ready to Build NEXUS.", ST["cover_title"]))
    story.append(sp(8))
    story.append(Paragraph(
        "This guide contains everything you need — architecture, full Python code, "
        "deployment configs, and a clear 12-week roadmap.",
        ST["cover_sub"]))
    story.append(sp(20))
    story.append(Paragraph(
        "Software Resonance Group Inc.  ·  contact@srgtechinc.com  ·  srgtechinc.com",
        ST["cover_desc"]))

    # ── Build
    doc.build(story, onFirstPage=pt, onLaterPages=pt)
    print(f"PDF built: {output_path}")


if __name__ == "__main__":
    build_pdf("/Users/vikram/Desktop/NEXUS_Agentic_AI_Implementation_Guide.pdf")