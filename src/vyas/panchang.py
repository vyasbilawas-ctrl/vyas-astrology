"""Panchang & Avakhada engine for VYAS.

Everything is computed from the JPL ephemeris – nothing is hard-coded per chart.

Conventions (same as AstroSage / Parashara's Light defaults):
* Sunrise/sunset: upper limb of the Sun on the horizon with standard refraction
  (-0°50'), i.e. Skyfield's ``almanac.sunrise_sunset``.
* Hindu day (vara) runs sunrise -> next sunrise.
* Tithi = (Moon - Sun) / 12°, Yoga = (Sun + Moon sidereal) / 13°20',
  Karana = half tithi, Nakshatra from sidereal Moon.
* Lunar month: Amanta (new-moon ending), named by the Sun's sidereal sign at the
  preceding new moon; Purnimanta name also returned.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta, timezone

from . import constants as C
from . import ephem

TITHIS = ["Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi",
          "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi",
          "Trayodashi", "Chaturdashi", "Purnima"]
TITHIS_HI = ["प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी", "षष्ठी", "सप्तमी",
             "अष्टमी", "नवमी", "दशमी", "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा"]
YOGAS = ["Vishkambha", "Priti", "Ayushman", "Saubhagya", "Shobhana", "Atiganda",
         "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi", "Dhruva", "Vyaghata",
         "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan", "Parigha", "Shiva",
         "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"]
KARANA_MOVABLE = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti (Bhadra)"]
VARAS = ["Ravivar (Sun)", "Somvar (Mon)", "Mangalvar (Tue)", "Budhvar (Wed)",
         "Guruvar (Thu)", "Shukravar (Fri)", "Shanivar (Sat)"]
VARA_LORD = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"]
MASAS = ["Chaitra", "Vaishakha", "Jyeshtha", "Ashadha", "Shravana", "Bhadrapada",
         "Ashwin", "Kartika", "Margashirsha", "Pausha", "Magha", "Phalguna"]

# ---- Avakhada tables (Moon based) -------------------------------------------
_VARNA_BY_SIGN = ["Kshatriya", "Vaishya", "Shudra", "Brahmin"] * 3  # Aries.. by element
_YONI = ["Ashwa", "Gaja", "Mesha", "Sarpa", "Sarpa", "Shwan", "Marjar", "Mesha",
         "Marjar", "Mushak", "Mushak", "Gau", "Mahish", "Vyaghra", "Mahish",
         "Vyaghra", "Mrig", "Mrig", "Shwan", "Vanar", "Nakul", "Vanar", "Simha",
         "Ashwa", "Simha", "Gau", "Gaja"]
_GANA = ["Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva",
         "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa",
         "Deva", "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya",
         "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva"]
_NADI_CYCLE = ["Adi", "Madhya", "Antya", "Antya", "Madhya", "Adi"]
_TATVA_BY_SIGN = ["Agni", "Prithvi", "Vayu", "Jal"] * 3
# Vashya: (sign index) -> (first 15°, last 15°)
_VASHYA = {0: ("Chatushpad",) * 2, 1: ("Chatushpad",) * 2, 2: ("Manav",) * 2,
           3: ("Jalchar",) * 2, 4: ("Vanchar",) * 2, 5: ("Manav",) * 2,
           6: ("Manav",) * 2, 7: ("Keet",) * 2, 8: ("Manav", "Chatushpad"),
           9: ("Chatushpad", "Jalchar"), 10: ("Manav",) * 2, 11: ("Jalchar",) * 2}
# Naam akshar: 4 syllables per nakshatra (pada 1..4), traditional Hoda Chakra.
_AKSHAR = [
    "Chu Che Cho La", "Li Lu Le Lo", "A I U E", "O Va Vi Vu", "Ve Vo Ka Ki",
    "Ku Gha Ng Chha", "Ke Ko Ha Hi", "Hu He Ho Da", "Di Du De Do", "Ma Mi Mu Me",
    "Mo Ta Ti Tu", "Te To Pa Pi", "Pu Sha Na Tha", "Pe Po Ra Ri", "Ru Re Ro Ta",
    "Ti Tu Te To", "Na Ni Nu Ne", "No Ya Yi Yu", "Ye Yo Bha Bhi", "Bhu Dha Pha Dha",
    "Bhe Bho Ja Ji", "Ju Je Jo Gha", "Ga Gi Gu Ge", "Go Sa Si Su", "Se So Da Di",
    "Du Tha Jha Na", "De Do Cha Chi"]


def _utc(dt: datetime) -> datetime:
    return dt.astimezone(timezone.utc)


def _sid(name: str, dt_utc: datetime) -> float:
    return ephem.sidereal_lon(name, dt_utc)


def _sun_moon(dt_utc: datetime) -> tuple[float, float]:
    return ephem.sidereal_lon("Sun", dt_utc), ephem.sidereal_lon("Moon", dt_utc)


def _elong(dt_utc):
    s, m = _sun_moon(dt_utc)
    return (m - s) % 360.0


def _yoga_sum(dt_utc):
    s, m = _sun_moon(dt_utc)
    return (s + m) % 360.0


def _moon(dt_utc):
    return _sid("Moon", dt_utc)


def _index(fn, span, dt):
    return int(fn(dt) // span)


def _next_boundary(fn, span: float, start: datetime, step_h: float = 2.0,
                   max_days: float = 3.0) -> datetime | None:
    """First instant after *start* where floor(fn/span) changes (bisection to ~1 s)."""
    i0 = _index(fn, span, start)
    t = start
    end = start + timedelta(days=max_days)
    while t < end:
        t2 = t + timedelta(hours=step_h)
        if _index(fn, span, t2) != i0:
            lo, hi = t, t2
            while (hi - lo).total_seconds() > 1:
                mid = lo + (hi - lo) / 2
                if _index(fn, span, mid) == i0:
                    lo = mid
                else:
                    hi = mid
            return hi
        t = t2
    return None


def _prev_boundary(fn, span, start, step_h=2.0, max_days=3.0):
    i0 = _index(fn, span, start)
    t = start
    end = start - timedelta(days=max_days)
    while t > end:
        t2 = t - timedelta(hours=step_h)
        if _index(fn, span, t2) != i0:
            lo, hi = t2, t
            while (hi - lo).total_seconds() > 1:
                mid = lo + (hi - lo) / 2
                if _index(fn, span, mid) == i0:
                    hi = mid
                else:
                    lo = mid
            return hi
        t = t2
    return None


def sun_rise_set(date_local: datetime, lat: float, lon: float, tz_hours: float):
    """Sunrise and sunset (local, tz-aware) for the civil date of *date_local*."""
    from skyfield import almanac
    from skyfield.api import wgs84
    ts, eph = ephem._load()
    tz = timezone(timedelta(hours=tz_hours))
    day0 = datetime(date_local.year, date_local.month, date_local.day, tzinfo=tz)
    t0 = ts.from_datetime(day0)
    t1 = ts.from_datetime(day0 + timedelta(days=1))
    f = almanac.sunrise_sunset(eph, wgs84.latlon(lat, lon))
    times, events = almanac.find_discrete(t0, t1, f)
    rise = sset = None
    for t, e in zip(times, events):
        if e == 1 and rise is None:
            rise = t.utc_datetime().astimezone(tz)
        elif e == 0 and sset is None:
            sset = t.utc_datetime().astimezone(tz)
    return rise, sset


@dataclass
class Panchang:
    vara: str
    vara_lord: str
    tithi: str
    tithi_hi: str
    paksha: str
    tithi_end: str
    nakshatra: str
    nakshatra_hi: str
    nakshatra_pada: int
    nakshatra_lord: str
    nakshatra_end: str
    yoga: str
    yoga_end: str
    karana: str
    karana_end: str
    sunrise: str
    sunset: str
    day_length: str
    masa_amanta: str
    masa_purnimanta: str
    vikram_samvat: int
    shaka_samvat: int
    ayanamsa: str
    ayanamsa_value: str
    avakhada: dict = field(default_factory=dict)
    rahu_kalam: str = "-"
    yamaganda: str = "-"
    gulika_kalam: str = "-"
    abhijit_muhurta: str = "-"
    brahma_muhurta: str = "-"
    pratah_sandhya: str = "-"
    vijaya_muhurta: str = "-"
    godhuli_muhurta: str = "-"
    sayahna_sandhya: str = "-"
    amrit_kalam: str = "-"
    nishita_muhurta: str = "-"
    chaughadiya_day: list = field(default_factory=list)
    chaughadiya_night: list = field(default_factory=list)
    horas_day: list = field(default_factory=list)
    horas_night: list = field(default_factory=list)

    def as_dict(self):
        return asdict(self)


def get_muhurta_and_chaughadiya(date_local, lat: float = 28.6139, lon: float = 77.2090, tz_hours: float = 5.5) -> dict:
    """Computes exact location-based Rahu Kaal, Yamaganda, Gulika, Abhijit and 8-period Day & Night Chaughadiyas."""
    from datetime import date as d_date
    try:
        lat = float(lat) if lat is not None else 28.6139
    except Exception:
        lat = 28.6139
    try:
        lon = float(lon) if lon is not None else 77.2090
    except Exception:
        lon = 77.2090
    try:
        tz_hours = float(tz_hours) if tz_hours is not None else 5.5
    except Exception:
        tz_hours = 5.5

    tz = timezone(timedelta(hours=tz_hours))
    # Normalize input whether passed as date, naive datetime or aware datetime
    if isinstance(date_local, datetime):
        if date_local.tzinfo is None:
            dt_eval = date_local.replace(tzinfo=tz)
        else:
            dt_eval = date_local.astimezone(tz)
    elif isinstance(date_local, d_date):
        dt_eval = datetime(date_local.year, date_local.month, date_local.day, 12, 0, 0, tzinfo=tz)
    else:
        dt_eval = datetime.now(tz)

    try:
        rise, sset = sun_rise_set(dt_eval, lat, lon, tz_hours)
    except Exception:
        rise = sset = None

    if rise is None or sset is None:
        return {
            "sunrise": "-", "sunset": "-",
            "rahu_kalam": "-", "yamaganda": "-", "gulika_kalam": "-", "abhijit_muhurta": "-",
            "muhurtas": {"rahu_kaal": "-", "yamaganda": "-", "gulika": "-", "abhijit": "-"},
            "chaughadiya_day": [], "chaughadiya_night": [],
            "day_chaughadiya": [], "night_chaughadiya": [],
            "horas_day": [], "horas_night": []
        }

    # In Vedic astronomy, a day begins at sunrise.
    # If dt_eval is before sunrise, the current operational cycle belongs to yesterday's sunrise.
    if dt_eval < rise:
        prev_day = dt_eval - timedelta(days=1)
        prev_rise, prev_sset = sun_rise_set(prev_day, lat, lon, tz_hours)
        if prev_rise and prev_sset:
            next_rise = rise
            rise, sset = prev_rise, prev_sset
            vara_date = prev_day
        else:
            next_rise = rise
            vara_date = dt_eval - timedelta(days=1)
    else:
        # Next day sunrise for accurate night division
        next_day = dt_eval + timedelta(days=1)
        next_rise, _ = sun_rise_set(next_day, lat, lon, tz_hours)
        if next_rise is None:
            next_rise = sset + timedelta(hours=12)
        vara_date = dt_eval

    day_secs = (sset - rise).total_seconds()
    day_part = day_secs / 8.0
    night_secs = (next_rise - sset).total_seconds()
    night_part = night_secs / 8.0

    # Hindu vara: 0=Sunday, 1=Monday, 2=Tuesday, 3=Wednesday, 4=Thursday, 5=Friday, 6=Saturday
    wd = (vara_date.weekday() + 1) % 7

    # Classical 8-part daytime indices (0-indexed):
    # Rahu Kaal: Sun=7 (8th part), Mon=1 (2nd), Tue=6 (7th), Wed=4 (5th), Thu=5 (6th), Fri=3 (4th), Sat=2 (3rd)
    rahu_parts = {0: 7, 1: 1, 2: 6, 3: 4, 4: 5, 5: 3, 6: 2}
    yamaganda_parts = {0: 4, 1: 3, 2: 2, 3: 1, 4: 0, 5: 6, 6: 5}
    gulika_parts = {0: 6, 1: 5, 2: 4, 3: 3, 4: 2, 5: 1, 6: 0}

    r_idx = rahu_parts[wd]
    y_idx = yamaganda_parts[wd]
    g_idx = gulika_parts[wd]

    def _fmt_span(start_dt, end_dt):
        return f"{start_dt.strftime('%I:%M %p')} - {end_dt.strftime('%I:%M %p')}"

    rahu_str = _fmt_span(rise + timedelta(seconds=r_idx * day_part), rise + timedelta(seconds=(r_idx + 1) * day_part))
    yama_str = _fmt_span(rise + timedelta(seconds=y_idx * day_part), rise + timedelta(seconds=(y_idx + 1) * day_part))
    guli_str = _fmt_span(rise + timedelta(seconds=g_idx * day_part), rise + timedelta(seconds=(g_idx + 1) * day_part))

    # Classical 30 Muhurtas (15 Day + 15 Night):
    # Day Muhurta length = day_secs / 15.0
    # Night Muhurta length = night_secs / 15.0
    d_muhurta = day_secs / 15.0
    n_muhurta = night_secs / 15.0

    # 1. Brahma Muhurta: 2 Muhurtas before sunrise (14th Muhurta of night = sunrise - 96 min to sunrise - 48 min)
    brahma_s = rise - timedelta(seconds=2 * n_muhurta)
    brahma_e = rise - timedelta(seconds=1 * n_muhurta)
    brahma_str = _fmt_span(brahma_s, brahma_e)

    # 2. Pratah Sandhya: 1 Muhurta before sunrise until sunrise
    pratah_sandhya_str = _fmt_span(rise - timedelta(seconds=1 * n_muhurta), rise)

    # 3. Abhijit Muhurta: 8th Muhurta of the day (day length / 15 * 7th to 8th)
    # शास्त्रोक्त प्रमाण (मुहूर्त चिंतामणि):
    # 'बुधेऽभिजित्प्रदोषोऽस्ति' अर्थात् बुधवार को अभिजीत मुहूर्त सर्वथा अनुपस्थित/अमान्य होता है।
    if wd == 3:
        abhijit_str = "कोई नहीं (बुधवार को अभिजीत मुहूर्त नहीं होता)"
    else:
        abhijit_s = rise + timedelta(seconds=7 * d_muhurta)
        abhijit_e = rise + timedelta(seconds=8 * d_muhurta)
        abhijit_str = _fmt_span(abhijit_s, abhijit_e)

    # 4. Vijaya Muhurta: 11th Muhurta of the day (day length / 15 * 10th to 11th)
    vijaya_s = rise + timedelta(seconds=10 * d_muhurta)
    vijaya_e = rise + timedelta(seconds=11 * d_muhurta)
    vijaya_str = _fmt_span(vijaya_s, vijaya_e)

    # 5. Godhuli Muhurta: 24 minutes around sunset (sunset - 12m to sunset + 12m)
    godhuli_s = sset - timedelta(minutes=12)
    godhuli_e = sset + timedelta(minutes=12)
    godhuli_str = _fmt_span(godhuli_s, godhuli_e)

    # 6. Sayahna Sandhya: sunset to 1 Muhurta after sunset
    sayahna_str = _fmt_span(sset, sset + timedelta(seconds=1 * n_muhurta))

    # 7. Amrit Kalam: 12th Muhurta of the day
    amrit_kalam_s = rise + timedelta(seconds=11 * d_muhurta)
    amrit_kalam_e = rise + timedelta(seconds=12 * d_muhurta)
    amrit_kalam_str = _fmt_span(amrit_kalam_s, amrit_kalam_e)

    # 8. Nishita Muhurta: 8th Muhurta of night (midnight apex: night length / 15 * 7th to 8th)
    nishita_s = sset + timedelta(seconds=7 * n_muhurta)
    nishita_e = sset + timedelta(seconds=8 * n_muhurta)
    nishita_str = _fmt_span(nishita_s, nishita_e)

    # 7 Chaughadiya types: Udveg (Sun), Char (Ven), Labh (Mer), Amrit (Moon), Kaal (Sat), Shubh (Jup), Rog (Mars)
    # Cycle order: Udveg -> Char -> Labh -> Amrit -> Kaal -> Shubh -> Rog
    # Rules: Shubh, Labh, Amrit, Char = Green (#10b981)
    # Udveg, Kaal, Rog = Red (#ef4444)
    ch_names = [
        {"name": "Udveg", "name_hi": "उद्वेग", "nature": "अशुभ (Sun)", "color": "#ef4444", "is_good": False},
        {"name": "Char", "name_hi": "चल", "nature": "शुभ / चर (Ven)", "color": "#10b981", "is_good": True},
        {"name": "Labh", "name_hi": "लाभ", "nature": "अति शुभ (Mer)", "color": "#10b981", "is_good": True},
        {"name": "Amrit", "name_hi": "अमृत", "nature": "सर्वश्रेष्ठ (Moon)", "color": "#10b981", "is_good": True},
        {"name": "Kaal", "name_hi": "काल", "nature": "अशुभ / काल (Sat)", "color": "#ef4444", "is_good": False},
        {"name": "Shubh", "name_hi": "शुभ", "nature": "उत्तम / शुभ (Jup)", "color": "#10b981", "is_good": True},
        {"name": "Rog", "name_hi": "रोग", "nature": "अशुभ / रोग (Mars)", "color": "#ef4444", "is_good": False}
    ]
    # -------------------------------------------------------------------------
    # EXPLICIT 7-DAY FIXED ARRAYS (शास्त्रीय 7 वारों का निर्धारित क्रम - सूर्योदय से सूर्यास्त एवं सूर्यास्त से सूर्योदय)
    # -------------------------------------------------------------------------
    # Day Chaughadiya sequence (सूर्योदय से सूर्यास्त):
    # रविवार: उद्वेग -> चर -> लाभ -> अमृत -> काल -> शुभ -> रोग -> उद्वेग
    # सोमवार: अमृत -> काल -> शुभ -> रोग -> उद्वेग -> चर -> लाभ -> अमृत
    # मंगलवार: रोग -> उद्वेग -> चर -> लाभ -> अमृत -> काल -> शुभ -> रोग
    # बुधवार: लाभ -> अमृत -> काल -> शुभ -> रोग -> उद्वेग -> चर -> लाभ
    # गुरुवार: शुभ -> रोग -> उद्वेग -> चर -> लाभ -> अमृत -> काल -> शुभ
    # शुक्रवार: चर -> लाभ -> अमृत -> काल -> शुभ -> रोग -> उद्वेग -> चर
    # शनिवार: काल -> शुभ -> रोग -> उद्वेग -> चर -> लाभ -> अमृत -> काल
    CHAUGHADIYA_7_DAYS_DAY = {
        0: ["Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg"],
        1: ["Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit"],
        2: ["Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog"],
        3: ["Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh"],
        4: ["Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal", "Shubh"],
        5: ["Char", "Labh", "Amrit", "Kaal", "Shubh", "Rog", "Udveg", "Char"],
        6: ["Kaal", "Shubh", "Rog", "Udveg", "Char", "Labh", "Amrit", "Kaal"]
    }

    # Night Chaughadiya sequence (सूर्यास्त से अगले सूर्योदय):
    # रविवार: शुभ -> अमृत -> चर -> रोग -> काल -> लाभ -> उद्वेग -> शुभ
    # सोमवार: चल (चर) -> रोग -> काल -> लाभ -> उद्वेग -> शुभ -> अमृत -> चल
    # मंगलवार: काल -> लाभ -> उद्वेग -> शुभ -> अमृत -> चल -> रोग -> काल
    # बुधवार: उद्वेग -> शुभ -> अमृत -> चल -> रोग -> काल -> लाभ -> उद्वेग
    # गुरुवार: अमृत -> चल -> रोग -> काल -> लाभ -> उद्वेग -> शुभ -> अमृत
    # शुक्रवार: रोग -> काल -> लाभ -> उद्वेग -> शुभ -> अमृत -> चल -> रोग
    # शनिवार: लाभ -> उद्वेग -> शुभ -> अमृत -> चल -> रोग -> काल -> लाभ
    CHAUGHADIYA_7_DAYS_NIGHT = {
        0: ["Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh"],
        1: ["Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char"],
        2: ["Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal"],
        3: ["Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg"],
        4: ["Amrit", "Char", "Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit"],
        5: ["Rog", "Kaal", "Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog"],
        6: ["Labh", "Udveg", "Shubh", "Amrit", "Char", "Rog", "Kaal", "Labh"]
    }

    ch_meta = {
        "Udveg": {"name": "Udveg", "name_hi": "उद्वेग", "nature": "अशुभ (Sun)", "color": "#ef4444", "is_good": False},
        "Char": {"name": "Char", "name_hi": "चल", "nature": "शुभ / चर (Ven)", "color": "#10b981", "is_good": True},
        "Labh": {"name": "Labh", "name_hi": "लाभ", "nature": "अति शुभ (Mer)", "color": "#10b981", "is_good": True},
        "Amrit": {"name": "Amrit", "name_hi": "अमृत", "nature": "सर्वश्रेष्ठ (Moon)", "color": "#10b981", "is_good": True},
        "Kaal": {"name": "Kaal", "name_hi": "काल", "nature": "अशुभ / काल (Sat)", "color": "#ef4444", "is_good": False},
        "Shubh": {"name": "Shubh", "name_hi": "शुभ", "nature": "उत्तम / शुभ (Jup)", "color": "#10b981", "is_good": True},
        "Rog": {"name": "Rog", "name_hi": "रोग", "nature": "अशुभ / रोग (Mars)", "color": "#ef4444", "is_good": False}
    }

    day_sequence = CHAUGHADIYA_7_DAYS_DAY[wd]
    night_sequence = CHAUGHADIYA_7_DAYS_NIGHT[wd]

    day_ch = []
    for i in range(8):
        c_key = day_sequence[i]
        c_obj = ch_meta[c_key]
        c_s = rise + timedelta(seconds=i * day_part)
        c_e = rise + timedelta(seconds=(i + 1) * day_part)
        day_ch.append({
            "name": c_obj["name"],
            "name_hi": c_obj["name_hi"],
            "nature": c_obj["nature"],
            "color": c_obj["color"],
            "is_good": c_obj["is_good"],
            "start": c_s.strftime("%I:%M %p"),
            "end": c_e.strftime("%I:%M %p")
        })

    night_ch = []
    for i in range(8):
        c_key = night_sequence[i]
        c_obj = ch_meta[c_key]
        c_s = sset + timedelta(seconds=i * night_part)
        c_e = sset + timedelta(seconds=(i + 1) * night_part)
        night_ch.append({
            "name": c_obj["name"],
            "name_hi": c_obj["name_hi"],
            "nature": c_obj["nature"],
            "color": c_obj["color"],
            "is_good": c_obj["is_good"],
            "start": c_s.strftime("%I:%M %p"),
            "end": c_e.strftime("%I:%M %p")
        })

    # -------------------------------------------------------------------------
    # 24 PLANETARY HORAS (12 दिन की होरा + 12 रात्रि की होरा - 7 वारों का नियत क्रम)
    # -------------------------------------------------------------------------
    # प्रथम होरा सदैव वार स्वामी की होती है, उसके बाद काल्डीयन अवरोही क्रम (Surya -> Shukra -> Budh -> Chandra -> Shani -> Guru -> Mangal)
    hora_planets_info = {
        "Sun": {"lord": "Sun", "lord_hi": "सूर्य", "nature": "तेजस्वी / मध्यम", "color": "#f59e0b"},
        "Venus": {"lord": "Venus", "lord_hi": "शुक्र", "nature": "शुभ / सौम्य", "color": "#10b981"},
        "Mercury": {"lord": "Mercury", "lord_hi": "बुध", "nature": "शुभ / बुद्धिप्रद", "color": "#10b981"},
        "Moon": {"lord": "Moon", "lord_hi": "चन्द्र", "nature": "शुभ / शांतिप्रद", "color": "#10b981"},
        "Saturn": {"lord": "Saturn", "lord_hi": "शनि", "nature": "क्रूर / सावधान", "color": "#ef4444"},
        "Jupiter": {"lord": "Jupiter", "lord_hi": "गुरु", "nature": "अति शुभ / ज्ञान", "color": "#10b981"},
        "Mars": {"lord": "Mars", "lord_hi": "मंगल", "nature": "उग्र / मध्यम", "color": "#ef4444"}
    }
    
    chaldean_cycle = ["Sun", "Venus", "Mercury", "Moon", "Saturn", "Jupiter", "Mars"]
    # Day 1st Hora: Sun=0 (Sun), Mon=3 (Moon), Tue=6 (Mars), Wed=2 (Mercury), Thu=5 (Jupiter), Fri=1 (Venus), Sat=4 (Saturn)
    first_hora_offset = {0: 0, 1: 3, 2: 6, 3: 2, 4: 5, 5: 1, 6: 4}
    start_h_idx = first_hora_offset[wd]

    hora_day_part = day_secs / 12.0
    hora_night_part = night_secs / 12.0

    day_horas = []
    for h in range(12):
        p_name = chaldean_cycle[(start_h_idx + h) % 7]
        h_info = hora_planets_info[p_name]
        h_s = rise + timedelta(seconds=h * hora_day_part)
        h_e = rise + timedelta(seconds=(h + 1) * hora_day_part)
        day_horas.append({
            "num": h + 1,
            "lord": h_info["lord"],
            "lord_hi": h_info["lord_hi"],
            "nature": h_info["nature"],
            "color": h_info["color"],
            "start": h_s.strftime("%I:%M %p"),
            "end": h_e.strftime("%I:%M %p")
        })

    night_horas = []
    for h in range(12):
        p_name = chaldean_cycle[(start_h_idx + 12 + h) % 7]
        h_info = hora_planets_info[p_name]
        h_s = sset + timedelta(seconds=h * hora_night_part)
        h_e = sset + timedelta(seconds=(h + 1) * hora_night_part)
        night_horas.append({
            "num": h + 1,
            "lord": h_info["lord"],
            "lord_hi": h_info["lord_hi"],
            "nature": h_info["nature"],
            "color": h_info["color"],
            "start": h_s.strftime("%I:%M %p"),
            "end": h_e.strftime("%I:%M %p")
        })

    return {
        "sunrise": rise.strftime("%I:%M %p"),
        "sunset": sset.strftime("%I:%M %p"),
        "rahu_kalam": rahu_str,
        "yamaganda": yama_str,
        "gulika_kalam": guli_str,
        "abhijit_muhurta": abhijit_str,
        "brahma_muhurta": brahma_str,
        "pratah_sandhya": pratah_sandhya_str,
        "vijaya_muhurta": vijaya_str,
        "godhuli_muhurta": godhuli_str,
        "sayahna_sandhya": sayahna_str,
        "amrit_kalam": amrit_kalam_str,
        "nishita_muhurta": nishita_str,
        "muhurtas": {
            "abhijit": abhijit_str,
            "brahma": brahma_str,
            "vijaya": vijaya_str,
            "godhuli": godhuli_str,
            "sayahna": sayahna_str,
            "amrit_kalam": amrit_kalam_str,
            "nishita": nishita_str,
            "rahu_kaal": rahu_str,
            "yamaganda": yama_str,
            "gulika": guli_str
        },
        "chaughadiya_day": day_ch,
        "chaughadiya_night": night_ch,
        "day_chaughadiya": day_ch,
        "night_chaughadiya": night_ch,
        "horas_day": day_horas,
        "horas_night": night_horas
    }


def _dms(x: float) -> str:
    d = int(x)
    m_f = (x - d) * 60
    m = int(m_f)
    s = int(round((m_f - m) * 60))
    if s == 60:
        m, s = m + 1, 0
    return f"{d:02d}°{m:02d}'{s:02d}\""


def karana_name(elong: float) -> str:
    k = int(elong // 6.0)          # 0..59
    if k == 0:
        return "Kimstughna"
    if k == 57:
        return "Shakuni"
    if k == 58:
        return "Chatushpada"
    if k == 59:
        return "Naga"
    return KARANA_MOVABLE[(k - 1) % 7]


def avakhada(moon_lon: float, asc_lon: float | None = None) -> dict:
    sign = int(moon_lon // 30)
    nak = int(moon_lon // C.NAKSHATRA_SPAN) % 27
    pada = int((moon_lon % C.NAKSHATRA_SPAN) // C.PADA_SPAN) + 1
    deg_in_sign = moon_lon % 30
    out = {
        "Varna": _VARNA_BY_SIGN[sign] if sign % 4 != 3 else "Brahmin",
        "Vashya": _VASHYA[sign][0 if deg_in_sign < 15 else 1],
        "Yoni": _YONI[nak],
        "Gana": _GANA[nak],
        "Nadi": _NADI_CYCLE[nak % 6],
        "Tatva": _TATVA_BY_SIGN[sign],
        "Rashi": C.SIGNS[sign],
        "Rashi Lord": C.SIGN_LORD[sign],
        "Nakshatra": f"{C.NAKSHATRAS[nak]} - {pada}",
        "Nakshatra Lord": C.VIMSHOTTARI_ORDER[nak % 9],
        "Naam Akshar": _AKSHAR[nak].split()[pada - 1],
    }
    if asc_lon is not None:
        a = int(asc_lon // 30)
        out["Lagna"] = C.SIGNS[a]
        out["Lagna Lord"] = C.SIGN_LORD[a]
    return out


def compute(dt_local, lat: float, lon: float, tz_hours: float,
            asc_lon: float | None = None) -> Panchang:
    """Full panchang for a tz-aware or naive local datetime or date with exact location-based Chaughadiyas & Rahu Kaal."""
    from datetime import date as d_date
    tz = timezone(timedelta(hours=tz_hours))
    if isinstance(dt_local, datetime):
        if dt_local.tzinfo is None:
            dt_local = dt_local.replace(tzinfo=tz)
    elif isinstance(dt_local, d_date):
        dt_local = datetime(dt_local.year, dt_local.month, dt_local.day, 12, 0, 0, tzinfo=tz)
    else:
        dt_local = datetime.now(tz)
    dt_u = _utc(dt_local)

    rise, sset = sun_rise_set(dt_local, lat, lon, tz_hours)
    # Hindu day starts at sunrise; before sunrise belongs to the previous vara.
    vara_date = dt_local if (rise is None or dt_local >= rise) else dt_local - timedelta(days=1)
    wd = (vara_date.weekday() + 1) % 7         # Python Mon=0 -> Sun=0

    e = _elong(dt_u)
    t_idx = int(e // 12.0)
    paksha = "Shukla" if t_idx < 15 else "Krishna"
    tn = t_idx % 15
    tithi = "Amavasya" if t_idx == 29 else TITHIS[tn]
    tithi_hi = "अमावस्या" if t_idx == 29 else TITHIS_HI[tn]

    moon = _moon(dt_u)
    nak = int(moon // C.NAKSHATRA_SPAN) % 27
    pada = int((moon % C.NAKSHATRA_SPAN) // C.PADA_SPAN) + 1
    y = int(_yoga_sum(dt_u) // C.NAKSHATRA_SPAN) % 27

    def fmt(t):
        return t.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S") if t else "-"

    t_end = _next_boundary(_elong, 12.0, dt_u)
    n_end = _next_boundary(_moon, C.NAKSHATRA_SPAN, dt_u)
    y_end = _next_boundary(_yoga_sum, C.NAKSHATRA_SPAN, dt_u)
    k_end = _next_boundary(_elong, 6.0, dt_u)

    # Lunar month: Sun's sidereal sign at the preceding new moon (Amanta).
    nm = _prev_boundary(_elong, 360.0, dt_u, step_h=12.0, max_days=31.0) or dt_u
    sun_sign_nm = int(_sid("Sun", nm) // 30)
    masa = (sun_sign_nm + 1) % 12
    masa_p = (masa + 1) % 12 if paksha == "Krishna" else masa

    yr = dt_local.year
    # New samvat begins at Chaitra Shukla Pratipada.
    before_new_year = dt_local.month <= 4 and masa in (9, 10, 11)
    vs = yr + (56 if before_new_year else 57)
    shaka = yr - (79 if before_new_year else 78)

    day_len = (sset - rise) if (rise and sset) else None
    jd = ephem._t(dt_u).tt

    muh_ch = get_muhurta_and_chaughadiya(dt_local, lat, lon, tz_hours)

    return Panchang(
        vara=VARAS[wd], vara_lord=VARA_LORD[wd],
        tithi=f"{paksha} {tithi}", tithi_hi=tithi_hi, paksha=paksha, tithi_end=fmt(t_end),
        nakshatra=C.NAKSHATRAS[nak], nakshatra_hi=C.NAKSHATRAS_HI[nak],
        nakshatra_pada=pada, nakshatra_lord=C.VIMSHOTTARI_ORDER[nak % 9],
        nakshatra_end=fmt(n_end),
        yoga=YOGAS[y], yoga_end=fmt(y_end),
        karana=karana_name(e), karana_end=fmt(k_end),
        sunrise=rise.strftime("%H:%M:%S") if rise else "-",
        sunset=sset.strftime("%H:%M:%S") if sset else "-",
        day_length=str(day_len).split(".")[0] if day_len else "-",
        masa_amanta=MASAS[masa], masa_purnimanta=MASAS[masa_p],
        vikram_samvat=vs, shaka_samvat=shaka,
        ayanamsa=ephem.AYANAMSA_NAME, ayanamsa_value=_dms(ephem.ayanamsa_deg(jd)),
        avakhada=avakhada(moon, asc_lon),
        rahu_kalam=muh_ch["rahu_kalam"],
        yamaganda=muh_ch["yamaganda"],
        gulika_kalam=muh_ch["gulika_kalam"],
        abhijit_muhurta=muh_ch["abhijit_muhurta"],
        brahma_muhurta=muh_ch.get("brahma_muhurta", "-"),
        pratah_sandhya=muh_ch.get("pratah_sandhya", "-"),
        vijaya_muhurta=muh_ch.get("vijaya_muhurta", "-"),
        godhuli_muhurta=muh_ch.get("godhuli_muhurta", "-"),
        sayahna_sandhya=muh_ch.get("sayahna_sandhya", "-"),
        amrit_kalam=muh_ch.get("amrit_kalam", "-"),
        nishita_muhurta=muh_ch.get("nishita_muhurta", "-"),
        chaughadiya_day=muh_ch["chaughadiya_day"],
        chaughadiya_night=muh_ch["chaughadiya_night"],
        horas_day=muh_ch.get("horas_day", []),
        horas_night=muh_ch.get("horas_night", [])
    )
