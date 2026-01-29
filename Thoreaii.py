import streamlit as st
import pandas as pd
import pdfplumber
import random
import os
from typing import List, Tuple

# -----------------------------
# Konfiguration
# -----------------------------

VOCAB_STORAGE_FILE = "vocabularies.csv"
SUPPORTED_SEPARATORS = [" - ", " – ", " — ", ":", "="]

st.set_page_config(
    page_title="📚 PDF Vokabeltrainer",
    page_icon="📘",
    layout="centered"
)

# -----------------------------
# Hilfsfunktionen
# -----------------------------

def extract_text_from_pdf(file) -> str:
    """Extrahiert Text aus einer PDF-Datei."""
    text = ""
    try:
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        st.error(f"Fehler beim Lesen der PDF: {e}")
    return text


def parse_vocabulary(text: str) -> List[Tuple[str, str]]:
    """
    Analysiert Text zeilenweise und extrahiert Wortpaare.
    Gibt eine Liste von (Vokabel, Übersetzung) zurück.
    """
    vocab_pairs = []

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        for sep in SUPPORTED_SEPARATORS:
            if sep in line:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    word, translation = parts
                    word = word.strip()
                    translation = translation.strip()
                    if word and translation:
                        vocab_pairs.append((word, translation))
                break

    return vocab_pairs


def load_saved_vocabularies() -> pd.DataFrame:
    """Lädt gespeicherte Vokabeln aus CSV."""
    if os.path.exists(VOCAB_STORAGE_FILE):
        return pd.read_csv(VOCAB_STORAGE_FILE)
    return pd.DataFrame(columns=["word", "translation"])


def save_vocabularies(df: pd.DataFrame):
    """Speichert Vokabeln dauerhaft als CSV."""
    df.to_csv(VOCAB_STORAGE_FILE, index=False)


def init_session_state():
    """Initialisiert Session State Variablen."""
    if "vocab_df" not in st.session_state:
        st.session_state.vocab_df = load_saved_vocabularies()

    if "flashcards" not in st.session_state:
        st.session_state.flashcards = []

    if "current_index" not in st.session_state:
        st.session_state.current_index = 0

    if "show_translation" not in st.session_state:
        st.session_state.show_translation = False


# -----------------------------
# Initialisierung
# -----------------------------

init_session_state()

# -----------------------------
# UI – Titel
# -----------------------------

st.title("📚 Interaktiver PDF-Vokabeltrainer")
st.write(
    "Lade ein oder mehrere PDF-Dokumente mit Vokabeln hoch "
    "und lerne sie mit digitalen Lernkarten."
)

# -----------------------------
# Abschnitt 1 – PDF Upload
# -----------------------------

st.header("📄 PDFs hochladen")

uploaded_files = st.file_uploader(
    "PDF-Dateien auswählen",
    type=["pdf"],
    accept_multiple_files=True
)

if uploaded_files:
    all_vocab = []

    for file in uploaded_files:
        text = extract_text_from_pdf(file)
        vocab = parse_vocabulary(text)
        all_vocab.extend(vocab)

    if all_vocab:
        new_df = pd.DataFrame(all_vocab, columns=["word", "translation"])

        # Duplikate vermeiden
        st.session_state.vocab_df = pd.concat(
            [st.session_state.vocab_df, new_df]
        ).drop_duplicates().reset_index(drop=True)

        st.success(f"✅ {len(new_df)} neue Vokabeln erkannt.")
    else:
        st.warning("⚠️ Keine gültigen Vokabeln gefunden.")

# -----------------------------
# Abschnitt 2 – Vokabelübersicht
# -----------------------------

st.header("🗂️ Geladene Vokabeln")

if not st.session_state.vocab_df.empty:
    st.dataframe(st.session_state.vocab_df, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("💾 Vokabeln dauerhaft speichern"):
            save_vocabularies(st.session_state.vocab_df)
            st.success("Vokabeln wurden gespeichert.")

    with col2:
        if st.button("🗑️ Alle Vokabeln löschen"):
            st.session_state.vocab_df = pd.DataFrame(columns=["word", "translation"])
            st.session_state.flashcards = []
            st.success("Alle Vokabeln wurden entfernt.")
else:
    st.info("Noch keine Vokabeln geladen.")

# -----------------------------
# Abschnitt 3 – Lernmodus
# -----------------------------

st.header("🎴 Lernmodus (Flashcards)")

if st.button("🚀 Lernmodus starten"):
    if st.session_state.vocab_df.empty:
        st.warning("Bitte zuerst Vokabeln laden.")
    else:
        st.session_state.flashcards = (
            st.session_state.vocab_df.sample(frac=1).to_dict("records")
        )
        st.session_state.current_index = 0
        st.session_state.show_translation = False

if st.session_state.flashcards:
    card = st.session_state.flashcards[st.session_state.current_index]

    st.subheader(f"Vokabel {st.session_state.current_index + 1} "
                 f"von {len(st.session_state.flashcards)}")

    st.markdown(f"### 📝 {card['word']}")

    if st.session_state.show_translation:
        st.markdown(f"### ✅ {card['translation']}")
    else:
        st.markdown("### ❓ ???")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔄 Übersetzung anzeigen / verbergen"):
            st.session_state.show_translation = not st.session_state.show_translation

    with col2:
        if st.button("➡️ Nächste Karte"):
            st.session_state.current_index = (
                st.session_state.current_index + 1
            ) % len(st.session_state.flashcards)
            st.session_state.show_translation = False
