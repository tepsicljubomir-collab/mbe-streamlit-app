import os
import io
from datetime import datetime

import pandas as pd
import streamlit as st

# 🔐 LOZINKA (lokalno default, na cloudu iz secrets)
try:
    APP_PASSWORD = st.secrets["APP_PASSWORD"]
except Exception:
    APP_PASSWORD = "MbeSesvete_123"  # lokalni default, promijeni ako želiš

# 📁 Glavni folder (lokalno) – na cloudu ćeš vjerojatno koristiti samo upload
try:
    DEFAULT_MAIN_FOLDER = st.secrets["MAIN_FOLDER"]
except Exception:
    DEFAULT_MAIN_FOLDER = r"C:\Users\tepsi\OneDrive\Fajlovi"

# ✅ PAGE CONFIG – SAMO JEDNOM!
st.set_page_config(page_title="MBE – Kombinacija Excel fajlova", layout="wide")


def check_password() -> bool:
    """Jednostavna provjera lozinke preko session_state."""

    def password_entered():
        """Poziva se kad user nešto upiše u password polje."""
        if st.session_state["app_password"] == APP_PASSWORD:
            st.session_state["password_correct"] = True
            # više ne trebamo držati lozinku u memoriji
            del st.session_state["app_password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        st.title("🔐 MBE – login")
        st.text_input(
            "Lozinka",
            type="password",
            key="app_password",
            on_change=password_entered,
        )
        if (
            st.session_state["password_correct"] is False
            and "app_password" in st.session_state
        ):
            st.error("❌ Pogrešna lozinka")
        # stopiraj ostatak appa dok lozinka nije dobra
        return False

    return True


# ⬇️ ako lozinka nije dobra, ne idemo dalje
if not check_password():
    st.stop()

# Ako je prošao login, nastavljamo s appom

st.caption("Mapiranje kolona, ujednačavanje datuma, težinski razredi, export u Excel i CSV.")

# Inicijalni main_folder u session_state
if "saved_main_folder" not in st.session_state:
    st.session_state.saved_main_folder = DEFAULT_MAIN_FOLDER

# 👉 Ovdje do sada već imaš ostatak koda (kurir_by_folder, funkcije, APP FLOW...)



# ⬇️ nakon ovoga ide tvoja prava aplikacija ⬇️

# Ovo mora biti nakon definicije funkcije, ali prije ostatka appa
if not check_password():
    st.stop()

# Sad možemo postaviti pravi layout za app
st.set_page_config(page_title="MBE – Sesvete", layout="wide")


st.caption("Mapiranje kolona, ujednačavanje datuma, težinski razredi, export u Excel i CSV.")

# Inicijalni main_folder u session_state
if "saved_main_folder" not in st.session_state:
    st.session_state.saved_main_folder = DEFAULT_MAIN_FOLDER

# ostatak TVOG postojećeg koda ide odavde nadalje:
# - definicije kurir_by_folder, default_weight_unit_by_folder, itd.
# - funkcije normalize_units, add_filter_bar, kpis_and_summary, ...
# - APP FLOW s lokalnim folderima i uploadom




# ------------------ UI POSTAVKE ------------------
st.set_page_config(page_title="MBE – Kombinacija Excel fajlova", layout="wide")
st.title("📦 MBE SESVETE")
st.caption("Mapiranje kolona, ujednačavanje datuma, težinski razredi, export u Excel i CSV.")
st.set_page_config(page_title="MBE – Kombinacija Excel fajlova", layout="wide")
# 🔐 ako lozinka nije ok, ne idemo dalje
if not check_password():
    st.stop()


# ------------------ SESSION (SPREMANJE POSTAVKI) ------------------
if "saved_main_folder" not in st.session_state:
    st.session_state.saved_main_folder = r"C:\Users\tepsi\OneDrive\Fajlovi"
    # spremnik za kombinirane podatke
if "combined_local" not in st.session_state:
    st.session_state["combined_local"] = None

if "combined_upload" not in st.session_state:
    st.session_state["combined_upload"] = None
if "filter_profiles" not in st.session_state:
    st.session_state["filter_profiles"] = {}



# ------------------ KORISNIČKE OPCIJE ------------------
st.sidebar.header("Postavke")

mode = st.sidebar.radio("Način rada", ["Lokalni folderi", "Upload fajlova"])

main_folder = st.sidebar.text_input(
    "Glavni folder (sadrži mape hp_gotovo, gls_gotovo, ...)",
    st.session_state.saved_main_folder,
)

save_prefs = st.sidebar.checkbox("Spremi ovaj glavni folder kao zadani")
if save_prefs:
    st.session_state.saved_main_folder = main_folder
    st.sidebar.success("Postavka spremljena.")

kurir_by_folder = {
    "hp_gotovo": "HP",
    "gls_gotovo": "GLS",
    "dpd_gotovo": "DPD",
    "ps_gotovo": "PS",
    "ovs_gotovo": "OVS",
}
default_weight_unit_by_folder = {
    "hp_gotovo": "g",
    "gls_gotovo": "g",
    "dpd_gotovo": "kg",
    "ps_gotovo": "g",
    "ovs_gotovo": "kg",
}

bins = [0,1,2,5,10,15,20,25,30,40,50,60,70,80,90,100,150,200,250,300,350,400,450,500,600,700,800,900,1000,float("inf")]
labels = [f"{i}. Do {v}Kg" for i, v in enumerate(
    [1,2,5,10,15,20,25,30,40,50,60,70,80,90,100,150,200,250,300,350,400,450,500,600,700,800,900,1000], 1
)] + ["29. Preko 1000Kg"]

standard_columns = [
    "Sifra_kupca","Barkod",
    "Naziv_posiljatelja","Adresa_posiljatelja",
    "Naziv_primatelja","Adresa_primatelja",
    "Iznos_otkupnine","Povrat_dokumentacije",
    "Masa_posiljke","Masa_posiljke_kg",
    "Težinski_razred","Ukupna_cijena","Kolicina",
    "SourceFile","Kurir","CreationDate","ModifiedDate","DatumFinal"
]

mapping_by_folder = {
    "hp_gotovo": {
        "Referenca 3":"Sifra_kupca","Barkod":"Barkod",
        "Pošiljatelj Naziv":"Naziv_posiljatelja","Pošiljatelj Ulica":"Adresa_posiljatelja",
        "Primatelj Naziv":"Naziv_primatelja","Primatelj Ulica":"Adresa_primatelja",
        "Iznos otkupnine":"Iznos_otkupnine","Povrat dokumentacije":"Povrat_dokumentacije",
        "Masa pošiljke":"Masa_posiljke","Ukupna cijena":"Ukupna_cijena",
        "Broj paketa u pošiljci":"Kolicina","Datum zaprimanja":"DatumFinal",
    },
    "gls_gotovo": {
        "Client reference":"Sifra_kupca","Parcel number":"Barkod",
        "Sender":"Naziv_posiljatelja","Sender's address":"Adresa_posiljatelja",
        "Receiver's name":"Naziv_primatelja","Delivery address":"Adresa_primatelja",
        "COD value":"Iznos_otkupnine","Weight / Size":"Masa_posiljke",
        "Total amount":"Ukupna_cijena","Number of the parcels in the same stop":"Kolicina",
        "Invoice date":"DatumFinal",
    },
    "dpd_gotovo": {
        "REF1":"Sifra_kupca","PARCEL NUMBER":"Barkod",
        "SENDER NAME":"Naziv_posiljatelja","SENDER CITY":"Adresa_posiljatelja",
        "RECEIVER NAME":"Naziv_primatelja","RECEIVER ADDRESS":"Adresa_primatelja",
        "COD AMOUNT":"Iznos_otkupnine","WEIGHT":"Masa_posiljke",
        "TOTAL PRICE":"Ukupna_cijena","PIECE NUMBER":"Kolicina",
        "PICKUP DATE":"DatumFinal",
    },
    "ps_gotovo": {
        "Opomba":"Sifra_kupca","Sprejemna številka":"Barkod",
        "Naziv podružnice":"Naziv_posiljatelja","Naziv naslovnika":"Naziv_primatelja",
        "Naslov naslovnika":"Adresa_primatelja","Odkupnina (EUR)":"Iznos_otkupnine",
        "Masa (g)":"Masa_posiljke","Vrednost (EUR)":"Ukupna_cijena",
        "Količina":"Kolicina","Obračunski datum":"DatumFinal",
    },
    "ovs_gotovo": {
        "Ref1":"Sifra_kupca","Barkod pošiljke":"Barkod",
        "Naziv pošiljatelja":"Naziv_posiljatelja","Adresa pošiljatelja":"Adresa_posiljatelja",
        "Naziv primatelja":"Naziv_primatelja","Adresa primatelja":"Adresa_primatelja",
        "Količina RETS":"Povrat_dokumentacije","Težin":"Masa_posiljke",
        "Ukupna cijena":"Ukupna_cijena","Paketi realno":"Kolicina",
        "Datum slanja":"DatumFinal",
    },
}

def ensure_standard(df: pd.DataFrame) -> pd.DataFrame:
    for c in standard_columns:
        if c not in df.columns:
            df[c] = None
    return df[standard_columns]

def apply_folder_mapping(df: pd.DataFrame, folder_name: str) -> pd.DataFrame:
    mapping = mapping_by_folder.get(folder_name, {})
    df = df.rename(columns={src: dst for src, dst in mapping.items() if src in df.columns})
    for col in ["Povrat_dokumentacije","Adresa_posiljatelja"]:
        if col not in df.columns:
            df[col] = None
    if folder_name == "ps_gotovo" and "Sifra_kupca" in df.columns:
        df["Sifra_kupca"] = df["Sifra_kupca"].astype(str).str[-4:].str.strip()
    return df

def normalize_units(df: pd.DataFrame, unit: str) -> pd.DataFrame:
    if "Masa_posiljke" in df.columns:
        df["Masa_posiljke"] = pd.to_numeric(df["Masa_posiljke"], errors="coerce")
        if unit == "kg":
            df["Masa_posiljke_kg"] = df["Masa_posiljke"].round(2)
            df["Masa_posiljke"] = (df["Masa_posiljke"] * 1000).round(0)
        else:
            df["Masa_posiljke_kg"] = (df["Masa_posiljke"] / 1000).round(2)
    else:
        df["Masa_posiljke"] = None
        df["Masa_posiljke_kg"] = None
    return df

def parse_datums(df: pd.DataFrame) -> pd.DataFrame:
    if "DatumFinal" in df.columns:
        df["DatumFinal"] = df["DatumFinal"].astype(str).str.strip()
        numeric_vals = pd.to_numeric(df["DatumFinal"], errors="coerce")
        converted = pd.Series(index=df.index, dtype="datetime64[ns]")

        m_num = numeric_vals.notna()
        converted.loc[m_num] = pd.to_datetime(
            numeric_vals[m_num].astype(float),
            unit="d",
            origin="1899-12-30"
        )
        m_txt = ~m_num
        converted.loc[m_txt] = pd.to_datetime(
            df.loc[m_txt, "DatumFinal"],
            errors="coerce",
            dayfirst=True
        )
        df["DatumFinal"] = converted.dt.strftime("%Y-%m-%d")
    else:
        df["DatumFinal"] = None
    return df

def add_weight_buckets(df: pd.DataFrame) -> pd.DataFrame:
    df["Težinski_razred"] = pd.cut(df["Masa_posiljke_kg"], bins=bins, labels=labels, right=False)
    return df

def process_one_df(df_raw: pd.DataFrame, folder_name: str, fname: str, base_path: str) -> pd.DataFrame:
    df = apply_folder_mapping(df_raw.copy(), folder_name)
    df = normalize_units(df, default_weight_unit_by_folder.get(folder_name, "g"))
    df = parse_datums(df)

    df["Ukupna_cijena"] = pd.to_numeric(df.get("Ukupna_cijena", 0), errors="coerce")
    df.loc[df["Ukupna_cijena"] < 1.5, "Sifra_kupca"] = 1000

    fpath = os.path.join(base_path, folder_name, fname) if base_path else None
    if fpath and os.path.exists(fpath):
        ctime = datetime.fromtimestamp(os.path.getctime(fpath))
        mtime = datetime.fromtimestamp(os.path.getmtime(fpath))
    else:
        ctime = datetime.now()
        mtime = datetime.now()

    df["SourceFile"] = fname
    df["Kurir"] = kurir_by_folder.get(folder_name, folder_name)
    df["CreationDate"] = ctime
    df["ModifiedDate"] = mtime

    df = ensure_standard(df)
    return df

def dataframe_downloads(df: pd.DataFrame, basename: str):
    # Excel (jedan sheet)
    xlsx_buf = io.BytesIO()
    df.to_excel(xlsx_buf, index=False)
    xlsx_buf.seek(0)

    # Excel (više sheetova)
    xlsx_multi = io.BytesIO()
    with pd.ExcelWriter(xlsx_multi, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="MBE_Sve", index=False)
        df.groupby("Kurir").apply(lambda d: d.drop(columns=["Kurir"])).to_excel(writer, sheet_name="Po_Kuriru")
        df.groupby("Težinski_razred").apply(lambda d: d.drop(columns=["Težinski_razred"])).to_excel(writer, sheet_name="Po_Tezinskom")
    xlsx_multi.seek(0)

    # CSV
    csv_buf = io.BytesIO()
    csv_buf.write(df.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig"))
    csv_buf.seek(0)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.download_button("⬇️ Excel (jedan sheet)", xlsx_buf, f"{basename}.xlsx")
    with col2:
        st.download_button("⬇️ Excel (više sheetova)", xlsx_multi, f"{basename}_multisheet.xlsx")
    with col3:
        st.download_button("⬇️ CSV", csv_buf, f"{basename}.csv")


# ------------------ PIPELINE: UČITAVANJE ------------------
def run_pipeline_from_folders(folder_root: str) -> pd.DataFrame:
    all_rows = []
    if not os.path.exists(folder_root):
        st.error(f"Folder ne postoji: {folder_root}")
        return pd.DataFrame(columns=standard_columns)

    for folder_name, _ in kurir_by_folder.items():
        path = os.path.join(folder_root, folder_name)
        if not os.path.exists(path):
            st.warning(f"Preskačem (ne postoji): {path}")
            continue

        for fname in os.listdir(path):
            if not fname.lower().endswith((".xlsx",".xls")):
                continue
            fpath = os.path.join(path, fname)
            try:
                df_raw = pd.read_excel(fpath)
            except PermissionError:
                st.warning(f"🔒 Zaključan file – preskačem: {fpath}")
                continue
            except Exception as e:
                st.warning(f"Greška pri čitanju {fpath}: {e}")
                continue

            df = process_one_df(df_raw, folder_name, fname, folder_root)
            all_rows.append(df)

    if not all_rows:
        return pd.DataFrame(columns=standard_columns)

    dfc = pd.concat(all_rows, ignore_index=True)
    dfc = dfc.dropna(subset=["Barkod","Sifra_kupca"], how="all")
    dfc = dfc.sort_values(by=["Kurir","CreationDate"])
    dfc = add_weight_buckets(dfc)
    return dfc

def run_pipeline_from_uploads(files, folder_name_global: str) -> pd.DataFrame:
    all_rows = []
    for uf in files:
        try:
            df_raw = pd.read_excel(uf)
        except Exception as e:
            st.warning(f"Greška pri čitanju {uf.name}: {e}")
            continue
        folder_name = folder_name_global  # sve pripada istom kuriru (jednostavnije za UI)
        df = process_one_df(df_raw, folder_name, uf.name, base_path="")
        all_rows.append(df)
    if not all_rows:
        return pd.DataFrame(columns=standard_columns)
    dfc = pd.concat(all_rows, ignore_index=True)
    dfc = dfc.dropna(subset=["Barkod","Sifra_kupca"], how="all")
    dfc = add_weight_buckets(dfc)
    return dfc

# ------------------ RUN & FILTER UI ------------------
def add_filter_bar(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.markdown("---")
    st.sidebar.header("Filteri")

    if df.empty:
        st.info("Nema podataka za filtriranje.")
        st.session_state["filter_info"] = "Nema podataka."
        return df

    # ---------- PROFILI (UČITAJ / OBRIŠI) ----------
    if "filter_profiles" not in st.session_state:
        st.session_state["filter_profiles"] = {}

    with st.sidebar.expander("Profili filtera – učitaj / obriši"):
        profiles = st.session_state["filter_profiles"]
        profile_names = list(profiles.keys())
        selected_profile = st.selectbox(
            "Odaberi profil",
            ["— nema —"] + profile_names,
            key="profile_select",
        )

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            if st.button("Učitaj profil"):
                if selected_profile != "— nema —":
                    prof = profiles[selected_profile]
                    # vrati sve spremljene vrijednosti u session_state
                    for key, value in prof.items():
                        st.session_state[key] = value
                    st.success(f"Profil '{selected_profile}' učitan.")
                    st.experimental_rerun()
        with col_p2:
            if st.button("Obriši profil"):
                if selected_profile != "— nema —":
                    del profiles[selected_profile]
                    st.session_state["filter_profiles"] = profiles
                    st.success(f"Profil '{selected_profile}' obrisan.")
                    st.experimental_rerun()

    # ---------- RESET GUMB ----------
    if st.sidebar.button("Resetiraj filtere"):
        for key in [
            "kuriri_selected",
            "kuriri_multiselect",
            "sender_query",
            "weight_bucket_query",
            "global_query",
            "masa_slider",
            "date_range",
        ]:
            if key in st.session_state:
                del st.session_state[key]

    # ---------- KURIRI + SELECT ALL / DESELECT ALL ----------
    kuriri = sorted(df["Kurir"].dropna().unique().tolist())

    if "kuriri_selected" not in st.session_state:
        st.session_state["kuriri_selected"] = kuriri

    col_k1, col_k2 = st.sidebar.columns(2)
    with col_k1:
        if st.button("Select all kuriri"):
            st.session_state["kuriri_selected"] = kuriri
    with col_k2:
        if st.button("Deselect all kuriri"):
            st.session_state["kuriri_selected"] = []

    sel_kuriri = st.sidebar.multiselect(
        "Kuriri",
        options=kuriri,
        default=st.session_state["kuriri_selected"],
        key="kuriri_multiselect",
    )
    st.session_state["kuriri_selected"] = sel_kuriri

    # ---------- DATUM ----------
    df["_Datum_dt"] = pd.to_datetime(df["DatumFinal"], errors="coerce")
    min_d = df["_Datum_dt"].min()
    max_d = df["_Datum_dt"].max()

    if pd.notna(min_d) and pd.notna(max_d):
        date_range = st.sidebar.date_input(
            "Raspon datuma (DatumFinal)",
            value=(min_d.date(), max_d.date()),
            key="date_range",
        )
    else:
        date_range = None

    # ---------- MASA (SLIDER) ----------
    s_kg = pd.to_numeric(df["Masa_posiljke_kg"], errors="coerce")
    if s_kg.notna().any():
        min_w = float(s_kg.min())
        max_w = float(s_kg.max())
    else:
        min_w, max_w = 0.0, 1.0

    w_low, w_high = st.sidebar.slider(
        "Masa (kg)",
        min_value=0.0,
        max_value=max(1.0, round(max_w + 0.5, 1)),
        value=(0.0, max(1.0, round(max_w + 0.5, 1))),
        key="masa_slider",
    )

    # ---------- SEARCH: Naziv pošiljatelja ----------
    sender_query = st.sidebar.text_input(
        "Traži po Nazivu pošiljatelja",
        key="sender_query",
    )

    # ---------- SEARCH: Težinski razred ----------
    weight_bucket_query = st.sidebar.text_input(
        "Traži po Težinskom razredu (npr. 'Do 5Kg')",
        key="weight_bucket_query",
    )

    # ---------- GLOBALNI SEARCH ----------
    global_query = st.sidebar.text_input(
        "Traži globalno (Barkod / Šifra kupca / Nazivi)",
        key="global_query",
    )

    # ========== PRIMJENA FILTERA ==========
    flt = df.copy()

    # Kuriri
    if sel_kuriri:
        flt = flt[flt["Kurir"].isin(sel_kuriri)]
    else:
        flt = flt.iloc[0:0]

    # Datum
    if date_range and isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        d1, d2 = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
        flt = flt[(flt["_Datum_dt"] >= d1) & (flt["_Datum_dt"] <= d2)]

    # Masa
    flt["Masa_posiljke_kg"] = pd.to_numeric(flt["Masa_posiljke_kg"], errors="coerce")
    flt = flt[
        (flt["Masa_posiljke_kg"] >= w_low)
        & (flt["Masa_posiljke_kg"] <= w_high)
    ]

    # Naziv pošiljatelja – text search
    if sender_query.strip():
        q = sender_query.lower()
        flt["Naziv_posiljatelja"] = flt["Naziv_posiljatelja"].astype(str)
        flt = flt[
            flt["Naziv_posiljatelja"].str.lower().str.contains(q, na=False)
        ]

    # Težinski razred – text search
    if weight_bucket_query.strip():
        q = weight_bucket_query.lower()
        flt["Težinski_razred"] = flt["Težinski_razred"].astype(str)
        flt = flt[
            flt["Težinski_razred"].str.lower().str.contains(q, na=False)
        ]

    # Globalni search
    if global_query.strip():
        q = global_query.lower()
        cols = ["Barkod", "Sifra_kupca", "Naziv_posiljatelja", "Naziv_primatelja"]
        patt = flt[cols].astype(str).apply(
            lambda s: s.str.lower().str.contains(q, na=False)
        )
        flt = flt[patt.any(axis=1)]

    # makni pomoćni stupac
    flt = flt.drop(columns=["_Datum_dt"], errors="ignore")

    # ---------- SAŽETAK FILTERA ----------
    parts = []

    if sel_kuriri:
        parts.append("Kuriri: " + ", ".join(sel_kuriri))
    else:
        parts.append("Kuriri: nijedan")

    if date_range and isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        parts.append(f"Datum: {date_range[0]} → {date_range[1]}")

    parts.append(f"Masa: {w_low:.2f}–{w_high:.2f} kg")

    if sender_query.strip():
        parts.append(f"Naziv pošiljatelja ~ '{sender_query}'")

    if weight_bucket_query.strip():
        parts.append(f"Težinski razred ~ '{weight_bucket_query}'")

    if global_query.strip():
        parts.append(f"Globalni search ~ '{global_query}'")

    if parts:
        st.session_state["filter_info"] = " | ".join(parts)
    else:
        st.session_state["filter_info"] = "Bez dodatnih filtera."

    # ---------- PROFILI (SPREMI) ----------
    with st.sidebar.expander("Profili filtera – spremi"):
        new_name = st.text_input("Naziv novog profila", key="new_profile_name")
        if st.button("Spremi trenutne filtere"):
            if new_name.strip():
                st.session_state["filter_profiles"][new_name.strip()] = {
                    "kuriri_selected": sel_kuriri,
                    "sender_query": sender_query,
                    "weight_bucket_query": weight_bucket_query,
                    "global_query": global_query,
                    "masa_slider": (w_low, w_high),
                    "date_range": date_range,
                }
                st.success(f"Profil '{new_name.strip()}' spremljen.")

    return flt




def kpis_and_summary(df: pd.DataFrame):
    if df.empty:
        return

    # ---------- KPI ----------
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Broj pošiljaka", f"{len(df):,}".replace(",", "."))
    with c2:
        st.metric("Ukupna masa (kg)", f"{pd.to_numeric(df['Masa_posiljke_kg'], errors='coerce').sum():,.2f}".replace(",", " ").replace(".", ","))
    with c3:
        st.metric("Prosj. masa (kg)", f"{pd.to_numeric(df['Masa_posiljke_kg'], errors='coerce').mean():.2f}".replace(".", ","))
    with c4:
        st.metric("Ukupna cijena", f"{pd.to_numeric(df['Ukupna_cijena'], errors='coerce').sum():,.2f} €".replace(",", " ").replace(".", ","))

    # ---------- GRAF 1: Masa po kuriru ----------
    st.subheader("📊 Masa (kg) po kuriru")
    df_grp = df.groupby("Kurir")["Masa_posiljke_kg"].sum().reset_index()
    st.bar_chart(df_grp, x="Kurir", y="Masa_posiljke_kg")

    # ---------- GRAF 2: Broj pošiljaka po danu ----------
    st.subheader("📈 Broj pošiljaka po danu (DatumFinal)")
    df_dates = df.copy()
    df_dates["DatumFinal_dt"] = pd.to_datetime(df_dates["DatumFinal"], errors="coerce")
    daily = df_dates.groupby(df_dates["DatumFinal_dt"].dt.date).size().reset_index(name="Broj")
    st.line_chart(daily, x="DatumFinal_dt", y="Broj")

    # ---------- Tablica po kuriru ----------
    grp = df.groupby("Kurir", dropna=False).agg(
        Broj=("Barkod","count"),
        Masa_kg=("Masa_posiljke_kg", lambda s: pd.to_numeric(s, errors="coerce").sum()),
        Ukupno_EUR=("Ukupna_cijena", lambda s: pd.to_numeric(s, errors="coerce").sum()),
    ).reset_index()

    grp = grp.rename(columns={"Ukupno_EUR": "Ukupno (€)"})

    st.subheader("📘 Sažetak po kuriru")
    st.dataframe(grp)


# ------------------ APP FLOW ------------------
# ------------------ APP FLOW ------------------
if mode == "Lokalni folderi":
    st.subheader("🗂️ Obrada iz lokalnih foldera")
    st.write("Očekujem podmape: `hp_gotovo`, `gls_gotovo`, `dpd_gotovo`, `ps_gotovo`, `ovs_gotovo`.")

    # Gumb pokreće obradu i sprema rezultat u session_state
    if st.button("Pokreni obradu", key="btn_run_local"):
        combined = run_pipeline_from_folders(main_folder)
        if combined.empty:
            st.warning("Nema obrađenih fajlova.")
            st.session_state["combined_local"] = None
        else:
            st.success(f"Učitano redaka: {len(combined):,}".replace(",", "."))
            st.session_state["combined_local"] = combined

    # Nakon prvog pokretanja, uvijek uzimamo iz session_state
    combined = st.session_state.get("combined_local")

    if combined is not None and not combined.empty:
        # Filteri rade nad spremljenim podacima – ne gubimo ih na rerun
        filtered = add_filter_bar(combined)
        # INFO PANEL – sažetak filtera
        filter_info = st.session_state.get("filter_info")
        if filter_info:
            st.info(f"Aktivni filteri: {filter_info}")
        kpis_and_summary(filtered)
        st.subheader("Pregled (filtrirano)")
        st.dataframe(filtered.head(500))

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        dataframe_downloads(filtered, f"MBE_short_database_clean_{ts}")

else:
    st.subheader("📥 Upload fajlova (ručno)")
    st.write("Upload više Excel fajlova, i odaberi kurira (mapira se po njegovim kolonama).")

    uploaded = st.file_uploader("Odaberi Excel fajlove", type=["xlsx","xls"], accept_multiple_files=True)
    folder_pick = st.selectbox("Kurir (za sve uploade):", list(kurir_by_folder.keys()))

    # Gumb za obradu uploada
    if uploaded and st.button("Obradi uploade", key="btn_run_upload"):
        combined = run_pipeline_from_uploads(uploaded, folder_pick)
        if combined.empty:
            st.warning("Nema obrađenih fajlova.")
            st.session_state["combined_upload"] = None
        else:
            st.success(f"Učitano redaka: {len(combined):,}".replace(",", "."))
            st.session_state["combined_upload"] = combined

    combined = st.session_state.get("combined_upload")

    if combined is not None and not combined.empty:
        filtered = add_filter_bar(combined)
        # INFO PANEL – sažetak filtera
        filter_info = st.session_state.get("filter_info")
        if filter_info:
            st.info(f"Aktivni filteri: {filter_info}")
        kpis_and_summary(filtered)
        st.subheader("Pregled (filtrirano)")
        st.dataframe(filtered.head(500))

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M")
        dataframe_downloads(filtered, f"MBE_short_database_clean_{ts}")

st.markdown("---")
st.caption("© MBE – Streamlit alat za konsolidaciju dostavnih Excel izvještaja")
