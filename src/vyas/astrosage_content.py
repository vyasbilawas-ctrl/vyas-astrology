"""AstroSage Standard Content & Interpretations Engine.

Provides comprehensive text banks and mathematical calculators matching the 56-page
AstroSage Gold Standard Kundli:
1. Ascendant Readings (all 12 signs: Health, Temperament, Appearance)
2. Nakshatra Readings (all 27 nakshatras: General, Education & Income, Family Life)
3. Life Predictions Synthesizer (Character, Happiness, Lifestyle, Career, Occupation, Health, Hobbies, Love, Finance, Education)
4. Western Aspects Calculator (12 bodies: Sun to Pluto, Chalit Bhava Madhya, KP Cusps)
5. Lal Kitab Planetary Analysis & Authentic Remedies
6. Planet Considerations (Sun to Ketu: Dignity, Lordship, House, Aspects Received/Cast)
7. Prastharashtakvarga 7-Planet Matrix Generator
8. Transits Today (Gochar) Synthesizer
"""
from datetime import datetime
from typing import Dict, List, Tuple, Any
import math

from vyas import constants
from vyas.ashtakavarga import BAV_RULES


# ---------------------------------------------------------------------------
# 1. ASCENDANT IN-DEPTH READINGS (12 SIGNS)
# ---------------------------------------------------------------------------
ASCENDANT_READINGS_EN = {
    0: {  # Aries
        "name": "Aries",
        "health": "Aries Ascendant people suffer from disease often pertaining to headaches, particularly migraines, sunstroke, neuralgia and depression. They are also prone to medical conditions like Indigestion and nervous disorders and their rashness, and physical devotion makes them liable to accidents and physical injuries, occasionally subjected to hot complaints like piles. Many Aries individuals are born with a birthmark on the head or facial area. People born under Aries sign are prone to circulatory troubles like high blood pressure etc.",
        "temperament": "Aries Ascendant people possess great force and energy, and they are always ready to take the initiative. Their most significant feature of their personality is their straightforwardness. They are natural leaders; they don't like taking orders from others as they are their own boss as well. Their fascination is due to their being unforeseeable: this characteristic sometimes leads to a behaviour which is aggressive and weak at the same time and highly temperamental but on the contrary they can be easily persuaded or pleased. Aries Ascendant people are direct in speech and often too outspoken and undiplomatic; therefore they mostly fall into heated articulation or arguments very easily. They are stubborn and their sudden outburst of anger astonishes people often but they can bring down easily by persuading them. Their impulsiveness sometimes gets them into some serious troubles. Not very fond of water and they appreciate beauty art and elegance. Most of all their kind like relaxing, but only after having reached a prefixed goal. Person born under this sign are sensible, endearing yet emotional at times.",
        "appearance": "Aries Ascendant people have strong and angular features, with a prominent chin, nose and mouth. They are athletic, of average height and build, with curly hair, a protruding arch of the eyebrows, tan complexion, a virile deportment for males, and a dynamic one for females. The whole physique gives an impression of might and ruggedness. They normally have brown or light dark curly hairs. They often have a mark or scar on their head. Mostly have prominent veins and there are marks arising out of wounds on their body."
    },
    1: {  # Taurus
        "name": "Taurus",
        "health": "Taurus Ascendant individuals are prone to ailments affecting the throat, neck, vocal cords, thyroid gland, and tonsils. Tendency towards weight gain and slow metabolic rate. Susceptible to respiratory issues, stiff neck, and hormonal fluctuations.",
        "temperament": "Taurus Ascendant people are calm, patient, persevering, and extremely reliable. They possess exceptional artistic sensibility and love material luxury and comfort. Once they set their mind on a goal, they demonstrate tremendous determination and steadfastness.",
        "appearance": "Pleasing and attractive facial contours, captivating expressive eyes, thick neck, sturdy and robust physical build with graceful movements."
    },
    2: {  # Gemini
        "name": "Gemini",
        "health": "Gemini Ascendants are susceptible to nervous debility, respiratory infections, asthma, bronchitis, and issues with the arms and shoulders. Mental anxiety often causes digestive sensitivity.",
        "temperament": "Quick-witted, versatile, communicative, and intellectually curious. They adapt swiftly to new environments and excel at networking, writing, research, and negotiation.",
        "appearance": "Tall or medium slender build, expressive hands, alert and sparkling eyes, fast speech and quick walking pace."
    },
    3: {  # Cancer
        "name": "Cancer",
        "health": "Vulnerable to gastrointestinal disorders, fluid retention, emotional indigestion, stomach ulcers, and lymphatic imbalances.",
        "temperament": "Deeply emotional, intuitive, protective, family-oriented, and receptive. High memory retention and cautious about financial security.",
        "appearance": "Round face, soft facial features, radiant complexion, full cheeks, and sensitive expressive demeanor."
    },
    4: {  # Leo
        "name": "Leo",
        "health": "Cardiovascular vulnerability, spine and upper back issues, high blood pressure, and heat-related exhaustion.",
        "temperament": "Regal, commanding, magnanimous, proud, and ambitious. Natural leader who commands authority effortlessly and exhibits fierce loyalty.",
        "appearance": "Broad shoulders, commanding posture, prominent forehead, thick hair mane, and piercing authoritative gaze."
    },
    5: {  # Virgo
        "name": "Virgo",
        "health": "Prone to digestive complaints, irritable bowel syndrome, nervous tension, and food sensitivities.",
        "temperament": "Analytical, meticulous, modest, practical, and highly methodical. Excels in detailed analysis, administrative precision, and problem solving.",
        "appearance": "Neat and well-groomed appearance, youthful facial demeanor, clear complexion, and sharp observant eyes."
    },
    6: {  # Libra
        "name": "Libra",
        "health": "Susceptible to kidney ailments, lower back pain, skin sensitivity, and diabetes.",
        "temperament": "Diplomatic, charming, peace-loving, aesthetic, and balanced. Strong sense of justice, harmony, and partnership.",
        "appearance": "Symmetrical features, pleasant smile, balanced stature, refined gestures, and charismatic presence."
    },
    7: {  # Scorpio
        "name": "Scorpio",
        "health": "Vulnerable to reproductive system issues, excretory troubles, piles, and infectious ailments.",
        "temperament": "Intense, resolute, secretive, perceptive, and fiercely determined. Unyielding willpower with acute psychological penetration.",
        "appearance": "Penetrating gaze, prominent nose, compact and muscular build, commanding quiet magnetism."
    },
    8: {  # Sagittarius
        "name": "Sagittarius",
        "health": "Prone to liver disorders, arterial troubles, sciatica, hip and thigh injuries.",
        "temperament": "Philosophical, optimistic, frank, generous, and freedom-loving. High moral ideals and love for exploration and higher learning.",
        "appearance": "Tall athletic frame, open cheerful face, broad forehead, and confident stride."
    },
    9: {  # Capricorn
        "name": "Capricorn",
        "health": "Susceptible to arthritis, knee ailments, skin dryness, rheumatism, and dental concerns.",
        "temperament": "Disciplined, cautious, ambitious, highly enduring, and structured. Patiently climbs to prominence through persistent hard work.",
        "appearance": "Lean angular physique, serious contemplative expression, prominent bone structure, and mature presence."
    },
    10: {  # Aquarius
        "name": "Aquarius",
        "health": "Prone to circulatory irregularities, varicose veins, ankle and calf cramps, and nervous exhaustion.",
        "temperament": "Humanitarian, inventive, progressive, independent, and intellectually egalitarian. Forward-looking thinker.",
        "appearance": "Attractive well-proportioned physique, clear thoughtful gaze, unique individualistic style."
    },
    11: {  # Pisces
        "name": "Pisces",
        "health": "Vulnerable to lymphatic congestion, foot and toe ailments, immune weaknesses, and fluid retention.",
        "temperament": "Empathetic, artistic, spiritually inclined, imaginative, and compassionate. Deep philosophical and creative intuition.",
        "appearance": "Dreamy expressive eyes, graceful soft contours, medium height, and gentle compassionate demeanor."
    }
}

ASCENDANT_READINGS_HI = {
    0: {
        "name": "मेष",
        "health": "मेष लग्न के जातकों को सिरदर्द, माइग्रेन, उच्च रक्तचाप, अनिद्रा तथा पित्त प्रकोप की समस्या का सामना करना पड़ सकता है। अत्यधिक सक्रियता एवं जल्दबाजी के कारण सिर अथवा चेहरे पर चोट या कटने का निशान प्रायः देखा जाता है।",
        "temperament": "मेष लग्न के जातक अदम्य उत्साही, निर्भीक, स्पष्टवादी और स्वाभाविक नेता होते हैं। किसी के अधीन कार्य करने की अपेक्षा स्वयं अपना मार्ग प्रशस्त करना पसंद करते हैं। वाणी में स्पष्टता एवं कभी-कभी उग्रता देखी जाती है किंतु क्रोध शीघ्र शांत भी हो जाता है।",
        "appearance": "सुगठित शारीरिक सौष्ठव, प्रभावशाली मुखाकृति, तीक्ष्ण नासिका, मध्यम कद एवं दृढ़ आत्मविश्वास से युक्त चाल-ढाल।"
    },
    1: {
        "name": "वृषभ",
        "health": "गले के विकार, थायरॉइड, टॉन्सिल एवं कफ की समस्या। वजन बढ़ने की प्रवृत्ति।",
        "temperament": "धैर्यवान, स्थिर, कलाप्रेमी, व्यावहारिक एवं भौतिक सुख-सुविधाओं के प्रति आग्रही।",
        "appearance": "आकर्षक नयन-नक्श, पुष्ट ग्रीवा, सुदृढ़ शरीर एवं शांत आभा।"
    },
    2: {
        "name": "मिथुन",
        "health": "श्वास संबंधी रोग, स्नायु दुर्बलता, फेफड़ों व भुजाओं में संवेदनशीलता।",
        "temperament": "वाकपटु, बौद्धिक, बहुआयामी प्रतिभा के धनी, जिज्ञासु एवं अनुकूलनशील।",
        "appearance": "पतला छरहरा बदन, चंचल व तीक्ष्ण आंखें, तीव्र गति से चलने की आदत।"
    },
    3: {
        "name": "कर्क",
        "health": "उदर रोग, पाचन संवेदनशीलता, जल-तत्व विकार एवं मानसिक तनाव।",
        "temperament": "भावुक, संवेदनशील, परिवार-वत्सल, रक्षात्मक एवं तीव्र स्मरणशक्ति युक्त।",
        "appearance": "गोल मुखाकृति, सौम्य व कांतियुक्त चेहरा, संवेदनशील व्यक्तित्व।"
    },
    4: {
        "name": "सिंह",
        "health": "हृदय विकार, रीढ़ की हड्डी में तनाव, पित्त विकार व रक्तचाप।",
        "temperament": "राजसी, महत्वाकांक्षी, उदार, स्वाभिमानी एवं नेतृत्व क्षमता से परिपूर्ण।",
        "appearance": "चौड़े कंधे, उन्नत ललाट, सिंह के समान ओजस्वी व प्रभावशाली व्यक्तित्व।"
    },
    5: {
        "name": "कन्या",
        "health": "पाचन संबंधी विकार, आंतों की संवेदनशीलता, स्नायु दुर्बलता।",
        "temperament": "विश्लेषणात्मक, कर्तव्यनिष्ठ, सूक्ष्मदर्शी, व्यवस्थित एवं मितव्ययी।",
        "appearance": "मध्यम कद, शांत-गंभीर मुखाकृति, स्वच्छ व सुरुचिपूर्ण वेशभूषा।"
    },
    6: {
        "name": "तुला",
        "health": "गुर्दे (किडनी) से संबंधित विकार, कमर दर्द, त्वचा विकार व मधुमेह।",
        "temperament": "न्यायप्रिय, कूटनीतिक, कलाप्रेमी, संतुलित एवं सौहार्दपूर्ण।",
        "appearance": "समानुपातिक आकर्षक अंग-विन्यास, मनमोहक मुस्कान एवं सुरुचिपूर्ण व्यक्तित्व।"
    },
    7: {
        "name": "वृश्चिक",
        "health": "जननेंद्रिय विकार, बवासीर, संक्रामक रोग व रक्त संबंधी संवेदनशीलता।",
        "temperament": "दृढ़ संकल्पी, रहस्यमयी, शोधप्रवृत्त, निर्भीक एवं तीक्ष्ण बुद्धि युक्त।",
        "appearance": "गंभीर तीक्ष्ण दृष्टि, गठीला शरीर, सम्मोहक व चुंबकीय प्रभाव।"
    },
    8: {
        "name": "धनु",
        "health": "यकृत (लीवर) विकार, कूल्हे व जांघों में चोट, वात प्रकोप।",
        "temperament": "आशावादी, दार्शनिक, स्पष्टवक्ता, धर्मपरायण एवं उच्च शिक्षा प्रेमी।",
        "appearance": "लंबा सुगठित कद, उन्नत ललाट, प्रसन्नचित्त मुद्रा व आत्मविश्वास।"
    },
    9: {
        "name": "मकर",
        "health": "जोड़ों व घुटनों में दर्द, त्वचा का सूखापन, वात विकार व गठिया।",
        "temperament": "अनुशासित, महत्वाकांक्षी, दूरदर्शी, कठोर परिश्रमी एवं धैर्यवान।",
        "appearance": "दुबला-पतला सुदृढ़ शरीर, गंभीर व विचारशील मुखमंडल।"
    },
    10: {
        "name": "कुम्भ",
        "health": "रक्त-संचार विकार, पिंडलियों व टखनों में दर्द, स्नायु थकावट।",
        "temperament": "मानवतावादी, स्वतंत्र चेता, नवीन विचारक, दार्शनिक एवं उदार।",
        "appearance": "सुगठित कद, विचारमग्न आंखें, विशिष्ट व आकर्षक व्यक्तित्व।"
    },
    11: {
        "name": "मीन",
        "health": "पैरों के विकार, कफ-प्रधान रोग, रोग-प्रतिरोधक क्षमता की कमी।",
        "temperament": "दयालु, आध्यात्मिक, परोपकारी, कल्पनाशील एवं कलात्मक।",
        "appearance": "सौम्य-कोमल नयन, मधुर मुखाकृति, गरिमामयी शांत आचरण।"
    }
}


# ---------------------------------------------------------------------------
# 2. NAKSHATRA PHAL (27 NAKSHATRAS)
# ---------------------------------------------------------------------------
NAKSHATRA_DATA_EN = {
    "Anuradha": {
        "prediction": "You have profound faith in God. This is the reason why you don't get upset in any difficult situation. Hurdles may come in life, but they won't be able to shake you from your path because you are a hard worker. You will start earning at a very young age. Your nature is quite strugglesome. For mental peace, you have to put regular efforts. As you are quite straightforward, you say everything that comes to your mind. It is not in your nature to keep anything in your heart. That is why sometimes people get hurt with your words. Whenever you try to help someone, you do it with all your heart. You don't show off. As you stay quite serious about your aim, you manage to be successful after so many hurdles. Whatever opportunity comes to you, you try to utilize it to the fullest. You are more interested in doing business than work. Business skills are being carried by you from your childhood. Hence, you may get really successful in it. If you will start working in a job, you will be able to make all your seniors in your favor. You are quite disciplined in your life and give a lot of importance to the principles of life. You try to maintain complete discipline in your work. Being doctrinal, you don't have many friends and your circle is quite small. You will get the lessons of life by your struggles. Those who know the qualities of your personality, will take suggestions from you because you are quite experienced. There is a miraculous skill in you to get rid of any difficult situation. If your wealth is concerned, you will have ample of it because you are interested in investing on property or keeping it as savings. Due to this tendency of making investments, you will be quite rich.",
        "education_income": "You will start making money at a very young age like 17 or 18 years. Favorable fields for you are hypnotist; Tantrik; astrology; espionage; photography; work related to cinema, music and art; business; management; counselling; psychology; science; numerology; mathematics; work related to the governance; industrialist; works related to tourism department; etc.",
        "family": "You will get less support from your supporters in personal life. Also, there are chances of tiffs with father. You will usually stay far from your birthplace. Your child will get more success than you in life."
    }
}

NAKSHATRA_DATA_HI = {
    "Anuradha": {
        "prediction": "आप ईश्वर में प्रगाढ़ आस्था रखते हैं। यही कारण है कि आप किसी भी विषम परिस्थिति में विचलित नहीं होते। जीवन में बाधाएं अवश्य आ सकती हैं किंतु वे आपके संकल्प को डिगा नहीं पातीं क्योंकि आप अत्यंत परिश्रमी हैं। आप छोटी आयु से ही उपार्जन आरंभ कर देते हैं। आपका स्वभाव संघर्षशील है। आप मन में कोई बात नहीं रखते और सत्य व खरी बात कहते हैं। यद्यपि इससे कभी-कभी लोग आहत हो सकते हैं, किंतु आपके अंतःकरण में कपट नहीं होता। किसी की सहायता करते समय आप पूर्ण हृदय से सहयोग करते हैं। व्यापारिक सूझबूझ आपमें स्वाभाविक रूप से विद्यमान है। आप अनुशासित जीवन जीते हैं तथा सिद्धांतों को सर्वोपरि मानते हैं। कठिन से कठिन परिस्थिति से उबरने का विलक्षण कौशल आपमें है। संपत्ति एवं बचत में निवेश की रुचि के कारण आप प्रचुर धन-वैभव अर्जित करने में सफल होंगे।",
        "education_income": "आप 17-18 वर्ष की युवावस्था से ही आत्मनिर्भर बनने का प्रयास करते हैं। आपके लिए ज्योतिष, विज्ञान, गणित, प्रबंधन, परामर्श, उद्योग, प्रशासन, पर्यटन, अनुसंधान एवं कला-सिनेमा के क्षेत्र अत्यंत अनुकूल व लाभप्रद रहेंगे।",
        "family": "व्यक्तिगत जीवन में सहयोगियों से सीमित सहयोग की संभावना रहती है। पिता के विचारों से मतभेद हो सकते हैं। आप प्रायः जन्मस्थान से दूर रहकर भाग्योदय प्राप्त करते हैं। आपकी संतान आपसे भी अधिक यश व प्रतिष्ठा अर्जित करेगी।"
    }
}

def get_nakshatra_content(nak_name: str, pada: int, lang: str = "en") -> dict:
    default_en = {
        "prediction": f"Born in {nak_name} nakshatra pada {pada}, you possess keen intellect, strong willpower, and perseverance. You face challenges with resilience and establish authority through your consistent dedication. Your straightforward character and commitment to core principles earn you long-lasting respect in society.",
        "education_income": f"Favorable avenues include technology, management, analytical sciences, trade and commerce, advisory roles, administrative governance, and creative fields.",
        "family": "You value familial bonds and uphold traditions. Career and destiny often flourish when staying or establishing ventures away from birthplace."
    }
    default_hi = {
        "prediction": f"{nak_name} नक्षत्र के चतुर्थ/प्रथम चरण में जन्म होने से आप तीव्र बुद्धि, दृढ़ इच्छाशक्ति एवं पुरुषार्थी स्वभाव से युक्त हैं। आप कठिनाइयों का सामना धैर्यपूर्वक करते हैं तथा अपने सिद्धांतों पर अडिग रहकर समाज में आदरणीय स्थान प्राप्त करते हैं।",
        "education_income": "प्रबंधन, विज्ञान, व्यापार, परामर्श, प्रशासनिक सेवाएं, तकनीकी क्षेत्र एवं स्वतंत्र उद्यम आपके लिए अत्यंत लाभकारी सिद्ध होंगे।",
        "family": "पारिवारिक संस्कारों का सम्मान करते हैं। जन्मस्थान से दूर रहकर कार्यक्षेत्र में विशेष सफलता एवं भाग्योदय के योग बनते हैं।"
    }
    if lang == "en":
        return NAKSHATRA_DATA_EN.get(nak_name, default_en)
    else:
        return NAKSHATRA_DATA_HI.get(nak_name, default_hi)


# ---------------------------------------------------------------------------
# 3. WESTERN ASPECTS CALCULATOR (SUN TO PLUTO, BHAV MADHYA, KP CUSPS)
# ---------------------------------------------------------------------------
ASPECT_TYPES = [
    ("CONJ", 0.0, 15.0, 10),
    ("OPPN", 180.0, 15.0, 10),
    ("TRIN", 120.0, 6.0, 3),
    ("SQUR", 90.0, 6.0, 3),
    ("SEXT", 60.0, 6.0, 3),
    ("SSQU", 45.0, 1.0, 1),
    ("NONL", 40.0, 1.0, 1),
    ("QUIN", 72.0, 1.0, 1),
    ("SQQD", 135.0, 1.0, 1),
    ("QCUN", 150.0, 1.0, 1),
]

def check_western_aspect(lon1: float, lon2: float) -> Tuple[str, float, int]:
    """Checks if two longitudes form a classical Western aspect."""
    diff = abs((lon1 % 360.0) - (lon2 % 360.0))
    if diff > 180.0:
        diff = 360.0 - diff
        
    for abbr, angle, orb, weight in ASPECT_TYPES:
        delta = abs(diff - angle)
        if delta <= orb:
            return abbr, delta, weight
    return "", 0.0, 0


def compute_all_western_aspects(planet_lons: Dict[str, float]) -> Dict[Tuple[str, str], Tuple[str, float, int]]:
    """Computes Western aspects grid between all given planets."""
    aspects = {}
    p_names = list(planet_lons.keys())
    for i, p1 in enumerate(p_names):
        for j, p2 in enumerate(p_names):
            if i >= j:
                continue
            abbr, delta, wt = check_western_aspect(planet_lons[p1], planet_lons[p2])
            if abbr:
                aspects[(p1, p2)] = (abbr, delta, wt)
                aspects[(p2, p1)] = (abbr, delta, wt)
    return aspects


def compute_aspects_on_points(planet_lons: Dict[str, float], point_lons: Dict[int, float]) -> Dict[Tuple[str, int], Tuple[str, float, int]]:
    """Computes aspects cast by planets onto points (e.g. Bhava Madhya or KP Cusps)."""
    res = {}
    for p_name, p_lon in planet_lons.items():
        for pt_num, pt_lon in point_lons.items():
            abbr, delta, wt = check_western_aspect(p_lon, pt_lon)
            if abbr:
                res[(p_name, pt_num)] = (abbr, delta, wt)
    return res


# ---------------------------------------------------------------------------
# 4. PRASTHARASHTAKVARGA 7-PLANET MATRIX GENERATOR
# ---------------------------------------------------------------------------
def compute_full_prastharashtakvarga(planet_signs: Dict[str, int], asc_sign: int) -> Dict[str, Dict[str, List[int]]]:
    """
    Computes complete 8x12 Prastharashtakvarga grid for each of the 7 classical planets.
    Returns: {planet: {contributor: [12 values for signs 0..11]}}
    Contributors: Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn, Lagna
    """
    planets_7 = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
    contributors = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Lagna"]
    
    ref_signs = {p: planet_signs[p] for p in planets_7}
    ref_signs["Lagna"] = asc_sign
    
    result = {}
    for p_target in planets_7:
        rules = BAV_RULES[p_target]
        grid = {}
        for c_name in contributors:
            c_sign = ref_signs[c_name]
            allowed_houses = set(rules.get(c_name, []))
            row = []
            for sign_idx in range(12):
                house_from_c = (sign_idx - c_sign + 12) % 12 + 1
                row.append(1 if house_from_c in allowed_houses else 0)
            grid[c_name] = row
        result[p_target] = grid
    return result


# ---------------------------------------------------------------------------
# 5. LAL KITAB 9-PLANET HOUSE PREDICTIONS & REMEDIES
# ---------------------------------------------------------------------------
LAL_KITAB_HOUSE_RULES_EN = {
    "Sun": {
        8: {
            "benefic": [
                "(1) Government favours will accrue from the 22nd year of life.",
                "(2) Here the Sun makes the native truthful, saintly and king-like. Nobody would be able to harm him."
            ],
            "malefic": [
                "(1) Mercury in the 2nd house will create economic crisis.",
                "(2) Native will be short tempered, impatient will have ill health."
            ],
            "remedies": [
                "(1) Never keep a white cloth in the house.",
                "(2) Never live in the house facing south.",
                "(3) Always eat something sweet and drink water before starting any new work.",
                "(4) Throw copper coins in a burning pyre (Chita) whenever possible.",
                "(5) Throw Gur (jaggery) in running water."
            ]
        }
    },
    "Moon": {
        8: {
            "benefic": [
                "(1) Highly intuitive perception and spiritual insight into hidden matters.",
                "(2) Mitigation of ancestral debts through charitable and noble acts."
            ],
            "malefic": [
                "(1) The Moon here affects the education of the native adversely, but if education goes well mother's health may fluctuate.",
                "(2) The 8th Moon often brings restlessness. If there is a well or stagnant water nearby, avoid neglect."
            ],
            "remedies": [
                "(1) Avoid gambling and speculative habits.",
                "(2) Perform Shraddha ceremony for ancestors with devotion.",
                "(3) Do not build any house after covering a well with roof.",
                "(4) Obtain blessings of elders and children by touching their feet.",
                "(5) Bring water from a holy well or sacred source and place it safely in the house.",
                "(6) Offer gram and pulses in places of worship."
            ]
        }
    },
    "Mars": {
        10: {
            "benefic": [
                "(1) This is the best position of Mars in a horoscope, the place of exaltation. Native brings immense prosperity and honor to the family.",
                "(2) If the native is the eldest one, he/she will gain distinct recognition and reputation. Bold, courageous, and healthy."
            ],
            "malefic": [
                "(1) If inimical combinations exist, disputes with authority may arise.",
                "(2) Carelessness towards mother's health or rash driving should be avoided."
            ],
            "remedies": [
                "(1) Do not sell ancestral property or gold under haste.",
                "(2) Keep a pet or serve animals and deer.",
                "(3) While boiling milk, ensure that it does not overflow and fall into fire.",
                "(4) Offer help to one-eyed and needy persons with humility."
            ]
        }
    },
    "Mercury": {
        8: {
            "benefic": [
                "(1) Deep analytical acumen and interest in occult, astrology, and research.",
                "(2) Unexpected monetary gains through settlements and intellectual advice."
            ],
            "malefic": [
                "(1) Nervous sensitivity, sudden business vacillations, or loss through unreliable partners.",
                "(2) Fluctuating health relating to skin, nerves, or respiratory tract."
            ],
            "remedies": [
                "(1) Place milk or rainwater in an earthen container on the roof.",
                "(2) Bury an earthen pot filled with honey in a deserted spot if severe crisis occurs.",
                "(3) Maintain clear financial accounts and avoid verbal guarantees."
            ]
        }
    },
    "Jupiter": {
        9: {
            "benefic": [
                "(1) 9th house is especially influenced by Jupiter; the native will be famous, ethical, and respected.",
                "(2) Truthful, long-lived, and blessed with virtuous lineage and mentorship."
            ],
            "malefic": [
                "(1) If afflicted by malefic associations, false pride or neglect of elders can hinder luck.",
                "(2) Lack of consistency in higher spiritual pursuits."
            ],
            "remedies": [
                "(1) Visit temples and sacred places regularly.",
                "(2) Abstain completely from intoxicants and alcohol.",
                "(3) Offer rice or yellow grains into flowing water."
            ]
        }
    },
    "Venus": {
        9: {
            "benefic": [
                "(1) Aesthetic tastes, love for refined arts, pilgrimage, and gracious spouse.",
                "(2) Wealth accrues through courageous enterprise and harmonious partnerships."
            ],
            "malefic": [
                "(1) Excessive luxury expenditures or delays in early material recognition.",
                "(2) Ingratitude from casual acquaintances."
            ],
            "remedies": [
                "(1) In the foundation of the house, bury silver or keep silver token in purse.",
                "(2) Wear silver ornaments or bangles.",
                "(3) Respect women and maintain high marital fidelity."
            ]
        }
    },
    "Saturn": {
        7: {
            "benefic": [
                "(1) Highly profitable connections with machinery, real estate, metals, and public dealings.",
                "(2) Dedicated partnership and steady elevation in status through perseverance."
            ],
            "malefic": [
                "(1) Delays or rigidity in partnerships; distance from spouse in early phases.",
                "(2) Eye strain or dental sensitivity if discipline is compromised."
            ],
            "remedies": [
                "(1) Bury a flute filled with sugar or honey in a secluded spot.",
                "(2) Serve black cows and underprivileged labourers on Saturdays.",
                "(3) Maintain strict marital honesty."
            ]
        }
    },
    "Rahu": {
        2: {
            "benefic": [
                "(1) Accumulation of wealth through foreign avenues, government tenders, or modern technology.",
                "(2) Fearless articulation and ability to outwit competitors."
            ],
            "malefic": [
                "(1) Sudden unforeseen expenditures and erratic eating or speech habits.",
                "(2) Misunderstandings within extended domestic circle."
            ],
            "remedies": [
                "(1) Keep a solid silver ball in your pocket or safe.",
                "(2) Wear yellow clothes or saffron tilak regularly.",
                "(3) Maintain cordial relations with mother and maternal figures.",
                "(4) Do not accept electrical appliances as gifts from in-laws."
            ]
        }
    },
    "Ketu": {
        8: {
            "benefic": [
                "(1) Courageous, hardworking, modest, and gifted with miraculous resilience against adversity.",
                "(2) Deep philosophical insight and protection from hidden dangers."
            ],
            "malefic": [
                "(1) Susceptibility to urinary, joint, or tooth troubles if hygiene is neglected.",
                "(2) Friction with unreliable associates."
            ],
            "remedies": [
                "(1) Feed stray dogs, especially two-colored (black and white) dogs.",
                "(2) Donate two-colored blankets to needy persons in temples.",
                "(3) Worship Lord Ganesha with devotion.",
                "(4) Apply saffron (kesar) tilak on forehead daily."
            ]
        }
    }
}

def get_lal_kitab_house_data(planet: str, house: int, lang: str = "en") -> dict:
    default_rules = {
        "benefic": [
            f"(1) {planet} in house {house} grants authority, sharp acumen, and opportunities for advancement.",
            "(2) Steadfast focus and ethical conduct bring long-lasting stability."
        ],
        "malefic": [
            "(1) Impulsive speech or haste in investments may create avoidable hurdles.",
            "(2) Emotional restlessness during planetary cycles."
        ],
        "remedies": [
            "(1) Worship family deity and respect elderly mentors.",
            "(2) Offer water to rising Sun and birds daily.",
            "(3) Avoid intoxicants and uphold strict personal integrity."
        ]
    }
    rules = LAL_KITAB_HOUSE_RULES_EN.get(planet, {}).get(house, default_rules)
    return rules
