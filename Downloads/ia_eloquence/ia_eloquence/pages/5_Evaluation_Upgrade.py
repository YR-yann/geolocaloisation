
import json
import os
import wave
from datetime import datetime

import av
import librosa
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyaudio
import speech_recognition as sr
import streamlit as st
from spellchecker import SpellChecker
from streamlit_webrtc import AudioProcessorBase, WebRtcMode, webrtc_streamer

p = pyaudio.PyAudio()
device_count = p.get_device_count()
for i in range(device_count):
    info = p.get_device_info_by_index(i)
    print(f"Device {i}: {info['name']}")


st.set_page_config(page_title="Évaluation & Entraînement", layout="centered")

st.title("🎧 Évaluation & Entraînement")
st.markdown("Analyse ton éloquence grâce à l'IA 🤖")

audio_path = None

st.subheader("🔊 Importer ton audio")
uploaded_file = st.file_uploader("Choisis un fichier .wav", type=["wav"])

if uploaded_file:
    audio_path = "temp_audio.wav"
    with open(audio_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    st.audio(audio_path)

st.subheader("🎙️ Ou enregistre en live")

class AudioProcessor(AudioProcessorBase):
    def __init__(self):
        self.audio_chunks = []

    def recv(self, frame: av.AudioFrame) -> av.AudioFrame:
        pcm = frame.to_ndarray().flatten()
        self.audio_chunks.append(pcm)
        return frame

ctx = webrtc_streamer(
    key="audio",
    mode=WebRtcMode.SENDONLY,
    audio_receiver_size=1024,
    rtc_configuration={"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]},
    audio_processor_factory=AudioProcessor
    # Essaye de spécifier un périphérique par défaut ou un nom spécifique
    #video_processor_factory=None,  # Si tu n'as pas besoin de vidéo
    #device="Microphone Array (Realtek(R) Audio)"
# Essayez spécifier un périphérique audio spécifique, par exemple "default" ou le nom exact de votre périphérique
)

if ctx.audio_processor and ctx.state.playing:
    st.info("🎤 Enregistrement en cours... Parle maintenant !")
elif ctx.audio_processor and not ctx.state.playing and ctx.audio_processor.audio_chunks:
    st.success("✅ Enregistrement terminé !")
    audio_np = np.concatenate(ctx.audio_processor.audio_chunks)
    audio_path = "audio_live.wav"

    with wave.open(audio_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(48000)
        wf.writeframes(audio_np.astype(np.int16).tobytes())

    st.audio(audio_path)

# ---------------------------
# Analyse si fichier dispo
# ---------------------------

if audio_path:
    st.markdown("## 🔍 Résultats de l’analyse")

    r = sr.Recognizer()
    with sr.AudioFile(audio_path) as source:
        audio = r.record(source)
        try:
            transcription = r.recognize_google(audio, language="fr-FR")
        except sr.UnknownValueError:
            transcription = "[Erreur : audio inintelligible]"

    st.markdown("### 📝 Transcription")
    st.write(transcription)

    parasites = ["euh", "bah", "donc", "voilà", "hein"]
    words = transcription.lower().split()
    parasite_words_found = [w for w in words if w in parasites]

    st.markdown("### 🚨 Mots parasites")
    st.write(parasite_words_found)

    spell = SpellChecker(language="fr")
    misspelled = spell.unknown(words)

    st.markdown("### ✍️ Fautes d’orthographe")
    st.write(misspelled)

    nb_fautes = len(misspelled)

    y, sr_librosa = librosa.load(audio_path)
    tempo, _ = librosa.beat.beat_track(y, sr=sr_librosa)
    intervals = librosa.effects.split(y, top_db=30)
    pauses = [(i[1] - i[0]) / sr_librosa for i in intervals if (i[1] - i[0]) / sr_librosa > 1.5]

    rythme_score = len(pauses) * 2
    if tempo < 70 or tempo > 160:
        rythme_score += 10

    st.markdown("### 🧠 Analyse du rythme")
    st.write(f"⏱️ Tempo estimé : {round(tempo)} BPM")
    st.write(f"💤 Nombre de longues pauses : {len(pauses)}")

    eloquence_score = 100
    eloquence_score -= nb_fautes * 2
    eloquence_score -= len(parasite_words_found) * 1.5
    eloquence_score -= rythme_score
    eloquence_score = max(eloquence_score, 0)

    st.markdown("### 🏆 Score d’éloquence")
    st.metric("Score global", f"{int(eloquence_score)} / 100")

    os.makedirs("data", exist_ok=True)
    historique_path = "data/historique.json"

    session_result = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "transcription": transcription,
        "score": int(eloquence_score),
        "mots_parasites": parasite_words_found,
        "nb_fautes": nb_fautes
    }

    if os.path.exists(historique_path):
        with open(historique_path, "r") as f:
            historique = json.load(f)
    else:
        historique = []

    historique.append(session_result)

    with open(historique_path, "w") as f:
        json.dump(historique, f, indent=4)

# ---------------------------
# Historique & graphe
# ---------------------------

st.markdown("## 📜 Historique des évaluations")
if os.path.exists("data/historique.json"):
    with open("data/historique.json", "r") as f:
        historique = json.load(f)
    for session in reversed(historique[-5:]):
        st.markdown(f"**🕒 {session['date']}**")
        st.markdown(f"- 📝 Transcription : `{session['transcription'][:100]}...`")
        st.markdown(f"- 📊 Score : {session['score']}/100")
        st.markdown(f"- 🚨 Parasites : {session['mots_parasites']}")
        st.markdown(f"- ✍️ Fautes : {session['nb_fautes']}")
        st.markdown("---")

    df = pd.DataFrame(historique)
    st.subheader("📈 Évolution de ton score")
    fig, ax = plt.subplots()
    ax.plot(df["date"], df["score"], marker="o")
    ax.set_xlabel("Date")
    ax.set_ylabel("Score")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.info("Aucun historique pour le moment.")
