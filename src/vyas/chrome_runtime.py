"""Portable Chromium/Chrome discovery + auto-provisioning for headless PDF.

Streamlit Community Cloud ships no browser, and `packages.txt` package names
are image-specific: a single unknown name makes apt fail and takes the whole
app down (which is exactly what happened with `chromium-driver`). This module
therefore avoids apt entirely.

Resolution order:
  1. CHROME_BIN / CHROMIUM_BIN env var (explicit operator override)
  2. Well-known system paths (Windows / Linux / macOS)
  3. PATH lookup
  4. Auto-download a portable Chrome-for-Testing build into a writable cache
     dir (opt-in via VYAS_AUTO_CHROME=1, default ON for hosted Linux).
"""
from __future__ import annotations

import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from typing import Optional

# Chrome for Testing "known good versions" endpoint. Stable, no auth, no rate
# limit concerns for a handful of app boots.
CFT_LAST_KNOWN_GOOD = (
    "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"
)

_CACHE_DIR_NAME = "vyas_chrome"


def _cache_root() -> str:
    """A writable directory that survives across Streamlit reruns."""
    base = os.environ.get("VYAS_CHROME_CACHE") or os.path.join(
        os.path.expanduser("~"), ".cache", _CACHE_DIR_NAME
    )
    try:
        os.makedirs(base, exist_ok=True)
    except Exception:
        base = os.path.join(tempfile.gettempdir(), _CACHE_DIR_NAME)
        os.makedirs(base, exist_ok=True)
    return base


def _platform_key() -> Optional[str]:
    """Maps the running interpreter to a Chrome-for-Testing platform key."""
    machine = platform.machine().lower()
    if sys.platform.startswith("win"):
        return "win64" if machine in ("amd64", "x86_64") else "win32"
    if sys.platform == "darwin":
        return "mac-arm64" if machine in ("arm64", "aarch64") else "mac-x64"
    if sys.platform.startswith("linux"):
        return "linux64"
    return None


def _find_in_dir(root: str) -> Optional[str]:
    """Finds the chrome/chromium binary inside an extracted CFT build."""
    names = {"chrome", "chrome.exe", "chromium", "chromium-browser"}
    for dirpath, _dirnames, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower() in names:
                candidate = os.path.join(dirpath, fn)
                if os.path.isfile(candidate):
                    return candidate
    return None


def _download_portable_chrome(dest_root: str) -> Optional[str]:
    """Downloads + extracts a Chrome-for-Testing build. Returns exe path."""
    try:
        import requests
    except Exception:
        return None

    platform_key = _platform_key()
    if not platform_key:
        return None

    # Already provisioned?
    existing = _find_in_dir(dest_root)
    if existing:
        return existing

    try:
        resp = requests.get(CFT_LAST_KNOWN_GOOD, timeout=20)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[vyas_chrome] Could not fetch Chrome-for-Testing manifest: {exc}")
        return None

    downloads = (
        data.get("channels", {}).get("Stable", {}).get("downloads", {}).get("chrome", [])
    )
    url = next(
        (d.get("url") for d in downloads if d.get("platform") == platform_key), None
    )
    if not url:
        print(f"[vyas_chrome] No download for platform {platform_key!r}")
        return None

    archive = os.path.join(dest_root, os.path.basename(url))
    try:
        with requests.get(url, stream=True, timeout=180) as r:
            r.raise_for_status()
            with open(archive, "wb") as fh:
                for chunk in r.iter_content(chunk_size=1 << 20):
                    if chunk:
                        fh.write(chunk)

        if archive.endswith(".zip"):
            with zipfile.ZipFile(archive) as zf:
                zf.extractall(dest_root)
        elif archive.endswith((".tar.gz", ".tgz")):
            with tarfile.open(archive) as tf:
                tf.extractall(dest_root)  # noqa: S202 - trusted Google source
        else:
            print(f"[vyas_chrome] Unsupported archive: {archive}")
            return None
    except Exception as exc:  # pragma: no cover - network dependent
        print(f"[vyas_chrome] Download/extract failed: {exc}")
        return None
    finally:
        try:
            if os.path.exists(archive):
                os.remove(archive)
        except Exception:
            pass

    exe = _find_in_dir(dest_root)
    if exe and not exe.lower().endswith(".exe"):
        try:
            mode = os.stat(exe).st_mode
            os.chmod(exe, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except Exception:
            pass
    return exe


_SYSTEM_PATHS = [
    # Windows
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
    # Linux
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
    "/usr/bin/google-chrome",
    "/usr/bin/google-chrome-stable",
    "/snap/bin/chromium",
    "/opt/google/chrome/chrome",
    # macOS
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

_PATH_NAMES = (
    "chromium",
    "chromium-browser",
    "google-chrome",
    "google-chrome-stable",
    "chrome",
)


def find_chrome(allow_download: Optional[bool] = None) -> str:
    """Returns a path to a usable Chromium/Chrome binary (best effort).

    `allow_download=False` restricts to locally present browsers; the default
    auto-downloads on hosted Linux (no browser installed) so PDF generation
    works on Streamlit Community Cloud without packages.txt.
    """
    if allow_download is None:
        env = (os.environ.get("VYAS_AUTO_CHROME") or "").strip().lower()
        if env in ("0", "false", "no", "off"):
            allow_download = False
        elif env in ("1", "true", "yes", "on"):
            allow_download = True
        else:
            # Default: only auto-download on hosted Linux containers.
            allow_download = sys.platform.startswith("linux")

    # 1. Explicit override
    for env_var in ("CHROME_BIN", "CHROMIUM_BIN", "GOOGLE_CHROME_SHIM"):
        candidate = (os.environ.get(env_var) or "").strip()
        if candidate and os.path.exists(candidate):
            return candidate

    # 2. Well-known install locations
    for path in _SYSTEM_PATHS:
        if os.path.exists(path):
            return path

    # 3. PATH lookup
    for name in _PATH_NAMES:
        found = shutil.which(name)
        if found:
            return found

    # 4. Auto-provision a portable build
    if allow_download:
        exe = _download_portable_chrome(_cache_root())
        if exe:
            return exe

    return "chrome"


def chrome_available() -> bool:
    """True when a real, existing browser binary is resolvable."""
    exe = find_chrome(allow_download=False)
    return bool(exe) and os.path.exists(exe) and os.path.isfile(exe)
