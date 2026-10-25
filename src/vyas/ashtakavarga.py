"""Ashtakavarga Engine (BPHS Standards).

Computes:
1. Bhinnashtakavarga (BAV) for all 7 classical planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
   from 8 reference points (the 7 planets + Lagna).
2. Samudaya Ashtakavarga (SAV) summing all bindus across the 12 signs (Total = 337).
3. Trikona Shodhana (त्रिकोण शोधन - Trinal Reduction).
4. Ekadhipatya Shodhana (एकाधिपत्य शोधन - Dual-Lordship Reduction).
5. Shodhya Pinda (Rashi Pinda, Graha Pinda, and Total Shodhya Pinda).
6. Kakshya Division for Gochar transit timing.
"""
from typing import Dict, List, Tuple
from vyas import constants

# Classical BPHS Bindu Rules:
# For each planet (from 1 to 7), houses (1-12) from reference bodies that contribute 1 bindu.
BAV_RULES = {
    "Sun": {
        "Sun": [1, 2, 4, 7, 8, 9, 10, 11],
        "Moon": [3, 6, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [5, 6, 9, 11],
        "Venus": [6, 7, 12],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [3, 4, 6, 10, 11, 12]
    },
    "Moon": {
        "Sun": [3, 6, 7, 8, 10, 11],
        "Moon": [1, 3, 6, 7, 10, 11],
        "Mars": [2, 3, 5, 6, 9, 10, 11],
        "Mercury": [1, 3, 4, 5, 7, 8, 10, 11],
        "Jupiter": [1, 4, 7, 8, 10, 11, 12],
        "Venus": [3, 4, 5, 7, 9, 10, 11],
        "Saturn": [3, 5, 6, 11],
        "Lagna": [3, 6, 10, 11]
    },
    "Mars": {
        "Sun": [3, 5, 6, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [3, 5, 6, 11],
        "Jupiter": [6, 10, 11, 12],
        "Venus": [6, 8, 11, 12],
        "Saturn": [1, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 3, 6, 10, 11]
    },
    "Mercury": {
        "Sun": [5, 6, 9, 11, 12],
        "Moon": [2, 4, 6, 8, 10, 11],
        "Mars": [1, 2, 4, 7, 8, 9, 10, 11],
        "Mercury": [1, 3, 5, 6, 9, 10, 11, 12],
        "Jupiter": [6, 8, 11, 12],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 11],
        "Saturn": [1, 2, 4, 7, 8, 9, 10, 11],
        "Lagna": [1, 2, 4, 6, 8, 10, 11]
    },
    "Jupiter": {
        "Sun": [1, 2, 3, 4, 7, 8, 9, 10, 11],
        "Moon": [2, 5, 7, 9, 11],
        "Mars": [1, 2, 4, 7, 8, 10, 11],
        "Mercury": [1, 2, 4, 5, 6, 9, 10, 11],
        "Jupiter": [1, 2, 3, 4, 7, 8, 10, 11],
        "Venus": [2, 5, 6, 9, 10, 11],
        "Saturn": [3, 5, 6, 12],
        "Lagna": [1, 2, 4, 5, 6, 7, 9, 10, 11]
    },
    "Venus": {
        "Sun": [8, 11, 12],
        "Moon": [1, 2, 3, 4, 5, 8, 9, 11, 12],
        "Mars": [3, 5, 6, 9, 11, 12],
        "Mercury": [3, 5, 6, 9, 11],
        "Jupiter": [5, 8, 9, 10, 11],
        "Venus": [1, 2, 3, 4, 5, 8, 9, 10, 11],
        "Saturn": [3, 5, 8, 9, 10, 11],
        "Lagna": [1, 2, 3, 4, 5, 8, 9, 11]
    },
    "Saturn": {
        "Sun": [1, 2, 4, 7, 8, 10, 11],
        "Moon": [3, 6, 11],
        "Mars": [3, 5, 6, 10, 11, 12],
        "Mercury": [6, 8, 9, 10, 11, 12],
        "Jupiter": [5, 6, 11, 12],
        "Venus": [6, 11, 12],
        "Saturn": [3, 5, 6, 11],
        "Lagna": [1, 3, 4, 6, 10, 11]
    }
}

# Rashi Multipliers (Rashi Gunakara) for Shodhya Pinda:
# Aries: 7, Taurus: 10, Gemini: 8, Cancer: 4, Leo: 10, Virgo: 5,
# Libra: 7, Scorpio: 8, Sagittarius: 9, Capricorn: 5, Aquarius: 11, Pisces: 12
RASHI_GUNAKARA = [7, 10, 8, 4, 10, 5, 7, 8, 9, 5, 11, 12]

# Graha Multipliers (Graha Gunakara):
# Sun: 5, Moon: 5, Mars: 8, Mercury: 5, Jupiter: 10, Venus: 7, Saturn: 5
GRAHA_GUNAKARA = {
    "Sun": 5, "Moon": 5, "Mars": 8, "Mercury": 5, "Jupiter": 10, "Venus": 7, "Saturn": 5
}

def compute_ashtakavarga(planet_signs: Dict[str, int], asc_sign: int) -> dict:
    """
    Computes BAV, SAV, Trikona Shodhana, Ekadhipatya Shodhana, and Shodhya Pinda.
    planet_signs: Dict mapping planet name to sign index (0-11).
    asc_sign: Ascendant sign index (0-11).
    """
    ref_signs = dict(planet_signs)
    ref_signs["Lagna"] = asc_sign

    # 1. Bhinnashtakavarga (BAV) for 7 planets across 12 signs (0=Aries .. 11=Pisces)
    bav: Dict[str, List[int]] = {p: [0] * 12 for p in BAV_RULES}
    bav_detail: Dict[str, Dict[str, List[int]]] = {p: {} for p in BAV_RULES}

    for target_p, ref_dict in BAV_RULES.items():
        for ref_body, good_houses in ref_dict.items():
            ref_s = ref_signs[ref_body]
            bindu_row = [0] * 12
            for h in good_houses:
                target_s = (ref_s + h - 1) % 12
                bindu_row[target_s] = 1
                bav[target_p][target_s] += 1
            bav_detail[target_p][ref_body] = bindu_row

    # 2. Samudaya Ashtakavarga (SAV) = sum of all 7 BAVs per sign
    sav = [sum(bav[p][s] for p in BAV_RULES) for s in range(12)]

    # 3. Trikona Shodhana (Trinal Reductions)
    # Trines: (0, 4, 8), (1, 5, 9), (2, 6, 10), (3, 7, 11)
    trik_bav: Dict[str, List[int]] = {}
    for p in BAV_RULES:
        pts = list(bav[p])
        for trine_start in range(4):
            t_signs = [trine_start, trine_start + 4, trine_start + 8]
            min_val = min(pts[s] for s in t_signs)
            for s in t_signs:
                pts[s] -= min_val
        trik_bav[p] = pts

    # 4. Ekadhipatya Shodhana (Dual-Lordship Reductions)
    # Dual lords: Mars (0, 7), Venus (1, 6), Mercury (2, 5), Jupiter (8, 11), Saturn (9, 10)
    # Sun (4) and Moon (3) have single ownership.
    dual_pairs = [
        ("Mars", 0, 7),
        ("Venus", 1, 6),
        ("Mercury", 2, 5),
        ("Jupiter", 8, 11),
        ("Saturn", 9, 10)
    ]
    
    # Signs occupied by planets
    occupied_signs = set(planet_signs[p] for p in BAV_RULES)

    eka_bav: Dict[str, List[int]] = {}
    for p in BAV_RULES:
        pts = list(trik_bav[p])
        for lord, s1, s2 in dual_pairs:
            occ1 = s1 in occupied_signs
            occ2 = s2 in occupied_signs
            v1, v2 = pts[s1], pts[s2]

            if not occ1 and not occ2:
                # Neither sign occupied
                if v1 == v2:
                    pts[s1] = 0
                    pts[s2] = 0
                elif v1 > v2:
                    pts[s1] = v2
                else:
                    pts[s2] = pts[s1]
            elif occ1 and not occ2:
                # Sign 1 occupied, Sign 2 empty
                if v2 >= v1:
                    pts[s2] = 0
                else:
                    pts[s2] = 0
            elif not occ1 and occ2:
                # Sign 2 occupied, Sign 1 empty
                if v1 >= v2:
                    pts[s1] = 0
                else:
                    pts[s1] = 0
            else:
                # Both signs occupied: no reduction
                pass
        eka_bav[p] = pts

    # 5. Shodhya Pinda (Rashi Pinda + Graha Pinda)
    pindas: Dict[str, dict] = {}
    for p in BAV_RULES:
        reduced = eka_bav[p]
        # Rashi Pinda: sum(reduced[s] * RASHI_GUNAKARA[s])
        rashi_pinda = sum(reduced[s] * RASHI_GUNAKARA[s] for s in range(12))
        
        # Graha Pinda: for each planet, points in its sign * planet gunakara
        graha_pinda = 0
        for pl_name, g_gun in GRAHA_GUNAKARA.items():
            pl_s = planet_signs[pl_name]
            graha_pinda += reduced[pl_s] * g_gun
            
        total_pinda = rashi_pinda + graha_pinda
        pindas[p] = {
            "rashi_pinda": rashi_pinda,
            "graha_pinda": graha_pinda,
            "shodhya_pinda": total_pinda
        }

    return {
        "bav": bav,
        "bav_detail": bav_detail,
        "sav": sav,
        "trikona_shodhana": trik_bav,
        "ekadhipatya_shodhana": eka_bav,
        "pindas": pindas
    }
