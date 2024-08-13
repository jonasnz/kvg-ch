import streamlit as st
import pandas as pd
from datetime import datetime

# Kanton-Kürzel-Mapping
KANTON_KUERZEL = {
    "Aargau": "AG",
    "Appenzell Ausserrhoden": "AR",
    "Appenzell Innerrhoden": "AI",
    "Basel-Landschaft": "BL",
    "Basel-Stadt": "BS",
    "Bern": "BE",
    "Freiburg": "FR",
    "Genf": "GE",
    "Glarus": "GL",
    "Graubünden": "GR",
    "Jura": "JU",
    "Luzern": "LU",
    "Neuenburg": "NE",
    "Nidwalden": "NW",
    "Obwalden": "OW",
    "Schaffhausen": "SH",
    "Schwyz": "SZ",
    "Solothurn": "SO",
    "St. Gallen": "SG",
    "Tessin": "TI",
    "Thurgau": "TG",
    "Uri": "UR",
    "Waadt": "VD",
    "Wallis": "VS",
    "Zug": "ZG",
    "Zürich": "ZH"
}

# Laden der Datenbank (aus Excel-Datei)
@st.cache_data
def load_data():
    export_df = pd.read_excel('gesamtbericht_ch.xlsx', sheet_name='Export')
    wertebereiche_df = pd.read_excel('wertebereiche.xlsx', sheet_name='Wertebereiche')
    plz_df = pd.read_excel('Liste-der-PLZ-in-Excel-Karte-Schweiz-Postleitzahlen.xlsx', sheet_name='Tabelle1')
    
    # Debugging: Zeige die Spaltennamen im DataFrame an
    st.write("Spaltennamen im Export DataFrame:", export_df.columns.tolist())
    st.write("Spaltennamen im PLZ DataFrame:", plz_df.columns.tolist())
    
    return export_df, wertebereiche_df, plz_df

export_df, wertebereiche_df, plz_df = load_data()

# Helferfunktion zur Altersberechnung
def berechne_alter(geburtsdatum):
    heute = datetime.today()
    geburtsdatum = datetime.strptime(geburtsdatum, '%Y-%m-%d')
    alter = heute.year - geburtsdatum.year - ((heute.month, heute.day) < (geburtsdatum.month, geburtsdatum.day))
    return alter

# Ermitteln der möglichen Kantone basierend auf den ersten Ziffern der Postleitzahl
def ermittle_kantone(plz_prefix):
    if len(plz_prefix) >= 2:
        plz_prefix = int(plz_prefix)
        gefiltert = plz_df[plz_df['PLZ'].astype(str).str.startswith(str(plz_prefix))]
        return gefiltert[['PLZ', 'Kanton']].drop_duplicates().values.tolist()
    return []

# Streamlit App
st.title("Krankenversicherung für Grenzgänger in der Schweiz")

# Benutzereingaben
geburtsdatum = st.date_input("Geburtsdatum")
plz_prefix = st.text_input("Erste zwei bis drei Ziffern der Postleitzahl (Schweiz)")

kantone_moeglich = ermittle_kantone(plz_prefix)
kanton_auswahl = None

if kantone_moeglich:
    kanton_auswahl = st.selectbox("Wählen Sie den Kanton:", options=kantone_moeglich, format_func=lambda x: f"PLZ: {x[0]} - Kanton: {x[1]}")
else:
    st.write("Bitte geben Sie mindestens zwei Ziffern ein, um Kantone anzuzeigen.")

geschlecht = st.selectbox("Geschlecht", options=["Männlich", "Weiblich"])
franchise = st.selectbox("Höhe der Franchise", options=["FRA-300", "FRA-500", "FRA-1000", "FRA-1500", "FRA-2000", "FRA-2500"])

# Berechnung ausführen, wenn auf den Button geklickt wird
if st.button("Versicherung berechnen") and kanton_auswahl:
    if geburtsdatum and kanton_auswahl:
        # Alter und Kanton bestimmen
        alter = berechne_alter(str(geburtsdatum))
        kanton_name = kanton_auswahl[1]
        
        # Umwandeln des Kanton-Namens in das Kürzel
        kanton = KANTON_KUERZEL.get(kanton_name, None)
        
        if kanton:
            # Filterung der Datenbank nach dem Kanton-Kürzel
            gefiltert_df = export_df[(export_df['Kanton'] == kanton) &
                                     (export_df['Franchise'] == franchise)]

            # Altersklasse bestimmen
            if alter <= 18:
                altersklasse = 'AKL-KIN'
            elif 19 <= alter <= 25:
                altersklasse = 'AKL-JUG'
            else:
                altersklasse = 'AKL-ERW'

            gefiltert_df = gefiltert_df[gefiltert_df['Altersklasse'] == altersklasse]

            # Ergebnisse anzeigen
            if not gefiltert_df.empty:
                st.subheader("Ihre Versicherungen:")
                for index, row in gefiltert_df.iterrows():
                    st.write(f"{row['Tarifbezeichnung']} - {row['Prämie']} CHF")
            else:
                st.write("Keine passenden Versicherungen gefunden.")
        else:
            st.write("Kanton konnte nicht gefunden werden.")
    else:
        st.error("Bitte alle Felder ausfüllen.")
