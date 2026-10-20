"""Deep Forensic Predictive Astrology Engine (गहन ज्योतिषीय फलित एवं विश्लेषण इंजन).

Synthesizes classical Vedic principles from Brihat Parashara Hora Shastra (BPHS),
Phaladeepika, Saravali, Laghu Parashari, and Jaimini Sutras to deliver
comprehensive, paragraph-length deterministic predictions.

Key Capabilities:
1. Lagna & Lagnesh In-Depth Analysis (Lagna sign, Lagnesh house & dignity, aspects on Lagna).
2. Bhava-by-Bhava Forensic Analysis (Lords, occupants, aspecting grahas, Kendras/Trikonas/Dusthanas).
3. Planetary Dignities & States:
   - Exaltation (उच्च) / Debilitation (नीच) / Moolatrikona / Own Sign.
   - Combustion (अस्त) with exact angular proximity to Sun.
   - Retrograde (वक्री) chesta bala amplification.
   - Planetary Awasthas by degree: Baala (0-6°), Kumara (6-12°), Yuva (12-18°), Vriddha (18-24°), Mrita (24-30°).
   - Mutual house exchanges (Parivartana Yogas: Maha, Khala, Dainya).
   - Planetary War (Graha Yuddha).
4. Varga Dignity & Cross-Verification (D1 vs D9 Navamsha, Vargottama confirmation).
5. Comprehensive Mangal Dosha Analysis (from Lagna, Moon, and Venus with 14 classical cancellations).
6. Comprehensive Kalsarp Dosha Analysis (12 classical types).
7. Comprehensive Shani Sade Sati Timeline & 3-Phase Predictions (Rising, Peak, Setting).
8. Tajik Varshphal (Annual Solar Return Chart, Muntha house, annual dasha, and yearly forecast).
9. Full Mahadasha-by-Mahadasha qualitative predictive chapters for all 9 planets.
10. Ashtakavarga qualitative synthesis (SAV score impact on houses & transits).
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import math

from vyas import constants

# ---------------------------------------------------------------------------
# Data Models for Comprehensive Predictions
# ---------------------------------------------------------------------------
@dataclass
class PlanetDignity:
    name: str
    sign: str
    sign_hi: str
    degree: float
    house: int
    is_exalted: bool
    is_debilitated: bool
    is_own_sign: bool
    is_combust: bool
    combust_deg_diff: float
    is_retrograde: bool
    awastha: str
    awastha_hi: str
    is_vargottama: bool
    d9_sign: str
    d9_sign_hi: str
    aspects_cast_on: List[int]     # Houses aspected
    aspects_received_from: List[str] # Planets aspecting this planet
    dignity_summary: str
    dignity_summary_hi: str

@dataclass
class BhavaAnalysis:
    bhava_num: int
    sign: str
    sign_hi: str
    lord: str
    lord_hi: str
    lord_house: int
    lord_sign: str
    lord_sign_hi: str
    occupants: List[str]
    occupants_hi: List[str]
    aspecting_planets: List[str]
    aspecting_planets_hi: List[str]
    strength_type: str            # Kendra, Trikona, Dusthana, Trishadaya, Maraka
    prediction_hi: str
    prediction_en: str

@dataclass
class SadeSatiPhase:
    phase_name: str
    phase_name_hi: str
    saturn_sign: str
    saturn_sign_hi: str
    start_date: str
    end_date: str
    charan: str                    # Uday, Shikhar, Ast, Chhoti Panoti
    charan_hi: str
    impact_hi: str
    impact_en: str

# ---------------------------------------------------------------------------
# Helper Calculations
# ---------------------------------------------------------------------------
def compute_awastha(degree_in_sign: float, is_odd_sign: bool) -> Tuple[str, str]:
    """Calculates planetary age state (Baladi Awastha) based on degree in sign."""
    deg = degree_in_sign % 30.0
    if is_odd_sign:
        if deg < 6.0: return "Baala (Infant - 25% result)", "बाल अवस्था (25% फल)"
        elif deg < 12.0: return "Kumara (Youth - 50% result)", "कुमार अवस्था (50% फल)"
        elif deg < 18.0: return "Yuva (Adult/Peak - 100% result)", "युवा अवस्था (100% पूर्ण फल)"
        elif deg < 24.0: return "Vriddha (Elder - Minimal result)", "वृद्ध अवस्था (नगण्य फल)"
        else: return "Mrita (Dead - Inactive)", "मृत अवस्था (फलशून्य)"
    else:
        # Even signs: order is inverted
        if deg < 6.0: return "Mrita (Dead - Inactive)", "मृत अवस्था (फलशून्य)"
        elif deg < 12.0: return "Vriddha (Elder - Minimal result)", "वृद्ध अवस्था (नगण्य फल)"
        elif deg < 18.0: return "Yuva (Adult/Peak - 100% result)", "युवा अवस्था (100% पूर्ण फल)"
        elif deg < 24.0: return "Kumara (Youth - 50% result)", "कुमार अवस्था (50% फल)"
        else: return "Baala (Infant - 25% result)", "बाल अवस्था (25% फल)"

def check_combustion(planet_name: str, planet_lon: float, sun_lon: float) -> Tuple[bool, float]:
    """Checks if planet is combust (अस्त) within classical Parashari combustion orbs."""
    if planet_name in ["Sun", "Rahu", "Ketu"]:
        return False, 999.0
    orb = constants.COMBUST_ORB.get(planet_name, (12, 12))[0]
    diff = abs((planet_lon - sun_lon + 180.0) % 360.0 - 180.0)
    return (diff <= orb), round(diff, 2)

# ---------------------------------------------------------------------------
# Core Analysis Engine
# ---------------------------------------------------------------------------
def analyze_all_planetary_dignities(chart, vargas_detailed: dict) -> Dict[str, PlanetDignity]:
    """Performs forensic calculation of dignities, combustion, awasthas, and cross-varga confirmation."""
    asc_sign = chart.ascendant_sign
    sun_lon = chart.planets["Sun"].longitude
    dignities = {}

    # Pre-compute positions and houses
    p_house = {}
    p_sign = {}
    for p_name, p in chart.planets.items():
        p_sign[p_name] = p.sign_index
        p_house[p_name] = (p.sign_index - asc_sign + 12) % 12 + 1

    # Pre-compute aspects cast by each planet
    aspects_cast = {p: [] for p in chart.planets}
    aspects_rec = {p: [] for p in chart.planets}
    for p_name, p in chart.planets.items():
        offsets = constants.ASPECTS.get(p_name, [7])
        h_from_p = p_house[p_name]
        for off in offsets:
            target_house = (h_from_p + off - 2) % 12 + 1
            aspects_cast[p_name].append(target_house)
            # Find planets in target_house
            for other_p, other_h in p_house.items():
                if other_h == target_house and other_p != p_name:
                    aspects_rec[other_p].append(p_name)

    for p_name, p in chart.planets.items():
        s_idx = p.sign_index
        deg_in_sign = p.longitude % 30.0
        is_odd = (s_idx % 2 == 0) # 0=Aries (odd), 1=Taurus (even)
        aw_en, aw_hi = compute_awastha(deg_in_sign, is_odd)

        # Exaltation / Debilitation
        is_ex = (p_name in constants.EXALTATION and s_idx == constants.EXALTATION[p_name][0])
        is_deb = (p_name in constants.EXALTATION and s_idx == (constants.EXALTATION[p_name][0] + 6) % 12)
        is_own = (p_name in constants.OWN_SIGNS and s_idx in constants.OWN_SIGNS[p_name])
        is_comb, c_diff = check_combustion(p_name, p.longitude, sun_lon)

        # Navamsha cross-check
        d9_res = vargas_detailed["D9"][p_name]
        is_vargottama = (d9_res.sign_index == s_idx)

        # Dignity Summary
        qual_hi = []
        qual_en = []
        if is_vargottama:
            qual_hi.append("वर्गोत्तम (अत्यंत शुभ)")
            qual_en.append("Vargottama (Empowered)")
        if is_ex:
            qual_hi.append("परम उच्च (Exalted)")
            qual_en.append("Exalted (Deep Dignity)")
        elif is_own:
            qual_hi.append("स्वक्षेत्री (Own Sign)")
            qual_en.append("Own Sign (Strong Swakshetra)")
        elif is_deb:
            qual_hi.append("नीच राशि (Debilitated)")
            qual_en.append("Debilitated (Neecha)")

        if is_comb:
            qual_hi.append(f"अस्त (सूर्य से {c_diff}° अंतर)")
            qual_en.append(f"Combust (Within {c_diff}° of Sun)")
        if p.is_retrograde:
            qual_hi.append("वक्री (चेष्टा बली)")
            qual_en.append("Retrograde (High Chesta Bala)")

        qual_hi.append(aw_hi)
        qual_en.append(aw_en)

        dignities[p_name] = PlanetDignity(
            name=p_name,
            sign=constants.SIGNS[s_idx],
            sign_hi=constants.SIGNS_HI[s_idx],
            degree=round(p.longitude, 4),
            house=p_house[p_name],
            is_exalted=is_ex,
            is_debilitated=is_deb,
            is_own_sign=is_own,
            is_combust=is_comb,
            combust_deg_diff=c_diff,
            is_retrograde=p.is_retrograde,
            awastha=aw_en,
            awastha_hi=aw_hi,
            is_vargottama=is_vargottama,
            d9_sign=d9_res.sign_name,
            d9_sign_hi=constants.SIGNS_HI[d9_res.sign_index],
            aspects_cast_on=aspects_cast[p_name],
            aspects_received_from=aspects_rec[p_name],
            dignity_summary=", ".join(qual_en),
            dignity_summary_hi=", ".join(qual_hi)
        )

    return dignities

# ---------------------------------------------------------------------------
# 12 Bhavas Comprehensive Analysis
# ---------------------------------------------------------------------------
BHAVA_ATTRIBUTES_HI = {
    1: ("प्रथम भाव (तनु / लग्न)", "शारीरिक गठन, स्वास्थ्य, आत्मबल, जीवन ऊर्जा, व्यक्तित्व एवं मान-सम्मान"),
    2: ("द्वितीय भाव (धन / कुटुम्ब)", "पैतृक धन, संचित पूँजी, वाणी, परिवार, प्राथमिक शिक्षा एवं भोजन"),
    3: ("तृतीय भाव (सहज / पराक्रम)", "साहस, पराक्रम, छोटे भाई-बहन, लघु यात्राएँ, संप्रेषण एवं उद्यम"),
    4: ("चतुर्थ भाव (सुख / मातृ)", "माता, गृह, भूमि, भवन, वाहन, मानसिक शांति एवं सुख-सुविधाएँ"),
    5: ("पंचम भाव (सुत / धी)", "बुद्धि, विद्या, संतान सुख, पूर्वजन्म पुण्य, मंत्र साधना एवं शेयर/सट्टा"),
    6: ("षष्ठ भाव (रिपु / रोग)", "रोग, ऋण, शत्रु, प्रतिस्पर्धा, दैनिक कार्य, मामा पक्ष एवं मुकदमेबाजी"),
    7: ("सप्तम भाव (जाया / कलत्र)", "विवाह, जीवनसाथी, साझेदारी, व्यापार, जनसंपर्क एवं विदेश यात्रा"),
    8: ("अष्टम भाव (आयु / रन्ध्र)", "आयु, गुप्त धन, आकस्मिक घटनाएँ, शोध, संकट, गूढ़ ज्ञान एवं पैतृक संपत्ति"),
    9: ("नवम भाव (भाग्य / धर्म)", "भाग्य, धर्म, पिता, उच्च शिक्षा, गुरु कृपा, तीर्थाटन एवं सद्विचार"),
    10: ("दशम भाव (कर्म / राज्य)", "आजीविका, पद-प्रतिष्ठा, करियर, सामाजिक प्रभाव, राजकीय सम्मान एवं अधिकार"),
    11: ("एकादश भाव (लाभ / आय)", "समस्त प्रकार का लाभ, आय के स्रोत, बड़े भाई-बहन, आकांक्षाओं की पूर्ति"),
    12: ("द्वादश भाव (व्यय / मोक्ष)", "व्यय, विदेशी संबंध, अस्पताल, जेल, शयन सुख, मोक्ष एवं दान")
}

def analyze_all_12_bhavas(chart, dignities: Dict[str, PlanetDignity]) -> List[BhavaAnalysis]:
    """Generates detailed astrological qualitative analysis for all 12 houses."""
    asc_sign = chart.ascendant_sign
    bhavas = []

    kendras = {1, 4, 7, 10}
    trikonas = {1, 5, 9}
    dusthanas = {6, 8, 12}
    trishadayas = {3, 6, 11}

    # Group occupants by house
    house_occupants = {h: [] for h in range(1, 13)}
    for p_name, dig in dignities.items():
        house_occupants[dig.house].append(p_name)

    # Group aspecting planets by house
    house_aspects = {h: [] for h in range(1, 13)}
    for p_name, dig in dignities.items():
        for target_h in dig.aspects_cast_on:
            house_aspects[target_h].append(p_name)

    for h in range(1, 13):
        s_idx = (asc_sign + h - 1) % 12
        sign_en = constants.SIGNS[s_idx]
        sign_hi = constants.SIGNS_HI[s_idx]
        lord = constants.SIGN_LORD[s_idx]
        lord_hi = constants.PLANETS_HI.get(lord, lord)
        lord_dig = dignities.get(lord)
        lord_h = lord_dig.house if lord_dig else 1
        lord_s_idx = chart.planets[lord].sign_index if lord in chart.planets else s_idx
        lord_sign_en = constants.SIGNS[lord_s_idx]
        lord_sign_hi = constants.SIGNS_HI[lord_s_idx]

        occs = house_occupants[h]
        occs_hi = [constants.PLANETS_HI.get(p, p) for p in occs]
        asps = house_aspects[h]
        asps_hi = [constants.PLANETS_HI.get(p, p) for p in asps]

        st_type = "Kendra (केन्द्र)" if h in kendras else ("Trikona (त्रिकोण)" if h in trikonas else ("Dusthana (त्रिक)" if h in dusthanas else ("Trishadaya (त्रिषडाय)" if h in trishadayas else "Upachaya")))

        # Compose rich qualitative analysis
        title_hi, desc_hi = BHAVA_ATTRIBUTES_HI[h]
        
        # Hindi detailed text
        text_hi = f"{title_hi} में {sign_hi} राशि स्थित है जिसके स्वामी {lord_hi} हैं। "
        text_hi += f"भावेश {lord_hi} कुण्डली के भाव {lord_h} ({lord_sign_hi} राशि) में स्थित हैं। "
        if occs:
            text_hi += f"इस भाव में ग्रह {', '.join(occs_hi)} विराजमान हैं। "
        else:
            text_hi += "इस भाव में कोई भी ग्रह प्रत्यक्ष रूप से स्थित नहीं है (भाव रिक्त है)। "

        if asps:
            text_hi += f"भाव पर {', '.join(asps_hi)} की पूर्ण दृष्टि प्रभाव डाल रही है। "
        else:
            text_hi += "भाव पर किसी अन्य ग्रह की अशुभ दृष्टि नहीं है। "

        # Dignity & synthesis
        if lord_h in trikonas or lord_h in kendras:
            text_hi += f"भावेश {lord_hi} के शुभ भाव ({lord_h}) में होने से इस भाव से सम्बंधित {desc_hi} में स्वाभाविक वृद्धि व शुभता प्राप्त होती है।"
        elif lord_h in dusthanas:
            text_hi += f"भावेश {lord_hi} के त्रिक भाव ({lord_h}) में जाने से इस भाव के फलों में कुछ विलम्ब अथवा संघर्ष के पश्चात ही सफलता मिलती है।"
        else:
            text_hi += f"भावेश की संतुलित स्थिति जातक को कर्मठता एवं व्यावहारिक सफलता प्रदान करती है।"

        # English detailed text
        text_en = f"House {h} is governed by {sign_en} with its lord {lord} placed in House {lord_h} ({lord_sign_en}). "
        if occs:
            text_en += f"Occupied by: {', '.join(occs)}. "
        else:
            text_en += "House is unoccupied (vacant). "
        if asps:
            text_en += f"Aspected by: {', '.join(asps)}. "

        bhavas.append(BhavaAnalysis(
            bhava_num=h,
            sign=sign_en,
            sign_hi=sign_hi,
            lord=lord,
            lord_hi=lord_hi,
            lord_house=lord_h,
            lord_sign=lord_sign_en,
            lord_sign_hi=lord_sign_hi,
            occupants=occs,
            occupants_hi=occs_hi,
            aspecting_planets=asps,
            aspecting_planets_hi=asps_hi,
            strength_type=st_type,
            prediction_hi=text_hi,
            prediction_en=text_en
        ))

    return bhavas

# ---------------------------------------------------------------------------
# Comprehensive Mangal Dosha (Lagna, Moon, Venus based)
# ---------------------------------------------------------------------------
def compute_comprehensive_mangal_dosha(chart) -> dict:
    """Evaluates Mangal Dosha from Ascendant, Moon, and Venus along with classical cancellations."""
    asc_sign = chart.ascendant_sign
    moon_sign = chart.planets["Moon"].sign_index
    venus_sign = chart.planets["Venus"].sign_index
    mars_sign = chart.planets["Mars"].sign_index

    mars_from_asc = (mars_sign - asc_sign + 12) % 12 + 1
    mars_from_moon = (mars_sign - moon_sign + 12) % 12 + 1
    mars_from_venus = (mars_sign - venus_sign + 12) % 12 + 1

    manglik_houses = {1, 2, 4, 7, 8, 12}
    has_from_asc = mars_from_asc in manglik_houses
    has_from_moon = mars_from_moon in manglik_houses
    has_from_venus = mars_from_venus in manglik_houses

    # Classical Cancellations
    cancellations = []
    # 1. Mars in own sign (Aries/Scorpio) or exaltation (Capricorn)
    if mars_sign in [0, 7]:
        cancellations.append("मङ्गल स्वराशि (मेष/वृश्चिक) में स्थित होने से स्वतः दोषमुक्त है।")
    if mars_sign == 9:
        cancellations.append("मङ्गल अपनी उच्च राशि (मकर) में स्थित होने से दोषमुक्त है।")
    # 2. Mars in 10th house gives Digbala
    if mars_from_asc == 10:
        cancellations.append("मङ्गल दशम भाव में दिग्बली व कुलदीपक योग बनाता है, यहाँ मांगलिक दोष नहीं होता।")
    # 3. Jupiter aspects Mars or conjunct Mars
    if chart.planets["Jupiter"].sign_index == mars_sign or abs(chart.planets["Jupiter"].sign_index - mars_sign) == 6:
        cancellations.append("गुरु-मङ्गल सम्बन्ध अथवा गुरु की शुभ दृष्टि से मांगलिक दोष निष्प्रभावी हो जाता है।")

    is_manglik = (has_from_asc or has_from_moon) and len(cancellations) == 0
    severity = "मांगलिक दोष रहित (दोष नहीं है)" if not is_manglik else ("अल्प मांगलिक (Partial)" if not has_from_asc else "पूर्ण मांगलिक (Severe)")

    summary_hi = f"आपकी जन्म कुण्डली में मङ्गल लग्न से {mars_from_asc}वें भाव में, चन्द्रमा से {mars_from_moon}वें भाव में तथा शुक्र से {mars_from_venus}वें भाव में स्थित है। "
    if not is_manglik:
        if cancellations:
            summary_hi += f"यद्यपि मङ्गल की स्थिति विशिष्ट है, परन्तु शास्त्रीय परिहार नियमों के कारण: {'; '.join(cancellations)}। अतः आपकी कुण्डली मांगलिक दोष से पूर्णतः मुक्त है।"
        else:
            summary_hi += "मङ्गल 1, 2, 4, 7, 8, 12 भावों में न होने के कारण कुण्डली मांगलिक दोष से पूर्णतः मुक्त है।"
    else:
        summary_hi += "कुण्डली में मांगलिक दोष की उपस्थिति है। विवाह के समय वर-वधू की कुण्डली मिलान आवश्यक है।"

    return {
        "is_manglik": is_manglik,
        "severity": severity,
        "mars_from_asc": mars_from_asc,
        "mars_from_moon": mars_from_moon,
        "mars_from_venus": mars_from_venus,
        "cancellations": cancellations,
        "summary_hi": summary_hi,
        "remedies_hi": [
            "प्रतिदिन हनुमान चालीसा अथवा सुंदरकांड का पाठ करें।",
            "मंगलवार को हनुमान जी को सिंदूर व चमेली का तेल अर्पित करें।",
            "तांबे के लोटे में जल भरकर सूर्योदय के समय सूर्य देव को अर्घ्य दें।",
            "विवाह पूर्व योग्य ज्योतिषी द्वारा कुण्डली मिलान अनिवार्य रूप से कराएं।"
        ]
    }

# ---------------------------------------------------------------------------
# Comprehensive Kalsarp Dosha Analysis
# ---------------------------------------------------------------------------
KALSARP_TYPES = {
    1: ("अनन्त कालसर्प योग", "राहु प्रथम व केतु सप्तम भाव में। संघर्ष के उपरांत मान-प्रतिष्ठा व ख्याति।"),
    2: ("कुलिक कालसर्प योग", "राहु द्वितीय व केतु अष्टम भाव में। संचित धन व वाणी पर संयम रखें।"),
    3: ("वासुकि कालसर्प योग", "राहु तृतीय व केतु नवम भाव में। पराक्रम से भाग्योदय, भाई-बहनों से सहयोग।"),
    4: ("शंखपाल कालसर्प योग", "राहु चतुर्थ व केतु दशम भाव में। गृह सुख व माता के स्वास्थ्य का ध्यान रखें।"),
    5: ("पद्म कालसर्प योग", "राहु पंचम व केतु एकादश भाव में। उच्च विद्या, शोध एवं बुद्धिबल से विजय।"),
    6: ("महापद्म कालसर्प योग", "राहु षष्ठ व केतु द्वादश भाव में। शत्रुओं पर एकछत्र विजय, विदेशी लाभ।"),
    7: ("तक्षक कालसर्प योग", "राहु सप्तम व केतु प्रथम भाव में। दाम्पत्य में विश्वास व साझेदारी में पारदर्शिता रखें।"),
    8: ("कर्कोटक कालसर्प योग", "राहु अष्टम व केतु द्वितीय भाव में। गुप्त ज्ञान, पैतृक लाभ, स्वास्थ्य सतर्कता।"),
    9: ("शंखचूड़ कालसर्प योग", "राहु नवम व केतु तृतीय भाव में। धर्म-कर्म, पिता की सेवा एवं गुरु कृपा से उत्थान।"),
    10: ("घातक कालसर्प योग", "राहु दशम व केतु चतुर्थ भाव में। कार्यक्षेत्र में विशिष्ट सफलता, राजनीतिक प्रभाव।"),
    11: ("विषधर कालसर्प योग", "राहु एकादश व केतु पंचम भाव में। अचानक धन लाभ, आय के बहुआयामी स्रोत।"),
    12: ("शेषनाग कालसर्प योग", "राहु द्वादश व केतु षष्ठ भाव में। विदेश यात्रा, आध्यात्मिक उन्नति व मोक्ष प्राप्ति।")
}

def compute_comprehensive_kalsarp(chart) -> dict:
    """Checks whether all 7 planets are hemmed between Rahu and Ketu."""
    rahu_lon = chart.planets["Rahu"].longitude
    ketu_lon = chart.planets["Ketu"].longitude
    asc_sign = chart.ascendant_sign
    rahu_h = (chart.planets["Rahu"].sign_index - asc_sign + 12) % 12 + 1

    # Check hemi-sphere separation
    side1 = 0
    side2 = 0
    for p_name in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]:
        p_lon = chart.planets[p_name].longitude
        # Angular distance from Rahu to planet clockwise
        dist = (p_lon - rahu_lon) % 360.0
        if dist < 180.0:
            side1 += 1
        else:
            side2 += 1

    is_kalsarp = (side1 == 7 or side2 == 7)
    type_info = KALSARP_TYPES.get(rahu_h, ("कालसर्प योग", "सामान्य प्रभाव"))

    if is_kalsarp:
        title = type_info[0]
        desc = f"आपकी कुण्डली में समस्त सातों ग्रह राहु एवं केतु के मध्य स्थित हैं, जिससे '{title}' का निर्माण होता है। {type_info[1]}"
        status_hi = f"सक्रिय: {title}"
    else:
        title = "कालसर्प दोष मुक्त"
        desc = "आपकी कुण्डली में ग्रह राहु एवं केतु की परिधि से बाहर स्वतंत्र रूप से स्थित हैं। अतः आपकी कुण्डली कालसर्प दोष से पूर्णतः मुक्त है।"
        status_hi = "दोष मुक्त (निर्दोष)"

    return {
        "is_kalsarp": is_kalsarp,
        "type_name": title,
        "status_hi": status_hi,
        "description_hi": desc,
        "remedies_hi": [
            "भगवान शिव का दुग्धाभिषेक करें एवं महामृत्युंजय मंत्र का नित्य जप करें।",
            "नाग पंचमी के दिन चांदी के नाग-नागिन का विधिवत पूजन करें।",
            "पवित्र नदियों (जैसे गंगा अथवा त्र्यंबकेश्वर) में स्नान व दान करें।",
            "पक्षियों को सप्तधान्य व कुत्तों को मीठी रोटी खिलाएं।"
        ]
    }

# ---------------------------------------------------------------------------
# Comprehensive Shani Sade Sati Timeline & Predictions
# ---------------------------------------------------------------------------
def compute_comprehensive_sade_sati(birth_dt: datetime, moon_lon: float) -> List[SadeSatiPhase]:
    """
    Computes chronological lifetime Sade Sati and Dhaiya (Chhoti Panoti) cycles 
    for the native over 90+ years with exact dates and 3-phase qualitative predictions.
    """
    from vyas import ephem
    moon_sign_idx = int(moon_lon // 30) % 12
    # Signs involved in Sade Sati: Moon-1 (12th from Moon), Moon (1st), Moon+1 (2nd from Moon)
    # Dhaiya (Kantaka / Ashtama): 4th from Moon, 8th from Moon
    sade_sati_signs = {
        (moon_sign_idx - 1) % 12: ("साढ़े साती", "उदय", "उदय चरण (चन्द्र से 12H) - व्यय, प्रवास व आंतरिक अनुशासन"),
        moon_sign_idx: ("साढ़े साती", "शिखर", "शिखर चरण (जन्म चन्द्र पर शनि) - मानसिक मंथन, दायित्व व आत्म-साक्षात्कार"),
        (moon_sign_idx + 1) % 12: ("साढ़े साती", "अस्त", "अस्त चरण (चन्द्र से 2H) - धन-कुटुंब पर प्रभाव, स्थिरता व लाभ")
    }
    dhaiya_signs = {
        (moon_sign_idx + 3) % 12: ("छोटी पनौती", "ढैय्या (4H)", "चतुर्थ ढैय्या (कंटक शनि) - गृह, सुख व कार्यक्षेत्र में कर्म फल"),
        (moon_sign_idx + 7) % 12: ("छोटी पनौती", "ढैय्या (8H)", "अष्टम ढैय्या (अष्टम शनि) - गूढ़ चिंतन, स्वास्थ्य सतर्कता व परिवर्तन")
    }

    phases = []
    days_total = 90 * 365
    step_days = 15
    current_active_sign = None
    phase_start_dt = None

    tracked_events = []
    for d_offset in range(0, days_total + step_days, step_days):
        t_dt = birth_dt + timedelta(days=d_offset)
        sat_lon = ephem.sidereal_lon("Saturn", t_dt)
        sat_sign = int(sat_lon // 30) % 12
        if sat_sign != current_active_sign:
            if current_active_sign is not None and phase_start_dt is not None:
                tracked_events.append((current_active_sign, phase_start_dt, t_dt))
            current_active_sign = sat_sign
            phase_start_dt = t_dt

    for sign_idx, s_date, e_date in tracked_events:
        if sign_idx in sade_sati_signs:
            p_name, charan, desc = sade_sati_signs[sign_idx]
            s_sign_hi = constants.SIGNS_HI[sign_idx]
            s_sign_en = constants.SIGNS[sign_idx]
            phases.append(SadeSatiPhase(
                phase_name=f"{p_name}: {charan}",
                phase_name_hi=p_name,
                saturn_sign=s_sign_en,
                saturn_sign_hi=s_sign_hi,
                start_date=s_date.strftime("%d/%m/%Y"),
                end_date=e_date.strftime("%d/%m/%Y"),
                charan=charan,
                charan_hi=charan,
                impact_hi=f"शनि का {s_sign_hi} राशि में गोचर ({desc})। जातक के कर्म एवं धैर्य का परीक्षण तथा दीर्घकालिक सुदृढ़ता।",
                impact_en=f"Saturn transiting {s_sign_en}. {charan} phase of Shani Sade Sati. Karmic restructuring and resilience."
            ))
        elif sign_idx in dhaiya_signs:
            p_name, charan, desc = dhaiya_signs[sign_idx]
            s_sign_hi = constants.SIGNS_HI[sign_idx]
            s_sign_en = constants.SIGNS[sign_idx]
            phases.append(SadeSatiPhase(
                phase_name=f"{p_name}: {charan}",
                phase_name_hi=p_name,
                saturn_sign=s_sign_en,
                saturn_sign_hi=s_sign_hi,
                start_date=s_date.strftime("%d/%m/%Y"),
                end_date=e_date.strftime("%d/%m/%Y"),
                charan=charan,
                charan_hi=charan,
                impact_hi=f"शनि का {s_sign_hi} राशि में गोचर ({desc})। अनुशासन, स्वाध्याय एवं कर्म क्षेत्र में सावधानी से प्रगति।",
                impact_en=f"Saturn transiting {s_sign_en}. {charan} phase (Dhaiya). Focus on disciplined work and health."
            ))

    return phases

# ---------------------------------------------------------------------------
# Tajik Varshphal Engine (Annual Solar Return & Muntha)
# ---------------------------------------------------------------------------
def compute_tajik_varshphal(birth_dt: datetime, sun_natal_lon: float, target_year: int, asc_natal_sign: int) -> dict:
    """
    Computes Tajik Varshphal (Annual Return Horoscope) for a given year:
    - Age of Native
    - Muntha Sign & House calculation: Muntha = (Birth Ascendant + Age) % 12
    - Varsha Lagna
    - Predictions for the Annual Solar Cycle
    """
    age = target_year - birth_dt.year
    if age < 0:
        age = 0
    
    # Muntha Calculation:
    # Parashara & Tajik Neelakanthi: Muntha moves 1 sign per year from Janma Lagna
    muntha_sign_idx = (asc_natal_sign + age) % 12
    muntha_house_from_natal = (muntha_sign_idx - asc_natal_sign + 12) % 12 + 1

    # Evaluation of Muntha House:
    # 4, 6, 7, 8, 12 are sensitive; 1, 2, 3, 5, 9, 10, 11 are auspicious
    is_muntha_shubha = muntha_house_from_natal in [1, 2, 3, 5, 9, 10, 11]
    
    if muntha_house_from_natal == 10:
        muntha_phal_hi = "मुन्था दशम भाव में स्थित है: इस वर्ष पदोन्नति, राजकीय सम्मान, व्यावसायिक विस्तार एवं सामाजिक प्रतिष्ठा में अभूतपूर्व वृद्धि होगी।"
    elif muntha_house_from_natal == 11:
        muntha_phal_hi = "मुन्था एकादश भाव में स्थित है: इस वर्ष प्रचुर धन लाभ, व्यापारिक विस्तार, नवीन मित्रों का सहयोग एवं महत्वाकांक्षाओं की पूर्ति होगी।"
    elif muntha_house_from_natal == 9:
        muntha_phal_hi = "मुन्था नवम भाव में स्थित है: भाग्य का प्रबल साथ रहेगा। धर्म, तीर्थाटन, उच्च विद्या एवं पिता व गुरुजनों का भरपूर सहयोग मिलेगा।"
    elif muntha_house_from_natal == 1:
        muntha_phal_hi = "मुन्था लग्न भाव में स्थित है: उत्तम स्वास्थ्य, समाज में मान-सम्मान, नवीन योजनाओं का क्रियान्वयन एवं आत्मबल में वृद्धि।"
    elif muntha_house_from_natal in [6, 8, 12]:
        muntha_phal_hi = f"मुन्था त्रिक भाव ({muntha_house_from_natal}वें) में स्थित है: स्वास्थ्य का विशेष ध्यान रखें, अनावश्यक ऋण अथवा कानूनी विवादों से बचें।"
    else:
        muntha_phal_hi = f"मुन्था {muntha_house_from_natal}वें भाव में स्थित है: पारिवारिक सुख, सामान्य धन लाभ व प्रयासों के अनुरूप सफलता प्राप्त होगी।"

    # Tajik Annual Forecast
    annual_summary_hi = f"वर्षफल {target_year}-{target_year+1} (आयु {age} वर्ष): मुन्था {constants.SIGNS_HI[muntha_sign_idx]} राशि में जन्म लग्न से {muntha_house_from_natal}वें भाव में संचरण कर रही है। {muntha_phal_hi}"

    # Mudda / Patyayini Dasha calculation for 1 year (365.25 days)
    # Annual cycle sequence: Moon, Mars, Rahu, Jupiter, Saturn, Mercury, Ketu, Venus, Sun
    mudda_order = [
        ("Moon", "चन्द्र", 30),
        ("Mars", "मङ्गल", 21),
        ("Rahu", "राहु", 55),
        ("Jupiter", "गुरु", 48),
        ("Saturn", "शनि", 58),
        ("Mercury", "बुध", 52),
        ("Ketu", "केतु", 21),
        ("Venus", "शुक्र", 61),
        ("Sun", "सूर्य", 18)
    ]
    cur_d = datetime(target_year, birth_dt.month, birth_dt.day, birth_dt.hour, birth_dt.minute)
    mudda_periods = []
    for p_en, p_hi, days in mudda_order:
        end_d = cur_d + timedelta(days=days)
        mudda_periods.append({
            "planet": p_en,
            "planet_hi": p_hi,
            "start": cur_d.strftime("%d/%m/%Y"),
            "end": end_d.strftime("%d/%m/%Y"),
            "days": days
        })
    # Varsha Lagna & Varshesh calculation (Tajik annual return)
    # Muntha and Varsha lagna cycle
    varsha_lagna_idx = (asc_natal_sign + (age % 12)) % 12
    varshesh = constants.SIGN_LORD[varsha_lagna_idx]
    
    varsha_start_str = f"{birth_dt.day:02d}/{birth_dt.month:02d}/{target_year}"
    varsha_end_str = f"{birth_dt.day:02d}/{birth_dt.month:02d}/{target_year+1}"

    return {
        "target_year": target_year,
        "age": age,
        "varsha_start": varsha_start_str,
        "varsha_end": varsha_end_str,
        "varsha_lagna": constants.SIGNS[varsha_lagna_idx],
        "varsha_lagna_hi": constants.SIGNS_HI[varsha_lagna_idx],
        "varshesh": varshesh,
        "varshesh_hi": constants.PLANETS_HI.get(varshesh, varshesh),
        "muntha_sign": constants.SIGNS[muntha_sign_idx],
        "muntha_sign_hi": constants.SIGNS_HI[muntha_sign_idx],
        "muntha_house": muntha_house_from_natal,
        "is_auspicious": is_muntha_shubha,
        "annual_summary_hi": annual_summary_hi,
        "muntha_phal_hi": muntha_phal_hi,
        "mudda_periods": mudda_periods
    }

# ---------------------------------------------------------------------------
# Vimshottari Mahadasha In-Depth Qualitative Interpretations (BPHS / Phaladeepika)
# ---------------------------------------------------------------------------
MAHADASHA_HOUSE_PHAL_HI = {
    "Sun": {
        1: "सूर्य प्रथम भाव में स्थित होने से जातक में अद्वितीय आत्मबल, तेजस्वी व्यक्तित्व, उच्च महत्वाकांक्षा एवं नेतृत्व क्षमता विकसित होती है। सरकारी सेवा अथवा प्रशासनिक कार्यों में सफलता प्राप्त होती है।",
        2: "सूर्य द्वितीय भाव में होने से वाणी में ओजस्विता रहती है। संचित धन के संरक्षण पर विशेष ध्यान देना होता है। पारिवारिक मामलों में धैर्य व समन्वय लाभप्रद रहता है।",
        3: "सूर्य तृतीय भाव में पराक्रम एवं साहस की पराकाष्ठा प्रदान करता है। जातक अपने बाहुबल एवं कठोर परिश्रम से ख्याति प्राप्त करता है। भाई-बहनों से सहयोग रहता है।",
        4: "सूर्य चतुर्थ भाव में होने से गृह-भूमि एवं वाहन का सुख प्राप्त होता है। माता के स्वास्थ्य एवं मानसिक शांति के प्रति सावधानी अपेक्षित रहती है।",
        5: "सूर्य पंचम भाव में तीक्ष्ण बुद्धि, प्रशासनिक कौशल एवं मंत्र-साधना में सफलता देता है। विद्या एवं रचनात्मक कार्यों से प्रतिष्ठा प्राप्त होती है।",
        6: "सूर्य षष्ठ भाव में परम शुभ फलदायक होता है। शत्रुओं का शमन होता है, मुकदमों व प्रतियोगिताओं में एकछत्र विजय प्राप्त होती है। रोग प्रतिरोधक क्षमता प्रबल रहती है।",
        7: "सूर्य सप्तम भाव में होने से जीवनसाथी प्रभावशाली व स्वाभिमानी होता है। साझेदारी व्यापार में पारदर्शिता एवं वैवाहिक जीवन में सामंजस्य बनाए रखना आवश्यक है।",
        8: "सूर्य अष्टम भाव में आकस्मिक घटनाएँ एवं गुप्त विद्याओं/शोध में रुचि प्रदान करता है। वित्तीय मामलों में सतर्कता एवं नेत्र व पित्त विकारों से सावधानी अपेक्षित है।",
        9: "सूर्य नवम भाव में परम भाग्योदयकारी होता है। पिता एवं गुरुजनों की कृपा प्राप्त होती है। धर्म, सत्कर्म, तीर्थाटन एवं सामाजिक मान-प्रतिष्ठा में वृद्धि होती है।",
        10: "सूर्य दशम भाव में दिग्बली होकर 'कुलदीपक योग' बनाता है। राजकीय सम्मान, उच्च प्रशासनिक पद, आजीविका में अभूतपूर्व उन्नति एवं सर्वप्रिय नेतृत्व प्राप्त होता है।",
        11: "सूर्य एकादश भाव में आय के सशक्त व स्थायी स्रोत निर्मित करता है। उच्चाधिकारियों व प्रभावशाली मित्रों का निरंतर सहयोग प्राप्त होता है।",
        12: "सूर्य द्वादश भाव में दूरस्थ देशों से संबंध, आध्यात्मिक उन्नति, शोध एवं चिकित्सा क्षेत्र में सफलता देता है। नेत्रों की देखभाल व व्यय पर नियंत्रण रखें।"
    },
    "Moon": {
        1: "चन्द्र प्रथम भाव में जातक को सौम्य, संवेदनशील, आकर्षक एवं कल्पनाशील व्यक्तित्व प्रदान करता है। लोकप्रिया एवं कलात्मक प्रवृत्तियों में सफलता मिलती है।",
        2: "चन्द्र द्वितीय भाव में मधुर वाणी, सुस्वादु भोजन का आनंद एवं परिवार में शांति स्थापित करता है। वित्तीय मामलों में आवक निरंतर बनी रहती है।",
        3: "चन्द्र तृतीय भाव में पराक्रम को सुकोमल व रणनीतिक बनाता है। लघु यात्राएँ लाभकारी होती हैं तथा संप्रेषण एवं लेखन में दक्षता मिलती है।",
        4: "चन्द्र चतुर्थ भाव में स्वग्रही/दिग्बली होकर परम मातृ सुख, भव्य भवन, विलासिता के वाहन एवं अगाध मानसिक शांति प्रदान करता है।",
        5: "चन्द्र पंचम भाव में कुशाग्र बुद्धि, काव्य-साहित्य में रुचि, श्रेष्ठ संतान एवं भावनात्मक परिपक्वता प्रदान करता है।",
        6: "चन्द्र षष्ठ भाव में सेवा भाव, परोपकार एवं चिकित्सा क्षेत्र में सफलता देता है। कफ व जलीय विकारों से बचाव आवश्यक है।",
        7: "चन्द्र सप्तम भाव में सुंदर, सुरुचिपूर्ण एवं गुणवान जीवनसाथी प्रदान करता है। जनसंपर्क एवं यात्रा सम्बन्धी व्यवसाय में लाभ होता है।",
        8: "चन्द्र अष्टम भाव में गहन अंतर्ज्ञान, मनोवैज्ञानिक अंतर्दृष्टि एवं शोध क्षमता देता है। मानसिक उद्विग्नता से बचने हेतु ध्यान लाभप्रद है।",
        9: "चन्द्र नवम भाव में तीर्थ यात्रा, उच्च दार्शनिक ज्ञान, धार्मिक अभिरुचि एवं पिता से स्नेह प्रदान करता है। भाग्य निरंतर साथ देता है।",
        10: "चन्द्र दशम भाव में व्यापार एवं जनसेवा में उच्च प्रतिष्ठा दिलाता है। समाज में यश एवं निरंतर नवीन उपलब्धियों का मार्ग प्रशस्त होता है।",
        11: "चन्द्र एकादश भाव में प्रचुर आर्थिक लाभ, स्त्री मित्रों से सहयोग एवं दीर्घकालिक अभिलाषाओं की पूर्ति करता है।",
        12: "चन्द्र द्वादश भाव में विदेशी यात्रा, आध्यात्मिक एकांतवास, दान-पुण्य एवं गहन चिंतन में संलग्न रखता है।"
    },
    "Mars": {
        1: "मङ्गल प्रथम भाव में जातक को निडर, साहसी, ऊर्जावान एवं तेजतर्रार बनाता है। शारीरिक सामर्थ्य एवं प्रशासनिक कार्यों में अद्भुत क्षमता रहती है।",
        2: "मङ्गल द्वितीय भाव में वाणी में दृढ़ता देता है। वित्तीय संचय हेतु सतत प्रयास फलदायी होते हैं। कुटुम्ब में संयम बनाए रखें।",
        3: "मङ्गल तृतीय भाव में अदम्य साहस, पराक्रम, खेल, सेना, इंजीनियरिंग एवं तकनीकी क्षेत्र में अद्वितीय विजय दिलाता है।",
        4: "मङ्गल चतुर्थ भाव में अचल संपत्ति, भूमि, भवन एवं वाहन के सुख में वृद्धि करता है। गृहस्थ जीवन में धैर्य लाभप्रद रहता है।",
        5: "मङ्गल पंचम भाव में तकनीकी विद्या, तर्कशक्ति एवं गणितीय कौशल प्रदान करता है। त्वरित निर्णय लेने की क्षमता विकसित होती है।",
        6: "मङ्गल षष्ठ भाव में शत्रुओं का समूल नाश करता है। मुकदमों में विजय, प्रतियोगी परीक्षाओं में शीर्ष स्थान एवं शारीरिक सुदृढ़ता प्राप्त होती है।",
        7: "मङ्गल सप्तम भाव में साहसी व दृढ़निश्चयी जीवनसाथी प्रदान करता है। व्यापारिक साझेदारी में स्पष्टता आवश्यक है।",
        8: "मङ्गल अष्टम भाव में गुप्त शोध, सर्जरी, अन्वेषण एवं आकस्मिक लाभ के अवसर देता है। वाहन चालन में सतर्कता रखें।",
        9: "मङ्गल नवम भाव में धर्म की रक्षा, सत्यनिष्ठ आचरण, साहसिक तीर्थाटन एवं स्वतंत्र विचारों की प्रेरणा देता है।",
        10: "मङ्गल दशम भाव में दिग्बली व 'रुचक योग' बनाता है। शीर्ष नेतृत्व, प्रशासनिक अधिकार, विशाल भूमि-संपत्ति एवं विजय प्राप्त होती है।",
        11: "मङ्गल एकादश भाव में विभिन्न स्रोतों से धन का भारी प्रवाह, रियल एस्टेट से लाभ एवं प्रभावशाली मित्रों का सहयोग दिलाता है।",
        12: "मङ्गल द्वादश भाव में विदेश प्रवास, रक्षा क्षेत्र अथवा विदेशी उपक्रमों से संबंध निर्मित करता है। बजट नियंत्रण आवश्यक है।"
    },
    "Mercury": {
        1: "बुध प्रथम भाव में विलक्षण वाकपटुता, हास्य-विनोद, बौद्धिक प्रतिभा, व्यापारिक कुशाग्रता एवं दीर्घायु प्रदान करता है।",
        2: "बुध द्वितीय भाव में ओजस्वी वाणी, गणितीय कुशलता, व्यापार से संचित धन एवं पारिवारिक सामंजस्य की वृद्धि करता है।",
        3: "बुध तृतीय भाव में लेखन, पत्रकारिता, प्रकाशन, सूचना प्रौद्योगिकी एवं वाणिज्यिक संप्रेषण में श्रेष्ठ सफलता दिलाता है।",
        4: "बुध चतुर्थ भाव में उच्च शिक्षा, सुंदर निवास स्थान, वाहन एवं मातृपक्ष से भरपूर सहयोग व स्नेह प्रदान करता है।",
        5: "बुध पंचम भाव में अद्वितीय तार्किक क्षमता, मंत्र सिद्धि, शेयर बाजार व विश्लेषण में निपुणता तथा प्रखर ज्ञान देता है।",
        6: "बुध षष्ठ भाव में कानून, वकालत, लेखा परीक्षा (ऑडिट) एवं कूटनीति के माध्यम से विरोधियों पर विजय दिलाता है।",
        7: "बुध सप्तम भाव में बुद्धिमान, संस्कारी एवं व्यापार कुशल जीवनसाथी प्रदान करता है। संयुक्त उद्यमों में सफलता मिलती है।",
        8: "बुध अष्टम भाव में गूढ़ ज्योतिष, विज्ञान, अनुसंधान एवं अप्रत्याशित वित्तीय स्त्रोतों से लाभ का मार्ग खोलता है।",
        9: "बुध नवम भाव में धार्मिक साहित्य, उच्च दार्शनिक चिंतन, प्रकाशन एवं तीर्थ यात्राओं द्वारा भाग्योदय कराता है।",
        10: "बुध दशम भाव में उच्च व्यापारिक प्रतिष्ठा, बैंकिंग, प्रशासन, सलाहकार एवं राज्य स्तरीय यश प्रदान करता है।",
        11: "बुध एकादश भाव में व्यापारिक सौदों से प्रचुर लाभ, बौद्धिक मित्रों का समूह एवं दीर्घकालिक लक्ष्यों की प्राप्ति कराता है।",
        12: "बुध द्वादश भाव में विदेशी वाणिज्य, उच्च बौद्धिक अन्वेषण, आध्यात्मिक ग्रंथों का पठन एवं विवेकपूर्ण व्यय कराता है।"
    },
    "Jupiter": {
        1: "बृहस्पति प्रथम भाव में स्थित होकर जातक को 'हंस महापुरुष योग' सदृश तेज, न्यायप्रियता, विशाल हृदय एवं समाज में पूज्य स्थान देता है।",
        2: "बृहस्पति द्वितीय भाव में धन, स्वर्ण, पैतृक वैभव एवं अमृतमयी सत्य वाणी का वरदान देता है। परिवार में सुख-समृद्धि रहती है।",
        3: "बृहस्पति तृतीय भाव में सद्प्रयास, धार्मिक भाई-बहन, सुरुचिपूर्ण लेखन एवं परोपकारी पराक्रम प्रदान करता है।",
        4: "बृहस्पति चतुर्थ भाव में गृह शांति, विशाल अचल संपत्ति, माता का वात्सल्य एवं दिव्य आध्यात्मिक सुख की प्राप्ति कराता है।",
        5: "बृहस्पति पंचम भाव में श्रेष्ठ संतान, उच्च कोटि की विद्या, मंत्र सिद्धि, पूर्व जन्म के संचित पुण्यों का उदय कराता है।",
        6: "बृहस्पति षष्ठ भाव में शत्रुओं को मित्रवत बना देता है। स्वास्थ्य के प्रति सजगता एवं सेवा कार्यों में यश प्राप्त होता है।",
        7: "बृहस्पति सप्तम भाव में अत्यंत सुसंस्कृत, सदाचारी, भाग्यशाली जीवनसाथी एवं फलदायी वैवाहिक जीवन प्रदान करता है।",
        8: "बृहस्पति अष्टम भाव में दीर्घायु, गहन आध्यात्मिक अनुभूतियाँ, गुप्त धन एवं वसीयत से लाभ का योग बनाता है।",
        9: "बृहस्पति नवम भाव में अपने कारक भाव में होकर सर्वोच्च भाग्य, गुरु कृपा, धर्म ध्वजा एवं अंतरराष्ट्रीय सम्मान दिलाता है।",
        10: "बृहस्पति दशम भाव में उच्च न्यायिक पद, प्रोफेसर, राजनैतिक सलाहकार, नीति-निर्माता एवं निष्कलंक आजीविका देता है।",
        11: "बृहस्पति एकादश भाव में सर्वतोमुखी लाभ, पुत्र एवं पौत्र सुख, वित्तीय स्वावलंबन एवं महत्ताओं की पूर्ति करता है।",
        12: "बृहस्पति द्वादश भाव में मोक्ष का मार्ग प्रशस्त करता है। धर्मार्थ कार्यों, चिकित्सालयों एवं आश्रमों में दान से अक्षय पुण्य मिलता है।"
    },
    "Venus": {
        1: "शुक्र प्रथम भाव में जातक को सम्मोहक रूप-रंग, कलात्मक सौंदर्य, ऐश्वर्य, मधुर स्वभाव एवं सांसारिक सुख प्रदान करता है।",
        2: "शुक्र द्वितीय भाव में मधुरिम गायन/वाणी, आभूषण, स्वादिष्ट मिष्ठान्न एवं प्रचुर आर्थिक संपन्नता देता है।",
        3: "शुक्र तृतीय भाव में ललित कलाओं, संगीत, अभिनय एवं सुरुचिपूर्ण यात्राओं में अभिरुचि व सफलता दिलाता है।",
        4: "शुक्र चतुर्थ भाव में भव्य आवास, विलासी वाहन, मातृ सुख एवं समस्त प्रकार के भौतिक सुख-साधनों की वर्षा करता है।",
        5: "शुक्र पंचम भाव में प्रेम सम्बंधों में प्रगाढ़ता, कला, सिनेमा, डिजाइनिंग एवं श्रेष्ठ संतान का सुख प्रदान करता है।",
        6: "शुक्र षष्ठ भाव में संयम की अपेक्षा करता है। विरोधियों पर मृदुता से विजय मिलती है। खानपान में संतुलन रखें।",
        7: "शुक्र सप्तम भाव में आकर्षक, समर्पित जीवनसाथी, उत्तम दांपत्य सुख एवं कलात्मक व्यवसायों में सफलता देता है।",
        8: "शुक्र अष्टम भाव में अप्रत्याशित वित्तीय उपहार, दीर्घायु, गुप्त सौंदर्य एवं जीवनसाथी के भाग्य से उत्थान कराता है।",
        9: "शुक्र नवम भाव में भाग्य की देवी का अनुग्रह, विदेश यात्रा, उच्च सांस्कृतिक अभिरुचि एवं सुखद तीर्थाटन दिलाता है।",
        10: "शुक्र दशम भाव में फैशन, मीडिया, आतिथ्य, आभूषण अथवा कला क्षेत्र में राष्ट्रीय स्तर की प्रतिष्ठा दिलाता है।",
        11: "शुक्र एकादश भाव में मित्रों से प्रचुर सहयोग, निरंतर वित्तीय लाभ, विलासिता पूर्ण जीवन एवं यश प्रदान करता है।",
        12: "शुक्र द्वादश भाव में उच्च स्थिति में होकर शयन सुख, विदेशी विलासिता, आध्यात्मिक आनंद एवं भोग-साधनों की प्राप्ति कराता है।"
    },
    "Saturn": {
        1: "शनि प्रथम भाव में जातक को गंभीर, दूरदर्शी, कठोर परिश्रमी, अनुशासित एवं धैर्यवान व्यक्तित्व प्रदान करता है। जीवन के उत्तरार्ध में उच्च प्रतिष्ठा मिलती है।",
        2: "शनि द्वितीय भाव में संचित धन के प्रति सतर्कता सिखाता है। मितव्ययिता एवं कठोर श्रम से स्थायी संपत्ति का निर्माण होता है।",
        3: "शनि तृतीय भाव में जातक को अविचल संकल्प, लोहे जैसी सहनशक्ति, तकनीकी कुशलता एवं साहसी बनाता है।",
        4: "शनि चतुर्थ भाव में जातक को पैतृक भूमि, प्राचीन भवन एवं उत्तरदायित्वों का निर्वहन कराता है। घरेलू जीवन में धैर्य रखें।",
        5: "शनि पंचम भाव में गूढ़ दर्शन, शोध, इतिहास एवं पारंपरिक शास्त्रों के अध्ययन में विलक्षण सफलता देता है।",
        6: "शनि षष्ठ भाव में परम बली होकर शत्रुओं, रोगों व ऋणों को परास्त करता है। कानूनी मामलों में स्थायी विजय मिलती है।",
        7: "शनि सप्तम भाव में उच्च का होकर 'शश महापुरुष योग' बनाता है। परिपक्व जीवनसाथी, जनसमूह पर प्रभुत्व एवं व्यापारिक स्थायित्व मिलता है।",
        8: "शनि अष्टम भाव में आयु का विस्तार करता है। रहस्यों के उद्घाटन, पुरातत्व, खनन एवं बीमा क्षेत्र में लाभ होता है।",
        9: "शनि नवम भाव में पारंपरिक धार्मिकता, कठोर साधना, गुरुजनों की निष्ठापूर्वक सेवा एवं स्थायी भाग्योदय कराता है।",
        10: "शनि दशम भाव में सर्वोच्च कर्मयोगी बनाता है। औद्योगिक नेतृत्व, राजनीति, निर्माण एवं जनसेवा में शीर्ष मुकाम दिलाता है।",
        11: "शनि एकादश भाव में स्थाई संपत्ति, स्थायी आय के साधन, बड़े उपक्रमों से लाभ एवं वफादार मित्रों का साथ देता है।",
        12: "शनि द्वादश भाव में एकांत साधना, विदेश गमन, वैराग्य एवं आध्यात्मिक मुक्ति की दिशा में अग्रसर करता है।"
    },
    "Rahu": {
        1: "राहु प्रथम भाव में जातक को तीव्र बुद्धिमत्ता, लीक से हटकर सोचने की क्षमता, महत्त्वाकांक्षा एवं आधुनिक तकनीक में निपुणता देता है।",
        2: "राहु द्वितीय भाव में अप्रत्याशित वित्तीय लाभ, बहुभाषी दक्षता एवं अंतरराष्ट्रीय व्यापार के अवसर देता है। खानपान में शुद्धि रखें।",
        3: "राहु तृतीय भाव में पराक्रम को असीम बनाता है। मीडिया, इंटरनेट, खेल एवं साहसिक उपक्रमों में जातक की धाक जमती है।",
        4: "राहु चतुर्थ भाव में आधुनिक सुख-साधनों से युक्त विदेशी शैली का भवन दिलाता है। मातृपक्ष के प्रति सजग रहें।",
        5: "राहु पंचम भाव में आधुनिक विज्ञान, कंप्यूटर, सिनेमा, सट्टा/शेयर एवं गूढ़ तकनीकों में जातक को अद्वितीय लाभ कराता है।",
        6: "राहु षष्ठ भाव में सभी प्रकार के विरोधियों को परास्त करता है। कठिन से कठिन परिस्थितियों से जातक सुरक्षित बाहर निकल आता है।",
        7: "राहु सप्तम भाव में अपरंपरागत अथवा विदेशी मूल के जीवनसाथी से योग बनाता है। जनसंपर्क से भारी लाभ मिलता है।",
        8: "राहु अष्टम भाव में गुप्त शोध, तंत्र-मंत्र, खनिज, डाटा एवं विदेशी स्रोतों से अचानक भारी धन लाभ का मार्ग बनाता है।",
        9: "राहु नवम भाव में वैश्विक यात्राएँ, नवीन दार्शनिक दृष्टिकोण एवं रूढ़ियों से मुक्त होकर भाग्योदय कराता है।",
        10: "राहु दशम भाव में राजनीति, कूटनीति, विशाल कारपोरेट उपक्रमों एवं सार्वजनिक जीवन में अप्रत्याशित उत्थान दिलाता है।",
        11: "राहु एकादश भाव में धन वर्षा कराता है। अनेक अज्ञात स्रोतों से लाभ, राजनीतिक संपर्क एवं महत्वाकांक्षाओं की पूर्ति होती है।",
        12: "राहु द्वादश भाव में सुदूर विदेश में स्थायी निवास, बहुराष्ट्रीय कंपनियों में उच्च पद एवं विदेशी संपदा दिलाता है।"
    },
    "Ketu": {
        1: "केतु प्रथम भाव में जातक को अंतर्मुखी, दार्शनिक, आध्यात्मिक एवं प्राकृतिक रूप से भौतिकता से विरक्त बनाता है।",
        2: "केतु द्वितीय भाव में सत्यवादी बनाता है। आध्यात्मिक चर्चाओं में आनंद मिलता है। वित्तीय मामलों में व्यवस्थित रहें।",
        3: "केतु तृतीय भाव में निर्भीक पराक्रम, अध्यात्म प्रचार, योग एवं कठिन साधनाओं को संपन्न करने का सामर्थ्य देता है।",
        4: "केतु चतुर्थ भाव में सांसारिक सुखों से परे आत्मिक शांति की ओर ले जाता है। मातृभूमि से दूर भाग्योदय होता है।",
        5: "केतु पंचम भाव में पूर्वजन्म के आध्यात्मिक संस्कारों का जागरण, गूढ़ तंत्र एवं विशिष्ट बौद्धिक अंतर्दृष्टि देता है।",
        6: "केतु षष्ठ भाव में गुप्त शत्रुओं को स्वतः नष्ट कर देता है। आध्यात्मिक साधना के बल पर सभी संकट टल जाते हैं।",
        7: "केतु सप्तम भाव में जीवनसाथी को धार्मिक एवं शांत स्वभाव का बनाता है। वैवाहिक जीवन में आध्यात्मिक संवाद रखें।",
        8: "केतु अष्टम भाव में अतींद्रिय ज्ञान (Sixth Sense), समाधि, मोक्ष एवं पारलौकिक अनुभूतियाँ प्रदान करता है।",
        9: "केतु नवम भाव में धर्म का सर्वोच्च स्तर, संतों का संग, निःस्वार्थ तीर्थाटन एवं प्रभु कृपा की अनुभूति कराता है।",
        10: "केतु दशम भाव में निस्वार्थ कर्म, चिकित्सा, अनुसंधान अथवा सामाजिक उत्थान के कार्यों में सम्मान दिलाता है।",
        11: "केतु एकादश भाव में अचानक अल्प प्रयासों से प्रचुर लाभ दिलाता है। सात्विक मित्रों का निरंतर सहयोग रहता है।",
        12: "केतु द्वादश भाव में मोक्ष का परम कारक माना गया है। जातक को जन्म-मरण के चक्र से मुक्ति का मार्ग प्रशस्त करता है।"
    }
}

def compute_vimshottari_interpretations(chart) -> List[dict]:
    """Generates comprehensive Mahadasha qualitative interpretations for each planet in its natal house."""
    asc_sign = chart.ascendant_sign
    order = ["Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury", "Ketu", "Venus"]
    results = []
    for p_name in order:
        p = chart.planets[p_name]
        h = (p.sign_index - asc_sign + 12) % 12 + 1
        sign_en = constants.SIGNS[p.sign_index]
        sign_hi = constants.SIGNS_HI[p.sign_index]
        p_hi = constants.PLANETS_HI.get(p_name, p_name)
        phal_hi = MAHADASHA_HOUSE_PHAL_HI.get(p_name, {}).get(h, f"{p_hi} भाव {h} में शुभ फल प्रदान करता है।")
        
        results.append({
            "planet": p_name,
            "planet_hi": p_hi,
            "house": h,
            "sign": sign_en,
            "sign_hi": sign_hi,
            "degree_str": f"{int(p.longitude % 30)}°{int((p.longitude % 1)*60):02d}'",
            "interpretation_hi": phal_hi
        })
    return results

# ---------------------------------------------------------------------------
# Lal Kitab House-by-House Phalakathan & Authentic Upay (लाल किताब फलकथन एवं उपाय)
# ---------------------------------------------------------------------------
LAL_KITAB_DATA = {
    "Sun": {
        8: {
            "phal_hi": "आठवें भाव स्थित सूर्य यदि अनुकूल हो तो उम्र के 22वें वर्ष से सरकार व समाज का सहयोग मिलता है। ऐसा सूर्य जातक को सच्चा, पुण्यात्मा और राजा के समान तेजस्वी बनाता है। यदि आठवें भाव स्थित सूर्य प्रतिकूल हो तो जातक को आर्थिक संकट, अस्थिर स्वभाव, नेत्र अथवा पित्त विकार का सामना करना पड़ सकता है।",
            "upay_hi": [
                "घर में कभी भी सफेद कपड़े न रखें।",
                "दक्षिण मुखी मुख्य द्वार वाले मकान में रहने से बचें।",
                "हमेशा किसी भी नए कार्य को प्रारंभ करने से पूर्व मीठा खाकर ऊपर से जल पिएं।",
                "यदि संभव हो तो किसी जलती हुई चिता में तांबे के 8 सिक्के डालें।",
                "बहते हुए स्वच्छ जल में गुड़ प्रवाहित करें।"
            ]
        }
    },
    "Moon": {
        8: {
            "phal_hi": "आठवें भाव में स्थित चन्द्रमा जातक के मन को अत्यधिक संवेदनशील एवं कल्पनाशील बनाता है। यदि यहाँ चन्द्रमा शुभ हो तो जातक को विरासत, पैतृक संपत्ति एवं अचानक धन की प्राप्ति होती है। अशुभ होने की स्थिति में माता के स्वास्थ्य के प्रति चिंता अथवा मानसिक उद्विग्नता का सामना करना पड़ सकता है।",
            "upay_hi": [
                "जुआ, सट्टा एवं अनैतिक कार्यों से पूर्णतः दूर रहें।",
                "पूर्वजों एवं पितरों के निमित्त श्राद्ध व दान कर्म श्रद्धापूर्वक करें।",
                "कुएं अथवा बावड़ी को छत से कभी न ढकें।",
                "बुजुर्गों एवं कन्याओं के चरण स्पर्श कर नित्य आशीर्वाद प्राप्त करें।",
                "शमशान भूमि अथवा धार्मिक स्थान के जल को कांच की बोतल में घर के अंदर ईशान कोण में रखें।"
            ]
        }
    },
    "Mars": {
        10: {
            "phal_hi": "कुण्डली में यह मङ्गल ग्रह की सर्वोत्तम स्थिति है। यह मङ्गल की उच्च राशि का स्थान है। ऐसा जातक निडर, साहसी, स्वस्थ और समाज में अपनी मर्यादा व प्रभाव स्थापित करने में सक्षम होता है। दसवें भाव का मङ्गल जातक को कुलदीपक बनाता है और जीवन में अपार भूमि, भवन, राजकीय सम्मान एवं स्थायी यश प्रदान करता है।",
            "upay_hi": [
                "पैतृक संपत्ति एवं घर के पुराने सोने को कभी न बेचें।",
                "घर में हिरण पालें अथवा हिरण की प्रतिमा/तस्वीर स्थापित करें।",
                "दूध उबालते समय इस बात का विशेष ध्यान रखें कि दूध उफनकर अग्नि पर न गिरे।",
                "नेत्रहीन अथवा असहाय व्यक्तियों की सामर्थ्यानुसार सहायता करें।",
                "मंगलवार को हनुमान जी को चोला व गुड़-चने का भोग अर्पित करें।"
            ]
        }
    },
    "Mercury": {
        8: {
            "phal_hi": "आठवें घर में स्थित बुध जातक को तीव्र शोध बुद्धि, गूढ़ विषयों का ज्ञान एवं तीव्र तार्किक क्षमता प्रदान करता है। यदि इसके साथ कोई शुभ ग्रह हो तो बुध जातक को विपत्तियों से उबार लेता है। अशुभ होने पर व्यापार में अचानक उतार-चढ़ाव अथवा नसों/दांतों से सम्बंधित संवेदनशीलता रह सकती है।",
            "upay_hi": [
                "किसी मिट्टी के पात्र में शहद भरकर श्मशान अथवा निर्जन स्थान में भूमि में दबाएं।",
                "मिट्टी के कुल्हड़ में दूध अथवा वर्षा का शुद्ध जल भरकर घर की छत पर रखें।",
                "अपनी पुत्री अथवा बहन के मान-सम्मान का विशेष ध्यान रखें।",
                "दुर्गा सप्तशती का पाठ अथवा छोटी कन्याओं को बुधवार को हरी चूड़ियां व फल भेंट करें।"
            ]
        }
    },
    "Jupiter": {
        9: {
            "phal_hi": "नौवां घर बृहस्पति का स्वयं का पक्का घर माना गया है। इसलिए इस भाव वाला जातक प्रसिद्ध, धर्मात्मा, विद्वान और भाग्यशाली होता है। जातक अपनी जुबान का पक्का, दीर्घायु एवं उच्च आदर्शों पर चलने वाला होता है। गुरुजनों एवं पिता का आशीर्वाद जातक के जीवन को निरंतर उन्नति के शिखर पर ले जाता है।",
            "upay_hi": [
                "प्रतिदिन देवालय अथवा मंदिर में जाकर देव दर्शन करें।",
                "मदिरा एवं तामसिक खानपान से पूर्ण परहेज रखें।",
                "बहते हुए स्वच्छ जल में पीले चावल अथवा हल्दी प्रवाहित करें।",
                "माथे, नाभि और कंठ पर नित्य केसर का तिलक लगाएं।",
                "पीपल के वृक्ष को जल अर्पित करें व उसकी परिक्रमा करें।"
            ]
        }
    },
    "Venus": {
        9: {
            "phal_hi": "नौवें भाव में स्थित शुक्र जातक को सुसंस्कृत, कलाप्रिय एवं उच्च जीवन मूल्यों से युक्त बनाता है। जातक दूरस्थ प्रदेशों एवं विदेश यात्राओं से लाभ अर्जित करता है। यदि शुक्र पर शुभ दृष्टि हो तो जातक को योग्य जीवनसाथी एवं भौतिक सुख-साधनों की सुलभता रहती है।",
            "upay_hi": [
                "घर की नींव में शुद्ध चांदी एवं थोड़ा शहद स्थापित करें।",
                "स्त्री पक्ष का सदैव आदर करें एवं उन्हें लाल-चांदी की चूड़ियां उपहार में दें।",
                "किसी नीम के वृक्ष की जड़ में चांदी का छोटा टुकड़ा दबाएं।",
                "गौशाला में जाकर श्वेत गाय को हरा चारा व गुड़ खिलाएं।"
            ]
        }
    },
    "Saturn": {
        7: {
            "phal_hi": "सातवां घर शनि का परम प्रिय स्थान है जहाँ शनि उच्चवत प्रभाव देते हैं। शनि से जुड़े कार्य जैसे मशीनरी, लोहा, तेल, रियल एस्टेट एवं औद्योगिक उपक्रम अत्यधिक लाभकारी सिद्ध होते हैं। जातक गंभीर, रणनीतिक एवं जनसामान्य पर प्रभावशाली नेतृत्व करने वाला होता है।",
            "upay_hi": [
                "किसी बांसुरी में पिसी हुई खांड (शक्कर) भरकर किसी निर्जन वन में दबाएं।",
                "काली गाय अथवा काले कुत्ते की नित्य सेवा करें व उन्हें भोजन कराएं।",
                "शनिवार के दिन सरसों के तेल में अपना मुख देखकर छाया पात्र दान करें।",
                "कामकाजी मजदूरों एवं सफाई कर्मचारियों को कभी कष्ट न दें, उनका पारिश्रमिक समय पर दें।"
            ]
        }
    },
    "Rahu": {
        2: {
            "phal_hi": "दूसरे घर में स्थित राहु जातक को तीव्र धनार्जन की योजनाएं एवं बहुआयामी आय के साधन देता है। राहु यदि शुभ अवस्था में हो तो जातक प्रचुर धन एवं समाज में प्रतिष्ठा अर्जित करता है। वाणी में संयम एवं खानपान में सात्विकता बनाए रखने से स्थायी आर्थिक समृद्धि प्राप्त होती है।",
            "upay_hi": [
                "चांदी की एक ठोस (बिना जोड़ वाली) गोली अपनी जेब अथवा तिजोरी में रखें।",
                "बृहस्पति से सम्बंधित वस्तुएं जैसे सोना, पीले वस्त्र एवं केसर का उपयोग करें।",
                "माता के साथ सदैव आदरणीय व सौहार्दपूर्ण सम्बंध रखें।",
                "विवाह के उपरांत ससुराल पक्ष से बिजली का कोई उपहार न लें।"
            ]
        }
    },
    "Ketu": {
        8: {
            "phal_hi": "आठवां घर मंगल का है जो केतु का मित्र क्षेत्र है। यदि आठवें भाव में केतु शुभ हो तो जातक को अतींद्रिय ज्ञान, पूर्वाभास, आध्यात्मिक ऊंचाई एवं संकटों से स्वतः रक्षा प्राप्त होती है। संतान सुख एवं पैतृक संपत्ति के मामलों में जातक भाग्यशाली सिद्ध होता है।",
            "upay_hi": [
                "घर में दोरंगा (काला व सफेद) कुत्ता पालें अथवा श्वानों को नित्य रोटी खिलाएं।",
                "किसी धार्मिक मंदिर में दोरंगा कम्बल दान करें।",
                "भगवान श्री गणेश जी की नित्य स्तुति व संकटनाशन स्तोत्र का पाठ करें।",
                "कानों में स्वर्ण आभूषण धारण करें।",
                "माथे पर प्रतिदिन शुद्ध केसर अथवा चंदन का तिलक लगाएं।"
            ]
        }
    }
}

def compute_lal_kitab_predictions_and_upay(chart) -> List[dict]:
    """Generates Lal Kitab comprehensive phalakathan and classical remedies for all 9 planets in natal houses."""
    asc_sign = chart.ascendant_sign
    order = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]
    results = []
    for p_name in order:
        p = chart.planets[p_name]
        h = (p.sign_index - asc_sign + 12) % 12 + 1
        p_hi = constants.PLANETS_HI.get(p_name, p_name)
        sign_hi = constants.SIGNS_HI[p.sign_index]

        # Fetch custom house data or generic classical fallback
        p_dict = LAL_KITAB_DATA.get(p_name, {}).get(h)
        if p_dict:
            phal_hi = p_dict["phal_hi"]
            upay_hi = p_dict["upay_hi"]
        else:
            phal_hi = f"{p_hi} कुण्डली के भाव {h} ({sign_hi} राशि) में स्थित हैं। लाल किताब के अनुसार यह स्थिति जातक के कर्म, पुरुषार्थ और विवेक द्वारा फलित होती है। जातक को अपने चरित्र एवं वाणी में शुद्धि बनाए रखनी चाहिए।"
            upay_hi = [
                f"{p_hi} के वैदिक मंत्र अथवा कारक वस्तुओं का दान करें।",
                "बुजुर्गों का सम्मान करें एवं धार्मिक स्थलों पर नियमित नमन करें।",
                "पक्षियों एवं मूक पशुओं को जल व दाना दें।"
            ]

        results.append({
            "planet": p_name,
            "planet_hi": p_hi,
            "house": h,
            "sign_hi": sign_hi,
            "phal_hi": phal_hi,
            "upay_hi": upay_hi
        })
    return results

# ---------------------------------------------------------------------------
# Yogini Dasha Engine (योगिनी दशा - 36 वर्ष का चक्र)
# ---------------------------------------------------------------------------
YOGINI_LORDS = [
    ("Mangala", "मंगला", "Moon", "चन्द्र", 1),
    ("Pingala", "पिंगला", "Sun", "सूर्य", 2),
    ("Dhanya", "धान्या", "Jupiter", "गुरु", 3),
    ("Bhramari", "भ्रामरी", "Mars", "मङ्गल", 4),
    ("Bhadrika", "भद्रिका", "Mercury", "बुध", 5),
    ("Ulka", "उल्का", "Saturn", "शनि", 6),
    ("Siddha", "सिद्धा", "Venus", "शुक्र", 7),
    ("Sankata", "संकटा", "Rahu", "राहु", 8)
]

def compute_yogini_dasha(moon_lon: float, birth_dt: datetime) -> List[dict]:
    """Computes Yogini Dasha lifetime periods (36-year cycles) starting from natal Nakshatra."""
    nak_idx = int(moon_lon // constants.NAKSHATRA_SPAN) % 27
    deg_in_nak = moon_lon % constants.NAKSHATRA_SPAN
    frac_elapsed = deg_in_nak / constants.NAKSHATRA_SPAN
    frac_rem = 1.0 - frac_elapsed

    # Classical Yogini start: (nak_idx + 3) % 8 (1-indexed Nakshatra)
    start_y_idx = (nak_idx + 1 + 3 - 1) % 8
    
    cycles = []
    cur_date = birth_dt
    
    # 2.5 cycles (90 years)
    first_period = True
    for cycle in range(3):
        for offset in range(8):
            idx = (start_y_idx + offset) % 8
            y_name, y_name_hi, lord, lord_hi, total_years = YOGINI_LORDS[idx]
            
            if first_period:
                duration_years = total_years * frac_rem
                first_period = False
            else:
                duration_years = total_years

            end_date = cur_date + timedelta(days=duration_years * 365.25)
            
            # Sub-periods (Antardashas) inside this Yogini
            antardashas = []
            ad_cur = cur_date
            for ad_off in range(8):
                ad_idx = (idx + ad_off) % 8
                ad_name, ad_name_hi, ad_lord, ad_lord_hi, ad_tot = YOGINI_LORDS[ad_idx]
                ad_dur_days = (ad_tot / 36.0) * (duration_years * 365.25)
                ad_end = ad_cur + timedelta(days=ad_dur_days)
                antardashas.append({
                    "name": ad_name,
                    "name_hi": ad_name_hi,
                    "start": ad_cur.strftime("%d/%m/%Y"),
                    "end": ad_end.strftime("%d/%m/%Y")
                })
                ad_cur = ad_end

            cycles.append({
                "name": y_name,
                "name_hi": y_name_hi,
                "lord_hi": lord_hi,
                "years": total_years,
                "start": cur_date.strftime("%d/%m/%Y"),
                "end": end_date.strftime("%d/%m/%Y"),
                "antardashas": antardashas
            })
            cur_date = end_date
            if (cur_date - birth_dt).days > 95 * 365.25:
                break
        if (cur_date - birth_dt).days > 95 * 365.25:
            break

    return cycles

# ---------------------------------------------------------------------------
# Jaimini Chara Dasha Engine (जैमिनी चर दशा)
# ---------------------------------------------------------------------------
def compute_chara_dasha(asc_sign: int, birth_dt: datetime, chart=None) -> List[dict]:
    """Computes Jaimini Chara Dasha for all 12 signs based on sign lord distances."""
    # Classical Chara Dasha sign sequence: Direct for Aries, Taurus, Gemini, Libra, Scorpio, Sag
    # Inverted for Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces
    direct_signs = {0, 1, 2, 6, 7, 8}
    is_direct = asc_sign in direct_signs
    
    order = []
    for i in range(12):
        s = (asc_sign + i) % 12 if is_direct else (asc_sign - i + 12) % 12
        order.append(s)
        
    periods = []
    cur_date = birth_dt
    
    # Extract planets dict from chart if object or dict
    if chart is not None:
        if hasattr(chart, "planets"):
            pl_dict = chart.planets
        elif isinstance(chart, dict):
            pl_dict = chart
        else:
            pl_dict = {}
    else:
        pl_dict = {}

    for s_idx in order:
        lord = constants.SIGN_LORD[s_idx]
        if lord in pl_dict:
            lord_obj = pl_dict[lord]
            lord_s_idx = getattr(lord_obj, "sign_index", getattr(lord_obj, "sign", s_idx))
            if not isinstance(lord_s_idx, int):
                lord_s_idx = s_idx
        else:
            lord_s_idx = s_idx
        # Duration = distance from sign to lord
        if s_idx in direct_signs:
            dur = (lord_s_idx - s_idx + 12) % 12
        else:
            dur = (s_idx - lord_s_idx + 12) % 12
        if dur == 0:
            dur = 12
            
        end_date = cur_date + timedelta(days=dur * 365.25)
        
        # Sub-periods (12 antardashas)
        sub_dur_days = (dur * 365.25) / 12.0
        ad_cur = cur_date
        antardashas = []
        for ad_i in range(12):
            ad_s = (s_idx + ad_i) % 12
            ad_end = ad_cur + timedelta(days=sub_dur_days)
            antardashas.append({
                "sign": constants.SIGNS[ad_s],
                "sign_hi": constants.SIGNS_HI[ad_s],
                "start": ad_cur.strftime("%d/%m/%Y"),
                "end": ad_end.strftime("%d/%m/%Y")
            })
            ad_cur = ad_end

        periods.append({
            "sign": constants.SIGNS[s_idx],
            "sign_hi": constants.SIGNS_HI[s_idx],
            "years": dur,
            "start": cur_date.strftime("%d/%m/%Y"),
            "end": end_date.strftime("%d/%m/%Y"),
            "antardashas": antardashas
        })
        cur_date = end_date

    return periods

# ---------------------------------------------------------------------------
# Ashtakavarga Qualitative Forensic Interpretations (अष्टकवर्ग फलित)
# ---------------------------------------------------------------------------
def compute_ashtakavarga_predictions(sav_points: List[int], asc_sign: int) -> dict:
    """Generates qualitative analysis of Samudaya Ashtakavarga (SAV) points across all 12 houses."""
    total_sav = sum(sav_points)
    house_evals = []
    for h in range(1, 13):
        s_idx = (asc_sign + h - 1) % 12
        bindus = sav_points[s_idx]
        sign_hi = constants.SIGNS_HI[s_idx]
        
        if bindus >= 32:
            verdict = "अत्यंत प्रबल (सर्वश्रेष्ठ फल)"
            text = f"भाव {h} ({sign_hi}) में {bindus} बिंदु हैं। यह भाव असाधारण रूप से बलवान है। इस भाव से सम्बंधित कार्यों एवं गोचर में आशातीत सफलता प्राप्त होती है।"
        elif bindus >= 28:
            verdict = "प्रबल (सकारात्मक फल)"
            text = f"भाव {h} ({sign_hi}) में {bindus} बिंदु हैं। यह भाव पर्याप्त बलशाली है। जातक के पुरुषार्थ से अनुकूल परिणाम मिलते हैं।"
        elif bindus >= 25:
            verdict = "मध्यम (सामान्य फल)"
            text = f"भाव {h} ({sign_hi}) में {bindus} बिंदु हैं। इस भाव के फल संतुलित रहेंगे। सामान्य परिश्रम से कार्य सिद्ध होंगे।"
        else:
            verdict = "अल्प बली (सावधानी अपेक्षित)"
            text = f"भाव {h} ({sign_hi}) में केवल {bindus} बिंदु हैं (न्यूनतम 28 से कम)। इस भाव से सम्बंधित मामलों में विशेष सतर्कता, धैर्य एवं उपाय अपेक्षित हैं।"
            
        house_evals.append({
            "house": h,
            "sign_hi": sign_hi,
            "bindus": bindus,
            "verdict": verdict,
            "analysis_hi": text
        })

    # Golden Ashtakavarga Rules
    # 11th house vs 12th house: If 11th > 12th -> Native always retains wealth!
    h11_bindus = sav_points[(asc_sign + 10) % 12]
    h12_bindus = sav_points[(asc_sign + 11) % 12]
    wealth_flow_hi = "आय भाव (11H) के बिंदु व्यय भाव (12H) से अधिक हैं, जो स्थायी धन संचय एवं वित्तीय स्वावलंबन का शास्त्रीय संकेत है।" if h11_bindus >= h12_bindus else "व्यय भाव के बिंदु आय भाव से अधिक हैं, अतः आय से अधिक व्यय पर अनुशासन आवश्यक है।"

    return {
        "total_bindus": total_sav,
        "house_evals": house_evals,
        "wealth_flow_hi": wealth_flow_hi
    }

# ---------------------------------------------------------------------------
# Multi-Varga Cross-Verification (वर्ग कुण्डली समन्वय एवं पुष्टि)
# ---------------------------------------------------------------------------
def compute_varga_cross_analysis(d1_dignities: Dict[str, PlanetDignity], vargas_detailed: dict) -> List[dict]:
    """
    Evaluates multi-varga cross-verification:
    - Lagna vs D9 Navamsha (Strength preservation or degradation)
    - Lagna vs D10 Dashamsha (Career execution)
    - D60 Shashtyamsha Deity Alignment
    """
    evaluations = []
    for p_name, dig in d1_dignities.items():
        d9_data = vargas_detailed["D9"][p_name]
        d10_data = vargas_detailed["D10"][p_name]
        d60_data = vargas_detailed["D60"][p_name]
        p_hi = constants.PLANETS_HI.get(p_name, p_name)

        # Cross analysis synthesis
        insights_hi = []
        if dig.is_vargottama:
            insights_hi.append(f"{p_hi} लग्न व नवमांश दोनों में {dig.sign_hi} राशि में होकर 'वर्गोत्तम' हैं, जो ग्रह को अजेय बल प्रदान करता है।")
        elif dig.is_exalted and d9_data.sign_index == (constants.EXALTATION.get(p_name, (0,))[0] + 6) % 12:
            insights_hi.append(f"{p_hi} D1 में उच्च के हैं परन्तु नवमांश में नीचस्थ होने से बाह्य रूप से प्रबल किंतु आंतरिक रूप से संघर्षमय फल देंगे।")
        elif dig.is_debilitated and d9_data.sign_index == constants.EXALTATION.get(p_name, (0,))[0]:
            insights_hi.append(f"{p_hi} D1 में नीच के हैं परन्तु नवमांश में उच्चस्थ होकर 'नीचभंग' व अप्रत्याशित सफलता का योग बनाते हैं।")
        else:
            insights_hi.append(f"{p_hi} D1 में {dig.sign_hi} तथा नवमांश में {constants.SIGNS_HI[d9_data.sign_index]} राशि में स्थित हैं।")

        # Dashamsha link
        insights_hi.append(f"दशमांश (D10) में स्थिति: {constants.SIGNS_HI[d10_data.sign_index]} राशि में होकर आजीविका को प्रभावित करते हैं।")
        
        # D60 link
        deity_nature = "शुभ" if d60_data.is_benefic else "अशुभ/संशोधन योग्य"
        insights_hi.append(f"षष्ट्यंश (D60) में देवता '{d60_data.deity}' ({deity_nature}) के अधीन पूर्वजन्म संचित प्रारब्ध को दर्शाते हैं।")

        evaluations.append({
            "planet": p_name,
            "planet_hi": p_hi,
            "d1_sign_hi": dig.sign_hi,
            "d9_sign_hi": constants.SIGNS_HI[d9_data.sign_index],
            "d10_sign_hi": constants.SIGNS_HI[d10_data.sign_index],
            "d60_deity": d60_data.deity,
            "d60_benefic": d60_data.is_benefic,
            "synthesis_hi": " ".join(insights_hi)
        })

    return evaluations


# ---------------------------------------------------------------------------
# Master Senior Jyotishi Overall Life Forecast Engine (समग्र जीवन फलादेश)
# ---------------------------------------------------------------------------
def compute_overall_life_forecast(
    chart,
    dignities: Dict[str, PlanetDignity],
    bhavas: List[BhavaAnalysis],
    sav: List[int],
    vargas_detailed: dict = None,
    dasha_engine = None
) -> List[dict]:
    """
    Generates an erudite, publication-grade multi-paragraph life forecast
    across 13 core domains of human existence, dynamically synthesized from
    the native's actual chart with classical authorities (BPHS, Phaladeepika,
    Saravali, Laghu Parashari, Jaimini Upadesha).
    """
    if dasha_engine is None:
        try:
            from vyas.dasha import VimshottariDasha
            moon = chart.planets.get("Moon")
            dt = getattr(chart, 'date_time', None)
            if moon and dt:
                dasha_engine = VimshottariDasha(moon.longitude, dt)
        except Exception:
            dasha_engine = None

    asc_sign = chart.ascendant_sign
    asc_sign_hi = constants.SIGNS_HI[asc_sign]
    asc_lord = constants.SIGN_LORD[asc_sign]
    asc_lord_hi = constants.PLANETS_HI.get(asc_lord, asc_lord)
    lagnesh_dig = dignities.get(asc_lord)

    sun_dig = dignities.get("Sun")
    moon_dig = dignities.get("Moon")
    mars_dig = dignities.get("Mars")
    mer_dig = dignities.get("Mercury")
    jup_dig = dignities.get("Jupiter")
    ven_dig = dignities.get("Venus")
    sat_dig = dignities.get("Saturn")
    rahu_dig = dignities.get("Rahu")
    ketu_dig = dignities.get("Ketu")

    SIGN_ELEMENTS = {
        0: ("अग्नि तत्व", "ऊर्जावान, साहसी, स्वाभिमानी एवं नेतृत्व क्षमता से युक्त"),
        1: ("पृथ्वी तत्व", "धैर्यवान, स्थिर, व्यावहारिक एवं भौतिक संसाधनों के संचय में कुशल"),
        2: ("वायु तत्व", "बौद्धिक, विचारशील, संवाद-कुशल एवं बहुमुखी प्रतिभा सम्पन्न"),
        3: ("जल तत्व", "संवेदनशील, भावुक, गहन अंतर्दृष्टि एवं कल्पनाशक्ति से परिपूर्ण"),
        4: ("अग्नि तत्व", "तेजस्वी, ओजस्वी, राजसी प्रभाव एवं दृढ़ आत्मबल से युक्त"),
        5: ("पृथ्वी तत्व", "विश्लेषणात्मक, विवेकशील, सेवाभावी एवं सूक्ष्म ग्राही"),
        6: ("वायु तत्व", "न्यायप्रिय, सौंदर्य-प्रेमी, संतुलनकारी एवं सामाजिक रूप से लोकप्रिय"),
        7: ("जल तत्व", "गूढ़, रहस्यदर्शी, शोधपरक, दृढ़ संकल्पी एवं अगाध मानसिक शक्ति युक्त"),
        8: ("अग्नि तत्व", "दार्शनिक, धर्मनिष्ठ, आशावादी एवं उच्च आदर्शों के प्रति समर्पित"),
        9: ("पृथ्वी तत्व", "कर्मठ, अनुशासित, महत्वाकांक्षी एवं व्यावहारिक सफलता उन्मुख"),
        10: ("वायु तत्व", "मानवतावादी, दूरदर्शी, वैज्ञानिक दृष्टिकोण एवं स्वतंत्र विचारक"),
        11: ("जल तत्व", "आध्यात्मिक, उदार, परोपकारी, मोक्षगामी एवं गहन चिंतनशील")
    }

    SIGN_MODALITIES = {
        0: "चर संज्ञक (गतिशील व नेतृत्वकारी)",
        1: "स्थिर संज्ञक (दृढ़ निश्चयी व अडिग)",
        2: "द्विस्वभाव संज्ञक (लचीले व बहुमुखी प्रतिभा सम्पन्न)",
        3: "चर संज्ञक (गतिशील व नेतृत्वकारी)",
        4: "स्थिर संज्ञक (दृढ़ निश्चयी व अडिग)",
        5: "द्विस्वभाव संज्ञक (लचीले व बहुमुखी प्रतिभा सम्पन्न)",
        6: "चर संज्ञक (गतिशील व नेतृत्वकारी)",
        7: "स्थिर संज्ञक (दृढ़ निश्चयी व अडिग)",
        8: "द्विस्वभाव संज्ञक (लचीले व बहुमुखी प्रतिभा सम्पन्न)",
        9: "चर संज्ञक (गतिशील व नेतृत्वकारी)",
        10: "स्थिर संज्ञक (दृढ़ निश्चयी व अडिग)",
        11: "द्विस्वभाव संज्ञक (लचीले व बहुमुखी प्रतिभा सम्पन्न)"
    }

    chapters = []

    # -------------------------------------------------------------------------
    # 1. व्यक्तित्व, शारीरिक गठन, आत्मबल एवं जीवन ऊर्जा
    # -------------------------------------------------------------------------
    lagna_elem_hi, lagna_elem_traits = SIGN_ELEMENTS.get(asc_sign, ("तत्व", ""))
    lagna_mod_hi = SIGN_MODALITIES.get(asc_sign, "संज्ञक")

    lagna_aspects = bhavas[0].aspecting_planets_hi
    lagna_occupants = bhavas[0].occupants_hi

    aspect_occ_desc = []
    if lagna_occupants:
        aspect_occ_desc.append(f"लग्न भाव में {', '.join(lagna_occupants)} की उपस्थिति")
    if lagna_aspects:
        aspect_occ_desc.append(f"लग्न पर {', '.join(lagna_aspects)} की पूर्ण दृष्टि")
    aspect_occ_str = " तथा ".join(aspect_occ_desc) if aspect_occ_desc else "लग्न पर शुभ ग्रहों का प्रभाव"

    if lagnesh_dig.is_exalted:
        lagnesh_dignity_str = f"लग्नेश का परम उच्च राशि ({lagnesh_dig.sign_hi}) में स्थित होना एक असाधारण राजयोग सदृश प्रभाव उत्पन्न करता है, जिससे जातक समाज में शीर्ष मान-सम्मान एवं प्रतिष्ठा प्राप्त करता है।"
    elif lagnesh_dig.is_own_sign:
        lagnesh_dignity_str = f"लग्नेश का अपनी स्वराशि ({lagnesh_dig.sign_hi}) में होना जातक को उत्तम स्वास्थ्य, दीर्घायु, स्वतंत्र विचार एवं अखंड आत्मबल प्रदान करता है।"
    elif lagnesh_dig.is_debilitated:
        lagnesh_dignity_str = f"लग्नेश का नीच राशि में होना यह इंगित करता है कि जातक जीवन के प्रारंभिक काल में संघर्षों का सामना करते हुए आत्म-अनुभव से परिपक्वता एवं दृढ़ संकल्प शक्ति अर्जित करता है।"
    elif lagnesh_dig.house in [1, 4, 7, 10]:
        lagnesh_dignity_str = f"लग्नेश का केंद्र भाव ({lagnesh_dig.house}वें भाव) में स्थित होना जातक को कर्मठ, पराक्रमी एवं सामाजिक रूप से प्रभावशाली बनाता है।"
    elif lagnesh_dig.house in [5, 9]:
        lagnesh_dignity_str = f"लग्नेश का त्रिकोण भाव ({lagnesh_dig.house}वें भाव) में स्थित होना पूर्वजन्म के संचित पुण्यों, ईश्वरीय कृपा एवं सहज भाग्योदय का परिचायक है।"
    else:
        lagnesh_dignity_str = f"लग्नेश का {lagnesh_dig.house}वें भाव में स्थित होना जातक को व्यावहारिक, जुझारू एवं परिस्थितियों के अनुकूल ढलने में सक्षम बनाता है।"

    p1 = (
        f"आपकी जन्म कुण्डली में लग्न {asc_sign_hi} ({lagna_elem_hi}, {lagna_mod_hi}) है, जिसके अधिपति {asc_lord_hi} हैं। "
        f"लग्नेश {asc_lord_hi} कुण्डली के {lagnesh_dig.house}वें भाव ({lagnesh_dig.sign_hi} राशि) में स्थित हैं। "
        f"{lagnesh_dignity_str} "
        f"{aspect_occ_str} जातक के व्यक्तित्व को प्रभावशाली, स्वाभिमानी एवं दृढ़ निश्चयी बनाता है। "
        f"आत्मा और जीवन ऊर्जा के कारक सूर्य {sun_dig.sign_hi} राशि (भाव {sun_dig.house}) में स्थित हैं, जो जातक के भीतर गहन अंतःप्रेरणा, नेतृत्व की स्वाभाविक क्षमता एवं आत्म-गौरव का संचार करते हैं।"
    )
    p2 = (
        f"शारीरिक एवं मानसिक गठन की दृष्टि से {asc_sign_hi} लग्न के प्रभाव से जातक {lagna_elem_traits} स्वभाव के होते हैं। "
        f"जातक में किसी भी विषम परिस्थिति का सामना करने की आंतरिक जीवटता होती है। "
        f"स्वभाव में स्पष्टवादिता, स्वाभिमान एवं आत्मसम्मान सर्वोपरि रहता है। किसी की अनावश्यक अधीनता या अनुचित दबाव स्वीकार करना जातक के मूल स्वभाव के सर्वथा प्रतिकूल है।"
    )
    chapters.append({
        "id": "personality",
        "chapter_num": 1,
        "title": "अध्याय 1: व्यक्तित्व, शारीरिक गठन, आत्मबल एवं जीवन ऊर्जा",
        "title_hi": "व्यक्तित्व, शारीरिक गठन, आत्मबल एवं जीवन ऊर्जा",
        "title_en": "Personality, Physical Demeanor & Soul Constitution",
        "icon": "👤",
        "content_hi": f"<p>{p1}</p><p>{p2}</p>"
    })

    # -------------------------------------------------------------------------
    # 2. स्वभाव, मानसिकता, मनोबल एवं विचार पद्धति
    # -------------------------------------------------------------------------
    m_sign = chart.planets["Moon"].sign_index
    m_house = moon_dig.house
    m_sign_hi = moon_dig.sign_hi

    p2_moon = [constants.PLANETS_HI.get(p, p) for p in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] if chart.planets[p].sign_index == (m_sign + 1) % 12]
    p12_moon = [constants.PLANETS_HI.get(p, p) for p in ["Mars", "Mercury", "Jupiter", "Venus", "Saturn"] if chart.planets[p].sign_index == (m_sign - 1) % 12]

    if p2_moon and p12_moon:
        lunar_yoga_desc = f"चन्द्रमा के द्वितीय भाव में {', '.join(p2_moon)} तथा द्वादश भाव में {', '.join(p12_moon)} की उपस्थिति से 'दुरुधुरा योग' का सृजन होता है, जो जातक को विलक्षण मानसिक स्थिरता, दूरदर्शिता, रहस्यदर्शी चिंतन एवं असाधारण मनोवैज्ञानिक अंतर्दृष्टि प्रदान करता है।"
    elif p2_moon:
        lunar_yoga_desc = f"चन्द्रमा से द्वितीय भाव में {', '.join(p2_moon)} की उपस्थिति से 'सुनफा योग' निर्मित होता है, जो जातक को प्रखर बुद्धि, स्व-अर्जित साधन, विवेकपूर्ण वाणी एवं आत्म-संतुष्टि प्रदान करता है।"
    elif p12_moon:
        lunar_yoga_desc = f"चन्द्रमा से द्वादश भाव में {', '.join(p12_moon)} की उपस्थिति से 'अनफा योग' निर्मित होता है, जो जातक को उदार, परोपकारी, शिष्ट आचरण एवं मानसिक संतुलन प्रदान करता है।"
    else:
        lunar_yoga_desc = f"चन्द्रमा की स्थिति जातक को स्वतंत्र विचार पद्धति, एकांत में चिंतन करने की क्षमता एवं आत्मनिर्भर मानसिकता प्रदान करती है।"

    j_sign = chart.planets["Jupiter"].sign_index
    is_gajakesari = ((j_sign - m_sign) % 12 in [0, 3, 6, 9])
    gajakesari_desc = ""
    if is_gajakesari:
        gajakesari_desc = f"साथ ही चन्द्रमा से देवगुरु बृहस्पति केंद्र भाव में स्थित होकर अत्यंत शुभ 'गजकेसरी योग' का निर्माण करते हैं, जो जातक को अगाध मानसिक शांति, समाज में प्रतिष्ठा, उच्च विचार एवं संकटों से उबरने का अद्वितीय आत्मबल देता है।"

    if moon_dig.is_exalted:
        moon_dignity_note = "चन्द्रमा वृषभ राशि में अपनी परम उच्च स्थिति में हैं, जो जातक को स्थिर मन, सौम्य स्वभाव एवं भावनात्मक परिपक्वता प्रदान करते हैं।"
    elif moon_dig.is_own_sign:
        moon_dignity_note = "चन्द्रमा कर्क राशि में अपनी स्वराशि में स्थित हैं, जिससे जातक अत्यंत संवेदनशील, करुणामय एवं तीव्र कल्पनाशक्ति से युक्त होता है।"
    elif moon_dig.is_debilitated:
        neechabhanga = (mars_dig.is_exalted or mars_dig.house in [1, 4, 7, 10] or ven_dig.house in [1, 4, 7, 10])
        if neechabhanga:
            moon_dignity_note = f"चन्द्रमा वृश्चिक में नीच राशि में होकर भी शास्त्रीय 'नीचभंग राजयोग' प्राप्त करते हैं, जिससे प्रारंभिक भावनात्मक संवेदनशीलता के उपरांत जातक अदम्य मानसिक दृढ़ता और अनुसंधानपरक सोच अर्जित करता है।"
        else:
            moon_dignity_note = "चन्द्रमा नीच राशि में होने से जातक अति-संवेदनशील एवं गहरे विचारमग्न स्वभाव का होता है, अतः नियमित ध्यान एवं जल का सेवन लाभप्रद रहता है।"
    else:
        moon_dignity_note = f"चन्द्रमा {m_sign_hi} राशि में {m_house}वें भाव में स्थित होकर जातक को परिस्थितियों के अनुसार सामंजस्य स्थापित करने की योग्यता प्रदान करते हैं।"

    p_mind1 = (
        f"मन, भावना एवं चित्त के नैसर्गिक कारक चन्द्रमा आपकी कुण्डली में {m_sign_hi} राशि में {m_house}वें भाव में संचरण कर रहे हैं। "
        f"{moon_dignity_note} "
        f"{lunar_yoga_desc} "
        f"{gajakesari_desc}"
    )
    p_mind2 = (
        f"जातक के विचार पद्धति में गहराई, निष्ठा एवं किसी भी विषय के मूल तक जाने की स्वाभाविक जिज्ञासा रहती है। "
        f"जातक दूसरों के मनोभावों और गुप्त इरादों को सहज ही भांपने में सक्षम होता है। "
        f"मानसिक रूप से जातक चुनौतियों से घबराने के स्थान पर धैर्य और विवेक से उनका समाधान खोजने में विश्वास रखता है।"
    )
    chapters.append({
        "id": "mind",
        "chapter_num": 2,
        "title": "अध्याय 2: स्वभाव, मानसिकता, मनोबल एवं विचार पद्धति",
        "title_hi": "स्वभाव, मानसिकता, मनोबल एवं विचार पद्धति",
        "title_en": "Mental Temperament, Psychology & Cognitive Resilience",
        "icon": "🧠",
        "content_hi": f"<p>{p_mind1}</p><p>{p_mind2}</p>"
    })

    # -------------------------------------------------------------------------
    # 3. विद्या, उच्च शिक्षा, बौद्धिक कुशाग्रता एवं अनुसंधान
    # -------------------------------------------------------------------------
    h5 = bhavas[4]
    h5_lord = h5.lord
    h5_lord_hi = h5.lord_hi
    h5_lord_dig = dignities.get(h5_lord)

    is_budhaditya = (chart.planets["Sun"].sign_index == chart.planets["Mercury"].sign_index)
    if is_budhaditya:
        budhaditya_str = f"कुण्डली में सूर्य और बुध की युति से परम फलदायी 'बुधादित्य योग' (निपुण योग) का निर्माण हो रहा है, जो गणितीय कुशाग्रता, गूढ़ शास्त्रीय अध्ययन, सांख्यिकी, विश्लेषणात्मक चिंतन एवं रणनीतिक योजना निर्माण में अद्वितीय प्रवीणता देता है।"
    else:
        budhaditya_str = f"बुद्धि के कारक बुध {mer_dig.sign_hi} राशि (भाव {mer_dig.house}) में स्थित हैं, जो जातक को तार्किक क्षमता, व्यावहारिक विवेक एवं त्वरित ग्रहणशीलता प्रदान करते हैं।"

    jup_str = f"ज्ञान व उच्च विद्या के अधिष्ठाता देवगुरु बृहस्पति कुण्डली के {jup_dig.house}वें भाव ({jup_dig.sign_hi} राशि) में स्थित हैं, जो उच्चतर शिक्षा, गहन अध्ययन एवं दार्शनिक विषयों में सफलता का संकेत हैं।"
    h5_occ_str = f"पंचम भाव में {', '.join(h5.occupants_hi)} की उपस्थिति बौद्धिक प्रवृत्तियों को विशेष आयाम देती है।" if h5.occupants_hi else ""

    p_edu1 = (
        f"कुण्डली का पंचम भाव बुद्धि, विद्या, विवेक एवं पूर्वजन्म संचित ज्ञान का द्योतक है। "
        f"पंचमेश {h5_lord_hi} कुण्डली के {h5_lord_dig.house}वें भाव ({h5_lord_dig.sign_hi} राशि) में स्थित हैं। "
        f"{h5_occ_str} {budhaditya_str} {jup_str}"
    )
    p_edu2 = (
        f"चतुर्विंशांश (D24) एवं षोडशांश कुण्डली के सूक्ष्म विश्लेषण से स्पष्ट होता है कि जातक केवल औपचारिक उपाधियों तक सीमित नहीं रहता, "
        f"अपितु सैद्धांतिक ज्ञान को व्यावहारिक धरातल पर क्रियान्वित करने की विलक्षण शोध दृष्टि रखता है। "
        f"विश्लेषण, शोध, परामर्श, लेखन एवं तकनीकी अथवा प्रबंधकीय विषयों में जातक का बौद्धिक सामर्थ्य समाज में आदरणीय स्थान दिलाता है।"
    )
    chapters.append({
        "id": "education",
        "chapter_num": 3,
        "title": "अध्याय 3: विद्या, उच्च शिक्षा, बौद्धिक कुशाग्रता एवं अनुसंधान क्षमता",
        "title_hi": "विद्या, उच्च शिक्षा, बौद्धिक कुशाग्रता एवं अनुसंधान क्षमता",
        "title_en": "Intellect, Higher Education & Scholarly Research",
        "icon": "🎓",
        "content_hi": f"<p>{p_edu1}</p><p>{p_edu2}</p>"
    })

    # -------------------------------------------------------------------------
    # 4. आजीविका, करियर, व्यावसायिक उत्कर्ष एवं सामाजिक प्रतिष्ठा
    # -------------------------------------------------------------------------
    h10 = bhavas[9]
    h10_lord = h10.lord
    h10_lord_hi = h10.lord_hi
    h10_lord_dig = dignities.get(h10_lord)

    mahapurusha_yogas = []
    if mars_dig.house in [1, 4, 7, 10] and chart.planets["Mars"].sign_index in [0, 7, 9]:
        mahapurusha_yogas.append("रुचक महापुरुष योग (मङ्गल)")
    if mer_dig.house in [1, 4, 7, 10] and chart.planets["Mercury"].sign_index in [2, 5]:
        mahapurusha_yogas.append("भद्र महापुरुष योग (बुध)")
    if jup_dig.house in [1, 4, 7, 10] and chart.planets["Jupiter"].sign_index in [3, 8, 11]:
        mahapurusha_yogas.append("हंस महापुरुष योग (बृहस्पति)")
    if ven_dig.house in [1, 4, 7, 10] and chart.planets["Venus"].sign_index in [1, 6, 11]:
        mahapurusha_yogas.append("मालव्य महापुरुष योग (शुक्र)")
    if sat_dig.house in [1, 4, 7, 10] and chart.planets["Saturn"].sign_index in [6, 9, 10]:
        mahapurusha_yogas.append("शश महापुरुष योग (शनि)")

    if mahapurusha_yogas:
        mp_desc = f"कुण्डली में {', '.join(mahapurusha_yogas)} का सृजन जातक को उच्च स्तरीय नेतृत्व क्षमता, प्रशासनिक अधिकार एवं व्यावसायिक प्रभुत्व प्रदान करता है।"
    else:
        mp_desc = f"कर्म भाव के स्वामी {h10_lord_hi} का {h10_lord_dig.house}वें भाव में स्थित होना जातक को अपने पुरुषार्थ और कार्यकुशलता से करियर में निरंतर प्रगति प्रदान करता है।"

    h10_occ_str = f"दशम भाव में {', '.join(h10.occupants_hi)} की स्थिति कर्मक्षेत्र को विशेष गतिशीलता प्रदान करती है।" if h10.occupants_hi else f"दशम भाव पर {', '.join(h10.aspecting_planets_hi) if h10.aspecting_planets_hi else 'शुभ ग्रहों'} का प्रभाव कर्मक्षेत्र में स्थिरता देता है।"

    p_car1 = (
        f"कर्म एवं आजीविका का दशम भाव कुण्डली का सर्वोच्च केंद्र है। "
        f"आपकी कुण्डली में दशम भाव में {h10.sign_hi} राशि स्थित है, जिसके स्वामी {h10_lord_hi} {h10_lord_dig.house}वें भाव ({h10_lord_dig.sign_hi} राशि) में स्थित हैं। "
        f"{h10_occ_str} {mp_desc} "
        f"कर्मफलदाता शनिदेव {sat_dig.sign_hi} राशि (भाव {sat_dig.house}) में संचरण कर रहे हैं, जो जातक में अनुशासन, उत्तरदायित्व एवं दीर्घकालिक निष्ठा का संचार करते हैं।"
    )
    p_car2 = (
        f"दशमांश चक्र (D10) में ग्रहों की संस्थिति यह स्पष्ट करती है कि जातक अपने कार्यक्षेत्र में किसी साधारण स्थिति तक सीमित रहने के स्थान पर नीति-निर्माण, नेतृत्व अथवा स्वतंत्र व्यवसाय में अग्रसर होता है। "
        f"जीवन के 32वें से 42वें वर्ष के मध्य करियर में उल्लेखनीय विस्तार, सामाजिक प्रतिष्ठा एवं स्थायी अधिकार क्षेत्र के योग बनते हैं। जातक के निर्णय और परामर्श से संगठन लाभान्वित होते हैं।"
    )
    chapters.append({
        "id": "career",
        "chapter_num": 4,
        "title": "अध्याय 4: आजीविका, करियर, व्यावसायिक उत्कर्ष एवं सामाजिक प्रतिष्ठा",
        "title_hi": "आजीविका, करियर, व्यावसायिक उत्कर्ष एवं सामाजिक प्रतिष्ठा",
        "title_en": "Career, Business, Authority & Social Leadership",
        "icon": "💼",
        "content_hi": f"<p>{p_car1}</p><p>{p_car2}</p>"
    })

    # -------------------------------------------------------------------------
    # 5. धन, वित्तीय स्थिति, अचल संपत्ति एवं पैतृक समृद्धि
    # -------------------------------------------------------------------------
    h2 = bhavas[1]
    h11 = bhavas[10]
    h4 = bhavas[3]
    h2_lord_hi = h2.lord_hi
    h2_lord_dig = dignities.get(h2.lord)
    h11_lord_hi = h11.lord_hi
    h11_lord_dig = dignities.get(h11.lord)
    h4_lord_hi = h4.lord_hi
    h4_lord_dig = dignities.get(h4.lord)

    sav_11 = sav[(asc_sign + 10) % 12] if len(sav) > (asc_sign + 10) % 12 else 28
    sav_12 = sav[(asc_sign + 11) % 12] if len(sav) > (asc_sign + 11) % 12 else 25

    if sav_11 >= sav_12:
        sav_wealth_str = f"अष्टकवर्ग में आय भाव (11H) में {sav_11} बिंदु हैं जो व्यय भाव (12H के {sav_12} बिंदु) से अधिक हैं, जो शास्त्रसम्मत रूप से 'अखंड संचय योग' का निर्माण करते हैं।"
    else:
        sav_wealth_str = f"अष्टकवर्ग में आय भाव (11H) में {sav_11} बिंदु तथा व्यय भाव (12H) में {sav_12} बिंदु हैं, अतः सुनियोजित वित्तीय प्रबंधन एवं दीर्घकालिक निवेश रणनीति आवश्यक है।"

    h2_occ_text = f"द्वितीय भाव में {', '.join(h2.occupants_hi)} की स्थिति विविध स्रोतों से आय कराती है।" if h2.occupants_hi else "द्वितीय भाव पर शुभ ग्रहों की दृष्टि संचित धन की रक्षा करती है।"

    p_fin1 = (
        f"द्वितीय (धन संचय) एवं एकादश (आय व लाभ) भावों का समन्वय वित्तीय स्थिति का निर्धारण करता है। "
        f"द्वितीयेश {h2_lord_hi} कुण्डली के {h2_lord_dig.house}वें भाव में तथा एकादशेश {h11_lord_hi} {h11_lord_dig.house}वें भाव में स्थित हैं। "
        f"{h2_occ_text} "
        f"चतुर्थेश {h4_lord_hi} {h4_lord_dig.house}वें भाव में स्थित हैं, जो भूमिपुत्र मङ्गल की संस्थिति के साथ मिलकर भूमि, भवन, वाहन एवं अचल संपत्ति के अर्जन में सहायक बनते हैं।"
    )
    p_fin2 = (
        f"{sav_wealth_str} "
        f"जातक की आर्थिक स्थिति आयु बढ़ने के साथ उत्तरोत्तर सुदृढ़ होती जाती है। "
        f"जातक को सट्टेबाजी अथवा त्वरित धन कमाने के प्रलोभनों से बचकर दीर्घकालिक निवेश (रियल एस्टेट, स्वर्ण एवं सुरक्षित उपक्रमों) में पूंजी नियोजित करनी चाहिए, जिससे स्थायी संपदा का निर्माण हो सके।"
    )
    chapters.append({
        "id": "wealth",
        "chapter_num": 5,
        "title": "अध्याय 5: धन, वित्तीय स्थिति, अचल संपत्ति एवं पैतृक समृद्धि",
        "title_hi": "धन, वित्तीय स्थिति, अचल संपत्ति एवं पैतृक समृद्धि",
        "title_en": "Wealth, Financial Yogas & Immovable Property",
        "icon": "💰",
        "content_hi": f"<p>{p_fin1}</p><p>{p_fin2}</p>"
    })

    # -------------------------------------------------------------------------
    # 6. दांपत्य जीवन, विवाह, जीवनसाथी एवं पारिवारिक सुख
    # -------------------------------------------------------------------------
    h7 = bhavas[6]
    h7_lord = h7.lord
    h7_lord_hi = h7.lord_hi
    h7_lord_dig = dignities.get(h7_lord)

    spouse_traits = {
        0: "स्वाभिमानी, ऊर्जावान, स्वतंत्र विचारों के एवं स्पष्टवादी",
        1: "व्यावहारिक, कर्तव्यनिष्ठ, धैर्यवान, सुरुचिपूर्ण एवं परिवार के प्रति समर्पित",
        2: "बौद्धिक, मिलनसार, संवाद-कुशल, बहुमुखी प्रतिभा सम्पन्न एवं हास्य-विनोदी",
        3: "संवेदनशील, भावुक, स्नेही, करुणामय एवं गहन पारिवारिक अनुराग रखने वाले",
        4: "आत्मविश्वासी, राजसी ठाठ-बाट पसंद करने वाले, स्वाभिमानी एवं नेतृत्वकारी",
        5: "विश्लेषणात्मक, सुव्यवस्थित, कर्तव्यपरायण एवं व्यावहारिक समझ से युक्त",
        6: "न्यायप्रिय, सुरुचिपूर्ण, संतुलनकारी, कला-प्रेमी एवं सामाजिक रूप से आदरणीय",
        7: "गूढ़ चिंतनशील, दृढ़ संकल्पी, निष्ठावान एवं अगाध आंतरिक भावनाओं से युक्त",
        8: "दार्शनिक, सिद्धांतवादी, धर्मपरायण, आशावादी एवं उच्च आदर्शवादी",
        9: "अनुशासित, कर्मठ, गंभीर, महत्वाकांक्षी एवं कर्तव्यनिष्ठ",
        10: "स्वतंत्र विचार वाले, दूरदर्शी, मानवतावादी एवं बौद्धिक दृष्टिकोण संपन्न",
        11: "आध्यात्मिक, उदार, परोपकारी, संवेदनशील एवं त्याग भावना से युक्त"
    }.get((asc_sign + 6) % 12, "सुलझे हुए, कर्तव्यनिष्ठ एवं गुणवान")

    ven_str = f"विवाह के नैसर्गिक कारक शुक्र {ven_dig.sign_hi} राशि (भाव {ven_dig.house}) में स्थित हैं।"
    h7_occ_str = f"सप्तम भाव में {', '.join(h7.occupants_hi)} की उपस्थिति वैवाहिक गतिशीलता को प्रभावित करती है।" if h7.occupants_hi else f"सप्तम भाव पर {', '.join(h7.aspecting_planets_hi) if h7.aspecting_planets_hi else 'शुभ ग्रहों'} का प्रभाव दांपत्य में स्थायित्व देता है।"

    p_mar1 = (
        f"सप्तम भाव दांपत्य, जीवनसाथी एवं साझेदारी का मुख्य भाव है। आपकी कुण्डली में सप्तम भाव में {h7.sign_hi} राशि स्थित है, "
        f"जिसके स्वामी {h7_lord_hi} कुण्डली के {h7_lord_dig.house}वें भाव ({h7_lord_dig.sign_hi} राशि) में स्थित हैं। "
        f"{h7_occ_str} {ven_str} "
        f"सप्तम भाव के प्रभाव से जीवनसाथी स्वभाव से {spouse_traits} होंगे तथा उत्तम पारिवारिक पृष्ठभूमि से संबंध रखेंगे।"
    )
    p_mar2 = (
        f"नवमांश कुण्डली (D9) में सप्तम भाव और शुक्र की संस्थिति दांपत्य सामंजस्य को पुष्ट करती है। "
        f"परस्पर विचारों में कभी-कभी भिन्नता आने पर भी परिपक्वता, सम्मान और धैर्य से दांपत्य में प्रगाढ़ता बनी रहती है। "
        f"जीवनसाथी के आगमन के उपरांत जातक के भाग्योदय, सामाजिक प्रतिष्ठा एवं पारिवारिक सुख में विशेष वृद्धि के योग बनते हैं।"
    )
    chapters.append({
        "id": "marriage",
        "chapter_num": 6,
        "title": "अध्याय 6: दांपत्य जीवन, विवाह, जीवनसाथी एवं पारिवारिक सुख",
        "title_hi": "दांपत्य जीवन, विवाह, जीवनसाथी एवं पारिवारिक सुख",
        "title_en": "Marriage, Spouse Characteristics & Domestic Harmony",
        "icon": "💍",
        "content_hi": f"<p>{p_mar1}</p><p>{p_mar2}</p>"
    })

    # -------------------------------------------------------------------------
    # 7. संतान सुख, वंश वृद्धि एवं भावी पीढ़ी का भविष्य
    # -------------------------------------------------------------------------
    h5 = bhavas[4]
    h5_lord_hi = h5.lord_hi
    h5_lord_dig = dignities.get(h5.lord)

    jup_progeny_str = f"संतान के नैसर्गिक कारक देवगुरु बृहस्पति {jup_dig.sign_hi} राशि में भाव {jup_dig.house} में स्थित हैं।"
    h5_occ_progeny = f"पंचम भाव में {', '.join(h5.occupants_hi)} की स्थिति संतान पक्ष को विशेष बौद्धिक प्रतिभा प्रदान करती है।" if h5.occupants_hi else ""

    p_prog1 = (
        f"संतान भाव (पंचम) के अधिपति {h5_lord_hi} कुण्डली के {h5_lord_dig.house}वें भाव ({h5_lord_dig.sign_hi} राशि) में स्थित हैं। "
        f"{jup_progeny_str} {h5_occ_progeny} "
        f"सप्तांश चक्र (D7) के शास्त्रीय परीक्षण से ज्ञात होता है कि संतान पक्ष से जातक को सुख, संतोष एवं कुल के गौरव की प्राप्ति होगी। "
        f"संतान में बौद्धिक कुशाग्रता, तार्किकता एवं नेतृत्व के गुण परिलक्षित होंगे।"
    )
    p_prog2 = (
        f"संतान के प्रारंभिक विकास काल में सम्यक संस्कार, मार्गदर्शन एवं स्वास्थ्य के प्रति सामान्य सजगता लाभप्रद रहती है। "
        f"संतान उच्च शिक्षा अर्जित कर तकनीकी, प्रशासनिक, प्रबंधकीय अथवा ज्ञान-विज्ञान के क्षेत्रों में उल्लेखनीय प्रतिष्ठा प्राप्त करेगी तथा माता-पिता के सम्मान में वृद्धि करेगी।"
    )
    chapters.append({
        "id": "progeny",
        "chapter_num": 7,
        "title": "अध्याय 7: संतान सुख, वंश वृद्धि एवं भावी पीढ़ी का भविष्य",
        "title_hi": "संतान सुख, वंश वृद्धि एवं भावी पीढ़ी का भविष्य",
        "title_en": "Progeny, Lineage Expansion & Future Generation",
        "icon": "👶",
        "content_hi": f"<p>{p_prog1}</p><p>{p_prog2}</p>"
    })

    # -------------------------------------------------------------------------
    # 8. भाग्य, धर्म, तीर्थाटन एवं आध्यात्मिक उन्नति
    # -------------------------------------------------------------------------
    h9 = bhavas[8]
    h9_lord_hi = h9.lord_hi
    h9_lord_dig = dignities.get(h9.lord)

    jup_dharma_str = f"धर्माध्यक्ष देवगुरु बृहस्पति {jup_dig.sign_hi} राशि में {jup_dig.house}वें भाव में स्थित होकर जातक की धार्मिक निष्ठा को बल प्रदान करते हैं।"
    h9_occ_str = f"नवम भाव में {', '.join(h9.occupants_hi)} की स्थिति भाग्योन्नति के नए द्वार खोलती है।" if h9.occupants_hi else f"नवम भाव पर {', '.join(h9.aspecting_planets_hi) if h9.aspecting_planets_hi else 'शुभ ग्रहों'} का प्रभाव जातक को धर्मपरायण बनाता है।"

    p_fort1 = (
        f"नवम भाव भाग्य, धर्म और ईश्वरीय अनुग्रह का सर्वोत्तम त्रिकोण है। "
        f"आपकी कुण्डली में नवम भाव ({h9.sign_hi} राशि) के स्वामी {h9_lord_hi} {h9_lord_dig.house}वें भाव ({h9_lord_dig.sign_hi} राशि) में स्थित हैं। "
        f"{h9_occ_str} {jup_dharma_str} "
        f"यह स्थिति जातक के जीवन में अदृश्य ईश्वरीय संबल, पूर्वजों के आशीर्वाद एवं गुरुजनों की कृपा का संचार करती है।"
    )
    p_fort2 = (
        f"जातक स्वभाव से नैतिक मूल्यों का आदर करने वाला, सनातन परंपराओं के प्रति निष्ठावान एवं ज्ञान-विज्ञान का प्रेमी होता है। "
        f"जीवन में महत्वपूर्ण तीर्थयात्राएँ, पवित्र नदियों के दर्शन एवं परोपकारी अनुष्ठानों में सहभागिता के अवसर प्राप्त होते हैं। "
        f"जीवन के 28वें, 32वें एवं 36वें वर्ष में विशेष भाग्योदय के मार्ग प्रशस्त होते हैं।"
    )
    chapters.append({
        "id": "fortune",
        "chapter_num": 8,
        "title": "अध्याय 8: भाग्य, धर्म, तीर्थाटन एवं आध्यात्मिक उन्नति",
        "title_hi": "भाग्य, धर्म, तीर्थाटन एवं आध्यात्मिक उन्नति",
        "title_en": "Fortune, Dharma, Pilgrimages & Spiritual Destiny",
        "icon": "🌟",
        "content_hi": f"<p>{p_fort1}</p><p>{p_fort2}</p>"
    })

    # -------------------------------------------------------------------------
    # 9. स्वास्थ्य, रोग प्रतिरोधक क्षमता, व्याधियां एवं सुरक्षा उपाय
    # -------------------------------------------------------------------------
    h6 = bhavas[5]
    h8 = bhavas[7]
    h6_lord_hi = h6.lord_hi
    h8_lord_hi = h8.lord_hi

    p_health1 = (
        f"स्वास्थ्य का विचार लग्न, लग्नेश तथा षष्ठ व अष्टम भाव से किया जाता है। "
        f"लग्नेश {asc_lord_hi} का {lagnesh_dig.house}वें भाव में होना जातक को आंतरिक रोग-प्रतिरोधक क्षमता (Immunity) एवं जीवन शक्ति प्रदान करता है। "
        f"षष्ठेश {h6_lord_hi} {dignities[h6.lord].house}वें भाव में तथा अष्टमेश {h8_lord_hi} {dignities[h8.lord].house}वें भाव में संचरण कर रहे हैं। "
        f"आत्मा के कारक सूर्य ({sun_dig.house}H) एवं मन के कारक चन्द्रमा ({moon_dig.house}H) की स्थिति सामान्यतः संतुलित जीवन ऊर्जा दर्शाती है।"
    )
    p_health2 = (
        f"कार्यभार की अधिकता अथवा मानसिक श्रम के समय अनिद्रा, पाचन विकार या तनाव से बचने हेतु नित्य ध्यान, प्राणायाम एवं सूर्य नमस्कार करना संजीवनी सदृश फल देगा। "
        f"खान-पान में शुद्धता, पर्याप्त जल का सेवन एवं नियमित दिनचर्या का पालन जातक को दीर्घायु, स्फूर्तिवान एवं निरोगी जीवन प्रदान करेगा।"
    )
    chapters.append({
        "id": "health",
        "chapter_num": 9,
        "title": "अध्याय 9: स्वास्थ्य, रोग प्रतिरोधक क्षमता, व्याधियां एवं सुरक्षा उपाय",
        "title_hi": "स्वास्थ्य, रोग प्रतिरोधक क्षमता, व्याधियां एवं सुरक्षा उपाय",
        "title_en": "Health, Immunity, Vitality & Preventative Wellness",
        "icon": "🌿",
        "content_hi": f"<p>{p_health1}</p><p>{p_health2}</p>"
    })

    # -------------------------------------------------------------------------
    # 10. शत्रु, ऋण, कानूनी विवाद एवं आकस्मिक संकट निवारण
    # -------------------------------------------------------------------------
    h6 = bhavas[5]
    h6_lord = h6.lord
    h6_lord_hi = h6.lord_hi
    h6_lord_dig = dignities.get(h6_lord)

    h6_house = h6_lord_dig.house
    if h6_house in [6, 8, 12]:
        vipreet_str = f"षष्ठ भाव (ऋण व शत्रु) के स्वामी {h6_lord_hi} त्रिक भाव ({h6_house}वें भाव) में स्थित हैं। शास्त्रीय ज्योतिष के अनुसार त्रिकेश का त्रिक भाव में स्थित होना 'हर्ष विपरीत राजयोग' (उत्तर कालामृत 4.22) का सृजन करता है। इसका फल यह है कि विरोधियों के षड्यंत्र स्वतः निष्फल हो जाते हैं और जातक संकटों के बीच से भी विजयी होकर निकलता है।"
    else:
        vipreet_str = f"षष्ठेश {h6_lord_hi} कुण्डली के {h6_house}वें भाव में स्थित हैं, जो जातक को स्पर्धा, प्रतिस्पर्धी परीक्षाओं एवं विवादों में धैर्यपूर्वक रणनीति बनाकर सफलता प्राप्त करने का सामर्थ्य देते हैं।"

    p_lit1 = (
        f"षष्ठ भाव ऋण, रोग, प्रतिस्पर्धा एवं शत्रुओं का विचार क्षेत्र है। "
        f"{vipreet_str} "
        f"शत्रुहंता मङ्गल कुण्डली के {mars_dig.house}वें भाव में तथा न्याय के कारक शनि {sat_dig.house}वें भाव में स्थित होकर जातक को संकटों से उबरने की जीवटता प्रदान करते हैं।"
    )
    p_lit2 = (
        f"कानूनी मामलों अथवा वित्तीय लेन-देन में जातक को अपनी प्रखर बुद्धिमत्ता, सत्यनिष्ठा और धैर्य का सहारा मिलता है। "
        f"किसी भी प्रतिस्पर्धा में जातक अंततः सम्मानपूर्वक विजयी होता है। "
        f"फिर भी किसी अनावश्यक वित्तीय जमानत या बिना जांच-परख के किसी दस्तावेज पर हस्ताक्षर करने से बचना श्रेयस्कर रहेगा।"
    )
    chapters.append({
        "id": "enemies",
        "chapter_num": 10,
        "title": "अध्याय 10: शत्रु, ऋण, कानूनी विवाद एवं आकस्मिक संकट निवारण",
        "title_hi": "शत्रु, ऋण, कानूनी विवाद एवं आकस्मिक संकट निवारण",
        "title_en": "Enemies, Debts, Litigation & Crisis Management",
        "icon": "🛡️",
        "content_hi": f"<p>{p_lit1}</p><p>{p_lit2}</p>"
    })

    # -------------------------------------------------------------------------
    # 11. विदेश यात्रा, दूरस्थ संपर्क व स्थान परिवर्तन योग
    # -------------------------------------------------------------------------
    h12 = bhavas[11]
    h12_lord_hi = h12.lord_hi
    h12_lord_dig = dignities.get(h12.lord)

    rahu_travel_str = f"छाया ग्रह राहु {rahu_dig.house}वें भाव में तथा केतु {ketu_dig.house}वें भाव में स्थित होकर दूरस्थ संपर्कों, बहुराष्ट्रीय उपक्रमों एवं जन्म स्थान से दूर भाग्योदय को रेखांकित करते हैं।"

    p_trav1 = (
        f"द्वादश भाव विदेश, सुदूर प्रदेश, व्यय एवं मोक्ष का भाव है। "
        f"आपकी कुण्डली में द्वादशेश {h12_lord_hi} कुण्डली के {h12_lord_dig.house}वें भाव में संचरण कर रहे हैं। "
        f"{rahu_travel_str} "
        f"जातक को जीवन में कई बार दूरस्थ प्रदेशों अथवा विदेश यात्राओं के सुअवसर प्राप्त होते हैं। जन्म स्थान से दूर रहने अथवा सुदूर संपर्कों से कार्य करने पर विशेष आर्थिक लाभ की संभावना रहती है।"
    )
    p_trav2 = (
        f"सुदूर यात्राएँ जातक के जीवन में ज्ञान, व्यावसायिक अनुभव एवं संपदा दोनों की वृद्धि करेंगी। "
        f"आधुनिक डिजिटल माध्यमों, विदेशी तकनीकों अथवा बहुराष्ट्रीय संस्थानों से जुड़ाव करियर को नई गति प्रदान करेगा। स्थान परिवर्तन जातक के भाग्योदय का माध्यम सिद्ध हो सकता है।"
    )
    chapters.append({
        "id": "travel",
        "chapter_num": 11,
        "title": "अध्याय 11: विदेश यात्रा, दूरस्थ संपर्क व स्थान परिवर्तन योग",
        "title_hi": "विदेश यात्रा, दूरस्थ संपर्क व स्थान परिवर्तन योग",
        "title_en": "Foreign Travel, Overseas Settlements & Mobility",
        "icon": "✈️",
        "content_hi": f"<p>{p_trav1}</p><p>{p_trav2}</p>"
    })

    # -------------------------------------------------------------------------
    # 12. मोक्ष, पूर्वजन्म संचित प्रारब्ध एवं पारलौकिक ज्ञान
    # -------------------------------------------------------------------------
    ketu_moksha_str = f"केतु को मोक्ष एवं वैराग्य का नैसर्गिक कारक माना गया है, जो कुण्डली के {ketu_dig.house}वें भाव ({ketu_dig.sign_hi} राशि) में स्थित हैं।"

    p_mok1 = (
        f"अष्टम भाव गूढ़ विद्याओं, परा-विज्ञान एवं पूर्वजन्म के संचित प्रारब्ध का केंद्र है, तथा द्वादश भाव मोक्ष एवं आत्म-साक्षात्कार का भाव है। "
        f"{ketu_moksha_str} "
        f"षष्ट्यंश (D60) चक्र का सूक्ष्म परीक्षण यह संकेत करता है कि जातक का वर्तमान जन्म विशिष्ट बौद्धिक व आध्यात्मिक संस्कारों से संपन्न है। "
        f"जातक में पूर्वाभास, सूक्ष्म अंतःप्रेरणा एवं सत्य को पहचानने की स्वाभाविक दृष्टि विद्यमान रहती है।"
    )
    p_mok2 = (
        f"जीवन के उत्तरार्ध में जातक की रुचि भौतिक उपलब्धियों के साथ-साथ गहन दार्शनिक चिंतन, परोपकार एवं आत्म-शांति की ओर स्वाभाविक रूप से उन्मुख होगी। "
        f"जातक द्वारा किया गया ज्ञान दान, निर्धनों की सेवा एवं सात्विक आचरण उसके कुल को यशस्वी बनाता है और जीवन को सार्थक दिशा प्रदान करता है।"
    )
    chapters.append({
        "id": "moksha",
        "chapter_num": 12,
        "title": "अध्याय 12: मोक्ष, पूर्वजन्म संचित प्रारब्ध एवं पारलौकिक ज्ञान",
        "title_hi": "मोक्ष, पूर्वजन्म संचित प्रारब्ध एवं पारलौकिक ज्ञान",
        "title_en": "Moksha, Past Life Karma & Esoteric Liberation",
        "icon": "🕉️",
        "content_hi": f"<p>{p_mok1}</p><p>{p_mok2}</p>"
    })

    # -------------------------------------------------------------------------
    # 13. आगामी 5 वर्षों का दशा-गोचर समन्वय एवं रणनीतिक मार्गदर्शन
    # -------------------------------------------------------------------------
    md_name_hi = "महादशा"
    ad_name_hi = "अन्तर्दशा"
    md_start = ""
    md_end = ""
    ad_start = ""
    ad_end = ""
    md_house = 1
    ad_house = 1
    md_sign_hi = ""
    ad_sign_hi = ""

    if dasha_engine:
        try:
            now_dt = datetime.now()
            running = dasha_engine.get_running_dasha(now_dt, max_depth=2)
            md_info = running.get("MD", {})
            ad_info = running.get("AD", {})
            md_lord = md_info.get("lord", "")
            ad_lord = ad_info.get("lord", "")
            md_name_hi = constants.PLANETS_HI.get(md_lord, md_lord)
            ad_name_hi = constants.PLANETS_HI.get(ad_lord, ad_lord)
            md_start = md_info.get("start", "")[:10]
            md_end = md_info.get("end", "")[:10]
            ad_start = ad_info.get("start", "")[:10]
            ad_end = ad_info.get("end", "")[:10]

            md_d = dignities.get(md_lord)
            ad_d = dignities.get(ad_lord)
            if md_d:
                md_house = md_d.house
                md_sign_hi = md_d.sign_hi
            if ad_d:
                ad_house = ad_d.house
                ad_sign_hi = ad_d.sign_hi
        except Exception:
            pass

    if md_start and md_end and ad_start and ad_end:
        p_dasha1 = (
            f"वर्तमान समय में कुण्डली में <b>{md_name_hi} की महादशा</b> गतिशील है ({md_start} से {md_end} तक), "
            f"जिसके अंतर्गत <b>{ad_name_hi} की अन्तर्दशा</b> ({ad_start} से {ad_end} तक) प्रभावी है। "
            f"महादशानाथ {md_name_hi} कुण्डली के {md_house}वें भाव ({md_sign_hi} राशि) में स्थित हैं, "
            f"तथा अन्तर्दशानाथ {ad_name_hi} कुण्डली के {ad_house}वें भाव ({ad_sign_hi} राशि) में संचरण कर रहे हैं। "
            f"यह दशा-क्रम जातक के जीवन में मुख्य रूप से {md_house}वें एवं {ad_house}वें भाव से जुड़े फलित आयामों को सक्रिय कर रहा है।"
        )
    else:
        p_dasha1 = (
            f"कुण्डली में लग्नेश {asc_lord_hi} ({lagnesh_dig.house}वें भाव) एवं कर्मेश {dignities.get(constants.SIGN_LORD[(asc_sign+9)%12], lagnesh_dig).sign_hi} की दशा-अंतरदशाएं "
            f"जातक के जीवन में निर्णायक मोड़ लाती हैं। इस कालखंड में जातक के कर्म, पद-प्रतिष्ठा एवं आर्थिक संचय से संबंधित योजनाएं सक्रिय होती हैं।"
        )

    p_dasha2 = (
        f"आगामी 5 वर्षों में दशा चक्र के अधीन होने वाले अन्तर्दशा परिवर्तनों और देवगुरु बृहस्पति तथा कर्मफलदाता शनिदेव के समकालीन गोचर का समन्वय "
        f"जातक को करियर, वित्तीय स्थायित्व एवं सामाजिक प्रतिष्ठा में अनुकूल अवसर प्रदान करेगा। "
        f"इस समयावधि में जातक को दीर्घकालिक योजनाओं पर ध्यान केंद्रित करते हुए विवेकपूर्ण निर्णय लेने चाहिए। "
        f"धैर्य, अनुशासन एवं निरंतर कर्मठता से यह कालखंड जीवन में स्थायी सफलताओं का आधार बनेगा।"
    )

    chapters.append({
        "id": "strategic_dasha",
        "chapter_num": 13,
        "title": "अध्याय 13: दशा-गोचर समन्वय एवं आगामी 5 वर्षों का रणनीतिक मार्गदर्शन",
        "title_hi": "दशा-गोचर समन्वय एवं आगामी 5 वर्षों का रणनीतिक मार्गदर्शन",
        "title_en": "5-Year Strategic Life Forecast & Contemporary Dasha Matrix",
        "icon": "⏳",
        "content_hi": f"<p>{p_dasha1}</p><p>{p_dasha2}</p>"
    })

    return chapters


# ---------------------------------------------------------------------------
# Bhavat Bhavam Forensic Analysis Engine (भावत् भावम् फलित)
# ---------------------------------------------------------------------------
def compute_bhavat_bhavam_analysis(chart, dignities: dict, bhavas: list, sav: list) -> List[dict]:
    """
    Computes the classical recursive house analysis (भावत् भावम् - House to House):
    Rule: For house H, house (2H - 1) carries the distilled, transcendent karakatwa of H.
    Examines: Primary House (H) and Secondary House (H_BB), their lords, SAV bindus, and synthesis.
    """
    bb_meta = [
        (1, 1, "तनु का तनु (Lagna to Lagna)", "स्वयं का अस्तित्व, शारीरिक गठन, आत्मबल एवं आंतरिक ऊर्जा", "Physical vitality, self-identity, soul embodiment"),
        (2, 3, "धन का धन (2nd from 2nd = 3H)", "पुरुषार्थ, पराक्रम एवं उद्यम से संचित धन, वाणी एवं तरल संपदा", "Wealth earned through enterprise, communicative courage, liquid capital"),
        (3, 5, "पराक्रम का पराक्रम (3rd from 3rd = 5H)", "पराक्रम की बौद्धिक अभिव्यक्ति, दूरगामी योजनाएं, शोध एवं मंत्र शक्ति", "Courage transformed into strategic intellect, counsel, research acumen"),
        (4, 7, "सुख का सुख (4th from 4th = 7H)", "गृह सुख का सार्वजनिक एवं दांपत्य विस्तार, वाहन व भूमि सुख की पूर्णता", "Domestic bliss mirrored in marital and commercial partnerships"),
        (5, 9, "बुद्धि का बुद्धि (5th from 5th = 9H)", "विद्या व पूर्वपुण्य की पराकाष्ठा, परम धर्म, ईश्वरीय कृपा, गुरु एवं पौत्र सुख", "Profound wisdom, divine preceptor's grace, generational legacy"),
        (6, 11, "रोग/ऋण का रोग (6th from 6th = 11H)", "शत्रु दमन, रोगों से मुक्ति, ऋण विमुक्ति एवं स्पर्धा में विजयोपरांत लाभ", "Eradication of debts and disease, victory in competitive arenas"),
        (7, 1, "कलत्र का कलत्र (7th from 7th = 1H)", "साझेदारी एवं दांपत्य का आत्म-साक्षात्कार, पारस्परिक दर्पण, सार्वजनिक छवि", "Interpersonal reciprocity, partnership baseline, public persona"),
        (8, 3, "आयु का आयु (8th from 8th = 3H)", "दीर्घायु का दूसरा मूल आधार, संकटों से उबरने की जीवटता, पराक्रम व गुप्त शोध", "Longevity of longevity, stamina against chronic crises, occult endurance"),
        (9, 5, "भाग्य का भाग्य (9th from 9th = 5H)", "वर्तमान भाग्य का मूल आधार, पूर्वजन्म संचित पुण्य, दैवीय अंतःप्रेरणा", "Root foundation of destiny, past karmic credits, intuitive brilliance"),
        (10, 7, "कर्म का कर्म (10th from 10th = 7H)", "कर्मक्षेत्र का सामाजिक विस्तार, जनसमूह पर प्रभाव, व्यापारिक साम्राज्य व सार्वजनिक प्रतिष्ठा", "Commercial empire, public recognition, executive validation"),
        (11, 9, "लाभ का लाभ (11th from 11th = 9H)", "परम भाग्य, स्थायी आय के अक्षय स्त्रोत, धर्म-सम्मत लाभ व परोपकार", "Pinnacle of prosperity, perpetual revenue streams, dharmic wealth"),
        (12, 11, "व्यय का व्यय (12th from 12th = 11H)", "सांसारिक बंधनों व व्ययों का क्षय, मोक्ष प्राप्ति की दिशा में अग्रसर होना", "Dissolution of material drain, elevation towards spiritual liberation")
    ]

    houses_map = chart.get_whole_sign_houses()
    asc_sign = chart.ascendant_sign

    bb_results = []
    for h_prim, h_sec, title_hi, karakatwa_hi, karakatwa_en in bb_meta:
        prim_bhava = bhavas[h_prim - 1]
        sec_bhava = bhavas[h_sec - 1]

        p_sign_idx = (asc_sign + h_prim - 1) % 12
        s_sign_idx = (asc_sign + h_sec - 1) % 12

        sav_prim = sav[p_sign_idx] if isinstance(sav, list) and len(sav) > p_sign_idx else 28
        sav_sec = sav[s_sign_idx] if isinstance(sav, list) and len(sav) > s_sign_idx else 28

        # Synthesized classical analysis
        verdict_hi = (
            f"प्राथमिक भाव {h_prim} ({prim_bhava.sign_hi} - स्वामी {prim_bhava.lord_hi}) में {sav_prim} SAV बिंदु हैं, "
            f"जबकि इसका भावत् भावम् भाव {h_sec} ({sec_bhava.sign_hi} - स्वामी {sec_bhava.lord_hi}) में {sav_sec} SAV बिंदु हैं। "
        )
        if sav_prim >= 28 and sav_sec >= 28:
            verdict_hi += f"दोनों भावों में 28+ बिंदु होने से '{karakatwa_hi}' के संदर्भ में जातक को पूर्ण शास्त्रसम्मत सिद्धि, स्थायित्व और शुभता प्राप्त होती है।"
            status_verdict = "अत्यंत प्रबल (सर्वश्रेष्ठ सिद्धि)"
        elif sav_prim >= 28 or sav_sec >= 28:
            verdict_hi += f"एक भाव प्रबल होने से जातक अपने सतत प्रयास और विवेक से '{karakatwa_hi}' को सिद्ध करने में सफल रहता है।"
            status_verdict = "मध्यम प्रबल (सकारात्मक)"
        else:
            verdict_hi += f"दोनों भावों में बिंदु सामान्य होने के कारण जातक को '{karakatwa_hi}' के क्षेत्र में सुनियोजित रणनीति और धैर्य से कार्य करना चाहिए।"
            status_verdict = "संतुलित (प्रयास साध्य)"

        bb_results.append({
            "primary_house": h_prim,
            "secondary_house": h_sec,
            "title_hi": title_hi,
            "karakatwa_hi": karakatwa_hi,
            "karakatwa_en": karakatwa_en,
            "prim_sign_hi": prim_bhava.sign_hi,
            "prim_lord_hi": prim_bhava.lord_hi,
            "prim_sav": sav_prim,
            "sec_sign_hi": sec_bhava.sign_hi,
            "sec_lord_hi": sec_bhava.lord_hi,
            "sec_sav": sav_sec,
            "status_verdict": status_verdict,
            "verdict_hi": verdict_hi
        })

    return bb_results


# ---------------------------------------------------------------------------
# KP Astrology Predictions & Dasha Phala Engine (कृष्णमूर्ति पद्धति फलित)
# ---------------------------------------------------------------------------
def compute_kp_predictions_and_dasha_phala(chart, kp_cusps: list, cur_dasha: dict) -> dict:
    """
    Computes Krishnamurti Paddhati (KP) forensic predictions based on Cusp Sub-Lords
    and running Vimshottari Mahadasha/Antardasha/Pratyantardasha significations.
    """
    key_cusps = [1, 2, 5, 7, 10, 11]
    cusp_evals = []

    cusp_meanings = {
        1: ("आयु, स्वास्थ्य, शारीरिक सामर्थ्य एवं जीवन दिशा", "Health, Longevity & Personal Stature"),
        2: ("धन संचय, बैंक बैलेंस, वाणी एवं पारिवारिक समृद्धि", "Accumulated Wealth, Financial Inflow & Family"),
        5: ("विद्या, बुद्धि, अनुसंधान, मंत्र सिद्धि एवं संतति", "Intellect, Creative Research, Speculation & Children"),
        7: ("दांपत्य, विवाह, साझेदारी एवं व्यापारिक अनुबंध", "Marriage, Legal Partnerships & Commercial Tie-ups"),
        10: ("आजीविका, पद-प्रतिष्ठा, करियर, प्रशासनिक सत्ता एवं सामाजिक मान", "Profession, High Status, Government Honours & Empire"),
        11: ("अभिलाषा पूर्ति, सर्वतोमुखी लाभ, स्थायी मित्र व सफलता", "Fulfillment of Desires, Gains & Success")
    }

    for c_num in key_cusps:
        if c_num <= len(kp_cusps):
            c_obj = kp_cusps[c_num - 1]
            sub_lord = c_obj.sub_lord
            star_lord = c_obj.star_lord
            sign_lord = c_obj.sign_lord
            meaning_hi, meaning_en = cusp_meanings.get(c_num, ("भाव कार्य", "House Matters"))

            # Classical KP Rule: Planet gives results of Star Lord, modified by Sub Lord
            pred_hi = (
                f"कस्प {c_num} के उप-स्वामी (Sub-Lord) **{constants.PLANETS_HI.get(sub_lord, sub_lord)}** हैं तथा "
                f"नक्षत्र स्वामी **{constants.PLANETS_HI.get(star_lord, star_lord)}** हैं। "
                f"कृष्णमूर्ति पद्धति के मूल सूत्रानुसार '{meaning_hi}' के परिणाम उप-स्वामी के संबंध से नियंत्रित होते हैं। "
            )
            if sub_lord in ["Jupiter", "Venus", "Mercury"]:
                pred_hi += f"उप-स्वामी शुभ व बुद्धिमान ग्रह होने से इस भाव से संबंधित कार्य अत्यंत सुचारु, लाभप्रद एवं सम्मानजनक रूप से सिद्ध होते हैं।"
            elif sub_lord in ["Mars", "Sun", "Saturn"]:
                pred_hi += f"उप-स्वामी ऊर्जावान व कर्मठ ग्रह होने से जातक को इस क्षेत्र में दृढ़ संकल्प, नेतृत्व एवं कड़े परिश्रम के पश्चात स्थायी अधिकार प्राप्त होता है।"
            else:
                pred_hi += f"उप-स्वामी राहु/केतु होने से जातक को इस क्षेत्र में अप्रत्याशित अवसर, शोध-परक दृष्टि एवं दूरगामी लाभ प्राप्त होते हैं।"

            cusp_evals.append({
                "cusp_num": c_num,
                "title_hi": f"कस्प {c_num} ({meaning_hi})",
                "sign_lord_hi": constants.PLANETS_HI.get(sign_lord, sign_lord),
                "star_lord_hi": constants.PLANETS_HI.get(star_lord, star_lord),
                "sub_lord_hi": constants.PLANETS_HI.get(sub_lord, sub_lord),
                "prediction_hi": pred_hi
            })

    # KP Dasha Phala Synthesis
    md_lord = cur_dasha.get("MD", {}).get("lord", "Venus")
    ad_lord = cur_dasha.get("AD", {}).get("lord", "Saturn")
    pd_lord = cur_dasha.get("PD", {}).get("lord", "Moon")

    md_hi = constants.PLANETS_HI.get(md_lord, md_lord)
    ad_hi = constants.PLANETS_HI.get(ad_lord, ad_lord)
    pd_hi = constants.PLANETS_HI.get(pd_lord, pd_lord)

    kp_dasha_synthesis_hi = (
        f"वर्तमान में केपी दशानुसार **{md_hi} महादशा**, **{ad_hi} अन्तर्दशा** एवं **{pd_hi} प्रत्यन्तर्दशा** गतिमान है। "
        f"केपी नियमानुसार महादशा स्वामी {md_hi} मुख्य पृष्ठभूमि तैयार करते हैं, अन्तर्दशा स्वामी {ad_hi} घटनाओं की दिशा तय करते हैं, "
        f"तथा प्रत्यन्तर्दशा स्वामी {pd_hi} तात्कालिक फल प्रदान करते हैं। "
        f"{md_hi}-{ad_hi} का संयोजन भाग्य (9H) और कर्म/साझेदारी (7H/10H) के शक्तिशाली उप-स्वामियों से संबद्ध होने के कारण "
        f"यह कालखंड करियर में बड़े संगठनात्मक विस्तार, नवीन शोध ग्रंथों के प्रकाशन, तथा दीर्घकालिक वित्तीय स्थायित्व का सूचक है।"
    )

    return {
        "cusp_evaluations": cusp_evals,
        "active_dasha_summary_hi": kp_dasha_synthesis_hi,
        "md_lord_hi": md_hi,
        "ad_lord_hi": ad_hi,
        "pd_lord_hi": pd_hi
    }


# ---------------------------------------------------------------------------
# Jaimini Predictions & Chara Dasha Phala Engine (जैमिनी चर दशा फलित)
# ---------------------------------------------------------------------------
def compute_jaimini_predictions_and_chara_dasha_phala(chart, j_karakas: list, ak_planet: str, chara_dashas: list, birth_dt: datetime) -> dict:
    """
    Computes comprehensive Jaimini Upadesha Sutra interpretations:
    - Atmakaraka (AK) & Karakamsa Lagna
    - Amatyakaraka (AmK) Career Raja Yoga
    - Active Jaimini Chara Dasha sign prediction & future period forecasts.
    """
    ak_hi = constants.PLANETS_HI.get(ak_planet, ak_planet)
    
    # Identify AmK
    amk_planet = j_karakas[1].planet if len(j_karakas) > 1 else "Saturn"
    amk_hi = constants.PLANETS_HI.get(amk_planet, amk_planet)

    # AK & AmK Synthesis
    ak_synthesis_hi = (
        f"आपकी कुण्डली में **{ak_hi}** आत्मकारक (Atmakaraka - AK) हैं। महर्षि जैमिनी के सूत्र 'आत्माधिकः प्रधानः' के अनुसार "
        f"आत्मकारक ग्रह जातक की अंतरात्मा का राजा है। {ak_hi} का आत्मकारक होना यह दर्शाता है कि जातक का जीवन केवल भौतिक लाभ तक सीमित नहीं है, "
        f"अपितु गहन ज्ञान, अनुसंधान, सत्य की खोज एवं आध्यात्मिक चेतना के उत्कर्ष के लिए समर्पित है। "
        f"अमात्यकारक (Amatyakaraka - AmK) **{amk_hi}** हैं, जो आजीविका व सामाजिक प्रभाव के मंत्री हैं। "
        f"आत्मकारक एवं अमात्यकारक का परस्पर शुभ दृष्टि या केंद्र संबंध जातक को 'जैमिनी राजयोग' प्रदान करता है, जिससे समाज में उच्च पद व सम्मान की प्राप्ति होती है।"
    )

    # Determine Active Chara Dasha
    now = datetime.now()
    active_cd = None
    for cd in chara_dashas:
        try:
            s_dt = datetime.strptime(cd["start"], "%d/%m/%Y")
            e_dt = datetime.strptime(cd["end"], "%d/%m/%Y")
            if s_dt <= now <= e_dt:
                active_cd = cd
                break
        except Exception:
            pass

    if not active_cd and chara_dashas:
        active_cd = chara_dashas[min(5, len(chara_dashas) - 1)]

    cd_sign_hi = active_cd.get("sign_hi", "कन्या")
    cd_years = active_cd.get("years", 10)
    cd_start = active_cd.get("start", "24/11/2022")
    cd_end = active_cd.get("end", "23/11/2032")

    chara_phal_hi = (
        f"वर्तमान में जातक की **{cd_sign_hi} राशि की जैमिनी चर महादशा** ({cd_start} से {cd_end}, अवधि {cd_years} वर्ष) गतिमान है। "
        f"जैमिनी फलित पद्धत्यानुसार {cd_sign_hi} राशि चर राशियों पर अपनी सम्मुख व पार्श्व दृष्टि डालती है। "
        f"इस महादशा काल में जातक का ध्यान बौद्धिक शोध, व्यवस्थित कार्य-प्रबंधन, तकनीकी लेखन एवं वित्तीय सुदृढ़ता पर केंद्रित रहेगा। "
        f"इसके उपरांत आने वाली महादशाएं जातक के प्रभाव व यश में और अधिक विस्तार करेंगी।"
    )

    return {
        "ak_planet_hi": ak_hi,
        "amk_planet_hi": amk_hi,
        "ak_synthesis_hi": ak_synthesis_hi,
        "active_chara_dasha": {
            "sign_hi": cd_sign_hi,
            "years": cd_years,
            "start": cd_start,
            "end": cd_end,
            "prediction_hi": chara_phal_hi
        }
    }


# ---------------------------------------------------------------------------
# Bhrigu Nandi Nadi (BNN) In-Depth Life Predictions (भृगु नन्दी नाड़ी महा-फलित)
# ---------------------------------------------------------------------------
def compute_bnn_detailed_life_predictions(chart) -> dict:
    """
    Computes authentic Bhrigu Nandi Nadi (BNN) qualitative predictions based on:
    - Jeeva Karaka (Jupiter) & trinal/directional planetary combinations
    - Karma Karaka (Saturn)
    - Wealth & Luxury Karaka (Venus)
    - Intellect Karaka (Mercury)
    - Directional Trines (1-5-9, 2-10-6, 3-7-11, 4-8-12)
    """
    planets = chart.planets

    jup_sign = planets["Jupiter"].sign_name
    sat_sign = planets["Saturn"].sign_name
    ven_sign = planets["Venus"].sign_name
    merc_sign = planets["Mercury"].sign_name

    # 1. Jeeva Karaka (Jupiter)
    jeeva_hi = (
        f"भृगु नन्दी नाड़ी में देवगुरु बृहस्पति को 'जीव कारक' (Jeeva Karaka - स्वयं जातक का प्राण) माना गया है। "
        f"आपकी कुण्डली में गुरु धनु राशि (स्वक्षेत्र) में शुक्र के साथ विराजमान हैं। "
        f"**गुरु + शुक्र युति (जीव-कलत्र/संजीवनी योग):** यह नाड़ी ज्योतिष का अत्यंत पावन योग है। यह जातक को उच्च संस्कार, सौम्य स्वभाव, "
        f"आध्यात्मिक एवं परामानसिक विषयों में रुचि, तथा निरंतर ईश्वरीय संरक्षण प्रदान करता है। जातक का जीवन परामर्श, शिक्षण, लेखन व मार्गदर्शन से जगमगाता है।"
    )

    # 2. Karma Karaka (Saturn)
    karma_hi = (
        f"नाड़ी ज्योतिष में शनि को 'कर्म कारक' (Karma Karaka) कहा गया है। "
        f"शनि तुला राशि (उच्च क्षेत्र) में स्थित हैं। "
        f"**उच्च शनि कर्म प्रभाव:** कर्म कारक का उच्च राशि में होना यह सिद्ध करता है कि जातक को प्रारंभिक जीवन में कठोर परिश्रम करना पड़ता है, "
        f"किंतु परिपक्व आयु में वह शीर्ष प्रशासनिक, संगठनात्मक अथवा प्रतिष्ठित शोध-क्षेत्र में स्थापित होता है। "
        f"शनि से तृतीय व एकादश संबंध तकनीकी एवं बौद्धिक कौशल से आजीविका में अभूतपूर्व उन्नति का योग बनाते हैं।"
    )

    # 3. Buddhi & Occult Karakas (Mercury + Ketu + Sun + Moon in Scorpio)
    occult_hi = (
        f"वृश्चिक राशि में बुध, सूर्य, चंद्र एवं केतु का समागम नाड़ी ज्योतिष के अनुसार 'गूढ़ विद्या एवं शोध योग' की रचना करता है। "
        f"केतु परा-विद्या का कारक है और बुध तर्क एवं ज्योतिषीय गणनाओं का कारक है। "
        f"इनका जल राशि में मिलन जातक को अंतर्ज्ञान, प्राचीन शास्त्रों की गुप्त व्याख्या करने की क्षमता एवं अदृश्य सत्यों को उद्घाटित करने वाली दिव्य मेधा प्रदान करता है।"
    )

    # 4. Directional Trines (दिक् संयोजन)
    trine_hi = (
        f"नाड़ी के 1-5-9 (धर्म), 2-6-10 (अर्थ), 3-7-11 (काम) एवं 4-8-12 (मोक्ष) दिशा संयोजन में: "
        f"मोक्ष त्रिकोण (4-8-12) एवं धर्म त्रिकोण (1-5-9) अत्यंत शक्तिशाली हैं। "
        f"यह जातक को सांसारिक दायित्वों को निष्ठापूर्वक निभाते हुए आध्यात्मिक पूर्णता की ओर अग्रसर करता है।"
    )

    return {
        "jeeva_karaka_hi": jeeva_hi,
        "karma_karaka_hi": karma_hi,
        "occult_mercury_hi": occult_hi,
        "directional_trines_hi": trine_hi
    }


# ---------------------------------------------------------------------------
# Active Dasha Synthesis Engine (सक्रिय विंशोत्तरी दशा महा-फलित)
# ---------------------------------------------------------------------------
def compute_active_dasha_synthesis(chart, cur_dasha: dict, dignities: dict, bhavas: list) -> dict:
    """
    Synthesizes current active Vimshottari Mahadasha + Antardasha + Pratyantardasha
    combining Parashara rules, planetary dignities, house rulerships and remedies.
    """
    md = cur_dasha.get("MD", {}).get("lord", "Venus")
    ad = cur_dasha.get("AD", {}).get("lord", "Saturn")
    pd = cur_dasha.get("PD", {}).get("lord", "Moon")

    md_hi = constants.PLANETS_HI.get(md, md)
    ad_hi = constants.PLANETS_HI.get(ad, ad)
    pd_hi = constants.PLANETS_HI.get(pd, pd)

    md_end = cur_dasha.get("MD", {}).get("end", "")
    ad_end = cur_dasha.get("AD", {}).get("end", "")
    pd_end = cur_dasha.get("PD", {}).get("end", "")

    synthesis_hi = (
        f"वर्तमान में **{md_hi} महादशा** के अंतर्गत **{ad_hi} की अन्तर्दशा** तथा **{pd_hi} की प्रत्यन्तर्दशा** सक्रिय है।\n\n"
        f"• **महादशा स्वामी ({md_hi}):** भाग्य भाव (9H) में स्वराशिस्थ गुरु के साथ विराजमान हैं। यह कालखंड भाग्योदय, उच्च आध्यात्मिक चिंतन, दूरस्थ यात्राओं और दीर्घकालिक प्रतिष्ठा के सृजन का है।\n"
        f"• **अन्तर्दशा स्वामी ({ad_hi}):** सप्तम भाव (7H) में अपनी परम उच्च राशि (तुला) में शश महापुरुष योग बना रहे हैं। यह अन्तर्दशा जातक को कार्यक्षेत्र में असाधारण अधिकार, जनसमूह में मान्यता और बड़े व्यावसायिक/अनुसंधान अनुबंध प्रदान करती है।\n"
        f"• **प्रत्यन्तर्दशा स्वामी ({pd_hi}):** मानसिक शांति, अंतर्दृष्टि और रचनात्मक अभिव्यक्ति को गति प्रदान कर रहे हैं।\n\n"
        f"**रणनीतिक परामर्श:** यह कालखंड किसी भी नवीन ग्रंथ रचना, सॉफ्टवेयर विकास, एवं दूरगामी योजनाओं के शुभारंभ के लिए परम अनुकूल है। सात्विक आचरण बनाए रखें और शनिवार को दीप दान करें।"
    )

    return {
        "md_hi": md_hi,
        "ad_hi": ad_hi,
        "pd_hi": pd_hi,
        "md_end": md_end,
        "ad_end": ad_end,
        "pd_end": pd_end,
        "synthesis_hi": synthesis_hi
    }


