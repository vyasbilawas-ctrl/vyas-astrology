"""VYAS Google Authentication & Google Drive Cloud Storage Integration.

Provides end-to-end integration for:
1. 'Sign in with Google' (OAuth 2.0 authentication flow)
2. Auto-creation of a dedicated folder in Google Drive ('VYAS Kundli & Horoscopes')
3. Direct cloud upload of generated 56-page Kundli PDFs and saved horoscopes
4. Retrieval of direct shareable Google Drive links (webViewLink)
5. Token refresh and local/session persistence
"""
import os
import json
import urllib.parse
from typing import Dict, Optional, Tuple, Any
import requests

# Basic sign-in scopes: profile only. These are non-sensitive, so an OAuth
# client in "Testing" mode lets a test user through without the scary
# "app is not verified" 403 page. Login must NEVER depend on a sensitive
# scope — that is what made "Google से साइन इन करें" bounce with
# access_denied for accounts that were not on the verified/test list.
GOOGLE_OAUTH_SCOPES_BASIC = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]

# Google Drive upload needs one extra (sensitive) scope. It is requested
# separately via the "Google Drive से कनेक्ट करें" button, only after the
# user is already signed in (incremental authorization).
GOOGLE_OAUTH_SCOPES_DRIVE = GOOGLE_OAUTH_SCOPES_BASIC + [
    "https://www.googleapis.com/auth/drive.file",
]

# Backwards-compatible alias for callers that want the full Drive scope.
GOOGLE_OAUTH_SCOPES = GOOGLE_OAUTH_SCOPES_DRIVE

CONFIG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "google_oauth_config.json"
)

# Canonical redirect URI — Google requires byte-exact match between the
# authorization request, the token exchange, and the Console registration.
DEFAULT_REDIRECT_URI = "http://localhost:8501"

# Every redirect URI registered on the OAuth client ("VYAS Astra", Web
# application). A URI that is NOT in this set makes Google reject the flow
# with redirect_uri_mismatch, so detection only ever returns a member.
# Adding a new deployment host? Register it in Google Cloud Console first,
# then add the exact string here.
REGISTERED_REDIRECT_URIS = frozenset({
    "http://localhost:8501",
    "https://vyas-astrology-111.streamlit.app",
})


def detect_runtime_redirect_uri() -> str:
    """Best-effort redirect URI for the CURRENT runtime host.

    Streamlit Cloud serves the app from a public host, so defaulting to
    ``http://localhost:8501`` makes Google bounce back to the developer's
    machine (or fail with redirect_uri_mismatch). Deriving the public
    ``https://<host>`` keeps local dev on localhost while cloud deployments
    work without manual secret editing.

    Google requires a byte-exact match against the Authorized redirect URIs
    registered on the OAuth client, so every candidate is checked against
    ``REGISTERED_REDIRECT_URIS``. Streamlit exposes the current request URL
    directly, which is preferred over header sniffing because it is exactly
    the origin the browser is using.
    """
    candidates = []

    # 1. The live request URL — the most faithful source of the public origin.
    try:
        import streamlit as st
        req_url = ""
        try:
            req_url = str(getattr(st.context, "url", "") or "")
        except Exception:
            req_url = ""
        if not req_url:
            headers = getattr(st.context, "headers", None)
            if headers:
                proto = (headers.get("X-Forwarded-Proto") or "https").split(",")[0].strip()
                fwd_host = (headers.get("X-Forwarded-Host") or headers.get("Host") or "").strip()
                if fwd_host:
                    req_url = f"{proto}://{fwd_host.split(',')[0].strip()}/"
        if req_url:
            parsed = urllib.parse.urlparse(req_url)
            if parsed.scheme and parsed.netloc:
                candidates.append(f"{parsed.scheme}://{parsed.netloc}")
    except Exception:
        pass

    # 2. Header-only fallback (covers older Streamlit versions).
    try:
        import streamlit as st
        headers = getattr(st, "context", None) and st.context.headers
        if headers:
            host = (headers.get("X-Forwarded-Host") or headers.get("Host") or "").strip()
            if host:
                host = host.split(",")[0].strip()
                proto = (headers.get("X-Forwarded-Proto") or "").split(",")[0].strip()
                scheme = proto or ("http" if "localhost" in host or host.startswith("127.") else "https")
                candidates.append(f"{scheme}://{host}".rstrip("/"))
    except Exception:
        pass

    for cand in candidates:
        cand = cand.rstrip("/")
        if cand in REGISTERED_REDIRECT_URIS:
            return cand

    # Detected but not yet registered in Google Cloud Console. Returning the
    # real public origin is far better than silently falling back to
    # http://localhost:8501, which on a hosted deployment sends the browser to
    # a dead local port with no explanation. Google will instead answer with an
    # explicit redirect_uri_mismatch naming the exact URI to register.
    for cand in candidates:
        cand = cand.rstrip("/")
        parsed = urllib.parse.urlparse(cand)
        if parsed.scheme == "https" and parsed.netloc:
            return cand

    return DEFAULT_REDIRECT_URI


def resolve_redirect_uri(configured: str = "") -> str:
    """Picks the effective redirect URI: explicit config first, else runtime.

    Any candidate that is not in ``REGISTERED_REDIRECT_URIS`` would be rejected
    by Google with redirect_uri_mismatch, so it falls back to the canonical
    default instead (see ``detect_runtime_redirect_uri``).
    """
    configured = (configured or "").strip()
    if configured:
        normalized = normalize_redirect_uri(configured)
        # A configured localhost URI is meaningless on a hosted deployment.
        if "localhost" in normalized or "127.0.0.1" in normalized:
            detected = detect_runtime_redirect_uri()
            if detected != DEFAULT_REDIRECT_URI:
                return detected
        if normalized in REGISTERED_REDIRECT_URIS:
            return normalized
    return detect_runtime_redirect_uri()


def normalize_redirect_uri(uri: str) -> str:
    """Strips whitespace and trailing slashes so auth URL, token exchange and
    saved config all use the exact same redirect_uri string."""
    return (uri or "").strip().rstrip("/") or DEFAULT_REDIRECT_URI


def _get_or_create_oauth_state() -> str:
    """Per-session random nonce for CSRF protection of the OAuth callback.

    Each nonce is stored under its own key (``oauth_state:<nonce>``) instead of
    one shared row. A single shared row is overwritten by every other visitor,
    so on a public deployment one person's login invalidated another's. The
    callback looks the nonce up by value and deletes it (single use), which also
    makes concurrent logins safe.
    """
    import secrets as _secrets
    nonce = ""
    try:
        import streamlit as st
        nonce = st.session_state.get("oauth_state") or ""
    except Exception:
        nonce = ""

    if nonce:
        return nonce

    nonce = _secrets.token_urlsafe(16)
    try:
        import streamlit as st
        st.session_state["oauth_state"] = nonce
    except Exception:
        pass
    try:
        from vyas import auth_vault
        auth_vault.prune_app_state("oauth_state:", keep_hours=6)
        auth_vault.set_app_state(f"oauth_state:{nonce}", nonce)
    except Exception:
        pass
    return nonce


def verify_oauth_state(received: str) -> bool:
    """True when `received` matches a nonce issued for a login attempt.

    Lenient by design: when no nonce of that value was ever stored (fresh
    deployment, DB reset, or a browser that never rendered the login button)
    the callback is accepted rather than locking the user out. A *stored* nonce
    is always consumed and must match exactly.
    """
    if not received:
        return False
    try:
        from vyas import auth_vault
        stored = auth_vault.get_app_state(f"oauth_state:{received}")
        if stored is None:
            return True  # nothing recorded — lenient
        auth_vault.pop_app_state(f"oauth_state:{received}")
        return stored == received
    except Exception:
        return True


def _pkce_pair() -> Tuple[str, str]:
    """Creates a PKCE (verifier, challenge) pair for this session.

    PKCE binds the authorization code to this exact session, so an intercepted
    code cannot be redeemed elsewhere. It also lets the flow remain secure
    even if the client secret is ever exposed, and is required for public
    (secret-less) OAuth clients.
    """
    import base64
    import hashlib
    import secrets as _secrets

    verifier = _secrets.token_urlsafe(64)[:96]
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
    return verifier, challenge


def _store_pkce_verifier(verifier: str) -> None:
    """Keeps the PKCE verifier for the token exchange.

    Written to BOTH session_state and the app_state table. The Cloud login
    button leaves the iframe (Google won't render inside an embedded frame), so
    the callback runs in a fresh session; only the durable copy survives.
    """
    try:
        import streamlit as st
        st.session_state["oauth_code_verifier"] = verifier
    except Exception:
        pass
    try:
        from vyas import auth_vault
        auth_vault.set_app_state("oauth_code_verifier", verifier)
    except Exception:
        pass


def _pop_pkce_verifier() -> str:
    """Consumes the PKCE verifier — single use, always.

    Both copies (session_state and the durable app_state row) are consumed on
    every call, even when only one holds a value. Leaving the durable copy
    behind would let a stale verifier be replayed against a later callback.
    """
    verifier = ""
    try:
        import streamlit as st
        verifier = st.session_state.pop("oauth_code_verifier", "") or ""
    except Exception:
        verifier = ""

    durable = ""
    try:
        from vyas import auth_vault
        durable = auth_vault.pop_app_state("oauth_code_verifier") or ""
    except Exception:
        durable = ""

    # Prefer the session copy (the flow that never left the process) and fall
    # back to the durable copy written before escaping to accounts.google.com.
    return verifier or durable


def load_google_config() -> Dict[str, str]:
    """Loads Google OAuth credentials.

    Precedence (first non-empty value per field wins):
      1. Environment variables   (deployment override)
      2. data/google_oauth_config.json (saved from the in-app credentials form)
      3. .streamlit/secrets.toml  (bundled defaults)
    Previously env/secrets always shadowed the JSON file, which made the
    in-app "Save Credentials" button a silent no-op.
    """
    env_cfg = {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", "").strip(),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", "").strip(),
        "redirect_uri": os.environ.get("GOOGLE_REDIRECT_URI", "").strip(),
    }

    saved_cfg: Dict[str, str] = {}
    if os.path.exists(CONFIG_FILE_PATH):
        try:
            with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if isinstance(raw, dict):
                    saved_cfg = {k: str(v or "").strip() for k, v in raw.items()}
        except Exception:
            saved_cfg = {}

    secrets_cfg = {"client_id": "", "client_secret": "", "redirect_uri": ""}
    try:
        import streamlit as st
        if hasattr(st, "secrets"):
            secrets_cfg = {
                "client_id": str(st.secrets.get("GOOGLE_CLIENT_ID", "") or "").strip(),
                "client_secret": str(st.secrets.get("GOOGLE_CLIENT_SECRET", "") or "").strip(),
                "redirect_uri": str(st.secrets.get("GOOGLE_REDIRECT_URI", "") or "").strip(),
            }
    except Exception:
        pass

    # Bundled defaults used to ship here; secrets must NEVER be committed
    # (GitHub push protection blocks Google OAuth secrets). Operators provide
    # credentials via Streamlit secrets / env vars / the in-app form instead.
    config = {}
    for key in ("client_id", "client_secret", "redirect_uri"):
        config[key] = env_cfg[key] or saved_cfg.get(key, "") or secrets_cfg[key]

    # Always normalize — one canonical form for the whole OAuth flow.
    config["redirect_uri"] = normalize_redirect_uri(
        config.get("redirect_uri") or DEFAULT_REDIRECT_URI
    )
    return config


def save_google_config(client_id: str, client_secret: str, redirect_uri: str = DEFAULT_REDIRECT_URI) -> bool:
    """Persists Google OAuth credentials to the local config file."""
    try:
        os.makedirs(os.path.dirname(CONFIG_FILE_PATH), exist_ok=True)
        with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump({
                "client_id": client_id.strip(),
                "client_secret": client_secret.strip(),
                "redirect_uri": normalize_redirect_uri(redirect_uri)
            }, f, indent=2)
        return True
    except Exception:
        return False


def record_oauth_error(message: str) -> None:
    """Persists the last OAuth failure so it survives the callback session.

    The callback normally runs in a brand-new Streamlit session and then
    reruns; without a durable copy the exact Google error is lost and the user
    only sees a generic failure. The diagnostics panel reads this back.
    """
    try:
        from vyas import auth_vault
        from datetime import datetime as _dt
        auth_vault.set_app_state(
            "last_oauth_error",
            f"{_dt.now().strftime('%d-%m-%Y %H:%M:%S')} — {str(message)[:600]}",
        )
    except Exception:
        pass


def get_last_oauth_error() -> str:
    try:
        from vyas import auth_vault
        return auth_vault.get_app_state("last_oauth_error") or ""
    except Exception:
        return ""


def clear_oauth_error() -> None:
    try:
        from vyas import auth_vault
        auth_vault.pop_app_state("last_oauth_error")
    except Exception:
        pass


def oauth_diagnostics() -> Dict[str, str]:
    """Snapshot of the OAuth wiring, shown to operators in the login panel."""
    cfg = load_google_config()
    cid = cfg.get("client_id", "")
    rid = resolve_redirect_uri(cfg.get("redirect_uri", ""))
    runtime = ""
    try:
        runtime = detect_runtime_redirect_uri()
    except Exception:
        runtime = ""
    if len(cid) > 32:
        cid_hint = f"{cid[:12]}…{cid[-16:]}"
    else:
        cid_hint = cid
    return {
        "client_id_configured": "yes" if cid else "no",
        "client_id_hint": cid_hint,
        "client_secret_configured": "yes" if cfg.get("client_secret") else "no",
        "configured_redirect_uri": cfg.get("redirect_uri", ""),
        "effective_redirect_uri": rid,
        "runtime_origin": runtime,
        "redirect_uri_registered": "yes" if rid in REGISTERED_REDIRECT_URIS else "no",
        "last_oauth_error": get_last_oauth_error(),
    }


def get_google_auth_url(
    redirect_uri: Optional[str] = None,
    state: Optional[str] = None,
    include_drive: bool = True,
) -> str:
    """Generates the official Google OAuth 2.0 authorization URL.

    ``include_drive=False`` requests only the basic profile scopes. Use that for
    plain sign-in: a sensitive Drive scope makes Google block accounts that are
    not on the verified/test list with an opaque 403 before the app is reached.
    """
    cfg = load_google_config()
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    r_uri = normalize_redirect_uri(redirect_uri) if redirect_uri else resolve_redirect_uri(cfg.get("redirect_uri", ""))
    state_val = state or _get_or_create_oauth_state()

    if not client_id:
        return ""

    scopes = GOOGLE_OAUTH_SCOPES_DRIVE if include_drive else GOOGLE_OAUTH_SCOPES_BASIC

    # PKCE is only needed for a PUBLIC client (no secret). With a confidential
    # web client the secret already binds the exchange, and PKCE adds a fragile
    # dependency: the verifier must survive the top-level navigation via the
    # shared app_state row, where any concurrent page load overwrites it and
    # the exchange then dies with "code_verifier does not match". Skipping it
    # when a secret exists removes that entire failure mode.
    verifier = ""
    challenge = ""
    if not client_secret:
        verifier, challenge = _pkce_pair()
        _store_pkce_verifier(verifier)

    params = {
        "client_id": client_id,
        "redirect_uri": r_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "access_type": "offline",
        # "select_account" still shows the account chooser but does NOT force a
        # fresh consent screen every single login (better UX, fewer 403s).
        "prompt": "select_account",
        "state": state_val,
    }
    if challenge:
        params["code_challenge"] = challenge
        params["code_challenge_method"] = "S256"
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Exchanges Google authorization code for access and refresh tokens."""
    cfg = load_google_config()
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    r_uri = normalize_redirect_uri(redirect_uri) if redirect_uri else resolve_redirect_uri(cfg.get("redirect_uri", ""))

    if not client_id or not client_secret:
        return False, "Google Client ID या Client Secret कॉन्फ़िगर नहीं है।", None

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": r_uri,
        "grant_type": "authorization_code"
    }
    # Send the PKCE verifier when this session started the flow with a challenge.
    _verifier = _pop_pkce_verifier()
    if _verifier:
        data["code_verifier"] = _verifier

    try:
        resp = requests.post(token_url, data=data, timeout=15)

        # The verifier copy lives in a single shared app_state row, so a
        # concurrent page load can replace it between "authorize" and
        # "exchange". If Google complains about the verifier, retry once without
        # it — the client secret is sufficient proof for a confidential client.
        if resp.status_code != 200 and _verifier:
            try:
                _first_err = str((resp.json() or {}).get("error_description", ""))
            except Exception:
                _first_err = ""
            if "verifier" in _first_err.lower() or "code_verifier" in _first_err.lower():
                _retry = {k: v for k, v in data.items() if k != "code_verifier"}
                resp = requests.post(token_url, data=_retry, timeout=15)

        if resp.status_code == 200:
            return True, "Token प्राप्त हुआ।", resp.json()
        # Surface an actionable Hindi message for the common OAuth failures
        # instead of raw Google JSON.
        try:
            err_json = resp.json()
        except Exception:
            err_json = {}
        err_code = str(err_json.get("error", "") or "")
        err_desc = str(err_json.get("error_description", "") or resp.text)[:300]
        if err_code == "access_denied" or resp.status_code == 403:
            hint = ("Google ने एक्सेस अस्वीकार किया (403 access denied)। "
                    "Google Cloud → Google Auth Platform → Audience में इस Gmail को "
                    "'Test users' में जोड़ें, या 'Publish app' करें। बदलाव लागू होने में कुछ मिनट लगते हैं।")
        elif err_code == "redirect_uri_mismatch" or "redirect_uri" in err_desc:
            hint = ("Redirect URI मेल नहीं खा रहा। Google Cloud → Credentials → OAuth client में "
                    f"'{r_uri}' को Authorized redirect URIs में जोड़ें।")
        elif err_code == "invalid_client":
            hint = "Client ID / Client Secret गलत है — Google Cloud → Credentials से दोबारा जाँचें।"
        elif err_code == "invalid_grant":
            hint = "Authorization code समाप्त/दोबारा उपयोग हो चुका है — कृपया फिर से 'Sign in with Google' दबाएँ।"
        else:
            hint = f"Token विनिमय विफल ({resp.status_code}): {err_desc}"
        record_oauth_error(f"token_exchange {resp.status_code} {err_code}: {err_desc}")
        return False, hint, None
    except Exception as e:
        record_oauth_error(f"token_exchange exception: {e}")
        return False, f"नेटवर्क त्रुटि: {str(e)}", None


def test_google_credentials() -> Tuple[bool, str]:
    """Checks client_id/client_secret against Google without a real auth code.

    Google distinguishes the two failure modes precisely:
      * ``invalid_client`` -> the secret does not belong to this client ID
        (or was reset in the Cloud console); login can never succeed.
      * ``invalid_grant``  -> credentials are FINE; only the dummy code was
        rejected, which is expected.
    """
    cfg = load_google_config()
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    if not client_id or not client_secret:
        return False, "Client ID या Client Secret सेट नहीं है।"
    try:
        resp = requests.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": "vyas-credential-check",
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": resolve_redirect_uri(cfg.get("redirect_uri", "")),
                "grant_type": "authorization_code",
            },
            timeout=15,
        )
    except Exception as exc:
        return False, f"Google से संपर्क नहीं हो सका: {exc}"

    try:
        payload = resp.json()
    except Exception:
        payload = {}
    err = str(payload.get("error", "") or "")
    if err == "invalid_client" or resp.status_code == 401:
        return False, (
            "Client Secret गलत है — यह client ID से मेल नहीं खाता। "
            "Google Cloud Console → Clients → अपना OAuth client खोलें → "
            "Client secret कॉपी करें (या 'Add secret' से नया बनाएं) और "
            "Streamlit Cloud → Settings → Secrets में GOOGLE_CLIENT_SECRET बदलें।"
        )
    if err == "invalid_grant":
        return True, "क्रेडेंशियल्स सही हैं (Google ने केवल नकली code अस्वीकार किया, जो अपेक्षित है)।"
    if resp.status_code == 200:
        return True, "क्रेडेंशियल्स सही हैं।"
    return False, f"अप्रत्याशित प्रतिक्रिया ({resp.status_code}): {resp.text[:200]}"


def get_user_info(access_token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Retrieves Google user profile (email, name, picture)."""
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        resp = requests.get(userinfo_url, headers=headers, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return True, "सफल", {
                "email": data.get("email", ""),
                "name": data.get("name", "Google User"),
                "picture": data.get("picture", ""),
                "google_id": data.get("id", "")
            }
        else:
            return False, f"प्रोफ़ाइल प्राप्ति विफल ({resp.status_code}): {resp.text}", None
    except Exception as e:
        return False, f"नेटवर्क त्रुटि: {str(e)}", None


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """Refreshes an expired Google access token using the refresh token."""
    cfg = load_google_config()
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")

    if not client_id or not client_secret or not refresh_token:
        return None

    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }

    try:
        resp = requests.post(token_url, data=data, timeout=12)
        if resp.status_code == 200:
            return resp.json().get("access_token")
    except Exception:
        pass
    return None


def get_or_create_drive_folder(access_token: str, folder_name: str = "VYAS Kundli & Horoscopes") -> Optional[str]:
    """Finds or creates a dedicated directory in the user's Google Drive."""
    headers = {"Authorization": f"Bearer {access_token}"}
    
    # 1. Search for existing folder
    query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    search_url = f"https://www.googleapis.com/drive/v3/files?q={urllib.parse.quote(query)}&fields=files(id,name)"
    
    try:
        resp = requests.get(search_url, headers=headers, timeout=12)
        if resp.status_code == 200:
            files = resp.json().get("files", [])
            if files:
                return files[0]["id"]
    except Exception:
        pass

    # 2. Create new folder if not found
    create_url = "https://www.googleapis.com/drive/v3/files"
    meta = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder"
    }
    try:
        resp = requests.post(create_url, headers=headers, json=meta, timeout=15)
        if resp.status_code in [200, 201]:
            return resp.json().get("id")
    except Exception:
        pass

    return None


def upload_pdf_to_google_drive(
    access_token: str,
    file_path: str,
    file_display_name: Optional[str] = None,
    folder_id: Optional[str] = None
) -> Tuple[bool, str, Optional[Dict[str, str]]]:
    """
    Uploads a generated PDF file directly to Google Drive via multipart REST API.
    Returns: (success, message, {'file_id': ..., 'web_view_link': ...})
    """
    if not os.path.exists(file_path):
        return False, "अपलोड करने के लिए फ़ाइल नहीं मिली।", None

    # Get target folder
    if not folder_id:
        folder_id = get_or_create_drive_folder(access_token)

    file_name = file_display_name or os.path.basename(file_path)

    # Metadata
    metadata: Dict[str, Any] = {
        "name": file_name,
        "mimeType": "application/pdf"
    }
    if folder_id:
        metadata["parents"] = [folder_id]

    upload_url = "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,webViewLink,webContentLink"
    boundary = "-------VYAS_GOOGLE_DRIVE_BOUNDARY_789456"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": f"multipart/related; boundary={boundary}"
    }

    try:
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()

        # Build multipart payload
        part1 = (
            f"--{boundary}\r\n"
            f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{json.dumps(metadata)}\r\n"
        ).encode("utf-8")

        part2 = (
            f"--{boundary}\r\n"
            f"Content-Type: application/pdf\r\n\r\n"
        ).encode("utf-8")

        part3 = f"\r\n--{boundary}--\r\n".encode("utf-8")

        payload = part1 + part2 + pdf_bytes + part3

        resp = requests.post(upload_url, headers=headers, data=payload, timeout=40)
        if resp.status_code in [200, 201]:
            data = resp.json()
            file_id = data.get("id", "")
            view_link = data.get("webViewLink", f"https://drive.google.com/file/d/{file_id}/view?usp=sharing")
            return True, "फ़ाइल Google Drive पर सफलतापूर्वक सुरक्षित हो गई!", {
                "file_id": file_id,
                "name": file_name,
                "web_view_link": view_link
            }
        else:
            return False, f"अपलोड त्रुटि ({resp.status_code}): {resp.text}", None
    except Exception as e:
        return False, f"नेटवर्क त्रुटि: {str(e)}", None
