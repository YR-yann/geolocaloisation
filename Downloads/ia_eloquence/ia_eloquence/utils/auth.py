
import streamlit as st

# Dictionnaire simulé pour authentification
users = {"boss@eloquence.ai": "1234"}  # à remplacer par une base réelle plus tard

def login():
    email = st.text_input("Email")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Se connecter"):
        if users.get(email) == password:
            st.success("Connexion réussie ! Accès au tableau de bord.")
            st.session_state["logged_in"] = True
        else:
            st.error("Identifiants incorrects")

def register():
    email = st.text_input("Nouvel email")
    password = st.text_input("Mot de passe", type="password")
    if st.button("Créer un compte"):
        users[email] = password
        st.success("Compte créé. Connecte-toi maintenant.")
