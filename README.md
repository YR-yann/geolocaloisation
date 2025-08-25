<<<<<<< HEAD
# Eloquence_project
# eloquence2
=======
## Application de géocodage d'adresses

Cette application Streamlit permet de :
- Géocoder une adresse unique (latitude/longitude)
- Importer un fichier Excel avec une colonne `adresse` et obtenir un tableau complet des latitudes/longitudes
- Visualiser les points sur une carte et exporter les résultats (CSV/Excel)

### Installation (Windows)
1. Ouvrez un terminal (CMD) dans le dossier du projet.
2. Installez les dépendances:
```
pip install -r requirements.txt
```

### Lancement
```
streamlit run app/app.py
```

### Utilisation
- Onglet « Adresse unique » : saisir une adresse complète (ex: `10 Rue de la Paix, 75002 Paris, France`).
- Onglet « Fichier Excel » : chargez un `.xlsx` contenant une colonne `adresse` (casse indifférente). Lancez le géocodage, téléchargez les résultats.

Cette application utilise le service Nominatim d'OpenStreetMap. Respectez les conditions d'utilisation et évitez un trafic excessif.


>>>>>>> e115cdb (Initial commit Streamlit)
