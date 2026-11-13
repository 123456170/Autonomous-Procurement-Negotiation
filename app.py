"""
ACCORD·01 — Autonomous Procurement Negotiation Agent (live sandbox)

A self-running, interactive simulation of an agentic procurement system:
  • Sourcing & Supplier Discovery
  • Negotiation Strategy Engine (anchors, concessions, walk-aways)
  • Policy & Approval Guard (spend limits, vendor risk, compliance)
  • Contract Drafting & Handoff (human sign-off inbox)

No API key required. All vendors, prices and records are synthetic demo data.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""
from __future__ import annotations

import copy
import inspect
import math
import random
import time
from html import escape

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="ACCORD · Autonomous Procurement Negotiation",
    page_icon="🤝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Compatibility helpers (work across Streamlit sizing APIs)
# ---------------------------------------------------------------------------
def _size_kwargs(fn):
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        params = {}
    return {"width": "stretch"} if "width" in params else {"use_container_width": True}

BTN_W = _size_kwargs(st.button)
DL_W = _size_kwargs(st.download_button)
FIG_W = _size_kwargs(st.plotly_chart)
RERUN_FRAG = {"scope": "fragment"} if "scope" in inspect.signature(st.rerun).parameters else {}

def rerun_frag():
    st.rerun(**RERUN_FRAG)

def show_fig(fig, key):
    st.plotly_chart(fig, key=key, config={"displayModeBar": False}, **FIG_W)

# ---------------------------------------------------------------------------
# Palette & visual language
# ---------------------------------------------------------------------------
P = dict(bg="#F5F7FB", surf="#FFFFFF", line="#DDE3EF", txt="#1B2440", mut="#5B6B8C",
         cyan="#0D9488", violet="#4F46E5", green="#059669", amber="#D97706",
         rose="#E11D48", blue="#2563EB", magenta="#DB2777", gold="#B7791F")
SUP_COLORS = [P["cyan"], P["violet"], P["amber"], P["blue"], P["green"]]

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

/* ---------- base ---------- */
[data-testid="stApp"]{
  color:#1B2440;
  background:
    radial-gradient(1100px 750px at 88% -12%, rgba(79,70,229,.10), transparent 60%),
    radial-gradient(900px 700px at -8% 112%, rgba(13,148,136,.10), transparent 55%),
    radial-gradient(700px 500px at 55% 118%, rgba(124,58,237,.06), transparent 60%),
    repeating-linear-gradient(0deg, transparent 0 46px, rgba(79,70,229,.045) 46px 47px),
    repeating-linear-gradient(90deg, transparent 0 46px, rgba(79,70,229,.045) 46px 47px),
    #F5F7FB;
  background-size:160% 160%,160% 160%,160% 160%,auto,auto,auto;
  animation:drift 46s ease-in-out infinite alternate;
}
@keyframes drift{0%{background-position:0% 0%,100% 100%,50% 100%,0 0,0 0,0 0}
                 100%{background-position:100% 40%,0% 60%,20% 80%,0 0,0 0,0 0}}
[data-testid="stHeader"]{background:transparent}
[data-testid="stToolbar"]{display:none}
footer{display:none}
[data-testid="stHeaderActionElements"], a.anchor-link{display:none !important}
[data-testid="stMainBlockContainer"]{padding-top:1.1rem; padding-bottom:2.2rem; max-width:1520px}
h1,h2,h3,h4{font-family:'Space Grotesk',sans-serif !important; letter-spacing:.2px; color:#1B2440}
p,li,span,div{font-family:'Space Grotesk',sans-serif}
[data-testid="stCaptionContainer"], .stCaption{color:#5B6B8C}

/* ---------- scrollbars ---------- */
*::-webkit-scrollbar{width:10px;height:10px}
*::-webkit-scrollbar-track{background:#EEF1F8;border-radius:8px}
*::-webkit-scrollbar-thumb{background:linear-gradient(180deg,rgba(13,148,136,.55),rgba(79,70,229,.55));
  border-radius:8px;border:2px solid #EEF1F8}
*::-webkit-scrollbar-thumb:hover{background:linear-gradient(180deg,#0D9488,#4F46E5)}
*{scrollbar-width:thin;scrollbar-color:#C9D3E6 #EEF1F8}

/* ---------- sidebar ---------- */
[data-testid="stSidebar"]{background:linear-gradient(180deg,#EEF1F8,#E8ECF5);border-right:1px solid #E6EBF4}
[data-testid="stSidebar"] *{color:#26324F}
.brand{font-family:'Space Grotesk';font-weight:700;font-size:26px;letter-spacing:2px;line-height:1}
.brand em{font-style:normal;background:linear-gradient(90deg,#0D9488,#4F46E5);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.brand span{font-size:13px;color:#64738F;letter-spacing:1px}
.tagline{font-size:10px;letter-spacing:2.4px;text-transform:uppercase;color:#64738F;margin:4px 0 10px}
.side-h{margin:16px 0 6px;font-size:10.5px;letter-spacing:2.4px;text-transform:uppercase;color:#64738F;
  border-top:1px solid #E6EBF4;padding-top:12px}
.sandbox-chip{display:inline-block;font-family:'IBM Plex Mono';font-size:10px;letter-spacing:1.5px;
  color:#0D9488;border:1px solid rgba(13,148,136,.4);border-radius:999px;padding:3px 10px;
  background:rgba(13,148,136,.07);margin-bottom:6px}
.persona{font-size:11.5px;color:#5B6B8C;padding:3px 0;font-family:'IBM Plex Mono'}
.persona b{color:#26324F;font-weight:600}

/* ---------- buttons ---------- */
.stButton>button, [data-testid="stBaseButton-secondary"], [data-testid="baseButton-secondary"]{
  background:#FFFFFF !important;border:1px solid #D3DBEA !important;color:#26324F !important;
  border-radius:10px;font-family:'Space Grotesk';font-weight:600;font-size:13px;
  transition:all .16s ease}
.stButton>button:hover{border-color:#4F46E5 !important;color:#4F46E5 !important;transform:translateY(-1px);
  box-shadow:0 4px 16px rgba(79,70,229,.15)}
.stButton>button[kind="primary"], [data-testid="stBaseButton-primary"], [data-testid="baseButton-primary"]{
  background:linear-gradient(135deg,#0D9488,#4F46E5) !important;border:none !important;
  color:#FFFFFF !important;font-weight:700}
.stButton>button[kind="primary"]:hover, [data-testid="stBaseButton-primary"]:hover{
  filter:brightness(1.08);box-shadow:0 6px 20px rgba(79,70,229,.30);color:#FFFFFF !important}
.stButton>button:disabled{opacity:.35;transform:none;box-shadow:none}
[data-testid="stDownloadButton"] button{background:#FFFFFF;border:1px solid #D3DBEA;color:#26324F;
  border-radius:10px;font-weight:600;font-size:12.5px}
[data-testid="stDownloadButton"] button:hover{border-color:#059669;color:#059669}
.st-key-nav .stButton>button{border-radius:999px;padding:.32rem .85rem;font-size:12.5px}
.st-key-nav [data-testid="stHorizontalBlock"]{gap:6px}

/* ---------- inputs ---------- */
[data-baseweb="select"]>div, [data-baseweb="input"]{background:#FFFFFF !important;
  border-color:#D3DBEA !important;color:#1B2440 !important;border-radius:10px !important}
[data-baseweb="select"]>div:focus-within, [data-baseweb="input"]:focus-within{
  border-color:#0D9488 !important;box-shadow:0 0 0 2px rgba(13,148,136,.18) !important}
[data-baseweb="popover"] ul, [data-baseweb="menu"]{background:#FFFFFF !important;
  border:1px solid #D3DBEA !important}
[data-baseweb="menu"] li:hover{background:#EEF2FB !important}
[data-baseweb="slider"] div[style*="255, 75, 75"]{background:linear-gradient(90deg,#0D9488,#4F46E5) !important}
[role="slider"]{box-shadow:0 0 0 4px rgba(79,70,229,.18) !important}
[data-testid="stToggle"] div[style*="255, 75, 75"]{background:#0D9488 !important}
[data-testid="stWidgetLabel"] p{font-size:12.5px;color:#5B6B8C;font-weight:600;letter-spacing:.3px}

/* ---------- KPI cards ---------- */
.kgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin:10px 0 14px}
.kcard{box-shadow:0 1px 3px rgba(30,41,80,.06);background:linear-gradient(160deg,#FFFFFF,#F8FAFD);border:1px solid #DDE3EF;border-radius:14px;
  padding:13px 16px 12px;position:relative;overflow:hidden}
.kcard::before{content:"";position:absolute;top:0;left:0;height:3px;width:100%;
  background:linear-gradient(90deg,#0D9488,#4F46E5)}
.kcard.k-green::before{background:linear-gradient(90deg,#059669,#0D9488)}
.kcard.k-amber::before{background:linear-gradient(90deg,#D97706,#E11D48)}
.kcard.k-violet::before{background:linear-gradient(90deg,#4F46E5,#DB2777)}
.kcard.k-blue::before{background:linear-gradient(90deg,#2563EB,#059669)}
.klabel{font-size:10px;letter-spacing:1.8px;text-transform:uppercase;color:#64738F;font-weight:600}
.kval{font-family:'IBM Plex Mono';font-size:25px;font-weight:600;color:#1B2440;margin:3px 0 2px;line-height:1.1}
.ksub{font-size:11px;color:#5B6B8C;font-family:'IBM Plex Mono'}
.ksub b{color:#059669;font-weight:600}

/* ---------- status / pipeline ---------- */
.badge{display:inline-flex;align-items:center;gap:7px;font-family:'IBM Plex Mono';font-size:11px;
  letter-spacing:1.4px;border-radius:999px;padding:4px 12px;border:1px solid}
.badge.cyan{color:#0D9488;border-color:rgba(13,148,136,.45);background:rgba(13,148,136,.08)}
.badge.amber{color:#D97706;border-color:rgba(217,119,6,.45);background:rgba(217,119,6,.08)}
.badge.violet{color:#6D28D9;border-color:rgba(79,70,229,.45);background:rgba(79,70,229,.08)}
.badge.mut{color:#5B6B8C;border-color:#C9D3E6;background:#FFFFFF}
.dot{width:8px;height:8px;border-radius:50%;background:currentColor;animation:pulse 1.4s ease infinite}
@keyframes pulse{0%,100%{box-shadow:0 0 0 0 currentColor;opacity:1}50%{box-shadow:0 0 0 5px transparent;opacity:.55}}
.pipe{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 14px}
.pstep{font-family:'IBM Plex Mono';font-size:11px;letter-spacing:.8px;color:#64738F;
  border:1px solid #DDE3EF;border-radius:8px;padding:5px 12px;background:#F8FAFD}
.pstep.done{color:#059669;border-color:rgba(5,150,105,.4)}
.pstep.on{color:#FFFFFF;font-weight:600;background:linear-gradient(135deg,#0D9488,#4F46E5);
  border-color:transparent;box-shadow:0 4px 14px rgba(79,70,229,.30)}
.chips{font-family:'IBM Plex Mono';font-size:11px;color:#5B6B8C}
.chips .chip{margin-right:6px}

/* ---------- chips & bars ---------- */
.chip{display:inline-block;font-family:'IBM Plex Mono';font-size:10.5px;border-radius:6px;
  padding:2px 8px;border:1px solid #C9D3E6;color:#5B6B8C;background:#FFFFFF;white-space:nowrap}
.chip.ok{color:#059669;border-color:rgba(5,150,105,.4);background:rgba(5,150,105,.07)}
.chip.warn{color:#D97706;border-color:rgba(217,119,6,.4);background:rgba(217,119,6,.07)}
.chip.bad{color:#E11D48;border-color:rgba(225,29,72,.4);background:rgba(225,29,72,.07)}
.chip.info{color:#2563EB;border-color:rgba(37,99,235,.4);background:rgba(37,99,235,.07)}
.chip.hot{color:#0D9488;border-color:rgba(13,148,136,.4);background:rgba(13,148,136,.07)}
.chip.vio{color:#6D28D9;border-color:rgba(79,70,229,.4);background:rgba(79,70,229,.07)}
.bar{height:6px;border-radius:3px;background:#E2E8F3;min-width:70px;overflow:hidden}
.bar>i{display:block;height:100%;border-radius:3px;background:linear-gradient(90deg,#0D9488,#4F46E5)}

/* ---------- feed ---------- */
.feed{max-height:470px;overflow-y:auto;padding-right:6px}
.ev{display:flex;gap:9px;align-items:baseline;padding:7px 10px;border-left:3px solid #C9D3E6;
  background:rgba(255,255,255,.92);border-radius:8px;margin-bottom:6px;font-size:12.3px;line-height:1.45;
  animation:evin .35s ease}
@keyframes evin{from{opacity:0;transform:translateY(-5px)}to{opacity:1;transform:none}}
.ev-t{font-family:'IBM Plex Mono';font-size:10px;color:#64738F;min-width:56px}
.ev-k{font-family:'IBM Plex Mono';font-size:9.5px;font-weight:600;letter-spacing:1px;min-width:66px}
.ev-x{color:#3A4666}
.ev-PLAN{border-color:#4F46E5}.ev-PLAN .ev-k{color:#6D28D9}
.ev-ACT{border-color:#0D9488}.ev-ACT .ev-k{color:#0D9488}
.ev-OBS{border-color:#2563EB}.ev-OBS .ev-k{color:#2563EB}
.ev-REFLECT{border-color:#059669}.ev-REFLECT .ev-k{color:#059669}
.ev-GUARD{border-color:#D97706}.ev-GUARD .ev-k{color:#D97706}
.ev-BLOCK{border-color:#E11D48}.ev-BLOCK .ev-k{color:#E11D48}
.ev-CONTRACT{border-color:#B7791F}.ev-CONTRACT .ev-k{color:#B7791F}
.ev-HUMAN{border-color:#DB2777}.ev-HUMAN .ev-k{color:#DB2777}
.ev-AUTO{border-color:#2563EB}.ev-AUTO .ev-k{color:#2563EB}
.ev-SAVE{border-color:#059669}.ev-SAVE .ev-k{color:#059669}
.ev-SYS{border-color:#C9D3E6}.ev-SYS .ev-k{color:#5B6B8C}

/* ---------- tables ---------- */
.tblwrap{overflow:auto;max-height:430px;border:1px solid #DDE3EF;border-radius:12px;background:#F8FAFD}
.tblwrap table{width:100%;border-collapse:collapse;font-size:12.3px}
.tblwrap th{position:sticky;top:0;background:#EEF2F9;color:#64738F;text-transform:uppercase;
  font-size:10px;letter-spacing:1.6px;padding:10px 12px;text-align:left;z-index:2}
.tblwrap td{padding:9px 12px;border-top:1px solid #E6EBF4;color:#3A4666;font-family:'IBM Plex Mono';font-size:12px}
.tblwrap tr:hover td{background:#EEF2FB}
.tblwrap td.nm{font-family:'Space Grotesk';font-weight:600;color:#1B2440}

/* ---------- panels / cards ---------- */
.panel{background:linear-gradient(160deg,#FFFFFF,#F8FAFD);border:1px solid #DDE3EF;border-radius:14px;
  padding:16px 18px;margin-bottom:12px}
.panel h4{margin:0 0 8px;font-size:14px}
.panel .kv{display:flex;justify-content:space-between;font-size:12.5px;padding:4px 0;
  border-bottom:1px dashed #E6EBF4}
.panel .kv:last-child{border-bottom:none}
.panel .kv span{color:#5B6B8C}.panel .kv b{font-family:'IBM Plex Mono';color:#1B2440;font-weight:600}
.suprow{display:flex;gap:10px;flex-wrap:wrap;margin-top:10px}
.supcard{flex:1 1 170px;background:#F8FAFD;border:1px solid #DDE3EF;border-radius:12px;padding:11px 13px}
.supcard.lead{border-color:rgba(5,150,105,.5);box-shadow:0 2px 14px rgba(5,150,105,.14)}
.supname{font-size:12px;font-weight:600;display:flex;align-items:center;gap:7px}
.supdot{width:9px;height:9px;border-radius:50%;display:inline-block}
.supval{font-family:'IBM Plex Mono';font-size:19px;font-weight:600;margin:5px 0 2px}
.supterms{font-size:10.5px;color:#5B6B8C;font-family:'IBM Plex Mono';margin-top:5px;line-height:1.6}
.banner{border:1px solid rgba(217,119,6,.5);background:linear-gradient(90deg,rgba(217,119,6,.12),rgba(79,70,229,.10));
  border-radius:12px;padding:12px 16px;margin:8px 0 12px;display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.banner .b-t{font-weight:700;font-size:14px;color:#D97706}
.banner .b-x{font-size:12.5px;color:#3A4666}
.rec{border:1px solid rgba(5,150,105,.45);background:linear-gradient(90deg,rgba(5,150,105,.10),rgba(13,148,136,.08));
  border-radius:12px;padding:12px 16px;margin:10px 0;font-size:13px}
.rec b{color:#059669}
.hint{font-size:11.5px;color:#64738F;font-family:'IBM Plex Mono';margin-top:10px}
.foot{font-size:10.5px;color:#7A879F;font-family:'IBM Plex Mono';margin-top:22px;
  border-top:1px solid #E6EBF4;padding-top:10px;letter-spacing:.4px}
.dots::after{content:"…";animation:pulse 1.2s infinite}

/* ---------- contract paper ---------- */
.paper{background:#F6F1E6;color:#20283A;border-radius:6px;padding:34px 40px;position:relative;
  overflow:hidden;font-family:Georgia,'Times New Roman',serif;box-shadow:0 10px 32px rgba(30,41,80,.14);
  border:1px solid #E2D9C4;margin-top:8px}
.paper *{font-family:Georgia,'Times New Roman',serif;color:#20283A}
.paper h2{font-size:21px;margin:0 0 2px;letter-spacing:.5px;color:#161D2C !important}
.paper .p-sub{font-size:11.5px;color:#6B6350 !important;letter-spacing:1.5px;text-transform:uppercase}
.paper h3{font-size:13.5px;margin:18px 0 4px;text-transform:uppercase;letter-spacing:1px;
  border-bottom:1px solid #C9BFA8;padding-bottom:3px;color:#161D2C !important}
.paper p{font-size:13px;line-height:1.65;margin:4px 0}
.paper table{width:100%;border-collapse:collapse;margin:8px 0;font-size:12.5px}
.paper th,.paper td{border:1px solid #C9BFA8;padding:6px 10px;text-align:left}
.paper th{background:#EDE5D2;font-size:11px;text-transform:uppercase;letter-spacing:1px}
.paper .wm{position:absolute;top:38%;left:50%;transform:translate(-50%,-50%) rotate(-22deg);
  font-size:88px;font-weight:700;letter-spacing:14px;color:rgba(32,40,58,.06) !important;
  pointer-events:none;white-space:nowrap}
.stamp{display:inline-block;transform:rotate(-5deg);border:2.5px solid;border-radius:5px;
  padding:2px 12px;font-weight:700;letter-spacing:3px;font-size:13px;margin-left:10px}
.stamp.draft{color:#B45309 !important;border-color:#B45309}
.stamp.exec{color:#047857 !important;border-color:#047857}
.stamp.rej{color:#BE123C !important;border-color:#BE123C}
.stamp.rev{color:#1D4ED8 !important;border-color:#1D4ED8}
.sig-grid{display:flex;gap:16px;flex-wrap:wrap;margin-top:16px}
.sig{flex:1 1 170px;border:1px dashed #8B8268;border-radius:6px;padding:10px 12px;min-height:86px}
.sig .s-role{font-size:10px;text-transform:uppercase;letter-spacing:1.5px;color:#6B6350 !important}
.sig .s-name{font-size:15px;font-style:italic;margin-top:12px}
.sig .s-st{font-size:10.5px;font-family:'IBM Plex Mono',monospace !important;margin-top:6px}
.sig.signed{border-style:solid;border-color:#047857;background:rgba(4,120,87,.05)}
.sig.signed .s-st{color:#047857 !important}
.sig.pending .s-st{color:#B45309 !important}
.sig.agent{border-style:solid;border-color:#6D28D9;background:rgba(109,40,217,.05)}
.sig.agent .s-st{color:#6D28D9 !important}
.clausechips{margin:10px 0}

/* ---------- responsive & motion ---------- */
@media (max-width:900px){
  [data-testid="stHorizontalBlock"]{flex-wrap:wrap}
  [data-testid="column"]{min-width:270px;flex:1 1 270px}
  .paper{padding:22px 20px}
  .kval{font-size:21px}
}
@media (prefers-reduced-motion:reduce){
  *{animation:none !important;transition:none !important}
}
"""
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Seeded demo world (synthetic vendors, prices, policies)
# ---------------------------------------------------------------------------
AUTONOMY = ["L1 · Suggest only", "L2 · Act with approval", "L3 · Act & notify (auto-sign)"]
TERM_MODES = ["Price first", "Balanced", "Terms first"]
SIGNERS = {"Category Buyer": "L. Ortega", "Finance Controller": "D. Okafor", "Legal Counsel": "A. Novak"}
BUYER_CO = "Northwind Manufacturing GmbH"
MANUAL_HOURS = 96.0
TICK_MINUTES = 45

def _req(num, title, cat, item, qty, unit, warr, lead):
    return dict(num=num, id=f"REQ-{num}", title=title, cat=cat, item=item, qty=qty,
                base_unit=unit, base_total=unit * qty, budget=unit * qty * 1.02,
                need=dict(warr=warr, pay=30, lead=lead))

REQ_QUEUE = [
    _req(2417, "Engineering laptop refresh", "IT Hardware",
         '14" developer laptop · 32 GB / 1 TB', 120, 1480.0, 24, 21),
    _req(2422, "Q1 corrugated packaging program", "Packaging",
         "Double-wall carton 600×400 mm", 250000, 0.86, 12, 14),
    _req(2431, "EU regional freight program", "Logistics",
         "FTL lane contract · 12 months", 1, 342000.0, 12, 10),
]

def _sup(sid, name, src, lst, fmult, flex, quality, lead, risk, esg):
    return dict(id=sid, name=name, src=src, list=lst, fmult=fmult, flex=flex,
                quality=quality, lead=lead, risk=risk, esg=esg)

CATALOG = {
    "IT Hardware": [
        _sup("NVS", "Nordvik Systems", "Catalog · v2025.11", 1520.0, .80, .70, 91, 14, 18, 74),
        _sup("ALT", "Altura Distribution", "Past quotes · Q3 RFQ", 1465.0, .84, .50, 84, 10, 26, 61),
        _sup("CSC", "Cascade Compute", "Web scan · verified", 1580.0, .78, .85, 88, 18, 32, 82),
        _sup("HLX", "Helix IT Partners", "Catalog · v2025.11", 1440.0, .88, .35, 79, 9, 55, 58),
        _sup("BRT", "Brightline Devices", "Web scan · new vendor", 1395.0, .90, .30, 72, 25, 68, 44),
    ],
    "Packaging": [
        _sup("VRD", "Verdant Pack Co.", "Catalog · v2025.11", 0.92, .76, .80, 90, 12, 15, 91),
        _sup("CRF", "CorruFlex", "Past quotes · Q2 RFQ", 0.88, .82, .55, 86, 8, 22, 70),
        _sup("PKA", "PackAtlas", "Web scan · verified", 0.95, .79, .75, 83, 15, 30, 47),
        _sup("EMB", "EmberBox Industries", "Catalog · v2025.11", 0.84, .90, .30, 74, 20, 48, 52),
        _sup("KFT", "Kraft & Co.", "Web scan · new vendor", 0.90, .85, .45, 80, 11, 64, 63),
    ],
    "Logistics": [
        _sup("MRD", "Meridian Freight", "Past quotes · 2024 lanes", 358000.0, .80, .65, 89, 5, 20, 72),
        _sup("BRL", "BlueRail Logistics", "Catalog · v2025.11", 345000.0, .86, .40, 82, 7, 28, 85),
        _sup("SWH", "SwiftHaul", "Web scan · verified", 332000.0, .90, .30, 76, 6, 41, 45),
        _sup("CGN", "CargoNova", "Web scan · verified", 368000.0, .77, .85, 87, 9, 33, 68),
    ],
}

LEVERS = ["volume commitment", "12-month price lock", "competitive tension (alt bid on table)",
          "faster payment within policy", "consolidated award", "forecast visibility"]
REJECT_REASONS = ["savings below mandate for this cycle", "lead-time risk on primary lane",
                  "warranty terms weaker than incumbent", "budget phasing mismatch with Q1 plan"]

# ---------------------------------------------------------------------------
# Small utilities
# ---------------------------------------------------------------------------
def money(v, dec=None):
    if dec is None:
        dec = 2 if abs(v) < 10 else 0
    return f"${v:,.{dec}f}"

def udec(req):
    return 2 if req["base_unit"] < 10 else 0

def tplus(tick):
    m = tick * TICK_MINUTES
    return f"T+{m // 60:02d}:{m % 60:02d}"

def chip(txt, cls=""):
    return f"<span class='chip {cls}'>{txt}</span>"

def bar(v):
    v = max(0.0, min(100.0, v))
    return f"<div class='bar'><i style='width:{v:.0f}%'></i></div>"

def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))

def lead_score(lead):
    return clamp(100 - (lead - 5) * 4)

def qual_score(s):
    return .45 * s["quality"] + .25 * (100 - s["risk"]) + .15 * s["esg"] + .15 * lead_score(s["lead"])

def by_id(run, sid):
    return next(s for s in run["sups"] if s["id"] == sid)

def cfg():
    ss = st.session_state
    return dict(
        speed=float(ss.get("sb_speed", 1.2)),
        aggr=int(ss.get("sb_aggr", 62)),
        anchor=int(ss.get("sb_anchor", 14)),
        maxr=int(ss.get("sb_rounds", 7)),
        ceiling=int(ss.get("sb_ceiling", 96)),
        maxrisk=int(ss.get("sb_risk", 60)),
        autonomy=ss.get("sb_autonomy", AUTONOMY[1]),
        terms=ss.get("sb_terms", "Balanced"),
        autocont=bool(ss.get("sb_autocont", True)),
        verbose=bool(ss.get("sb_verbose", True)),
    )

def approval_roles(total):
    if total <= 50000:
        return ["Category Buyer"]
    if total <= 250000:
        return ["Category Buyer", "Finance Controller"]
    return ["Category Buyer", "Finance Controller", "Legal Counsel"]

def terms_value(req, s):
    t = s["terms"]; total = s["offer"] * req["qty"]; need = req["need"]["warr"]
    return total * (.004 * max(0, t["pay"] - 30) / 15
                    + .002 * max(0, t["warr"] - need) / 12
                    + .005 * max(0, t["lock"] - 6) / 6)

def terms_brief(s):
    t = s["terms"]
    txt = f"Net {t['pay']} · {t['warr']}mo · lock {t['lock']}mo"
    if t["prepay"] > 0:
        txt += f" · prepay {t['prepay']}%"
    return txt

# ---------------------------------------------------------------------------
# Simulation engine
# ---------------------------------------------------------------------------
def ev(sim, kind, text):
    sim["events"].append(dict(tick=sim["tick"], kind=kind, text=text))
    if len(sim["events"]) > 260:
        sim["events"] = sim["events"][-260:]

def new_run(req, sim):
    rng = sim["rng"]; sups = []
    for s in CATALOG[req["cat"]]:
        d = dict(s)
        d["list"] = round(s["list"] * rng.uniform(.97, 1.03), udec(req) or 0)
        d["floor"] = d["list"] * s["fmult"]
        d["offer"] = d["list"]
        d["hist"] = []
        d["terms"] = dict(pay=30, warr=req["need"]["warr"], lock=6, prepay=0, lead=s["lead"])
        d["pay15"] = False
        sups.append(d)
    return dict(req=req, sups=sups, phase="sourcing", pt=0, round=0, extra=0, short=[],
                best=None, checks=[], contract=None, start=sim["tick"],
                scanned=120 + rng.randint(0, 60), rej=0, chg=0, terms_push=False, tok=0)

def build_scenario(seed):
    sim = dict(seed=seed, rng=random.Random(seed), tick=0, running=True, last_wall=0.0,
               req_index=0, next_num=2438, events=[], ledger=[], contracts={}, nav=0,
               weights=dict(price=35, quality=20, lead=10, risk=15, esg=5, terms=15),
               ui=dict(q="", minq=0, hide_blocked=False, csel=None),
               counters=dict(checks=0, blocked=0, committed=0, accepted=0, rejected=0, escalated=0),
               realized=0.0, base_signed=0.0, hours=[], undo=None, hold=False,
               celebrated=False, cost=0.0)
    sim["run"] = new_run(REQ_QUEUE[0], sim)
    return sim

def synth_req(sim):
    base = REQ_QUEUE[sim["req_index"] % len(REQ_QUEUE)]
    rng = sim["rng"]
    qty = base["qty"] if base["qty"] == 1 else int(round(base["qty"] * rng.uniform(.85, 1.15) / 10) * 10)
    unit = round(base["base_unit"] * rng.uniform(.95, 1.05), udec(base))
    num = sim["next_num"]; sim["next_num"] += 1
    cyc = sim["req_index"] // len(REQ_QUEUE) + 1
    return _req(num, f"{base['title']} · cycle {cyc}", base["cat"], base["item"], qty, unit,
                base["need"]["warr"], base["need"]["lead"])

def eligible(s, req, c):
    return s["risk"] <= c["maxrisk"] and s["offer"] <= req["base_unit"] * c["ceiling"] / 100

def score_rows(run, sim):
    c = cfg(); req = run["req"]; w = sim["weights"]; wsum = max(1, sum(w.values()))
    rows = []
    for sid in run["short"]:
        s = by_id(run, sid)
        sub = dict(
            price=clamp((req["base_unit"] - s["offer"]) / (.25 * req["base_unit"]) * 100),
            quality=s["quality"], lead=lead_score(s["terms"]["lead"]),
            risk=100 - s["risk"], esg=s["esg"],
            terms=clamp(40 + (s["terms"]["pay"] - 30) / 15 * 18
                        + (s["terms"]["warr"] - req["need"]["warr"]) / 12 * 14
                        + (s["terms"]["lock"] - 6) / 6 * 10
                        + (6 if s["terms"]["prepay"] == 0 else 0)))
        total = sum(w[k] * sub[k] for k in w) / wsum
        rows.append(dict(s=s, sub=sub, total=total, ok=eligible(s, req, c),
                         sav=req["base_total"] - s["offer"] * req["qty"],
                         pct=(1 - s["offer"] / req["base_unit"]) * 100))
    rows.sort(key=lambda r: r["total"], reverse=True)
    return rows

def guard_rows(run, s, c):
    req = run["req"]; t = s["terms"]
    ceil_u = req["base_unit"] * c["ceiling"] / 100
    total = s["offer"] * req["qty"]
    alts = max(0, len(run["short"]) - 1)
    defs = [
        ("PROC-02", "Unit price ceiling", f"≤ {money(ceil_u, udec(req))}", money(s["offer"], udec(req)), s["offer"] <= ceil_u, "block"),
        ("PROC-05", "Requisition budget", f"≤ {money(req['budget'])}", money(total), total <= req["budget"], "block"),
        ("FIN-03", "Payment terms floor", "≥ Net 30", f"Net {t['pay']}", t["pay"] >= 30, "block"),
        ("FIN-07", "Prepayment cap", "≤ 30%", f"{t['prepay']}%", t["prepay"] <= 30, "block"),
        ("RISK-11", "Vendor risk score", f"≤ {c['maxrisk']}", str(s["risk"]), s["risk"] <= c["maxrisk"], "block"),
        ("PROC-11", "Warranty / SLA term", f"≥ {req['need']['warr']} mo", f"{t['warr']} mo", t["warr"] >= req["need"]["warr"], "block"),
        ("ESG-04", "ESG floor (soft)", "≥ 50", str(s["esg"]), s["esg"] >= 50, "warn"),
        ("PROC-09", "Dual-source coverage", "≥ 1 alternate", str(alts), alts >= 1, "info"),
    ]
    return [dict(code=a, name=b, limit=cc, actual=d, ok=e, sev=f, fixed=False) for a, b, cc, d, e, f in defs]

def build_clauses(req, s):
    t = s["terms"]; total = s["offer"] * req["qty"]
    wlabel = "Warranty" if req["cat"] == "IT Hardware" else ("Quality guarantee" if req["cat"] == "Packaging" else "Service level term")
    sla = ("Delivery within the agreed lead time; service credits of 2% of order value per week late, capped at 10%."
           if req["cat"] != "Logistics" else
           "On-time performance ≥ 96% per lane per month; service credits of 1.5% of monthly fees per point below target.")
    cl = [
        ("CL-01", "Scope & Deliverables", f"Supplier shall provide {req['item']} — {req['qty']:,} unit(s) — per specification {req['id']} and the agreed acceptance criteria."),
        ("CL-03", "Pricing & Price Lock", f"Fixed unit price {money(s['offer'], udec(req))}; contract value {money(total)}. Prices locked for {t['lock']} months; no escalation, surcharges or indexation during the lock."),
        ("CL-04", "Payment", f"Net {t['pay']} days from receipt of a valid invoice. Prepayment {t['prepay']}%. Invoices referenced to {req['id']} and the purchase order."),
        ("CL-05", "Delivery & Service Levels", f"Committed lead time ≤ {t['lead']} days. {sla}"),
        ("CL-06", wlabel, f"{wlabel} of {t['warr']} months from acceptance. Defects remedied by replacement within 10 business days at Supplier's cost."),
        ("CL-07", "Limitation of Liability", "Aggregate liability capped at 12 months of fees paid or payable. Carve-outs: confidentiality breach, IP infringement, wilful misconduct."),
        ("CL-08", "Termination", "Buyer may terminate for convenience on 30 days' written notice; for cause immediately upon material breach uncured for 10 business days."),
        ("CL-09", "Confidentiality", "Mutual confidentiality of pricing, volumes and specifications; obligations survive 3 years after expiry or termination."),
        ("CL-12", "Compliance & Conduct", "Anti-bribery, sanctions and export compliance; adherence to Buyer's Supplier Code of Conduct; annual audit rights on 10 days' notice."),
    ]
    if req["cat"] == "IT Hardware":
        cl.append(("CL-14", "Data Protection", "Devices shipped with no residual data; DPA executed where personal data is processed; secure logistics chain of custody."))
    return [dict(code=a, title=b, body=cc) for a, b, cc in cl]

def assemble_contract(sim, run, s):
    req = run["req"]; total = s["offer"] * req["qty"]
    sav = req["base_total"] - total
    roles = approval_roles(total)
    sigs = [dict(role="ACCORD Agent", name="ACCORD·01", status="drafted", at=sim["tick"])]
    sigs += [dict(role=r, name=SIGNERS[r], status="pending", at=None) for r in roles]
    return dict(id=f"PA-{req['num']}", req=req["id"], title=req["title"], item=req["item"],
                supplier=s["name"], buyer=BUYER_CO, unit=s["offer"], qty=req["qty"],
                total=total, baseline=req["base_total"], sav=sav,
                pct=sav / req["base_total"] * 100, terms=dict(s["terms"]),
                clauses=build_clauses(req, s), sigs=sigs, status="pending",
                tick=sim["tick"], risk=s["risk"], esg=s["esg"], udec=udec(req))

def snapshot(sim):
    sim["undo"] = copy.deepcopy({k: v for k, v in sim.items() if k != "undo"})

def really_advance(sim):
    sim["req_index"] += 1
    i = sim["req_index"]
    req = REQ_QUEUE[i] if i < len(REQ_QUEUE) else synth_req(sim)
    sim["run"] = new_run(req, sim)

def advance(sim):
    if cfg()["autocont"]:
        really_advance(sim)
    else:
        sim["hold"] = True
        ev(sim, "SYS", "Auto-continue is off — next requisition queued. Press 'Next requisition' to proceed.")

def escalate(sim, reason):
    run = sim["run"]; req = run["req"]
    sim["counters"]["escalated"] += 1
    ev(sim, "BLOCK", f"⛔ Escalated {req['id']}: {reason}. Logged for buyer review — no commitment made.")
    sim["ledger"].append(dict(cid="—", req=req["id"], title=req["title"], supplier="—",
                              total=0.0, sav=0.0, pct=0.0,
                              hours=(sim["tick"] - run["start"]) * TICK_MINUTES / 60,
                              status="escalated"))
    st.toast(f"⚠️ {req['id']} escalated — {reason}", icon="🛡️")
    advance(sim)

def finalize(sim):
    run = sim["run"]; req = run["req"]; c = run["contract"]
    c["status"] = "executed"
    for sg in c["sigs"]:
        if sg["status"] == "pending":
            sg["status"] = "signed"; sg["at"] = sim["tick"]
    hours = (sim["tick"] - run["start"]) * TICK_MINUTES / 60
    sim["counters"]["accepted"] += 1
    sim["realized"] += c["sav"]; sim["base_signed"] += c["baseline"]
    sim["hours"].append(hours)
    sim["ledger"].append(dict(cid=c["id"], req=req["id"], title=req["title"], supplier=c["supplier"],
                              total=c["total"], sav=c["sav"], pct=c["pct"], hours=hours, status="executed"))
    if len(sim["ledger"]) > 30:
        sim["ledger"] = sim["ledger"][-30:]
    ev(sim, "SAVE", f"✅ {c['id']} EXECUTED · {c['supplier']} · savings {money(c['sav'])} ({c['pct']:.1f}%) vs baseline · cycle {hours:.1f}h vs {MANUAL_HOURS:.0f}h manual.")
    st.toast(f"✅ {c['id']} executed — {money(c['sav'])} savings locked", icon="🤝")
    if not sim["celebrated"]:
        sim["celebrated"] = True
        try:
            st.balloons()
        except Exception:
            pass
    advance(sim)

def sign_action(sim):
    c = sim["run"]["contract"]
    if not c or c["status"] != "pending":
        return
    snapshot(sim)
    nxt = next((sg for sg in c["sigs"] if sg["status"] == "pending"), None)
    if nxt:
        nxt["status"] = "signed"; nxt["at"] = sim["tick"]
        ev(sim, "HUMAN", f"✍️ {nxt['role']} — {nxt['name']} signed {c['id']}.")
        st.toast(f"✍️ Signed as {nxt['role']}", icon="🖊️")
    if not any(sg["status"] == "pending" for sg in c["sigs"]):
        finalize(sim)
    rerun_frag()

def reject_action(sim):
    run = sim["run"]; c = run["contract"]
    if not c or c["status"] != "pending":
        return
    snapshot(sim)
    reason = sim["rng"].choice(REJECT_REASONS)
    sim["counters"]["rejected"] += 1; run["rej"] += 1
    c["status"] = "rejected"
    ev(sim, "HUMAN", f"✕ Buyer rejected {c['id']} — “{reason}”. Agent re-planning.")
    st.toast(f"✕ {c['id']} rejected — agent re-negotiating", icon="↩️")
    if run["rej"] >= 2:
        escalate(sim, "buyer rejected twice — sourcing restart required")
    else:
        run["phase"] = "negotiate"; run["extra"] += 2; run["terms_push"] = True
        ev(sim, "REFLECT", "Re-anchor −2 pts · +2 rounds · shift leverage to payment terms and price lock.")
    rerun_frag()

def changes_action(sim):
    run = sim["run"]; c = run["contract"]
    if not c or c["status"] != "pending":
        return
    snapshot(sim)
    run["chg"] += 1; c["status"] = "revising"
    run["phase"] = "negotiate"; run["extra"] += 2; run["terms_push"] = True
    ev(sim, "HUMAN", f"↩ Changes requested on {c['id']}: Net 60 + 12-month lock. Returning to negotiation.")
    ev(sim, "PLAN", "Revised mandate: prioritise terms over price for remaining rounds; re-draft after guard.")
    st.toast("↩ Change request sent to agent", icon="📨")
    rerun_frag()

def undo_action(sim):
    u = sim.get("undo")
    if not u:
        return
    sim.clear(); sim.update(u); sim["undo"] = None
    st.toast("↶ Last decision reverted", icon="↶")
    rerun_frag()

def terms_step(s, r, mode, push, need):
    t = s["terms"]
    fast = push or mode == "Terms first"
    if r >= 2:
        t["lock"] = 12
    if (fast and r >= 2) or (mode == "Balanced" and r >= 3) or (mode == "Price first" and r >= 6):
        t["pay"] = max(t["pay"], 45)
    if (fast and r >= 4) or (mode == "Balanced" and r >= 5):
        t["pay"] = max(t["pay"], 60)
    if r >= 4:
        t["warr"] = min(need + 12, t["warr"] + 12)
    if r >= 5:
        t["lead"] = max(3, s["lead"] - 2)

def do_tick(sim):
    if sim["hold"]:
        return
    c = cfg(); rng = sim["rng"]
    sim["tick"] += 1
    run = sim["run"]; req = run["req"]
    step_tok = rng.randint(280, 900)
    run["tok"] += step_tok
    sim["cost"] += rng.uniform(.004, .011)
    if run["tok"] > 40000:
        escalate(sim, "agent token budget exceeded (40k)")
        return
    ceil_u = req["base_unit"] * c["ceiling"] / 100
    anchor_p = req["base_unit"] * (1 - c["anchor"] / 100)
    target = req["base_unit"] * (1 - c["anchor"] * .7 / 100)
    phase = run["phase"]

    # ---------------- SOURCING ----------------
    if phase == "sourcing":
        if run["pt"] == 0:
            ev(sim, "SYS", f"📥 {req['id']} released · {req['item']} · {req['qty']:,} unit(s) · baseline {money(req['base_total'])}.")
            ev(sim, "PLAN", f"Plan: discover → qualify → anchor −{c['anchor']}% → ≤{c['maxr']} rounds → guard → draft. Ceiling {money(ceil_u, udec(req))}/unit · budget {money(req['budget'])}.")
            ev(sim, "ACT", f"Scanning supplier catalog v2025.11, historical RFQs and web index… {run['scanned']} vendors matched “{req['cat']}”.")
        elif run["pt"] == 1:
            ok = [s for s in run["sups"] if s["risk"] <= c["maxrisk"]]
            ev(sim, "OBS", f"Qualification: {len(ok)} of {run['scanned']} pass certifications, capacity and risk pre-screen (≤ {c['maxrisk']}).")
        else:
            ok = sorted([s for s in run["sups"] if s["risk"] <= c["maxrisk"]], key=qual_score, reverse=True)
            short = ok[:3]
            run["short"] = [s["id"] for s in short]
            for s in short:
                s["hist"] = [s["list"]]
                ev(sim, "ACT", f"Shortlisted {s['name']} — qual {qual_score(s):.0f}, risk {s['risk']}, lead {s['lead']}d · {s['src']}.")
            blocked = [s["name"] for s in run["sups"] if s["risk"] > c["maxrisk"]]
            if blocked:
                ev(sim, "REFLECT", f"Excluded on vendor risk: {', '.join(blocked)} (RISK-11 > {c['maxrisk']}). Kept on watchlist.")
            culprit = rng.choice(short)
            culprit["terms"]["prepay"] = rng.choice([40, 50, 60])
            others = [s for s in short if s["id"] != culprit["id"]]
            if others:
                p15 = rng.choice(others); p15["pay15"] = True; p15["terms"]["pay"] = 15
            ev(sim, "PLAN", f"Anchor {money(anchor_p, udec(req))}/unit (−{c['anchor']}% vs baseline). Target {money(target, udec(req))} · walk-away {money(ceil_u, udec(req))}.")
            run["phase"] = "negotiate"; run["pt"] = -1
        run["pt"] += 1

    # ---------------- NEGOTIATION ----------------
    elif phase == "negotiate":
        run["round"] += 1; r = run["round"]
        mode = "Terms first" if run["terms_push"] else c["terms"]
        for sid in run["short"]:
            s = by_id(run, sid)
            k = (.30 + s["flex"] * .30 + c["aggr"] * .0035) * (.9 if mode == "Terms first" else 1)
            raw = s["floor"] + (s["list"] - s["floor"]) * math.exp(-k * r)
            raw += raw * rng.uniform(-.004, .006)
            s["offer"] = round(min(s["offer"], max(s["floor"] * 1.002, raw)), udec(req) or 2)
            s["hist"].append(s["offer"])
            terms_step(s, r, mode, run["terms_push"], req["need"]["warr"])
            if s["pay15"] and r == 2:
                s["terms"]["pay"] = 30; s["pay15"] = False
                sim["counters"]["blocked"] += 1
                ev(sim, "BLOCK", f"FIN-03 blocked Net 15 from {s['name']} → countered Net 30 (policy floor). Supplier accepted.")
        focus = by_id(run, run["short"][r % len(run["short"])])
        counter = max(target * .985, focus["offer"] * (1 - .018 - c["aggr"] * .0005))
        lever = rng.choice(LEVERS)
        ev(sim, "ACT", f"R{r} · Counter {money(counter, udec(req))} to {focus['name']} — lever: {lever}.")
        below = (1 - focus["offer"] / req["base_unit"]) * 100
        ev(sim, "OBS", f"{focus['name']} → {money(focus['offer'], udec(req))} ({below:.1f}% below baseline) · {terms_brief(focus)}.")
        if r % 3 == 0:
            board = " · ".join(f"{by_id(run, i)['name'].split()[0]} {money(by_id(run, i)['offer'], udec(req))}" for i in run["short"])
            ev(sim, "OBS", f"Board: {board}.")
        if r % 2 == 0:
            best = min((by_id(run, i) for i in run["short"]), key=lambda s: s["offer"])
            gap = (best["offer"] - target) / target * 100
            delta = (best["hist"][-2] - best["hist"][-1]) / best["hist"][-2] * 100 if len(best["hist"]) >= 2 else 0
            if gap > 3:
                alt = max((by_id(run, i) for i in run["short"]), key=lambda s: s["offer"])
                ev(sim, "REFLECT", f"Gap {gap:.1f}% to target · {best['name']} conceding {delta:.1f}%/round — raise competitive tension, cite {alt['name']} at {money(alt['offer'], udec(req))}.")
            else:
                ev(sim, "REFLECT", f"Within {max(0.0, gap):.1f}% of target · concession rate {delta:.1f}%/round — hold anchor, trade payment terms for final basis points.")
        cap = c["maxr"] + run["extra"]
        best_offer = min(by_id(run, i)["offer"] for i in run["short"])
        exhausted = all(by_id(run, i)["offer"] <= by_id(run, i)["floor"] * 1.012 for i in run["short"])
        if r >= cap or (r >= 4 and best_offer <= target) or exhausted:
            ev(sim, "REFLECT", "Concession curve flattening (Δ < 0.3%/round) or mandate met — locking offers for scoring.")
            run["phase"] = "evaluate"

    # ---------------- EVALUATE ----------------
    elif phase == "evaluate":
        rows = score_rows(run, sim)
        rank = " · ".join(f"{i + 1}. {r['s']['name']} {r['total']:.1f}" for i, r in enumerate(rows))
        ev(sim, "OBS", f"Scorecard → {rank}.")
        okrows = [r for r in rows if r["ok"]]
        if not okrows:
            escalate(sim, f"no offer under the {c['ceiling']}% policy ceiling — buyer intervention required")
            return
        best = okrows[0]
        run["best"] = best["s"]["id"]
        ev(sim, "PLAN", f"Selected {best['s']['name']} at {money(best['s']['offer'], udec(req))} — {best['pct']:.1f}% below baseline. Routing to Policy & Approval Guard.")
        run["phase"] = "guard"

    # ---------------- POLICY GUARD ----------------
    elif phase == "guard":
        s = by_id(run, run["best"])
        rows = guard_rows(run, s, c)
        fixed = 0
        for row in rows:
            if not row["ok"] and row["sev"] == "block" and row["code"] in ("FIN-03", "FIN-07", "PROC-11"):
                if row["code"] == "FIN-03":
                    s["terms"]["pay"] = 30
                elif row["code"] == "FIN-07":
                    s["terms"]["prepay"] = 0
                else:
                    s["terms"]["warr"] = req["need"]["warr"]
                row["fixed"] = True; fixed += 1
                sim["counters"]["blocked"] += 1
                ev(sim, "BLOCK", f"{row['code']} blocked {row['name'].lower()} ({row['actual']}) on {s['name']} → auto-remediated to {row['limit']}.")
        rows = guard_rows(run, s, c)
        hard = [r for r in rows if not r["ok"] and r["sev"] == "block"]
        if hard:
            okrows = [r for r in score_rows(run, sim) if r["ok"] and r["s"]["id"] != s["id"]]
            if not okrows:
                escalate(sim, f"{hard[0]['code']} breach with no compliant alternate")
                return
            s = okrows[0]["s"]; run["best"] = s["id"]
            ev(sim, "GUARD", f"Best offer breached {hard[0]['code']} → fell back to {s['name']} at {money(s['offer'], udec(req))}.")
            rows = guard_rows(run, s, c)
        warns = sum(1 for r in rows if not r["ok"] and r["sev"] == "warn")
        passed = sum(1 for r in rows if r["ok"])
        sim["counters"]["checks"] += len(rows)
        run["checks"] = rows
        for r in rows:
            if r["code"] in ("FIN-03", "FIN-07", "PROC-11") and fixed and r["ok"]:
                pass
        ev(sim, "GUARD", f"Guard sweep · {s['name']}: {passed}/{len(rows)} clear · {fixed} remediated · {warns} warning(s). Committed violations: 0.")
        run["phase"] = "draft"

    # ---------------- CONTRACT DRAFT ----------------
    elif phase == "draft":
        s = by_id(run, run["best"])
        cts = assemble_contract(sim, run, s)
        run["contract"] = cts
        sim["contracts"][cts["id"]] = cts
        roles = [sg["role"] for sg in cts["sigs"] if sg["role"] != "ACCORD Agent"]
        ev(sim, "CONTRACT", f"📄 {cts['id']}: assembled {len(cts['clauses'])} clauses from library v3.2 — liability cap CL-07, service credits CL-05, termination 30d CL-08.")
        ev(sim, "CONTRACT", f"Pricing schedule locked: {money(cts['unit'], udec(req))} × {cts['qty']:,} = {money(cts['total'])} · lock {cts['terms']['lock']}mo · savings {money(cts['sav'])} ({cts['pct']:.1f}%).")
        ev(sim, "CONTRACT", f"Routed per approval matrix AM-2: {', '.join(roles)} (total {money(cts['total'])}).")
        if c["autonomy"].startswith("L3") and cts["pct"] >= 8:
            ev(sim, "AUTO", f"L3 autonomy active — auto-sign scheduled (within policy, savings {cts['pct']:.1f}% ≥ 8%).")
        else:
            ev(sim, "HUMAN", f"🛑 Authority boundary: human sign-off required — {', '.join(roles)}. Agent cannot commit spend.")
        run["phase"] = "signoff"; run["pt"] = 0

    # ---------------- SIGN-OFF GATE ----------------
    elif phase == "signoff":
        run["pt"] += 1
        cts = run["contract"]
        if c["autonomy"].startswith("L3") and cts["pct"] >= 8 and run["pt"] >= 2:
            for sg in cts["sigs"]:
                if sg["status"] == "pending":
                    sg["status"] = "signed"; sg["at"] = sim["tick"]
                    ev(sim, "AUTO", f"L3 auto-sign · {sg['role']} ({sg['name']}) approved {cts['id']}.")
            finalize(sim)
        elif run["pt"] % 4 == 0:
            ev(sim, "HUMAN", f"⏳ Awaiting sign-off on {cts['id']} · SLA 4h · open Policy & Approvals.")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------
def _layout(fig, height):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono, monospace", color=P["mut"], size=11),
        margin=dict(l=10, r=14, t=42, b=10),
        legend=dict(orientation="h", y=1.14, x=0, font=dict(size=10, color=P["txt"])),
        hoverlabel=dict(bgcolor=P["surf"], bordercolor=P["line"], font=dict(color=P["txt"], size=11)),
    )
    return fig

def fig_offers(run, c):
    req = run["req"]
    if not run["short"] or not by_id(run, run["short"][0])["hist"]:
        return None
    fmt = "$,.2f" if udec(req) else "$,.0f"
    fig = go.Figure()
    for i, sid in enumerate(run["short"]):
        s = by_id(run, sid)
        fig.add_trace(go.Scatter(
            x=list(range(len(s["hist"]))), y=s["hist"], name=s["name"],
            mode="lines+markers", line=dict(color=SUP_COLORS[i % 5], width=2.6),
            marker=dict(size=6), hovertemplate="%{y:" + fmt + "}<extra>" + s["name"] + "</extra>"))
    ceil_u = req["base_unit"] * c["ceiling"] / 100
    target = req["base_unit"] * (1 - c["anchor"] * .7 / 100)
    for y, colr, dash, label in [
        (req["base_unit"], P["rose"], "dash", "Baseline"),
        (ceil_u, P["amber"], "dashdot", "Policy ceiling"),
        (target, P["green"], "dot", "Target"),
    ]:
        fig.add_hline(y=y, line_dash=dash, line_color=colr, opacity=.75,
                      annotation_text=label, annotation_position="top left",
                      annotation_font=dict(size=9.5, color=colr))
    fig.update_xaxes(title=dict(text="Negotiation round", font=dict(size=10)), dtick=1,
                     gridcolor=P["line"], zeroline=False)
    fig.update_yaxes(tickformat=fmt, gridcolor=P["line"], zeroline=False)
    fig.update_layout(hovermode="x unified")
    return _layout(fig, 345)

def fig_radar(rows):
    dims = ["Price", "Quality", "Lead time", "Risk (inv)", "ESG", "Terms"]
    keys = ["price", "quality", "lead", "risk", "esg", "terms"]
    fig = go.Figure()
    for i, r in enumerate(rows[:3]):
        vals = [r["sub"][k] for k in keys]
        colr = SUP_COLORS[i % 5]
        fig.add_trace(go.Scatterpolar(
            r=vals + vals[:1], theta=dims + dims[:1], name=r["s"]["name"],
            fill="toself", fillcolor=colr + "22", line=dict(color=colr, width=2),
            marker=dict(size=4)))
    fig.update_layout(polar=dict(
        bgcolor="rgba(0,0,0,0)",
        radialaxis=dict(range=[0, 100], tickfont=dict(size=8.5, color=P["mut"]),
                        gridcolor=P["line"], linecolor=P["line"]),
        angularaxis=dict(gridcolor=P["line"], linecolor=P["line"],
                         tickfont=dict(size=10, color=P["txt"]))))
    return _layout(fig, 330)

def fig_waterfall(req, s):
    base = req["base_total"]; total = s["offer"] * req["qty"]
    sav = base - total; tv = terms_value(req, s)
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["absolute", "relative", "relative", "total"],
        x=["Baseline", "Price savings", "Terms value", "Effective cost"],
        y=[base, -sav, -tv, 0],
        text=[money(base), "−" + money(sav), "−" + money(tv), money(base - sav - tv)],
        textposition="outside", textfont=dict(size=10.5, color=P["txt"]),
        decreasing=dict(marker=dict(color=P["green"])),
        increasing=dict(marker=dict(color=P["rose"])),
        totals=dict(marker=dict(color=P["violet"])),
        connector=dict(line=dict(color=P["line"], width=1.4)),
    ))
    fig.update_yaxes(tickformat="$,.0f", gridcolor=P["line"], zeroline=False,
                     range=[0, base * 1.22])
    fig.update_xaxes(gridcolor=P["line"])
    return _layout(fig, 300)

# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------
def status_badge(sim):
    run = sim["run"]
    if not sim["running"]:
        return "<span class='badge mut'><span class='dot'></span>PAUSED</span>"
    if sim["hold"]:
        return "<span class='badge mut'><span class='dot'></span>HOLD · QUEUE</span>"
    ph = run["phase"]
    if ph == "sourcing":
        return "<span class='badge cyan'><span class='dot'></span>SOURCING</span>"
    if ph == "negotiate":
        cap = cfg()["maxr"] + run["extra"]
        return f"<span class='badge cyan'><span class='dot'></span>NEGOTIATING · R{run['round']}/{cap}</span>"
    if ph == "evaluate":
        return "<span class='badge violet'><span class='dot'></span>SCORING</span>"
    if ph == "guard":
        return "<span class='badge amber'><span class='dot'></span>POLICY GUARD</span>"
    if ph == "draft":
        return "<span class='badge violet'><span class='dot'></span>DRAFTING</span>"
    return "<span class='badge amber'><span class='dot'></span>AWAITING SIGN-OFF</span>"

def kpis_html(sim):
    c = sim["counters"]; run = sim["run"]; req = run["req"]
    realized = sim["realized"]
    rpct = realized / sim["base_signed"] * 100 if sim["base_signed"] else 0.0
    signed = sum(1 for l in sim["ledger"] if l["status"] == "executed")
    proj_v, proj_s = "—", "awaiting first offers"
    live = [by_id(run, i) for i in run["short"] if by_id(run, i)["hist"]]
    if live:
        b = min(live, key=lambda s: s["offer"])
        psav = req["base_total"] - b["offer"] * req["qty"]
        proj_v = money(psav)
        proj_s = f"{psav / req['base_total'] * 100:.1f}% · {b['name']}"
    hours = sum(sim["hours"]) / len(sim["hours"]) if sim["hours"] else (sim["tick"] - run["start"]) * TICK_MINUTES / 60
    faster = max(0.0, 100 - hours / MANUAL_HOURS * 100)
    denom = c["accepted"] + c["rejected"]
    acc = f"{c['accepted'] / denom * 100:.0f}%" if denom else "—"
    cards = [
        ("k-green", "Savings realized", money(realized), f"<b>{rpct:.1f}%</b> vs baseline · {signed} signed"),
        ("", "Live best offer", proj_v, escape(proj_s)),
        ("k-amber", "Policy violation rate", f"{c['committed'] / max(1, signed) * 100:.1f}%", f"0 committed · <b>{c['blocked']} blocked</b> pre-commit"),
        ("k-violet", "Negotiation cycle", f"{hours:.1f}h", f"vs {MANUAL_HOURS:.0f}h manual · <b>−{faster:.0f}%</b>"),
        ("k-blue", "Buyer acceptance", acc, f"{c['accepted']} signed · {c['rejected']} rejected · {c['escalated']} escalated"),
    ]
    h = "<div class='kgrid'>"
    for cls, label, val, sub in cards:
        h += f"<div class='kcard {cls}'><div class='klabel'>{label}</div><div class='kval'>{val}</div><div class='ksub'>{sub}</div></div>"
    return h + "</div>"

def pipeline_html(sim):
    steps = ["Source", "Negotiate", "Score", "Guard", "Draft", "Sign-off"]
    idx = {"sourcing": 0, "negotiate": 1, "evaluate": 2, "guard": 3, "draft": 4, "signoff": 5}[sim["run"]["phase"]]
    h = "<div class='pipe'>"
    for i, sname in enumerate(steps):
        cls = "done" if i < idx else ("on" if i == idx else "")
        mark = "✓ " if i < idx else ""
        h += f"<span class='pstep {cls}'>{mark}{sname}</span>"
    return h + "</div>"

def feed_html(sim, kinds=None, limit=55):
    evs = sim["events"]
    if kinds:
        evs = [e for e in evs if e["kind"] in kinds]
    evs = evs[-limit:][::-1]
    h = "<div class='feed'>"
    for e in evs:
        h += (f"<div class='ev ev-{e['kind']}'><span class='ev-t'>{tplus(e['tick'])}</span>"
              f"<span class='ev-k'>{e['kind']}</span><span class='ev-x'>{e['text']}</span></div>")
    return h + "</div>"

def sup_cards_html(run):
    req = run["req"]
    live = [(i, by_id(run, i)) for i in run["short"] if by_id(run, i)["hist"]]
    if not live:
        return ""
    best_id = min(live, key=lambda t: t[1]["offer"])[1]["id"]
    h = "<div class='suprow'>"
    for i, s in live:
        idx = run["short"].index(i)
        colr = SUP_COLORS[idx % 5]
        pct = (1 - s["offer"] / req["base_unit"]) * 100
        lead_chip = chip("LEADING", "ok") if s["id"] == best_id else ""
        prepay = chip(f"prepay {s['terms']['prepay']}%", "warn") if s["terms"]["prepay"] > 0 else ""
        h += (f"<div class='supcard {'lead' if s['id'] == best_id else ''}'>"
              f"<div class='supname'><span class='supdot' style='background:{colr}'></span>{s['name']} {lead_chip}</div>"
              f"<div class='supval'>{money(s['offer'], udec(req))}</div>"
              f"{chip(f'−{pct:.1f}% vs base', 'ok')} {prepay}"
              f"<div class='supterms'>{terms_brief(s)}<br>lead {s['terms']['lead']}d · risk {s['risk']}</div></div>")
    return h + "</div>"

def table_html(headers, rows):
    h = "<div class='tblwrap'><table><thead><tr>"
    for hd in headers:
        h += f"<th>{hd}</th>"
    h += "</tr></thead><tbody>"
    for row in rows:
        h += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>"
    return h + "</tbody></table></div>"

def risk_chip(risk, maxrisk):
    cls = "ok" if risk <= 40 else ("warn" if risk <= maxrisk else "bad")
    return chip(str(risk), cls)

# ---------------------------------------------------------------------------
# Export builders
# ---------------------------------------------------------------------------
def contract_md(c):
    lines = [f"# PURCHASE AGREEMENT {c['id']}",
             f"**Status:** {c['status'].upper()} · drafted {tplus(c['tick'])} by ACCORD·01",
             f"**Buyer:** {c['buyer']}  ", f"**Supplier:** {c['supplier']}  ",
             f"**Requisition:** {c['req']} — {c['title']}", "",
             "## Commercial schedule", "",
             "| Item | Qty | Unit price | Total | Baseline | Savings |",
             "|---|---|---|---|---|---|",
             f"| {c['item']} | {c['qty']:,} | {money(c['unit'], c['udec'])} | {money(c['total'])} | {money(c['baseline'])} | {money(c['sav'])} ({c['pct']:.1f}%) |",
             "",
             f"Payment Net {c['terms']['pay']} · prepayment {c['terms']['prepay']}% · price lock {c['terms']['lock']} mo · "
             f"warranty/SLA {c['terms']['warr']} mo · lead ≤ {c['terms']['lead']} d", "",
             "## Clauses"]
    for i, cl in enumerate(c["clauses"], 1):
        lines += ["", f"### {i}. {cl['title']} ({cl['code']})", cl["body"]]
    lines += ["", "## Signatures"]
    for sg in c["sigs"]:
        at = f" · {tplus(sg['at'])}" if sg["at"] is not None else ""
        lines.append(f"- **{sg['role']}** — {sg['name']} · {sg['status'].upper()}{at}")
    lines += ["", "---", "_Generated in the ACCORD sandbox with synthetic data. Not a legal commitment._"]
    return "\n".join(lines)

def report_md(sim):
    c = sim["counters"]
    denom = c["accepted"] + c["rejected"]
    acc = f"{c['accepted'] / denom * 100:.0f}%" if denom else "n/a"
    hours = f"{sum(sim['hours']) / len(sim['hours']):.1f}h" if sim["hours"] else "in progress"
    rpct = sim["realized"] / sim["base_signed"] * 100 if sim["base_signed"] else 0
    lines = ["# ACCORD·01 — Run report",
             f"Seed {sim['seed']} · {tplus(sim['tick'])} simulated · agent spend ${sim['cost']:.2f}", "",
             "## Success metrics",
             f"- Savings vs baseline: **{money(sim['realized'])} ({rpct:.1f}%)**",
             f"- Policy violation rate: **0.0%** committed · {c['blocked']} blocked pre-commit · {c['checks']} checks",
             f"- Negotiation cycle time: **{hours}** (manual benchmark {MANUAL_HOURS:.0f}h)",
             f"- Buyer acceptance rate: **{acc}** ({c['accepted']} signed / {c['rejected']} rejected / {c['escalated']} escalated)",
             "", "## Award ledger", "",
             "| Contract | Requisition | Supplier | Total | Savings | Cycle | Status |",
             "|---|---|---|---|---|---|---|"]
    for l in sim["ledger"]:
        lines.append(f"| {l['cid']} | {l['req']} | {l['supplier']} | {money(l['total'])} | {money(l['sav'])} ({l['pct']:.1f}%) | {l['hours']:.1f}h | {l['status']} |")
    lines += ["", "## Recent agent trace"]
    for e in sim["events"][-30:]:
        lines.append(f"- `{tplus(e['tick'])}` **{e['kind']}** — {e['text']}")
    lines += ["", "---", "_Synthetic sandbox run — no real vendors, prices or commitments._"]
    return "\n".join(lines)

# ---------------------------------------------------------------------------
# UI callbacks (mirror widget values into sim so fragment reruns keep them)
# ---------------------------------------------------------------------------
def _mirror_weight(k):
    st.session_state.sim["weights"][k] = st.session_state[f"w_{k}"]

def _mirror_ui(field, wkey):
    st.session_state.sim["ui"][field] = st.session_state[wkey]

# ---------------------------------------------------------------------------
# Console sections
# ---------------------------------------------------------------------------
TABS = ["🎯 Mission Control", "🔎 Sourcing", "📊 Scorecard", "🛡️ Policy & Approvals", "📄 Contract"]

def render_header(sim):
    run = sim["run"]; c = cfg()
    left, right = st.columns([0.62, 0.38], gap="small")
    with left:
        st.markdown(
            f"<div style='display:flex;align-items:center;gap:14px;flex-wrap:wrap'>"
            f"<h2 style='margin:0;font-size:22px'>{run['req']['id']} · {run['req']['title']}</h2>"
            f"{status_badge(sim)}</div>", unsafe_allow_html=True)
    with right:
        cap = c["maxr"] + run["extra"]
        st.markdown(
            f"<div class='chips' style='text-align:right'>"
            f"{chip('⏱ ' + tplus(sim['tick']), 'hot')} {chip('seed ' + str(sim['seed']))} "
            f"{chip(f'⛁ {run[chr(116)+chr(111)+chr(107)] / 1000:.1f}k/40k tok')} "
            f"{chip(f'${sim[chr(99)+chr(111)+chr(115)+chr(116)]:.2f}')} {chip(f'R{run[chr(114)+chr(111)+chr(117)+chr(110)+chr(100)]}/{cap}', 'vio')}</div>",
            unsafe_allow_html=True)
        st.download_button("⬇ Export run report (.md)", data=report_md(sim),
                           file_name=f"accord_run_{sim['seed']}.md", mime="text/markdown",
                           key="dl_report", **DL_W)

def render_nav(sim):
    pending = 1 if sim["run"]["phase"] == "signoff" and sim["run"]["contract"] and sim["run"]["contract"]["status"] == "pending" else 0
    clicked = None
    with st.container(key="nav"):
        cols = st.columns(len(TABS), gap="small")
        for i, (colname, label) in enumerate(zip(cols, TABS)):
            txt = label + (" ●" if i == 3 and pending else "")
            if colname.button(txt, key=f"nav_{i}", type="primary" if sim["nav"] == i else "secondary", **BTN_W):
                clicked = i
    if clicked is not None and clicked != sim["nav"]:
        sim["nav"] = clicked
        rerun_frag()

def render_mission(sim):
    run = sim["run"]; c = cfg()
    st.markdown(kpis_html(sim), unsafe_allow_html=True)
    st.markdown(pipeline_html(sim), unsafe_allow_html=True)
    cts = run["contract"]
    if run["phase"] == "signoff" and cts and cts["status"] == "pending" and not c["autonomy"].startswith("L3"):
        b1, b2 = st.columns([0.78, 0.22], gap="small")
        with b1:
            st.markdown(
                f"<div class='banner'><span class='b-t'>🛑 HUMAN SIGN-OFF REQUIRED</span>"
                f"<span class='b-x'>{cts['id']} · {cts['supplier']} · {money(cts['total'])} · "
                f"saves {money(cts['sav'])} ({cts['pct']:.1f}%) — the agent's authority stops here.</span></div>",
                unsafe_allow_html=True)
        with b2:
            if st.button("Open approval inbox →", key="go_appr", type="primary", **BTN_W):
                sim["nav"] = 3
                rerun_frag()
    left, right = st.columns([1.55, 1.0], gap="medium")
    with left:
        st.markdown("<div class='panel'><h4>📉 Negotiation theater — unit price vs mandate</h4></div>",
                    unsafe_allow_html=True)
        fig = fig_offers(run, c)
        if fig is not None:
            show_fig(fig, "fig_offers")
        else:
            st.markdown("<div class='panel'><span class='dots'>Discovering suppliers</span></div>",
                        unsafe_allow_html=True)
        st.markdown(sup_cards_html(run), unsafe_allow_html=True)
    with right:
        st.markdown("<div class='panel'><h4>🧠 Agent trace — plan · act · observe · reflect</h4></div>",
                    unsafe_allow_html=True)
        kinds = None if c["verbose"] else {"PLAN", "ACT", "GUARD", "BLOCK", "CONTRACT", "HUMAN", "AUTO", "SAVE", "SYS"}
        st.markdown(feed_html(sim, kinds=kinds), unsafe_allow_html=True)
    st.markdown("<div class='hint'>Tip · tune Aggressiveness / Anchor in the sidebar and watch the curve react · "
                "switch Autonomy to L3 for hands-free auto-sign · Reject a contract to force a re-negotiation loop.</div>",
                unsafe_allow_html=True)

def render_sourcing(sim):
    run = sim["run"]; req = run["req"]; c = cfg(); ui = sim["ui"]
    left, right = st.columns([1.1, 1.0], gap="medium")
    with left:
        st.markdown(
            f"<div class='panel'><h4>📥 Purchase requisition {req['id']}</h4>"
            f"<div class='kv'><span>Item</span><b>{req['item']}</b></div>"
            f"<div class='kv'><span>Category</span><b>{req['cat']}</b></div>"
            f"<div class='kv'><span>Quantity</span><b>{req['qty']:,}</b></div>"
            f"<div class='kv'><span>Baseline unit / total</span><b>{money(req['base_unit'], udec(req))} · {money(req['base_total'])}</b></div>"
            f"<div class='kv'><span>Budget ceiling</span><b>{money(req['budget'])}</b></div>"
            f"<div class='kv'><span>Required terms</span><b>Net ≥30 · warranty ≥{req['need']['warr']}mo · lead ≤{req['need']['lead']}d</b></div>"
            f"</div>", unsafe_allow_html=True)
    with right:
        okc = sum(1 for s in run["sups"] if s["risk"] <= c["maxrisk"])
        anchor_p = req["base_unit"] * (1 - c["anchor"] / 100)
        target = req["base_unit"] * (1 - c["anchor"] * .7 / 100)
        st.markdown(
            f"<div class='panel'><h4>🛰️ Discovery funnel</h4>"
            f"<div class='kv'><span>Vendor universe scanned</span><b>{run['scanned']}</b></div>"
            f"<div class='kv'><span>Risk-qualified</span><b>{okc}</b></div>"
            f"<div class='kv'><span>Shortlisted for negotiation</span><b>{len(run['short'])}</b></div>"
            f"<div class='kv'><span>Anchor / target</span><b>{money(anchor_p, udec(req))} / {money(target, udec(req))}</b></div>"
            f"<div class='kv'><span>Provenance</span><b>catalog · past RFQs · web scan</b></div>"
            f"</div>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns([1.2, 1.0, 0.8], gap="small")
    with f1:
        st.text_input("Search supplier / source", value=ui["q"], key="ui_q",
                      on_change=_mirror_ui, args=("q", "ui_q"), placeholder="e.g. Nordvik, web scan…")
    with f2:
        st.slider("Min qualification score", 0, 90, int(ui["minq"]), key="ui_minq",
                  on_change=_mirror_ui, args=("minq", "ui_minq"))
    with f3:
        st.toggle("Hide risk-blocked", value=bool(ui["hide_blocked"]), key="ui_hb",
                  on_change=_mirror_ui, args=("hide_blocked", "ui_hb"))
    q = ui["q"].lower()
    rows = []
    for s in sorted(run["sups"], key=qual_score, reverse=True):
        qs = qual_score(s)
        if q and q not in s["name"].lower() and q not in s["src"].lower():
            continue
        if qs < ui["minq"]:
            continue
        blocked = s["risk"] > c["maxrisk"]
        if ui["hide_blocked"] and blocked:
            continue
        status = chip("BLOCKED · RISK-11", "bad") if blocked else (
            chip("SHORTLISTED", "hot") if s["id"] in run["short"] else chip("QUALIFIED"))
        rows.append([f"<span class='nm'>{s['name']}</span>", s["src"],
                     f"{bar(qs)}<span style='font-size:10px;color:#64738F'>{qs:.0f}</span>",
                     risk_chip(s["risk"], c["maxrisk"]), f"{s['lead']}d", str(s["esg"]),
                     money(s["list"], udec(req)), status])
    st.markdown(table_html(["Supplier", "Provenance", "Qualification", "Risk", "Lead", "ESG", "List price", "Status"], rows),
                unsafe_allow_html=True)
    st.markdown("<div class='hint'>Synthetic vendor universe · qualification = 45% quality · 25% risk⁻¹ · 15% ESG · 15% lead-time. "
                "Raise “Max vendor risk” in the sidebar to see blocked suppliers re-enter.</div>", unsafe_allow_html=True)

def render_scorecard(sim):
    run = sim["run"]; req = run["req"]
    if not run["short"]:
        st.markdown("<div class='panel'><span class='dots'>Scorecard builds once offers arrive</span></div>",
                    unsafe_allow_html=True)
        return
    st.markdown("<div class='panel'><h4>⚖️ Award weights — move a slider, the recommendation recomputes live</h4></div>",
                unsafe_allow_html=True)
    wlabels = [("price", "Price"), ("quality", "Quality"), ("lead", "Lead time"),
               ("risk", "Risk (inverse)"), ("esg", "ESG"), ("terms", "Terms")]
    cols = st.columns(3, gap="small")
    for i, (k, label) in enumerate(wlabels):
        with cols[i % 3]:
            st.slider(label, 0, 60, int(sim["weights"][k]), key=f"w_{k}",
                      on_change=_mirror_weight, args=(k,))
    rows_data = score_rows(run, sim)
    rows = []
    for i, r in enumerate(rows_data):
        s = r["s"]
        status = chip("RECOMMENDED", "ok") if (r["ok"] and r is rows_data[0]) else (
            chip("ELIGIBLE", "info") if r["ok"] else chip("BLOCKED", "bad"))
        if not r["ok"] and rows_data[0] is not r:
            first_ok = next((x for x in rows_data if x["ok"]), None)
            if first_ok is r:
                status = chip("RECOMMENDED", "ok")
        rows.append([f"#{i + 1}", f"<span class='nm'>{s['name']}</span>",
                     money(s["offer"], udec(req)), f"−{r['pct']:.1f}%",
                     f"{r['sub']['quality']:.0f}", f"{s['risk']}", f"{s['terms']['lead']}d",
                     f"{r['sub']['terms']:.0f}",
                     f"{bar(r['total'])}<b>{r['total']:.1f}</b>", status])
    st.markdown(table_html(["Rank", "Supplier", "Offer", "Δ base", "Qual", "Risk", "Lead", "Terms", "Weighted score", "Status"], rows),
                unsafe_allow_html=True)
    okrows = [r for r in rows_data if r["ok"]]
    if okrows:
        b = okrows[0]; s = b["s"]; tv = terms_value(req, s)
        st.markdown(
            f"<div class='rec'>🏆 <b>Recommended award: {s['name']}</b> — {money(s['offer'], udec(req))}/unit · "
            f"saves <b>{money(b['sav'])} ({b['pct']:.1f}%)</b> plus {money(tv)} negotiated-terms value · "
            f"risk {s['risk']} · {terms_brief(s)}.</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='banner'><span class='b-t'>⚠️ NO COMPLIANT OFFER</span>"
                    "<span class='b-x'>Every offer breaches the current ceiling or risk cap — loosen guardrails or let the agent escalate.</span></div>",
                    unsafe_allow_html=True)
    left, right = st.columns([1.0, 1.0], gap="medium")
    with left:
        st.markdown("<div class='panel'><h4>🕸️ Capability radar — top 3</h4></div>", unsafe_allow_html=True)
        show_fig(fig_radar(rows_data), "fig_radar")
    with right:
        st.markdown("<div class='panel'><h4>💧 Savings waterfall — vs baseline</h4></div>", unsafe_allow_html=True)
        show_fig(fig_waterfall(req, (okrows[0] if okrows else rows_data[0])["s"]), "fig_waterfall")

def render_approvals(sim):
    run = sim["run"]; req = run["req"]; c = cfg()
    left, right = st.columns([1.05, 1.0], gap="medium")
    with left:
        stored = run["checks"] and run["phase"] in ("guard", "draft", "signoff")
        if stored:
            rows_g = run["checks"]; sub = f"validated sweep · {by_id(run, run['best'])['name']}"
        else:
            live = [by_id(run, i) for i in run["short"] if by_id(run, i)["hist"]]
            s = min(live, key=lambda x: x["offer"]) if live else min(run["sups"], key=lambda x: x["list"])
            rows_g = guard_rows(run, s, c); sub = f"live pre-check · {s['name']}"
        st.markdown(f"<div class='panel'><h4>🛡️ Policy & Approval Guard</h4>"
                    f"<div class='chips'>{chip(sub, 'hot')} {chip(str(sim['counters']['checks']) + ' checks run')} "
                    f"{chip(str(sim['counters']['blocked']) + ' blocked', 'warn')}</div></div>", unsafe_allow_html=True)
        rows = []
        for r in rows_g:
            stt = chip("PASS", "ok") if r["ok"] else (chip("WARN", "warn") if r["sev"] == "warn" else chip("BLOCK", "bad"))
            rows.append([r["code"], f"<span class='nm'>{r['name']}</span>", r["limit"], r["actual"], stt])
        st.markdown(table_html(["Policy", "Rule", "Limit", "Current", "Status"], rows), unsafe_allow_html=True)
        st.markdown("<div class='panel' style='margin-top:12px'><h4>🚧 Guard interventions</h4></div>", unsafe_allow_html=True)
        st.markdown(feed_html(sim, kinds={"GUARD", "BLOCK"}, limit=10), unsafe_allow_html=True)
    with right:
        cts = run["contract"]
        st.markdown("<div class='panel'><h4>📥 Approval inbox</h4></div>", unsafe_allow_html=True)
        if cts and cts["status"] == "pending":
            sig_html = ""
            for sg in cts["sigs"]:
                if sg["role"] == "ACCORD Agent":
                    continue
                mark = "✅" if sg["status"] == "signed" else "⭕"
                sig_html += f"<div class='kv'><span>{mark} {sg['role']}</span><b>{sg['name']}</b></div>"
            ct = cts["terms"]
            terms_txt = f"Net {ct['pay']} · {ct['warr']}mo · lock {ct['lock']}mo"
            st.markdown(
                f"<div class='panel' style='border-color:rgba(245,158,11,.5)'>"
                f"<h4>{cts['id']} · {cts['supplier']}</h4>"
                f"<div class='kv'><span>Contract value</span><b>{money(cts['total'])}</b></div>"
                f"<div class='kv'><span>Savings vs baseline</span><b style='color:#059669'>{money(cts['sav'])} ({cts['pct']:.1f}%)</b></div>"
                f"<div class='kv'><span>Terms</span><b>{terms_txt}</b></div>"
                f"{sig_html}</div>", unsafe_allow_html=True)
            nxt = next((sg for sg in cts["sigs"] if sg["status"] == "pending"), None)
            if nxt and st.button(f"✍️ Sign as {nxt['role']} — {nxt['name']}", key="act_sign", type="primary", **BTN_W):
                sign_action(sim)
            if st.button("↩ Request changes (Net 60 · 12-mo lock)", key="act_chg", **BTN_W):
                changes_action(sim)
            if st.button("✕ Reject offer — send back to negotiation", key="act_rej", **BTN_W):
                reject_action(sim)
            st.markdown("<div class='hint'>Signing commits spend — at L1/L2 the agent can never execute this itself.</div>",
                        unsafe_allow_html=True)
        else:
            ph = run["phase"].replace("signoff", "sign-off")
            st.markdown(f"<div class='panel'>Inbox clear — agent is <b>{ph}</b> on {req['id']}. "
                        f"Drafts land here automatically after the guard sweep.</div>", unsafe_allow_html=True)
        if sim["undo"] and st.button("↶ Undo last decision", key="act_undo", **BTN_W):
            undo_action(sim)
        st.markdown("<div class='panel' style='margin-top:12px'><h4>🧾 Approval matrix AM-2</h4>"
                    "<div class='kv'><span>≤ $50k</span><b>Category Buyer</b></div>"
                    "<div class='kv'><span>≤ $250k</span><b>Buyer + Finance Controller</b></div>"
                    "<div class='kv'><span>&gt; $250k</span><b>Buyer + Finance + Legal</b></div></div>",
                    unsafe_allow_html=True)
        if sim["ledger"]:
            rows = []
            for l in sim["ledger"][-6:][::-1]:
                stt = chip("EXECUTED", "ok") if l["status"] == "executed" else chip("ESCALATED", "bad")
                rows.append([l["cid"], l["req"], f"<span class='nm'>{l['supplier']}</span>",
                             money(l["sav"]), f"{l['hours']:.1f}h", stt])
            st.markdown(table_html(["Contract", "Req", "Supplier", "Savings", "Cycle", "Status"], rows),
                        unsafe_allow_html=True)

def render_contract(sim):
    contracts = sim["contracts"]
    if not contracts:
        st.markdown(
            "<div class='paper'><div class='wm'>AWAITING DRAFT</div>"
            "<h2>PURCHASE AGREEMENT</h2><div class='p-sub'>Accord·01 contract drafting & handoff</div>"
            "<h3>1. Scope & Deliverables</h3><p>The draft assembles automatically once the negotiation converges and the "
            "Policy & Approval Guard clears the winning offer. Watch Mission Control — clauses, pricing schedule and the "
            "signature route will appear here.</p>"
            "<h3>2. Pricing & Price Lock</h3><p>Fixed unit pricing with a negotiated lock period; no escalation during the lock.</p>"
            "<h3>3. Signature Route</h3><p>Routed per approval matrix AM-2 based on contract value.</p></div>",
            unsafe_allow_html=True)
        return
    pending = [k for k, v in contracts.items() if v["status"] == "pending"]
    others = sorted([k for k in contracts if k not in pending], key=lambda k: contracts[k]["tick"], reverse=True)
    options = pending + others
    sel = sim["ui"]["csel"]
    idx = options.index(sel) if sel in options else 0
    st.selectbox("Agreement", options, index=idx, key="ui_csel",
                 on_change=_mirror_ui, args=("csel", "ui_csel"),
                 format_func=lambda k: f"{k} · {contracts[k]['supplier']} · {contracts[k]['status'].upper()}")
    c = contracts[st.session_state.get("ui_csel", options[idx])]
    stamp_cls = {"pending": "draft", "executed": "exec", "rejected": "rej", "revising": "rev"}.get(c["status"], "draft")
    wm = "" if c["status"] == "executed" else f"<div class='wm'>{c['status'].upper()}</div>"
    arts = ""
    for i, cl in enumerate(c["clauses"], 1):
        arts += f"<h3>{i}. {cl['title']} <span style='font-size:10px;color:#6B6350 !important'>({cl['code']})</span></h3><p>{cl['body']}</p>"
    sigs = ""
    for sg in c["sigs"]:
        cls = "agent" if sg["role"] == "ACCORD Agent" else ("signed" if sg["status"] == "signed" else "pending")
        at = f" · {tplus(sg['at'])}" if sg["at"] is not None else ""
        name = sg["name"] if sg["status"] in ("signed", "drafted") else "________________"
        sigs += (f"<div class='sig {cls}'><div class='s-role'>{sg['role']}</div>"
                 f"<div class='s-name'>{name}</div><div class='s-st'>{sg['status'].upper()}{at}</div></div>")
    st.markdown(
        f"<div class='paper'>{wm}"
        f"<h2>PURCHASE AGREEMENT {c['id']}<span class='stamp {stamp_cls}'>{c['status'].upper()}</span></h2>"
        f"<div class='p-sub'>Drafted {tplus(c['tick'])} · ACCORD·01 · clause library v3.2 · requisition {c['req']}</div>"
        f"<p><b>Buyer:</b> {c['buyer']} &nbsp;&nbsp; <b>Supplier:</b> {c['supplier']}</p>"
        f"<table><tr><th>Item</th><th>Qty</th><th>Unit price</th><th>Total</th><th>Baseline</th><th>Savings</th></tr>"
        f"<tr><td>{c['item']}</td><td>{c['qty']:,}</td><td>{money(c['unit'], c['udec'])}</td>"
        f"<td>{money(c['total'])}</td><td>{money(c['baseline'])}</td><td>{money(c['sav'])} ({c['pct']:.1f}%)</td></tr></table>"
        f"{arts}<h3>Execution</h3><div class='sig-grid'>{sigs}</div></div>",
        unsafe_allow_html=True)
    chips_h = "<div class='clausechips'>" + " ".join(chip(cl["code"] + " · " + cl["title"], "vio") for cl in c["clauses"]) + "</div>"
    st.markdown(chips_h, unsafe_allow_html=True)
    st.download_button("⬇ Download agreement (.md)", data=contract_md(c),
                       file_name=f"{c['id']}_draft.md", mime="text/markdown", key="dl_contract", **DL_W)

# ---------------------------------------------------------------------------
# Live console (single auto-refreshing fragment)
# ---------------------------------------------------------------------------
def render_console():
    sim = st.session_state.sim
    c = cfg()
    now = time.time()
    if sim["running"] and not sim["hold"] and now - sim["last_wall"] >= c["speed"] * 0.85:
        do_tick(sim)
        sim["last_wall"] = now
    render_header(sim)
    render_nav(sim)
    section = sim["nav"]
    if section == 0:
        render_mission(sim)
    elif section == 1:
        render_sourcing(sim)
    elif section == 2:
        render_scorecard(sim)
    elif section == 3:
        render_approvals(sim)
    else:
        render_contract(sim)
    st.markdown("<div class='foot'>ACCORD·01 SANDBOX · synthetic vendors, prices & policies · human sign-off enforced at L1–L2 · "
                "no commitments leave this page · plan→act→observe→reflect loop with token & round budgets</div>",
                unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar — permanently visible control deck
# ---------------------------------------------------------------------------
def sidebar(sim):
    with st.sidebar:
        st.markdown("<div class='brand'>ACCORD<em>·01</em> <span>v2.4</span></div>"
                    "<div class='tagline'>Autonomous Procurement Negotiation</div>"
                    "<span class='sandbox-chip'>● LIVE SANDBOX · SEEDED</span>", unsafe_allow_html=True)
        b1, b2 = st.columns(2, gap="small")
        with b1:
            label = "⏸ Pause" if sim["running"] else "▶ Resume"
            if st.button(label, key="sb_pause", type="primary" if sim["running"] else "secondary", **BTN_W):
                sim["running"] = not sim["running"]
                sim["last_wall"] = 0.0
        with b2:
            if st.button("⏭ Step +1", key="sb_step", disabled=sim["running"] or sim["hold"], **BTN_W):
                do_tick(sim)
                sim["last_wall"] = time.time()
        b3, b4 = st.columns(2, gap="small")
        with b3:
            if st.button("↺ Reset run", key="sb_reset", **BTN_W):
                seed = sim["seed"]
                st.session_state.sim = build_scenario(seed)
                for _ in range(4):
                    do_tick(st.session_state.sim)
                st.toast(f"↺ Scenario reset · seed {seed}", icon="↺")
        with b4:
            if st.button("🎲 Randomize", key="sb_rand", **BTN_W):
                seed = random.randint(1, 999999)
                st.session_state.sim = build_scenario(seed)
                for _ in range(4):
                    do_tick(st.session_state.sim)
                st.toast(f"🎲 New scenario seeded · {seed}", icon="🎲")
        if sim["hold"]:
            if st.button("▶ Next requisition", key="sb_next", type="primary", **BTN_W):
                sim["hold"] = False
                really_advance(sim)
                sim["last_wall"] = 0.0
        st.slider("Tick speed (seconds / round)", 0.4, 3.0, 1.2, 0.1, key="sb_speed")

        st.markdown("<div class='side-h'>Negotiation strategy</div>", unsafe_allow_html=True)
        st.slider("Aggressiveness", 0, 100, 62, key="sb_aggr",
                  help="Higher = steeper concession pressure on suppliers")
        st.slider("Opening anchor discount %", 5, 25, 14, key="sb_anchor",
                  help="Agent's first counter below baseline; target = 70% of anchor depth")
        st.slider("Max negotiation rounds", 3, 10, 7, key="sb_rounds")
        st.selectbox("Concession priority", TERM_MODES, index=1, key="sb_terms")

        st.markdown("<div class='side-h'>Policy guardrails</div>", unsafe_allow_html=True)
        st.slider("Unit price ceiling · % of baseline", 85, 100, 96, key="sb_ceiling",
                  help="PROC-02 walk-away — offers above this are never accepted")
        st.slider("Max vendor risk score", 30, 90, 60, key="sb_risk",
                  help="RISK-11 — suppliers above this are excluded from sourcing")
        st.selectbox("Autonomy level", AUTONOMY, index=1, key="sb_autonomy",
                  help="L3 auto-signs compliant deals with ≥8% savings; L1/L2 always wait for a human")

        st.markdown("<div class='side-h'>Run options</div>", unsafe_allow_html=True)
        st.toggle("Auto-continue to next requisition", value=True, key="sb_autocont")
        st.toggle("Verbose trace (observe / reflect)", value=True, key="sb_verbose")

        st.markdown("<div class='side-h'>Who's in the loop</div>", unsafe_allow_html=True)
        st.markdown("<div class='persona'>👤 <b>Mara Chen</b> · Procurement Manager (you)</div>"
                    "<div class='persona'>🧑‍💼 <b>L. Ortega</b> · Category Buyer</div>"
                    "<div class='persona'>📊 <b>D. Okafor</b> · Finance Controller</div>"
                    "<div class='persona'>⚖️ <b>A. Novak</b> · Legal Counsel</div>", unsafe_allow_html=True)
        st.caption("Loop caps per requisition: ≤12 rounds · 40k tokens · $2.00 agent spend. "
                   "Synthetic data only — no API key, no real commitments.")

# ---------------------------------------------------------------------------
# Boot — auto-loaded, auto-starting
# ---------------------------------------------------------------------------
if "sim" not in st.session_state:
    st.session_state.sim = build_scenario(20261113)
    for _ in range(4):
        do_tick(st.session_state.sim)

sidebar(st.session_state.sim)
sim = st.session_state.sim
_interval = cfg()["speed"]
_run_every = _interval if sim["running"] and not sim["hold"] else None
st.fragment(run_every=_run_every)(render_console)()