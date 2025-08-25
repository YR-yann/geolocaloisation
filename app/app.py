import time
from typing import List, Optional, Tuple

import pandas as pd
import streamlit as st
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

APP_TITLE = "Géocodage d'adresses (latitudes & longitudes)"
APP_DESC = (
    "Entrez une adresse unique ou importez un fichier Excel contenant une colonne d'adresses. "
    "L'application renvoie les latitudes et longitudes et affiche les résultats sur une carte."
)


@st.cache_resource(show_spinner=False)
def get_geocoder() -> Tuple[Nominatim, RateLimiter]:
    geolocator = Nominatim(user_agent="as-tech-import-localisation-app")
    geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1, swallow_exceptions=False)
    return geolocator, geocode


@st.cache_data(show_spinner=False)
def geocode_single(address: str) -> Optional[Tuple[float, float, str]]:
    if not address or not address.strip():
        return None
    _, geocode = get_geocoder()
    location = geocode(address)
    if location is None:
        return None
    return location.latitude, location.longitude, getattr(location, "address", "")


@st.cache_data(show_spinner=False)
def geocode_batch(addresses: List[str]) -> pd.DataFrame:
    results = []
    _, geocode = get_geocoder()
    for address in addresses:
        if not address or not str(address).strip():
            results.append({
                "adresse": address,
                "latitude": None,
                "longitude": None,
                "adresse_normalisee": None,
                "statut": "adresse vide",
            })
            continue
        try:
            location = geocode(str(address))
            if location is None:
                results.append({
                    "adresse": address,
                    "latitude": None,
                    "longitude": None,
                    "adresse_normalisee": None,
                    "statut": "introuvable",
                })
            else:
                results.append({
                    "adresse": address,
                    "latitude": location.latitude,
                    "longitude": location.longitude,
                    "adresse_normalisee": getattr(location, "address", ""),
                    "statut": "ok",
                })
        except Exception as exc:  # noqa: BLE001
            results.append({
                "adresse": address,
                "latitude": None,
                "longitude": None,
                "adresse_normalisee": None,
                "statut": f"erreur: {type(exc).__name__}",
            })
    return pd.DataFrame(results)


def ui_single():
    st.subheader("Adresse unique")
    address = st.text_input("Adresse", placeholder="Ex: 10 Rue de la Paix, 75002 Paris, France")
    if st.button("Géocoder"):
        with st.spinner("Recherche en cours…"):
            result = geocode_single(address)
        if result is None:
            st.warning("Aucun résultat trouvé.")
        else:
            lat, lon, normalized = result
            st.success("Adresse trouvée !")
            st.write(normalized)
            st.write({"latitude": lat, "longitude": lon})
            st.map(pd.DataFrame({"lat": [lat], "lon": [lon]}), latitude="lat", longitude="lon", zoom=12)


def ui_batch():
    st.subheader("Import Excel (plusieurs adresses)")
    st.caption(
        "Téléversez un fichier .xlsx. Vous pouvez soit fournir une colonne 'adresse', soit construire l'adresse à partir de plusieurs colonnes."
    )
    file = st.file_uploader("Choisir un fichier Excel .xlsx", type=["xlsx"], key="uploader_excel")
    if file is not None:
        try:
            df = pd.read_excel(file)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Impossible de lire le fichier: {exc}")
            return
        cols_lower = {c.lower(): c for c in df.columns}

        st.markdown("### Construction de l'adresse")
        st.caption(
            "Sélectionnez les colonnes qui composent l'adresse et leur ordre. Les valeurs seront concaténées avec des espaces."
        )

        default_order = [c for c in df.columns if c.strip().lower() in ["n° rue", "n°", "numero", "numéro", "type de", "rue", "ville"]]
        selected_cols = st.multiselect(
            "Colonnes à concaténer (dans l'ordre)",
            options=list(df.columns),
            default=default_order or list(df.columns)[:4],
            help="Exemples: N° rue, Type de, Rue, Ville",
            key="address_cols",
        )

        if not selected_cols and "adresse" in cols_lower:
            selected_cols = [cols_lower["adresse"]]

        def build_full_address(row) -> str:
            parts = []
            for col in selected_cols:
                if col in row and pd.notna(row[col]):
                    val = str(row[col]).strip()
                    if val:
                        parts.append(val)
            return " ".join(parts)

        if not selected_cols:
            st.error("Sélectionnez au moins une colonne d'adresse ou fournissez une colonne 'adresse'.")
            return

        addresses = df.apply(build_full_address, axis=1).astype(str).fillna("").tolist()
        original_cols_df = df[selected_cols].copy() if selected_cols else pd.DataFrame()
        original_cols_df = original_cols_df.reset_index(drop=True)
        original_cols_df["adresse_concatenee"] = pd.Series(addresses)

        start = st.button("Lancer le géocodage", key="start_batch")
        if start:
            progress = st.progress(0)
            status_area = st.empty()
            batch_results = []
            total = len(addresses)
            geocoder_df = pd.DataFrame()
            for idx, addr in enumerate(addresses, start=1):
                status_area.write(f"Géocodage {idx}/{total}…")
                # Traitement unitaire avec cache
                res = geocode_single(addr)
                if res is None:
                    batch_results.append({
                        "adresse": addr,
                        "latitude": None,
                        "longitude": None,
                        "adresse_normalisee": None,
                        "statut": "introuvable",
                    })
                else:
                    lat, lon, normalized = res
                    batch_results.append({
                        "adresse": addr,
                        "latitude": lat,
                        "longitude": lon,
                        "adresse_normalisee": normalized,
                        "statut": "ok",
                    })
                progress.progress(min(idx / total, 1.0))
            geocoder_df = pd.DataFrame(batch_results)
            # Concaténer les colonnes d'origine avec les résultats
            try:
                final_df = pd.concat([original_cols_df, geocoder_df], axis=1)
            except Exception:
                final_df = geocoder_df.copy()

            st.success("Terminé !")
            st.dataframe(final_df, use_container_width=True)

            valid_points = final_df.dropna(subset=["latitude", "longitude"])  # type: ignore[arg-type]
            if not valid_points.empty:
                st.map(valid_points.rename(columns={"latitude": "lat", "longitude": "lon"}), latitude="lat", longitude="lon")

            csv = final_df.to_csv(index=False).encode("utf-8")
            st.download_button("Télécharger CSV", data=csv, file_name="geocodage_resultats.csv", mime="text/csv")

            try:
                xlsx_buffer = pd.ExcelWriter("/tmp/geocodage_resultats.xlsx", engine="openpyxl")
                final_df.to_excel(xlsx_buffer, index=False)
                xlsx_buffer.close()
                with open("/tmp/geocodage_resultats.xlsx", "rb") as f:
                    st.download_button(
                        "Télécharger Excel",
                        data=f,
                        file_name="geocodage_resultats.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
            except Exception:
                pass


def main():
    st.set_page_config(page_title="Localisation d'adresses", page_icon="🗺️", layout="wide")
    st.title(APP_TITLE)
    st.write(APP_DESC)

    with st.sidebar:
        st.markdown("**Mode**")
        mode = st.radio("Choisir le mode", ["Adresse unique", "Fichier Excel"], label_visibility="visible", key="mode_radio")
        st.markdown("---")
        st.markdown(
            "Cette application utilise le service Nominatim d'OpenStreetMap. "
            "Veuillez saisir des adresses complètes pour de meilleurs résultats."
        )

    if mode == "Adresse unique":
        ui_single()
    else:
        ui_batch()


if __name__ == "__main__":
    main()


