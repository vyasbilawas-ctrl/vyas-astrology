"""VYAS Executive Publication-Grade PDF Report Generator.

Features:
- Full Devanagari (Hindi) and English bilingual rendering with high-quality Unicode typography (Nirmala UI).
- True North Indian Chart drawings with visual sign and planet placements (in Hindi or English).
- Complete multi-chart rendering:
  * Page 1: Lagna Kundli (D1) & Navamsha Kundli (D9)
  * Page 2: Dashamsha Kundli (D10) & Bhava Chalit Kundli + KP Planetary Matrix
  * Page 3: Shashtyamsha Kundli (D60) + KP Cusps + D60 Deity Table + Chalit Table
  * Page 4: Samudaya Ashtakavarga (SAV) & Shadbala Strength Breakdown
  * Page 5: Jaimini Chara Karakas & Vimshottari Dasha Hierarchy (MD, AD, PD, SD, PrD with timestamps)
  * Page 6: Deep Classical Sutra Bank (Laghu Parashari, Phaladeepika, Saravali, BPHS) & TCR Predictive Synthesis
- Dynamic 2-pass page numbering ("Page X of Y") with executive golden and ruby borders.
"""
import os
import re
from typing import Dict, List, Optional
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, Line, String
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from vyas import constants

# ---------------------------------------------------------------------------
# Font Registration (Windows Nirmala / Mangal / Fallback)
# ---------------------------------------------------------------------------
FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"

for reg_path, bold_path in [
    ("C:/Windows/Fonts/Nirmala.ttf", "C:/Windows/Fonts/NirmalaB.ttf"),
    ("C:/Windows/Fonts/mangal.ttf", "C:/Windows/Fonts/mangalb.ttf"),
    ("C:/Windows/Fonts/ARIALUNI.TTF", "C:/Windows/Fonts/ARIALUNI.TTF"),
]:
    if os.path.exists(reg_path) and os.path.exists(bold_path):
        try:
            pdfmetrics.registerFont(TTFont("VyasUnicode", reg_path))
            pdfmetrics.registerFont(TTFont("VyasUnicode-Bold", bold_path))
            FONT_REGULAR = "VyasUnicode"
            FONT_BOLD = "VyasUnicode-Bold"
            break
        except Exception:
            pass

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "logo.jpg")

# ---------------------------------------------------------------------------
# Translation Dictionaries (Bilingual Support)
# ---------------------------------------------------------------------------
PLANET_ABBR_HI = {
    "Sun": "सू", "Su": "सू",
    "Moon": "चं", "Mo": "चं",
    "Mars": "मं", "Ma": "मं",
    "Mercury": "बु", "Me": "बु",
    "Jupiter": "गु", "Ju": "गु",
    "Venus": "शु", "Ve": "शु",
    "Saturn": "श", "Sa": "श",
    "Rahu": "रा", "Ra": "रा",
    "Ketu": "के", "Ke": "के",
    "Ascendant": "लग्न", "Asc": "लग्न", "Lagna": "लग्न", "Lg": "लग्न"
}

PLANET_NAMES_HI = {
    "Sun": "सूर्य", "Moon": "चन्द्र", "Mars": "मङ्गल", "Mercury": "बुध",
    "Jupiter": "गुरु", "Venus": "शुक्र", "Saturn": "शनि", "Rahu": "राहु", "Ketu": "केतु",
    "Lagna": "लग्न", "Ascendant": "लग्न"
}

SIGN_NAMES_HI = {
    "Aries": "मेष", "Taurus": "वृषभ", "Gemini": "मिथुन", "Cancer": "कर्क",
    "Leo": "सिंह", "Virgo": "कन्या", "Libra": "तुला", "Scorpio": "वृश्चिक",
    "Sagittarius": "धनु", "Capricorn": "मकर", "Aquarius": "कुम्भ", "Pisces": "मीन"
}

BHAVA_NAMES_HI = {
    1: "प्रथम भाव (लग्न)", 2: "द्वितीय भाव (धन)", 3: "तृतीय भाव (सहज)", 4: "चतुर्थ भाव (सुख)",
    5: "पंचम भाव (पुत्र/धी)", 6: "षष्ठ भाव (रिपु)", 7: "सप्तम भाव (जाया)", 8: "अष्टम भाव (आयु)",
    9: "नवम भाव (भाग्य)", 10: "दशम भाव (कर्म)", 11: "एकादश भाव (लाभ)", 12: "द्वादश भाव (व्यय)"
}

def translate_planet(pl: str, lang: str = "hi") -> str:
    if lang == "hi":
        return PLANET_NAMES_HI.get(pl, pl)
    return pl

def translate_sign(sign: str, lang: str = "hi") -> str:
    if lang == "hi":
        return SIGN_NAMES_HI.get(sign, sign)
    return sign

def translate_chart_item(item_str: str, lang: str = "hi") -> str:
    if lang != "hi":
        return item_str
    # Replace English planet abbreviations with Devanagari
    res = item_str
    for en_abbr, hi_abbr in PLANET_ABBR_HI.items():
        res = re.sub(rf'\b{en_abbr}\b', hi_abbr, res)
    return res

# ---------------------------------------------------------------------------
# Numbered Canvas for Two-Pass Dynamic Page Numbering & Border Branding
# ---------------------------------------------------------------------------
class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        page_count = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(page_count)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        
        # Outer Royal Gold Border
        self.setStrokeColor(colors.HexColor("#D4AF37"))
        self.setLineWidth(1.2)
        self.rect(0.35 * inch, 0.42 * inch, 7.8 * inch, 10.16 * inch)
        
        # Inner Ruby Accent Border
        self.setStrokeColor(colors.HexColor("#8B0000"))
        self.setLineWidth(0.6)
        self.rect(0.38 * inch, 0.45 * inch, 7.74 * inch, 10.10 * inch)

        # Header Text (Pages 2+)
        if self._pageNumber > 1:
            self.setFont(FONT_BOLD, 8)
            self.setFillColor(colors.HexColor("#8B0000"))
            self.drawString(0.5 * inch, 10.35 * inch, "VYAS (Vedic Yield Astrology Systems)")
            self.setFont(FONT_REGULAR, 7.5)
            self.setFillColor(colors.HexColor("#444444"))
            self.drawRightString(8.0 * inch, 10.35 * inch, "System Developed by Nikhil Vyas (M.A. Jyotish / PG in Astrology) • Cell: 9414121172")
            self.setStrokeColor(colors.HexColor("#D4AF37"))
            self.setLineWidth(0.5)
            self.line(0.5 * inch, 10.28 * inch, 8.0 * inch, 10.28 * inch)

        # Footer on all pages
        self.setFont(FONT_BOLD, 7.5)
        self.setFillColor(colors.HexColor("#8B0000"))
        self.drawString(0.5 * inch, 0.28 * inch, "VYAS ASTRA-Ω")
        self.setFont(FONT_REGULAR, 7)
        self.setFillColor(colors.HexColor("#333333"))
        self.drawString(1.4 * inch, 0.28 * inch, "• System Developed by Nikhil Vyas (M.A. Jyotish / PG in Astrology) • Cell: 9414121172 • Email: inikhilvyas@gmail.com")
        
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.setFont(FONT_BOLD, 7.5)
        self.setFillColor(colors.HexColor("#8B0000"))
        self.drawRightString(8.0 * inch, 0.28 * inch, page_str)

        self.restoreState()

# ---------------------------------------------------------------------------
# Visual North Indian Chart Drawing Function
# ---------------------------------------------------------------------------
def draw_north_indian_chart_pdf(houses_dict: dict, size: float = 210, title: str = "", lang: str = "hi") -> Drawing:
    """
    Renders a true North Indian chart in ReportLab Drawing.
    houses_dict: {1: ["2", "Su 07°42'", "Me 29°15'"], ...}
    First item is sign number; rest are planets with degrees.
    """
    d = Drawing(size, size)
    # Background
    d.add(Rect(0, 0, size, size, fillColor=colors.HexColor("#FDFBF7"), strokeColor=colors.HexColor("#8B0000"), strokeWidth=1.5))
    
    # Outer accents
    d.add(Rect(3, 3, size - 6, size - 6, fillColor=None, strokeColor=colors.HexColor("#D4AF37"), strokeWidth=0.6))
    
    # Diagonals
    d.add(Line(0, 0, size, size, strokeColor=colors.HexColor("#8B0000"), strokeWidth=1))
    d.add(Line(0, size, size, 0, strokeColor=colors.HexColor("#8B0000"), strokeWidth=1))
    
    # Inner Diamond
    mid = size / 2.0
    q = size / 4.0
    d.add(Line(mid, size, 0, mid, strokeColor=colors.HexColor("#8B0000"), strokeWidth=1))
    d.add(Line(0, mid, mid, 0, strokeColor=colors.HexColor("#8B0000"), strokeWidth=1))
    d.add(Line(mid, 0, size, mid, strokeColor=colors.HexColor("#8B0000"), strokeWidth=1))
    d.add(Line(size, mid, mid, size, strokeColor=colors.HexColor("#8B0000"), strokeWidth=1))
    
    # Coordinates of 12 Houses in North Indian Chart
    positions = {
        1: (mid, mid + q - 8),
        2: (q, size - q/2 + 2),
        3: (q/2 + 4, mid + q - 8),
        4: (q, mid),
        5: (q/2 + 4, q + 6),
        6: (q, q/2 - 2),
        7: (mid, q + 6),
        8: (size - q, q/2 - 2),
        9: (size - q/2 - 4, q + 6),
        10: (size - q, mid),
        11: (size - q/2 - 4, mid + q - 8),
        12: (size - q, size - q/2 + 2)
    }
    
    for h_num, pos in positions.items():
        x, y = pos
        h_content = houses_dict.get(h_num, [])
        if not h_content:
            continue
            
        sign_val = str(h_content[0])
        planets = h_content[1:]
        
        # Sign number (Ruby)
        d.add(String(x, y + 8, sign_val, fontName=FONT_BOLD, fontSize=7.5, fillColor=colors.HexColor("#8B0000"), textAnchor="middle"))
        
        # Planets
        for idx, pl_str in enumerate(planets):
            pl_y = y - 4 - (idx * 8.5)
            clean_pl = translate_chart_item(pl_str, lang=lang)
            d.add(String(x, pl_y, clean_pl, fontName=FONT_BOLD, fontSize=6.5, fillColor=colors.HexColor("#081127"), textAnchor="middle"))
            
    if title:
        d.add(String(mid, size - 12, title, fontName=FONT_BOLD, fontSize=8, fillColor=colors.HexColor("#8B0000"), textAnchor="middle"))
        
    return d

# ---------------------------------------------------------------------------
# Main Executive PDF Document Builder
# ---------------------------------------------------------------------------
def build_pdf_report(filename: str, report_data: dict, lang: str = "hi"):
    """
    Builds the 6-page comprehensive VYAS thesis report in either Hindi ('hi'),
    English ('en'), or Bilingual ('bi').
    """
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=0.45 * inch,
        rightMargin=0.45 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.55 * inch
    )

    styles = getSampleStyleSheet()
    
    header_title_style = ParagraphStyle(
        'VyasHeaderTitle',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=13,
        alignment=1,
        textColor=colors.HexColor("#8B0000"),
        spaceAfter=2
    )
    sub_title_style = ParagraphStyle(
        'VyasSubTitle',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=8.5,
        alignment=1,
        textColor=colors.HexColor("#D4AF37"),
        spaceAfter=1
    )
    dev_contact_style = ParagraphStyle(
        'VyasDevContact',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=7.5,
        alignment=1,
        textColor=colors.HexColor("#222222"),
        spaceAfter=5
    )
    section_style = ParagraphStyle(
        'VyasSectionHeader',
        parent=styles['Heading2'],
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=colors.HexColor("#8B0000"),
        spaceBefore=4,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'VyasBody',
        parent=styles['Normal'],
        fontName=FONT_REGULAR,
        fontSize=7,
        leading=8.5
    )
    bold_body_style = ParagraphStyle(
        'VyasBoldBody',
        parent=styles['Normal'],
        fontName=FONT_BOLD,
        fontSize=7,
        leading=8.5
    )

    story = []

    # =========================================================================
    # PAGE 1: COVER, NATIVE META, AVAKHADA & D1 / D9 KUNDLIS
    # =========================================================================
    if os.path.exists(LOGO_PATH):
        img_logo = Image(LOGO_PATH, width=0.85*inch, height=0.85*inch)
    else:
        img_logo = Paragraph("<b>☸️ VYAS</b>", header_title_style)

    top_invocation = "|| श्री गणेशाय नमः ||" if lang in ["hi", "bi"] else "|| OM SRI GANESHAYA NAMAHA ||"
    sub_heading = "Vedic, KP, Nadi & Multi-System Research-Grade Jyotisha Thesis" if lang == "en" else "वैदिक, केपी, नाड़ी एवं बहु-पद्धति शोध-स्तरीय ज्योतिष शोध प्रबंध"

    banner_text = [
        Paragraph(top_invocation, ParagraphStyle('DevanagariTop', fontName=FONT_BOLD, fontSize=10, alignment=1, textColor=colors.HexColor("#8B0000"))),
        Paragraph("VYAS (Vedic Yield Astrology Systems)", header_title_style),
        Paragraph(sub_heading, sub_title_style),
        Paragraph("<b>System Developed by Nikhil Vyas (M.A. Jyotish / PG in Astrology)</b> • Cell: 9414121172 • Email: inikhilvyas@gmail.com", dev_contact_style)
    ]
    t_banner = Table([[img_logo, banner_text]], colWidths=[1.1*inch, 6.4*inch])
    t_banner.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_banner)
    story.append(Spacer(1, 0.04 * inch))

    # Native Details & Avakhada Chakra Table
    meta = report_data.get("native_meta", {})
    av = report_data.get("avakhada", {})
    pan = report_data.get("panchang", {})

    sec1_title = "<b>Birth Meta & Avakhada Chakra / जन्म विवरण एवं अवकहड़ा चक्र</b>" if lang != "en" else "<b>Birth Details & Avakhada Chakra</b>"
    story.append(Paragraph(sec1_title, section_style))

    l_name = "Name / नाम:" if lang != "en" else "Name:"
    l_date = "Date / दिनांक:" if lang != "en" else "Date of Birth:"
    l_time = "Time / समय:" if lang != "en" else "Time of Birth:"
    l_place = "Place / स्थान:" if lang != "en" else "Place of Birth:"
    l_varna = "Varna / वर्ण:" if lang != "en" else "Varna:"
    l_vashya = "Vashya / वश्य:" if lang != "en" else "Vashya:"
    l_yoni = "Yoni / योनि:" if lang != "en" else "Yoni:"
    l_gana = "Gana / गण:" if lang != "en" else "Gana:"
    l_nadi = "Nadi / नाड़ी:" if lang != "en" else "Nadi:"
    l_tithi = "Tithi / तिथि:" if lang != "en" else "Tithi:"
    l_yoga = "Yoga / योग:" if lang != "en" else "Yoga:"

    rashi_val = translate_sign(str(av.get("Rashi", "Scorpio")), lang=lang)

    meta_data = [
        [Paragraph(f"<b>{l_name}</b>", bold_body_style), Paragraph(str(meta.get("name","")), body_style),
         Paragraph(f"<b>{l_date}</b>", bold_body_style), Paragraph(str(meta.get("dob","")), body_style),
         Paragraph(f"<b>{l_varna}</b>", bold_body_style), Paragraph(str(av.get("Varna","Brahmin")), body_style)],
        
        [Paragraph(f"<b>{l_time}</b>", bold_body_style), Paragraph(str(meta.get("tob","")), body_style),
         Paragraph(f"<b>{l_place}</b>", bold_body_style), Paragraph(str(meta.get("pob","")), body_style),
         Paragraph(f"<b>{l_vashya}</b>", bold_body_style), Paragraph(str(av.get("Vashya","Keet")), body_style)],
        
        [Paragraph("<b>Lagna / लग्न:</b>" if lang != "en" else "<b>Lagna:</b>", bold_body_style), Paragraph(str(meta.get("asc_str","Aries")), body_style),
         Paragraph("<b>Ayanamsha / अयनांश:</b>" if lang != "en" else "<b>Ayanamsa:</b>", bold_body_style), Paragraph(f"{meta.get('ayanamsha_type','Lahiri')} ({meta.get('ayanamsha_deg','')})", body_style),
         Paragraph(f"<b>{l_yoni}</b>", bold_body_style), Paragraph(str(av.get("Yoni","Mrig")), body_style)],
         
        [Paragraph("<b>Rashi / राशि:</b>" if lang != "en" else "<b>Rashi:</b>", bold_body_style), Paragraph(rashi_val, body_style),
         Paragraph("<b>Nakshatra / नक्षत्र:</b>" if lang != "en" else "<b>Nakshatra:</b>", bold_body_style), Paragraph(str(av.get("Nakshatra","Anuradha-4")), body_style),
         Paragraph(f"<b>{l_gana}</b>", bold_body_style), Paragraph(str(av.get("Gana","Deva")), body_style)],

        [Paragraph(f"<b>{l_tithi}</b>", bold_body_style), Paragraph(str(pan.get("tithi","Shukla Pratipada")), body_style),
         Paragraph(f"<b>{l_yoga}</b>", bold_body_style), Paragraph(str(pan.get("yoga","Sukarma")), body_style),
         Paragraph(f"<b>{l_nadi}</b>", bold_body_style), Paragraph(str(av.get("Nadi","Madhya")), body_style)]
    ]
    t_meta = Table(meta_data, colWidths=[1.1*inch, 1.4*inch, 1.1*inch, 1.4*inch, 1.1*inch, 1.4*inch])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDFBF7")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2B48C")),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 0.08 * inch))

    # Visual D1 and D9 Charts
    d1_houses = report_data.get("d1_chart_houses", {})
    d9_houses = report_data.get("d9_chart_houses", {})

    d1_title = "Lagna Kundli (D1) / लग्न चक्र" if lang != "en" else "Lagna Kundli (D1)"
    d9_title = "Navamsha Kundli (D9) / नवमांश चक्र" if lang != "en" else "Navamsha Kundli (D9)"

    d1_drawing = draw_north_indian_chart_pdf(d1_houses, size=210, title=d1_title, lang=lang)
    d9_drawing = draw_north_indian_chart_pdf(d9_houses, size=210, title=d9_title, lang=lang)

    charts_table_p1 = Table([
        [Paragraph(f"<b>{d1_title}</b>", section_style), Paragraph(f"<b>{d9_title}</b>", section_style)],
        [d1_drawing, d9_drawing]
    ], colWidths=[3.75 * inch, 3.75 * inch])
    charts_table_p1.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(charts_table_p1)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: D10 (DASHAMSHA), BHAVA CHALIT CHARTS & PLANETARY MATRIX
    # =========================================================================
    d10_houses = report_data.get("d10_chart_houses", {})
    chalit_houses = report_data.get("chalit_chart_houses", {})

    d10_title = "Dashamsha Kundli (D10) / दशमांश (कर्म चक्र)" if lang != "en" else "Dashamsha Kundli (D10 - Career/Karma)"
    chalit_title = "Bhava Chalit Kundli / भाव चलित चक्र" if lang != "en" else "Bhava Chalit Kundli"

    d10_drawing = draw_north_indian_chart_pdf(d10_houses, size=195, title=d10_title, lang=lang)
    chalit_drawing = draw_north_indian_chart_pdf(chalit_houses, size=195, title=chalit_title, lang=lang)

    charts_table_p2 = Table([
        [Paragraph(f"<b>{d10_title}</b>", section_style), Paragraph(f"<b>{chalit_title}</b>", section_style)],
        [d10_drawing, chalit_drawing]
    ], colWidths=[3.75 * inch, 3.75 * inch])
    charts_table_p2.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('TOPPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(charts_table_p2)
    story.append(Spacer(1, 0.05 * inch))

    # Planetary Positions Table
    sec2_title = "<b>Vedic & KP Planetary Matrix (Micro-Degrees, Nakshatra & Sub-Lords) / ग्रह स्पष्ट तालिका</b>" if lang != "en" else "<b>Vedic & KP Planetary Matrix (Micro-Degrees, Nakshatra & Sub-Lords)</b>"
    story.append(Paragraph(sec2_title, section_style))

    if lang == "en":
        p_headers = ["Planet", "Sign", "Degree (DMS)", "Nakshatra", "Pada", "RL", "NL", "SL", "SSL", "Speed"]
    else:
        p_headers = ["ग्रह (Planet)", "राशि", "अंश (DMS)", "नक्षत्र", "पद", "RL", "NL", "SL", "SSL", "गति"]

    p_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in p_headers]]
    for p_name, p_d in report_data.get("planetary_positions", {}).items():
        pl_display = translate_planet(p_name, lang=lang)
        sign_display = translate_sign(p_d.get("sign",""), lang=lang)
        p_rows.append([
            Paragraph(f"<b>{pl_display}</b>", bold_body_style),
            Paragraph(sign_display, body_style),
            Paragraph(p_d.get("dms",""), body_style),
            Paragraph(p_d.get("nakshatra",""), body_style),
            Paragraph(str(p_d.get("pada","")), body_style),
            Paragraph(translate_planet(p_d.get("rl",""), lang=lang), body_style),
            Paragraph(translate_planet(p_d.get("nl",""), lang=lang), body_style),
            Paragraph(translate_planet(p_d.get("sl",""), lang=lang), body_style),
            Paragraph(translate_planet(p_d.get("ssl",""), lang=lang), body_style),
            Paragraph(str(p_d.get("speed","-")), body_style)
        ])
    t_planets = Table(p_rows, colWidths=[0.85*inch, 0.8*inch, 0.9*inch, 0.95*inch, 0.35*inch, 0.65*inch, 0.65*inch, 0.65*inch, 0.65*inch, 0.85*inch])
    t_planets.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8B0000")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2B48C")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FFF8DC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_planets)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: D60 CHART, KP 12 CUSPS, D60 DEITIES & SRIPATI CHALIT TABLE
    # =========================================================================
    d60_houses = report_data.get("d60_chart_houses", {})
    d60_chart_title = "Shashtyamsha Kundli (D60) / षष्ट्यंश चक्र (प्रारब्ध)" if lang != "en" else "Shashtyamsha Kundli (D60 - Destiny)"
    d60_drawing = draw_north_indian_chart_pdf(d60_houses, size=180, title=d60_chart_title, lang=lang)

    # KP Cusps Table
    if lang == "en":
        c_headers = ["Cusp", "Sign", "Degree", "Sign Lord", "Star Lord", "Sub Lord", "Sub-Sub"]
    else:
        c_headers = ["भाव (Cusp)", "राशि", "अंश", "राशि स्वामी", "नक्षत्र स्वामी", "उप-स्वामी", "SSL"]
    c_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in c_headers]]
    for c_d in report_data.get("kp_cusps", []):
        c_rows.append([
            Paragraph(f"<b>{c_d.get('Cusp','')}</b>", bold_body_style),
            Paragraph(translate_sign(c_d.get("Sign",""), lang=lang), body_style),
            Paragraph(c_d.get("Degree (DMS)",""), body_style),
            Paragraph(translate_planet(c_d.get("Sign Lord (RL)",""), lang=lang), body_style),
            Paragraph(translate_planet(c_d.get("Star Lord (NL)",""), lang=lang), body_style),
            Paragraph(translate_planet(c_d.get("Sub Lord (SL)",""), lang=lang), body_style),
            Paragraph(translate_planet(c_d.get("Sub-Sub Lord (SSL)",""), lang=lang), body_style)
        ])
    t_cusps = Table(c_rows, colWidths=[0.7*inch, 0.7*inch, 0.8*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.65*inch])
    t_cusps.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#081127")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#D4AF37")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FDFBF7")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))

    # Place D60 chart and KP cusps side by side
    top_p3_table = Table([
        [Paragraph(f"<b>{d60_chart_title}</b>", section_style), Paragraph("<b>KP Placidus 12 House Cusps / भाव कस्प</b>", section_style)],
        [d60_drawing, t_cusps]
    ], colWidths=[2.6 * inch, 4.9 * inch])
    top_p3_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 1),
    ]))
    story.append(top_p3_table)
    story.append(Spacer(1, 0.04 * inch))

    # D60 Shashtyamsha Deity Table
    sec3_d60_title = "<b>D60 Shashtyamsha Analysis & Deities (षष्ट्यंश देवता एवं प्रकृति - BPHS)</b>" if lang != "en" else "<b>D60 Shashtyamsha Deity Analysis (Parashara BPHS)</b>"
    story.append(Paragraph(sec3_d60_title, section_style))

    if lang == "en":
        d60_headers = ["Point", "Sign", "Degree in D60", "Sign Lord", "D60 Deity", "Disposition"]
    else:
        d60_headers = ["बिन्दु (Point)", "राशि", "D60 अंश", "राशि स्वामी", "अधिष्ठाता देवता", "प्रकृति"]

    d60_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in d60_headers]]
    for d60_item in report_data.get("d60_table", []):
        d60_rows.append([
            Paragraph(f"<b>{translate_planet(d60_item.get('Point',''), lang=lang)}</b>", bold_body_style),
            Paragraph(translate_sign(d60_item.get("Divisional Sign",""), lang=lang), body_style),
            Paragraph(d60_item.get("Degree in Varga",""), body_style),
            Paragraph(translate_planet(d60_item.get("Sign Lord",""), lang=lang), body_style),
            Paragraph(f"<b>{d60_item.get('D60 Deity','')}</b>", bold_body_style),
            Paragraph("शुभ (Shubha)" if d60_item.get("Disposition","") == "Shubha" else "अशुभ (Ashubha)" if lang != "en" else d60_item.get("Disposition",""), body_style)
        ])
    t_d60 = Table(d60_rows, colWidths=[1.1*inch, 1.1*inch, 1.2*inch, 1.1*inch, 1.8*inch, 1.2*inch])
    t_d60.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8B0000")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2B48C")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FFF8DC")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_d60)
    story.append(Spacer(1, 0.04 * inch))

    # Sripati Chalit Table
    sec3_ch_title = "<b>Sripati Bhava Chalit (श्रीपति भाव आरम्भ, मध्य एवं अन्त)</b>" if lang != "en" else "<b>Sripati Bhava Chalit Details</b>"
    story.append(Paragraph(sec3_ch_title, section_style))

    if lang == "en":
        ch_headers = ["Bhava", "Arambha (Start)", "Madhya (Cusp)", "Anta (End)", "Planets in Chalit"]
    else:
        ch_headers = ["भाव", "आरम्भ (Arambha)", "मध्य (Madhya)", "अन्त (Anta)", "चलित भावस्थ ग्रह"]

    ch_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in ch_headers]]
    for ch_item in report_data.get("chalit_table", []):
        pl_chalit = ch_item.get("Planets in Chalit Bhava","")
        if lang == "hi" and pl_chalit and pl_chalit != "-":
            pl_parts = [translate_planet(p.strip(), lang="hi") for p in pl_chalit.split(",")]
            pl_chalit = ", ".join(pl_parts)
        ch_rows.append([
            Paragraph(f"<b>{ch_item.get('Bhava','')}</b>", bold_body_style),
            Paragraph(ch_item.get("Bhava Arambha",""), body_style),
            Paragraph(ch_item.get("Bhava Madhya",""), body_style),
            Paragraph(ch_item.get("Bhava Anta",""), body_style),
            Paragraph(pl_chalit, bold_body_style)
        ])
    t_chalit = Table(ch_rows, colWidths=[1.1*inch, 1.7*inch, 1.7*inch, 1.7*inch, 1.3*inch])
    t_chalit.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#081127")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#D4AF37")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FDFBF7")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_chalit)
    story.append(PageBreak())

    # ---------------------------------------------------------------------------
    # PAGE 5: DETAILED PREDICTIONS (per domain)
    # ---------------------------------------------------------------------------
    pred_data = report_data.get("predictions", {})
    if pred_data:
        story.append(PageBreak())
        sec5_title = "Detailed Predictions" if lang == "en" else "विस्तृत भविष्यफल"
        story.append(Paragraph(sec5_title, section_style))
        for domain, pred_text in pred_data.items():
            domain_title = domain.title() if isinstance(domain, str) else str(domain)
            story.append(Paragraph(f"<b>{domain_title}</b>", bold_body_style))
            story.append(Paragraph(pred_text, body_style))
            story.append(Spacer(1, 0.08 * inch))
    else:
        # placeholder if no predictions supplied
        story.append(PageBreak())
        story.append(Paragraph("No detailed predictions available.", body_style))

    sav_row = [str(sav_vals[i]) for i in range(12)] + [str(sum(sav_vals))]
    t_sav = Table([[Paragraph(f"<b>{h}</b>", bold_body_style) for h in sav_headers],
                   [Paragraph(f"<b>{v}</b>", bold_body_style) for v in sav_row]], colWidths=[0.55*inch]*12 + [0.7*inch])
    t_sav.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8B0000")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2B48C")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_sav)
    story.append(Spacer(1, 0.1 * inch))

    # Shadbala Breakdown
    sec4_sb = "<b>Shadbala Six-Fold Planetary Strength (षड्बल विरूप एवं रूप सामर्थ्य)</b>" if lang != "en" else "<b>Shadbala Six-Fold Planetary Strength (Virupas, Rupas & Verdict)</b>"
    story.append(Paragraph(sec4_sb, section_style))

    if lang == "en":
        sb_headers = ["Planet", "Sthana", "Dig", "Kala", "Chesta", "Naisargika", "Drik", "Total Virupas", "Rupas", "Rank", "Verdict"]
    else:
        sb_headers = ["ग्रह", "स्थान बल", "दिग् बल", "काल बल", "चेष्टा", "नैसर्गिक", "दृग् बल", "कुल विरूप", "रूप", "श्रेणी", "परिणाम"]

    sb_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in sb_headers]]
    for sb_item in report_data.get("shadbala_table", []):
        p_name = sb_item.get('Planet','')
        p_disp = translate_planet(p_name, lang=lang)
        verd = sb_item.get("Verdict","")
        if lang != "en":
            verd = verd.replace("Strong", "प्रबल (Strong)").replace("Weak", "निर्बल (Weak)")
        sb_rows.append([
            Paragraph(f"<b>{p_disp}</b>", bold_body_style),
            Paragraph(str(sb_item.get("Sthana Bala","")), body_style),
            Paragraph(str(sb_item.get("Dig Bala","")), body_style),
            Paragraph(str(sb_item.get("Kala Bala","")), body_style),
            Paragraph(str(sb_item.get("Chesta Bala","")), body_style),
            Paragraph(str(sb_item.get("Naisargika","")), body_style),
            Paragraph(str(sb_item.get("Drik Bala","")), body_style),
            Paragraph(f"<b>{sb_item.get('Total Virupas','')}</b>", bold_body_style),
            Paragraph(str(sb_item.get("Rupas","")), body_style),
            Paragraph(str(sb_item.get("Rank","")), bold_body_style),
            Paragraph(verd, body_style)
        ])
    t_sb = Table(sb_rows, colWidths=[0.75*inch, 0.65*inch, 0.6*inch, 0.6*inch, 0.65*inch, 0.65*inch, 0.6*inch, 0.85*inch, 0.6*inch, 0.55*inch, 0.9*inch])
    t_sb.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#081127")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#D4AF37")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FFF8DC")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_sb)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 5: JAIMINI CHARA KARAKAS & EXPANDED 5-LEVEL VIMSHOTTARI DASHA
    # =========================================================================
    sec5_jk = "<b>Jaimini Chara Karakas (सप्त चर कारक) & Arudha Lagna</b>" if lang != "en" else "<b>Jaimini Chara Karakas & Arudha Lagna</b>"
    story.append(Paragraph(sec5_jk, section_style))

    if lang == "en":
        jk_headers = ["Karaka", "Planet", "Degree in Sign", "Sign", "Signification"]
    else:
        jk_headers = ["कारक (Karaka)", "ग्रह (Graha)", "अंश (DMS)", "राशि", "शास्त्रीय कारकत्व"]

    jk_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in jk_headers]]
    for jk in report_data.get("jaimini_karakas", []):
        jk_rows.append([
            Paragraph(f"<b>{jk.get('Karaka','')}</b>", bold_body_style),
            Paragraph(translate_planet(jk.get("Graha",""), lang=lang), bold_body_style),
            Paragraph(jk.get("Degree in Sign",""), body_style),
            Paragraph(translate_sign(jk.get("Rashi",""), lang=lang), body_style),
            Paragraph(jk.get("Classical Role",""), body_style)
        ])
    t_jk = Table(jk_rows, colWidths=[1.4*inch, 1.0*inch, 1.2*inch, 1.1*inch, 2.8*inch])
    t_jk.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8B0000")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2B48C")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FDFBF7")]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
    ]))
    story.append(t_jk)
    story.append(Spacer(1, 0.08 * inch))

    # Vimshottari Dasha Hierarchy (5-Level Micro Resolution)
    bal_str = report_data.get('dasha_balance', '')
    sec5_dasha = f"<b>Vimshottari Dasha Hierarchy (Dasha Balance at Birth: {bal_str})</b>" if lang == "en" else f"<b>विंशोत्तरी दशा अनुक्रम (जन्म समय दशा शेष: {bal_str})</b>"
    story.append(Paragraph(sec5_dasha, section_style))

    cur_d = report_data.get("running_dasha", {})
    if cur_d:
        md_l = translate_planet(cur_d.get('MD',{}).get('lord',''), lang=lang)
        ad_l = translate_planet(cur_d.get('AD',{}).get('lord',''), lang=lang)
        pd_l = translate_planet(cur_d.get('PD',{}).get('lord',''), lang=lang)
        sd_l = translate_planet(cur_d.get('SD',{}).get('lord',''), lang=lang)
        prd_l = translate_planet(cur_d.get('PrD',{}).get('lord',''), lang=lang)
        
        run_txt = f"<b>सक्रिय पंच-स्तरीय दशा (Active 5-Fold Dasha):</b> <b>{md_l}</b> MD &nbsp;|&nbsp; <b>{ad_l}</b> AD &nbsp;|&nbsp; <b>{pd_l}</b> PD &nbsp;|&nbsp; <b>{sd_l}</b> SD &nbsp;|&nbsp; <b>{prd_l}</b> PrD (Pratyantar Ends: {cur_d.get('PD',{}).get('end','')})"
        story.append(Paragraph(run_txt, bold_body_style))
        story.append(Spacer(1, 0.04 * inch))

    # Sub-table of Active Antardasha's 9 Pratyantar Dashas (Micro Breakdown)
    pd_list = report_data.get("active_ad_pratyantardashas", [])
    if pd_list:
        sub_pd_title = "<b>वर्तमान अन्तर्दशा की 9 प्रत्यन्तर्दशाएँ (Active Antardasha Pratyantar Breakdown):</b>" if lang != "en" else "<b>Current Antardasha's 9 Pratyantardashas:</b>"
        story.append(Paragraph(sub_pd_title, bold_body_style))
        pd_headers = ["प्रत्यन्तर्दशा नाथ (PD Lord)", "आरम्भ (Start)", "समाप्ति (End)", "अवधि (Days)", "स्थिति (Status)"] if lang != "en" else ["PD Lord", "Start Date", "End Date", "Duration (Days)", "Status"]
        pd_table_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in pd_headers]]
        for pd_item in pd_list:
            is_cur = pd_item.get("is_active", False)
            p_lord_str = translate_planet(pd_item.get("lord",""), lang=lang)
            status_str = "🔴 सक्रिय (ACTIVE)" if is_cur else "-"
            pd_table_rows.append([
                Paragraph(f"<b>{p_lord_str} PD</b>", bold_body_style),
                Paragraph(pd_item.get("start",""), body_style),
                Paragraph(pd_item.get("end",""), body_style),
                Paragraph(f"{pd_item.get('duration_days',0):.1f}", body_style),
                Paragraph(f"<b>{status_str}</b>", bold_body_style)
            ])
        t_pd = Table(pd_table_rows, colWidths=[1.6*inch, 1.6*inch, 1.6*inch, 1.2*inch, 1.5*inch])
        t_pd.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#8B0000")),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D2B48C")),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FFF8DC")]),
            ('TOPPADDING', (0,0), (-1,-1), 1.5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ]))
        story.append(t_pd)
        story.append(Spacer(1, 0.05 * inch))

    # Lifetime Mahadashas Overview
    if lang == "en":
        md_headers = ["Mahadasha Lord", "Start Date", "End Date", "Duration"]
    else:
        md_headers = ["महादशा स्वामी (MD Lord)", "आरम्भ तिथि (Start)", "समाप्ति तिथि (End)", "पूर्ण अवधि"]

    md_rows = [[Paragraph(f"<b>{h}</b>", bold_body_style) for h in md_headers]]
    for md_item in report_data.get("mahadasha_list", []):
        md_disp = translate_planet(md_item.get('lord',''), lang=lang)
        md_rows.append([
            Paragraph(f"<b>{md_disp} MD</b>", bold_body_style),
            Paragraph(md_item.get("start",""), body_style),
            Paragraph(md_item.get("end",""), body_style),
            Paragraph(f"{constants.VIMSHOTTARI_YEARS.get(md_item.get('lord',''), 0)} Years", body_style)
        ])
    t_md = Table(md_rows, colWidths=[1.8*inch, 1.8*inch, 1.8*inch, 2.1*inch])
    t_md.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#081127")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor("#D4AF37")),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#FFF8DC")]),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
    ]))
    story.append(t_md)
    story.append(PageBreak())

    # =========================================================================
    # PAGE 6: CLASSICAL SUTRA BANK & TRIPLE-CONVERGENCE PREDICTIONS
    # =========================================================================
    sec6_sutra = "<b>Classical Sutra Bank (शास्त्रीय सूत्र डेटाबैंक — लघु पाराशरी, फलदीपिका, सारावली, BPHS)</b>" if lang != "en" else "<b>Classical Sutra Bank (Laghu Parashari, Phaladeepika, Saravali & BPHS)</b>"
    story.append(Paragraph(sec6_sutra, section_style))

    for s_item in report_data.get("sutra_list", []):
        lbl_shloka = "श्लोक (Shloka):" if lang != "en" else "Sanskrit Shloka:"
        lbl_cond = "सत्यापित स्थिति (Condition):" if lang != "en" else "Verified Condition:"
        lbl_res = "फलकथन (Result):" if lang != "en" else "Deterministic Result:"

        s_block = [
            [Paragraph(f"<b>✨ {s_item.get('name','')}</b> [{s_item.get('category','')}] — <i>{s_item.get('source','')}</i>", bold_body_style)],
            [Paragraph(f"<b>{lbl_shloka}</b> <i>{s_item.get('shloka_sanskrit','')}</i>", body_style)],
            [Paragraph(f"<b>{lbl_cond}</b> {s_item.get('condition_description','')}", body_style)],
            [Paragraph(f"<b>{lbl_res}</b> {s_item.get('deterministic_result','')}", body_style)]
        ]
        t_s = Table(s_block, colWidths=[7.5*inch])
        t_s.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FFFDF8")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#8B0000")),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t_s)
        story.append(Spacer(1, 0.04 * inch))

    story.append(Spacer(1, 0.06 * inch))
    sec6_pred = "<b>Triple-Convergence Rule (TCR) Predictive Synthesis / दशा-गोचर समन्वय</b>" if lang != "en" else "<b>Triple-Convergence Rule (TCR) Predictive Synthesis</b>"
    story.append(Paragraph(sec6_pred, section_style))

    for p_item in report_data.get("predictions", []):
        pred_block = [
            [Paragraph(f"<b>{p_item.get('domain','')}</b> — <b>`{p_item.get('confidence','')}` {p_item.get('verdict','')}</b> (Horizon: {p_item.get('timing_window','')})", bold_body_style)],
            [Paragraph(p_item.get("detailed_analysis",""), body_style)]
        ]
        t_p = Table(pred_block, colWidths=[7.5*inch])
        t_p.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#FDFBF7")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#D4AF37")),
            ('TOPPADDING', (0,0), (-1,-1), 2),
            ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ]))
        story.append(t_p)
        story.append(Spacer(1, 0.04 * inch))

    doc.build(story, canvasmaker=NumberedCanvas)
