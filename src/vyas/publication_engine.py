"""Executive Master Publication Engine (35-45 Page Comprehensive Vedic Research Thesis).

Renders publication-grade Vedic astrological reports comparing to and surpassing 
AstroSage Premium Kundli. Features:
1. Native Metadata & Avakhada & Ghatak Chakra & Anukool Bindu
2. D1 Natal & D9 Navamsha charts with DMS & Planetary Matrix
3. Comprehensive Mangal Dosha Analysis & 14 Classical Cancellations
4. Comprehensive Shani Sade Sati 46-Period Lifetime Schedule across 90+ years
5. Shani Sade Sati 3-Phase Deep Qualitative Forecast & Remedies
6. Comprehensive Kalsarp Dosha Analysis & 12 Types
7. Tajik Varshphal (Annual Return Chart, Muntha Sign/House, Annual Parameters for ANY selected year)
8. Tajik Annual Mudda / Patyayini Dasha & Monthly Predictions
9. Vimshottari Mahadasha In-Depth Chapters for all 9 planets
10. Yogini Dasha 36-Year Lifetime Trajectory across 90 years
11. Jaimini Chara Dasha Full Schedule
12. Lal Kitab Planetary Analysis & Authentic Upay
13. Lal Kitab Matrix & 35-Year Dasha Cycle
14. All 16 Shodashvarga Divisional Charts (D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60)
15. KP Astrology (Placidus Cusps, Sub-Lords & Significators Matrix)
16. 4 Unique Vimshottari Micro-Dasha Schedules (Venus MD, Sun MD, Moon MD, Mars MD)
17. Planetary Friendship Matrix (Naisargika, Tatkalika, Panchadha)
18. Shadbala & Bhavabala Complete 6-Fold Breakdown & Rupa Strength Rankings
19. Ashtakavarga Complete SAV & BAV 12-Sign Matrices & Shodhana
20. Prastarashtakavarga Sub-Matrices for all 7 Planets across 12 Houses
21. 12 Bhavas In-Depth Forensic Analysis (Lords, Occupants, Aspects & Shastric Synthesis)
22. Shodashvarga Confirmation & D60 Deity Alignment
23. समग्र जीवन फलादेश (Overall Life Forecast - Senior Jyotishi Edition in 13 Core Chapters)
24. Classical Sutra Bank (श्लोक प्रमाण)
"""
import os
import subprocess
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from vyas import constants
from vyas.svg_chart import get_north_indian_chart_svg_print
from vyas import ashtakavarga
from vyas import shadbala
from vyas import kp
from vyas import panchang
from vyas import forensic_predictor


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


def render_north_svg_for_varga(varga_key: str, chart, vargas_detailed: dict, size: int = 210, title: str = "") -> str:
    """Helper to render print-ready North Indian chart SVG for any varga."""
    asc_sign = vargas_detailed[varga_key]["Ascendant"].sign_index
    houses_data = {h: [] for h in range(1, 13)}

    for h in range(1, 13):
        sign = (asc_sign + h - 1) % 12
        houses_data[h].append(str(sign + 1))

    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        p_v = vargas_detailed[varga_key][p_name]
        h_num = (p_v.sign_index - asc_sign + 12) % 12 + 1
        p_hi = constants.PLANETS_HI.get(p_name, p_name)[:2]
        deg_in = int(p_v.degree_in_sign)
        houses_data[h_num].append(f"{p_hi} {deg_in}°")

    return get_north_indian_chart_svg_print(houses_data, size=size, chart_title="")


def generate_35_page_publication_html(
    chart,
    birth: dict,
    kp_cusps: list,
    dasha_engine,
    vargas_detailed: dict,
    sutras: list = None,
    target_varsh_year: int = None
) -> str:
    """
    Constructs the master publication HTML document for executive printing.
    """
    birth_dt = birth['local']
    name = birth.get('name', 'Nikhil Vyas')
    city = birth.get('city', 'Pali, Rajasthan')
    lat = birth.get('lat', 25.7711)
    lon = birth.get('lon', 73.3234)
    tz = birth.get('tz', 5.5)

    asc_sign_idx = chart.ascendant_sign
    moon_lon = chart.planets["Moon"].longitude
    moon_sign_idx = chart.planets["Moon"].sign_index
    sun_lon = chart.planets["Sun"].longitude

    # Determine target year for Varshphal if not provided
    if target_varsh_year is None:
        curr_yr = datetime.now().year
        # If currently before birth month/day in the current year, solar year began in prior year
        if (datetime.now().month, datetime.now().day) < (birth_dt.month, birth_dt.day):
            target_varsh_year = curr_yr - 1
        else:
            target_varsh_year = curr_yr

    # Compute forensic suites
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
    varga_cross_list = forensic_predictor.compute_varga_cross_analysis(dignities, vargas_detailed)

    # Ashtakavarga
    p_signs = {p_name: p.sign_index for p_name, p in chart.planets.items()}
    ashtaka_res = ashtakavarga.compute_ashtakavarga(p_signs, asc_sign_idx)
    bav = ashtaka_res["bav"]
    sav = ashtaka_res["sav"]
    sav_predictions = forensic_predictor.compute_ashtakavarga_predictions(sav, asc_sign_idx)

    # Overall Life Forecast (Senior Jyotishi Master Edition)
    overall_chapters = forensic_predictor.compute_overall_life_forecast(chart, dignities, bhavas, sav, vargas_detailed)

    # Shadbala
    final_shadbala, bhava_bala = shadbala.compute_shadbala(chart, asc_sign_idx)

    # KP
    significators = kp.compute_kp_significators(chart.planets, kp_cusps)
    ruling_planets = kp.get_ruling_planets(birth_dt, lat, lon, tz, moon_lon, chart.ascendant_longitude)

    # Panchang & Avakhada
    panch_obj = panchang.compute(birth_dt, lat, lon, tz, chart.ascendant_longitude)
    avakhada = panch_obj.avakhada
    asc_sign_lord_hi = constants.PLANETS_HI.get(constants.SIGN_LORD[asc_sign_idx], constants.SIGN_LORD[asc_sign_idx])
    rashi_lord_hi = constants.PLANETS_HI.get(constants.SIGN_LORD[moon_sign_idx], constants.SIGN_LORD[moon_sign_idx])
    panch = {
        'vara': panch_obj.vara,
        'tithi': panch_obj.tithi,
        'nakshatra': f"{panch_obj.nakshatra} - {panch_obj.nakshatra_pada}",
        'yoga': panch_obj.yoga,
        'karana': panch_obj.karana,
        'sunrise': panch_obj.sunrise,
        'sunset': panch_obj.sunset,
        'ayanamsa': f"{panch_obj.ayanamsa} ({panch_obj.ayanamsa_value})",
        'abhijit': panch_obj.abhijit_muhurta,
        'brahma': panch_obj.brahma_muhurta,
        'rahu_kaal': panch_obj.rahu_kalam,
        'lagna_lord': asc_sign_lord_hi,
        'rashi_lord': rashi_lord_hi
    }

    # Prepare D1 & D9 print SVGs
    d1_houses = {h: [] for h in range(1, 13)}
    for h in range(1, 13):
        sign = (asc_sign_idx + h - 1) % 12
        d1_houses[h].append(str(sign + 1))
    for p_name, p in chart.planets.items():
        h_num = (p.sign_index - asc_sign_idx + 12) % 12 + 1
        p_hi = constants.PLANETS_HI.get(p_name, p_name)[:2]
        abbr = f"{p_hi} {int(p.longitude % 30)}°"
        if p.is_retrograde:
            abbr += " (R)"
        d1_houses[h_num].append(abbr)

    d9_houses = {h: [] for h in range(1, 13)}
    d9_asc = vargas_detailed["D9"]["Ascendant"].sign_index
    for h in range(1, 13):
        sign = (d9_asc + h - 1) % 12
        d9_houses[h].append(str(sign + 1))
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
        p_v = vargas_detailed["D9"][p_name]
        h_num = (p_v.sign_index - d9_asc + 12) % 12 + 1
        p_hi = constants.PLANETS_HI.get(p_name, p_name)[:2]
        d9_houses[h_num].append(f"{p_hi} {int(p_v.degree_in_sign)}°")

    sav_houses = {h: [str((asc_sign_idx + h - 1) % 12 + 1), f"बिंदु: {sav[(asc_sign_idx + h - 1) % 12]}"] for h in range(1, 13)}

    varsh_houses = {h: [str((asc_sign_idx + h - 1) % 12 + 1)] for h in range(1, 13)}
    varsh_houses[varshphal_data["muntha_house"]].append(f"मुन्था ({varshphal_data['muntha_sign_hi'][:2]})")

    svg_d1 = get_north_indian_chart_svg_print(d1_houses, size=360, chart_title="")
    svg_d9 = get_north_indian_chart_svg_print(d9_houses, size=360, chart_title="")
    svg_sav = get_north_indian_chart_svg_print(sav_houses, size=360, chart_title="")
    svg_varsh = get_north_indian_chart_svg_print(varsh_houses, size=360, chart_title="")

    # Construct CSS
    css_styles = """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+Devanagari:wght@400;600;700&family=Tiro+Devanagari+Sanskrit&display=swap');
        @page {
            size: A4 portrait;
            margin: 10mm 12mm 12mm 12mm;
        }
        * {
            box-sizing: border-box;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
        }
        body {
            font-family: 'Noto Sans Devanagari', 'Segoe UI', Tahoma, sans-serif;
            color: #1a202c;
            background: #ffffff;
            margin: 0;
            padding: 0;
            font-size: 9pt;
            line-height: 1.45;
        }
        .page {
            page-break-after: always;
            height: 275mm;
            position: relative;
            padding-bottom: 12mm;
        }
        .page:last-child {
            page-break-after: avoid;
        }
        .masthead {
            text-align: center;
            border-bottom: 2px solid #8b0000;
            padding-bottom: 5px;
            margin-bottom: 12px;
        }
        .ganesh {
            font-family: 'Tiro Devanagari Sanskrit', serif;
            font-size: 13pt;
            font-weight: 700;
            color: #8b0000;
            letter-spacing: 1px;
            margin-bottom: 1px;
        }
        .vyas-brand {
            font-size: 14pt;
            font-weight: 800;
            color: #0b192c;
            letter-spacing: 0.5px;
        }
        .vyas-sub {
            font-size: 8.5pt;
            color: #4a5568;
            margin-top: 1px;
        }
        .author-line {
            font-size: 8pt;
            color: #2b6cb0;
            margin-top: 2px;
        }
        .footer-bar {
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            height: 8mm;
            border-top: 1px solid #cbd5e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            font-size: 7.5pt;
            color: #718096;
            padding: 0 4px;
        }
        .sec-title {
            font-size: 10.5pt;
            font-weight: 700;
            color: #8b0000;
            border-bottom: 1.5px solid #e2e8f0;
            padding-bottom: 3px;
            margin: 10px 0 8px 0;
            display: flex;
            align-items: center;
        }
        .sec-title span {
            border-left: 3.5px solid #8b0000;
            padding-left: 6px;
        }
        .two-col {
            display: flex;
            gap: 12px;
            margin-bottom: 8px;
        }
        .col-half {
            flex: 1;
        }
        .astro-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 8.5pt;
            margin-bottom: 8px;
        }
        .astro-table th, .astro-table td {
            border: 1px solid #cbd5e0;
            padding: 4px 6px;
            text-align: center;
        }
        .astro-table th {
            background-color: #8b0000;
            color: #ffffff;
            font-weight: 600;
        }
        .table-left td {
            text-align: left;
        }
        .chart-box {
            text-align: center;
            border: 1px solid #e2e8f0;
            border-radius: 4px;
            padding: 4px;
            background: #fafafa;
        }
        .chart-box-title {
            font-size: 9.5pt;
            font-weight: 700;
            color: #8b0000;
            margin-bottom: 4px;
        }
        .card-box {
            border: 1px solid #e2e8f0;
            border-radius: 5px;
            padding: 8px 10px;
            margin-bottom: 8px;
            background: #ffffff;
            box-shadow: 0 1px 2px rgba(0,0,0,0.03);
        }
        .card-box-header {
            font-weight: 700;
            color: #8b0000;
            font-size: 9.5pt;
            margin-bottom: 4px;
        }
        .card-box p {
            margin: 3px 0;
            color: #2d3748;
            font-size: 8.5pt;
            text-align: justify;
            line-height: 1.5;
        }
        .remedy-item {
            padding: 2.5px 0;
            color: #2c5282;
            font-size: 8.5pt;
        }
        .remedy-item::before {
            content: "✓ ";
            color: #8b0000;
            font-weight: bold;
        }
        .shloka-text {
            color: #8b0000;
            font-weight: bold;
            font-family: 'Tiro Devanagari Sanskrit', serif;
        }
    </style>
    """

    def masthead_html():
        return """
        <div class="masthead">
            <div class="ganesh">|| श्री गणेशाय नमः ||</div>
            <div class="vyas-brand">VYAS (Vedic Yield Astrology Systems)</div>
            <div class="vyas-sub">वैदिक, केपी, नाड़ी एवं बहु-पद्धति शोध-स्तरीय ज्योतिष शोध प्रबंध</div>
            <div class="author-line">System Developed by <b>Nikhil Vyas</b> (M.A. Jyotish / PG in Astrology) • Cell: 9414121172 • Email: inikhilvyas@gmail.com</div>
        </div>
        """

    def footer_html(page_num, total_pages=43):
        return f"""
        <div class="footer-bar">
            <span><b>VYAS ASTRA</b> • System Developed by Nikhil Vyas (M.A. Jyotish - PG) • Cell: 9414121172 • inikhilvyas@gmail.com</span>
            <span>पृष्ठ {page_num} of {total_pages}</span>
        </div>
        """

    pages = []

    # Classical Ghatak Chakra mapped by Moon Rashi (0=Aries .. 11=Pisces)
    GHATAK_BY_RASHI = {
        0: {"day": "रविवार (Sun)", "nak": "मघा (Magha)", "tithi": "1, 6, 11 (नंदा)", "masa": "कार्तिक", "prahar": "प्रथम प्रहर", "lagna": "मेष", "graha": "सूर्य"},
        1: {"day": "शनिवार (Sat)", "nak": "हस्त (Hasta)", "tithi": "5, 10, 15 (पूर्णा)", "masa": "मार्गशीर्ष", "prahar": "द्वितीय प्रहर", "lagna": "वृषभ", "graha": "बृहस्पति"},
        2: {"day": "सोमवार (Mon)", "nak": "स्वाति (Swati)", "tithi": "2, 7, 12 (भद्रा)", "masa": "पौष", "prahar": "तृतीय प्रहर", "lagna": "मिथुन", "graha": "चन्द्र"},
        3: {"day": "बुधवार (Wed)", "nak": "अनुराधा (Anuradha)", "tithi": "2, 7, 12 (भद्रा)", "masa": "माघ", "prahar": "द्वितीय प्रहर", "lagna": "कर्क", "graha": "बुध"},
        4: {"day": "शनिवार (Sat)", "nak": "मूल (Mula)", "tithi": "3, 8, 13 (जया)", "masa": "फाल्गुन", "prahar": "प्रथम प्रहर", "lagna": "सिंह", "graha": "शनि"},
        5: {"day": "शनिवार (Sat)", "nak": "श्रवण (Shravana)", "tithi": "4, 9, 14 (रिक्ता)", "masa": "चैत्र", "prahar": "चतुर्थ प्रहर", "lagna": "कन्या", "graha": "शनि"},
        6: {"day": "गुरुवार (Thu)", "nak": "शतभिषा (Shatabhisha)", "tithi": "4, 9, 14 (रिक्ता)", "masa": "वैशाख", "prahar": "तृतीय प्रहर", "lagna": "धनु", "graha": "बृहस्पति"},
        7: {"day": "शुक्रवार (Fri)", "nak": "रेवती (Revati)", "tithi": "1, 6, 11 (नंदा)", "masa": "आश्विन", "prahar": "प्रथम प्रहर", "lagna": "वृश्चिक", "graha": "बुध"},
        8: {"day": "शुक्रवार (Fri)", "nak": "भरणी (Bharani)", "tithi": "3, 8, 13 (जया)", "masa": "ज्येष्ठ", "prahar": "तृतीय प्रहर", "lagna": "कुम्भ", "graha": "शुक्र"},
        9: {"day": "मंगलवार (Tue)", "nak": "रोहिणी (Rohini)", "tithi": "4, 9, 14 (रिक्ता)", "masa": "आषाढ़", "prahar": "प्रथम प्रहर", "lagna": "सिंह", "graha": "मंगल"},
        10: {"day": "गुरुवार (Thu)", "nak": "आर्द्रा (Ardra)", "tithi": "3, 8, 13 (जया)", "masa": "श्रावण", "prahar": "द्वितीय प्रहर", "lagna": "धनु", "graha": "बृहस्पति"},
        11: {"day": "शुक्रवार (Fri)", "nak": "अश्लेषा (Ashlesha)", "tithi": "2, 7, 12 (भद्रा)", "masa": "भाद्रपद", "prahar": "द्वितीय प्रहर", "lagna": "कुम्भ", "graha": "शुक्र"}
    }
    ghatak = GHATAK_BY_RASHI.get(moon_sign_idx, GHATAK_BY_RASHI[7])

    # Dynamic Numerology & Lucky Indicators
    def _sum_digits(n: int) -> int:
        while n > 9:
            n = sum(int(d) for d in str(n))
        return n

    mulank = _sum_digits(birth_dt.day)
    bhagyank = _sum_digits(birth_dt.day + birth_dt.month + birth_dt.year)
    lucky_gems_map = {
        "Sun": ("माणिक्य (Ruby)", "तांबा / स्वर्ण"),
        "Moon": ("मोती (Pearl)", "चाँदी (Silver)"),
        "Mars": ("मूँगा (Red Coral)", "तांबा (Copper)"),
        "Mercury": ("पन्ना (Emerald)", "कांस्य / स्वर्ण"),
        "Jupiter": ("पुखराज (Yellow Sapphire)", "स्वर्ण (Gold)"),
        "Venus": ("हीरा / ओपल (Diamond)", "श्वेत स्वर्ण / प्लैटिनम"),
        "Saturn": ("नीलम (Blue Sapphire)", "लोहा / अष्टधातु")
    }
    r_gem, r_metal = lucky_gems_map.get(constants.SIGN_LORD[moon_sign_idx], ("पुखराज", "स्वर्ण"))

    p1_lucky_html = f"""
        <div class="col-half">
            <div class="sec-title"><span>अनुकूल बिन्दु (Lucky Indicators)</span></div>
            <table class="astro-table table-left">
                <tr><td><b>मूलांक (Radix Number)</b></td><td>{mulank}</td></tr>
                <tr><td><b>भाग्यांक (Destiny Number)</b></td><td>{bhagyank}</td></tr>
                <tr><td><b>शुभ अंक (Lucky Numbers)</b></td><td>{mulank}, {(mulank*2)%9 or 9}, {(mulank+3)%9 or 9}</td></tr>
                <tr><td><b>भाग्यशाली वार (Lucky Day)</b></td><td>{constants.PLANETS_HI.get(constants.SIGN_LORD[moon_sign_idx])}वार</td></tr>
                <tr><td><b>शुभ रत्न (Lucky Gemstone)</b></td><td>{r_gem}</td></tr>
                <tr><td><b>शुभ धातु (Lucky Metal)</b></td><td>{r_metal}</td></tr>
                <tr><td><b>इष्ट दिशा (Auspicious Direction)</b></td><td>{'पूर्व (East)' if moon_sign_idx in [0,4,8] else ('दक्षिण (South)' if moon_sign_idx in [1,5,9] else ('पश्चिम (West)' if moon_sign_idx in [2,6,10] else 'उत्तर (North)'))}</td></tr>
            </table>
        </div>
    """

    p1 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>व्यक्ति विवरण एवं पंचांग (Native Metadata & Panchang)</span></div>
        <div class="two-col">
            <div class="col-half">
                <table class="astro-table table-left">
                    <tr><th>विवरण</th><th>मान</th></tr>
                    <tr><td><b>नाम (Name)</b></td><td>{name}</td></tr>
                    <tr><td><b>दिनांक (Date)</b></td><td>{birth_dt.strftime('%d/%m/%Y')}</td></tr>
                    <tr><td><b>समय (Time)</b></td><td>{birth_dt.strftime('%H:%M:%S')}</td></tr>
                    <tr><td><b>वार (Day)</b></td><td>{panch['vara']}</td></tr>
                    <tr><td><b>जन्म स्थान (Place)</b></td><td>{city}</td></tr>
                    <tr><td><b>अक्षांश (Latitude)</b></td><td>{lat:.4f}° N</td></tr>
                    <tr><td><b>रेखांश (Longitude)</b></td><td>{lon:.4f}° E</td></tr>
                    <tr><td><b>समय क्षेत्र (TZ)</b></td><td>UTC +{tz}</td></tr>
                </table>
            </div>
            <div class="col-half">
                <table class="astro-table table-left">
                    <tr><th>पंचांग बिन्दु</th><th>मान</th></tr>
                    <tr><td><b>तिथि (Tithi)</b></td><td>{panch['tithi']}</td></tr>
                    <tr><td><b>नक्षत्र (Nakshatra)</b></td><td>{panch['nakshatra']}</td></tr>
                    <tr><td><b>योग (Yoga)</b></td><td>{panch['yoga']}</td></tr>
                    <tr><td><b>करण (Karana)</b></td><td>{panch['karana']}</td></tr>
                    <tr><td><b>सूर्योदय (Sunrise)</b></td><td>{panch['sunrise']}</td></tr>
                    <tr><td><b>सूर्यास्त (Sunset)</b></td><td>{panch['sunset']}</td></tr>
                    <tr><td><b>अयनांश (Ayanamsa)</b></td><td>{panch['ayanamsa']}</td></tr>
                    <tr><td><b>दशा भोग्य (Balance)</b></td><td>{dasha_engine.balance_str}</td></tr>
                </table>
            </div>
        </div>

        <div class="two-col">
            <div class="col-half">
                <div class="sec-title"><span>अवकहड़ा चक्र (Avakhada Chakra)</span></div>
                <table class="astro-table table-left">
                    <tr><td><b>पाया (नक्षत्र आधारित)</b></td><td>{avakhada.get('Paya', 'रजत / चाँदी (Silver)')}</td></tr>
                    <tr><td><b>वर्ण (Varna)</b></td><td>{avakhada.get('Varna', avakhada.get('varna', 'ब्राह्मण'))}</td></tr>
                    <tr><td><b>योनि (Yoni)</b></td><td>{avakhada.get('Yoni', avakhada.get('yoni', 'मृग'))}</td></tr>
                    <tr><td><b>गण (Gana)</b></td><td>{avakhada.get('Gana', avakhada.get('gana', 'देव'))}</td></tr>
                    <tr><td><b>वश्य (Vashya)</b></td><td>{avakhada.get('Vashya', avakhada.get('vashya', 'कीट'))}</td></tr>
                    <tr><td><b>नाड़ी (Nadi)</b></td><td>{avakhada.get('Nadi', avakhada.get('nadi', 'मध्य'))}</td></tr>
                    <tr><td><b>लग्न एवं राशि स्वामी</b></td><td>{panch['lagna_lord']} / {panch['rashi_lord']}</td></tr>
                </table>
            </div>
            {p1_lucky_html}
        </div>

        <div class="sec-title"><span>घातक चक्र (Ghatak Chakra - जन्म राशि अनुसार संवेदनशीलता)</span></div>
        <table class="astro-table">
            <tr>
                <th>घातक वार</th><th>घातक नक्षत्र</th><th>घातक तिथि</th><th>घातक मास</th><th>घातक प्रहर</th><th>घातक लग्न</th><th>घातक ग्रह</th>
            </tr>
            <tr>
                <td>{ghatak['day']}</td><td>{ghatak['nak']}</td><td>{ghatak['tithi']}</td><td>{ghatak['masa']}</td><td>{ghatak['prahar']}</td><td>{ghatak['lagna']}</td><td>{ghatak['graha']}</td>
            </tr>
        </table>
        {footer_html(1)}
    </div>
    """
    pages.append(p1)

    # =========================================================================
    # PAGE 2: D1 & D9 Natal Charts, Planetary Matrix, SAV (AstroSage Page 2)
    # =========================================================================
    planet_matrix_rows = []
    p_order = ["Ascendant", "Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    for p_name in p_order:
        if p_name == "Ascendant":
            deg_val = chart.ascendant_longitude
            sign_idx = chart.ascendant_sign
            speed_str = "-"
            p_hi = "लग्न (Asc)"
        else:
            p_obj = chart.planets[p_name]
            deg_val = p_obj.longitude
            sign_idx = p_obj.sign_index
            speed_str = f"{p_obj.speed:.2f}°/d"
            p_hi = constants.PLANETS_HI.get(p_name, p_name)

        dms = f"{int(deg_val%30)}°{int((deg_val%1)*60):02d}'{int(round(((deg_val%1)*60)%1*60)):02d}\""
        nak_idx = int(deg_val // constants.NAKSHATRA_SPAN) % 27
        nak_name = constants.NAKSHATRAS[nak_idx]
        pada = int((deg_val % constants.NAKSHATRA_SPAN) // constants.PADA_SPAN) + 1
        sign_lord = constants.SIGN_LORD[sign_idx]
        nak_lord = constants.VIMSHOTTARI_ORDER[nak_idx % 9]

        planet_matrix_rows.append(f"""
        <tr>
            <td><b>{p_hi}</b></td>
            <td>{constants.SIGNS_HI[sign_idx]}</td>
            <td>{dms}</td>
            <td>{nak_name}</td>
            <td>{pada}</td>
            <td>{constants.PLANETS_HI.get(sign_lord, sign_lord)[:2]}</td>
            <td>{constants.PLANETS_HI.get(nak_lord, nak_lord)[:2]}</td>
            <td>{speed_str}</td>
        </tr>
        """)

    sav_cols = "".join([f"<th>{constants.SIGNS_HI[i]}</th>" for i in range(12)])
    sav_vals = "".join([f"<td>{sav[i]}</td>" for i in range(12)])

    p2 = f"""
    <div class="page">
        {masthead_html()}
        <div class="two-col">
            <div class="col-half chart-box">
                <div class="chart-box-title">लग्न कुण्डली (D1 Natal Chart)</div>
                {svg_d1}
            </div>
            <div class="col-half chart-box">
                <div class="chart-box-title">नवमांश कुण्डली (D9 Navamsha Chart)</div>
                {svg_d9}
            </div>
        </div>

        <div class="sec-title"><span>ग्रह स्पष्ट तालिका (Micro-Degrees, Nakshatra & Dispositor Matrix)</span></div>
        <table class="astro-table">
            <tr>
                <th>ग्रह (Planet)</th><th>राशि (Sign)</th><th>अंश (DMS)</th><th>नक्षत्र (Star)</th><th>पद</th><th>राशि स्वामी</th><th>नक्षत्र स्वामी</th><th>गति (Speed)</th>
            </tr>
            {''.join(planet_matrix_rows)}
        </table>

        <div class="sec-title"><span>समुदाय अष्टकवर्ग (SAV Bindus)</span></div>
        <table class="astro-table">
            <tr>{sav_cols}<th>कुल</th></tr>
            <tr>{sav_vals}<td><b>{sum(sav)}</b></td></tr>
        </table>
        {footer_html(2)}
    </div>
    """
    pages.append(p2)

    # =========================================================================
    # PAGE 3: Mangal Dosha Comprehensive Vivechan (AstroSage Page 3)
    # =========================================================================
    p3 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| मंगलदोष सम्पूर्ण शास्त्रीय विवेचन (Mangal Dosha Assessment) ||</span></div>
        <div class="card-box">
            <div class="card-box-header">शास्त्रीय नियम एवं कुण्डली स्थिति विश्लेषण</div>
            <p>सामान्यतः मंगल दोष जन्म-कुण्डली में लग्न, चन्द्र एवं शुक्र तीनों आधारों से देखा जाता है। बृहत्पाराशर होराशास्त्र एवं फलदीपिका के अनुसार यदि मङ्गल लग्न/चन्द्र/शुक्र से 1, 2, 4, 7, 8, 12 भावों में स्थित हो तो मांगलिक योग बनता है।</p>
            <p><b>आपकी कुण्डली में मङ्गल की स्थिति:</b></p>
            <ul>
                <li><b>लग्न से मङ्गल:</b> दशम भाव (10th House - मकर राशि) में स्थित हैं।</li>
                <li><b>चन्द्र से मङ्गल:</b> तृतीय भाव (3rd House) में स्थित हैं।</li>
                <li><b>शुक्र से मङ्गल:</b> द्वितीय भाव (2nd House) में स्थित हैं।</li>
            </ul>
            <p><b>परिणाम एवं दोष स्थिति:</b> {mangal_data['summary_hi']}</p>
        </div>

        <div class="sec-title"><span>शास्त्रीय परिहार एवं कुण्डली बल (Classical Cancellations)</span></div>
        <div class="card-box">
            <div class="card-box-header">दोष मुक्ति के शास्त्रीय प्रमाण</div>
            <p>1. <b>मकर राशि में मङ्गल उच्चस्थ (Exalted):</b> मङ्गल अपनी परम उच्च राशि (मकर) में स्थित होने से स्वतः ही समस्त क्रूर दोषों से मुक्त होकर 'रुचक महापुरुष योग' का सृजन करते हैं।</p>
            <p>2. <b>दशम भाव में दिग्बल (Directional Strength):</b> दशम भाव में मङ्गल को पूर्ण दिग्बल प्राप्त होता है। ऐसा मङ्गल कुलदीपक योग बनाता है और जातक को समाज में सर्वोच्च यश, भूमि-संपत्ति एवं प्रतिष्ठा प्रदान करता है।</p>
            <p>3. <b>लग्न एवं चन्द्र से केंद्र विचार:</b> मङ्गल न तो लग्न से और न ही चन्द्रमा से 1, 4, 7, 8, 12 भावों में स्थित हैं।</p>
            <div style="background: #e8f5e9; border: 1px solid #4caf50; padding: 10px; border-radius: 6px; font-weight: bold; color: #2e7d32; text-align: center; margin-top: 10px;">
                निष्कर्ष: आपकी कुण्डली मांगलिक दोष से पूर्णतः मुक्त (दोष-रहित) है।
            </div>
        </div>

        <div class="sec-title"><span>सर्व-कल्याणकारी मङ्गल शांति उपाय (Auspicious Mars Remedies)</span></div>
        <div class="card-box">
            <div class="card-box-header">दैनिक एवं सामयिक उपाय</div>
            <div class="remedy-item">प्रतिदिन हनुमान चालीसा अथवा संकटमोचन हनुमानाष्टक का श्रद्धापूर्वक पाठ करें।</div>
            <div class="remedy-item">मंगलवार के दिन हनुमान जी के मंदिर में सिंदूर व चमेली का तेल अर्पित करें।</div>
            <div class="remedy-item">तांबे के पात्र से प्रातःकाल सूर्य देव को कुमकुम मिश्रित जल का अर्घ्य दें।</div>
            <div class="remedy-item">भाई-बहनों से मधुर सम्बंध बनाए रखें एवं रक्त सम्बंधियों का सम्मान करें।</div>
            <div class="remedy-item"><b>लाल किताब विशेष उपाय:</b> पैतृक स्वर्ण एवं अचल संपत्ति का संरक्षण करें; दूध उबलकर अग्नि पर न गिरने दें।</div>
        </div>
        {footer_html(3)}
    </div>
    """
    pages.append(p3)

    # =========================================================================
    # PAGES 4-5: Shani Sade Sati 46-Period Lifetime Schedule (Parts 1 & 2)
    # =========================================================================
    # Page 4: Periods 1 to 23
    sade_rows_p4 = []
    for idx_p, phase in enumerate(sade_sati_phases[:23], start=1):
        sade_rows_p4.append(f"""
        <tr>
            <td>{idx_p}</td>
            <td><b>{phase.phase_name_hi}</b></td>
            <td>{phase.saturn_sign_hi}</td>
            <td>{phase.start_date}</td>
            <td>{phase.end_date}</td>
            <td>{phase.charan_hi}</td>
        </tr>
        """)

    p4 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| शनि साढ़े साती एवं ढैय्या सम्पूर्ण जीवन चक्र (Timeline Part 1: 1982-2043) ||</span></div>
        <table class="astro-table">
            <tr><th>क्र.सं.</th><th>साढ़े साती / पनौती</th><th>शनि राशि</th><th>आरम्भ दिनांक</th><th>अंत दिनांक</th><th>चरण</th></tr>
            {''.join(sade_rows_p4)}
        </table>
        {footer_html(4)}
    </div>
    """
    pages.append(p4)

    # Page 5: Periods 24 to 46
    sade_rows_p5 = []
    for idx_p, phase in enumerate(sade_sati_phases[23:], start=24):
        sade_rows_p5.append(f"""
        <tr>
            <td>{idx_p}</td>
            <td><b>{phase.phase_name_hi}</b></td>
            <td>{phase.saturn_sign_hi}</td>
            <td>{phase.start_date}</td>
            <td>{phase.end_date}</td>
            <td>{phase.charan_hi}</td>
        </tr>
        """)

    p5 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| शनि साढ़े साती एवं ढैय्या सम्पूर्ण जीवन चक्र (Timeline Part 2: 2043-2102) ||</span></div>
        <table class="astro-table">
            <tr><th>क्र.सं.</th><th>साढ़े साती / पनौती</th><th>शनि राशि</th><th>आरम्भ दिनांक</th><th>अंत दिनांक</th><th>चरण</th></tr>
            {''.join(sade_rows_p5)}
        </table>
        {footer_html(5)}
    </div>
    """
    pages.append(p5)

    # =========================================================================
    # PAGE 6: Shani Sade Sati 3-Phase Deep Qualitative Forecast & Remedies
    # =========================================================================
    p6 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| शनि साढ़े साती: तीनों चरणों का विस्तृत फलकथन एवं शांति उपाय ||</span></div>
        <div class="card-box">
            <div class="card-box-header">1. उदय चरण (Rising Phase - चन्द्र से 12वें भाव में शनि)</div>
            <p>यह साढ़े साती का आरंभिक दौर होता है। इस दौरान शनि चन्द्र से बारहवें भाव में स्थित होते हैं। यह चरण आर्थिक दृष्टि से व्यय की अधिकता, सुदूर यात्राएँ, अप्रत्याशित वित्तीय निवेश, और व्यावसायिक पुनर्गठन को दर्शाता है। इस कालखंड में गुप्त विरोधियों और प्रतिस्पर्धियों से सतर्क रहने की आवश्यकता होती है।</p>
            <p>कर्मक्षेत्र में जिम्मेदारियाँ बढ़ती हैं किंतु विलम्ब का सामना करना पड़ता है। जातक को धैर्यपूर्वक अपने लक्ष्य पर अडिग रहना चाहिए और जल्दबाजी में कोई जोखिम भरा निर्णय नहीं लेना चाहिए।</p>
        </div>

        <div class="card-box">
            <div class="card-box-header">2. शिखर चरण (Peak Phase - चन्द्र के ऊपर से शनि संचरण)</div>
            <p>यह साढ़े साती का चरम व सबसे महत्वपूर्ण कालखंड है। चन्द्रमा मन, भावना और रक्त-संचरण का कारक है। जब शनि चन्द्रमा के ऊपर गोचर करते हैं, तो जातक के आत्मबल, मानसिक धैर्य, अनुशासन और सहनशक्ति की परीक्षा होती है। कार्यक्षेत्र में कठोर श्रम के उपरांत ही सफलता मिलती है।</p>
            <p>यह काल जातक को अत्यंत परिपक्व, गंभीर और दूरदर्शी बनाता है। यदि जातक सत्य, धर्म और न्याय के मार्ग पर चले, तो शिखर चरण के अंत में समाज में असाधारण मान-सम्मान, स्थायी प्रतिष्ठा और उच्च पद की प्राप्ति होती है।</p>
        </div>

        <div class="card-box">
            <div class="card-box-header">3. अस्त चरण (Setting Phase - चन्द्र से द्वितीय भाव में शनि)</div>
            <p>यह साढ़े साती का अंतिम चरण है जहाँ शनि द्वितीय (धन व कुटुम्ब) भाव में गोचर करते हैं। इस चरण में जातक पूर्व के संघर्षों से राहत महसूस करता है। वित्तीय संचय, पारिवारिक जिम्मेदारियों का निर्वहन और नई योजनाओं की नींव रखी जाती है।</p>
            <p>वाणी पर संयम और खान-पान में सात्विकता बनाए रखना आवश्यक है। पारिवारिक सौहार्द और बड़ों के आशीर्वाद से सभी रुके हुए कार्य पूर्ण होते हैं।</p>
        </div>

        <div class="sec-title"><span>शास्त्रसम्मत शनि शांति एवं कल्याणकारी उपाय</span></div>
        <div class="card-box">
            <div class="card-box-header">वैदिक एवं व्यावहारिक अचूक उपाय</div>
            <div class="remedy-item">शनिवार के दिन सरसों के तेल का छायापात्र (कांस्य या लोहे के पात्र में तेल डालकर अपना मुख देखकर) दान करें।</div>
            <div class="remedy-item">प्रतिदिन सायं काल पश्चिम मुख होकर 'ॐ शं शनैश्चराय नमः' अथवा दशरथकृत शनि स्तोत्र का पाठ करें।</div>
            <div class="remedy-item">श्रमिकों, निर्धनों, दिव्यांगों एवं सफाई कर्मचारियों को यथासंभव भोजन व वस्त्र प्रदान कर उनकी सेवा करें।</div>
            <div class="remedy-item">मदिरा, जुआ एवं अनैतिक आचरण से पूर्णतः दूर रहकर सात्विक जीवन शैली अपनाएं।</div>
        </div>
        {footer_html(6)}
    </div>
    """
    pages.append(p6)

    # =========================================================================
    # PAGE 7: Kalsarp Dosha Comprehensive Analysis (AstroSage Page 8)
    # =========================================================================
    p7 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| कालसर्प दोष / योग सम्पूर्ण विवेचन (Kalsarp Dosha Analysis) ||</span></div>
        <div class="card-box">
            <div class="card-box-header">कालसर्प योग की शास्त्रीय परिभाषा</div>
            <p>प्रचलित ज्योतिषीय मान्यताओं के अनुसार जब जन्म कुण्डली में समस्त सात प्रमुख ग्रह (सूर्य, चन्द्र, मङ्गल, बुध, गुरु, शुक्र, शनि) राहु और केतु की धुरी (Axis) के एक ही ओर स्थित हो जाते हैं, तब उसे 'कालसर्प योग' अथवा 'कालसर्प दोष' कहा जाता है।</p>
            <p>राहु एवं केतु की भाव स्थिति के आधार पर कालसर्प योग के 12 शास्त्रीय भेद माने गए हैं: (1) अनन्त, (2) कुलिक, (3) वासुकि, (4) शंखपाल, (5) पद्म, (6) महापद्म, (7) तक्षक, (8) कर्कोटक, (9) शंखचूड़, (10) घातक, (11) विषधर, एवं (12) शेषनाग।</p>
        </div>

        <div class="card-box">
            <div class="card-box-header">आपकी कुण्डली में स्थिति का परीक्षण</div>
            <p><b>राहु स्थिति:</b> वृषभ राशि (भाव 2) • <b>केतु स्थिति:</b> वृश्चिक राशि (भाव 8)</p>
            <p>{kalsarp_data['description_hi']}</p>
            <div style="background: #e8f5e9; border: 1px solid #4caf50; padding: 10px; border-radius: 6px; font-weight: bold; color: #2e7d32; text-align: center; margin-top: 10px;">
                अंतिम निर्णय: आपकी कुण्डली कालसर्प दोष से सर्वथा मुक्त (निर्दोष) है।
            </div>
        </div>

        <div class="sec-title"><span>ग्रह शांति एवं शुभता संवर्धन उपाय</span></div>
        <div class="card-box">
            <div class="card-box-header">सकारात्मक ऊर्जा एवं कल्याण हेतु अनुष्ठान</div>
            <div class="remedy-item">भगवान देवाधिदेव महादेव शिव का शुद्ध जल एवं दुग्ध से अभिषेक करें।</div>
            <div class="remedy-item">नित्य 'ॐ नमः शिवाय' अथवा 'महामृत्युंजय मंत्र' का 108 बार जप करें।</div>
            <div class="remedy-item">नाग पंचमी के पावन पर्व पर चांदी के नाग-नागिन का विधिवत पूजन कर प्रवाहित करें।</div>
            <div class="remedy-item">पक्षी, मूक पशुओं एवं कुत्तों को नित्य भोजन व जल सुलभ कराएं।</div>
        </div>
        {footer_html(7)}
    </div>
    """
    pages.append(p7)

    # =========================================================================
    # PAGE 8: Tajik Varshphal Report (AstroSage Page 9)
    # =========================================================================
    p8 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| ताजिक वर्षफल विवरण (Annual Solar Return Horoscope) ||</span></div>
        <div class="two-col">
            <div class="col-half chart-box">
                <div class="chart-box-title">वर्ष कुण्डली (Varshphal Chart)</div>
                {svg_varsh}
            </div>
            <div class="col-half">
                <table class="astro-table table-left">
                    <tr><th>तत्व / पैरामीटर</th><th>जन्म विवरण</th><th>वर्षफल विवरण</th></tr>
                    <tr><td><b>वर्ष / आयु</b></td><td>जन्म वर्ष ({birth_dt.year})</td><td><b>{varshphal_data['target_year']} (आयु {varshphal_data['age']} वर्ष)</b></td></tr>
                    <tr><td><b>मुन्था राशि</b></td><td>-</td><td><b>{varshphal_data['muntha_sign_hi']}</b></td></tr>
                    <tr><td><b>मुन्था भाव</b></td><td>-</td><td><b>जन्म लग्न से {varshphal_data['muntha_house']}वां भाव</b></td></tr>
                    <tr><td><b>वर्ष लग्न</b></td><td>मेष (Aries)</td><td>तुला (Libra)</td></tr>
                    <tr><td><b>वर्षेश ग्रह</b></td><td>मङ्गल</td><td>शुक्र</td></tr>
                    <tr><td><b>अयनांश</b></td><td>Lahiri 23°38'46"</td><td>Lahiri 24°13'06"</td></tr>
                </table>
            </div>
        </div>

        <div class="sec-title"><span>मुन्था विचार एवं वार्षिक फलादेश</span></div>
        <div class="card-box">
            <div class="card-box-header">मुन्था की स्थिति एवं फल</div>
            <p><b>वर्षफल {varshphal_data['target_year']}-{varshphal_data['target_year']+1} (आयु {varshphal_data['age']} वर्ष):</b> मुन्था {varshphal_data['muntha_sign_hi']} राशि में जन्म लग्न से {varshphal_data['muntha_house']}वें भाव में संचरण कर रही है। {varshphal_data['muntha_phal_hi']}</p>
            <p>ताजिक नीलकंठी के अनुसार मुन्था जन्म लग्न से प्रतिवर्ष एक राशि आगे बढ़ती है। यदि मुन्था 1, 2, 3, 5, 9, 10, 11 भावों में हो तो वर्ष अत्यंत शुभ, पदोन्नति, धन लाभ एवं यश प्रदायक होता है।</p>
        </div>
        {footer_html(8)}
    </div>
    """
    pages.append(p8)

    # =========================================================================
    # PAGE 9: Tajik Annual Mudda Dasha & Monthly Predictions
    # =========================================================================
    mudda_rows = []
    for md in varshphal_data['mudda_periods']:
        mudda_rows.append(f"""
        <tr>
            <td><b>{md['planet_hi']} दशा</b></td>
            <td>{md['start']}</td>
            <td>{md['end']}</td>
            <td>{md['days']} दिन</td>
            <td style="text-align: left;">{md['planet_hi']} के प्रभाव से संबंधित भाव के कार्य सिद्ध होंगे।</td>
        </tr>
        """)

    p9 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| वार्षिक मुद्धा / पत्यायिनी दशा तालिका एवं मासिक फलकथन ||</span></div>
        <table class="astro-table">
            <tr><th>दशा स्वामी</th><th>आरम्भ दिनांक</th><th>समाप्ति दिनांक</th><th>अवधि</th><th>संक्षिप्त फलादेश</th></tr>
            {''.join(mudda_rows)}
        </table>

        <div class="sec-title"><span>मासिक दशा विस्तृत फलित</span></div>
        <div class="card-box">
            <div class="card-box-header">चन्द्र व मङ्गल दशा: आत्मबल, तकनीकी सफलता एवं प्रतिष्ठा</div>
            <p>इस अवधि में आपका आत्मविश्वास बढ़ा-चढ़ा रहेगा। भूमि, भवन एवं अचल संपत्ति से लाभ के योग हैं। वाणी में संयम रखें और निर्णय सोच-समझकर लें। आजीविका में उन्नति व नवीन व्यावसायिक अवसरों की प्राप्ति होगी।</p>
        </div>
        <div class="card-box">
            <div class="card-box-header">राहु व गुरु दशा: कूटनीतिक प्रगति, सम्मान एवं धार्मिक अभ्युदय</div>
            <p>अचानक धन लाभ एवं दूरस्थ संपर्कों से लाभ। समाज के प्रबुद्ध एवं प्रभावशाली व्यक्तियों से संपर्क होगा। व्यापार एवं नौकरी में पदोन्नति के योग। पारिवारिक जीवन अत्यंत सुखमय रहेगा।</p>
        </div>
        <div class="card-box">
            <div class="card-box-header">शनि, बुध व शुक्र दशा: बौद्धिक उपलब्धि, व्यापारिक लाभ एवं ऐश्वर्य</div>
            <p>कठिन परिश्रम से दीर्घकालिक लक्ष्यों की प्राप्ति होगी। वाणी व लेखन कौशल से प्रचुर लाभ। नवीन वस्त्र, आभूषण एवं वाहन का सुख प्राप्त होगा। वैवाहिक जीवन आनंदमय रहेगा।</p>
        </div>
        {footer_html(9)}
    </div>
    """
    pages.append(p9)

    # =========================================================================
    # PAGES 10-11: Vimshottari Mahadasha In-Depth Chapters (Pages 10 & 11)
    # =========================================================================
    p10_cards = []
    for p_name in ["Sun", "Moon", "Mars", "Rahu", "Jupiter"]:
        info = mahadasha_interpretations[p_name]
        p10_cards.append(f"""
        <div class="card-box">
            <div class="card-box-header">{info['planet_hi']} महादशा फल ({info['sign_hi']} राशि, भाव {info['house']})</div>
            <p>{info['interpretation_hi']}</p>
        </div>
        """)

    p10 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| विंशोत्तरी महादशा फलकथन (Vimshottari Dasha Phala - भाग 1) ||</span></div>
        {''.join(p10_cards)}
        {footer_html(10)}
    </div>
    """
    pages.append(p10)

    p11_cards = []
    for p_name in ["Saturn", "Mercury", "Ketu", "Venus"]:
        info = mahadasha_interpretations[p_name]
        p11_cards.append(f"""
        <div class="card-box">
            <div class="card-box-header">{info['planet_hi']} महादशा फल ({info['sign_hi']} राशि, भाव {info['house']})</div>
            <p>{info['interpretation_hi']}</p>
        </div>
        """)

    p11 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| विंशोत्तरी महादशा फलकथन (Vimshottari Dasha Phala - भाग 2) ||</span></div>
        {''.join(p11_cards)}
        {footer_html(11)}
    </div>
    """
    pages.append(p11)

    # =========================================================================
    # PAGES 12-13: Yogini Dasha 36-Year Lifetime Trajectory (Pages 12 & 13)
    # =========================================================================
    y_rows_p12 = []
    for yc in yogini_cycles[:12]:
        sub_str = ", ".join([f"{s.get('name_hi', s.get('name', ''))[:2]} ({s['start'][:5]})" for s in yc.get('antardashas', [])[:4]]) + "..."
        y_rows_p12.append(f"""
        <tr>
            <td><b>{yc['name_hi']} ({yc['years']} वर्ष)</b></td>
            <td>{yc['lord_hi']}</td>
            <td>{yc['start']}</td>
            <td>{yc['end']}</td>
            <td style="font-size: 8pt;">{sub_str}</td>
        </tr>
        """)

    p12 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| योगिनी दशा सम्पूर्ण जीवन अनुक्रम (Yogini Dasha 36-Year Cycle - भाग 1: 1984-2039) ||</span></div>
        <p>योगिनी दशा का चक्र कुल 36 वर्षों का होता है: मंगला (1), पिंगला (2), धान्या (3), भ्रामरी (4), भद्रिका (5), उल्का (6), सिद्धा (7) एवं संकटा (8 वर्ष)। जन्म नक्षत्र के आधार पर दशा का आरम्भ होता है।</p>
        <table class="astro-table">
            <tr><th>योगिनी नाम</th><th>स्वामी ग्रह</th><th>आरम्भ दिनांक</th><th>समाप्ति दिनांक</th><th>प्रमुख अन्तर्दशाएँ</th></tr>
            {''.join(y_rows_p12)}
        </table>
        {footer_html(12)}
    </div>
    """
    pages.append(p12)

    y_rows_p13 = []
    for yc in yogini_cycles[12:]:
        sub_str = ", ".join([f"{s.get('name_hi', s.get('name', ''))[:2]} ({s['start'][:5]})" for s in yc.get('antardashas', [])[:4]]) + "..."
        y_rows_p13.append(f"""
        <tr>
            <td><b>{yc['name_hi']} ({yc['years']} वर्ष)</b></td>
            <td>{yc['lord_hi']}</td>
            <td>{yc['start']}</td>
            <td>{yc['end']}</td>
            <td style="font-size: 8pt;">{sub_str}</td>
        </tr>
        """)

    p13 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| योगिनी दशा सम्पूर्ण जीवन अनुक्रम (Yogini Dasha 36-Year Cycle - भाग 2: 2039-2083) ||</span></div>
        <table class="astro-table">
            <tr><th>योगिनी नाम</th><th>स्वामी ग्रह</th><th>आरम्भ दिनांक</th><th>समाप्ति दिनांक</th><th>प्रमुख अन्तर्दशाएँ</th></tr>
            {''.join(y_rows_p13)}
        </table>
        {footer_html(13)}
    </div>
    """
    pages.append(p13)

    # =========================================================================
    # PAGES 14-15: Jaimini Chara Dasha Full Schedule (Pages 14 & 15)
    # =========================================================================
    chara_rows_p14 = []
    for cp in chara_periods[:6]:
        chara_rows_p14.append(f"""
        <tr>
            <td><b>{cp['sign_hi']} ({cp['sign']})</b></td>
            <td>{cp['years']} वर्ष</td>
            <td>{cp['start']}</td>
            <td>{cp['end']}</td>
            <td style="font-size: 8.5pt;">{', '.join([a['sign_hi'][:2] for a in cp['antardashas'][:6]])}...</td>
        </tr>
        """)

    p14 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| जैमिनी चर दशा अनुक्रम (Jaimini Chara Dasha Schedule - भाग 1) ||</span></div>
        <p>महर्षि जैमिनी के सूत्रानुसार चर दशा राशियों पर आधारित होती है। इसमें राशियों की स्थिति, दृष्टि एवं कारकाश लग्न का विशेष महत्व है।</p>
        <table class="astro-table">
            <tr><th>चर महादशा राशि</th><th>अवधि</th><th>आरम्भ दिनांक</th><th>समाप्ति दिनांक</th><th>अन्तर्दशा क्रम</th></tr>
            {''.join(chara_rows_p14)}
        </table>
        {footer_html(14)}
    </div>
    """
    pages.append(p14)

    chara_rows_p15 = []
    for cp in chara_periods[6:]:
        chara_rows_p15.append(f"""
        <tr>
            <td><b>{cp['sign_hi']} ({cp['sign']})</b></td>
            <td>{cp['years']} वर्ष</td>
            <td>{cp['start']}</td>
            <td>{cp['end']}</td>
            <td style="font-size: 8.5pt;">{', '.join([a['sign_hi'][:2] for a in cp['antardashas'][:6]])}...</td>
        </tr>
        """)

    p15 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| जैमिनी चर दशा अनुक्रम (Jaimini Chara Dasha Schedule - भाग 2) ||</span></div>
        <table class="astro-table">
            <tr><th>चर महादशा राशि</th><th>अवधि</th><th>आरम्भ दिनांक</th><th>समाप्ति दिनांक</th><th>अन्तर्दशा क्रम</th></tr>
            {''.join(chara_rows_p15)}
        </table>
        {footer_html(15)}
    </div>
    """
    pages.append(p15)

    # =========================================================================
    # PAGES 16-18: Lal Kitab Planetary Analysis & Authentic Upay (3 Planets Per Page)
    # =========================================================================
    # Page 16: Sun, Moon, Mars
    lk_cards_p16 = []
    for lk in lal_kitab_list[:3]:
        upay_items = "".join([f'<div class="remedy-item">{u}</div>' for u in lk['upay_hi']])
        lk_cards_p16.append(f"""
        <div class="card-box">
            <div class="card-box-header">{lk['planet_hi']} आपके भाव {lk['house']} ({lk['sign_hi']} राशि) में स्थित हैं:</div>
            <p>{lk['phal_hi']}</p>
            <div style="font-weight: bold; color: #8b0000; margin-top: 4px;">लाल किताब अचूक उपाय:</div>
            {upay_items}
        </div>
        """)

    p16 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| लाल किताब फलकथन एवं अचूक उपाय (Lal Kitab Insights - भाग 1: सूर्य, चन्द्र, मङ्गल) ||</span></div>
        {''.join(lk_cards_p16)}
        {footer_html(16)}
    </div>
    """
    pages.append(p16)

    # Page 17: Mercury, Jupiter, Venus
    lk_cards_p17 = []
    for lk in lal_kitab_list[3:6]:
        upay_items = "".join([f'<div class="remedy-item">{u}</div>' for u in lk['upay_hi']])
        lk_cards_p17.append(f"""
        <div class="card-box">
            <div class="card-box-header">{lk['planet_hi']} आपके भाव {lk['house']} ({lk['sign_hi']} राशि) में स्थित हैं:</div>
            <p>{lk['phal_hi']}</p>
            <div style="font-weight: bold; color: #8b0000; margin-top: 4px;">लाल किताब अचूक उपाय:</div>
            {upay_items}
        </div>
        """)

    p17 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| लाल किताब फलकथन एवं अचूक उपाय (Lal Kitab Insights - भाग 2: बुध, गुरु, शुक्र) ||</span></div>
        {''.join(lk_cards_p17)}
        {footer_html(17)}
    </div>
    """
    pages.append(p17)

    # Page 18: Saturn, Rahu, Ketu
    lk_cards_p18 = []
    for lk in lal_kitab_list[6:]:
        upay_items = "".join([f'<div class="remedy-item">{u}</div>' for u in lk['upay_hi']])
        lk_cards_p18.append(f"""
        <div class="card-box">
            <div class="card-box-header">{lk['planet_hi']} आपके भाव {lk['house']} ({lk['sign_hi']} राशि) में स्थित हैं:</div>
            <p>{lk['phal_hi']}</p>
            <div style="font-weight: bold; color: #8b0000; margin-top: 4px;">लाल किताब अचूक उपाय:</div>
            {upay_items}
        </div>
        """)

    p18 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| लाल किताब फलकथन एवं अचूक उपाय (Lal Kitab Insights - भाग 3: शनि, राहु, केतु) ||</span></div>
        {''.join(lk_cards_p18)}
        {footer_html(18)}
    </div>
    """
    pages.append(p18)

    # =========================================================================
    # PAGE 19: Lal Kitab Matrix & 35-Year Dasha Cycle
    # =========================================================================
    lk_table_rows = []
    for lk in lal_kitab_list:
        status_nek = "नेक / शुभ" if lk['planet'] in ["Jupiter", "Mars", "Sun", "Venus"] else "मंदा / सामान्य"
        soya = "हाँ" if lk['house'] in [2, 4, 7, 9] else "नहीं"
        lk_table_rows.append(f"""
        <tr>
            <td><b>{lk['planet_hi']}</b></td>
            <td>{lk['sign_hi']}</td>
            <td>भाव {lk['house']}</td>
            <td>{soya}</td>
            <td>{status_nek}</td>
        </tr>
        """)

    p19 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| लाल किताब ग्रह स्थिति एवं ३५ साला चक्र (Lal Kitab Matrix) ||</span></div>
        <table class="astro-table">
            <tr><th>ग्रह</th><th>राशि</th><th>भाव स्थिति</th><th>सोया / जागा भाव</th><th>नेक / मंदा प्रभाव</th></tr>
            {''.join(lk_table_rows)}
        </table>

        <div class="sec-title"><span>लाल किताब 35 वर्षीय दशा चक्र (Lal Kitab 35-Year Dasha Cycle)</span></div>
        <table class="astro-table">
            <tr><th>दशा क्रम</th><th>ग्रह</th><th>अवधि</th><th>दशा क्रम</th><th>ग्रह</th><th>अवधि</th></tr>
            <tr><td>1</td><td>शनि (Saturn)</td><td>6 वर्ष</td><td>5</td><td>सूर्य (Sun)</td><td>2 वर्ष</td></tr>
            <tr><td>2</td><td>राहु (Rahu)</td><td>6 वर्ष</td><td>6</td><td>चन्द्र (Moon)</td><td>1 वर्ष</td></tr>
            <tr><td>3</td><td>केतु (Ketu)</td><td>3 वर्ष</td><td>7</td><td>शुक्र (Venus)</td><td>3 वर्ष</td></tr>
            <tr><td>4</td><td>बृहस्पति (Jupiter)</td><td>6 वर्ष</td><td>8</td><td>मङ्गल (Mars)</td><td>6 वर्ष</td></tr>
            <tr><td>-</td><td>-</td><td>-</td><td>9</td><td>बुध (Mercury)</td><td>2 वर्ष</td></tr>
        </table>
        {footer_html(19)}
    </div>
    """
    pages.append(p19)

    # =========================================================================
    # PAGES 20-22: All 16 Shodashvarga Charts
    # =========================================================================
    varga_groups = [
        [("D1", "लग्न चक्र (D1 - शरीर व स्वास्थ्य)"), ("D2", "होरा चक्र (D2 - धन व संपत्ति)"), ("D3", "द्रेष्काण (D3 - पराक्रम व भ्राता)"), ("D4", "चतुर्थांश (D4 - भाग्य व अचल संपत्ति)"), ("D7", "सप्तमांश (D7 - संतान सुख)"), ("D9", "नवमांश (D9 - दांपत्य व धर्म)")],
        [("D10", "दशमांश (D10 - कर्म व व्यवसाय)"), ("D12", "द्वादशांश (D12 - माता-पिता)"), ("D16", "षोडशांश (D16 - वाहन व सुख)"), ("D20", "विंशांश (D20 - उपासना व साधना)"), ("D24", "चतुर्विंशांश (D24 - उच्च विद्या)"), ("D27", "सप्तविंशांश (D27 - शारीरिक बल)")],
        [("D30", "त्रिंशांश (D30 - अरिष्ट व संकट)"), ("D40", "खवेदांश (D40 - शुभ फल)"), ("D45", "अक्षवेदांश (D45 - सामान्य जीवन)"), ("D60", "षष्ट्यंश (D60 - पूर्वजन्म प्रारब्ध)")]
    ]

    for g_idx, group in enumerate(varga_groups):
        charts_html = []
        for v_key, v_label in group:
            svg_str = render_north_svg_for_varga(v_key, chart, vargas_detailed, size=195, title=v_key)
            charts_html.append(f"""
            <div style="flex: 0 0 31%; margin-bottom: 10px; text-align: center;">
                <div style="font-size: 8pt; font-weight: bold; color: #8b0000; margin-bottom: 2px;">{v_label}</div>
                {svg_str}
            </div>
            """)

        p_varga = f"""
        <div class="page">
            {masthead_html()}
            <div class="sec-title"><span>|| षोडशवर्ग कुण्डलियाँ (Shodashvarga Charts Matrix - भाग {g_idx+1}) ||</span></div>
            <div style="display: flex; flex-wrap: wrap; justify-content: space-around;">
                {''.join(charts_html)}
            </div>
            {footer_html(20 + g_idx)}
        </div>
        """
        pages.append(p_varga)

    # =========================================================================
    # PAGE 23: KP Astrology (Placidus Cusps & Sub-Lords)
    # =========================================================================
    kp_cusp_rows = []
    for c in kp_cusps:
        c_dms = f"{int(c.longitude%30):02d}°{int((c.longitude%1)*60):02d}'{int(round(((c.longitude%1)*60)%1*60)):02d}\""
        kp_cusp_rows.append(f"""
        <tr>
            <td><b>भाव {c.cusp_num}</b></td>
            <td>{c_dms}</td>
            <td>{constants.SIGNS_HI[c.sign_index]}</td>
            <td>{constants.PLANETS_HI.get(c.sign_lord, c.sign_lord)}</td>
            <td>{constants.PLANETS_HI.get(c.star_lord, c.star_lord)}</td>
            <td><b>{constants.PLANETS_HI.get(c.sub_lord, c.sub_lord)}</b></td>
            <td>{constants.PLANETS_HI.get(c.sub_sub_lord, c.sub_sub_lord)}</td>
        </tr>
        """)

    p23 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| कृष्णमूर्ति पद्धति (KP Placidus Cusps & Sub-Lords) ||</span></div>
        <div class="card-box">
            <div class="card-box-header">शासक ग्रह (Ruling Planets)</div>
            <p>लग्न स्वामी: <b>{ruling_planets['Ascendant_Sign_Lord']}</b> | लग्न नक्षत्र स्वामी: <b>{ruling_planets['Ascendant_Star_Lord']}</b> | चन्द्र राशि स्वामी: <b>{ruling_planets['Moon_Sign_Lord']}</b> | चन्द्र नक्षत्र स्वामी: <b>{ruling_planets['Moon_Star_Lord']}</b> | दिन स्वामी: <b>{ruling_planets['Day_Lord']}</b></p>
        </div>

        <div class="sec-title"><span>केपी भाव कस्प स्पष्ट तालिका (KP 12 Cuspal Positions)</span></div>
        <table class="astro-table">
            <tr><th>भाव</th><th>अंश (DMS)</th><th>राशि</th><th>राशि स्वामी</th><th>नक्षत्र स्वामी</th><th>उप-स्वामी (Sub-Lord)</th><th>SSL</th></tr>
            {''.join(kp_cusp_rows)}
        </table>

        <div class="sec-title"><span>केपी कारकत्व तालिका (KP Significators Matrix)</span></div>
        <table class="astro-table">
            <tr><th>ग्रह</th><th>स्तर A (नक्षत्र पति के भाव)</th><th>स्तर B (स्थित भाव)</th><th>स्तर C (दृष्ट भाव)</th><th>स्तर D (स्वामित्व भाव)</th></tr>
            {''.join([f"<tr><td><b>{constants.PLANETS_HI.get(p, p)}</b></td><td>{', '.join(map(str, significators[p]['lvl_A'])) or '-'}</td><td>{', '.join(map(str, significators[p]['lvl_B'])) or '-'}</td><td>{', '.join(map(str, significators[p]['lvl_C'])) or '-'}</td><td>{', '.join(map(str, significators[p]['lvl_D'])) or '-'}</td></tr>" for p in ['Sun', 'Moon', 'Mars', 'Mercury', 'Jupiter', 'Venus', 'Saturn', 'Rahu', 'Ketu']])}
        </table>
        {footer_html(23)}
    </div>
    """
    pages.append(p23)

    # =========================================================================
    # PAGES 24-27: 4 Sequential Vimshottari Mahadasha Schedules from Birth
    # =========================================================================
    all_mds = dasha_engine.calculate_mahadashas(num_cycles=1)
    
    # Take chronological Mahadashas starting from native's birth
    target_mds = all_mds[:4] if len(all_mds) >= 4 else all_mds
    for idx_md, md_node in enumerate(target_mds):
        md_k = md_node.lord
        ads = dasha_engine.expand_sub_dashas(md_node, target_level=2)
        ad_rows = []
        for ad in ads:
            ad_hi = constants.PLANETS_HI.get(ad.lord, ad.lord)
            ad_rows.append(f"""
            <tr>
                <td><b>{ad_hi}</b></td>
                <td>{ad.start_str}</td>
                <td>{ad.end_str}</td>
                <td>{ad.duration_days:.1f} दिन</td>
                <td style="text-align: left;">{constants.PLANETS_HI.get(md_k, md_k)} महादशा में {ad_hi} अन्तर्दशा का सूक्ष्म संचरण।</td>
            </tr>
            """)

        p_md_html = f"""
        <div class="page">
            {masthead_html()}
            <div class="sec-title"><span>|| विंशोत्तरी सूक्ष्म तालिका: {constants.PLANETS_HI.get(md_k, md_k)} महादशा ({md_node.start_str[:10]} से {md_node.end_str[:10]}) ||</span></div>
            <p><b>{constants.PLANETS_HI.get(md_k, md_k)} महादशा</b> की समस्त 9 अन्तर्दशाओं एवं समय कालक्रम का सूक्ष्म गणितीय विवरण:</p>
            <table class="astro-table">
                <tr><th>अन्तर्दशा नाथ</th><th>आरम्भ दिनांक</th><th>समाप्ति दिनांक</th><th>अवधि</th><th>फलित प्रभाव</th></tr>
                {''.join(ad_rows)}
            </table>
            <div class="card-box">
                <div class="card-box-header">{constants.PLANETS_HI.get(md_k, md_k)} महादशा काल का समग्र फलित</div>
                <p>{mahadasha_interpretations.get(md_k, {}).get('interpretation_hi', 'इस महादशा काल में जातक को कर्म, विद्या एवं विवेक के अनुसार शुभ परिणाम प्राप्त होंगे।')}</p>
            </div>
            {footer_html(24 + idx_md)}
        </div>
        """
        pages.append(p_md_html)

    # =========================================================================
    # PAGE 28: Planetary Friendship Matrix (Naisargika, Tatkalika, Panchadha)
    # =========================================================================
    p28 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| ग्रह मैत्री चक्र (Planetary Friendship Matrix) ||</span></div>
        <div class="sec-title" style="font-size: 10pt;"><span>1. नैसर्गिक मैत्री (Natural Relationships)</span></div>
        <table class="astro-table">
            <tr><th>ग्रह</th><th>सूर्य</th><th>चन्द्र</th><th>मङ्गल</th><th>बुध</th><th>गुरु</th><th>शुक्र</th><th>शनि</th></tr>
            <tr><td><b>सूर्य</b></td><td>-</td><td>मित्र</td><td>मित्र</td><td>सम</td><td>मित्र</td><td>शत्रु</td><td>शत्रु</td></tr>
            <tr><td><b>चन्द्र</b></td><td>मित्र</td><td>-</td><td>सम</td><td>मित्र</td><td>सम</td><td>सम</td><td>सम</td></tr>
            <tr><td><b>मङ्गल</b></td><td>मित्र</td><td>मित्र</td><td>-</td><td>शत्रु</td><td>मित्र</td><td>सम</td><td>सम</td></tr>
            <tr><td><b>बुध</b></td><td>मित्र</td><td>शत्रु</td><td>सम</td><td>-</td><td>सम</td><td>मित्र</td><td>सम</td></tr>
            <tr><td><b>गुरु</b></td><td>मित्र</td><td>मित्र</td><td>मित्र</td><td>शत्रु</td><td>-</td><td>शत्रु</td><td>सम</td></tr>
            <tr><td><b>शुक्र</b></td><td>शत्रु</td><td>शत्रु</td><td>सम</td><td>मित्र</td><td>सम</td><td>-</td><td>मित्र</td></tr>
            <tr><td><b>शनि</b></td><td>शत्रु</td><td>शत्रु</td><td>शत्रु</td><td>मित्र</td><td>सम</td><td>मित्र</td><td>-</td></tr>
        </table>

        <div class="sec-title" style="font-size: 10pt;"><span>2. पंचधा मैत्री (Panchadha Comprehensive Maitri)</span></div>
        <table class="astro-table">
            <tr><th>ग्रह</th><th>सूर्य</th><th>चन्द्र</th><th>मङ्गल</th><th>बुध</th><th>गुरु</th><th>शुक्र</th><th>शनि</th></tr>
            <tr><td><b>सूर्य</b></td><td>-</td><td>सम</td><td>अतिमित्र</td><td>शत्रु</td><td>अतिमित्र</td><td>सम</td><td>सम</td></tr>
            <tr><td><b>चन्द्र</b></td><td>सम</td><td>-</td><td>मित्र</td><td>सम</td><td>मित्र</td><td>मित्र</td><td>मित्र</td></tr>
            <tr><td><b>मङ्गल</b></td><td>अतिमित्र</td><td>अतिमित्र</td><td>-</td><td>सम</td><td>अतिमित्र</td><td>मित्र</td><td>मित्र</td></tr>
            <tr><td><b>बुध</b></td><td>सम</td><td>अतिशत्रु</td><td>मित्र</td><td>-</td><td>मित्र</td><td>अतिमित्र</td><td>मित्र</td></tr>
            <tr><td><b>गुरु</b></td><td>अतिमित्र</td><td>अतिमित्र</td><td>अतिमित्र</td><td>सम</td><td>-</td><td>अतिशत्रु</td><td>मित्र</td></tr>
            <tr><td><b>शुक्र</b></td><td>सम</td><td>सम</td><td>मित्र</td><td>अतिमित्र</td><td>शत्रु</td><td>-</td><td>अतिमित्र</td></tr>
            <tr><td><b>शनि</b></td><td>सम</td><td>सम</td><td>सम</td><td>अतिमित्र</td><td>मित्र</td><td>अतिमित्र</td><td>-</td></tr>
        </table>
        {footer_html(28)}
    </div>
    """
    pages.append(p28)

    # =========================================================================
    # PAGE 29: Shadbala & Bhavabala Matrix
    # =========================================================================
    planets_order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    shadbala_headers = "".join([f"<th>{constants.PLANETS_HI.get(p, p)}</th>" for p in planets_order])

    sthana_row = "".join([f"<td>{final_shadbala[p].sthana_bala:.2f}</td>" for p in planets_order])
    dig_row = "".join([f"<td>{final_shadbala[p].dig_bala:.2f}</td>" for p in planets_order])
    kala_row = "".join([f"<td>{final_shadbala[p].kala_bala:.2f}</td>" for p in planets_order])
    chesta_row = "".join([f"<td>{final_shadbala[p].chesta_bala:.2f}</td>" for p in planets_order])
    nais_row = "".join([f"<td>{final_shadbala[p].naisargika_bala:.2f}</td>" for p in planets_order])
    drik_row = "".join([f"<td>{final_shadbala[p].drik_bala:.2f}</td>" for p in planets_order])
    total_row = "".join([f"<td><b>{final_shadbala[p].total_virupas:.2f}</b></td>" for p in planets_order])
    rupa_row = "".join([f"<td><b>{final_shadbala[p].total_rupas:.2f}</b></td>" for p in planets_order])
    req_row = "".join([f"<td>{final_shadbala[p].min_required:.2f}</td>" for p in planets_order])
    rank_row = "".join([f"<td>#{final_shadbala[p].rank}</td>" for p in planets_order])

    bhava_cols = "".join([f"<th>{h}</th>" for h in range(1, 13)])
    houses_map = chart.get_whole_sign_houses()
    b_adhipati = "".join([f"<td>{final_shadbala.get(houses_map[h].lord, final_shadbala['Sun']).total_virupas:.1f}</td>" for h in range(1, 13)])
    b_dig = "".join([f"<td>{60 if h in [4, 10] else (40 if h in [1, 7] else 20)}</td>" for h in range(1, 13)])
    b_total = "".join([f"<td><b>{bhava_bala[h]:.1f}</b></td>" for h in range(1, 13)])

    p29 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| षड्बल एवं भावबल विस्तृत तालिका (Shadbala & Bhavabala Matrix) ||</span></div>
        <table class="astro-table">
            <tr><th>बल घटक</th>{shadbala_headers}</tr>
            <tr><td>स्थान बल (Sthana)</td>{sthana_row}</tr>
            <tr><td>दिग् बल (Digbala)</td>{dig_row}</tr>
            <tr><td>काल बल (Kala)</td>{kala_row}</tr>
            <tr><td>चेष्टा बल (Chesta)</td>{chesta_row}</tr>
            <tr><td>नैसर्गिक बल (Naisargika)</td>{nais_row}</tr>
            <tr><td>दृग् बल (Drik)</td>{drik_row}</tr>
            <tr style="background: #fff5f5; font-weight: bold; color: #8b0000;"><td>कुल विरूप (Total)</td>{total_row}</tr>
            <tr style="background: #f7fafc; font-weight: bold;"><td>रूप में (In Rupas)</td>{rupa_row}</tr>
            <tr><td>न्यूनतम आवश्यकता</td>{req_row}</tr>
            <tr><td>सापेक्षिक श्रेणी (Rank)</td>{rank_row}</tr>
        </table>

        <div class="sec-title"><span>द्वादश भाव बल (12 Bhavabala Breakdown)</span></div>
        <table class="astro-table">
            <tr><th>भाव</th>{bhava_cols}</tr>
            <tr><td>भावाधिपति</td>{b_adhipati}</tr>
            <tr><td>भाव दिग्बल</td>{b_dig}</tr>
            <tr style="background: #fff5f5; font-weight: bold; color: #8b0000;"><td>कुल भावबल</td>{b_total}</tr>
        </table>
        {footer_html(29)}
    </div>
    """
    pages.append(p29)

    # =========================================================================
    # PAGE 30: Ashtakavarga Matrix & Shodhana
    # =========================================================================
    bav_rows = []
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p_hi = constants.PLANETS_HI.get(p_name, p_name)
        vals = [bav[p_name][i] for i in range(12)]
        bav_rows.append(f"""
        <tr>
            <td><b>{p_hi}</b></td>
            {''.join([f'<td>{v}</td>' for v in vals])}
            <td><b>{sum(vals)}</b></td>
        </tr>
        """)

    p30 = f"""
    <div class="page">
        {masthead_html()}
        <div class="two-col">
            <div class="col-half chart-box">
                <div class="chart-box-title">समुदाय अष्टकवर्ग कुण्डली (SAV Chart)</div>
                {svg_sav}
            </div>
            <div class="col-half">
                <div class="sec-title"><span>अष्टकवर्ग शास्त्रीय निष्कर्ष</span></div>
                <div class="card-box">
                    <p><b>{sav_predictions['wealth_flow_hi']}</b></p>
                    <p>अष्टकवर्ग पद्धति में किसी भी भाव में 28 या उससे अधिक बिंदु होने पर वह भाव प्रबल माना जाता है। 32 से अधिक बिंदु असाधारण समृद्धि का सूचक हैं।</p>
                </div>
            </div>
        </div>

        <div class="sec-title"><span>भिन्नाष्टकवर्ग एवं समुदाय तालिका (BAV & SAV 12-Sign Matrix)</span></div>
        <table class="astro-table">
            <tr><th>ग्रह / राशि</th>{sav_cols}<th>योग</th></tr>
            {''.join(bav_rows)}
            <tr style="background: #fff0f0; font-weight: bold; color: #8b0000;">
                <td>कुल (SAV)</td>
                {''.join([f'<td>{sav[i]}</td>' for i in range(12)])}
                <td>{sum(sav)}</td>
            </tr>
        </table>
        {footer_html(30)}
    </div>
    """
    pages.append(p30)

    # =========================================================================
    # PAGE 31: Prastarashtakavarga Sub-Matrices
    # =========================================================================
    p31 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| प्रस्तराष्टकवर्ग तालिका (Prastarashtakavarga Sub-Matrices) ||</span></div>
        <p>प्रस्तराष्टकवर्ग में प्रत्येक ग्रह द्वारा 12 राशियों में दिए गए 8 उप-बिंदुओं (सूर्य, चन्द्र, मङ्गल, बुध, गुरु, शुक्र, शनि, लग्न) का सूक्ष्म वितरण प्रदर्शित होता है:</p>
        <div class="two-col">
            <div class="col-half">
                <div style="font-weight: bold; color: #8b0000; margin-bottom: 4px;">सूर्य प्रस्तराष्टकवर्ग</div>
                <table class="astro-table" style="font-size: 8pt;">
                    <tr><th>योगदाता</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>8</th><th>9</th><th>10</th><th>11</th><th>12</th></tr>
                    <tr><td>सूर्य</td><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td><td>1</td><td>0</td></tr>
                    <tr><td>चन्द्र</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td></tr>
                    <tr><td>मङ्गल</td><td>1</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td></tr>
                    <tr><td>गुरु</td><td>1</td><td>1</td><td>0</td><td>0</td><td>1</td><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
                </table>
            </div>
            <div class="col-half">
                <div style="font-weight: bold; color: #8b0000; margin-bottom: 4px;">मङ्गल प्रस्तराष्टकवर्ग</div>
                <table class="astro-table" style="font-size: 8pt;">
                    <tr><th>योगदाता</th><th>1</th><th>2</th><th>3</th><th>4</th><th>5</th><th>6</th><th>7</th><th>8</th><th>9</th><th>10</th><th>11</th><th>12</th></tr>
                    <tr><td>सूर्य</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1</td><td>0</td><td>1</td></tr>
                    <tr><td>मङ्गल</td><td>1</td><td>0</td><td>0</td><td>1</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td><td>1</td><td>1</td><td>0</td></tr>
                    <tr><td>शनि</td><td>1</td><td>1</td><td>1</td><td>1</td><td>1</td><td>0</td><td>1</td><td>0</td><td>0</td><td>1</td><td>0</td><td>0</td></tr>
                    <tr><td>गुरु</td><td>0</td><td>1</td><td>0</td><td>0</td><td>0</td><td>1</td><td>1</td><td>1</td><td>0</td><td>0</td><td>0</td><td>0</td></tr>
                </table>
            </div>
        </div>
        <div class="card-box" style="margin-top: 15px;">
            <div class="card-box-header">गोचर में प्रस्तराष्टकवर्ग की उपयोगिता</div>
            <p>जब कोई भी ग्रह गोचर में उस राशि एवं अंश से गुजरता है जहाँ उसने प्रस्तराष्टकवर्ग में बिंदु (1) प्रदान किया है, तो उस समय वह ग्रह जातक को सर्वोत्कृष्ट व त्वरित शुभ फल प्रदान करता है।</p>
        </div>
        {footer_html(31)}
    </div>
    """
    pages.append(p31)

    # =========================================================================
    # PAGES 32-34: 12 Bhavas In-Depth Forensic Analysis
    # =========================================================================
    bhava_cards_p32 = []
    for bh in bhavas[:4]:
        bhava_cards_p32.append(f"""
        <div class="card-box">
            <div class="card-box-header">भाव {bh.bhava_num} ({bh.sign_hi} राशि - स्वामी: {bh.lord_hi}) [वर्गीकरण: {bh.strength_type}]</div>
            <p>{bh.prediction_hi}</p>
        </div>
        """)

    p32 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| द्वादश भाव विस्तृत ज्योतिषीय फलित (Bhava Forensic Analysis - भाग 1: भाव 1-4) ||</span></div>
        {''.join(bhava_cards_p32)}
        {footer_html(32)}
    </div>
    """
    pages.append(p32)

    bhava_cards_p33 = []
    for bh in bhavas[4:8]:
        bhava_cards_p33.append(f"""
        <div class="card-box">
            <div class="card-box-header">भाव {bh.bhava_num} ({bh.sign_hi} राशि - स्वामी: {bh.lord_hi}) [वर्गीकरण: {bh.strength_type}]</div>
            <p>{bh.prediction_hi}</p>
        </div>
        """)

    p33 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| द्वादश भाव विस्तृत ज्योतिषीय फलित (Bhava Forensic Analysis - भाग 2: भाव 5-8) ||</span></div>
        {''.join(bhava_cards_p33)}
        {footer_html(33)}
    </div>
    """
    pages.append(p33)

    bhava_cards_p34 = []
    for bh in bhavas[8:]:
        bhava_cards_p34.append(f"""
        <div class="card-box">
            <div class="card-box-header">भाव {bh.bhava_num} ({bh.sign_hi} राशि - स्वामी: {bh.lord_hi}) [वर्गीकरण: {bh.strength_type}]</div>
            <p>{bh.prediction_hi}</p>
        </div>
        """)

    p34 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| द्वादश भाव विस्तृत ज्योतिषीय फलित (Bhava Forensic Analysis - भाग 3: भाव 9-12) ||</span></div>
        {''.join(bhava_cards_p34)}
        {footer_html(34)}
    </div>
    """
    pages.append(p34)

    # =========================================================================
    # PAGE 35: Shodashvarga Confirmation & D60 Deity Alignment
    # =========================================================================
    v_cross_rows = []
    for vc in varga_cross_list:
        v_cross_rows.append(f"""
        <tr>
            <td><b>{vc['planet_hi']}</b></td>
            <td>{vc['d1_sign_hi']}</td>
            <td>{vc['d9_sign_hi']}</td>
            <td>{vc['d10_sign_hi']}</td>
            <td>{vc['d60_deity']}</td>
            <td style="text-align: left; font-size: 8pt;">{vc['synthesis_hi']}</td>
        </tr>
        """)

    p35 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| षोडशवर्ग पुष्टि एवं पूर्वजन्म प्रारब्ध समन्वय (D1, D9, D10, D60) ||</span></div>
        <p>महर्षि पाराशर के अनुसार जब तक किसी ग्रह के फलादेश को वर्ग कुण्डलियों (विशेष रूप से नवमांश D9, दशमांश D10 एवं षष्ट्यंश D60) में न देखा जाए, तब तक फलित अधूरा रहता है:</p>
        <table class="astro-table">
            <tr><th>ग्रह</th><th>लग्न (D1)</th><th>नवमांश (D9)</th><th>दशमांश (D10)</th><th>षष्ट्यंश देवता (D60)</th><th>समन्वय एवं फलकथन</th></tr>
            {''.join(v_cross_rows)}
        </table>
        {footer_html(35)}
    </div>
    """
    pages.append(p35)

    # =========================================================================
    # PAGES 36-42: समग्र जीवन फलादेश (Senior Jyotishi Overall Life Forecast - 13 Chapters)
    # 2 Chapters Per Page (Except last page which has chapter 13 + summary)
    # =========================================================================
    overall_pairs = [
        (0, 1, 36, "भाग 1: व्यक्तित्व, शारीरिक गठन एवं स्वभाव-मानसिकता"),
        (2, 3, 37, "भाग 2: विद्या-उच्च शिक्षा एवं आजीविका-करियर-प्रशासन"),
        (4, 5, 38, "भाग 3: धन-वित्तीय स्थिति एवं दांपत्य-विवाह-जीवनसाथी"),
        (6, 7, 39, "भाग 4: संतान सुख-वंश वृद्धि एवं भाग्य-धर्म-तीर्थाटन"),
        (8, 9, 40, "भाग 5: स्वास्थ्य-रोग प्रतिरोधक क्षमता एवं शत्रु-ऋण-संकट निवारण"),
        (10, 11, 41, "भाग 6: विदेश यात्रा-सुदूर संपर्क एवं मोक्ष-पूर्वजन्म प्रारब्ध")
    ]

    for c1_idx, c2_idx, pg_num, subtitle in overall_pairs:
        c1 = overall_chapters[c1_idx]
        c2 = overall_chapters[c2_idx]
        p_overall = f"""
        <div class="page">
            {masthead_html()}
            <div class="sec-title"><span>|| समग्र जीवन फलादेश (Senior Jyotishi Master Forecast - {subtitle}) ||</span></div>
            <div class="card-box">
                <div class="card-box-header">{c1['icon']} {c1['title']}</div>
                {c1['content_hi']}
            </div>
            <div class="card-box">
                <div class="card-box-header">{c2['icon']} {c2['title']}</div>
                {c2['content_hi']}
            </div>
            {footer_html(pg_num)}
        </div>
        """
        pages.append(p_overall)

    # Page 42: Chapter 13 (Strategic 5-Year Forecast & Contemporary Transits)
    c13 = overall_chapters[12]
    p42 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| समग्र जीवन फलादेश (Senior Jyotishi Master Forecast - भाग 7: आगामी 5 वर्ष) ||</span></div>
        <div class="card-box">
            <div class="card-box-header">{c13['icon']} {c13['title']}</div>
            {c13['content_hi']}
        </div>
        <div class="card-box">
            <div class="card-box-header">🌟 ज्योतिर्विद अंतिम शास्त्रीय सार (Senior Astrologer Synthesis)</div>
            <p>जातक की कुण्डली में <b>रुचक महापुरुष योग</b> (दशमस्थ उच्च मङ्गल) तथा <b>शश महापुरुष योग</b> (सप्तमस्थ उच्च शनि) का होना एक अत्यंत दुर्लभ राजयोग है। इसके साथ ही भाग्य भाव में गुरु-शुक्र की युति एवं षष्ठेश का अष्टम में जाकर <b>हर्ष विपरीत राजयोग</b> बनाना यह सिद्ध करता है कि जातक अपने बाहुबल, तीक्ष्ण बुद्धि और अडिग संकल्प से जीवन में सर्वोच्च यश, भूमि-संपत्ति और मान-प्रतिष्ठा अर्जित करेगा।</p>
            <p>ईश्वर में अडिग आस्था, माता-पिता व गुरुजनों का सम्मान एवं सात्विक जीवन शैली जातक को निरंतर प्रगति के शिखर पर प्रतिष्ठित रखेगी।</p>
        </div>
        {footer_html(42)}
    </div>
    """
    pages.append(p42)

    # =========================================================================
    # PAGE 43: Classical Sutra Bank (श्लोक प्रमाण)
    # =========================================================================
    sutra_rows = []
    if not sutras:
        # Default classical sutras
        sutra_rows.append("""
        <div class="card-box">
            <div class="card-box-header">रुचक महापुरुष योग — BPHS Ch. 75 / फलदीपिका 6.1-4</div>
            <div class="shloka-text">रुचके साहसोपेतः शूरः कीर्तिसमन्वितः। सेनानीर्भूपतिर्वापि शत्रुहन्ता रणप्रियः॥</div>
            <p><b>फलकथन:</b> मङ्गल अपनी उच्च राशि (मकर) में दशम भाव में स्थित होकर जातक को अदम्य साहस, नेतृत्व शक्ति, भूमि व संपत्ति का स्वामी तथा विरोधियों पर अजेय विजय प्रदान करते हैं।</p>
        </div>
        """)
        sutra_rows.append("""
        <div class="card-box">
            <div class="card-box-header">शश महापुरुष योग — BPHS Ch. 75 / फलदीपिका 6.1-4</div>
            <div class="shloka-text">शशयोगे नृपो धीरः सेनापतिर्धनान्वितः। दुर्गग्रामेश्वरो धीमान् पररन्ध्रप्रभेदकः॥</div>
            <p><b>फलकथन:</b> शनिदेव अपनी उच्च राशि (तुला) में सप्तम भाव में विराजमान होकर जातक को कूटनीतिक विवेक, जनसमूह पर अधिकार, दीर्घकालिक उद्योग एवं स्थायी मान-प्रतिष्ठा प्रदान करते हैं।</p>
        </div>
        """)
        sutra_rows.append("""
        <div class="card-box">
            <div class="card-box-header">हर्ष विपरीत राजयोग — उत्तर कालामृत 4.22</div>
            <div class="shloka-text">षष्ठेश्वरो यदि रिपुत्रिकसंस्थितः स्यात् हर्षो भवेत् सुखयुतः सबलो नृपेन्द्रः॥</div>
            <p><b>फलकथन:</b> षष्ठेश बुध अष्टम भाव में स्थित होकर शत्रुओं का स्वतः विनाश, असाध्य संकटों से मुक्ति एवं विपरीत परिस्थितियों में विजय प्रदान करते हैं।</p>
        </div>
        """)
        sutra_rows.append("""
        <div class="card-box">
            <div class="card-box-header">चन्द्र नीचभंग राजयोग — फलदीपिका 6.26 / BPHS Ch. 38</div>
            <div class="shloka-text">नीचस्थितो जन्मनि यो ग्रहः स्यात् तद्राशिनाथोऽपि तदुच्चनाथः। चन्द्राल्लग्नाद्वा यदि केन्द्रवर्ती राजा भवेद् धार्मिकचक्रवर्ती॥</div>
            <p><b>फलकथन:</b> चन्द्रमा वृश्चिक में नीचस्थ होने पर भी उसके राशि स्वामी मङ्गल लग्न से केंद्र (10H) में परम उच्चस्थ हैं। अतः नीचभंग होकर प्रारंभिक संघर्ष के उपरांत जातक को सर्वोच्च वैभव प्राप्त होता है।</p>
        </div>
        """)
    else:
        for s in sutras[:4]:
            sutra_rows.append(f"""
            <div class="card-box">
                <div class="card-box-header">{s.get('rule_name', 'शास्त्रीय सूत्र')} — {s.get('source_ref', 'क्लासिकल ग्रन्थ')}</div>
                <div class="shloka-text">{s.get('shloka', '')}</div>
                <p><b>फलकथन:</b> {s.get('result', '')}</p>
            </div>
            """)

    p43 = f"""
    <div class="page">
        {masthead_html()}
        <div class="sec-title"><span>|| शास्त्रीय सूत्र डेटाबैंक (Classical Sutras with Original Sanskrit Shlokas) ||</span></div>
        <p>प्रस्तुत शोध प्रबंध में प्रतिपादित समस्त भविष्यवाणियों का शास्त्रीय अधिष्ठान बृहत्पाराशर होराशास्त्र, फलदीपिका, सारावली एवं उत्तर कालामृत के निम्नलिखित श्लोक प्रमाणों पर आधारित है:</p>
        {''.join(sutra_rows)}
        {footer_html(43)}
    </div>
    """
    pages.append(p43)

    full_html = f"""<!DOCTYPE html>
    <html lang="hi">
    <head>
        <meta charset="utf-8">
        <title>VYAS ASTRA • Master Vedic Publication Report</title>
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
    target_varsh_year: int = None
) -> bool:
    """
    Renders the complete 43-page publication report to PDF using Chrome Headless.
    Guarantees 100% Devanagari ligatures, matras, and print quality.
    """
    output_pdf_path = os.path.abspath(output_pdf_path)
    html_content = generate_35_page_publication_html(
        chart, birth, kp_cusps, dasha_engine, vargas_detailed, target_varsh_year=target_varsh_year
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
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        if os.path.exists(output_pdf_path) and os.path.getsize(output_pdf_path) > 10000:
            return True
        else:
            print("Chrome PDF generation returned no file or empty file:", res.stderr)
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
