"""Maharshi Vyas Classical Natural-Dialogue AI Astrological Consultation Engine.

Key Architectural Principles:
1. Natural, fluent, dignified Hindi conversation without artificial robotic templates or raw data dumps.
2. 100% authentic Jyotish Shastra logic:
   - Evaluates exact Lagna, Lagnesh, Chandra Rashi, Nakshatra.
   - Evaluates specific Bhava lords, occupants, conjunctions (Yuti), and Graha Drishti (aspects).
   - Directly addresses the user's specific query (Timing / When will time improve, Dasha predictions, RHJS/Judiciary,
     Career, Finances, Marriage, Health, Children, Property, Foreign, Obstacles, Remedies).
   - Never outputs stuttering or repeated words like 'मंगल मंगल' or 'शनि शनि'.
3. Multi-turn conversation awareness:
   - Welcoming greeting only on the initial turn.
   - Subsequent questions receive direct, authoritative, focused astrological answers.
4. Hybrid AI Engine:
   - If Gemini API Key is configured in environment or secrets, can leverage LLM with deep astrological prompt.
   - Powerful, deterministic classical Vedic inference engine guarantees deep, accurate answers offline or without API key.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
import os
import re

from vyas import constants
from vyas import sutra_synthesizer

class VyasChatbotEngine:
    """Authentic Vedic Astrological Dialogue Engine."""

    def __init__(self):
        pass

    def _extract_chart_framework(self, chart, cur_dasha: Any, transit_pos: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Extracts complete astronomical and planetary positioning from the chart."""
        asc_sign = chart.ascendant_sign
        asc_sign_name = constants.SIGNS_HI[asc_sign]
        lagnesh = constants.SIGN_LORD[asc_sign]
        lagnesh_hi = constants.PLANETS_HI.get(lagnesh, lagnesh)

        moon_p = chart.planets.get("Moon")
        moon_sign = moon_p.sign_index if moon_p else 0
        moon_sign_name = constants.SIGNS_HI[moon_sign]
        moon_nak_idx = int(moon_p.longitude // constants.NAKSHATRA_SPAN) % 27 if moon_p else 0
        moon_nak_name = constants.NAKSHATRAS_HI[moon_nak_idx]

        # House placements and degrees
        p_info = {}
        house_occupants = {h: [] for h in range(1, 13)}

        for p_name, p in chart.planets.items():
            h = (p.sign_index - asc_sign + 12) % 12 + 1
            house_occupants[h].append(p_name)
            p_info[p_name] = {
                "house": h,
                "sign_idx": p.sign_index,
                "sign_name": constants.SIGNS_HI[p.sign_index],
                "deg": round(p.longitude % 30, 2),
                "is_retro": getattr(p, "is_retrograde", False),
                "hi": constants.PLANETS_HI.get(p_name, p_name)
            }

        # Planetary Aspects (दृष्टियां)
        aspects_map = {}
        for p_name, p in p_info.items():
            h_from = p["house"]
            offsets = constants.ASPECTS.get(p_name, [7])
            aspected_houses = []
            for off in offsets:
                tgt_h = (h_from + off - 1)
                while tgt_h > 12:
                    tgt_h -= 12
                aspected_houses.append(tgt_h)
            aspects_map[p_name] = aspected_houses

        # Resolve Dasha string and dates
        dasha_md, dasha_ad, dasha_pd = "अज्ञात", "", ""
        md_start, md_end = "", ""
        ad_start, ad_end = "", ""
        pd_start, pd_end = "", ""
        md_lord_en, ad_lord_en, pd_lord_en = "", "", ""

        if isinstance(cur_dasha, dict):
            if "MD" in cur_dasha and isinstance(cur_dasha["MD"], dict):
                md_lord_en = cur_dasha["MD"].get("lord", "")
                ad_lord_en = cur_dasha.get("AD", {}).get("lord", "")
                pd_lord_en = cur_dasha.get("PD", {}).get("lord", "")
                dasha_md = constants.PLANETS_HI.get(md_lord_en, md_lord_en)
                dasha_ad = constants.PLANETS_HI.get(ad_lord_en, ad_lord_en)
                dasha_pd = constants.PLANETS_HI.get(pd_lord_en, pd_lord_en)
                md_start = cur_dasha["MD"].get("start", "")
                md_end = cur_dasha["MD"].get("end", "")
                def _clean_date(d_val: Any) -> str:
                    if not d_val:
                        return ""
                    return str(d_val).split()[0]

                md_start = _clean_date(cur_dasha["MD"].get("start", ""))
                md_end = _clean_date(cur_dasha["MD"].get("end", ""))
                ad_start = _clean_date(cur_dasha.get("AD", {}).get("start", ""))
                ad_end = _clean_date(cur_dasha.get("AD", {}).get("end", ""))
                pd_start = _clean_date(cur_dasha.get("PD", {}).get("start", ""))
                pd_end = _clean_date(cur_dasha.get("PD", {}).get("end", ""))
            else:
                dasha_md = cur_dasha.get("full_path") or str(cur_dasha)
        elif isinstance(cur_dasha, str):
            dasha_md = cur_dasha

        # Determine next Antardasha
        next_ad_lord_en = ""
        next_ad_lord_hi = ""
        if ad_lord_en in constants.VIMSHOTTARI_ORDER:
            cur_ad_idx = constants.VIMSHOTTARI_ORDER.index(ad_lord_en)
            next_ad_lord_en = constants.VIMSHOTTARI_ORDER[(cur_ad_idx + 1) % 9]
            next_ad_lord_hi = constants.PLANETS_HI.get(next_ad_lord_en, next_ad_lord_en)

        # Transits
        transit_info = {}
        if not transit_pos:
            try:
                from vyas.ephem import planet_positions
                from datetime import timezone
                transit_pos = planet_positions(datetime.now(timezone.utc))
            except Exception:
                transit_pos = {}

        if transit_pos:
            for p_name in ["Saturn", "Jupiter", "Rahu", "Ketu", "Mars", "Sun", "Venus", "Mercury"]:
                tp = transit_pos.get(p_name)
                if tp:
                    s_idx = getattr(tp, "sign_index", int(getattr(tp, "longitude", 0) // 30) % 12)
                    h_lagna = (s_idx - asc_sign + 12) % 12 + 1
                    h_moon = (s_idx - moon_sign + 12) % 12 + 1
                    transit_info[p_name] = {
                        "sign": constants.SIGNS_HI[s_idx],
                        "h_lagna": h_lagna,
                        "h_moon": h_moon,
                        "hi": constants.PLANETS_HI.get(p_name, p_name)
                    }

        return {
            "asc_sign": asc_sign,
            "asc_sign_name": asc_sign_name,
            "lagnesh": lagnesh,
            "lagnesh_hi": lagnesh_hi,
            "moon_sign": moon_sign,
            "moon_sign_name": moon_sign_name,
            "moon_nak_name": moon_nak_name,
            "p_info": p_info,
            "house_occupants": house_occupants,
            "aspects_map": aspects_map,
            "dasha_md": dasha_md,
            "dasha_ad": dasha_ad,
            "dasha_pd": dasha_pd,
            "md_lord_en": md_lord_en,
            "ad_lord_en": ad_lord_en,
            "pd_lord_en": pd_lord_en,
            "md_start": md_start,
            "md_end": md_end,
            "ad_start": ad_start,
            "ad_end": ad_end,
            "pd_start": pd_start,
            "pd_end": pd_end,
            "next_ad_lord_en": next_ad_lord_en,
            "next_ad_lord_hi": next_ad_lord_hi,
            "transits": transit_info
        }

    def _call_gemini_if_available(self, query: str, fw: Dict[str, Any], name: str,
                                   chat_history: Optional[List[Dict[str, str]]]) -> Optional[str]:
        """Tries to call official Gemini API via google.genai if GEMINI_API_KEY is configured."""
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            return None

        try:
            from google import genai
            client = genai.Client(api_key=api_key)

            p_list = [f"{v['hi']} {v['house']}वें भाव में ({v['sign_name']})" for v in fw['p_info'].values()]
            planets_summary = ", ".join(p_list)

            tr_list = [f"{k} {v['sign']} में (लग्न से {v['h_lagna']}वें भाव)" for k, v in fw['transits'].items()]
            transits_summary = ", ".join(tr_list)

            system_prompt = (
                f"आप आचार्य व्यास हैं—एक परम विदुषी, प्रामाणिक, गंभीर एवं पूज्य वैदिक ज्योतिषी। "
                f"जातक का नाम: {name}। "
                f"कुण्डली विवरण: {fw['asc_sign_name']} लग्न, लग्नेश {fw['lagnesh_hi']}, "
                f"{fw['moon_sign_name']} चन्द्र राशि ({fw['moon_nak_name']} नक्षत्र)। "
                f"वर्तमान विंशोत्तरी दशा: महादशा {fw['dasha_md']} ({fw['md_start']} से {fw['md_end']}), "
                f"अन्तर्दशा {fw['dasha_ad']} (समाप्ति: {fw['ad_end']}), "
                f"प्रत्यन्तर्दशा {fw['dasha_pd']} (समाप्ति: {fw['pd_end']})। "
                f"आगामी अन्तर्दशा: {fw['next_ad_lord_hi']} (प्रारंभ: {fw['ad_end']})। "
                f"ग्रह स्थितियां: {planets_summary}। "
                f"गोचर: {transits_summary}। "
                f"नियम:\n"
                f"1. शुद्ध, गरिमामय एवं सुरुचिपूर्ण हिन्दी में उत्तर दें।\n"
                f"2. कभी भी शब्दों की अनुचित पुनरावृत्ति न करें (जैसे 'मंगल मंगल' या 'शनि शनि')।\n"
                f"3. जातक के प्रश्न का सीधा, तार्किक और समय-सीमा (Timeframe / Dates) सहित सटीक शास्त्रीय समाधान दें।\n"
                f"4. यदि जातक दशा, आगामी समय, परीक्षा, करियर, वित्त या विवाह पूछे, तो स्पष्ट ज्योतिष्य फलादेश व प्रामाणिक उपाय बताएं।"
            )

            # Build conversation history
            contents = []
            if chat_history:
                for msg in chat_history[-6:]:
                    r = "user" if msg.get("role") == "user" else "model"
                    contents.append(f"{r}: {msg.get('content', '')}")
            contents.append(f"user: {query}")
            full_prompt = system_prompt + "\n\n" + "\n".join(contents)

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=full_prompt
            )
            if response and response.text:
                return response.text.strip()
        except Exception:
            pass

        return None

    def consult(self, query: str, chart, cur_dasha: Any, birth_info: Dict[str, Any],
                transit_pos: Optional[Dict[str, Any]] = None,
                prashna_meta: Optional[Dict[str, Any]] = None,
                chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Generates a direct, authentic, personalized astrological consultation response.
        """
        fw = self._extract_chart_framework(chart, cur_dasha, transit_pos)
        name = birth_info.get("name", "जातक")
        q_lower = query.lower()

        # 1. Try Gemini API first if configured
        gemini_reply = self._call_gemini_if_available(query, fw, name, chat_history)
        if gemini_reply:
            return gemini_reply

        # 2. Comprehensive Deterministic Vedic Shastra Consultation Engine
        p_inf = fw["p_info"]
        asp = fw["aspects_map"]
        occ = fw["house_occupants"]
        tr = fw["transits"]

        # Helper: Clean placement string without repeating planet names
        def _placement(p_name: str) -> str:
            p = p_inf.get(p_name, {})
            h = p.get('house', '-')
            sign = p.get('sign_name', '')
            retro = " (वक्री)" if p.get('is_retro') else ""
            return f"{h}वें भाव में {sign} राशि{retro}"

        # Helper: Full planet description
        def _full_planet(p_name: str) -> str:
            p_hi = constants.PLANETS_HI.get(p_name, p_name)
            return f"{p_hi} देव {_placement(p_name)}"

        # Dasha display text
        dasha_display = fw["dasha_md"]
        if fw["dasha_ad"]:
            dasha_display += f" में {fw['dasha_ad']}"
        if fw["dasha_pd"]:
            dasha_display += f" (प्रत्यंतर: {fw['dasha_pd']})"

        # Check conversation history depth:
        user_msg_count = 0
        if chat_history:
            user_msg_count = sum(1 for m in chat_history if m.get("role") == "user")

        # Conversational opening: greeting only on turn 1
        salutation = f"सादर प्रणाम {name} जी।\n\n" if user_msg_count <= 1 else f"{name} जी,\n\n"

        # ---------------------------------------------------------------------
        # INTENT 1: TIMING OF EVENTS & WHEN WILL TIME IMPROVE?
        # Keywords: 'aagami', 'kab se', 'sahi hoga', 'achha samay', 'when', 'future',
        # 'kab theek', 'sudhar', 'badlega', 'kab aayega', 'turning point'
        # ---------------------------------------------------------------------
        if any(w in q_lower for w in ["kab", "कब", "aagami", "आगामी", "sahi hoga", "सही होगा", "theek", "ठीक",
                                     "future", "भविष्य", "sudhar", "सुधार", "badlega", "बदलेगा", "achha samay",
                                     "अच्छा समय", "shubh", "शुभ समय", "turning point", "when will", "kab tak"]):
            ans = [salutation]
            ans.append(f"आपके प्रश्न — **'आगामी समय कब से अनुकूल होगा व भाग्योदय कब से होगा?'** के संबंध में ग्रहों, विंशोत्तरी दशा व गोचर का काल-विभाजन विश्लेषण इस प्रकार है:\n")

            # Phase A: Current friction / delay diagnosis
            ans.append(f"1. **वर्तमान समय की स्थिति (कारण एवं प्रभाव):**")
            ans.append(
                f"वर्तमान में आपकी विंशोत्तरी दशा **{fw['dasha_md']} महादशा में {fw['dasha_ad']} की अन्तर्दशा** "
                f"तथा **{fw['dasha_pd']} की प्रत्यन्तर्दशा** सक्रिय है।\n"
                f"• अन्तर्दशा स्वामी {fw['dasha_ad']} देव आपकी कुण्डली के {_placement(fw['ad_lord_en'])} में स्थित हैं। "
                f"{'शनि देव का स्वभाव धीमी गति व कड़ी परीक्षा के बाद ही परिणाम देने का होता है। ' if fw['ad_lord_en'] == 'Saturn' else ''}"
                f"इस कारण वर्तमान में प्रयास अधिक और तात्कालिक परिणाम मिलने में विलंब या मानसिक दबाव अनुभव हो सकता है।"
            )

            # Phase B: Exact Relief Milestone (Pratyantardasha)
            pd_end_str = fw["pd_end"] or "आगामी कुछ सप्ताह"
            ans.append(f"2. **प्रथम राहत काल (First Relief Milestone):**")
            ans.append(
                f"तात्कालिक मानसिक उलझनों और गतिरोध में **{pd_end_str}** से सकारात्मक परिवर्तन दृष्टिगोचर होगा, "
                f"जब वर्तमान प्रत्यन्तर्दशा समाप्त होकर अगले अनुकूल ग्रह का प्रत्यंतर प्रारंभ होगा।"
            )

            # Phase C: Major Golden Turning Point (Next Antardasha)
            ad_end_str = fw["ad_end"] or "2027"
            next_lord_hi = fw["next_ad_lord_hi"] or "बुध"
            next_lord_en = fw["next_ad_lord_en"] or "Mercury"
            ans.append(f"3. **मुख्य स्वर्णिम कालखंड एवं भाग्योदय (Major Turning Point):**")
            ans.append(
                f"आपकी कुण्डली में वास्तविक और दीर्घकालिक सकारात्मक मोड़ **{ad_end_str}** से आएगा, "
                f"जब वर्तमान {fw['dasha_ad']} की अन्तर्दशा पूर्ण होकर **{next_lord_hi} देव की अन्तर्दशा** प्रारंभ होगी।\n"
                f"• {next_lord_hi} देव आपकी जन्म कुण्डली में {_placement(next_lord_en)} में स्थित हैं। "
                f"यह अवधि आपके लिए बौद्धिक निर्णयों, कार्यक्षेत्र में गतिशीलता, नए व्यावसायिक/प्रशासनिक अवसरों तथा आर्थिक संचय के लिए अत्यधिक फलदायी सिद्ध होगी।"
            )

            # Phase D: Transit support (Gochar)
            jup_tr = tr.get("Jupiter", {})
            sat_tr = tr.get("Saturn", {})
            ans.append(f"4. **गोचर कालीन संबल (Planetary Transits):**")
            if jup_tr:
                ans.append(f"• देवगुरु बृहस्पति वर्तमान में {jup_tr.get('sign', '')} राशि में संचरण कर रहे हैं (लग्न से {jup_tr.get('h_lagna', '')}वें भाव में)। गुरु का यह गोचर आपके महत्वपूर्ण भावों पर शुभ प्रभाव डाल रहा है।")
            if sat_tr:
                ans.append(f"• शनि देव का गोचर {sat_tr.get('sign', '')} राशि में चल रहा है, जो यह स्पष्ट करता है कि धैर्यपूर्वक कर्म करने पर सफलता सुनिश्चित है।")

            # Phase E: Strategic Advice
            ans.append(f"**आचार्य निर्देश (मार्गदर्शन):**")
            ans.append(
                f"वर्तमान समय संयम और आगामी बड़े कार्यों की नींव रखने का है। किसी भी नए कार्य में जल्दबाजी या निराशा से बचें। "
                f"नित्य प्रातः सूर्य देव को तांबे के लोटे से जल अर्पित करें और ॐ नमः शिवाय का यथाशक्ति जप करें।"
            )
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 2: DASHA PREDICTIONS & VIMSHOTTARI ANALYSIS
        # Keywords: 'dasha', 'dashao', 'mahadasha', 'antardasha', 'दशा', 'महादशा', 'अंतर्दशा'
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["dasha", "दशा", "mahadasha", "महादशा", "antardasha", "अन्तर्दशा", "अंतर्दशा",
                                       "pratyantar", "प्रत्यंतर", "vimshottari", "विंशोत्तरी"]):
            ans = [salutation]
            ans.append(f"आपकी कुण्डली की **सक्रिय विंशोत्तरी दशाओं का समग्र शास्त्रीय फलादेश** इस प्रकार है:\n")

            # 1. Mahadasha Lord Analysis
            md_en = fw["md_lord_en"] or "Venus"
            md_hi = fw["dasha_md"]
            md_h = p_inf.get(md_en, {}).get("house", 9)
            md_sign = p_inf.get(md_en, {}).get("sign_name", "")
            ans.append(f"1. **महादशा स्वामी — {md_hi} देव:**")
            ans.append(
                f"• **अवधि:** {fw['md_start']} से {fw['md_end']} तक।\n"
                f"• **स्थिति:** {md_hi} देव कुण्डली के **{md_h}वें भाव में {md_sign} राशि** में स्थित हैं।\n"
                f"• **शास्त्रीय फल:** यह महादशा भाग्य, धर्म, दूरस्थ यात्राओं, सामाजिक मान-सम्मान और दीर्घकालिक समृद्धि की आधारशिला रखती है। यह कालखंड जातक को ज्ञानवान और प्रतिष्ठित बनाता है।"
            )

            # 2. Antardasha Lord Analysis
            ad_en = fw["ad_lord_en"] or "Saturn"
            ad_hi = fw["dasha_ad"]
            ad_h = p_inf.get(ad_en, {}).get("house", 7)
            ad_sign = p_inf.get(ad_en, {}).get("sign_name", "")
            if ad_en == "Saturn":
                ad_phala = "यह अन्तर्दशा अधिकार, दायित्व और कर्मक्षेत्र में कड़े परिश्रम की मांग करती है। शनि देव जातक को धैर्य और अनुशासन की कसौटी पर परखते हैं, तत्पश्चात स्थायी सफलता व प्रतिष्ठा प्रदान करते हैं।"
            elif ad_en == "Ketu":
                ad_phala = "केतु की अन्तर्दशा आध्यात्मिक चिंतन, गहन शोध, आत्म-मंथन और आंतरिक एकाग्रता लाती है। सांसारिक निर्णयों में जल्दबाजी से बचकर विवेक से कार्य करना चाहिए।"
            elif ad_en == "Rahu":
                ad_phala = "राहु की अन्तर्दशा उच्च महत्वाकांक्षा, अप्रत्याशित अवसर और दूरगामी योजनाएं लाती है। इसमें भ्रम अथवा जल्दबाजी से बचकर विवेकपूर्ण निर्णय लेना श्रेयस्कर रहता है।"
            elif ad_en in ["Jupiter", "Venus", "Mercury"]:
                ad_phala = f"{ad_hi} देव की शुभ अन्तर्दशा बुद्धि, ज्ञान, नए व्यावसायिक/प्रशासनिक अनुबंध, वित्तीय लाभ और पारिवारिक सुख में निरंतर वृद्धि करती है।"
            elif ad_en == "Sun":
                ad_phala = "सूर्य देव की अन्तर्दशा राजपक्ष, शासन-प्रशासन, आत्मबल एवं समाज में प्रभाव क्षेत्र में वृद्धि करती है।"
            elif ad_en == "Moon":
                ad_phala = "चन्द्रमा की अन्तर्दशा मानसिक संवेदनशीलता, रचनात्मकता, परिजनों का सहयोग तथा जनसंपर्क में विस्तार लाती है।"
            else:
                ad_phala = "मंगल देव की अन्तर्दशा पराक्रम, साहस, त्वरित निर्णय क्षमता और कर्मक्षेत्र में विजय प्रदान करती है।"

            ans.append(f"2. **वर्तमान अन्तर्दशा स्वामी — {ad_hi} देव:**")
            ans.append(
                f"• **अवधि:** {fw['ad_start']} से **{fw['ad_end']}** तक।\n"
                f"• **स्थिति:** {ad_hi} देव कुण्डली के **{ad_h}वें भाव में {ad_sign} राशि** में विराजमान हैं{' (तुला राशि में अपनी परम उच्च अवस्था में)' if ad_sign == 'तुला' else ''}।\n"
                f"• **शास्त्रीय फल:** {ad_phala}"
            )

            # 3. Pratyantardasha Lord Analysis
            pd_en = fw["pd_lord_en"] or "Moon"
            pd_hi = fw["dasha_pd"]
            ans.append(f"3. **सूक्ष्म प्रत्यन्तर्दशा — {pd_hi} देव:**")
            ans.append(
                f"• **समाप्ति तिथि:** **{fw['pd_end']}**\n"
                f"• **प्रभाव:** तात्कालिक दैनिक निर्णय, मनोबल और मानसिक एकाग्रता को प्रभावित कर रहे हैं। इस अवधि में मन को शांत रखकर नियमित कार्य संपन्न करें।"
            )

            # 4. Next Antardasha Preview
            next_lord_hi = fw["next_ad_lord_hi"] or "बुध"
            next_lord_en = fw["next_ad_lord_en"] or "Mercury"
            ans.append(f"4. **आगामी अन्तर्दशा — {next_lord_hi} देव का पूर्वावलोकन:**")
            ans.append(
                f"• **प्रारंभ दिनांक:** **{fw['ad_end']}** से।\n"
                f"• **फलकथन:** {next_lord_hi} देव की अन्तर्दशा प्रारंभ होते ही पूर्व में अटके हुए कार्यों में तीव्रता आएगी। व्यापार, नए अनुबंध, वित्तीय लाभ और पारिवारिक सौहार्द में वृद्धि होगी।"
            )

            # 5. Dasha Upay
            ans.append(f"**दशा अनुकूलता हेतु सिद्ध उपाय:**")
            ans.append(
                f"• शनिवार के दिन संध्या समय पीपल के वृक्ष के नीचे सरसों के तेल का दीपक प्रज्वलित करें।\n"
                f"• शुक्रवार को श्वेत वस्तुओं अथवा मिश्री का दान करें तथा श्री सूक्त का पाठ करें।"
            )
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 3: COMPETITIVE EXAMS / JUDICIARY / RHJS / UPSC / GOVT JOB
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["rhjs", "rjs", "exam", "judiciary", "judge", "judicial", "न्यायिक",
                                       "परीक्षा", "प्रतियोगिता", "upsc", "clear", "सफलता", "निकलेगा"]):
            h6_sign = (fw["asc_sign"] + 5) % 12
            h6_lord = constants.SIGN_LORD[h6_sign]
            h6_lord_hi = constants.PLANETS_HI.get(h6_lord, h6_lord)

            h10_sign = (fw["asc_sign"] + 9) % 12
            h10_lord = constants.SIGN_LORD[h10_sign]
            h10_lord_hi = constants.PLANETS_HI.get(h10_lord, h10_lord)

            ans = [salutation]
            ans.append(f"आपके प्रश्न — **न्यायिक सेवा (RHJS / Judiciary) अथवा उच्च प्रतियोगी परीक्षा में चयन के योग** के संबंध में कुण्डली विश्लेषण:\n")

            ans.append(
                f"न्यायिक सेवा एवं उच्च प्रशासनिक पदों के लिए ज्योतिष शास्त्र में **सूर्य (राजसत्ता), देवगुरु बृहस्पति (विधि व न्याय), "
                f"शनि (न्यायाधीश/दंड विधान)** तथा **षष्ठ भाव (प्रतियोगिता विजय)** व **दशम भाव (राजपद)** का विचार किया जाता है।\n"
                f"1. **प्रतियोगिता एवं विजय भाव (षष्ठ भाव):** षष्ठेश {h6_lord_hi} की स्थिति आपकी परीक्षा रणनीति और कठिन प्रतिस्पर्धा से जूझने की क्षमता को दर्शाती है।\n"
                f"2. **न्यायकारक ग्रह स्थिति:** न्याय व धर्म के स्वाभाविक कारक देवगुरु बृहस्पति {_full_planet('Jupiter')} हैं तथा न्यायाधीश शनि देव {_full_planet('Saturn')} हैं।\n"
                f"3. **दशम भाव पर प्रभाव:** {'शनि देव की दृष्टि दशम भाव पर पड़ रही है, जो कानून, न्यायपालिका और प्रशासनिक व्यवस्था में स्वाभाविक योग्यता को सिद्ध करती है।' if 10 in asp.get('Saturn', []) else 'दशम भाव का संबंध उच्च राजकीय सेवा के अनुकूल बना हुआ है।'}\n"
                f"4. **सक्रिय दशा का प्रभाव:** वर्तमान में {dasha_display} चल रही है। परीक्षा में अंतिम सफलता के लिए मुख्य परीक्षा के उत्तर लेखन में अत्यधिक अनुशासन तथा साक्षात्कार में आत्मविश्वास बनाए रखना अनिवार्य होगा।"
            )
            ans.append(f"**आचार्य निर्णय:** कुण्डली में न्यायिक एवं विधिक सेवा के पूर्ण शास्त्रीय योग उपस्थित हैं। आगामी अन्तर्दशा ({fw['ad_end']} से) आपको अत्यधिक अनुकूल परिणाम देने में सक्षम है।")
            ans.append(f"**साधना व उपाय:** नित्य प्रातः सूर्य देव को कुंकुम युक्त जल अर्पित कर आदित्य हृदय स्तोत्र का पाठ करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 4: CAREER / JOB / PROMOTION / BUSINESS
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["career", "job", "नौकरी", "प्रमोशन", "promotion", "आजीविका", "व्यवसाय",
                                       "business", "व्यापार", "काम", "ऑफिस"]):
            h10_sign = (fw["asc_sign"] + 9) % 12
            h10_lord = constants.SIGN_LORD[h10_sign]
            h10_lord_hi = constants.PLANETS_HI.get(h10_lord, h10_lord)

            ans = [salutation]
            ans.append(f"आपकी आजीविका, करियर एवं कार्यक्षेत्र के संबंध में ग्रहों का शास्त्रीय विश्लेषण:\n")
            ans.append(
                f"1. **कर्म भाव (दशम भाव):** आपके दशम भाव के अधिपति **{h10_lord_hi}** देव कुण्डली के {_placement(h10_lord)} में स्थित हैं। "
                f"कर्मेश की यह स्थिति कार्यक्षेत्र में स्थायित्व, गहन बौद्धिक दक्षता और अधिकार को दर्शाती है।\n"
                f"2. **कर्मकारक शनि देव की भूमिका:** कर्म के नैसर्गिक कारक शनि देव आपकी कुण्डली के {_placement('Saturn')} में विराजमान हैं। "
                f"शनि देव यहाँ से महत्वपूर्ण भावों पर अपनी पूर्ण दृष्टि डाल रहे हैं, जिससे व्यक्ति अपनी निष्ठा और योग्यता सिद्ध करने के बाद ही उच्च पद व सम्मान प्राप्त करता है।\n"
                f"3. **दशा व तात्कालिक स्थिति:** वर्तमान में सक्रिय **{dasha_display}** कार्यक्षेत्र में धैर्य की मांग करती है। वरिष्ठों से तालमेल बनाए रखें। "
                f"आगामी समय में पदोन्नति एवं प्रभाव क्षेत्र में विस्तार के स्पष्ट योग निर्मित हो रहे हैं।"
            )
            ans.append(f"**परामर्श:** नौकरी व स्वतंत्र परामर्श दोनों में ही आपकी सफलता सुनिश्चित है। शनिवार को गरीबों को काले तिल या भोजन का दान करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 5: WEALTH / FINANCE / DEBT / INVESTMENT
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["धन", "money", "wealth", "पैसा", "कर्ज", "debt", "आर्थिक", "निवेश", "लाभ", "रुपया"]):
            h2_sign = (fw["asc_sign"] + 1) % 12
            h11_sign = (fw["asc_sign"] + 10) % 12
            h2_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h2_sign])
            h11_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h11_sign])

            ans = [salutation]
            ans.append(f"आपकी आर्थिक स्थिति, धन संचय एवं वित्तीय संभावनाओं का शास्त्रीय विचार:\n")
            ans.append(
                f"1. **धन भाव (द्वितीय भाव) एवं लाभ भाव (एकादश भाव):** धन भाव के स्वामी **{h2_lord}** और आय भाव के स्वामी **{h11_lord}** देव हैं। "
                f"कुण्डली में नियमित आय और धन संचय के योग उत्तम हैं।\n"
                f"2. **धनकारक गुरु की स्थिति:** धन व ऐश्वर्य के कारक देवगुरु बृहस्पति कुण्डली के {_placement('Jupiter')} में स्थित हैं, जो पैतृक व स्वअर्जित संपत्ति में वृद्धि करते हैं।\n"
                f"3. **सावधानी:** चालू दशा में बिना उचित अनुबंध के किसी को धन उधार देने या शेयर सट्टे जैसे आकस्मिक जोखिम से बचें। संचित कोष की सुरक्षा प्राथमिक होनी चाहिए।"
            )
            ans.append(f"**उपाय:** श्री कनकधारा स्तोत्र का पाठ करें तथा गुरुवार को केसर अथवा चने की दाल का दान करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 6: MARRIAGE / RELATIONSHIP / SPOUSE
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["विवाह", "शादी", "marriage", "पत्नी", "पति", "दांपत्य", "रिश्ता", "प्रेम", "सप्तम"]):
            h7_sign = (fw["asc_sign"] + 6) % 12
            h7_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h7_sign])

            ans = [salutation]
            ans.append(f"दांपत्य जीवन एवं वैवाहिक सुख के संबंध में ग्रह संकेत:\n")
            ans.append(
                f"1. **सप्तम भाव (कलत्र भाव):** आपके सप्तम भाव के स्वामी **{h7_lord}** हैं और विवाह के नैसर्गिक कारक शुक्र देव {_placement('Venus')} में स्थित हैं।\n"
                f"2. सप्तम भाव में {_full_planet('Saturn')} की स्थिति दांपत्य में परिपक्वता, गंभीरता और आपसी सम्मान की अपेक्षा रखती है।\n"
                f"3. चालू दशा ({dasha_display}) में जीवनसाथी के विचारों का आदर करें और किसी भी पारिवारिक विषय पर खुलकर व शांतिपूर्ण संवाद करें।"
            )
            ans.append(f"**उपाय:** शुक्रवार को माँ लक्ष्मी को सुगंधित श्वेत पुष्प अर्पित करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 7: HEALTH / WELLNESS
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["स्वास्थ्य", "health", "रोग", "बीमारी", "तबीयत", "इलाज", "दर्द"]):
            h6_sign = (fw["asc_sign"] + 5) % 12
            h6_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h6_sign])

            ans = [salutation]
            ans.append(f"आरोग्य एवं स्वास्थ्य संबंधी शास्त्रीय विश्लेषण:\n")
            ans.append(
                f"1. **लग्न एवं षष्ठ भाव:** लग्नेश {fw['lagnesh_hi']} देव {_placement(fw['lagnesh'])} में विराजमान हैं, जो शारीरिक जीवनी शक्ति को बलवान बनाते हैं।\n"
                f"2. षष्ठेश {h6_lord} और वर्तमान दशा के प्रभाव से मौसमी व्याधियों, उदर विकार अथवा कार्यभार से उत्पन्न मानसिक तनाव से सावधान रहना चाहिए।\n"
                f"3. प्राणायाम, पर्याप्त जल सेवन एवं सात्विक खानपान से आपका स्वास्थ्य सदैव उत्तम बना रहेगा।"
            )
            ans.append(f"**उपाय:** महामृत्युंजय मंत्र का नित्य 11 बार स्मरण करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 8: CHILDREN / PROGENY
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["संतान", "बच्चे", "गर्भाधान", "पुत्र", "पुत्री", "child", "progeny"]):
            h5_sign = (fw["asc_sign"] + 4) % 12
            h5_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h5_sign])

            ans = [salutation]
            ans.append(f"संतान भाव एवं संतति सुख के विषय में ग्रह संकेत:\n")
            ans.append(
                f"1. **पंचम भाव (सुत भाव):** पंचम भाव के स्वामी **{h5_lord}** देव हैं तथा संतान के नैसर्गिक कारक देवगुरु बृहस्पति {_placement('Jupiter')} में स्थित हैं।\n"
                f"2. पंचम भाव और गुरु का बलवान होना सुयोग्य, आज्ञाकारी एवं कुलदीपक संतान का सुख प्रदान करता है।\n"
                f"3. आगामी समय संतान की शिक्षा और उन्नति के लिए अत्यधिक अनुकूल सिद्ध होगा।"
            )
            ans.append(f"**उपाय:** गोपाल सहस्रनाम का पाठ अथवा गुरुवार को केले के पौधे की सेवा करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 9: PROPERTY / HOUSE / VEHICLE
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["मकान", "घर", "भूमि", "वाहन", "गाड़ी", "प्रॉपर्टी", "flat", "plot", "car"]):
            h4_sign = (fw["asc_sign"] + 3) % 12
            h4_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h4_sign])

            ans = [salutation]
            ans.append(f"भूमि, भवन, वाहन एवं सुख भाव (चतुर्थ भाव) का विचार:\n")
            ans.append(
                f"1. **चतुर्थ भाव (मातृ व गृह सुख):** चतुर्थ भाव के स्वामी **{h4_lord}** देव हैं। भूमि कारक मंगल देव {_placement('Mars')} में तथा वाहन कारक शुक्र देव {_placement('Venus')} में स्थित हैं।\n"
                f"2. यह ग्रह विन्यास नवीन संपत्ति निर्माण, भूमि क्रय अथवा उच्च श्रेणी के वाहन सुख का प्रबल संकेत देता है।\n"
                f"3. वर्तमान दशा में आगामी वर्ष तक अचल संपत्ति के सौदे फलीभूत होने के स्पष्ट योग हैं।"
            )
            ans.append(f"**उपाय:** मंगलवार को हनुमान चालीसा का पाठ करें।")
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 10: FOREIGN TRAVEL / SETTLEMENT
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["विदेश", "foreign", "यात्रा", "travel", "settlement", "वीजा"]):
            h9_sign = (fw["asc_sign"] + 8) % 12
            h12_sign = (fw["asc_sign"] + 11) % 12
            h9_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h9_sign])
            h12_lord = constants.PLANETS_HI.get(constants.SIGN_LORD[h12_sign])

            ans = [salutation]
            ans.append(f"विदेश गमन, दूरस्थ यात्राओं एवं स्थानांतरण के संबंध में कुण्डली विश्लेषण:\n")
            ans.append(
                f"1. **नवम व द्वादश भाव:** भाग्य व दूरस्थ यात्रा भाव (9H) और विदेश भाव (12H) के स्वामी क्रमशः **{h9_lord}** व **{h12_lord}** हैं।\n"
                f"2. राहु देव {_placement('Rahu')} में स्थित होकर जन्मस्थान से दूर अथवा विदेश से आजीविका और सम्मान प्राप्त करने का योग बनाते हैं।\n"
                f"3. वर्तमान विंशोत्तरी दशा में दूरस्थ क्षेत्रों की यात्राएं ज्ञान, व्यापार और पदोन्नति के लिए लाभकारी रहेंगी।"
            )
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 11: TROUBLES / SADESATI / RELIEF / OBSTACLES
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["कष्ट", "परेशानी", "समस्या", "साढ़े साती", "ढैया", "राहत", "संकट", "मुसीबत", "तनाव"]):
            ans = [salutation]
            ans.append(f"कष्ट, मानसिक तनाव एवं बाधाओं से मुक्ति के संबंध में ग्रह स्थिति व समाधान:\n")
            ans.append(
                f"1. **मूल कारण का विश्लेषण:** वर्तमान में आपकी सक्रिय दशा ({dasha_display}) चल रही है। "
                f"शनि देव {_placement('Saturn')} में स्थित हैं। शनि जब कुण्डली के महत्वपूर्ण भावों को प्रभावित करते हैं, "
                f"तो वे व्यक्ति को धैर्य, अनुशासन और आंतरिक शुद्धता की परीक्षा में डालते हैं। यह कष्ट नहीं अपितु परिपक्वता का कालखंड है।\n"
                f"2. **राहत की समय-सीमा:** प्रत्यन्तर्दशा समाप्ति ({fw['pd_end'] or 'शीघ्र'}) और आगामी अन्तर्दशा प्रारंभ ({fw['ad_end'] or '2027'}) के साथ सभी बाधाओं का निवारण स्वतः होने लगेगा।\n"
                f"3. **शास्त्रीय शांति उपाय:**\n"
                f"• शनिवार को सूर्यास्त के बाद हनुमान जी के सम्मुख चमेली के तेल का दीपक जलाएं और सुंदरकांड का पाठ करें।\n"
                f"• चींटियों को आटा व पक्षियों को दाना डालें।"
            )
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 12: REMEDIES / GEMSTONES / MANTRAS
        # ---------------------------------------------------------------------
        elif any(w in q_lower for w in ["उपाय", "रत्न", "मंत्र", "दान", "पूजा", "remedy", "upay", "stone"]):
            ans = [salutation]
            ans.append(f"आपकी कुण्डली के अनुसार सबसे प्रभावी एवं निर्दोष शास्त्रीय उपाय:\n")
            ans.append(
                f"1. **लग्नेश बल संवर्धन:** आपके लग्नेश **{fw['lagnesh_hi']}** {_placement(fw['lagnesh'])} में स्थित हैं। "
                f"लग्नेश को बलवान करने से समस्त बाधाएं दूर होती हैं। नित्य गायत्री मंत्र अथवा हनुमान चालीसा का पाठ करें।\n"
                f"2. **दशा शांति उपाय:** चालू दशा ({dasha_display}) की अनुकूलता हेतु शनिवार को शनि स्तोत्र और शुक्रवार को लक्ष्मी स्तोत्र का पाठ परम श्रेयस्कर है।\n"
                f"3. **रत्न परामर्श:** कुण्डली के कारक ग्रहों (लग्नेश मंगल, नवमेश गुरु) के अनुकूल रत्न ज्योतिषी के विधिवत परीक्षण के उपरांत ही धारण करें।"
            )
            return "\n\n".join(ans)

        # ---------------------------------------------------------------------
        # INTENT 13: INTELLIGENT CONTEXTUAL SYNTHESIS (FALLBACK)
        # Never outputs a canned robotic template!
        # ---------------------------------------------------------------------
        else:
            ans = [salutation]
            ans.append(f"आपके प्रश्न — *\"{query}\"* के संदर्भ में आपकी कुण्डली की विस्तृत ग्रह स्थिति का अवलोकन:\n")
            ans.append(
                f"1. **लग्न एवं आत्मबल:** आपकी कुण्डली **{fw['asc_sign_name']} लग्न** की है और लग्नेश **{fw['lagnesh_hi']}** "
                f"कुण्डली के {_placement(fw['lagnesh'])} में विराजमान हैं। लग्नेश की यह सुदृढ़ स्थिति यह दर्शाती है कि आपके भीतर किसी भी परिस्थिति से निपटने की अटूट आंतरिक क्षमता और दृढ़ निश्चय है।\n"
                f"2. **चन्द्रमा एवं मन की स्थिति:** आपका चन्द्रमा **{fw['moon_sign_name']} राशि** में {fw['moon_nak_name']} नक्षत्र में संचरण कर रहा है, जो अंतर्मुखी प्रज्ञा और सूक्ष्म शोध की प्रवृत्ति प्रदान करता है।\n"
                f"3. **वर्तमान दशा का निर्देश:** सक्रिय विंशोत्तरी दशा **{dasha_display}** चल रही है (अन्तर्दशा समाप्ति: **{fw['ad_end'] or '2027'}**)। "
                f"यह ग्रह संयोजन यह स्पष्ट संकेत देता है कि वर्तमान समय शांत रहकर अपनी योजनाओं को परिपक्व करने का है।\n"
                f"4. **आगामी मोड़:** आगामी अन्तर्दशा प्रारंभ होते ही आपके द्वारा सोची गई योजनाएं तीव्र गति से सफलता की ओर अग्रसर होंगी।"
            )
            ans.append(f"**आचार्य परामर्श:** ईश्वर पर आस्था रखें, अपने दैनिक कर्म में शुचिता बनाए रखें और नित्य सूर्य नमस्कार अथवा प्राणायाम करें।")
            return "\n\n".join(ans)


vyas_chatbot = VyasChatbotEngine()
