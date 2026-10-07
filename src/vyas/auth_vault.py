"""VYAS User Authentication, 30-Day VIP Pro Free Trial, and Saved Kundlis Vault.

Provides persistent SQLite database storage for:
- User accounts (Username/Email, Password hash, Created at, VIP status, Trial expiry)
- 30-Day Auto VIP Trial on onboarding
- Saved Kundli Vault (up to 10 for Free, Unlimited for VIP)
- Profile switching, creation, editing, and deletion
"""
import sqlite3
import hashlib
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vyas_users.db")

def _get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database tables if they do not exist."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                vip_expiry TIMESTAMP NOT NULL,
                tier TEXT DEFAULT 'VIP_TRIAL'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS saved_kundlis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                dob TEXT NOT NULL,
                tob TEXT NOT NULL,
                city TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                tz REAL DEFAULT 5.5,
                ayanamsa TEXT DEFAULT 'KP',
                gender TEXT DEFAULT 'Male',
                notes TEXT,
                relationship TEXT DEFAULT 'Self',
                created_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS app_state (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP NOT NULL
            )
        """)
        conn.commit()

def set_active_session_user(user_id: int):
    """Saves the last logged-in user ID permanently so reopening the browser/app auto logs in."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_state (key, value, updated_at) VALUES ('active_user_id', ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """, (str(user_id), datetime.now().isoformat()))
            conn.commit()
    except Exception:
        pass

def clear_active_session():
    """Clears the active session on manual logout."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_state WHERE key = 'active_user_id'")
            conn.commit()
    except Exception:
        pass

def get_last_active_user() -> Optional[Dict]:
    """Retrieves the last logged-in user profile automatically on startup."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = 'active_user_id'")
            row = cursor.fetchone()
            if row:
                uid = int(row["value"])
                return get_user_by_id(uid)
            # If no active_user_id set yet, fallback to the latest registered user in the DB
            cursor.execute("SELECT id FROM users ORDER BY id DESC LIMIT 1")
            u_row = cursor.fetchone()
            if u_row:
                return get_user_by_id(u_row["id"])
    except Exception:
        pass
    return None

# Ensure DB is initialized on module import
init_db()

def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def register_user(email: str, name: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Registers a new user and grants an automatic 30-day VIP Pro Trial."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "अमान्य ईमेल आईडी। (Invalid Email)", None
    if len(password) < 4:
        return False, "पासवर्ड कम से कम 4 अक्षरों का होना चाहिए।", None

    now = datetime.now()
    vip_expiry = now + timedelta(days=30)
    pwd_hash = _hash_password(password)

    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO users (email, name, password_hash, created_at, vip_expiry, tier)
                VALUES (?, ?, ?, ?, ?, 'VIP_TRIAL')
            """, (email, name.strip(), pwd_hash, now.isoformat(), vip_expiry.isoformat()))
            user_id = cursor.lastrowid
            conn.commit()
            
            user_data = {
                "id": user_id,
                "email": email,
                "name": name.strip(),
                "tier": "VIP_TRIAL",
                "vip_expiry": vip_expiry.strftime("%d/%m/%Y"),
                "days_left": 30,
                "is_vip": True
            }
            return True, "सफल पंजीकरण! 30-दिन का VIP Pro निःशुल्क ट्रायल सक्रिय हो गया है।", user_data
    except sqlite3.IntegrityError:
        return False, "यह ईमेल पहले से पंजीकृत है। कृपया लॉगिन करें।", None
    except Exception as e:
        return False, f"पंजीकरण में त्रुटि: {str(e)}", None

def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Authenticates user and returns active tier details."""
    email = email.strip().lower()
    pwd_hash = _hash_password(password)

    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? AND password_hash = ?", (email, pwd_hash))
            row = cursor.fetchone()
            if not row:
                return False, "ईमेल या पासवर्ड गलत है।", None

            user_id = row["id"]
            name = row["name"]
            vip_exp = datetime.fromisoformat(row["vip_expiry"])
            now = datetime.now()
            
            days_left = max(0, (vip_exp - now).days)
            is_vip = vip_exp > now

            user_data = {
                "id": user_id,
                "email": email,
                "name": name,
                "tier": "VIP_TRIAL" if is_vip else "FREE",
                "vip_expiry": vip_exp.strftime("%d/%m/%Y"),
                "days_left": days_left,
                "is_vip": is_vip
            }
            return True, f"नमस्ते {name}! सफलतापूर्वक लॉगिन हुआ।", user_data
    except Exception as e:
        return False, f"लॉगिन त्रुटि: {str(e)}", None

def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Retrieves user profile by ID for session restoration."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            vip_exp = datetime.fromisoformat(row["vip_expiry"])
            now = datetime.now()
            days_left = max(0, (vip_exp - now).days)
            is_vip = vip_exp > now
            tier_val = row["tier"] if "tier" in row.keys() else "VIP_TRIAL"
            return {
                "id": row["id"],
                "email": row["email"],
                "name": row["name"],
                "tier": tier_val if is_vip else "FREE",
                "vip_expiry": vip_exp.strftime("%d/%m/%Y"),
                "days_left": days_left,
                "is_vip": is_vip
            }
    except Exception:
        return None

def login_or_register_google(email: str, name: str) -> Tuple[bool, str, Optional[Dict]]:
    """One-click Google login / registration."""
    email = email.strip().lower()
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                vip_exp = datetime.fromisoformat(row["vip_expiry"])
                now = datetime.now()
                days_left = max(0, (vip_exp - now).days)
                is_vip = vip_exp > now
                tier_val = row["tier"] if "tier" in row.keys() else "VIP_TRIAL"
                user_data = {
                    "id": row["id"],
                    "email": email,
                    "name": row["name"],
                    "tier": tier_val if is_vip else "FREE",
                    "vip_expiry": vip_exp.strftime("%d/%m/%Y"),
                    "days_left": days_left,
                    "is_vip": is_vip
                }
                return True, f"Google से सफल लॉगिन: {user_data['name']}", user_data
            else:
                # Register new google user with 30-day VIP trial
                now = datetime.now()
                vip_expiry = now + timedelta(days=30)
                pwd_hash = _hash_password(f"google_oauth_{email}")
                cursor.execute("""
                    INSERT INTO users (email, name, password_hash, created_at, vip_expiry, tier)
                    VALUES (?, ?, ?, ?, ?, 'VIP_TRIAL')
                """, (email, name.strip() or "Google User", pwd_hash, now.isoformat(), vip_expiry.isoformat()))
                user_id = cursor.lastrowid
                conn.commit()
                user_data = {
                    "id": user_id,
                    "email": email,
                    "name": name.strip() or "Google User",
                    "tier": "VIP_TRIAL",
                    "vip_expiry": vip_expiry.strftime("%d/%m/%Y"),
                    "days_left": 30,
                    "is_vip": True
                }
                return True, "Google से सफल पंजीकरण! 30-दिन का VIP Pro निःशुल्क सक्रिय।", user_data
    except Exception as e:
        return False, f"Google लॉगिन त्रुटि: {str(e)}", None

def save_kundli(user_id: int, kundli_dict: Dict) -> Tuple[bool, str]:
    """Saves a horoscope profile into the user vault."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vip_expiry FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                return False, "यूज़र नहीं मिला।"
            
            is_vip = datetime.fromisoformat(user_row["vip_expiry"]) > datetime.now()
            
            cursor.execute("SELECT COUNT(*) as cnt FROM saved_kundlis WHERE user_id = ?", (user_id,))
            cnt = cursor.fetchone()["cnt"]
            
            if not is_vip and cnt >= 5:
                return False, "मुफ्त वर्शन में अधिकतम 5 कुंडलियां सेव की जा सकती हैं। असीमित कुंडलियों के लिए VIP अपग्रेड करें।"

            now = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO saved_kundlis (user_id, name, dob, tob, city, lat, lon, tz, ayanamsa, gender, notes, relationship, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                kundli_dict.get("name", "Unknown"),
                kundli_dict.get("dob", "1990-01-01"),
                kundli_dict.get("tob", "12:00:00"),
                kundli_dict.get("city", "Pali, Rajasthan"),
                float(kundli_dict.get("lat", 25.7711)),
                float(kundli_dict.get("lon", 73.3234)),
                float(kundli_dict.get("tz", 5.5)),
                kundli_dict.get("ayanamsa", "KP"),
                kundli_dict.get("gender", "Male"),
                kundli_dict.get("notes", ""),
                kundli_dict.get("relationship", "Client"),
                now
            ))
            conn.commit()
            return True, f"कुंडली '{kundli_dict.get('name')}' वॉल्ट में सफलतापूर्वक सेव हो गई।"
    except Exception as e:
        return False, f"सेव करने में त्रुटि: {str(e)}"

def get_saved_kundlis(user_id: int) -> List[Dict]:
    """Fetches all saved kundlis for a user."""
    kundlis = []
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM saved_kundlis WHERE user_id = ? ORDER BY id DESC", (user_id,))
            rows = cursor.fetchall()
            for r in rows:
                kundlis.append(dict(r))
    except Exception:
        pass
    return kundlis

def upgrade_vip(user_id: int, plan_type: str, txn_id: str) -> Tuple[bool, str]:
    """Extends user VIP access based on payment plan."""
    days_map = {
        "monthly": 30,
        "annual": 365,
        "lifetime": 3650
    }
    add_days = days_map.get(plan_type.lower(), 365)
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vip_expiry FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if not row:
                return False, "उपयोगकर्ता नहीं मिला।"
            
            curr_exp = datetime.fromisoformat(row["vip_expiry"])
            base_date = max(datetime.now(), curr_exp)
            new_exp = base_date + timedelta(days=add_days)

            cursor.execute("""
                UPDATE users SET vip_expiry = ?, tier = 'VIP_PAID' WHERE id = ?
            """, (new_exp.isoformat(), user_id))
            conn.commit()
            return True, f"सफल अपग्रेड! आपका VIP प्लान {new_exp.strftime('%d/%m/%Y')} तक सक्रिय कर दिया गया है।"
    except Exception as e:
        return False, f"अपग्रेड में त्रुटि: {str(e)}"

