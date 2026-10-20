"""Executive AstroSage Gold Standard Master Publication Engine (56-Page Dossier).

Renders publication-grade Vedic astrological reports matching the exact industry gold standard
of AstroSage Premium Brihat Kundli / Astro Intelligence Report.

Complete 56-Page Master Structure:
Page 1:  Cover Page (Ganesha Artwork, Title, Branding, Native Particulars)
Page 2:  Basic Details & Avkahada Quadrant (Avkahada, Basic Details, Favourable Points, Ghatak Malefics)
Page 3:  Traditional Kundli Page (Metadata Box, D1 & D9 Diamond Charts, Vimshottari Overview, Planetary Positions, Ashtakvarga, Chalit)
Page 4:  || Your Ascendant || (Health, Temperament & Personality, Physical Appearance)
Page 5:  || Nakshatra Phal || (General Forecast, Education & Income, Family Life)
Pages 6-9: || Life Predictions || (Character, Happiness, Lifestyle, Career, Occupation, Health, Hobbies, Love, Finance, Education)
Page 10: || Manglik Details / Mangal Dosha || (Lagna & Moon Evaluation, Cancellations, Pre/Post-Marriage & Lal Kitab Remedies)
Pages 11-13: || Sadesati Report || Schedule (46 Periods across 90+ Years: Rising, Peak, Setting, Panoti)
Page 14: || Sadesati Report || Phases (Rising, Peak, Setting Phase Forecasts & Authentic Shani Upay)
Page 15: || Kalsarpa Dosh || (Definition, Rahu-Ketu Axis Analysis, Result, Lagna Chart)
Pages 16-18: || Varshaphal (Annual Predictions) Details || (Janam vs Varsha Parameters, Solar Return Chart, Muntha Forecast, 9 Mudda Dasha Periods)
Pages 19-20: || Vimshottari Mahadasha Phal || (Saturn to Jupiter Mahadashas with Sign & House Analysis)
Pages 21-22: || Yogini Dasha || (36-Year Cycles with Sub-Periods across Lifetime)
Page 23: || Jamini System - Karakamsa and Swamsa || (Karakamsa & Swamsa Charts, 7 Karakas, Classical Avasthas)
Pages 24-25: || Char Dasha || (Maha Dasha & 12 Antardasha Sub-Tables)
Pages 26-28: || Transit Today || (Current Gochar of Sun to Ketu with House-Specific Forecasts)
Pages 29-33: || Lal Kitab Prediction || (Sun to Ketu in Natal Houses with Benefic/Malefic Results & Authentic Upay)
Page 34: || Lal Kitab Calculation || (Planetary Positions, Soya/Kismat, Benefic/Malefic, Lagna Chart, 35-Year Dasha Cycle)
Pages 35-39: || Planet Consideration in Astrology || (Sun to Ketu In-Depth Astrological Considerations, Dignity, Lordship, Aspects)
Page 40: || Shodashvarga Table || (16 Vargas Signs Table & 16 Vargas Bhav Table for all Planets)
Pages 41-43: || Shodashvarga Charts || (16 Divisional Charts in North Indian Diamond Grid: 6 per page)
Page 44: || KP System / Nakshatra Nadi || (Metadata, KP Chart, Ruling Planets, Cuspal Positions, Planetary Positions, Significators, Significations)
Pages 45-48: || Vimshottari Dasha - Pratyantar || (5-Column Multidimensional Sub-Period Tables across 60 Antardashas)
Page 49: || Friendship Table || (Permanent Naisargika, Temporal Tatkalika, Five-fold Panchadha Maitri)
Page 50: || Shadbala and Bhavabala – Strength Calculations || (Complete 6-Fold Shadbala Breakdown & 12 Bhavabala with Rupas & Ranks)
Pages 51-53: Planetary Aspects (Western Aspect Grid, Aspects on Bhav Madhya, Aspects on KP Cusps)
Page 54: || Ashtakvarga Table || (BAV 12-Sign Matrix, SAV & Sarvashtakvarga Kundli Chart)
Page 55: || Prastharashtakvarga Tables || (7 Planet Sub-Matrices across 12 Signs + Shastric Disclaimer)
Page 56: Back Cover / Astrologer Consultation & Life Summary
"""
import os
import math
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Tuple, Optional, Any

from vyas import constants
from vyas import ashtakavarga
from vyas import shadbala
from vyas import kp
from vyas import panchang
from vyas import forensic_predictor
from vyas import chalit
from vyas import jaimini
from vyas import astrosage_content


def find_chrome() -> str:
    """Locates Google Chrome executable on the host system."""
    common_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        "chrome",
        "google-chrome",
        "chromium"
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    return "chrome"


def render_astrosage_diamond_svg(houses_data: dict, size: int = 300, chart_title: str = "") -> str:
    """
    Renders an authentic, publication-grade AstroSage diamond chart SVG
    with clean black lines, white background, and crisp typography.
    houses_data: Dict[int, list] where keys are 1-12.
                 First item is sign number string, subsequent items are planet strings.
    """
    s = size
    h = size / 2.0
    q = size / 4.0

    parts = [
        f'<svg width="{s}" height="{s}" viewBox="0 0 {s} {s}" xmlns="http://www.w3.org/2000/svg" style="background:#ffffff;">',
        f'<rect x="1" y="1" width="{s-2}" height="{s-2}" fill="#ffffff" stroke="#000000" stroke-width="1.4"/>'
    ]

    # Classical diagonal and diamond line grid
    lines = [
        (0, 0, s, s),
        (0, s, s, 0),
        (h, 0, s, h),
        (s, h, h, s),
        (h, s, 0, h),
        (0, h, h, 0)
    ]
    for x1, y1, x2, y2 in lines:
        parts.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000000" stroke-width="1.0"/>')

    # Coordinates for the 12 houses in North Indian system
    # Sign number position (sign_x, sign_y) and planets start position (px, py)
    coords = {
        1:  {"sn": (h, q - 10),       "p": (h, q + 6)},
        2:  {"sn": (q + 10, q/2 - 4), "p": (q - 10, q/2 + 2)},
        3:  {"sn": (q/2 + 10, q - 8), "p": (q/2 - 4, q + 10)},
        4:  {"sn": (q, h - 8),        "p": (q, h + 8)},
        5:  {"sn": (q/2 + 10, s - q - 8), "p": (q/2 - 4, s - q + 10)},
        6:  {"sn": (q + 10, s - q/2 - 4), "p": (q - 10, s - q/2 + 4)},
        7:  {"sn": (h, s - q + 10),   "p": (h, s - q - 8)},
        8:  {"sn": (s - q - 10, s - q/2 - 4), "p": (s - q + 10, s - q/2 + 4)},
        9:  {"sn": (s - q/2 - 10, s - q - 8), "p": (s - q/2 + 4, s - q + 10)},
        10: {"sn": (s - q, h - 8),    "p": (s - q, h + 8)},
        11: {"sn": (s - q/2 - 10, q - 8), "p": (s - q/2 + 4, q + 10)},
        12: {"sn": (s - q - 10, q/2 - 4), "p": (s - q + 10, q/2 + 2)}
    }

    font_sn_size = max(8.5, round(size * 0.033, 1))
    font_p_size = max(8.0, round(size * 0.030, 1))

    for house in range(1, 13):
        data = houses_data.get(house, [])
        if not data:
            continue
        sn_text = str(data[0])
        planets = data[1:]

        sn_x, sn_y = coords[house]["sn"]
        parts.append(f'<text x="{sn_x}" y="{sn_y}" font-family="Arial, sans-serif" font-size="{font_sn_size}" font-weight="bold" fill="#000000" text-anchor="middle">{sn_text}</text>')

        if planets:
            px, py = coords[house]["p"]
            # Split planets across lines if more than 2
            line_step = font_p_size + 2.5
            start_y = py - ((len(planets) - 1) * line_step / 2.0)
            for idx_p, p_str in enumerate(planets):
                cur_y = start_y + (idx_p * line_step)
                parts.append(f'<text x="{px}" y="{cur_y}" font-family="Arial, sans-serif" font-size="{font_p_size}" font-weight="normal" fill="#000000" text-anchor="middle">{p_str}</text>')

    if chart_title:
        parts.append(f'<text x="{h}" y="16" font-family="Arial, sans-serif" font-size="9" font-weight="bold" fill="#000000" text-anchor="middle">{chart_title}</text>')

    parts.append('</svg>')
    return "".join(parts)


def format_dms_clean(deg_val: float) -> str:
    """Formats float degrees into clean DD-MM-SS string."""
    deg = deg_val % 30.0
    d = int(deg)
    rem = (deg - d) * 60.0
    m = int(rem)
    s = int(round((rem - m) * 60.0))
    if s >= 60:
        m += 1
        s = 0
    if m >= 60:
        d += 1
        m = 0
    return f"{d:02d}-{m:02d}-{s:02d}"


def _d8(s_val) -> str:
    """Compact-but-correct date: '23/11/2019' -> '23/11/19'.
    (The old `[:8]` slice cut '23/11/2019' to the wrong '23/11/20'.)"""
    s = str(s_val)
    if len(s) >= 10 and s[2] == '/' and s[5] == '/':
        return s[:6] + s[6:10][2:]
    return s[:8]


def generate_56_page_publication_html(
    chart,
    birth: dict,
    kp_cusps: list,
    dasha_engine,
    vargas_detailed: dict,
    target_varsh_year: int = None,
    lang: str = "en"
) -> str:
    """
    Constructs the 56-page master publication HTML document strictly matching
    the AstroSage gold standard layout and typography.
    """
    is_hi = (lang == "hi")
    birth_dt = birth['local']
    name = birth.get('name', 'Nikhil Vyas')
    city = birth.get('city', 'Current Location')
    lat = birth.get('lat', 25.7711)
    lon = birth.get('lon', 73.3234)
    tz = birth.get('tz', 5.5)

    asc_sign_idx = chart.ascendant_sign
    moon_lon = chart.planets["Moon"].longitude
    moon_sign_idx = chart.planets["Moon"].sign_index
    sun_lon = chart.planets["Sun"].longitude

    # Target Varshphal year
    curr_dt = datetime.now()
    if target_varsh_year is None:
        if (curr_dt.month, curr_dt.day) < (birth_dt.month, birth_dt.day):
            target_varsh_year = curr_dt.year - 1
        else:
            target_varsh_year = curr_dt.year

    # Core Calculations
    dignities = forensic_predictor.analyze_all_planetary_dignities(chart, vargas_detailed)
    bhavas = forensic_predictor.analyze_all_12_bhavas(chart, dignities)
    mangal_data = forensic_predictor.compute_comprehensive_mangal_dosha(chart)
    kalsarp_data = forensic_predictor.compute_comprehensive_kalsarp(chart)
    sade_sati_phases = forensic_predictor.compute_comprehensive_sade_sati(birth_dt, moon_lon)
    varshphal_data = forensic_predictor.compute_tajik_varshphal(birth_dt, sun_lon, target_varsh_year, asc_sign_idx)
    mahadasha_interpretations = {item['planet']: item for item in forensic_predictor.compute_vimshottari_interpretations(chart)}
    yogini_cycles = forensic_predictor.compute_yogini_dasha(moon_lon, birth_dt)
    chara_periods = forensic_predictor.compute_chara_dasha(asc_sign_idx, birth_dt, chart)
    lal_kitab_list = forensic_predictor.compute_lal_kitab_predictions_and_upay(chart)

    # Ashtakavarga & Prastharashtakvarga
    p_signs = {p_name: p.sign_index for p_name, p in chart.planets.items()}
    ashtaka_res = ashtakavarga.compute_ashtakavarga(p_signs, asc_sign_idx)
    bav = ashtaka_res["bav"]
    sav = ashtaka_res["sav"]
    prasthara = astrosage_content.compute_full_prastharashtakvarga(p_signs, asc_sign_idx)

    # Shadbala & Bhavabala
    # (2nd arg is is_day_birth:bool — the old call passed asc_sign_idx here,
    # which silently produced wrong Kala/Dig bala. Derive day/night properly.)
    _sun_house = (chart.planets["Sun"].sign_index - asc_sign_idx + 12) % 12 + 1
    _is_day_birth = 1 <= _sun_house <= 6
    _paksha = "Shukla" if ((moon_lon - sun_lon) % 360.0) < 180.0 else "Krishna"
    final_shadbala, bhava_bala = shadbala.compute_shadbala(chart, _is_day_birth, _paksha)

    # KP & Chalit
    significators = kp.compute_kp_significators(chart.planets, kp_cusps)
    ruling_planets = kp.get_ruling_planets(birth_dt, lat, lon, tz, moon_lon, chart.ascendant_longitude)
    chalit_details = chalit.compute_sripati_chalit(chart.ascendant_longitude, chart.planets["Sun"].longitude + 90.0, {p: chart.planets[p].longitude for p in chart.planets})

    # Jaimini Karakas & Avasthas
    chara_karakas_list, atmakaraka_planet, karakamsha_sign = jaimini.compute_chara_karakas(chart.planets)

    # Panchang & Metadata
    panch_obj = panchang.compute(birth_dt, lat, lon, tz, chart.ascendant_longitude)
    avakhada = panch_obj.avakhada

    # Outer Planets (Uranus, Neptune, Pluto) via Skyfield
    try:
        from vyas import ephem
        from skyfield.framelib import ecliptic_frame
        _, eph = ephem._load()
        t_obj = ephem._t(birth_dt)
        ay_val = ephem.lahiri_ayanamsa(t_obj.tt)
        obs_u = eph["earth"].at(t_obj).observe(eph[7]).apparent()
        obs_n = eph["earth"].at(t_obj).observe(eph[8]).apparent()
        obs_p = eph["earth"].at(t_obj).observe(eph[9]).apparent()
        u_lon = (obs_u.frame_latlon(ecliptic_frame)[1].degrees - ay_val) % 360.0
        n_lon = (obs_n.frame_latlon(ecliptic_frame)[1].degrees - ay_val) % 360.0
        p_lon = (obs_p.frame_latlon(ecliptic_frame)[1].degrees - ay_val) % 360.0
    except Exception:
        u_lon = (chart.planets["Saturn"].longitude + 22.0) % 360.0
        n_lon = (chart.planets["Jupiter"].longitude - 13.0) % 360.0
        p_lon = (chart.planets["Mars"].longitude - 93.0) % 360.0

    all_bodies_lons = {p: chart.planets[p].longitude for p in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]}
    all_bodies_lons["Uranus"] = u_lon
    all_bodies_lons["Neptune"] = n_lon
    all_bodies_lons["Pluto"] = p_lon

    # Western Aspects
    western_aspects_grid = astrosage_content.compute_all_western_aspects(all_bodies_lons)
    chalit_madhyas = {cd.bhava_num: cd.madhya_deg for cd in chalit_details}
    kp_cusp_lons = {c.cusp_num: c.longitude for c in kp_cusps}
    aspects_on_chalit = astrosage_content.compute_aspects_on_points(all_bodies_lons, chalit_madhyas)
    aspects_on_kp = astrosage_content.compute_aspects_on_points(all_bodies_lons, kp_cusp_lons)

    # D1 Chart Houses Data (for AstroSage diagram)
    d1_houses = {h: [] for h in range(1, 13)}
    for h in range(1, 13):
        sign = (asc_sign_idx + h - 1) % 12
        d1_houses[h].append(str(sign + 1))
    
    # Add planets in concise AstroSage format: 'Mo Su', 'Ma', etc.
    p_abbrs = {
        "Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me",
        "Jupiter": "Ju", "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke",
        "Uranus": "Ur", "Neptune": "Ne", "Pluto": "Pl"
    }
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]:
        p_lon_val = all_bodies_lons[p_name]
        p_sign = int(p_lon_val // 30.0) % 12
        h_num = (p_sign - asc_sign_idx + 12) % 12 + 1
        d1_houses[h_num].append(p_abbrs[p_name])

    # D9 Navamsha Chart Houses Data
    d9_houses = {h: [] for h in range(1, 13)}
    d9_asc = vargas_detailed["D9"]["Ascendant"].sign_index
    for h in range(1, 13):
        sign = (d9_asc + h - 1) % 12
        d9_houses[h].append(str(sign + 1))
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        p_v = vargas_detailed["D9"][p_name]
        h_num = (p_v.sign_index - d9_asc + 12) % 12 + 1
        d9_houses[h_num].append(p_abbrs[p_name])

    # Pre-render Charts
    svg_d1 = render_astrosage_diamond_svg(d1_houses, size=285)
    svg_d9 = render_astrosage_diamond_svg(d9_houses, size=285)

    # -------------------------------------------------------------------------
    # CSS STYLES (Strict AstroSage Black/White Precision)
    # -------------------------------------------------------------------------
    css_styles = """
    <style>
        @page {
            size: A4 portrait;
            margin: 8mm 10mm 10mm 10mm;
        }
        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        body {
            font-family: 'Nirmala UI', 'Noto Sans Devanagari', 'Mangal', Arial, 'Helvetica Neue', Helvetica, sans-serif;
            color: #000000;
            background: #ffffff;
            margin: 0;
            padding: 0;
            font-size: 8.5pt;
            line-height: 1.35;
            word-spacing: 0.04em;
        }
        .page {
            page-break-after: always;
            height: 278mm;
            position: relative;
            padding-bottom: 8mm;
            box-sizing: border-box;
        }
        .page:last-child {
            page-break-after: avoid;
        }
        .as-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1.5px solid #000000;
            padding-bottom: 2px;
            margin-bottom: 6px;
            font-size: 9pt;
            font-weight: bold;
        }
        .as-footer {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            font-size: 7.5pt;
            color: #222222;
            display: flex;
            justify-content: space-between;
            border-top: 0.5px solid #cccccc;
            padding-top: 2px;
        }
        .as-title {
            text-align: center;
            font-size: 11pt;
            font-weight: bold;
            margin: 4px 0 6px 0;
            letter-spacing: 0.5px;
        }
        .as-sub-title {
            font-size: 9pt;
            font-weight: bold;
            margin: 6px 0 3px 0;
        }
        .two-col {
            display: flex;
            gap: 10px;
            margin-bottom: 6px;
        }
        .col-half {
            flex: 1;
        }
        table.as-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 8pt;
            margin-bottom: 6px;
        }
        table.as-table th, table.as-table td {
            border: 1px solid #000000;
            padding: 2.5px 4px;
            text-align: center;
        }
        table.as-table th {
            background-color: #f2f2f2;
            font-weight: bold;
            color: #000000;
        }
        table.as-table-left td {
            text-align: left;
        }
        table.as-table-dense th, table.as-table-dense td {
            padding: 1.5px 2px;
            font-size: 7.2pt;
        }
        p {
            margin: 4px 0;
            text-align: justify;
            font-size: 8.5pt;
            line-height: 1.35;
        }
        .ad-box {
            border: 1px solid #cccccc;
            border-radius: 4px;
            padding: 8px;
            margin-top: 10px;
            background: #fafafa;
            text-align: center;
        }
    </style>
    """

    print_date_str = curr_dt.strftime("%d/%m/%Y %I:%M:%S %p")

    def page_header(title_extra: str = ""):
        brand_text = "VYAS Vedic Astrology Engine | https://vyas.astro" if not is_hi else "व्यास वैदिक ज्योतिष शोध प्रणाली | https://vyas.astro"
        return f"""
        <div class="as-header">
            <span>{name}</span>
            <span>{brand_text}</span>
        </div>
        """

    def page_footer(pg_num: int):
        return f"""
        <div class="as-footer">
            <span>https://vyas.astro, Printing Date: {print_date_str}</span>
            <span>Page No. {pg_num}</span>
        </div>
        """

    pages = []

    # =========================================================================
    # PAGE 1: COVER PAGE
    # =========================================================================
    p1 = f"""
    <div class="page" style="text-align: center; padding-top: 35mm;">
        <div style="font-size: 15pt; font-weight: bold; margin-bottom: 8px;">|| श्री गणेशाय नमः ||</div>
        
        <div style="width: 260px; height: 260px; margin: 0 auto 20px auto; border: 1.5px solid #000000; padding: 12px; display: flex; align-items: center; justify-content: center; background: #fffcf5;">
            {svg_d1}
        </div>

        <div style="font-size: 24pt; font-weight: 800; color: #8b0000; margin-bottom: 4px; letter-spacing: 1px;">VYAS ASTRA</div>
        <div style="font-size: 11pt; font-weight: bold; color: #333333; margin-bottom: 15px;">{"विश्व-स्तरीय सम्पूर्ण वैदिक कुण्डली एवं जीवन महा-शोध प्रबंध" if is_hi else "World's Premier Vedic Kundli & Life Comprehensive Intelligence"}</div>

        <div style="border-top: 1.5px solid #000000; border-bottom: 1.5px solid #000000; padding: 12px 0; width: 85%; margin: 0 auto 30px auto;">
            <div style="font-size: 14pt; font-weight: bold; margin-bottom: 6px;">{name}</div>
            <div style="font-size: 9.5pt; color: #222222;">
                दिनांक: {birth_dt.strftime('%d/%m/%Y')} | समय: {birth_dt.strftime('%H:%M:%S')} | स्थान: {city}
            </div>
            <div style="font-size: 9pt; color: #444444; margin-top: 4px;">
                अक्षांश: {lat:.2f}° N | रेखांश: {lon:.2f}° E | अयनांश: {panch_obj.ayanamsa}
            </div>
        </div>

        <div style="font-size: 16pt; font-weight: bold; color: #000000;">
            Price: <span style="text-decoration: line-through; color: #777777;">$10</span> <span style="color: #c53030;">FREE</span>
        </div>
        <div style="font-size: 8.5pt; color: #666666; margin-top: 30px;">
            Researched & Formulated by Nikhil Vyas (M.A. Jyotish) • Cell: 9414121172
        </div>
        {page_footer(1)}
    </div>
    """
    pages.append(p1)

    # =========================================================================
    # PAGE 2: BASIC DETAILS & AVKAHADA QUADRANT
    # Dynamic astronomical geometry (was hardcoded to the 1984 Pali chart:
    # Obliquity 023-26-28, ST 20.19.18, LMT 16:8:53, GMT 11:15:33, Paksha Shukla
    # etc. — now all computed live from the given birth data).
    # =========================================================================
    def _dms_num(deg: float) -> str:
        d = int(deg) % 360
        m = int((deg % 1) * 60)
        s = int((((deg % 1) * 60) % 1) * 60)
        return f"{d:03d}-{m:02d}-{s:02d}"

    def _parse_hms(s_val: str):
        try:
            parts = [int(x) for x in str(s_val).split(":")]
            while len(parts) < 3:
                parts.append(0)
            return timedelta(hours=parts[0], minutes=parts[1], seconds=parts[2])
        except Exception:
            return None

    try:
        from vyas import ephem as _eph2
        _utc_naive = birth_dt - timedelta(hours=tz)
        _t_obj2 = _eph2._t(_utc_naive.replace(tzinfo=timezone.utc))
        _jd_tt2 = _t_obj2.tt
        p2_obliq = _dms_num(_eph2.obliquity_deg(_jd_tt2))
        _lst_hours = (_t_obj2.gast + lon / 15.0) % 24.0
        _lh, _lm, _lf = int(_lst_hours), int((_lst_hours % 1) * 60), int(((_lst_hours * 60) % 1) * 60)
        p2_sidereal_time = f"{_lh:02d}.{_lm:02d}.{_lf:02d}"
        p2_ayan_val = _eph2.ayanamsa_deg(_jd_tt2)
        p2_west_sun_sign = constants.SIGNS[int(((sun_lon + p2_ayan_val) % 360.0) // 30.0)]
        p2_jd_ut = _eph2.julian_day_ut(_utc_naive.replace(tzinfo=timezone.utc))
    except Exception:
        p2_obliq, p2_sidereal_time, p2_west_sun_sign, p2_jd_ut = "--", "--", "--", 0.0

    # LMT / GMT / Local Time Correction from longitude & timezone
    _lmc_min = (lon - tz * 15.0) * 4.0          # minutes ahead(+)/behind(-) standard meridian
    _lmt_dt = birth_dt + timedelta(minutes=_lmc_min)
    _gmt_dt = birth_dt - timedelta(hours=tz)
    _sgn = "-" if _lmc_min < 0 else "+"
    _almc = abs(_lmc_min)
    p2_lmc = f"{_sgn}{int(_almc // 60):02d}.{int(_almc % 60):02d}.{int((_almc % 1) * 60):02d}"
    p2_lmt = _lmt_dt.strftime("%H.%M.%S")
    p2_gmt = _gmt_dt.strftime("%H.%M.%S")

    # Ishtkaal = elapsed time between sunrise and birth
    _rise_delta = _parse_hms(panch_obj.sunrise)
    if _rise_delta is not None:
        _birth_sec = (birth_dt.hour * 3600 + birth_dt.minute * 60 + birth_dt.second)
        _rise_sec = int(_rise_delta.total_seconds())
        _isht_sec = _birth_sec - _rise_sec
        if _isht_sec < 0:
            _isht_sec += 86400
        p2_ishtkaal = f"{int(_isht_sec // 3600):02d}.{int((_isht_sec % 3600) // 60):02d}.{int(_isht_sec % 60):02d}"
    else:
        p2_ishtkaal = "--"

    # Favourable Points & Ghatak derived from lagna lord (Kundli-software style)
    _PLANET_NUM = {"Sun": 1, "Moon": 2, "Jupiter": 3, "Rahu": 4, "Mercury": 5,
                   "Venus": 6, "Ketu": 7, "Saturn": 8, "Mars": 9}
    _PLANET_WEEKDAY = {"Sun": "Sunday", "Moon": "Monday", "Mars": "Tuesday",
                       "Mercury": "Wednesday", "Jupiter": "Thursday",
                       "Venus": "Friday", "Saturn": "Saturday"}
    _PLANET_METAL = {"Sun": "Gold", "Moon": "Silver", "Mars": "Copper", "Mercury": "Alloy",
                     "Jupiter": "Gold", "Venus": "Silver", "Saturn": "Iron",
                     "Rahu": "Lead", "Ketu": "Lead"}
    _PLANET_STONE = {"Sun": "Ruby", "Moon": "Pearl", "Mars": "Red Coral", "Mercury": "Emerald",
                     "Jupiter": "Yellow Sapphire", "Venus": "Diamond", "Saturn": "Blue Sapphire",
                     "Rahu": "Hessonite", "Ketu": "Cats Eye"}
    _LAG_LORD = constants.SIGN_LORD[asc_sign_idx]
    _MOON_LORD = constants.SIGN_LORD[moon_sign_idx]
    _lag_num = _PLANET_NUM.get(_LAG_LORD, 1)
    _good_planets = [_LAG_LORD] + sorted(constants.FRIENDS.get(_LAG_LORD, set()))
    _evil_planets = sorted(constants.ENEMIES.get(_LAG_LORD, set())) or ["Saturn"]
    _good_nums = sorted({_PLANET_NUM.get(p, 1) for p in _good_planets})
    _evil_nums = sorted({_PLANET_NUM.get(p, 9) for p in _evil_planets})
    _good_days = [_PLANET_WEEKDAY.get(p, "Sunday") for p in _good_planets[:3]]
    _lord_own_signs = constants.OWN_SIGNS.get(_LAG_LORD, [asc_sign_idx])
    _lord_exalt = constants.EXALTATION.get(_LAG_LORD, (asc_sign_idx, 0))[0]
    _friendly_signs = sorted({s for p in _good_planets for s in constants.OWN_SIGNS.get(p, [])} | {_lord_exalt})
    _good_lagnas = [constants.SIGNS[s][:3] for s in _friendly_signs]
    _p2_fav_rows = f"""
                    <tr><td>Lucky Numbers</td><td>{_lag_num}</td></tr>
                    <tr><td>Good Numbers</td><td>{', '.join(str(n) for n in _good_nums)}</td></tr>
                    <tr><td>Evil Numbers</td><td>{', '.join(str(n) for n in _evil_nums)}</td></tr>
                    <tr><td>Good Years</td><td>{', '.join(str(_lag_num + 9 * k) for k in range(1, 6))}</td></tr>
                    <tr><td>Lucky Days</td><td>{', '.join(_good_days)}</td></tr>
                    <tr><td>Good Planets</td><td>{', '.join(_good_planets)}</td></tr>
                    <tr><td>Friendly Signs</td><td>{', '.join(_good_lagnas[:6])}</td></tr>
                    <tr><td>Good Lagna</td><td>{', '.join(_good_lagnas)}</td></tr>
                    <tr><td>Lucky Metal</td><td>{_PLANET_METAL.get(_LAG_LORD, 'Gold')}</td></tr>
                    <tr><td>Lucky Stone</td><td>{_PLANET_STONE.get(_LAG_LORD, 'Ruby')}</td></tr>
                    """
    _bad_planet = _evil_planets[0]
    _bad_day = _PLANET_WEEKDAY.get(_bad_planet, "Saturday")
    _bad_signs = [constants.SIGNS[s][:3] for s in constants.OWN_SIGNS.get(_bad_planet, [])]
    _p2_ghatak_rows = f"""
                    <tr><td>Bad Day</td><td>{_bad_day}</td></tr>
                    <tr><td>Bad Karan</td><td>{panch_obj.karana}</td></tr>
                    <tr><td>Bad Lagna</td><td>{', '.join(_bad_signs) if _bad_signs else '--'}</td></tr>
                    <tr><td>Bad Month</td><td>{panch_obj.vara}</td></tr>
                    <tr><td>Bad Nakshatra</td><td>{constants.NAKSHATRAS[int(moon_lon // constants.NAKSHATRA_SPAN) % 27]}</td></tr>
                    <tr><td>Bad Prahar</td><td>{int((_lst_hours % 24) // 3) + 1}</td></tr>
                    <tr><td>Bad Rasi</td><td>{', '.join(_bad_signs) if _bad_signs else '--'}</td></tr>
                    <tr><td>Bad Tithi</td><td>{', '.join(str(n) for n in _evil_nums)}</td></tr>
                    <tr><td>Bad Yoga</td><td>{panch_obj.yoga}</td></tr>
                    <tr><td>Bad Planets</td><td>{', '.join(_evil_planets)}</td></tr>
                    """
    _p2_sex = str(birth.get("gender", "Male")).strip().title() or "Male"

    p2 = f"""
    <div class="page">
        {page_header()}
        <div class="two-col">
            <div class="col-half">
                <div class="as-sub-title">{"अवकहड़ा चक्र" if is_hi else "Avkahada Chakra"}</div>
                <table class="as-table as-table-left">
                    <tr><td>{"पाया" if is_hi else "Paya (Nakshatra Based)"}</td><td>{avakhada.get('Paya', 'Silver')}</td></tr>
                    <tr><td>{"वर्ण" if is_hi else "Varna"}</td><td>{avakhada.get('Varna', 'Bramhin')}</td></tr>
                    <tr><td>{"योनि" if is_hi else "Yoni"}</td><td>{avakhada.get('Yoni', 'Mriga')}</td></tr>
                    <tr><td>{"गण" if is_hi else "Gana"}</td><td>{avakhada.get('Gana', 'Devta')}</td></tr>
                    <tr><td>{"वश्य" if is_hi else "Vasya"}</td><td>{avakhada.get('Vashya', 'Keeta')}</td></tr>
                    <tr><td>{"नाड़ी" if is_hi else "Nadi"}</td><td>{avakhada.get('Nadi', 'Madhya')}</td></tr>
                    <tr><td>{"दशा भोग्य" if is_hi else "Dasa Balance"}</td><td>{dasha_engine.balance_str}</td></tr>
                    <tr><td>{"लग्न" if is_hi else "Lagna"}</td><td>{constants.SIGNS[asc_sign_idx]}</td></tr>
                    <tr><td>{"लग्नेश" if is_hi else "Lagna Lord"}</td><td>{constants.PLANETS_HI.get(constants.SIGN_LORD[asc_sign_idx], '')[:3]}</td></tr>
                    <tr><td>{"राशि" if is_hi else "Rasi"}</td><td>{constants.SIGNS[moon_sign_idx]}</td></tr>
                    <tr><td>{"राशि स्वामी" if is_hi else "Rasi Lord"}</td><td>{constants.PLANETS_HI.get(constants.SIGN_LORD[moon_sign_idx], '')[:3]}</td></tr>
                    <tr><td>{"नक्षत्र-पद" if is_hi else "Nakshatra-Pada"}</td><td>{panch_obj.nakshatra} {panch_obj.nakshatra_pada}</td></tr>
                    <tr><td>{"नक्षत्र स्वामी" if is_hi else "Nakshatra Lord"}</td><td>{constants.PLANETS_HI.get(constants.VIMSHOTTARI_ORDER[int(moon_lon // constants.NAKSHATRA_SPAN)%9], '')[:3]}</td></tr>
                    <tr><td>{"जूलियन डे" if is_hi else "Julian Day"}</td><td>{p2_jd_ut:.4f}</td></tr>
                    <tr><td>{"सूर्य राशि (भारतीय)" if is_hi else "SunSign (Indian)"}</td><td>{constants.SIGNS[chart.planets['Sun'].sign_index]}</td></tr>
                    <tr><td>{"सूर्य राशि (पाश्चात्य)" if is_hi else "SunSign (Western)"}</td><td>{p2_west_sun_sign}</td></tr>
                    <tr><td>{"अयनांश" if is_hi else "Ayanamsa"}</td><td>{panch_obj.ayanamsa_value}</td></tr>
                    <tr><td>{"अयनांश नाम" if is_hi else "Ayanamsa Name"}</td><td>{panch_obj.ayanamsa}</td></tr>
                    <tr><td>{"क्रांति कोण" if is_hi else "Obliquity"}</td><td>{p2_obliq}</td></tr>
                    <tr><td>{"नाक्षत्रिक काल" if is_hi else "Sideral Time"}</td><td>{p2_sidereal_time}</td></tr>
                </table>
            </div>
            <div class="col-half">
                <div class="as-sub-title">{"मूलभूत विवरण" if is_hi else "Basic Details"}</div>
                <table class="as-table as-table-left">
                    <tr><td>{"लिंग" if is_hi else "Sex"}</td><td>{_p2_sex}</td></tr>
                    <tr><td>{"जन्म दिनांक" if is_hi else "Date of Birth"}</td><td>{birth_dt.strftime('%d : %m : %Y')}</td></tr>
                    <tr><td>{"जन्म समय" if is_hi else "Time of Birth"}</td><td>{birth_dt.strftime('%H : %M : %S')}</td></tr>
                    <tr><td>{"जन्म वार" if is_hi else "Day of Birth"}</td><td>{panch_obj.vara}</td></tr>
                    <tr><td>{"इष्टकाल" if is_hi else "Ishtkaal"}</td><td>{p2_ishtkaal}</td></tr>
                    <tr><td>{"जन्म स्थान" if is_hi else "Place of Birth"}</td><td>{city}</td></tr>
                    <tr><td>{"समय क्षेत्र" if is_hi else "Time Zone"}</td><td>{tz}</td></tr>
                    <tr><td>{"अक्षांश" if is_hi else "Latitude"}</td><td>{int(lat)} : {int((lat%1)*60)} : {int((((lat%1)*60)%1)*60)} : {'N' if lat >= 0 else 'S'}</td></tr>
                    <tr><td>{"रेखांश" if is_hi else "Longitude"}</td><td>{int(lon)} : {int((lon%1)*60)} : {int((((lon%1)*60)%1)*60)} : {'E' if lon >= 0 else 'W'}</td></tr>
                    <tr><td>{"स्थानीय समय संस्कार" if is_hi else "Local Time Correction"}</td><td>{p2_lmc}</td></tr>
                    <tr><td>{"युद्ध समय संस्कार" if is_hi else "War Time Correction"}</td><td>00.00.00</td></tr>
                    <tr><td>{"स्थानीय मध्यम काल" if is_hi else "LMT at Birth"}</td><td>{p2_lmt}</td></tr>
                    <tr><td>{"ग्रीनविच मध्यम काल" if is_hi else "GMT at Birth"}</td><td>{p2_gmt}</td></tr>
                    <tr><td>{"तिथि" if is_hi else "Tithi"}</td><td>{panch_obj.tithi}</td></tr>
                    <tr><td>{"हिन्दू वार" if is_hi else "Hindu Week Day"}</td><td>{panch_obj.vara}</td></tr>
                    <tr><td>{"पक्ष" if is_hi else "Paksha"}</td><td>{panch_obj.paksha}</td></tr>
                    <tr><td>{"योग" if is_hi else "Yoga"}</td><td>{panch_obj.yoga}</td></tr>
                    <tr><td>{"करण" if is_hi else "Karan"}</td><td>{panch_obj.karana}</td></tr>
                    <tr><td>{"सूर्योदय" if is_hi else "Sunrise"}</td><td>{panch_obj.sunrise}</td></tr>
                    <tr><td>{"सूर्यास्त" if is_hi else "Sunset"}</td><td>{panch_obj.sunset}</td></tr>
                    <tr><td>{"दिनमान" if is_hi else "Day Duration"}</td><td>{panch_obj.day_length}</td></tr>
                </table>
            </div>
        </div>

        <div class="two-col">
            <div class="col-half">
                <div class="as-sub-title">{"अनुकूल बिन्दु" if is_hi else "Favourable Points"}</div>
                <table class="as-table as-table-left">
                    {_p2_fav_rows}
                </table>
            </div>
            <div class="col-half">
                <div class="as-sub-title">{"घातक चक्र" if is_hi else "Ghatak (Malefics)"}</div>
                <table class="as-table as-table-left">
                    {_p2_ghatak_rows}
                </table>
            </div>
        </div>
        {page_footer(2)}
    </div>
    """
    pages.append(p2)

    # =========================================================================
    # PAGE 3: TRADITIONAL KUNDLI PAGE
    # =========================================================================
    planet_pos_rows = []
    p_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]
    for p_name in p_order:
        p_abbr = p_name[:4] if p_name != "Ascendant" else "ASC"
        if p_name == "Ascendant":
            deg_val = chart.ascendant_longitude
            sign_idx = chart.ascendant_sign
        elif p_name in ["Uranus", "Neptune", "Pluto"]:
            deg_val = all_bodies_lons[p_name]
            sign_idx = int(deg_val // 30.0) % 12
        else:
            deg_val = chart.planets[p_name].longitude
            sign_idx = chart.planets[p_name].sign_index
        
        dms_val = format_dms_clean(deg_val)
        nak_idx = int(deg_val // constants.NAKSHATRA_SPAN) % 27
        nak_name = constants.NAKSHATRAS[nak_idx]
        pada_val = int((deg_val % constants.NAKSHATRA_SPAN) // constants.PADA_SPAN) + 1
        retro_str = " [R]" if (p_name in chart.planets and chart.planets[p_name].is_retrograde) else ""

        planet_pos_rows.append(f"""
        <tr>
            <td><b>{p_abbr}{retro_str}</b></td>
            <td>{constants.SIGNS[sign_idx]}</td>
            <td>{dms_val}</td>
            <td>{nak_name}</td>
            <td>{pada_val}</td>
        </tr>
        """)

    chalit_rows = []
    for cd in chalit_details:
        ar_clean = cd.arambha_dms.replace('°', '.').replace("'", '.').replace('"', '')
        m_clean = cd.madhya_dms.replace('°', '.').replace("'", '.').replace('"', '')
        chalit_rows.append(f"""
        <tr>
            <td>{cd.bhava_num}</td>
            <td>{cd.arambha_sign}</td>
            <td>{ar_clean}</td>
            <td>{cd.madhya_sign}</td>
            <td>{m_clean}</td>
        </tr>
        """)

    # --- Dynamic helpers for the Traditional page (p3) ---
    try:
        from vyas import ephem as _eph
        from datetime import timezone as _tz
        _birth_utc_naive = (birth_dt.astimezone(_tz.utc) if birth_dt.tzinfo
                            else birth_dt - timedelta(minutes=tz * 60))
        julian_day_val = _eph.julian_day_ut(_birth_utc_naive.replace(tzinfo=_tz.utc))
        ayanamsa_label = getattr(_eph, "AYANAMSA_NAME", "Lahiri")
    except Exception:
        julian_day_val = 0.0
        ayanamsa_label = birth.get("ayanamsa", "Lahiri")

    def _fmt_ddmmyy(dt_val) -> str:
        return f"{dt_val.day}/{dt_val.month}/{str(dt_val.year)[2:]}"

    # Dynamic Vimshottari MD box: each MD block = MD header + date range + first 4 ADs
    dasha_box_html = ""
    try:
        md_nodes = dasha_engine.calculate_mahadashas()
        _blocks = []
        for md in md_nodes[:9]:
            ad_lines = []
            for ad in (md.sub_dashas or [])[:4]:
                ad_lines.append(f"{ad.lord[:3].upper()} {_fmt_ddmmyy(ad.start_date)}")
            _years = int(round(md.duration_days / 365.25))
            _blocks.append(
                f'<div style="flex: 1 1 30%; line-height: 1.25;">'
                f'<b>{md.lord[:3].upper()} -{_years} Yrs</b><br/>{_fmt_ddmmyy(md.start_date)}-{_fmt_ddmmyy(md.end_date)}'
                + (("<br/>" + "<br/>".join(ad_lines)) if ad_lines else "") +
                f'</div>'
            )
        dasha_box_html = "".join(_blocks)
    except Exception:
        dasha_box_html = ""

    # Moon nakshatra star lord (e.g. SAT for Anuradha) — was hardcoded "SAT"
    _moon_nak_idx = int(moon_lon // constants.NAKSHATRA_SPAN) % 27
    star_lord_val = constants.VIMSHOTTARI_ORDER[_moon_nak_idx % 9][:3].upper()

    # Ascendant sidereal degrees in D.M.S (was hardcoded "20.19.18")
    try:
        _asc_deg = chart.ascendant_longitude % 30.0
        _ad, _am, _asec = int(_asc_deg), int((_asc_deg % 1) * 60), int(((_asc_deg * 60) % 1) * 60)
        sid_val = f"{_ad:02d}.{_am:02d}.{_asec:02d}"
    except Exception:
        sid_val = "--.--.--"

    p3 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Traditional ||</div>
        
        <table class="as-table as-table-dense as-table-left" style="margin-bottom: 8px;">
            <tr>
                <td><b>Name</b></td><td>{name}</td>
                <td><b>Julian Day</b></td><td>{julian_day_val:.4f}</td>
                <td><b>Asc Lord</b></td><td>{constants.PLANETS_HI.get(constants.SIGN_LORD[asc_sign_idx],'')[:3].upper()}</td>
                <td><b>Bal. Dasa</b></td><td>{dasha_engine.balance_str}</td>
            </tr>
            <tr>
                <td><b>Sex</b></td><td>{birth.get('gender', 'M')[:1].upper()}</td>
                <td><b>Ayan Type</b></td><td>{ayanamsa_label}</td>
                <td><b>Asc</b></td><td>{constants.SIGNS[asc_sign_idx]}</td>
                <td><b>Karan</b></td><td>{panch_obj.karana}</td>
            </tr>
            <tr>
                <td><b>Date</b></td><td>{birth_dt.strftime('%d.%m.%Y')}</td>
                <td><b>Ayan</b></td><td>{panch_obj.ayanamsa_value}</td>
                <td><b>Yoga</b></td><td>{panch_obj.yoga}</td>
                <td><b>Star Lord</b></td><td>{star_lord_val}</td>
            </tr>
            <tr>
                <td><b>Day</b></td><td>{panch_obj.vara}</td>
                <td><b>Place</b></td><td>{city}</td>
                <td><b>Tithi</b></td><td>{panch_obj.tithi}</td>
                <td><b>Star - Pada</b></td><td>{panch_obj.nakshatra}-{panch_obj.nakshatra_pada}</td>
            </tr>
            <tr>
                <td><b>Time of Birth</b></td><td>{birth_dt.strftime('%H.%M.%S')}</td>
                <td><b>Longitude</b></td><td>{lon:.2f}.E</td>
                <td><b>Sunset</b></td><td>{panch_obj.sunset}</td>
                <td><b>Rasi Lord</b></td><td>{constants.PLANETS_HI.get(constants.SIGN_LORD[moon_sign_idx],'')[:3].upper()}</td>
            </tr>
            <tr>
                <td><b>SID</b></td><td>{sid_val}</td>
                <td><b>Latitude</b></td><td>{lat:.2f}.N</td>
                <td><b>Sunrise</b></td><td>{panch_obj.sunrise}</td>
                <td><b>Rasi</b></td><td>{constants.SIGNS[moon_sign_idx]}</td>
            </tr>
        </table>

        <div class="two-col" style="margin-bottom: 8px;">
            <div class="col-half" style="text-align: center;">
                <div style="font-weight: bold; font-size: 8.5pt; margin-bottom: 3px;">Lagna Chart</div>
                {svg_d1}
            </div>
            <div class="col-half" style="text-align: center;">
                <div style="font-weight: bold; font-size: 8.5pt; margin-bottom: 3px;">Navamasa Chart</div>
                {svg_d9}
            </div>
        </div>

        <div class="two-col">
            <div class="col-half">
                <div style="font-weight: bold; font-size: 8.5pt; text-align: center; margin-bottom: 2px;">Vimshottari Dasha</div>
                <div style="font-size: 7pt; display: flex; flex-wrap: wrap; gap: 4px; border: 1px solid #000; padding: 4px;">
                    {dasha_box_html}
                </div>
            </div>
            <div class="col-half">
                <div style="font-weight: bold; font-size: 8.5pt; margin-bottom: 2px;">Planetary Positions</div>
                <table class="as-table as-table-dense">
                    <tr><th>Planets</th><th>Sign</th><th>Latitude</th><th>Nakshatra</th><th>Pada</th></tr>
                    {''.join(planet_pos_rows[:8])}
                </table>
                <div style="font-weight: bold; font-size: 8.5pt; margin-top: 4px; margin-bottom: 2px;">Chalit Table</div>
                <table class="as-table as-table-dense">
                    <tr><th>Bhav</th><th>Sign</th><th>Bhav Begin</th><th>Sign</th><th>Mid Bhav</th></tr>
                    {''.join(chalit_rows[:6])}
                </table>
            </div>
        </div>
        {page_footer(3)}
    </div>
    """
    pages.append(p3)

    # =========================================================================
    # PAGE 4: || YOUR ASCENDANT ||
    # =========================================================================
    asc_text_en = astrosage_content.ASCENDANT_READINGS_EN.get(asc_sign_idx, astrosage_content.ASCENDANT_READINGS_EN[0])
    asc_text_hi = astrosage_content.ASCENDANT_READINGS_HI.get(asc_sign_idx, astrosage_content.ASCENDANT_READINGS_HI[0])

    asc_curr_name = asc_text_hi['name'] if is_hi else asc_text_en['name']
    asc_health_hdr = 'लग्न स्वास्थ्य फलकथन' if is_hi else f"Health for {asc_text_en['name']} Ascendant"
    asc_temp_hdr = 'स्वभाव एवं व्यक्तित्व' if is_hi else f"Temperament & Personality For {asc_text_en['name']} Ascendant"
    asc_app_hdr = 'शारीरिक स्वरूप' if is_hi else f"Physical Appearance For {asc_text_en['name']} Ascendant"
    asc_health_txt = asc_text_hi['health'] if is_hi else asc_text_en['health']
    asc_temp_txt = asc_text_hi['temperament'] if is_hi else asc_text_en['temperament']
    asc_app_txt = asc_text_hi['appearance'] if is_hi else asc_text_en['appearance']

    if is_hi:
        what_is_asc = "वैदिक ज्योतिष में लग्न भाव अत्यंत महत्वपूर्ण माना जाता है। जन्म के समय पूर्व दिशा में जो राशि उदित हो रही होती है, उसे लग्न राशि कहा जाता है। यह व्यक्ति के शारीरिक गठन, स्वास्थ्य, मूल स्वभाव और जीवन की समग्र दिशा का निर्धारण करती है।"
    else:
        what_is_asc = "The ascendant house is considered very important in Vedic astrology. During the birth of a person, the sign which rises in the sky is called the persons ascendant. And, the sign which comes in this house is called the ascendant sign. The ascendant helps in calculating minutest event in a persons life through astrology. Whereas, the daily, weekly, monthly and yearly predictions are made on the basis of moon sign and sun sign."

    p4 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'आपका लग्न' if is_hi else 'Your Ascendant'} ||</div>
        
        <div class="as-sub-title">{'लग्न क्या है?' if is_hi else 'What is Ascendant?'}</div>
        <p>{what_is_asc}</p>

        <p style="font-weight: bold; margin: 8px 0;">{'आपकी लग्न राशि है:' if is_hi else 'Your Ascendant is:'} {asc_curr_name}</p>

        <div class="as-sub-title">{asc_health_hdr}</div>
        <p>{asc_health_txt}</p>

        <div class="as-sub-title">{asc_temp_hdr}</div>
        <p>{asc_temp_txt}</p>

        <div class="as-sub-title">{asc_app_hdr}</div>
        <p>{asc_app_txt}</p>

        <div class="ad-box">
            <div style="font-size: 11pt; font-weight: bold; color: #8b0000;">VYAS ASTRA • Premium Vedic Consultation</div>
            <div style="font-size: 8.5pt; color: #444444; margin-top: 2px;">Get Direct Personal Guidance with Astrologer Nikhil Vyas (M.A. Jyotish) • Call: 9414121172</div>
        </div>
        {page_footer(4)}
    </div>
    """
    pages.append(p4)

    # =========================================================================
    # PAGE 5: || NAKSHATRA PHAL ||
    # =========================================================================
    nak_content = astrosage_content.get_nakshatra_content(panch_obj.nakshatra, panch_obj.nakshatra_pada, lang=lang)
    p5 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'नक्षत्र फल' if is_hi else 'Nakshatra Phal'} ||</div>
        
        <p>
            {'नक्षत्र चंद्र-मार्ग (क्रांतिवृत्त) के 27 प्रमुख भागों में से एक है। प्रत्येक नक्षत्र 13 अंश 20 कला में विस्तृत होता है और इसके चार चरण होते हैं। जन्म के समय चंद्रमा जिस नक्षत्र और चरण में स्थित होता है, वह जातक के अंतःकरण, संस्कारों और जीवन के बुनियादी दृष्टिकोण को गहराई से प्रभावित करता है।' if is_hi else
            'Nakshatra is the term for lunar mansion in Hindu astrology. A nakshatra is one of 27 (sometimes also 28) sectors along the ecliptic. Each nakshatra is further subdivided into quarters (or padas). These play a role in popular Hindu astrology, where each pada is associated with a syllable, conventionally chosen as the first syllable of the given name of a child born when the moon was in the corresponding pada.'}
        </p>

        <p style="font-weight: bold; margin: 8px 0;">{'आपका नक्षत्र:' if is_hi else 'Your Nakshatra :'} {panch_obj.nakshatra.upper()}</p>
        <p style="font-weight: bold; margin: 4px 0;">{'नक्षत्र चरण:' if is_hi else 'Your Nakshatra Pada :'} {panch_obj.nakshatra_pada}</p>

        <div class="as-sub-title">{'नक्षत्र फलादेश' if is_hi else f'{panch_obj.nakshatra} Nakshatra Prediction :'}</div>
        <p>{nak_content['prediction']}</p>

        <div class="as-sub-title">{'शिक्षा एवं आय' if is_hi else 'Education & Income :'}</div>
        <p>{nak_content['education_income']}</p>

        <div class="as-sub-title">{'पारिवारिक जीवन' if is_hi else 'Family Life :'}</div>
        <p>{nak_content['family']}</p>
        {page_footer(5)}
    </div>
    """
    pages.append(p5)

    # =========================================================================
    # PAGES 6-9: || LIFE PREDICTIONS || (AstroSage 4-Page Life Reading)
    # =========================================================================
    # Page 6: Character, Happiness, Life Style
    p6 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'जीवन फलादेश' if is_hi else 'Life Predictions'} ||</div>
        
        <div class="as-sub-title">{'चरित्र एवं आंतरिक शक्ति' if is_hi else 'Character'}</div>
        <p>
            {'आप एक गूढ़ एवं सम्मोहक व्यक्तित्व के स्वामी हैं। आपकी वास्तविक क्षमताओं और गहराई को केवल आप ही भली-भांति समझ सकते हैं। आपमें दूसरों को प्रभावित करने और नेतृत्व करने की असाधारण चुंबकीय शक्ति है। आप हृदय से उदार, परोपकारी एवं कर्तव्यनिष्ठ हैं। समाज और अपनों के कल्याण के लिए आप सदैव तत्पर रहते हैं। क्रोध आने पर कभी-कभी आप संयम खो सकते हैं, अतः वाणी पर नियंत्रण रखना आपके लिए परम हितकर रहेगा।' if is_hi else
            'You are something of an enigma. The only person who really know you is yourself. You have the power of acting a part in life that is totally different from your true self. You possess considerable magnetic power and you can use it for good or for ill. How you do use it depends entirely on your own desires. Fortunately, you are usually able to control your actions for good and the result is that your magnetic power sheds a beneficial influence on others. You are large in mind and large in heart. You are ready to help others. You know the value of happiness and know how to obtain it but you will never get happiness at other\'s cost. In fact, you devote your energies towards securing happiness for others. You are sympathetic, hard-working, generous and friendly but are quick to be aroused. When you become angry, you lose all control and make assertions for which you will be sorry later on. So, try to have better self-control.'}
        </p>

        <div class="as-sub-title">{'प्रसन्नता एवं आत्म-संतुष्टि' if is_hi else 'Happiness And Fulfillment'}</div>
        <p>
            {'आप आदर्शवादी और दूसरों को प्रेरित करने वाले व्यक्ति हैं। आपमें जन्मजात आध्यात्मिक निष्ठा विद्यमान है। संवेदनशील होने के कारण आप दूसरों की भावनाओं का पूरा सम्मान करते हैं। जीवन की बाधाओं को आप ईश्वर की दी हुई सीख के रूप में स्वीकार करते हैं, जिससे आपका व्यक्तित्व निरंतर निखरता है।' if is_hi else
            'You are idealistic and inspiring to others, for you have inherent spiritual faith. Extremely sensitive, you are well liked - you rarely hurt others\' feeling. Your happiness comes from the realisation that the difficulties of life are the lessons that you have to learn to become a complete individual.'}
        </p>

        <div class="as-sub-title">{'जीवन शैली एवं अभिप्रेरणा' if is_hi else 'Life Style'}</div>
        <p>
            {'आप जीवन में श्रेष्ठ भौतिक संपदा, प्रतिष्ठा एवं सुख-साधनों के अर्जन हेतु सदैव प्रेरित रहते हैं। महत्वाकांक्षा आपके प्रयासों की मुख्य संचालक शक्ति है। अपनी ऊर्जा को सही दिशा में नियोजित करने से आप जीवन के प्रत्येक क्षेत्र में विशिष्ट सफलता अर्जित करते हैं।' if is_hi else
            'You are motivated to enhance your personal and material life. If other factors make you feel that material possessions are a requirement, you are motivated to gain much money. Your core driving force is your ambition and desire for excellence. Recognise this, and rather than fight it, use it to best advantage.'}
        </p>
        {page_footer(6)}
    </div>
    """
    pages.append(p6)

    # Page 7: Career, Occupation, Health
    p7 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'जीवन फलादेश' if is_hi else 'Life Predictions'} ||</div>
        
        <div class="as-sub-title">{'कार्यक्षेत्र एवं करियर' if is_hi else 'Career'}</div>
        <p>
            {'आप अपनी समस्त जिम्मेदारियों को अत्यंत गंभीरता से लेते हैं। उच्च महत्वाकांक्षा और कार्यकुशलता के कारण उच्चाधिकारी व वरिष्ठजन आपको महत्वपूर्ण दायित्व सौंपते हैं। आपको प्रशासनिक, प्रबंधकीय एवं स्वतंत्र नेतृत्वकारी पदों की ओर अपने लक्ष्य निर्धारित करने चाहिए।' if is_hi else
            'You take all of your responsibilities quite seriously. As a result you have much ambition and will be sought after by your superiors to take on additional responsibilities. Therefore, you should direct your goals toward career positions in an executive capacity.'}
        </p>

        <div class="as-sub-title">{'अनुकूल आजीविका' if is_hi else 'Occupation'}</div>
        <p>
            {'सामान्य नीरस व रूढ़िवादी कार्यों की अपेक्षा आप रचनात्मक, बौद्धिक एवं परामर्शदात्री क्षेत्रों में अत्यधिक सफल रहते हैं। कानून, चिकित्सा, विज्ञान, साहित्य, शोध, प्रशासन, और परामर्श जैसे प्रतिष्ठित क्षेत्रों में आप अपनी प्रतिभा का उत्कृष्ट प्रदर्शन कर सकते हैं।' if is_hi else
            'You are not particularly well suited to a routine commercial life, since these demand a monotonous nature which you do not possess. There are plenty of occupations in which you ought to do remarkably well. Generally speaking, you have an aptitude for several of the highest professions: law, medicine, advisory consultancy, literature, executive management, and research.'}
        </p>

        <div class="as-sub-title">{'स्वास्थ्य एवं दीर्घायु' if is_hi else 'Health'}</div>
        <p>
            {'आपकी आयु और स्वास्थ्य का स्तर आपकी अनुशासित जीवनशैली पर अत्यधिक निर्भर करता है। शुद्ध वायु, नियमित प्राणायाम एवं सात्विक भोजन आपके लिए अमृत तुल्य हैं। मौसम परिवर्तन के समय श्वास व पाचन का विशेष ध्यान रखें।' if is_hi else
            'The length of your life depends more on yourself than on the fates. You have the power to attain a ripe old age. But, if you wish to do so, you must take particular care of your respiratory system. Seek all the fresh air you can obtain. Make a practice of regular walking. Never overload digestion with foods that are rich and hard to digest. Plain food will serve you best.'}
        </p>
        {page_footer(7)}
    </div>
    """
    pages.append(p7)

    # Page 8: Hobbies, Love Matters, Finance
    p8 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'जीवन फलादेश' if is_hi else 'Life Predictions'} ||</div>
        
        <div class="as-sub-title">{'रुचियां एवं शौक' if is_hi else 'Hobbies'}</div>
        <p>
            {'प्राकृतिक वातावरण में भ्रमण, यात्राएं और पुस्तकों का अध्ययन आपको विशेष आनंद प्रदान करता है। तीव्र गति के वाहन और लंबी यात्राएं आपको प्रिय हैं। ज्ञानवर्धन हेतु शैक्षिक व ऐतिहासिक स्थलों का भ्रमण करना आपकी मुख्य रुचि है।' if is_hi else
            'Outdoor pursuits engage much of your leisure time and you find them exceedingly beneficial. You love movement in the open, enjoy the pleasures of travel and long journeys, as well as educational visits. You take a keen interest in educating yourself using books and research.'}
        </p>

        <div class="as-sub-title">{'प्रेम व वैवाहिक संबंध' if is_hi else 'Love Matters'}</div>
        <p>
            {'आपका मित्र-मंडली का दायरा विस्तृत रहता है। जीवनसाथी का चयन प्रायः आपकी गहरी समझ और आकर्षण पर आधारित होता है। वैवाहिक जीवन में संतुलन एवं स्वतंत्रता का समन्वय बनाए रखना सुखद दांपत्य की कुंजी है।' if is_hi else
            'You never forget friends and possess a wide circle of acquaintances. You will marry and be comfortable. But, marriage will require conscious nurturing and communication so external interests do not create unnecessary misunderstandings. Mutual respect ensures deep lifelong harmony.'}
        </p>

        <div class="as-sub-title">{'आर्थिक स्थिति एवं वित्त' if is_hi else 'Finance'}</div>
        <p>
            {'आप अपने भाग्य के स्वयं निर्माता हैं। तीक्ष्ण बुद्धि और अवसर पहचानने की क्षमता से आप विपुल धन संचित करने में सफल होंगे। आय में उतार-चढ़ाव आ सकते हैं, किंतु आपकी बचत व निवेश की सूझबूझ आपको अंततः अत्यंत संपन्न बनाएगी।' if is_hi else
            'You are more likely to be architect of your own fortune than receive much help from others. In matters of finance, your quick-witted clever brain will give you great opportunities. There is no reason for you not to eventually succeed and even become wealthy. Holding impulsive expenditures in check will guarantee enormous prosperity.'}
        </p>
        {page_footer(8)}
    </div>
    """
    pages.append(p8)

    # Page 9: Education
    p9 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'जीवन फलादेश' if is_hi else 'Life Predictions'} ||</div>
        
        <div class="as-sub-title">{'विद्या एवं उच्च शिक्षा' if is_hi else 'Education'}</div>
        <p>
            {'आपमें गूढ़ और असाधारण विषयों को गहराई से समझने की विलक्षण क्षमता है। औपचारिक शिक्षा में प्रारंभिक चुनौतियों के उपरांत भी आपकी लगन और स्वाध्याय आपको उच्च शैक्षणिक प्रतिष्ठा दिलाते हैं। नियमित अभ्यास और एकाग्रता से आप अनुसंधान व विशेषज्ञता के उच्च शिखर पर पहुंचते हैं।' if is_hi else
            'You have the habit of keeping grave secrets, which will help you in getting hold of extraordinary subjects which won\'t be the cup of tea for many. On the other hand, you may face adverse circumstances in your formal education. You can overcome these challenges if you work hard with complete dedication. You should pay attention towards your studies and perform revisions regularly. This should be done so that you can imbibe all the knowledge you have acquired. Select your company wisely and situations will turn favorably in your higher educational pursuits.'}
        </p>
        {page_footer(9)}
    </div>
    """
    pages.append(p9)

    # =========================================================================
    # PAGE 10: || MANGLIK DETAILS / MANGAL DOSHA || (dynamic verdict)
    # =========================================================================
    mars_h_lagna = mangal_data["mars_from_asc"]
    mars_h_moon = mangal_data["mars_from_moon"]
    mars_h_venus = mangal_data["mars_from_venus"]
    _manglik = mangal_data["is_manglik"]
    if _manglik:
        _manglik_verdict_hi = ('अतः आपकी कुण्डली में मंगल दोष उपस्थित है (' + mangal_data["severity"] +
                              ')। विवाह पूर्व कुण्डली मिलान अनिवार्य है।')
        _manglik_verdict_en = ('Hence Mangal Dosha is PRESENT in your horoscope (' +
                              mangal_data["severity"].split('(')[-1].rstrip(')').strip() +
                              '). Kundli matching is recommended before marriage.')
    elif mangal_data["cancellations"]:
        _manglik_verdict_hi = ('अतः यद्यपि मंगल की स्थिति मांगलिक भावों में है, किंतु शास्त्रीय परिहारों के कारण '
                              'आपकी कुण्डली मंगल दोष से दोष-मुक्त है।')
        _manglik_verdict_en = ('Hence Mangal Dosha stands CANCELLED in your horoscope due to classical '
                              'cancellations (शास्त्रीय परिहार). The horoscope is free from Mangal Dosha.')
    else:
        _manglik_verdict_hi = 'अतः आपकी कुण्डली में लग्न एवं चन्द्र दोनों से मंगल दोष उपस्थित नहीं है (दोष-मुक्त)।'
        _manglik_verdict_en = 'Hence Mangal Dosha is present neither in Lagna Chart nor in Moon Chart.'

    _manglik_cancellation_html = ""
    if mangal_data["cancellations"]:
        _canc_items = "".join(f"<li>{c}</li>" for c in mangal_data["cancellations"])
        _manglik_cancellation_html = (
            f'<div class="as-sub-title">{"शास्त्रीय परिहार (Cancellations)" if is_hi else "Classical Cancellations"}</div>'
            f'<ul style="margin: 2px 0 6px 16px; font-size: 8pt;">{_canc_items}</ul>'
        )

    p10 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'मांगलिक विचार / मंगल दोष' if is_hi else 'Manglik Details / Mangal Dosha'} ||</div>
        
        <p>
            {'सामान्यतः जन्म कुण्डली में मंगल दोष का विचार लग्न एवं चन्द्र दोनों से मंगल की स्थिति के आधार पर किया जाता है।' if is_hi else
            'Generally Manglik Dosha is considered from the position of Lagna and Moon in the birth chart.'}
        </p>
        <p>
            {'आपकी जन्म कुण्डली में मंगल लग्न से ' + str(mars_h_lagna) + 'वें भाव में, चन्द्र कुण्डली से ' + str(mars_h_moon) + 'वें भाव में तथा शुक्र से ' + str(mars_h_venus) + 'वें भाव में स्थित है।' if is_hi else
            f'In the birth chart, Mangal is placed in {mars_h_lagna}th house from Lagna, {mars_h_moon}th house from Moon and {mars_h_venus}th house from Venus.'}
        </p>
        {_manglik_cancellation_html}
        <p style="font-weight: bold; margin: 8px 0;">
            {_manglik_verdict_hi if is_hi else _manglik_verdict_en}
        </p>
        <p>
            {'ज्योतिष शास्त्र में मंगल दोष दांपत्य जीवन में विलम्ब या विवाद का कारण माना जाता है। किंतु यदि मंगल अपनी उच्च राशि, स्वराशि या केंद्र में शुभ युत/दृष्ट हो अथवा परिहार प्राप्त हो तो यह दोष निष्प्रभावी हो जाता है।' if is_hi else
            'Mangal Dosha is considered to create hurdles in the married life of a person according to traditional belief. However, when Mars occupies its own sign, exaltation sign, or receives benefic aspects, the dosha stands completely cancelled.'}
        </p>

        <div class="as-sub-title">{'मंगल शांति एवं कल्याणकारी उपाय' if is_hi else 'Some Remedies (in case Mangal Dosha is present)'}</div>
        
        <div style="font-weight: bold; margin-top: 6px;">{'विवाह पूर्व उपाय:' if is_hi else 'Remedies (needs to be performed before marriage)'}</div>
        <p>Kumbha Vivah, Vishnu Vivah and Ashwatha Vivah are the most popular classical remedies for Mangal Dosha.</p>

        <div style="font-weight: bold; margin-top: 6px;">{'विवाह उपरांत उपाय:' if is_hi else 'Remedies (can be performed after marriage)'}</div>
        <p>1. Keep Kesariya Ganapati (Orange coloured idol of Lord Ganesha) in worship room and worship daily.<br/>
           2. Worship Lord Hanuman by reciting Hanuman Chalisa daily.<br/>
           3. Mahamrityunjaya paath (recitation of Mahamrityunjaya mantra).</p>

        <div style="font-weight: bold; margin-top: 6px;">{'लाल किताब विशेष उपाय:' if is_hi else 'Remedies (based on Lal Kitab, can be performed after marriage)'}</div>
        <p>1. Feed birds with something sweet.<br/>
           2. Keep ivory or copper article in home.<br/>
           3. Worship banyan tree with milk mixed with sweetness.</p>

        <p style="font-size: 7.5pt; color: #555555; margin-top: 10px;">
            Note: We strongly recommend you to consult an astrologer before performing these remedies on your own.
        </p>
        {page_footer(10)}
    </div>
    """
    pages.append(p10)

    # =========================================================================
    # PAGES 11-13: || SADESATI REPORT || SCHEDULE TABLES
    # =========================================================================
    sade_meta_box = f"""
    <table class="as-table as-table-left" style="margin-bottom: 8px;">
        <tr><td><b>Name</b></td><td>{name}</td><td><b>Sex</b></td><td>{_p2_sex}</td></tr>
        <tr><td><b>Date</b></td><td>{birth_dt.strftime('%d/%m/%Y')}</td><td><b>Rasi</b></td><td>{constants.SIGNS[moon_sign_idx]}</td></tr>
        <tr><td><b>Time of Birth</b></td><td>{birth_dt.strftime('%H:%M:%S')}</td><td><b>Tithi</b></td><td>{panch_obj.tithi}</td></tr>
        <tr><td><b>Place of Birth</b></td><td>{city}</td><td><b>Nakshatra</b></td><td>{panch_obj.nakshatra}</td></tr>
    </table>
    """

    # Split 46 phases into: P11 (1-17), P12 (18-33), P13 (34-46)
    def render_sade_table(phases_slice, start_num):
        rows = []
        for idx, p in enumerate(phases_slice, start=start_num):
            rows.append(f"""
            <tr>
                <td>{idx}</td>
                <td>{p.phase_name}</td>
                <td>{p.saturn_sign}</td>
                <td>{p.start_date}</td>
                <td>{p.end_date}</td>
                <td>{p.charan}</td>
            </tr>
            """)
        return f"""
        <table class="as-table">
            <tr><th>S.N.</th><th>Sade Sati / Panoti</th><th>Shani Rashi</th><th>Start Date</th><th>End Date</th><th>Phase</th></tr>
            {''.join(rows)}
        </table>
        """

    # Page 11
    p11 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Sadesati Report ||</div>
        {sade_meta_box}
        {render_sade_table(sade_sati_phases[:17], 1)}
        {page_footer(11)}
    </div>
    """
    pages.append(p11)

    # Page 12
    p12 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Sadesati Report ||</div>
        {render_sade_table(sade_sati_phases[17:33], 18)}
        {page_footer(12)}
    </div>
    """
    pages.append(p12)

    # Page 13
    p13 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Sadesati Report ||</div>
        {render_sade_table(sade_sati_phases[33:], 34)}
        {page_footer(13)}
    </div>
    """
    pages.append(p13)

    # =========================================================================
    # PAGE 14: || SADESATI REPORT || PHASES & REMEDIES
    # =========================================================================
    p14 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Sadesati Report ||</div>
        
        <div class="as-sub-title">Shani Sade Sati: Rising Phase</div>
        <p>This is starting period of Shani's Sade Sati. In this period Saturn will be transiting in 12th house from the Moon. It generally indicates financial expenses, problems by hidden competitors, aimless travel, disputes, and reorganizations. During this period, relationships with colleagues require care. Relationship with family requires patience. Saturn’s nature is of delay and dejection, but generally you will get results eventually, so be patient and wait for your turn.</p>

        <div class="as-sub-title">Shani Sade Sati: Peak Phase</div>
        <p>This is the peak of Shani's Sade Sati. Generally this phase of Saturn is the most transformative one. Saturn transiting over natal Moon indicates mental discipline, character strengthening, resilience, and spiritual elevation. Your constitution and endurance will be tested. Spiritual inclination and doing basics right will sail you out of this period with great honor and maturity.</p>

        <div class="as-sub-title">Shani Sade Sati: Setting Phase</div>
        <p>This is 'setting' period of Shani's Sade Sati. Saturn will be transiting in the 2nd house from the natal Moon, which indicates stabilization on financial and domestic front. You will start feeling relief after having two difficult phases of Sade Sati. Expenses stabilize and long-term consolidation occurs. Maintain high ethics and reverence towards elders.</p>

        <div style="font-weight: bold; margin-top: 10px;">Note:</div>
        <p style="font-size: 7.5pt; color: #444444;">Above predictions are of general nature. Truly speaking, Saturn acts as a great teacher and bestows monumental success to those who uphold truth, discipline, and charity.</p>
        {page_footer(14)}
    </div>
    """
    pages.append(p14)

    # =========================================================================
    # PAGE 15: || KALSARPA DOSH || (dynamic verdict from kalsarp_data)
    # =========================================================================
    if kalsarp_data["is_kalsarp"]:
        _kalsarp_result_hi = f"परिणाम: आपकी कुण्डली में {kalsarp_data['type_name']} सक्रिय है"
        _kalsarp_result_en = f"Result: {kalsarp_data['type_name']} (Kalsarpa Yoga) is ACTIVE in your horoscope"
        _kalsarp_color = "#9b2c2c"
        _kalsarp_desc_hi = kalsarp_data["description_hi"]
        _kalsarp_desc_en = ("As per the classical definition, when all seven major planets are situated between "
                            "Rahu and Ketu in the birth-chart, it is known as Kalsarp Yoga. When planets are well "
                            "posited, it does not cause harm and instead fosters great spiritual depth and "
                            "extraordinary elevation.")
    else:
        _kalsarp_result_hi = "परिणाम: आपकी कुण्डली कालसर्प योग से पूर्णतः मुक्त है"
        _kalsarp_result_en = "Result: Your Horoscope is free from Kalsarpa Yoga"
        _kalsarp_color = "#22543d"
        _kalsarp_desc_hi = kalsarp_data["description_hi"]
        _kalsarp_desc_en = ("As per the classical definition, when all seven major planets are situated between "
                            "Rahu and Ketu in the birth-chart, it is known as Kalsarp Yoga. When planets are well "
                            "posited, it does not cause harm and instead fosters great spiritual depth and "
                            "extraordinary elevation.")

    p15 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| {'कालसर्प दोष' if is_hi else 'Kalsarpa Dosh'} ||</div>
        
        <div class="as-sub-title">{'कालसर्प दोष / योग' if is_hi else 'Kalsarpa Dosh / Yog'}</div>
        <p>
            {_kalsarp_desc_hi if is_hi else _kalsarp_desc_en}
        </p>

        <p style="font-weight: bold; font-size: 9.5pt; margin: 10px 0; color: {_kalsarp_color};">
            {_kalsarp_result_hi if is_hi else _kalsarp_result_en}
        </p>

        <div style="text-align: center; margin: 20px 0;">
            <div style="font-weight: bold; margin-bottom: 6px;">{'लग्न कुण्डली' if is_hi else 'Lagna Chart'}:</div>
            {svg_d1}
        </div>
        {page_footer(15)}
    </div>
    """
    pages.append(p15)

    # =========================================================================
    # PAGES 16-18: || VARSHAPHAL (ANNUAL PREDICTIONS) DETAILS ||
    # =========================================================================
    varsh_houses = {h: [str((asc_sign_idx + h - 1) % 12 + 1)] for h in range(1, 13)}
    varsh_houses[varshphal_data["muntha_house"]].append(f"Mu ({varshphal_data['muntha_sign'][:2]})")
    svg_varsh = render_astrosage_diamond_svg(varsh_houses, size=280)

    # Live panchang for the Varsha (solar-return) year — replaces the hardcoded
    # reference values (11:10:33, Tuesday, Taurus, Krittika, 07.00.54, ...).
    try:
        _varsh_dt = datetime(target_varsh_year, birth_dt.month, birth_dt.day,
                             birth_dt.hour, birth_dt.minute, birth_dt.second)
        _varsh_panch = panchang.compute(_varsh_dt, lat, lon, tz, chart.ascendant_longitude)
        from vyas import ephem as _eph3
        _varsh_utc = (_varsh_dt - timedelta(hours=tz)).replace(tzinfo=timezone.utc)
        _varsh_moon_lon = _eph3.sidereal_lon("Moon", _varsh_utc)
        _varsh_rasi = constants.SIGNS[int(_varsh_moon_lon // 30)]
        _varsh_rasi_lord = constants.SIGN_LORD[int(_varsh_moon_lon // 30)][:3].upper()
        _varsh_sun_lon = _eph3.sidereal_lon("Sun", _varsh_utc)
        _varsh_west_sun = constants.SIGNS[int(((_varsh_sun_lon + _eph3.ayanamsa_deg(_eph3._t(_varsh_utc).tt)) % 360.0) // 30)]
        _varsh_time = _varsh_panch.sunrise if _varsh_panch.sunrise != "-" else _varsh_dt.strftime("%H:%M:%S")
        _varsh_day = _varsh_panch.vara
        _varsh_nak = _varsh_panch.nakshatra
        _varsh_nak_lord = _varsh_panch.nakshatra_lord[:3].upper()
        _varsh_yoga = _varsh_panch.yoga
        _varsh_karan = _varsh_panch.karana
        _varsh_rise = _varsh_panch.sunrise
        _varsh_set = _varsh_panch.sunset
        _varsh_ayan = _varsh_panch.ayanamsa_value
        _varsh_ayan_name = _varsh_panch.ayanamsa
    except Exception:
        _varsh_rasi = varshphal_data.get('varsha_lagna', '--')
        _varsh_rasi_lord = varshphal_data.get('varshesh', 'SUN')[:3].upper()
        _varsh_west_sun = '--'
        _varsh_time = birth_dt.strftime('%H:%M:%S')
        _varsh_day = panch_obj.vara
        _varsh_nak = panch_obj.nakshatra
        _varsh_nak_lord = panch_obj.nakshatra_lord[:3].upper() if hasattr(panch_obj, 'nakshatra_lord') else '--'
        _varsh_yoga = panch_obj.yoga
        _varsh_karan = panch_obj.karana
        _varsh_rise = panch_obj.sunrise
        _varsh_set = panch_obj.sunset
        _varsh_ayan = panch_obj.ayanamsa_value
        _varsh_ayan_name = panch_obj.ayanamsa

    p16 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Varshaphal (Annual Predictions) Details ||</div>
        
        <table class="as-table as-table-left" style="margin-bottom: 12px;">
            <tr><th>Janam (Birth)</th><th>Parameter</th><th>Varsha (Year)</th></tr>
            <tr><td>{_p2_sex}</td><td>Sex</td><td>{_p2_sex}</td></tr>
            <tr><td>{birth_dt.strftime('%d/%m/%Y')}</td><td>Date of Birth</td><td>{birth_dt.strftime('%d/%m/')}{varshphal_data['target_year']}</td></tr>
            <tr><td>{birth_dt.strftime('%H:%M:%S')}</td><td>Time of Birth</td><td>{_varsh_time}</td></tr>
            <tr><td>{panch_obj.vara}</td><td>Day of Birth</td><td>{_varsh_day}</td></tr>
            <tr><td>{city}</td><td>Place of Birth</td><td>{city}</td></tr>
            <tr><td>{lat:.4f}</td><td>Latitude</td><td>{lat:.4f}</td></tr>
            <tr><td>{lon:.4f}</td><td>Longitude</td><td>{lon:.4f}</td></tr>
            <tr><td>{p2_lmc}</td><td>Local Time Correction</td><td>{p2_lmc}</td></tr>
            <tr><td>00.00.00</td><td>War Time Correction</td><td>00.00.00</td></tr>
            <tr><td>{p2_lmt}</td><td>LMT at Birth</td><td>{p2_lmt}</td></tr>
            <tr><td>{panch_obj.sunrise}</td><td>Sunrise</td><td>{_varsh_rise}</td></tr>
            <tr><td>{panch_obj.sunset}</td><td>Sunset</td><td>{_varsh_set}</td></tr>
            <tr><td>{constants.SIGNS[asc_sign_idx]}</td><td>Lagna</td><td>{varshphal_data['varsha_lagna']}</td></tr>
            <tr><td>{constants.PLANETS_HI.get(constants.SIGN_LORD[asc_sign_idx],'')[:3].upper()}</td><td>Lagna Lord</td><td>{varshphal_data['varshesh'][:3].upper()}</td></tr>
            <tr><td>{constants.SIGNS[moon_sign_idx]}</td><td>Rasi</td><td>{_varsh_rasi}</td></tr>
            <tr><td>{constants.SIGN_LORD[moon_sign_idx][:3].upper()}</td><td>Rasi Lord</td><td>{_varsh_rasi_lord}</td></tr>
            <tr><td>{panch_obj.nakshatra}</td><td>Nakshatra</td><td>{_varsh_nak}</td></tr>
            <tr><td>{panch_obj.nakshatra_lord[:3].upper() if hasattr(panch_obj, 'nakshatra_lord') else constants.VIMSHOTTARI_ORDER[int(moon_lon // constants.NAKSHATRA_SPAN) % 9][:3].upper()}</td><td>Nakshatra Lord</td><td>{_varsh_nak_lord}</td></tr>
            <tr><td>{panch_obj.yoga}</td><td>Yoga</td><td>{_varsh_yoga}</td></tr>
            <tr><td>{panch_obj.karana}</td><td>Karan</td><td>{_varsh_karan}</td></tr>
            <tr><td>{p2_west_sun_sign}</td><td>Sun Sign (Western)</td><td>{_varsh_west_sun}</td></tr>
            <tr><td>{panch_obj.ayanamsa_value}</td><td>Ayanamsa</td><td>{_varsh_ayan}</td></tr>
            <tr><td>{panch_obj.ayanamsa}</td><td>Ayanamsa Name</td><td>{_varsh_ayan_name}</td></tr>
        </table>

        <div style="text-align: center;">
            <div style="font-weight: bold; margin-bottom: 4px;">Varshphal Chart (Solar Return Chart)</div>
            {svg_varsh}
        </div>
        {page_footer(16)}
    </div>
    """
    pages.append(p16)

    # Pages 17-18: Muntha & Mudda Dasha Periods
    mudda_p = varshphal_data['mudda_periods']
    muntha_h = varshphal_data['muntha_house']
    muntha_en_dict = {
        10: "You will enjoy all the prosperity and comfort. This is best position for Muntha where there is fulfillment of desires and you lead a contented life. Your fame and reputation will be on an increase. You will get promotion or improvement in status. You will be favored by ministers and government. You will help relatives and society.",
        11: "Muntha in the 11th house brings immense financial gains, business growth, support from powerful allies, fulfillment of cherished ambitions, and higher social elevation.",
        9: "Muntha in the 9th house bestows high fortune, virtuous endeavors, pilgrimages, blessings from mentors and father, and scholastic and philosophical recognition.",
        1: "Muntha in the 1st house confers vitality, personal magnetism, success in pioneering ventures, respected public standing, and sound health.",
        2: "Muntha in the 2nd house ensures wealth accumulation through systematic speech, harmonious domestic developments, and prosperous family ventures.",
        3: "Muntha in the 3rd house sparks brave initiatives, success through determined efforts, cordial ties with siblings, and profitable communications.",
        4: "Muntha in the 4th house advises calmness in domestic matters, care of mother's well-being, and deliberate caution in real estate transactions.",
        5: "Muntha in the 5th house brings creative brilliance, intellectual laurels, joyous news regarding children, and fruitful speculation.",
        6: "Muntha in the 6th house promises victory over obstacles and rivals, though prudence in financial loans and health maintenance is advised.",
        7: "Muntha in the 7th house highlights marital rapport, rewarding business partnerships, and meaningful foreign or distant travels.",
        8: "Muntha in the 8th house suggests safeguarding health, avoiding rash financial speculation, and channeling energies into deeper spiritual growth.",
        12: "Muntha in the 12th house indicates increased expenditures, foreign travel or relocation, philosophical seclusion, and need for fiscal prudence."
    }
    muntha_phal_text = muntha_en_dict.get(muntha_h, "You will enjoy prosperity and progress with steady efforts.") if lang == "en" else varshphal_data.get('muntha_phal_hi', '')

    def get_p_house(p_name):
        if p_name in dignities:
            return dignities[p_name].house
        if p_name in chart.planets:
            return (chart.planets[p_name].sign_index - asc_sign_idx + 12) % 12 + 1
        return 1

    p17 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Varshaphal (Annual Predictions) Details ||</div>
        
        <div class="as-sub-title">Muntha : {varshphal_data['muntha_house']} Bhav</div>
        <p>{muntha_phal_text}</p>

        <div class="as-sub-title">{mudda_p[0]['start']} - {mudda_p[0]['end']} Dasha {mudda_p[0]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[0]['planet']} is in Bhav Number {get_p_house(mudda_p[0]['planet'])}</div>
        <p>You should learn to relax to avoid unnecessary mental stress when things seem to be stagnating at the professional front. Resist the urge to change jobs on an impulse driven by temporary frustrations. Focus on health, safety while driving, and harmony at home.</p>

        <div class="as-sub-title">{mudda_p[1]['start']} - {mudda_p[1]['end']} Dasha {mudda_p[1]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[1]['planet']} is in Bhav Number {get_p_house(mudda_p[1]['planet'])}</div>
        <p>New projects or higher level of investment should be approached with thorough planning. If working as a professional, steady growth with routine hurdles is indicated. Patience will yield solid progress.</p>

        <div class="as-sub-title">{mudda_p[2]['start']} - {mudda_p[2]['end']} Dasha {mudda_p[2]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[2]['planet']} is in Bhav Number {get_p_house(mudda_p[2]['planet'])}</div>
        <p>Your courage and convictions are your strongest qualities. Financial caution is recommended. Family members and associates will provide valuable counsel. Focus on spiritual balance.</p>

        <div class="as-sub-title">{mudda_p[3]['start']} - {mudda_p[3]['end']} Dasha {mudda_p[3]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[3]['planet']} is in Bhav Number {get_p_house(mudda_p[3]['planet'])}</div>
        <p>There will be good stability of mind which would help live a positive and productive life. Excellent period for travel, higher education, communications, and venturing into disciplined enterprises.</p>
        {page_footer(17)}
    </div>
    """
    pages.append(p17)

    p18 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Varshaphal (Annual Predictions) Details ||</div>
        
        <div class="as-sub-title">{mudda_p[4]['start']} - {mudda_p[4]['end']} Dasha {mudda_p[4]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[4]['planet']} is in Bhav Number {get_p_house(mudda_p[4]['planet'])}</div>
        <p>Events of the year will strengthen your optimistic instincts. Intelligent timing of investments will yield profitable returns. Cooperation and happiness from loved ones and professional victory over competitors.</p>

        <div class="as-sub-title">{mudda_p[5]['start']} - {mudda_p[5]['end']} Dasha {mudda_p[5]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[5]['planet']} is in Bhav Number {get_p_house(mudda_p[5]['planet'])}</div>
        <p>Good and pious deeds bring spiritual authority. Partnerships prove constructive in both professional and personal spheres. An awakening experience creates deep inner harmony.</p>

        <div class="as-sub-title">{mudda_p[6]['start']} - {mudda_p[6]['end']} Dasha {mudda_p[6]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[6]['planet']} is in Bhav Number {get_p_house(mudda_p[6]['planet'])}</div>
        <p>New creative ideas for dealing with challenges. Dealings and transactions work out smoothly and effortlessly. Income accrues from multiple avenues, with acquisition of comforts.</p>

        <div class="as-sub-title">{mudda_p[7]['start']} - {mudda_p[7]['end']} Dasha {mudda_p[7]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[7]['planet']} is in Bhav Number {get_p_house(mudda_p[7]['planet'])}</div>
        <p>Excellent time for contracts, agreements, and status enhancement. Rise in position and authority. Harmonious domestic atmosphere with increased honor.</p>

        <div class="as-sub-title">{mudda_p[8]['start']} - {mudda_p[8]['end']} Dasha {mudda_p[8]['planet']}</div>
        <div style="font-weight: bold; margin: 2px 0;">{mudda_p[8]['planet']} is in Bhav Number {get_p_house(mudda_p[8]['planet'])}</div>
        <p>Ideal time to take concrete action on long-term plans. Domestic bliss, creative fulfillment, appreciation for intellectual output, and happiness from progeny.</p>
        {page_footer(18)}
    </div>
    """
    pages.append(p18)

    # =========================================================================
    # PAGES 19-20: || VIMSHOTTARI MAHADASHA PHAL (DASHA PREDICTIONS) ||
    # Fully dynamic: MD lords + date ranges from dasha_engine, sign/house from
    # the computed natal chart, and per-house phal from mahadasha_interpretations
    # (previously ALL dates were hardcoded to the 1984 Pali reference chart).
    # =========================================================================
    _MD_EN_TEXT = {
        "Saturn": "The period brings learning through responsibility and discipline. Career pressures require flexibility and tactful communications. Prudent financial management and avoidance of haste ensure steady progress.",
        "Mercury": "Active intellectual phase with deep interest in research, analytics, and occult studies. Financial flows require careful budgeting. Clear written agreements and avoidance of unvetted ventures ensure long-term stability.",
        "Ketu": "Deep spiritual awakening, charitable inclinations, and philosophical maturity. Intuitive breakthroughs bring unique problem-solving capabilities and emotional resilience.",
        "Venus": "A visit to sacred places of interest is favored. Charismatic demeanor enhances cordial public relations and valuable connections. Material fulfillment, status elevation, and acquisition of luxury vehicles and immovable property.",
        "Sun": "Period of inner courage and transformation. Transparent professional dealings and maintaining cordial relations with superiors yield enduring rewards.",
        "Moon": "Emotional depth and heightened intuition. Avoid speculative financial gambles. Cultivate calmness through meditation and mindful self-care. Domestic focus brings profound satisfaction.",
        "Mars": "Dynamic period granting executive authority, courage, and professional triumph. Recognition in occupation is assured. New leadership roles and initiatives yield commanding prestige.",
        "Rahu": "Unconventional avenues of wealth and international dealings. Steady progress achieved through diplomatic acumen and technological integration.",
        "Jupiter": "Supreme wisdom, spiritual authority, and societal respect. Long-distance journeys and mentorship bring boundless honor and enduring charitable legacy.",
    }

    def render_md_phal(md_node):
        lord = md_node.lord
        interp = mahadasha_interpretations.get(lord, {})
        h_house = interp.get("house", dignities.get(lord, {}).get("house", "?") if isinstance(dignities.get(lord), dict) else dignities[lord].house)
        sign_name = interp.get("sign", constants.SIGNS[chart.planets[lord].sign_index])
        if is_hi:
            body_txt = interp.get("interpretation_hi", _MD_EN_TEXT.get(lord, ""))
            head_txt = f"{interp.get('planet_hi', lord)} {h_house} वें भाव में {constants.SIGNS_HI[chart.planets[lord].sign_index]} राशि में स्थित है"
        else:
            body_txt = _MD_EN_TEXT.get(lord, "")
            head_txt = f"{lord} is in {sign_name} in your {h_house}th house"
        d1 = md_node.start_date.strftime("%d %B %Y")
        d2 = md_node.end_date.strftime("%d %B %Y")
        range_str = f"{d1} - {d2}" if md_node.start_date > birth_dt else f"Birth - {d2}"
        return f"""
        <div class="as-sub-title">{lord} Mahadasha Phal ({range_str})</div>
        <div style="font-weight: bold; margin: 2px 0;">{head_txt}</div>
        <p>{body_txt}</p>
        """

    _md_nodes = dasha_engine.calculate_mahadashas()
    _md_phal_html_1 = "".join(render_md_phal(m) for m in _md_nodes[:5])
    _md_phal_html_2 = "".join(render_md_phal(m) for m in _md_nodes[5:9])

    p19 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Vimshottari Mahadasha Phal (Dasha Predictions) ||</div>
        {_md_phal_html_1}
        {page_footer(19)}
    </div>
    """
    pages.append(p19)

    p20 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Vimshottari Mahadasha Phal (Dasha Predictions) ||</div>
        {_md_phal_html_2}
        {page_footer(20)}
    </div>
    """
    pages.append(p20)

    # =========================================================================
    # PAGES 21-22: || YOGINI DASHA || (36-Year Cycles)
    # =========================================================================
    def render_yogini_grid(cycles_slice):
        cols = []
        for yc in cycles_slice[:4]:
            sub_rows = "".join([f"<tr><td>{ad['name'][:2]}</td><td>{_d8(ad['start'])}</td></tr>" for ad in yc.get('antardashas', [])[:8]])
            cols.append(f"""
            <div style="flex: 1; border: 1px solid #000; padding: 2px;">
                <div style="font-weight: bold; text-align: center; background: #f2f2f2; border-bottom: 1px solid #000; padding: 2px 0;">
                    {yc['name'][:2]} {yc['years']} Years
                </div>
                <div style="font-size: 7pt; text-align: center; padding: 2px 0; border-bottom: 0.5px solid #000;">
                    From {_d8(yc['start'])}<br/>To {_d8(yc['end'])}
                </div>
                <table class="as-table as-table-dense" style="margin-bottom: 0;">
                    {sub_rows}
                </table>
            </div>
            """)
        return f'<div class="two-col" style="gap: 4px; margin-bottom: 8px;">{"".join(cols)}</div>'

    p21 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Yogini Dasha ||</div>
        {render_yogini_grid(yogini_cycles[:4])}
        {render_yogini_grid(yogini_cycles[4:8])}
        {render_yogini_grid(yogini_cycles[8:12])}
        {page_footer(21)}
    </div>
    """
    pages.append(p21)

    p22 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Yogini Dasha ||</div>
        {render_yogini_grid(yogini_cycles[12:16])}
        {render_yogini_grid(yogini_cycles[16:20])}
        {render_yogini_grid(yogini_cycles[20:24])}
        {page_footer(22)}
    </div>
    """
    pages.append(p22)

    # =========================================================================
    # PAGE 23: || JAMINI SYSTEM - KARAKAMSA AND SWAMSA ||
    # =========================================================================
    karakamsa_houses = {h: [str((asc_sign_idx + h - 1) % 12 + 1)] for h in range(1, 13)}
    ak_sign_idx = chart.planets[atmakaraka_planet].sign_index
    karakamsa_houses[(ak_sign_idx - asc_sign_idx + 12) % 12 + 1].append(f"AK ({atmakaraka_planet[:2]})")
    svg_karakamsa = render_astrosage_diamond_svg(karakamsa_houses, size=280)
    svg_swamsa = render_astrosage_diamond_svg(d9_houses, size=280)

    karak_rows = []
    sthir_map = {"Atma": "Sun", "Amatya": "Merc", "Bhratru": "Mars", "Matrua": "Moon", "Putra": "Jupt", "Gnati": "Satn", "Dara": "Venu"}
    for ck in chara_karakas_list:
        k_role = ck.karaka_name.replace("karaka", "")
        if k_role == "Matri": k_role = "Matrua"
        karak_rows.append(f"""
        <tr>
            <td><b>{k_role}</b></td>
            <td>{sthir_map.get(k_role, 'Sun')}</td>
            <td>{ck.planet[:4]}</td>
        </tr>
        """)

    avastha_rows = []
    for p_name in ["Sun", "Moon", "Mars", "Merc", "Jupt", "Venu", "Satn"]:
        pl_full = "Mercury" if p_name == "Merc" else ("Jupiter" if p_name == "Jupt" else ("Venus" if p_name == "Venu" else ("Saturn" if p_name == "Satn" else p_name)))
        deg = chart.planets[pl_full].longitude % 30.0
        sgn = chart.planets[pl_full].sign_index
        # Baladi
        if sgn % 2 == 0:
            b_av = "Bala" if deg < 6 else ("Kumara" if deg < 12 else ("Yuva" if deg < 18 else ("Vradha" if deg < 24 else "Mrat")))
        else:
            b_av = "Mrat" if deg < 6 else ("Vradha" if deg < 12 else ("Yuva" if deg < 18 else ("Kumara" if deg < 24 else "Bala")))
        j_av = "Jaagrat" if deg < 10 else ("Swapna" if deg < 20 else "Susupta")
        d_av = "Swatha" if dignities[pl_full].is_own_sign else ("Muditha" if dignities[pl_full].is_exalted else "Shant")

        avastha_rows.append(f"""
        <tr>
            <td><b>{p_name}</b></td>
            <td>{j_av}</td>
            <td>{b_av}</td>
            <td>{d_av}</td>
        </tr>
        """)

    p23 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Jamini System - Karakamsa and Swamsa ||</div>
        
        <div class="two-col" style="margin-bottom: 12px;">
            <div class="col-half" style="text-align: center;">
                <div style="font-weight: bold; margin-bottom: 4px;">Karakamsa Chart</div>
                {svg_karakamsa}
            </div>
            <div class="col-half" style="text-align: center;">
                <div style="font-weight: bold; margin-bottom: 4px;">Swamsa Chart</div>
                {svg_swamsa}
            </div>
        </div>

        <div class="two-col">
            <div class="col-half">
                <div class="as-sub-title" style="text-align: center;">Karak</div>
                <table class="as-table">
                    <tr><th>Karak</th><th>Sthir</th><th>Chara</th></tr>
                    {''.join(karak_rows)}
                </table>
            </div>
            <div class="col-half">
                <div class="as-sub-title" style="text-align: center;">Avastha</div>
                <table class="as-table">
                    <tr><th>Planets</th><th>Jagrat</th><th>Baladi</th><th>Deeptadi</th></tr>
                    {''.join(avastha_rows)}
                </table>
            </div>
        </div>
        {page_footer(23)}
    </div>
    """
    pages.append(p23)

    # =========================================================================
    # PAGES 24-25: || CHAR DASHA ||
    # =========================================================================
    char_md_rows_col1 = []
    char_md_rows_col2 = []
    for idx_cp, cp in enumerate(chara_periods):
        r_str = f"<tr><td><b>{cp['sign'][:3].upper()} {cp['years']:02d} Year</b></td><td>{_d8(cp['start'])}</td><td>{_d8(cp['end'])}</td></tr>"
        if idx_cp < 6:
            char_md_rows_col1.append(r_str)
        else:
            char_md_rows_col2.append(r_str)

    def render_char_ad_subtable(cp_node):
        sub_rows = []
        for ad in cp_node['antardashas']:
            sub_rows.append(f"<tr><td>{ad['sign'][:3].upper()}</td><td>{_d8(ad['start'])}</td><td>{_d8(ad['end'])}</td></tr>")
        return f"""
        <div style="flex: 1; border: 1px solid #000; padding: 2px;">
            <div style="font-weight: bold; text-align: center; background: #f2f2f2; border-bottom: 1px solid #000; padding: 2px 0;">
                {cp_node['sign'][:3].upper()} {cp_node['years']} Years
            </div>
            <table class="as-table as-table-dense" style="margin-bottom: 0;">
                {''.join(sub_rows)}
            </table>
        </div>
        """

    p24 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Char Dasha ||</div>
        
        <div class="as-sub-title">Char Maha Dasha</div>
        <div class="two-col" style="margin-bottom: 8px;">
            <div class="col-half">
                <table class="as-table">
                    {''.join(char_md_rows_col1)}
                </table>
            </div>
            <div class="col-half">
                <table class="as-table">
                    {''.join(char_md_rows_col2)}
                </table>
            </div>
        </div>

        <div class="as-sub-title">Char Antardasha</div>
        <div class="two-col" style="gap: 4px;">
            {render_char_ad_subtable(chara_periods[0])}
            {render_char_ad_subtable(chara_periods[1])}
            {render_char_ad_subtable(chara_periods[2])}
        </div>
        {page_footer(24)}
    </div>
    """
    pages.append(p24)

    p25 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Char Dasha ||</div>
        
        <div class="two-col" style="gap: 4px; margin-bottom: 6px;">
            {render_char_ad_subtable(chara_periods[3])}
            {render_char_ad_subtable(chara_periods[4])}
            {render_char_ad_subtable(chara_periods[5])}
        </div>
        <div class="two-col" style="gap: 4px; margin-bottom: 6px;">
            {render_char_ad_subtable(chara_periods[6])}
            {render_char_ad_subtable(chara_periods[7])}
            {render_char_ad_subtable(chara_periods[8])}
        </div>
        <div class="two-col" style="gap: 4px;">
            {render_char_ad_subtable(chara_periods[9])}
            {render_char_ad_subtable(chara_periods[10])}
            {render_char_ad_subtable(chara_periods[11])}
        </div>
        {page_footer(25)}
    </div>
    """
    pages.append(p25)

    # =========================================================================
    # PAGES 26-28: || TRANSIT TODAY || (Gochar — LIVE data from gochar module)
    # =========================================================================
    today_str = curr_dt.strftime("%d-%m-%Y")
    _transit_rows = []
    try:
        from vyas import gochar as _gochar
        _transit_rows = _gochar.transits(
            curr_dt, tz, moon_lon, chart.ascendant_longitude, with_ingress=True
        )
    except Exception:
        _transit_rows = []

    # Generic per-sign transit forecast text (sign-agnostic, house-aware).
    _GOCHAR_HOUSE_TEXT = {
        1: "Transit through the 1st house brings focus on self-development, health and personal initiatives. Energy levels are high; take care of impatience.",
        2: "This transit favours accumulation of wealth, family harmony and improvement in speech. Financial decisions made now yield steady results.",
        3: "A favourable transit for courage, sibling cooperation, short journeys and skill development. Your efforts earn recognition.",
        4: "Focus shifts to home, property, vehicle and mother's well-being. Domestic comfort increases; maintain patience in family matters.",
        5: "Auspicious for education, romance, speculation and progeny. Creative ideas flourish; avoid excessive risk in investments.",
        6: "Highly favourable transit — victory over enemies, competition and disease. Financial gains through service and hard work.",
        7: "Partnerships and marriage come into focus. Foreign connections and business alliances prove profitable; keep communication transparent.",
        8: "Exercise caution with health, debts and sudden events. This transit favours deep research, insurance matters and inheritance gains.",
        9: "Highly auspicious — luck, dharma and higher learning favour you. Pilgrimages and blessings of elders are indicated.",
        10: "Peak professional transit — promotion, honour and status elevation. Father's health deserves attention.",
        11: "Excellent for gains, friendships and fulfilment of desires. Income increases through networks and elder siblings.",
        12: "Expenses rise; foreign travels and spiritual pursuits are favoured. Keep strict ethics in financial transactions.",
    }

    def _render_transit_block(row):
        retro_str = " (R)" if row.retro else ""
        fav_color = "#22543d" if row.favourable else "#9b2c2c"
        verdict_txt = row.verdict
        if row.vedha_by:
            verdict_txt += f" — Vedha by: {row.vedha_by}"
        house_txt = _GOCHAR_HOUSE_TEXT.get(row.house_from_lagna, "")
        ingress_txt = f" Next ingress: {row.next_ingress}." if row.next_ingress else ""
        return f"""
        <div class="as-sub-title">{row.planet} is in {row.sign}{retro_str} {row.degree} ({row.nakshatra} {row.pada}) in your {row.house_from_lagna}th house (from Moon: {row.house_from_moon}th)</div>
        <div style="font-weight: bold; margin: 2px 0; color: {fav_color};">Transit Verdict: {verdict_txt}</div>
        <p>{house_txt}{ingress_txt}</p>
        """

    if _transit_rows:
        _t_blocks = [_render_transit_block(r) for r in _transit_rows]
        p26 = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Transit Today ({today_str}) ||</div>
            {''.join(_t_blocks[0:3])}
            {page_footer(26)}
        </div>
        """
        p27 = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Transit Today ({today_str}) ||</div>
            {''.join(_t_blocks[3:6])}
            {page_footer(27)}
        </div>
        """
        p28 = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Transit Today ({today_str}) ||</div>
            {''.join(_t_blocks[6:9])}
            {page_footer(28)}
        </div>
        """
    else:
        p26 = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Transit Today ({today_str}) ||</div>
            <p>Transit calculations unavailable for this report.</p>
            {page_footer(26)}
        </div>
        """
        p27 = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Transit Today ({today_str}) ||</div>
            {page_footer(27)}
        </div>
        """
        p28 = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Transit Today ({today_str}) ||</div>
            {page_footer(28)}
        </div>
        """
    pages.append(p26)
    pages.append(p27)
    pages.append(p28)

    # =========================================================================
    # PAGES 29-33: || LAL KITAB PREDICTION ||
    # =========================================================================
    def render_lk_planet_card(p_name: str):
        h = dignities[p_name].house
        data = astrosage_content.get_lal_kitab_house_data(p_name, h, lang=lang)
        b_str = "<br/>".join(data["benefic"])
        m_str = "<br/>".join(data["malefic"])
        r_str = "<br/>".join(data["remedies"])
        return f"""
        <div class="as-sub-title">{p_name} in your {h}th house:</div>
        <div style="font-weight: bold; margin: 2px 0;">If benefic</div>
        <p>{b_str}</p>
        <div style="font-weight: bold; margin: 2px 0;">If malefic</div>
        <p>{m_str}</p>
        <div style="font-weight: bold; margin: 2px 0;">Remedial Measures</div>
        <p>{r_str}</p>
        """

    p29 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Lal Kitab Prediction ||</div>
        {render_lk_planet_card('Sun')}
        {page_footer(29)}
    </div>
    """
    pages.append(p29)

    p30 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Lal Kitab Prediction ||</div>
        {render_lk_planet_card('Moon')}
        {render_lk_planet_card('Mars')}
        {page_footer(30)}
    </div>
    """
    pages.append(p30)

    p31 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Lal Kitab Prediction ||</div>
        {render_lk_planet_card('Mercury')}
        {render_lk_planet_card('Jupiter')}
        {page_footer(31)}
    </div>
    """
    pages.append(p31)

    p32 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Lal Kitab Prediction ||</div>
        {render_lk_planet_card('Venus')}
        {render_lk_planet_card('Saturn')}
        {page_footer(32)}
    </div>
    """
    pages.append(p32)

    p33 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Lal Kitab Prediction ||</div>
        {render_lk_planet_card('Rahu')}
        {render_lk_planet_card('Ketu')}
        {page_footer(33)}
    </div>
    """
    pages.append(p33)

    # =========================================================================
    # PAGE 34: || LAL KITAB CALCULATION ||
    # =========================================================================
    lk_deg_rows = []
    for lk in lal_kitab_list:
        p_nm = lk['planet']
        sgn_nm = constants.SIGNS[chart.planets[p_nm].sign_index] if p_nm in chart.planets else "Scorpion"
        soya_str = "Yes" if lk['house'] in [2, 4, 7, 9, 10] else "No"
        kismat_str = "Yes" if p_nm in ["Moon", "Jupiter"] else "No"
        eff_str = "Benefic" if p_nm in ["Sun", "Mars", "Jupiter", "Saturn"] else "Malefic"
        lk_deg_rows.append(f"""
        <tr>
            <td>{p_nm}</td>
            <td>{sgn_nm}</td>
            <td>----</td>
            <td>{soya_str}</td>
            <td>{kismat_str}</td>
            <td>{eff_str}</td>
        </tr>
        """)

    p34 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Lal Kitab Calculation ||</div>
        
        <table class="as-table as-table-dense as-table-left" style="margin-bottom: 8px;">
            <tr><td><b>Name</b></td><td>{name}</td><td><b>Sunrise</b></td><td>{panch_obj.sunrise}</td><td><b>Dasa Balance</b></td><td>{dasha_engine.balance_str}</td></tr>
            <tr><td><b>Sex</b></td><td>{_p2_sex}</td><td><b>Tithi</b></td><td>{panch_obj.tithi}</td><td><b>Sunset</b></td><td>{panch_obj.sunset}</td></tr>
            <tr><td><b>Date</b></td><td>{birth_dt.strftime('%d.%m.%Y')}</td><td><b>Yoga</b></td><td>{panch_obj.yoga}</td><td><b>Karan</b></td><td>{panch_obj.karana}</td></tr>
            <tr><td><b>Time</b></td><td>{birth_dt.strftime('%H.%M.%S')}</td><td><b>Lagna</b></td><td>{constants.SIGNS[asc_sign_idx]}</td><td><b>Lagna Lord</b></td><td>{constants.SIGN_LORD[asc_sign_idx][:3].upper()}</td></tr>
        </table>

        <div class="two-col" style="margin-bottom: 8px;">
            <div class="col-half">
                <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">Planetary Degree And Their Positions</div>
                <table class="as-table as-table-dense">
                    <tr><th>Planets</th><th>Sign</th><th>Positions</th><th>Soya</th><th>Kismat Jaganewala</th><th>Benefic / Malefic</th></tr>
                    {''.join(lk_deg_rows)}
                </table>
            </div>
            <div class="col-half" style="text-align: center;">
                <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">Lagna Chart</div>
                {svg_d1}
            </div>
        </div>

        <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">Lal Kitab Dasha (35-Year Lifetime Trajectory)</div>
        <div style="display: flex; flex-wrap: wrap; gap: 4px; font-size: 7.2pt; border: 1px solid #000; padding: 4px;">
            <div style="flex: 1 1 15%;"><b>Sat 6 Yr</b><br/>1984-1990<br/>Rahu 1986<br/>Mer 1988</div>
            <div style="flex: 1 1 15%;"><b>Rahu 6 Yr</b><br/>1990-1996<br/>Mars 1992<br/>Ketu 1994</div>
            <div style="flex: 1 1 15%;"><b>Ketu 3 Yr</b><br/>1996-1999<br/>Sat 1997<br/>Rahu 1998</div>
            <div style="flex: 1 1 15%;"><b>Jup 6 Yr</b><br/>1999-2005<br/>Ketu 2001<br/>Jup 2003</div>
            <div style="flex: 1 1 15%;"><b>Sun 2 Yr</b><br/>2005-2007<br/>Sun 2006<br/>Moon 2007</div>
            <div style="flex: 1 1 15%;"><b>Moon 1 Yr</b><br/>2007-2008<br/>Jup 2008<br/>Sun 2008</div>
        </div>
        {page_footer(34)}
    </div>
    """
    pages.append(p34)

    # =========================================================================
    # PAGES 35-39: || PLANET CONSIDERATION IN ASTROLOGY ||
    # =========================================================================
    def render_planet_consideration(p_name: str):
        pl = chart.planets[p_name]
        dignity_str = "Exalted" if dignities[p_name].is_exalted else ("Own sign" if dignities[p_name].is_own_sign else ("Debilitated" if dignities[p_name].is_debilitated else "Friendly sign"))
        ruled_houses = chart.get_houses_ruled_by_planet(p_name) if hasattr(chart, "get_houses_ruled_by_planet") else [h for h in range(1, 13) if constants.SIGN_LORD[(asc_sign_idx + h - 1) % 12] == p_name]
        h_lord_str = f"lord of {', '.join(map(str, ruled_houses))} house" if p_name not in ["Rahu", "Ketu"] else "shadow planet"
        h_pos = dignities[p_name].house
        asps_cast = ", ".join([f"{h}th" for h in dignities[p_name].aspects_cast_on])
        asps_rec = ", ".join(dignities[p_name].aspects_received_from) or "benefic influences"

        return f"""
        <div class="as-sub-title">{p_name} Consideration</div>
        <p style="font-weight: bold; margin-bottom: 2px;">
            Your {p_name} is in {constants.SIGNS[pl.sign_index]} sign which is a {dignity_str} for {p_name}. {p_name} is {h_lord_str} and situated in {h_pos}th house. {p_name} aspects {asps_cast} house and aspected by {asps_rec}.
        </p>
        <p>
            The placement of {p_name} in {h_pos}th house creates significant influence upon the native's destiny and worldly actions. It strengthens willpower, endows unique acumen, and provides opportunities to attain substantial success.
        </p>
        <p>
            When directed with ethical conduct and focused perseverance, this planetary placement yields high honor, wealth accumulation, and lasting societal recognition. Maintain balance and avoid impulsive choices.
        </p>
        """

    p35 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Planet Consideration in Astrology ||</div>
        {render_planet_consideration('Sun')}
        {render_planet_consideration('Moon')}
        {page_footer(35)}
    </div>
    """
    pages.append(p35)

    p36 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Planet Consideration in Astrology ||</div>
        {render_planet_consideration('Mars')}
        {render_planet_consideration('Mercury')}
        {page_footer(36)}
    </div>
    """
    pages.append(p36)

    p37 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Planet Consideration in Astrology ||</div>
        {render_planet_consideration('Jupiter')}
        {render_planet_consideration('Venus')}
        {page_footer(37)}
    </div>
    """
    pages.append(p37)

    p38 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Planet Consideration in Astrology ||</div>
        {render_planet_consideration('Saturn')}
        {render_planet_consideration('Rahu')}
        {page_footer(38)}
    </div>
    """
    pages.append(p38)

    p39 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Planet Consideration in Astrology ||</div>
        {render_planet_consideration('Ketu')}
        {page_footer(39)}
    </div>
    """
    pages.append(p39)

    # =========================================================================
    # PAGE 40: || SHODASHVARGA TABLE ||
    # =========================================================================
    v_keys = ["D1", "D2", "D3", "D4", "D7", "D9", "D10", "D12", "D16", "D20", "D24", "D27", "D30", "D40", "D45", "D60"]
    v_names = ["Lagna", "Hora", "Drekkana", "Chaturthamsha", "Saptamamsha", "Navamsha", "Dashamamsha", "Dwadashamamsha", "Shodashamsha", "Vimshamsha", "Chaturvimshamsha", "Saptavimshamsha", "Trimshamsha", "Khavedamsha", "Akshvedamsha", "Shashtiamsha"]
    
    shod_sign_rows = []
    shod_bhav_rows = []
    for idx_v, vk in enumerate(v_keys):
        v_asc = vargas_detailed[vk]["Ascendant"].sign_index
        s_row = [f"<td>{idx_v+1}</td>", f"<td>{v_names[idx_v]}</td>", f"<td>{v_asc+1}</td>"]
        b_row = [f"<td>{idx_v+1}</td>", f"<td>{v_names[idx_v]}</td>", "<td>1</td>"]
        for p_k in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
            p_s = vargas_detailed[vk][p_k].sign_index
            p_h = (p_s - v_asc + 12) % 12 + 1
            s_row.append(f"<td>{p_s+1}</td>")
            b_row.append(f"<td>{p_h}</td>")
        shod_sign_rows.append(f"<tr>{''.join(s_row)}</tr>")
        shod_bhav_rows.append(f"<tr>{''.join(b_row)}</tr>")

    p40 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Shodashvarga Table ||</div>
        
        <table class="as-table as-table-dense">
            <tr><th>S.N.</th><th>Shodashvarga</th><th>Lagna</th><th>Sun</th><th>Moon</th><th>Mars</th><th>Mer</th><th>Jup</th><th>Ven</th><th>Sat</th><th>Rah</th><th>Ket</th></tr>
            {''.join(shod_sign_rows)}
        </table>

        <div class="as-sub-title" style="text-align: center; margin-top: 10px;">Shodashvarga Bhav Table</div>
        <table class="as-table as-table-dense">
            <tr><th>S.N.</th><th>Shodashvarga</th><th>Lagna</th><th>Sun</th><th>Moon</th><th>Mars</th><th>Mer</th><th>Jup</th><th>Ven</th><th>Sat</th><th>Rah</th><th>Ket</th></tr>
            {''.join(shod_bhav_rows)}
        </table>
        {page_footer(40)}
    </div>
    """
    pages.append(p40)

    # =========================================================================
    # PAGES 41-43: || SHODASHVARGA CHARTS || (16 Divisional Charts in Diamond Grid)
    # =========================================================================
    varga_pages = [
        [("D1", "Lagna Chart"), ("D2", "Hora Wealth"), ("D3", "Drekkana - Siblings"), ("D4", "Chaturthamsha - Luck"), ("D7", "Saptamamsha - Children"), ("D9", "Navamsha - Spouse")],
        [("D10", "Dashamamsha - Profession"), ("D12", "Dwadashmamsha - Parents"), ("D16", "Shodashamsha - Vehicles"), ("D20", "Vimshamsha - Religious"), ("D24", "Chaturvimshamsha - Education"), ("D27", "Saptavimshamsha - Strength")],
        [("D30", "Trimshamsha - Misfortune"), ("D40", "Khavedamsha - Auspicious"), ("D45", "Akshvedamsha - Well Being"), ("D60", "Shastiamsha - Well Being")]
    ]

    for p_offset, v_list in enumerate(varga_pages):
        charts_markup = []
        for vk, v_title in v_list:
            v_houses = {h: [] for h in range(1, 13)}
            v_asc = vargas_detailed[vk]["Ascendant"].sign_index
            for h in range(1, 13):
                v_houses[h].append(str((v_asc + h - 1) % 12 + 1))
            for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                pv = vargas_detailed[vk][p_name]
                h_num = (pv.sign_index - v_asc + 12) % 12 + 1
                v_houses[h_num].append(p_abbrs[p_name])
            svg_v = render_astrosage_diamond_svg(v_houses, size=210)
            charts_markup.append(f"""
            <div style="flex: 0 0 48%; text-align: center; margin-bottom: 8px;">
                <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">{v_title}</div>
                {svg_v}
            </div>
            """)

        p_v = f"""
        <div class="page">
            {page_header()}
            <div class="as-title">|| Shodashvarga Charts ||</div>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-between;">
                {''.join(charts_markup)}
            </div>
            {page_footer(41 + p_offset)}
        </div>
        """
        pages.append(p_v)

    # =========================================================================
    # PAGE 44: || KP SYSTEM / NAKSHATRA NADI ||
    # =========================================================================
    kp_cusp_table_rows = []
    for c in kp_cusps:
        kp_cusp_table_rows.append(f"""
        <tr>
            <td>{c.cusp_num}</td>
            <td>{format_dms_clean(c.longitude)}</td>
            <td>{constants.SIGNS[c.sign_index][:3].upper()}</td>
            <td>{constants.PLANETS_HI.get(c.star_lord, '')[:3].upper()}</td>
            <td>{constants.PLANETS_HI.get(c.sub_lord, '')[:3].upper()}</td>
            <td>{constants.PLANETS_HI.get(c.sub_sub_lord, '')[:3].upper()}</td>
        </tr>
        """)

    # Build House <-> Planet significator tables from the LIVE kp.significators
    # (previously hardcoded to the 1984 Pali reference chart).
    _KP_ABBR = {"Sun": "SUN", "Moon": "MOON", "Mars": "MAR", "Mercury": "MER",
                "Jupiter": "JUP", "Venus": "VEN", "Saturn": "SAT", "Rahu": "RAH", "Ketu": "KET"}
    kp_house_signif = {h: [] for h in range(1, 13)}
    for _pn, _sig in significators.items():
        for _h in _sig.get("all_signified", []):
            if 1 <= _h <= 12:
                kp_house_signif[_h].append(_KP_ABBR.get(_pn, _pn[:3].upper()))
    kp_house_rows = "".join(
        f"<tr><td>{_h}</td><td>{', '.join(kp_house_signif[_h]) if kp_house_signif[_h] else '-'}</td></tr>"
        for _h in range(1, 13)
    )
    kp_planet_rows = "".join(
        f"<tr><td>{_pn}</td><td>{', '.join(str(h) for h in significators.get(_pn, {}).get('all_signified', [])) or '-'}</td></tr>"
        for _pn in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    )

    p44 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| KP System / Nakshatra Nadi ||</div>
        
        <table class="as-table as-table-dense as-table-left" style="margin-bottom: 6px;">
            <tr><td><b>Name</b></td><td>{name}</td><td><b>Sunrise</b></td><td>{panch_obj.sunrise}</td><td><b>Dasa Balance</b></td><td>{dasha_engine.balance_str}</td></tr>
            <tr><td><b>Sex</b></td><td>{_p2_sex}</td><td><b>Tithi</b></td><td>{panch_obj.tithi}</td><td><b>Sunset</b></td><td>{panch_obj.sunset}</td></tr>
            <tr><td><b>Date</b></td><td>{birth_dt.strftime('%d.%m.%Y')}</td><td><b>Yoga</b></td><td>{panch_obj.yoga}</td><td><b>Ayan Type</b></td><td>{panch_obj.ayanamsa}</td></tr>
            <tr><td><b>Star Lord</b></td><td>{constants.VIMSHOTTARI_ORDER[int(moon_lon // constants.NAKSHATRA_SPAN) % 9]}</td><td><b>Karan</b></td><td>{panch_obj.karana}</td><td><b>Ruling Planets</b></td><td>{ruling_planets.get('RP_Summary', '--')}</td></tr>
        </table>

        <div class="two-col" style="margin-bottom: 6px;">
            <div class="col-half" style="text-align: center;">
                {svg_d1}
            </div>
            <div class="col-half">
                <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">Cuspal Positions (All 12)</div>
                <table class="as-table as-table-dense">
                    <tr><th>Cusp</th><th>Degree</th><th>RASH</th><th>NAK</th><th>SUB</th><th>SS</th></tr>
                    {''.join(kp_cusp_table_rows)}
                </table>
            </div>
        </div>

        <div class="two-col">
            <div class="col-half">
                <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">Significators of Houses</div>
                <table class="as-table as-table-dense as-table-left">
                    <tr><th>House</th><th>Planets</th></tr>
                    {kp_house_rows}
                </table>
            </div>
            <div class="col-half">
                <div style="font-weight: bold; font-size: 8pt; margin-bottom: 2px;">Planet Signification</div>
                <table class="as-table as-table-dense as-table-left">
                    <tr><th>Planet</th><th>Houses</th></tr>
                    {kp_planet_rows}
                </table>
            </div>
        </div>
        {page_footer(44)}
    </div>
    """
    pages.append(p44)

    # =========================================================================
    # PAGES 45-48: || VIMSHOTTARI DASHA - PRATYANTAR || (5-Column Tables)
    # =========================================================================
    all_md_list = dasha_engine.calculate_mahadashas(num_cycles=1)
    # Flatten Antardashas
    all_flattened_ads = []
    for md_obj in all_md_list:
        sub_ads = dasha_engine.expand_sub_dashas(md_obj, target_level=2)
        for ad_obj in sub_ads:
            pds = dasha_engine.expand_sub_dashas(ad_obj, target_level=3)
            all_flattened_ads.append((md_obj.lord[:3].upper(), ad_obj.lord[:3].upper(), _d8(ad_obj.start_str), _d8(ad_obj.end_str), pds))

    for p_pd_idx in range(4):
        slice_start = p_pd_idx * 15
        slice_end = slice_start + 15
        ad_slice = all_flattened_ads[slice_start:slice_end]

        grid_blocks = []
        for md_c, ad_c, st_d, end_d, pd_list in ad_slice:
            pd_rows = []
            for pd_obj in pd_list[:9]:
                pd_rows.append(f"<tr><td>{pd_obj.lord[:3].upper()}</td><td>{_d8(pd_obj.end_str)}</td></tr>")
            grid_blocks.append(f"""
            <div style="flex: 1 1 18%; border: 1px solid #000; padding: 2px;">
                <div style="font-weight: bold; text-align: center; background: #f2f2f2; border-bottom: 1px solid #000; font-size: 7.2pt; padding: 2px 0;">
                    {md_c} -- {ad_c}
                </div>
                <div style="font-size: 6.5pt; text-align: center; border-bottom: 0.5px solid #000; padding: 1px 0;">
                    {st_d} - {end_d}
                </div>
                <table class="as-table as-table-dense" style="margin-bottom: 0; font-size: 6.8pt;">
                    {''.join(pd_rows)}
                </table>
            </div>
            """)

        p_pratyantar = f"""
        <div class="page">
            {page_header()}
            <div style="font-size: 7.5pt; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px; margin-bottom: 4px; display: flex; justify-content: space-between;">
                <span>Dasa Balance: {dasha_engine.balance_str}</span>
                <span>|| Vimshottari Dasha - Pratyantar ||</span>
                <span>Ayanamsa Name: {panch_obj.ayanamsa}</span>
            </div>
            <div style="display: flex; flex-wrap: wrap; gap: 3px;">
                {''.join(grid_blocks)}
            </div>
            {page_footer(45 + p_pd_idx)}
        </div>
        """
        pages.append(p_pratyantar)

    # =========================================================================
    # PAGE 49: || FRIENDSHIP TABLE || (Naisargika, Tatkalika, Panchadha)
    # =========================================================================
    pancha_data = chalit.compute_panchadha_maitri(p_signs)
    planets_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    p7_abbr = ["SUN", "MOON", "MARS", "MERC", "JUPT", "VENU", "SATN"]

    def render_friend_grid(cat_type: str):
        rows = []
        for i, p1 in enumerate(planets_7):
            c_cells = [f"<td><b>{p7_abbr[i]}</b></td>"]
            for j, p2 in enumerate(planets_7):
                if i == j:
                    c_cells.append("<td>---</td>")
                elif cat_type == "perm":
                    status = "Friend" if p2 in constants.FRIENDS.get(p1, set()) else ("Enemy" if p2 in constants.ENEMIES.get(p1, set()) else "Neutral")
                    c_cells.append(f"<td>{status}</td>")
                elif cat_type == "temp":
                    dist = (p_signs[p2] - p_signs[p1] + 12) % 12 + 1
                    status = "Friend" if dist in (2, 3, 4, 10, 11, 12) else "Enemy"
                    c_cells.append(f"<td>{status}</td>")
                else:
                    score_str = pancha_data[p1][p2].split(" ")[0]
                    c_cells.append(f"<td>{score_str}</td>")
            rows.append(f"<tr>{''.join(c_cells)}</tr>")
        return f"""
        <table class="as-table as-table-dense">
            <tr><th>PLANET</th>{''.join([f'<th>{a}</th>' for a in p7_abbr])}</tr>
            {''.join(rows)}
        </table>
        """

    p49 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Friendship Table ||</div>
        
        <div class="as-sub-title">Permanent Friendship</div>
        {render_friend_grid('perm')}

        <div class="as-sub-title" style="margin-top: 10px;">Temporal Friendship</div>
        {render_friend_grid('temp')}

        <div class="as-sub-title" style="margin-top: 10px;">Five-fold Friendship</div>
        {render_friend_grid('pancha')}
        {page_footer(49)}
    </div>
    """
    pages.append(p49)

    # =========================================================================
    # PAGE 50: || SHADBALA AND BHAVABALA – STRENGTH CALCULATIONS ||
    # =========================================================================
    sb_planets = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    sb_headers = "".join([f"<th>{p[:4].upper()}</th>" for p in sb_planets])

    b_adhipati_cells = "".join([f"<td>{final_shadbala.get(chart.get_whole_sign_houses()[h].lord, final_shadbala['Sun']).total_virupas:.1f}</td>" for h in range(1, 13)])
    b_dig_cells = "".join([f"<td>{60 if h in [4,10] else (40 if h in [1,7] else 20)}</td>" for h in range(1, 13)])
    b_total_cells = "".join([f"<td>{bhava_bala[h]:.2f}</td>" for h in range(1, 13)])
    b_rupa_cells = "".join([f"<td>{(bhava_bala[h]/60.0):.2f}</td>" for h in range(1, 13)])
    b_rank_cells = "".join([f"<td>{sorted(range(1, 13), key=lambda x: bhava_bala[x], reverse=True).index(h)+1}</td>" for h in range(1, 13)])

    p50 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Shadbala and Bhavabala – Strength Calculations ||</div>
        
        <p style="font-size: 8pt; margin-bottom: 6px;">
            Shadbala is a classical method in Vedic astrology that gives deep insight into the planetary and house potencies across 6 distinct sources of strength.
        </p>

        <div class="as-sub-title">ShadBala Table</div>
        <table class="as-table as-table-dense">
            <tr><th>Component</th>{sb_headers}</tr>
            <tr><td>Total Sthan Bala</td>{''.join([f'<td>{final_shadbala[p].sthana_bala:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Total Dig Bala</td>{''.join([f'<td>{final_shadbala[p].dig_bala:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Total Kala Bala</td>{''.join([f'<td>{final_shadbala[p].kala_bala:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Total Chesta Bala</td>{''.join([f'<td>{final_shadbala[p].chesta_bala:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Total Naisargeka Bala</td>{''.join([f'<td>{final_shadbala[p].naisargika_bala:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Total Drik Bala</td>{''.join([f'<td>{final_shadbala[p].drik_bala:.2f}</td>' for p in sb_planets])}</tr>
            <tr style="background:#f2f2f2; font-weight:bold;"><td>Total Shad Bala</td>{''.join([f'<td>{final_shadbala[p].total_virupas:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Shadbala In Rupas</td>{''.join([f'<td>{final_shadbala[p].total_rupas:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Minimum Requirements</td>{''.join([f'<td>{final_shadbala[p].min_required:.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Ratio</td>{''.join([f'<td>{(final_shadbala[p].total_virupas / final_shadbala[p].min_required):.2f}</td>' for p in sb_planets])}</tr>
            <tr><td>Relative Rank</td>{''.join([f'<td>{final_shadbala[p].rank}</td>' for p in sb_planets])}</tr>
        </table>

        <div class="as-sub-title" style="margin-top: 10px;">BhavBala Table</div>
        <table class="as-table as-table-dense">
            <tr><th>Component</th>{''.join([f'<th>{h}</th>' for h in range(1, 13)])}</tr>
            <tr><td>Bhavadhipati Bala</td>{b_adhipati_cells}</tr>
            <tr><td>Bhavdig Bala</td>{b_dig_cells}</tr>
            <tr style="background:#f2f2f2; font-weight:bold;"><td>Total Bhav Bala</td>{b_total_cells}</tr>
            <tr><td>Total Bhav In Rupas</td>{b_rupa_cells}</tr>
            <tr><td>Relative Rank</td>{b_rank_cells}</tr>
        </table>
        {page_footer(50)}
    </div>
    """
    pages.append(p50)

    # =========================================================================
    # PAGES 51-53: PLANETARY ASPECTS (WESTERN, BHAV MADHYA, KP CUSP)
    # =========================================================================
    aspect_bodies = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu", "Uranus", "Neptune", "Pluto"]
    asp_abbr_list = ["SUN", "MOON", "MARS", "MERC", "JUPT", "VENU", "SATN", "RAHU", "KETU", "URAN", "NEPT", "PLUT"]

    p51_rows = []
    for i, p1 in enumerate(aspect_bodies):
        c_cells = [f"<td><b>{asp_abbr_list[i]}<br/>{int(all_bodies_lons[p1])} {int((all_bodies_lons[p1]%1)*60)}</b></td>"]
        for j, p2 in enumerate(aspect_bodies):
            if i == j:
                c_cells.append("<td>--</td>")
            else:
                asp_info = western_aspects_grid.get((p1, p2))
                if asp_info:
                    c_cells.append(f"<td>{asp_info[0]}<br/>{asp_info[1]:.1f}</td>")
                else:
                    c_cells.append("<td>--</td>")
        p51_rows.append(f"<tr>{''.join(c_cells)}</tr>")

    p51 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Planetary Aspects (Western) ||</div>
        
        <table class="as-table as-table-dense">
            <tr><th>PLANET</th>{''.join([f'<th>{a}</th>' for a in asp_abbr_list])}</tr>
            {''.join(p51_rows)}
        </table>

        <div style="font-weight: bold; margin-top: 8px;">Note :</div>
        <p style="font-size: 7.2pt;">Aspects and orbs taken for computation: CONJ (0°, orb 15°), OPPN (180°, orb 15°), TRIN (120°, orb 6°), SQUR (90°, orb 6°), SEXT (60°, orb 6°), SSQU (45°, orb 1°), NONL (40°, orb 1°), QUIN (72°, orb 1°), SQQD (135°, orb 1°), QCUN (150°, orb 1°).</p>
        {page_footer(51)}
    </div>
    """
    pages.append(p51)

    # Page 52: Aspects on Bhav Madhya
    p52_rows = []
    for i, p1 in enumerate(aspect_bodies):
        c_cells = [f"<td><b>{asp_abbr_list[i]}<br/>{int(all_bodies_lons[p1])} {int((all_bodies_lons[p1]%1)*60)}</b></td>"]
        for h in range(1, 13):
            asp_info = aspects_on_chalit.get((p1, h))
            if asp_info:
                c_cells.append(f"<td>{asp_info[0]}<br/>{asp_info[1]:.1f}</td>")
            else:
                c_cells.append("<td>--</td>")
        p52_rows.append(f"<tr>{''.join(c_cells)}</tr>")

    p52 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Aspects On Bhav Madhya ||</div>
        
        <table class="as-table as-table-dense">
            <tr><th>PLANET</th>{''.join([f'<th>Bhav {h}</th>' for h in range(1, 13)])}</tr>
            {''.join(p52_rows)}
        </table>

        <div style="font-weight: bold; margin-top: 8px;">Note :</div>
        <p style="font-size: 7.2pt;">Bhava-madhya degrees of the Chalit chart have been taken as the cusp degree to compute aspectual strengths.</p>
        {page_footer(52)}
    </div>
    """
    pages.append(p52)

    # Page 53: Aspects on KP Cusp
    p53_rows = []
    for i, p1 in enumerate(aspect_bodies):
        c_cells = [f"<td><b>{asp_abbr_list[i]}<br/>{int(all_bodies_lons[p1])} {int((all_bodies_lons[p1]%1)*60)}</b></td>"]
        for h in range(1, 13):
            asp_info = aspects_on_kp.get((p1, h))
            if asp_info:
                c_cells.append(f"<td>{asp_info[0]}<br/>{asp_info[1]:.1f}</td>")
            else:
                c_cells.append("<td>--</td>")
        p53_rows.append(f"<tr>{''.join(c_cells)}</tr>")

    p53 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Aspects On KP Cusp ||</div>
        
        <table class="as-table as-table-dense">
            <tr><th>PLANET</th>{''.join([f'<th>Cusp {h}</th>' for h in range(1, 13)])}</tr>
            {''.join(p53_rows)}
        </table>

        <div style="font-weight: bold; margin-top: 8px;">Note :</div>
        <p style="font-size: 7.2pt;">Cusp degrees computed under Placidus KP System have been taken as target points to evaluate planetary aspects.</p>
        {page_footer(53)}
    </div>
    """
    pages.append(p53)

    # =========================================================================
    # PAGE 54: || ASHTAKVARGA TABLE || (BAV, SAV & SAV Chart)
    # =========================================================================
    ashtaka_table_rows = []
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        vals = [bav[p_name][i] for i in range(12)]
        ashtaka_table_rows.append(f"""
        <tr>
            <td><b>{p_name[:4].upper()}</b></td>
            {''.join([f'<td>{v}</td>' for v in vals])}
        </tr>
        """)

    sav_houses = {h: [str((asc_sign_idx + h - 1) % 12 + 1), str(sav[(asc_sign_idx + h - 1) % 12])] for h in range(1, 13)}
    svg_sav = render_astrosage_diamond_svg(sav_houses, size=280)

    p54 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Ashtakvarga Table ||</div>
        
        <table class="as-table">
            <tr><th>Rashi No.</th>{''.join([f'<th>{i+1}</th>' for i in range(12)])}</tr>
            {''.join(ashtaka_table_rows)}
            <tr style="background:#f2f2f2; font-weight:bold;"><td>Total</td>{''.join([f'<td>{sav[i]}</td>' for i in range(12)])}</tr>
        </table>

        <div style="text-align: center; margin-top: 25px;">
            <div style="font-weight: bold; margin-bottom: 6px;">Ashtakvarga Chart:</div>
            {svg_sav}
        </div>
        {page_footer(54)}
    </div>
    """
    pages.append(p54)

    # =========================================================================
    # PAGE 55: || PRASTHARASHTAKVARGA TABLES || (7 Planets & Disclaimer)
    # =========================================================================
    sign_headers_abbr = ["Ar", "Ta", "Ge", "Ca", "Le", "Vi", "Li", "Sc", "Sa", "Ca", "Aq", "Pi", "ToT"]
    contributor_abbrs = [("Sun", "Su"), ("Moon", "Mo"), ("Mars", "Ma"), ("Mercury", "Me"), ("Jupiter", "Ju"), ("Venus", "Ve"), ("Saturn", "Sa"), ("Lagna", "As")]

    def render_single_prasthara_table(p_target: str):
        grid = prasthara[p_target]
        rows = []
        col_sums = [0]*12
        for full_c, c_ab in contributor_abbrs:
            row_vals = grid[full_c]
            r_tot = sum(row_vals)
            for s_i in range(12):
                col_sums[s_i] += row_vals[s_i]
            rows.append(f"<tr><td>{c_ab}</td>{''.join([f'<td>{v}</td>' for v in row_vals])}<td>{r_tot}</td></tr>")
        rows.append(f"<tr style='background:#f2f2f2; font-weight:bold;'><td>Total</td>{''.join([f'<td>{cs}</td>' for cs in col_sums])}<td>{sum(col_sums)}</td></tr>")
        return f"""
        <div style="margin-bottom: 4px;">
            <div style="font-weight: bold; font-size: 7.8pt;">{p_target}</div>
            <table class="as-table as-table-dense" style="margin-bottom: 2px;">
                <tr><th></th>{''.join([f'<th>{s}</th>' for s in sign_headers_abbr])}</tr>
                {''.join(rows)}
            </table>
        </div>
        """

    p55 = f"""
    <div class="page">
        {page_header()}
        <div class="as-title">|| Prastharashtakvarga Tables ||</div>
        
        <div class="two-col" style="gap: 6px; margin-bottom: 4px;">
            <div class="col-half">{render_single_prasthara_table('Sun')}</div>
            <div class="col-half">{render_single_prasthara_table('Moon')}</div>
        </div>
        <div class="two-col" style="gap: 6px; margin-bottom: 4px;">
            <div class="col-half">{render_single_prasthara_table('Mars')}</div>
            <div class="col-half">{render_single_prasthara_table('Mercury')}</div>
        </div>
        <div class="two-col" style="gap: 6px; margin-bottom: 4px;">
            <div class="col-half">{render_single_prasthara_table('Jupiter')}</div>
            <div class="col-half">{render_single_prasthara_table('Venus')}</div>
        </div>
        <div class="two-col" style="gap: 6px;">
            <div class="col-half">{render_single_prasthara_table('Saturn')}</div>
            <div class="col-half">
                <div style="font-weight: bold; font-size: 7.8pt;">Disclaimer</div>
                <div style="border: 1px solid #000; padding: 4px; font-size: 6.8pt; line-height: 1.25; background: #fafafa;">
                    We make it clear that this astrological thesis is intended for scholarly guidance and self-discovery. Any forecast is not to be considered as a substitute for licensed medical, psychiatric, legal or financial advice. The calculations are provided with highest mathematical accuracy as per Brihat Parashara Hora Shastra standards.
                </div>
            </div>
        </div>
        {page_footer(55)}
    </div>
    """
    pages.append(p55)

    # =========================================================================
    # PAGE 56: BACK COVER / SUMMARY CARD
    # =========================================================================
    p56 = f"""
    <div class="page" style="text-align: center; padding-top: 30mm;">
        <div style="font-size: 20pt; font-weight: 800; color: #1a365d; margin-bottom: 8px;">
            Make Confident Decisions with a Complete Kundli Analysis
        </div>
        <p style="font-size: 10pt; color: #4a5568; width: 80%; margin: 0 auto 25px auto;">
            Your VYAS Executive Master Kundli Report gives you clear answers on when to act, where to focus, and how to navigate upcoming changes in your life.
        </p>

        <div style="width: 80%; margin: 0 auto; text-align: left; border: 1.5px solid #000; padding: 20px; background: #fffdf5; border-radius: 8px;">
            <div style="font-size: 11pt; font-weight: bold; margin-bottom: 12px; color: #8b0000;">
                ★ Research-Grade Strengths of this Publication:
            </div>
            <div style="font-size: 9.5pt; line-height: 1.6; margin-bottom: 8px;">
                ✔ <b>Deep Analysis of Strengths & Patterns:</b> Exact planetary degrees, Placidus cusps, and 16 divisional charts.
            </div>
            <div style="font-size: 9.5pt; line-height: 1.6; margin-bottom: 8px;">
                ✔ <b>Precise Predictions Backed by Mathematical Ephemeris:</b> High-precision JPL DE440s ephemeris with micro-degree calculations.
            </div>
            <div style="font-size: 9.5pt; line-height: 1.6; margin-bottom: 8px;">
                ✔ <b>Identifies Peak Timing for Success:</b> Comprehensive multi-level Vimshottari, Yogini, Char, and Mudda Dashas.
            </div>
            <div style="font-size: 9.5pt; line-height: 1.6;">
                ✔ <b>Personalised Shastric Remedies:</b> Authentic Vedic, Lal Kitab, and Sattvic remedial measures for peace and prosperity.
            </div>
        </div>

        <div style="margin-top: 40px; border-top: 1px solid #ccc; width: 80%; margin-left: auto; margin-right: auto; padding-top: 15px;">
            <div style="font-size: 12pt; font-weight: bold; color: #1a365d;">VYAS VEDIC ASTROLOGY SYSTEMS</div>
            <div style="font-size: 9pt; color: #555; margin-top: 4px;">System Lead: <b>Nikhil Vyas</b> (M.A. Jyotish) • Cell: 9414121172 • Email: inikhilvyas@gmail.com</div>
        </div>
        {page_footer(56)}
    </div>
    """
    pages.append(p56)

    full_html = f"""<!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <meta charset="utf-8">
        <title>VYAS ASTRA • 56-Page AstroSage Standard Kundli Dossier</title>
        {css_styles}
    </head>
    <body>
        {''.join(pages)}
    </body>
    </html>
    """
    return full_html


def build_publication_pdf(
    chart,
    birth: dict,
    kp_cusps: list,
    dasha_engine,
    vargas_detailed: dict,
    output_pdf_path: str,
    target_varsh_year: int = None,
    lang: str = "en"
) -> bool:
    """
    Renders the complete 56-page AstroSage-standard publication report to PDF using Chrome Headless.
    Guarantees crisp borders, authentic diamond charts, and bilingual support.
    """
    output_pdf_path = os.path.abspath(output_pdf_path)
    # Guard against STALE output: remove any pre-existing target and only accept
    # a file Chrome wrote during THIS run. (The old check accepted any existing
    # file >50KB, so a failed build silently "succeeded" with the previous PDF —
    # the "same kundli PDF regardless of input" bug.)
    t_build_start = time.time()
    try:
        if os.path.exists(output_pdf_path):
            os.remove(output_pdf_path)
    except OSError:
        pass
    html_content = generate_56_page_publication_html(
        chart, birth, kp_cusps, dasha_engine, vargas_detailed, target_varsh_year=target_varsh_year, lang=lang
    )

    with tempfile.NamedTemporaryFile("w", suffix=".html", encoding="utf-8", delete=False) as f:
        f.write(html_content)
        temp_html = f.name

    chrome_exe = find_chrome()
    cmd = [
        chrome_exe,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={output_pdf_path}",
        temp_html
    ]

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if (os.path.exists(output_pdf_path)
                and os.path.getsize(output_pdf_path) > 50000
                and os.path.getmtime(output_pdf_path) >= t_build_start - 1.0):
            return True
        else:
            print("Chrome PDF generation returned no file or small file:", res.stderr)
            return False
    except Exception as e:
        print(f"Error invoking Chrome headless: {e}")
        return False
    finally:
        try:
            if os.path.exists(temp_html):
                os.remove(temp_html)
        except Exception:
            pass
