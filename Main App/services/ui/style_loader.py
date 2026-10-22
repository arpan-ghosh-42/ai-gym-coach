import os
import streamlit as st
import streamlit.components.v1 as components
import base64


def load_css(file_path):
    """Legacy alias - loads a CSS file and injects it via st.markdown."""
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_movexa_logo(size=38, mode="dark", show_sub=True):
    text_color = "#FFFFFF" if mode == "dark" else "#0F172A"
    sub_color = "#00E5FF" if mode == "dark" else "#0284C7"
    bg_poly = "#0F1728" if mode == "dark" else "#F1F5F9"
    sub_html = (
        f'<div style="font-size:0.62rem;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:{sub_color};margin-top:2px;">AI Biometric Coach</div>'
        if show_sub
        else ''
    )

    svg = (
        f'<svg width="{size}" height="{size}" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">'
        f'<defs>'
        f'<linearGradient id="cxGrad1" x1="0%" y1="0%" x2="100%" y2="100%"><stop offset="0%" stop-color="#00E5FF"/><stop offset="100%" stop-color="#0077FE"/></linearGradient>'
        f'<linearGradient id="cxGrad2" x1="0%" y1="100%" x2="100%" y2="0%"><stop offset="0%" stop-color="#FF9100"/><stop offset="100%" stop-color="#FF385C"/></linearGradient>'
        f'</defs>'
        f'<polygon points="50,6 90,26 90,74 50,94 10,74 10,26" fill="{bg_poly}" stroke="url(#cxGrad1)" stroke-width="4"/>'
        f'<path d="M30 30 L70 70 M70 30 L30 70" stroke="url(#cxGrad1)" stroke-width="9" stroke-linecap="round"/>'
        f'<path d="M36 50 L64 50" stroke="url(#cxGrad2)" stroke-width="6" stroke-linecap="round"/>'
        f'<circle cx="30" cy="30" r="5" fill="#00E5FF"/><circle cx="70" cy="70" r="5" fill="#00E5FF"/>'
        f'<circle cx="70" cy="30" r="5" fill="#FF9100"/><circle cx="30" cy="70" r="5" fill="#FF9100"/>'
        f'</svg>'
    )

    return (
        f'<div style="display:inline-flex;align-items:center;gap:10px;">'
        f'{svg}'
        f'<div>'
        f'<div style="font-family:Space Grotesk,sans-serif;font-size:1.35rem;font-weight:800;line-height:1;letter-spacing:-0.03em;color:{text_color};">'
        f'Move<span style="background:linear-gradient(135deg,#00E5FF,#FF9100);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">xa</span>'
        f'</div>'
        f'{sub_html}'
        f'</div>'
        f'</div>'
    )


def inject_theme(theme_mode="dark"):
    is_dark = (theme_mode == "dark")

    if is_dark:
        bg_app = "#070A10"
        bg_gradient = """
            radial-gradient(ellipse 90% 60% at 15% -10%, rgba(0, 229, 255, 0.12), transparent 60%),
            radial-gradient(ellipse 80% 50% at 85% 30%, rgba(99, 102, 241, 0.10), transparent 60%),
            radial-gradient(ellipse 60% 40% at 30% 90%, rgba(245, 158, 11, 0.07), transparent 60%),
            radial-gradient(rgba(0, 229, 255, 0.12) 1px, transparent 1px),
            radial-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px)
        """
        bg_size = "100% 100%, 100% 100%, 100% 100%, 36px 36px, 18px 18px"
        bg_sidebar = "#0B101D"
        text_main = "#F8FAFC"
        text_secondary = "#94A3B8"
        surface_card = "rgba(16, 24, 40, 0.75)"
        surface_card_hover = "rgba(22, 33, 54, 0.85)"
        border_subtle = "rgba(255, 255, 255, 0.08)"
        border_hover = "rgba(0, 229, 255, 0.4)"
        nav_bg = "rgba(13, 18, 30, 0.85)"
        input_bg = "rgba(12, 18, 30, 0.9)"
        btn_sec_bg = "rgba(22, 32, 52, 0.85)"
        btn_sec_color = "#FFFFFF"
        metric_bg = "linear-gradient(145deg, rgba(20, 28, 44, 0.85), rgba(13, 18, 30, 0.95))"
        th_bg = "rgba(20, 28, 45, 0.95)"
        th_color = "#00E5FF"
        active_glow = "0 0 24px rgba(0, 229, 255, 0.22)"
        hr_color = "rgba(255, 255, 255, 0.08)"
        popover_bg = "#0F1728"
    else:
        bg_app = "#F8FAFC"
        bg_gradient = """
            radial-gradient(ellipse 90% 50% at 15% -10%, rgba(2, 132, 199, 0.10), transparent 60%),
            radial-gradient(ellipse 70% 50% at 85% 40%, rgba(99, 102, 241, 0.07), transparent 60%),
            radial-gradient(rgba(2, 132, 199, 0.08) 1px, transparent 1px)
        """
        bg_size = "100% 100%, 100% 100%, 36px 36px"
        bg_sidebar = "#FFFFFF"
        text_main = "#0F172A"
        text_secondary = "#475569"
        surface_card = "rgba(255, 255, 255, 0.92)"
        surface_card_hover = "rgba(248, 250, 252, 0.98)"
        border_subtle = "rgba(226, 232, 240, 0.95)"
        border_hover = "rgba(2, 132, 199, 0.5)"
        nav_bg = "rgba(255, 255, 255, 0.92)"
        input_bg = "#FFFFFF"
        btn_sec_bg = "#F1F5F9"
        btn_sec_color = "#0F172A"
        metric_bg = "linear-gradient(145deg, #FFFFFF, #F8FAFC)"
        th_bg = "#F1F5F9"
        th_color = "#0284C7"
        active_glow = "0 6px 24px rgba(2, 132, 199, 0.15)"
        hr_color = "rgba(226, 232, 240, 0.9)"
        popover_bg = "#FFFFFF"

    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Grotesk:wght@500;600;700;800&display=swap');

        /* ── Base App & Background ── */
        .stApp {{
            background-color: {bg_app} !important;
            background-image: {bg_gradient} !important;
            background-size: {bg_size} !important;
            color: {text_main} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }}

        /* Solid, blurred header so page content doesn't show through the sticky top navigation */
        [data-testid="stHeader"] {{
            background: {nav_bg} !important;
            backdrop-filter: blur(14px) !important;
            border-bottom: 1px solid {border_subtle} !important;
            color: {text_main} !important;
        }}

        [data-testid="stToolbar"] {{
            background: transparent !important;
            color: {text_main} !important;
        }}

        [data-testid="stAppDeployButton"], .stAppDeployButton {{
            display: none !important;
        }}

        [data-testid="stToolbar"] button, [data-testid="stToolbar"] svg {{
            color: {text_main} !important;
        }}

        [data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            border-right: 1px solid {border_subtle} !important;
        }}

        [data-testid="stSidebar"] * {{
            color: {text_main};
        }}

        .block-container {{
            padding: 1.2rem 2.2rem 3rem !important;
            max-width: 1400px !important;
        }}

        h1, h2, h3, h4, h5, h6 {{
            font-family: 'Space Grotesk', sans-serif !important;
            letter-spacing: -0.02em !important;
            color: {text_main} !important;
        }}

        p, span, label, div {{
            font-family: 'Plus Jakarta Sans', sans-serif;
            color: {text_main};
        }}

        /* ── Buttons ── */
        button, .stButton > button, [data-testid="stBaseButton-secondary"] {{
            background: {btn_sec_bg} !important;
            border: 1px solid {border_subtle} !important;
            border-radius: 12px !important;
            color: {btn_sec_color} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            transition: all 0.22s ease !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
        }}

        button:hover, .stButton > button:hover {{
            border-color: {border_hover} !important;
            transform: translateY(-2px) !important;
            box-shadow: {active_glow} !important;
        }}

        [data-testid="stBaseButton-primary"], button[kind="primary"], .stFormSubmitButton > button {{
            background: linear-gradient(135deg, #00E5FF, #0077FE) !important;
            color: #030710 !important;
            border: none !important;
            font-weight: 700 !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 18px rgba(0,229,255,0.35) !important;
        }}

        [data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover, .stFormSubmitButton > button:hover {{
            background: linear-gradient(135deg, #33EBFF, #2697FF) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 8px 26px rgba(0,229,255,0.5) !important;
        }}

        /* ── Inputs & Selects ── */
        input, textarea, [data-baseweb="input"], [data-baseweb="select"] > div, [data-testid="stSelectbox"] > div > div {{
            background-color: {input_bg} !important;
            border: 1px solid {border_subtle} !important;
            border-radius: 10px !important;
            color: {text_main} !important;
            font-family: 'Plus Jakarta Sans', sans-serif !important;
        }}

        input:focus, [data-baseweb="input"]:focus-within {{
            border-color: #00E5FF !important;
            box-shadow: 0 0 0 2px rgba(0,229,255,0.2) !important;
        }}

        [data-baseweb="popover"], [data-baseweb="menu"], div[role="menu"] {{
            background: {surface_card} !important;
            border: 1px solid {border_subtle} !important;
            border-radius: 12px !important;
            backdrop-filter: blur(16px) !important;
        }}

        [data-baseweb="popover"] ul, [data-baseweb="popover"] li,
        [data-baseweb="menu"] ul, [data-baseweb="menu"] li,
        [role="listbox"], [role="listbox"] li, [role="option"] {{
            background-color: {popover_bg} !important;
            color: {text_main} !important;
        }}

        [role="option"] *, [data-baseweb="menu"] li * {{
            color: inherit !important;
        }}

        [role="option"]:hover, [role="option"][aria-selected="true"] {{
            background-color: rgba(0,229,255,0.16) !important;
            color: {th_color} !important;
        }}

        /* ── Form Card ── */
        .stForm {{
            background: {surface_card} !important;
            border: 1px solid {border_subtle} !important;
            border-radius: 18px !important;
            padding: 1.8rem !important;
            box-shadow: 0 14px 36px rgba(0,0,0,0.15) !important;
            backdrop-filter: blur(16px) !important;
        }}

        /* ── Metrics ── */
        [data-testid="stMetric"] {{
            background: {metric_bg} !important;
            border: 1px solid {border_subtle} !important;
            border-radius: 14px !important;
            padding: 1rem 1.2rem !important;
            box-shadow: 0 6px 20px rgba(0,0,0,0.08) !important;
            transition: all 0.22s ease !important;
        }}

        [data-testid="stMetric"]:hover {{
            border-color: {border_hover} !important;
            transform: translateY(-2px) !important;
        }}

        [data-testid="stMetricLabel"] p {{
            color: {text_secondary} !important;
            font-size: 0.8rem !important;
            font-weight: 600 !important;
            text-transform: uppercase !important;
            letter-spacing: 0.06em !important;
        }}

        [data-testid="stMetricValue"] {{
            font-family: 'Space Grotesk', sans-serif !important;
            font-size: 1.85rem !important;
            font-weight: 800 !important;
            color: {text_main} !important;
        }}

        /* ── Tables ── */
        table {{
            background: {surface_card} !important;
            color: {text_main} !important;
            width: 100% !important;
        }}

        thead tr th {{
            background: {th_bg} !important;
            color: {th_color} !important;
            font-size: 0.82rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.08em !important;
            padding: 11px 16px !important;
            border-bottom: 1px solid {border_subtle} !important;
            font-family: 'Space Grotesk', sans-serif !important;
        }}

        tbody tr td {{
            padding: 11px 16px !important;
            border-bottom: 1px solid {border_subtle} !important;
            color: {text_main} !important;
        }}

        .stTable, .stDataFrame {{
            border-radius: 14px !important;
            overflow: hidden !important;
            border: 1px solid {border_subtle} !important;
        }}

        /* ── Alerts & Dividers ── */
        [data-testid="stAlert"] {{
            border-radius: 14px !important;
            background: {surface_card} !important;
            border: 1px solid {border_subtle} !important;
            backdrop-filter: blur(10px) !important;
        }}

        hr {{
            border-color: {hr_color} !important;
        }}
    </style>
    """, unsafe_allow_html=True)


def inject_local_font(font_path, font_name):
    if not os.path.exists(font_path):
        return
    with open(font_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(font_path)[1].lstrip(".")
    fmt = {"otf": "opentype"}.get(ext, ext)
    mime = {"otf": "font/otf"}.get(ext, f"font/{ext}")
    st.markdown(f"""
        <style>
        @font-face {{
            font-family: '{font_name}';
            src: url('data:{mime};base64,{encoded}') format('{fmt}');
            font-weight: 100 900;
            font-style: normal;
        }}
        </style>
    """, unsafe_allow_html=True)


def inject_webrtc_styles(theme_mode="dark"):
    is_dark = (theme_mode == "dark")
    btn_start = "linear-gradient(135deg, #00E5FF, #0077FE)"
    btn_stop = "linear-gradient(135deg, #FF385C, #E60026)"
    text_color = "#F3F4F6" if is_dark else "#0F172A"

    components.html(
        f"""
        <script>
        (function patchWebRTCStyles() {{
            function injectIntoIframe(iframe) {{
                try {{
                    const doc = iframe.contentDocument || iframe.contentWindow.document;
                    if (!doc || !doc.head) return;
                    if (doc.head.querySelector('#webrtc-custom-styles')) return;
                    const style = doc.createElement('style');
                    style.id = 'webrtc-custom-styles';
                    style.textContent = `
                        body {{
                            background: transparent !important;
                            color: {text_color} !important;
                            font-family: 'Plus Jakarta Sans', sans-serif !important;
                        }}
                        .MuiButtonBase-root,
                        .MuiButton-root,
                        .MuiButton-contained,
                        .MuiButton-text {{
                            border-radius: 10px !important;
                            font-family: 'Plus Jakarta Sans', sans-serif !important;
                            font-weight: 700 !important;
                            letter-spacing: 0.05em !important;
                            text-transform: uppercase !important;
                            padding: 10px 24px !important;
                            transition: all 0.25s ease !important;
                            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
                        }}
                        .MuiButton-containedPrimary {{
                            background: {btn_start} !important;
                            color: #030710 !important;
                        }}
                        .MuiButton-containedSecondary,
                        .MuiButton-containedError {{
                            background: {btn_stop} !important;
                            color: #FFFFFF !important;
                        }}
                        video {{
                            border-radius: 14px !important;
                            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4) !important;
                        }}
                    `;
                    doc.head.appendChild(style);
                }} catch (e) {{
                    console.warn('[patcher] could not inject:', e);
                }}
            }}

            function findAndPatch() {{
                const parentDoc = window.parent.document;
                const iframes = parentDoc.querySelectorAll('iframe');
                iframes.forEach(iframe => {{
                    if (iframe.src && iframe.src.includes('webrtc')) {{
                        if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
                            injectIntoIframe(iframe);
                        }} else {{
                            iframe.addEventListener('load', () => injectIntoIframe(iframe));
                        }}
                    }}
                }});
            }}

            findAndPatch();
            setTimeout(findAndPatch, 500);
            setTimeout(findAndPatch, 1500);
        }})();
        </script>
        """,
        height=0,
    )
