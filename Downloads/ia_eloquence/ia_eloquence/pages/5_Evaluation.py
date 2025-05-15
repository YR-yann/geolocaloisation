
import tempfile
import wave

import speech_recognition as sr
import streamlit as st
from spellchecker import SpellChecker

st.title("🎤 Évaluation & Entraînement à l'Éloquence")

st.markdown("""
Enregistre-toi ou téléverse un fichier `.wav` avec ta voix.  
Nous allons te donner une transcription, corriger ton texte, et t’indiquer les axes d’amélioration ✨
""")

# Upload de l'audio
uploaded_file = st.file_uploader("🎙️ Téléverse ton audio (.wav uniquement)", type=["wav"])

if uploaded_file is not None:
    st.audio(uploaded_file, format='audio/wav')
    st.success("Fichier chargé avec succès !")

    # Transcription vocale
    recognizer = sr.Recognizer()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
        temp_audio.write(uploaded_file.read())
        temp_audio_path = temp_audio.name

    with sr.AudioFile(temp_audio_path) as source:
        audio_data = recognizer.record(source)
        try:
            transcription = recognizer.recognize_google(audio_data, language="fr-FR")
            st.subheader("📝 Transcription brute")
            st.write(transcription)

            # Analyse IA simplifiée
            # 1. Mots parasites
            filler_words = ["euh", "donc", "bah", "hein", "voilà"]
            found_fillers = [word for word in filler_words if word in transcription.lower()]
            st.subheader("⚠️ Mots parasites détectés")
            if found_fillers:
                st.write(f"Tu as utilisé : {', '.join(found_fillers)}. Essaie de les éviter 🧘")
            else:
                st.write("Aucun mot parasite détecté. Clean 🔥")

            # 2. Correction orthographique
            spell = SpellChecker(language="fr")
            words = transcription.split()
            misspelled = spell.unknown(words)
            corrected = {word: spell.correction(word) for word in misspelled}

            st.subheader("🧠 Corrections orthographiques proposées")
            if corrected:
                for wrong, fix in corrected.items():
                    st.markdown(f"- **{wrong}** → {fix}")
            else:
                st.write("Aucune faute détectée. C’est nickel !")

            # 3. Score d'élocution (très simple pour commencer)
            word_count = len(words)
            filler_count = len(found_fillers)
            score = max(0, 100 - filler_count * 10 - len(corrected) * 5)
            st.subheader("🎯 Score d’éloquence (simulé)")
            st.metric("Score /100", score)

        except sr.UnknownValueError:
            st.error("Impossible de reconnaître la parole. Réessaye avec un fichier plus clair.")
        except sr.RequestError:
            st.error("Erreur de connexion avec l'API Google Speech Recognition.")
