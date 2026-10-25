"""VYAS User Authentication, 30-Day VIP Pro Free Trial, and Saved Kundlis Vault.

Storage: SQLite locally, or any Postgres database (Neon/Supabase/Railway) when
DATABASE_URL is configured — the Cloud filesystem is wiped on every redeploy,
so Postgres is required for accounts that survive restarts.

Provides persistent storage for:
- User accounts (Username/Email, Password hash, Created at, VIP status, Trial expiry)
- 30-Day Auto VIP Trial on onboarding
- Saved Kundli Vault (up to 10 for Free, Unlimited for VIP)
- Profile switching, creation, editing, and deletion
"""
import hashlib
import hmac
import os
import re
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "vyas_users.db")

# ---------------- DATABASE BACKEND ----------------
# Streamlit Community Cloud wipes the container filesystem on every reboot or
# redeploy, which used to delete vyas_users.db and every account inside it.
# When a Postgres URL is configured (Neon/Supabase/Railway), accounts live
# outside the container and survive deploys. SQLite stays as the zero-config
# local fallback so the app still runs without any secrets.
#
# Configure ONE of these (Streamlit Cloud → Settings → Secrets):
#     DATABASE_URL = "postgresql://user:pass@host/db?sslmode=require"
#     [database]
#     url = "postgresql://..."
# or set the DATABASE_URL environment variable.

def _clean_database_url(value) -> str:
    """Accepts only a real Postgres URL (never a template placeholder)."""
    value = ("" if value is None else str(value)).strip()
    if not value or value.startswith("<"):
        return ""
    if not value.startswith(("postgres://", "postgresql://")):
        return ""
    return value


def _load_database_url() -> str:
    url = _clean_database_url(os.environ.get("DATABASE_URL"))
    if url:
        return url
    try:
        import streamlit as st

        secrets = st.secrets
        for key in ("DATABASE_URL", "NEON_DATABASE_URL"):
            try:
                value = secrets.get(key, "")
            except Exception:
                value = ""
            url = _clean_database_url(value)
            if url:
                return url
        for section, key in (("database", "url"), ("database", "connection_string"), ("neon", "url")):
            try:
                value = secrets.get(section, {}).get(key, "")
            except Exception:
                value = ""
            url = _clean_database_url(value)
            if url:
                return url
    except Exception:
        pass
    return ""


DATABASE_URL = _load_database_url()
BACKEND = "postgres" if DATABASE_URL else "sqlite"
LAST_DB_ERROR = ""

_pg_local = threading.local()
_PG_ID_TABLES = ("users", "saved_kundlis")
_AUTOINCREMENT_RE = re.compile(r"INTEGER\s+PRIMARY\s+KEY\s+AUTOINCREMENT", re.I)
_TIMESTAMP_RE = re.compile(r"\bTIMESTAMP\b", re.I)


def _connect_postgres(url: str):
    """Opens a Postgres connection, preferring psycopg 3 and falling back to psycopg2."""
    # Keepalives + a server-side statement timeout stop a suspended Neon compute
    # (or a dropped socket) from hanging a Streamlit rerun forever.
    common = dict(
        connect_timeout=10,
        keepalives_idle=20,
        keepalives_interval=5,
        keepalives_count=3,
        options="-c statement_timeout=30000",
    )
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError:
        psycopg = None
    if psycopg is not None:
        return psycopg.connect(url, row_factory=dict_row, **common)
    import psycopg2
    from psycopg2.extras import RealDictCursor

    return psycopg2.connect(url, cursor_factory=RealDictCursor, **common)


_PG_IDLE_RECONNECT_SECONDS = 20


def _raw_pg_connection():
    """Returns a per-thread connection, recycled after a short idle period.

    Neon suspends idle computes and may drop their sockets; reusing a socket
    that died would make the next query hang. Recycling after ~20s means a
    burst of calls inside one Streamlit rerun reuses one cheap connection,
    while a user coming back later always gets a fresh one.
    """
    conn = getattr(_pg_local, "conn", None)
    if conn is not None:
        healthy = not getattr(conn, "closed", False) and not getattr(conn, "broken", False)
        fresh = time.time() - getattr(_pg_local, "last_used", 0.0) < _PG_IDLE_RECONNECT_SECONDS
        if healthy and fresh:
            _pg_local.last_used = time.time()
            return conn
        try:
            conn.close()
        except Exception:
            pass
        _pg_local.conn = None

    conn = _connect_postgres(DATABASE_URL)
    _pg_local.conn = conn
    _pg_local.last_used = time.time()
    return conn


def _pg_statement(sql: str):
    """Rewrites SQLite-flavoured SQL into Postgres SQL.

    The rest of this module was written for sqlite3, so the shim keeps that
    call style working instead of rewriting every query:
      * ``?`` placeholders become ``%s``
      * ``INSERT OR IGNORE`` / ``INSERT OR REPLACE`` become ``ON CONFLICT``
      * ``AUTOINCREMENT`` becomes ``SERIAL``, ``TIMESTAMP`` becomes ``TEXT``
        (the module stores and parses ISO strings, exactly like SQLite does)
      * inserts into id tables get ``RETURNING id`` for ``cursor.lastrowid``
    """
    text = sql
    upper = text.upper()
    needs_id = False

    if "INSERT OR REPLACE" in upper:
        text = re.sub(r"INSERT\s+OR\s+REPLACE", "INSERT", text, flags=re.I)
        if "ON CONFLICT" not in text.upper():
            if re.search(r"INTO\s+app_state\b", text, re.I):
                text = text.rstrip().rstrip(";") + (
                    " ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value,"
                    " updated_at = EXCLUDED.updated_at"
                )
            else:
                text = text.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    elif "INSERT OR IGNORE" in upper:
        text = re.sub(r"INSERT\s+OR\s+IGNORE", "INSERT", text, flags=re.I)
        if "ON CONFLICT" not in text.upper():
            text = text.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    else:
        match = re.match(r"\s*INSERT\s+INTO\s+([A-Za-z_][A-Za-z0-9_]*)", text, re.I)
        if match and match.group(1).lower() in _PG_ID_TABLES and "RETURNING" not in upper:
            needs_id = True
            text = text.rstrip().rstrip(";") + " RETURNING id"

    text = _AUTOINCREMENT_RE.sub("SERIAL PRIMARY KEY", text)
    text = _TIMESTAMP_RE.sub("TEXT", text)
    # psycopg treats every literal '%' as a placeholder marker, so escape any
    # pre-existing percent signs before introducing our own %s placeholders.
    text = text.replace("%", "%%")
    text = text.replace("?", "%s")
    return text, needs_id


class _PgCursorShim:
    """Mimics the small slice of sqlite3.Cursor this module relies on."""

    def __init__(self, cursor):
        self._cursor = cursor
        self.lastrowid = None

    def execute(self, sql, params=()):
        statement, needs_id = _pg_statement(sql)
        self.lastrowid = None
        self._cursor.execute(statement, tuple(params or ()))
        if needs_id:
            row = self._cursor.fetchone()
            if row is not None:
                self.lastrowid = row.get("id") if isinstance(row, dict) else row[0]
        return self

    def executemany(self, sql, seq_of_params):
        statement, _ = _pg_statement(sql)
        self._cursor.executemany(statement, seq_of_params)
        return self

    def fetchone(self):
        return self._cursor.fetchone()

    def fetchall(self):
        return self._cursor.fetchall()

    def fetchmany(self, size=None):
        return self._cursor.fetchmany(size) if size is not None else self._cursor.fetchmany()

    def close(self):
        return self._cursor.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._cursor.close()
        return False

    def __getattr__(self, name):
        return getattr(self._cursor, name)


class _PgConnectionShim:
    """Keeps the sqlite3 ``with _get_connection() as conn`` idiom working."""

    def __init__(self, raw):
        self._raw = raw

    def cursor(self):
        return _PgCursorShim(self._raw.cursor())

    def execute(self, sql, params=()):
        return self.cursor().execute(sql, params)

    def commit(self):
        self._raw.commit()
        _pg_local.last_used = time.time()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        # The socket is cached per thread; closing it every call would add a
        # full TLS + auth round trip to Neon on each Streamlit rerun.
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        try:
            if exc_type is None:
                self._raw.commit()
            else:
                self._raw.rollback()
            _pg_local.last_used = time.time()
        except Exception:
            try:
                self._raw.close()
            except Exception:
                pass
            _pg_local.conn = None
        return False

    def __getattr__(self, name):
        return getattr(self._raw, name)


def _get_connection():
    global BACKEND, LAST_DB_ERROR
    if BACKEND == "postgres":
        try:
            return _PgConnectionShim(_raw_pg_connection())
        except Exception as exc:
            LAST_DB_ERROR = f"{type(exc).__name__}: {exc}"
            BACKEND = "sqlite"
            print(
                f"[vyas] Postgres connection failed ({LAST_DB_ERROR}). "
                "Falling back to ephemeral SQLite for this run.",
                flush=True,
            )
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _sync_user_id_sequence(conn) -> None:
    """Keeps Postgres' id sequence ahead of the hard-coded guest row (id = 1)."""
    if BACKEND != "postgres":
        return
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT setval(pg_get_serial_sequence('users', 'id'),"
            " GREATEST((SELECT COALESCE(MAX(id), 0) FROM users), 1))"
        )
        conn.commit()
    except Exception:
        pass


def _is_integrity_error(exc: Exception) -> bool:
    """True for sqlite3 and psycopg unique/constraint violations alike."""
    if isinstance(exc, sqlite3.IntegrityError):
        return True
    return any(cls.__name__ in ("IntegrityError", "UniqueViolation") for cls in type(exc).__mro__)


def init_db():
    """Initializes the database tables, falling back to SQLite if Postgres is down."""
    global BACKEND, LAST_DB_ERROR
    try:
        _init_db_tables()
    except Exception as exc:
        LAST_DB_ERROR = f"{type(exc).__name__}: {exc}"
        print(f"[vyas] Database init failed ({LAST_DB_ERROR})", flush=True)
        if BACKEND == "postgres":
            BACKEND = "sqlite"
            _init_db_tables()
        else:
            raise


def _init_db_tables():
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
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS google_tokens (
                user_id INTEGER PRIMARY KEY,
                access_token TEXT,
                refresh_token TEXT,
                updated_at TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        # Ensure default seeker guest account exists
        cursor.execute("SELECT id FROM users WHERE id = 1")
        if not cursor.fetchone():
            now = datetime.now()
            vip_expiry = now + timedelta(days=365)
            cursor.execute("""
                INSERT OR IGNORE INTO users (id, email, name, password_hash, created_at, vip_expiry, tier)
                VALUES (1, 'seeker@vyasastro.com', 'नया जातक (Seeker)', '', ?, ?, 'VIP_TRIAL')
            """, (now.isoformat(), vip_expiry.isoformat()))
        conn.commit()
        _sync_user_id_sequence(conn)

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
    """Retrieves the last logged-in user profile automatically on startup.

    Only honors an explicit active_user_id set by a login. The old fallback
    (auto-login as the latest registered user) was removed: it silently
    re-logged-in the previous account right after a manual logout.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = 'active_user_id'")
            row = cursor.fetchone()
            if row:
                uid = int(row["value"])
                if uid == 1:
                    return None  # guest account — treat as "not logged in"
                return get_user_by_id(uid)
    except Exception:
        pass
    return None

def set_app_state(key: str, value: str) -> None:
    """Persists an arbitrary short-lived value in the app_state table.

    Used for OAuth bookkeeping (state nonce, PKCE verifier) that must survive
    a full top-level page navigation. Streamlit session_state does not: escaping
    the Cloud iframe to reach accounts.google.com reloads the app in a brand-new
    session, which silently dropped the PKCE verifier and broke token exchange.
    """
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO app_state (key, value, updated_at) VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated_at=excluded.updated_at
            """, (str(key), str(value), datetime.now().isoformat()))
            conn.commit()
    except Exception:
        pass

def get_app_state(key: str) -> Optional[str]:
    """Reads a value written by set_app_state (None when absent)."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = ?", (str(key),))
            row = cursor.fetchone()
            return row["value"] if row else None
    except Exception:
        return None

def pop_app_state(key: str) -> Optional[str]:
    """Reads and deletes a value written by set_app_state (single use)."""
    val = get_app_state(key)
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_state WHERE key = ?", (str(key),))
            conn.commit()
    except Exception:
        pass
    return val


def prune_app_state(prefix: str, keep_hours: int = 6) -> None:
    """Drops stale keys sharing a prefix so single-use rows cannot pile up."""
    cutoff = (datetime.now() - timedelta(hours=keep_hours)).isoformat()
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "DELETE FROM app_state WHERE key LIKE ? AND updated_at < ?",
                (str(prefix) + "%", cutoff),
            )
            conn.commit()
    except Exception:
        pass


# ---------------- PER-BROWSER SESSION TOKENS ----------------
# Streamlit Cloud has no server-side notion of "this browser". The old
# get_last_active_user() auto-login was global: after one person signed in,
# EVERY visitor was restored as that same account and could see their saved
# charts. These tokens are handed to one browser (cookie) and resolved back to
# that user only, so accounts stay isolated.

def create_session_token(user_id: int) -> str:
    """Creates a long-lived random token mapped to one user id."""
    import secrets as _secrets
    token = _secrets.token_urlsafe(32)
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO app_state (key, value, updated_at) VALUES (?, ?, ?)",
                (f"session:{token}", str(int(user_id)), datetime.now().isoformat()),
            )
            conn.commit()
    except Exception:
        return ""
    return token


def get_user_by_session_token(token: str) -> Optional[Dict]:
    """Resolves a browser cookie token back to its account (None if unknown)."""
    token = (token or "").strip()
    if not token:
        return None
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM app_state WHERE key = ?", (f"session:{token}",))
            row = cursor.fetchone()
            if not row:
                return None
            return get_user_by_id(int(row["value"]))
    except Exception:
        return None


def delete_session_token(token: str) -> None:
    """Invalidates one browser token (used on logout)."""
    token = (token or "").strip()
    if not token:
        return
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM app_state WHERE key = ?", (f"session:{token}",))
            conn.commit()
    except Exception:
        pass

# Ensure DB is initialized on module import
init_db()

def _hash_password(password: str) -> str:
    """Salted PBKDF2-HMAC-SHA256 hash (``pbkdf2$salt$hex``).

    The old scheme was a bare SHA-256 hex digest: identical passwords produced
    identical hashes and a stolen DB was trivially brute-forced. Existing rows
    still verify (see _verify_password) and are upgraded on next login.
    """
    import secrets as _secrets
    salt = _secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120_000)
    return f"pbkdf2${salt}${dk.hex()}"


def _legacy_hash(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def _verify_password(password: str, stored: str) -> bool:
    """Constant-time check that understands both hash formats."""
    import hmac
    stored = stored or ""
    if stored.startswith("pbkdf2$"):
        try:
            _, salt, expected = stored.split("$", 2)
        except ValueError:
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("ascii"), 120_000)
        return hmac.compare_digest(dk.hex(), expected)
    return hmac.compare_digest(_legacy_hash(password), stored)


def _needs_rehash(stored: str) -> bool:
    return not (stored or "").startswith("pbkdf2$")


def register_user(email: str, name: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Registers a new user and grants an automatic 30-day VIP Pro Trial."""
    email = email.strip().lower()
    if not email or "@" not in email:
        return False, "अमान्य ईमेल आईडी। (Invalid Email)", None
    if len(password) < 6:
        return False, "पासवर्ड कम से कम 6 अक्षरों का होना चाहिए।", None

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
    except Exception as e:
        if _is_integrity_error(e):
            return False, "यह ईमेल पहले से पंजीकृत है। कृपया लॉगिन करें।", None
        return False, f"पंजीकरण में त्रुटि: {str(e)}", None

def login_user(email: str, password: str) -> Tuple[bool, str, Optional[Dict]]:
    """Authenticates user and returns active tier details."""
    email = email.strip().lower()

    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if not row or not _verify_password(password, row["password_hash"]):
                return False, "ईमेल या पासवर्ड गलत है।", None

            # Transparently upgrade legacy SHA-256 rows to salted PBKDF2.
            if _needs_rehash(row["password_hash"]):
                try:
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (_hash_password(password), row["id"]),
                    )
                    conn.commit()
                except Exception:
                    pass

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

def save_google_tokens(user_id: int, access_token: str, refresh_token: str = "") -> bool:
    """Stores or updates Google OAuth access & refresh tokens for a user."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO google_tokens (user_id, access_token, refresh_token, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    access_token=excluded.access_token,
                    refresh_token=CASE WHEN excluded.refresh_token != '' THEN excluded.refresh_token ELSE google_tokens.refresh_token END,
                    updated_at=excluded.updated_at
            """, (user_id, access_token, refresh_token, datetime.now().isoformat()))
            conn.commit()
            return True
    except Exception:
        return False

def get_google_tokens(user_id: int) -> Optional[Dict[str, str]]:
    """Retrieves stored Google OAuth tokens for a user."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT access_token, refresh_token FROM google_tokens WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    "access_token": row["access_token"],
                    "refresh_token": row["refresh_token"] or ""
                }
    except Exception:
        pass
    return None


def save_kundli(user_id: int, kundli_dict: Dict) -> Tuple[bool, str]:
    """Saves a horoscope profile into the user vault."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT vip_expiry FROM users WHERE id = ?", (user_id,))
            user_row = cursor.fetchone()
            if not user_row:
                if user_id == 1:
                    now_dt = datetime.now()
                    vip_exp = now_dt + timedelta(days=365)
                    cursor.execute("""
                        INSERT OR IGNORE INTO users (id, email, name, password_hash, created_at, vip_expiry, tier)
                        VALUES (1, 'seeker@vyasastro.com', 'नया जातक (Seeker)', '', ?, ?, 'VIP_TRIAL')
                    """, (now_dt.isoformat(), vip_exp.isoformat()))
                    conn.commit()
                    _sync_user_id_sequence(conn)
                    is_vip = True
                else:
                    return False, "यूज़र नहीं मिला।"
            else:
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

def delete_kundli(user_id: int, kundli_id: int) -> Tuple[bool, str]:
    """Deletes a saved kundli by its ID."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM saved_kundlis WHERE id = ? AND user_id = ?", (kundli_id, user_id))
            conn.commit()
            return True, "कुण्डली सफलतापूर्वक हटा दी गई।"
    except Exception as e:
        return False, f"हटाने में त्रुटि: {str(e)}"

def update_kundli(user_id: int, kundli_id: int, kundli_dict: Dict) -> Tuple[bool, str]:
    """Updates an existing saved kundli."""
    try:
        with _get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE saved_kundlis 
                SET name = ?, dob = ?, tob = ?, city = ?, lat = ?, lon = ?, tz = ?, ayanamsa = ?, gender = ?, notes = ?, relationship = ?
                WHERE id = ? AND user_id = ?
            """, (
                kundli_dict.get("name", "Unknown"),
                kundli_dict.get("dob", "1990-01-01"),
                kundli_dict.get("tob", "12:00:00"),
                kundli_dict.get("city", "New Delhi, India"),
                float(kundli_dict.get("lat", 28.6139)),
                float(kundli_dict.get("lon", 77.2090)),
                float(kundli_dict.get("tz", 5.5)),
                kundli_dict.get("ayanamsa", "KP"),
                kundli_dict.get("gender", "Male"),
                kundli_dict.get("notes", ""),
                kundli_dict.get("relationship", "Self"),
                kundli_id,
                user_id
            ))
            conn.commit()
            return True, "कुण्डली सफलतापूर्वक अपडेट हो गई।"
    except Exception as e:
        return False, f"अपडेट त्रुटि: {str(e)}"

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

