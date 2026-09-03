"""Streamlit app: stáhne YouTube transcript a naformátuje ho do čitelných odstavců s časovými značkami."""

from __future__ import annotations

import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs

import streamlit as st
from youtube_transcript_api import (
    YouTubeTranscriptApi,
    TranscriptsDisabled,
    NoTranscriptFound,
    CouldNotRetrieveTranscript,
    VideoUnavailable,
)

st.set_page_config(page_title="YouTube Transcript → Markdown", page_icon="📝", layout="centered")


# ---------------------------------------------------------------------------
# Pomocné funkce
# ---------------------------------------------------------------------------

def extract_video_id(url: str) -> str | None:
    """Vytáhne 11znakové YouTube video ID z různých formátů URL (nebo přijme přímo ID)."""
    url = url.strip()

    if re.fullmatch(r"[0-9A-Za-z_-]{11}", url):
        return url

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if host in ("youtu.be", "www.youtu.be"):
        candidate = parsed.path.lstrip("/").split("/")[0]
        return candidate if re.fullmatch(r"[0-9A-Za-z_-]{11}", candidate) else None

    if "youtube.com" in host:
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            candidate = qs.get("v", [None])[0]
            return candidate if candidate and re.fullmatch(r"[0-9A-Za-z_-]{11}", candidate) else None
        for prefix in ("/embed/", "/shorts/", "/live/"):
            if parsed.path.startswith(prefix):
                candidate = parsed.path[len(prefix):].split("/")[0]
                return candidate if re.fullmatch(r"[0-9A-Za-z_-]{11}", candidate) else None

    return None


def format_timestamp(seconds: float) -> str:
    total = int(seconds)
    h, rem = divmod(total, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def group_into_paragraphs(snippets, max_gap: float, max_chars: int):
    """Seskupí jednotlivé titulkové úseky do odstavců podle pauz v řeči a délky textu."""
    paragraphs = []
    current_texts = []
    current_start = None
    prev_end = None

    for snip in snippets:
        text = snip.text.strip().replace("\n", " ")
        if not text:
            continue

        gap = (snip.start - prev_end) if prev_end is not None else 0
        current_len = sum(len(t) for t in current_texts)

        if current_texts and (gap > max_gap or current_len >= max_chars):
            paragraphs.append((current_start, " ".join(current_texts)))
            current_texts = []
            current_start = None

        if current_start is None:
            current_start = snip.start

        current_texts.append(text)
        prev_end = snip.start + snip.duration

    if current_texts:
        paragraphs.append((current_start, " ".join(current_texts)))

    return paragraphs


def build_markdown(video_id: str, language_label: str, paragraphs) -> str:
    lines = [
        f"# Přepis videa `{video_id}`",
        "",
        f"- **Zdroj:** https://www.youtube.com/watch?v={video_id}",
        f"- **Jazyk titulků:** {language_label}",
        f"- **Vygenerováno:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "---",
        "",
    ]
    for start, text in paragraphs:
        lines.append(f"**[{format_timestamp(start)}]** {text}")
        lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.title("📝 YouTube Transcript → Markdown")
st.caption("Vlož odkaz na YouTube video, stáhni titulky a exportuj je jako čitelný Markdown s časovými značkami.")

url = st.text_input("YouTube odkaz nebo video ID", placeholder="https://www.youtube.com/watch?v=...")

col1, col2 = st.columns(2)
with col1:
    preferred_languages_raw = st.text_input(
        "Preferované jazyky (kódy oddělené čárkou, v pořadí priority)",
        value="cs, en",
        help="Např. 'cs, en, sk' – zkusí se čeština, pak angličtina, pak slovenština.",
    )
with col2:
    include_generated = st.checkbox("Povolit automaticky generované titulky", value=True)

with st.expander("Pokročilé nastavení seskupování odstavců"):
    max_gap = st.slider("Max. pauza mezi větami pro nový odstavec (s)", 0.5, 10.0, 2.0, 0.5)
    max_chars = st.slider("Max. délka odstavce (znaky)", 100, 2000, 500, 50)

fetch_clicked = st.button("Stáhnout přepis", type="primary")

if "result_md" not in st.session_state:
    st.session_state.result_md = None
    st.session_state.video_id = None

if fetch_clicked:
    video_id = extract_video_id(url) if url else None

    if not video_id:
        st.error("Nepodařilo se rozpoznat video ID. Zkontroluj prosím odkaz.")
    else:
        preferred_languages = [lang.strip() for lang in preferred_languages_raw.split(",") if lang.strip()]
        if not preferred_languages:
            st.error("Zadej alespoň jeden jazykový kód (např. 'cs').")
        else:
            ytt_api = YouTubeTranscriptApi()
            try:
                transcript_list = ytt_api.list(video_id)

                try:
                    if include_generated:
                        transcript = transcript_list.find_transcript(preferred_languages)
                    else:
                        transcript = transcript_list.find_manually_created_transcript(preferred_languages)
                except NoTranscriptFound:
                    available = [
                        f"{t.language} ({t.language_code}){' – auto' if t.is_generated else ''}"
                        for t in transcript_list
                    ]
                    st.error(
                        "Pro zadané preferované jazyky nebyl nalezen žádný přepis.\n\n"
                        "Dostupné jazyky pro toto video: " + (", ".join(available) if available else "žádné")
                    )
                    transcript = None

                if transcript is not None:
                    fetched = transcript.fetch()
                    paragraphs = group_into_paragraphs(fetched, max_gap=max_gap, max_chars=max_chars)
                    language_label = f"{transcript.language} ({transcript.language_code})"
                    if transcript.is_generated:
                        language_label += " – automaticky generováno"

                    md = build_markdown(video_id, language_label, paragraphs)
                    st.session_state.result_md = md
                    st.session_state.video_id = video_id
                    st.success(f"Přepis načten – jazyk: {language_label}, počet odstavců: {len(paragraphs)}")

            except TranscriptsDisabled:
                st.error("Pro toto video jsou titulky zakázané.")
            except VideoUnavailable:
                st.error("Video není dostupné (neveřejné, smazané nebo neplatné ID).")
            except CouldNotRetrieveTranscript as exc:
                st.error(f"Přepis se nepodařilo získat: {exc}")
            except Exception as exc:  # noqa: BLE001 - zobrazíme neočekávanou chybu uživateli
                st.error(f"Nastala neočekávaná chyba: {exc}")

if st.session_state.result_md:
    st.subheader("Náhled")
    st.markdown(st.session_state.result_md)

    st.download_button(
        label="⬇️ Stáhnout jako .md",
        data=st.session_state.result_md.encode("utf-8"),
        file_name=f"transcript_{st.session_state.video_id}.md",
        mime="text/markdown",
    )
