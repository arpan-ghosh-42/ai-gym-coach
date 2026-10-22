"""Brands Streamlit's own loader page (run once at Docker build time).

Before the app's Python code runs, the browser shows Streamlit's static index.html: a "Streamlit" tab
title, the Streamlit favicon and an empty skeleton. This script, run against the installed package:
  - replaces the tab title and favicon with Movexa's;
  - adds a full-screen "Hold tight, getting things ready…" splash with the Movexa logo, removed as soon
    as the app's first elements render (or after a safety timeout).
It is idempotent, so re-running it is harmless.

Usage (from "Main App/"):  python scripts/brand_streamlit.py
"""
import shutil
from pathlib import Path

import streamlit

APP_DIR = Path(__file__).resolve().parent.parent
BRAND_DIR = APP_DIR / "static" / "brand"
STATIC_DIR = Path(streamlit.__file__).parent / "static"
MARKER = "movexa-boot"

SPLASH = """
    <style>
      #movexa-boot { position: fixed; inset: 0; z-index: 2147483647; background: #000; display: flex;
        flex-direction: column; align-items: center; justify-content: center; gap: 22px;
        font-family: system-ui, -apple-system, "Segoe UI", sans-serif; transition: opacity .45s ease; }
      #movexa-boot img { width: min(360px, 72vw); height: auto; }
      #movexa-boot .mx-spin { width: 34px; height: 34px; border-radius: 50%; border: 3px solid rgba(139, 92, 246, .25);
        border-top-color: #8B5CF6; animation: mx-spin .9s linear infinite; }
      #movexa-boot .mx-text { color: #E2E8F0; font-size: 17px; font-weight: 600; letter-spacing: .02em; }
      #movexa-boot .mx-sub { color: #94A3B8; font-size: 13px; margin-top: -12px; }
      @keyframes mx-spin { to { transform: rotate(360deg); } }
    </style>
    <div id="movexa-boot" role="status" aria-live="polite">
      <img src="./movexa_logo.jpg" alt="Movexa" />
      <div class="mx-spin"></div>
      <div class="mx-text">Hold tight, getting things ready…</div>
      <div class="mx-sub">Your AI gym trainer is warming up</div>
    </div>
    <script>
      (function () {
        var shownAt = Date.now();
        function hide() {
          var el = document.getElementById("movexa-boot");
          if (!el) return;
          el.style.opacity = "0";
          setTimeout(function () { el.remove(); }, 500);
          clearInterval(poll);
        }
        // Ready once the app has rendered its first few elements.
        var poll = setInterval(function () {
          var rendered = document.querySelectorAll('[data-testid="stElementContainer"]').length > 2;
          if (rendered && Date.now() - shownAt > 600) hide();
        }, 150);
        setTimeout(hide, 45000);  // never trap the user if something goes wrong

        // Streamlit sets the tab title to the script name ("main") until the app's own title arrives.
        function keepTitle() { if (document.title.indexOf("Movexa") === -1) document.title = "Movexa"; }
        new MutationObserver(keepTitle).observe(document.head, { subtree: true, childList: true, characterData: true });
        keepTitle();
      })();
    </script>
"""


def main() -> None:
    shutil.copyfile(BRAND_DIR / "movexa_icon_192.png", STATIC_DIR / "favicon.png")
    shutil.copyfile(BRAND_DIR / "movexa_logo.jpg", STATIC_DIR / "movexa_logo.jpg")

    index = STATIC_DIR / "index.html"
    html = index.read_text(encoding="utf-8")
    html = html.replace("<title>Streamlit</title>", "<title>Movexa</title>")
    if MARKER not in html:
        html = html.replace("<body>", "<body>" + SPLASH, 1)
    index.write_text(html, encoding="utf-8")

    assert "<title>Movexa</title>" in html and MARKER in html, "Streamlit index.html layout changed"
    print(f"Branded Streamlit loader in {STATIC_DIR}")


if __name__ == "__main__":
    main()
