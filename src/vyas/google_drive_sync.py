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

# Scopes needed: user profile (for Sign in with Google) + drive.file (safe, restricted access)
GOOGLE_OAUTH_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/drive.file"
]

CONFIG_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "data",
    "google_oauth_config.json"
)

# Canonical redirect URI — Google requires byte-exact match between the
# authorization request, the token exchange, and the Console registration.
DEFAULT_REDIRECT_URI = "http://localhost:8501"


def normalize_redirect_uri(uri: str) -> str:
    """Strips whitespace and trailing slashes so auth URL, token exchange and
    saved config all use the exact same redirect_uri string."""
    return (uri or "").strip().rstrip("/") or DEFAULT_REDIRECT_URI


def _get_or_create_oauth_state() -> str:
    """Per-session random nonce for CSRF protection of the OAuth callback."""
    import secrets as _secrets
    try:
        import streamlit as st
        if not st.session_state.get("oauth_state"):
            st.session_state["oauth_state"] = _secrets.token_urlsafe(16)
        return st.session_state["oauth_state"]
    except Exception:
        # Non-Streamlit callers (tests/scripts): single-use static fallback
        return "vyas_oauth"


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


def get_google_auth_url(redirect_uri: Optional[str] = None, state: Optional[str] = None) -> str:
    """Generates the official Google OAuth 2.0 authorization URL.

    A per-session random `state` nonce is generated and kept in
    st.session_state so the callback can verify the response (CSRF).
    """
    cfg = load_google_config()
    client_id = cfg.get("client_id", "")
    r_uri = normalize_redirect_uri(redirect_uri or cfg.get("redirect_uri", DEFAULT_REDIRECT_URI))
    state_val = state or _get_or_create_oauth_state()

    if not client_id:
        return ""

    params = {
        "client_id": client_id,
        "redirect_uri": r_uri,
        "response_type": "code",
        "scope": " ".join(GOOGLE_OAUTH_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "state": state_val
    }
    return f"https://accounts.google.com/o/oauth2/v2/auth?{urllib.parse.urlencode(params)}"


def exchange_code_for_tokens(code: str, redirect_uri: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
    """Exchanges Google authorization code for access and refresh tokens."""
    cfg = load_google_config()
    client_id = cfg.get("client_id", "")
    client_secret = cfg.get("client_secret", "")
    r_uri = normalize_redirect_uri(redirect_uri or cfg.get("redirect_uri", DEFAULT_REDIRECT_URI))

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

    try:
        resp = requests.post(token_url, data=data, timeout=15)
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
        return False, hint, None
    except Exception as e:
        return False, f"नेटवर्क त्रुटि: {str(e)}", None


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
