
import streamlit as st
from utils.auth import login, register

st.set_page_config(page_title="IA Éloquence", page_icon="🗣️")

st.title("🗣️ Bienvenue sur IA Éloquence")
st.subheader("Exprime-toi avec style. Apprends avec l’IA.")

menu = ["Connexion", "Inscription"]
choice = st.selectbox("Choisissez une option", menu)

if choice == "Connexion":
    login()
elif choice == "Inscription":
    register()
