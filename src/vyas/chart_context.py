"""ChartContext: Unified context object for deep chart synthesis.

Collects all relevant inputs (D1-D60, dasha up to PrD, KP, Ashtakavarga/Prasthara,
Shadbala/Bhavabala, Chalit, Jaimini, Panchang/Avakhada) into a single object
consumed by the Sutra Synthesizer.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from vyas import ashtakavarga
from vyas import astrosage_content
from vyas import chalit
from vyas import constants
from vyas import dasha
from vyas import forensic_predictor
from vyas import jaimini
from vyas import kp
from vyas import panchang
from vyas import shadbala
from vyas import varga


@dataclass
class PlanetCtx:
    name: str
    longitude: float
    sign_index: int
    sign: str
    sign_hi: str
    house: int  # D1 whole-sign
    house_chalit: int
    degree_in_sign: float
    nakshatra: str
    nakshatra_pada: int
    nakshatra_lord: str
    is_retrograde: bool
    is_combust: bool
    combust_diff: float
    speed: float
    dignity: Optional[forensic_predictor.PlanetDignity] = None


@dataclass
class ChartContext:
    birth: Dict[str, Any]
    chart: Any
    kp_cusps: List[Any]
    vargas_detailed: Dict[str, Any]

    planets: Dict[str, PlanetCtx] = field(default_factory=dict)
    asc_sign_idx: int = 0
    asc_lon: float = 0.0
    moon_lon: float = 0.0

    dignities: Dict[str, forensic_predictor.PlanetDignity] = field(default_factory=dict)
    bhavas: List[forensic_predictor.BhavaAnalysis] = field(default_factory=list)
    bhava_bala: Dict[int, float] = field(default_factory=dict)
    final_shadbala: Dict[str, Any] = field(default_factory=dict)

    bav: Dict[str, List[int]] = field(default_factory=dict)
    sav: List[int] = field(default_factory=list)
    prasthara: Dict[str, Any] = field(default_factory=dict)
    ashtaka_res: Dict[str, Any] = field(default_factory=dict)

    chalit_details: List[Any] = field(default_factory=list)
    chalit_houses: Dict[str, int] = field(default_factory=dict)

    kp_significators: Dict[str, Any] = field(default_factory=dict)
    ruling_planets: Dict[str, Any] = field(default_factory=dict)

    chara_karakas: List[Any] = field(default_factory=list)
    atmakaraka: Optional[str] = None
    karakamsha_sign: int = 0

    dasha_engine: Any = None
    running_dasha: Dict[str, Any] = field(default_factory=dict)

    panchang_obj: Any = None
    avakhada: Dict[str, Any] = field(default_factory=dict)
    aspect_matrix: Dict[str, List[int]] = field(default_factory=dict)
    yuti_groups: List[List[str]] = field(default_factory=list)
    drishti_matrix: Dict[str, Dict] = field(default_factory=dict)

    mangal_data: Dict[str, Any] = field(default_factory=dict)
    kalsarp_data: Dict[str, Any] = field(default_factory=dict)
    sade_sati_phases: List[Any] = field(default_factory=list)
    varshphal_data: Dict[str, Any] = field(default_factory=dict)

    all_bodies_lons: Dict[str, float] = field(default_factory=dict)

    @classmethod
    def build(cls, chart, birth: dict, kp_cusps: list, dasha_engine, vargas_detailed: dict, target_varsh_year: int = None) -> "ChartContext":
        ctx = cls(
            birth=birth,
            chart=chart,
            kp_cusps=kp_cusps,
            vargas_detailed=vargas_detailed,
            dasha_engine=dasha_engine,
        )

        ctx.asc_sign_idx = chart.ascendant_sign
        ctx.asc_lon = chart.ascendant_longitude
        ctx.moon_lon = chart.planets["Moon"].longitude

        ctx.dignities = forensic_predictor.analyze_all_planetary_dignities(chart, vargas_detailed)
        ctx.bhavas = forensic_predictor.analyze_all_12_bhavas(chart, ctx.dignities)
        ctx.mangal_data = forensic_predictor.compute_comprehensive_mangal_dosha(chart)
        ctx.kalsarp_data = forensic_predictor.compute_comprehensive_kalsarp(chart)
        ctx.sade_sati_phases = forensic_predictor.compute_comprehensive_sade_sati(birth['local'], ctx.moon_lon)

        birth_dt = birth['local']
        curr_dt = datetime.now()
        if target_varsh_year is None:
            if (curr_dt.month, curr_dt.day) < (birth_dt.month, birth_dt.day):
                target_varsh_year = curr_dt.year - 1
            else:
                target_varsh_year = curr_dt.year
        ctx.varshphal_data = forensic_predictor.compute_tajik_varshphal(birth_dt, chart.planets["Sun"].longitude, target_varsh_year, ctx.asc_sign_idx)

        p_signs = {p_name: p.sign_index for p_name, p in chart.planets.items()}
        ctx.ashtaka_res = ashtakavarga.compute_ashtakavarga(p_signs, ctx.asc_sign_idx)
        ctx.bav = ctx.ashtaka_res["bav"]
        ctx.sav = ctx.ashtaka_res["sav"]
        try:
            ctx.prasthara = astrosage_content.compute_full_prastharashtakvarga(p_signs, ctx.asc_sign_idx)
        except Exception:
            ctx.prasthara = {}

        _sun_house = (chart.planets["Sun"].sign_index - ctx.asc_sign_idx + 12) % 12 + 1
        _is_day_birth = 1 <= _sun_house <= 6
        _paksha = "Shukla" if ((ctx.moon_lon - chart.planets["Sun"].longitude) % 360.0) < 180.0 else "Krishna"
        ctx.final_shadbala, ctx.bhava_bala = shadbala.compute_shadbala(chart, _is_day_birth, _paksha)

        ctx.kp_significators = kp.compute_kp_significators(chart.planets, kp_cusps)
        try:
            ctx.ruling_planets = kp.get_ruling_planets(birth_dt, birth['lat'], birth['lon'], birth['tz'], ctx.moon_lon, ctx.asc_lon)
        except Exception:
            ctx.ruling_planets = {}

        _mc_lon = (ctx.asc_lon + 270.0) % 360.0
        try:
            ctx.chalit_details = chalit.compute_sripati_chalit(ctx.asc_lon, _mc_lon, {p: chart.planets[p].longitude for p in chart.planets})
            for cd in ctx.chalit_details:
                for pn in cd.planets_in_bhava:
                    ctx.chalit_houses[pn] = cd.bhava_num
        except Exception:
            ctx.chalit_details = []
            ctx.chalit_houses = {}

        try:
            ctx.chara_karakas, ctx.atmakaraka, ctx.karakamsha_sign = jaimini.compute_chara_karakas(chart.planets)
        except Exception:
            ctx.chara_karakas, ctx.atmakaraka, ctx.karakamsha_sign = [], None, 0

        try:
            ctx.panchang_obj = panchang.compute(birth_dt, birth['lat'], birth['lon'], birth['tz'], ctx.asc_lon)
            ctx.avakhada = getattr(ctx.panchang_obj, 'avakhada', {}) or {}
        except Exception:
            ctx.panchang_obj = None
            ctx.avakhada = {}

        try:
            ctx.running_dasha = dasha_engine.get_running_dasha(datetime.now(), max_depth=5)
        except Exception:
            ctx.running_dasha = {}

        for p_name, p in chart.planets.items():
            deg_in_sign = p.longitude % 30.0
            nak_idx = int(p.longitude // constants.NAKSHATRA_SPAN) % 27
            nak_name = constants.NAKSHATRAS[nak_idx]
            pada = int((p.longitude % constants.NAKSHATRA_SPAN) // constants.PADA_SPAN) + 1
            nak_lord = constants.VIMSHOTTARI_ORDER[nak_idx % 9]
            sign_name = constants.SIGNS[p.sign_index]
            sign_hi = constants.SIGNS_HI[p.sign_index] if hasattr(constants, 'SIGNS_HI') else sign_name
            h_d1 = (p.sign_index - ctx.asc_sign_idx + 12) % 12 + 1
            h_ch = ctx.chalit_houses.get(p_name, h_d1)
            is_combust, combust_diff = forensic_predictor.check_combustion(p_name, p.longitude, chart.planets["Sun"].longitude)
            ctx.planets[p_name] = PlanetCtx(
                name=p_name,
                longitude=p.longitude,
                sign_index=p.sign_index,
                sign=sign_name,
                sign_hi=sign_hi,
                house=h_d1,
                house_chalit=h_ch,
                degree_in_sign=deg_in_sign,
                nakshatra=nak_name,
                nakshatra_pada=pada,
                nakshatra_lord=nak_lord,
                is_retrograde=bool(getattr(p, 'is_retrograde', False)),
                is_combust=is_combust,
                combust_diff=combust_diff,
                speed=float(getattr(p, 'speed', 0.0)),
                dignity=ctx.dignities.get(p_name),
            )

        ctx.all_bodies_lons = {p: chart.planets[p].longitude for p in chart.planets}

        # Build unified relationship helpers
        try:
            ctx.aspect_matrix = cls._build_aspect_matrix(ctx)
        except Exception:
            ctx.aspect_matrix = {}
        try:
            ctx.yuti_groups = cls._build_yuti_groups(ctx)
        except Exception:
            ctx.yuti_groups = []
        try:
            ctx.drishti_matrix = cls._build_drishti_matrix(ctx)
        except Exception:
            ctx.drishti_matrix = {}

        return ctx

    @staticmethod
    def _build_aspect_matrix(ctx: "ChartContext") -> Dict[str, List[int]]:
        """Unified aspect matrix - houses aspected by each planet."""
        matrix = {}
        for p_name in ctx.planets:
            try:
                p_house = (ctx.planets[p_name].sign_index - ctx.asc_sign_idx + 12) % 12 + 1
                aspects = []
                for off in constants.ASPECTS.get(p_name, [7]):
                    target_h = (p_house + off - 2) % 12 + 1
                    aspects.append(target_h)
                matrix[p_name] = sorted(set(aspects))
            except Exception:
                matrix[p_name] = []
        return matrix

    @staticmethod
    def _build_yuti_groups(ctx: "ChartContext") -> List[List[str]]:
        """Planets in same sign grouped."""
        groups = defaultdict(list)
        for p_name, p in ctx.planets.items():
            groups[p.sign_index].append(p_name)
        return [g for g in groups.values() if len(g) >= 2]

    @staticmethod
    def _build_drishti_matrix(ctx: "ChartContext") -> Dict[str, Dict]:
        """Drishti matrix - who aspects whom."""
        matrix = {}
        aspect_matrix = ChartContext._build_aspect_matrix(ctx)
        for p_name, aspected_houses in aspect_matrix.items():
            matrix[p_name] = {"aspects_houses": aspected_houses, "aspects_planets": []}
            for other_p, other_p_ctx in ctx.planets.items():
                if other_p == p_name:
                    continue
                other_house = (other_p_ctx.sign_index - ctx.asc_sign_idx + 12) % 12 + 1
                if other_house in aspected_houses:
                    matrix[p_name]["aspects_planets"].append(other_p)
        return matrix
