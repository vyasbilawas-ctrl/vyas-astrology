from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Optional

from vyas import constants

@dataclass(frozen=True)
class PlanetState:
    name: str
    longitude: float
    speed: float
    
    @property
    def sign_index(self) -> int:
        return int(self.longitude // 30.0) % 12
        
    @property
    def sign_name(self) -> str:
        return constants.SIGNS[self.sign_index]
        
    @property
    def sign_lord(self) -> str:
        return constants.SIGN_LORD[self.sign_index]
        
    @property
    def nakshatra_index(self) -> int:
        return int(self.longitude // constants.NAKSHATRA_SPAN) % 27
        
    @property
    def nakshatra_name(self) -> str:
        return constants.NAKSHATRAS[self.nakshatra_index]
        
    @property
    def nakshatra_lord(self) -> str:
        # The lords follow Vimshottari order starting from Ketu for Ashwini (index 0)
        return constants.VIMSHOTTARI_ORDER[self.nakshatra_index % 9]
        
    @property
    def pada(self) -> int:
        # Pada is 1 to 4
        return int((self.longitude % constants.NAKSHATRA_SPAN) // constants.PADA_SPAN) + 1
        
    @property
    def is_retrograde(self) -> bool:
        return self.speed < 0 and self.name not in ("Rahu", "Ketu")
        
    def d9_sign(self) -> int:
        """Calculates the Navamsha (D9) sign index."""
        # 1 pada = 1 navamsha. Total 108 navamshas in 360 deg.
        # Ashwini 1st pada is Aries. Ashwini 2nd pada is Taurus...
        total_padas = int(self.longitude // constants.PADA_SPAN)
        # Signs cycle every 12 padas. Aries starts at 0.
        return total_padas % 12
        
    def d10_sign(self) -> int:
        """Calculates the Dashamsha (D10) sign index.
        Parashara: For odd signs, start from the sign itself.
        For even signs, start from the 9th house from it.
        """
        deg_in_sign = self.longitude % 30.0
        part = int(deg_in_sign // 3.0) # 0 to 9
        if self.sign_index % 2 == 0:
            # Odd sign (0=Aries, 2=Gemini, etc.)
            return (self.sign_index + part) % 12
        else:
            # Even sign (1=Taurus, etc.), start from 9th
            return (self.sign_index + 8 + part) % 12


@dataclass(frozen=True)
class HouseState:
    house_num: int # 1 to 12
    sign_index: int
    
    @property
    def sign_name(self) -> str:
        return constants.SIGNS[self.sign_index]
        
    @property
    def lord(self) -> str:
        return constants.SIGN_LORD[self.sign_index]

@dataclass
class Chart:
    ascendant_longitude: float
    planets: Dict[str, PlanetState]
    
    @property
    def ascendant_sign(self) -> int:
        return int(self.ascendant_longitude // 30.0) % 12
        
    @property
    def ascendant_nakshatra(self) -> int:
        return int(self.ascendant_longitude // constants.NAKSHATRA_SPAN) % 27
        
    @property
    def ascendant_pada(self) -> int:
        return int((self.ascendant_longitude % constants.NAKSHATRA_SPAN) // constants.PADA_SPAN) + 1
        
    def get_whole_sign_houses(self) -> Dict[int, HouseState]:
        """Returns houses 1-12 mapped to their signs using Whole Sign Houses."""
        houses = {}
        asc_sign = self.ascendant_sign
        for h in range(1, 13):
            sign_idx = (asc_sign + h - 1) % 12
            houses[h] = HouseState(house_num=h, sign_index=sign_idx)
        return houses
        
    def get_house_of_planet(self, planet_name: str) -> int:
        """Returns the house number (1-12) of a planet using Whole Sign Houses."""
        p_sign = self.planets[planet_name].sign_index
        asc_sign = self.ascendant_sign
        return (p_sign - asc_sign + 12) % 12 + 1
        
    def get_planets_in_house(self, house_num: int) -> List[str]:
        return [p.name for p in self.planets.values() if self.get_house_of_planet(p.name) == house_num]

    def get_houses_ruled_by_planet(self, planet_name: str) -> List[int]:
        """Returns the house numbers (1-12) ruled by the given planet."""
        asc_sign = self.ascendant_sign
        ruled = []
        for h in range(1, 13):
            sign_idx = (asc_sign + h - 1) % 12
            if constants.SIGN_LORD[sign_idx] == planet_name:
                ruled.append(h)
        return ruled

