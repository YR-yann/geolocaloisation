
import streamlit as st
import os
import json
from datetime import datetime
import speech_recognition as sr
from spellchecker import SpellChecker
import librosa
import numpy as np
from streamlit_audiorecorder import audiorecorder
import matplotlib.pyplot as plt
import pandas as pd

st.set_page_config(page_title="Évaluation & Entraînement", layout="wide")
st.title("🎧 Évaluation & Entraînement")

# Fonction : Analyse audio (rythme, pauses longues)
def analyze_audio(file_path):
    y, sr_ = librosa.load(file_path)
    tempo, _ = librosa.beat.beat_track(y, sr=sr_)
    duration = librosa.get_duration(y=y, sr=sr_)
    intervals = librosa.effects.split(y, top_db=30)
    pauses = [(i[1] - i[0]) / sr_ for i in intervals if (i[1] - i[0]) / sr_ > 1.5]
    rythme_score = min(len(pauses) * 5 + abs(tempo - 120) * 0.5, 25)  # max 25 pts
    return {
        "durée": round(duration, 2),
        "tempo_estimé": round(tempo, 2),
        "nb_pauses_longues": len(pauses),
        "rythme_score": round(rythme_score, 2),
        "pauses_en_secondes": [round(p, 2) for p in pauses]
    }

# Fonction : Score final
def calcul_score(total_fautes, nb_parasites, rythme_score):
    score = 100
    score -= total_fautes * 2  # max 30 pts
    score -= nb_parasites * 1.5  # max 25 pts
    score -= rythme_score       # max 25 pts
    return max(round(score), 0)

# Fonction : Transcription avec Google API
def transcribe_audio(path):
    recognizer = sr.Recognizer()
    with sr.AudioFile(path) as source:
        audio = recognizer.record(source)
    try:
        return recognizer.recognize_google(audio, language="fr-FR")
    except sr.UnknownValueError:
        return "Transcription non comprise."
    except sr.RequestError:
        return "Erreur API Google."

# Fonction : Détection fautes
def correction_orthographe(text):
    spell = SpellChecker(language='fr')
    words = text.split()
    fautes = spell.unknown(words)
    return list(fautes)

# Fonction : Détection parasites
parasites = ["euh", "bah", "enfin", "donc", "quoi", "voilà"]

def detect_parasites(text):
    words = text.lower().split()
    return [w for w in words if w in parasites]

# Upload ou Micro
audio_path = None

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("📂 Upload un fichier .wav", type=["wav"])
    if uploaded_file:
        audio_path = "temp_uploaded.wav"
        with open(audio_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success("Fichier uploadé avec succès !")

with col2:
    audio = audiorecorder("🎙️ Appuie pour enregistrer", "Relâche pour arrêter")
    if len(audio) > 0:
        st.audio(audio.tobytes(), format="audio/wav")
        audio_path = "audio_live.wav"
        with open(audio_path, "wb") as f:
            f.write(audio.tobytes())
        st.success("Micro enregistré !")

# Analyse si fichier dispo
if audio_path:
    transcription = transcribe_audio(audio_path)
    fautes = correction_orthographe(transcription)
    parasites_detectés = detect_parasites(transcription)
    rythme = analyze_audio(audio_path)
    score_final = calcul_score(len(fautes), len(parasites_detectés), rythme["rythme_score"])

    st.subheader("📝 Résultats")
    st.markdown(f"**Transcription :** {transcription}")
    st.markdown(f"**Fautes détectées :** {fautes}")
    st.markdown(f"**Parasites détectés :** {parasites_detectés}")
    st.markdown(f"**Durée :** {rythme['durée']} s — **Tempo estimé :** {rythme['tempo_estimé']} BPM")
    st.markdown(f"**Score d'éloquence :** `{score_final}/100`")

    # Sauvegarde historique
    os.makedirs("data", exist_ok=True)
    historique_path = "data/historique.json"
    session_result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transcription": transcription,
        "score": score_final,
        "mots_parasites": parasites_detectés,
        "nb_fautes": len(fautes),
    }

    if os.path.exists(historique_path):
        with open(historique_path, "r") as f:
            historique = json.load(f)
    else:
        historique = []

    historique.append(session_result)
    with open(historique_path, "w") as f:
        json.dump(historique, f, indent=4)

# Historique
with st.expander("📜 Voir l’historique des évaluations"):
    if os.path.exists("data/historique.json"):
        df = pd.read_json("data/historique.json")
        for _, row in df[::-1].iterrows():
            st.markdown(f"**🕒 {row['date']}**")
            st.markdown(f"- 📝 Transcription : `{row['transcription'][:100]}...`")
            st.markdown(f"- 📊 Score : {row['score']}/100")
            st.markdown(f"- 🚨 Parasites : {row['mots_parasites']}")
            st.markdown(f"- ✍️ Fautes : {row['nb_fautes']}")
            st.markdown("---")
    else:
        st.info("Aucune évaluation enregistrée.")

# Graphique d'évolution
with st.expander("📈 Progression dans le temps"):
    if os.path.exists("data/historique.json"):
        df = pd.read_json("data/historique.json")
        fig, ax = plt.subplots()
        ax.plot(df["date"], df["score"], marker="o")
        ax.set_xlabel("Date")
        ax.set_ylabel("Score")
        ax.set_title("Évolution de l'éloquence")
        st.pyplot(fig)
    else:
        st.info("Pas assez de données.")
