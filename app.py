import os
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection


# ============================================================
# KONFIGURASI APLIKASI
# ============================================================
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1WrnS3pFzkIzIF8ekYGo1fHtMLfJ7QSEPYprJrdhdy48/edit?usp=drive_web"
DEFAULT_MUSIM = "APRIL 2027 (Musim Gadu)"
DEFAULT_SALDO_AWAL = 233235079

st.set_page_config(
    page_title="Sistem Kas POKTAN SUKA MAJU",
    page_icon="🌾",
    layout="wide",
)

st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] .block-container {
            padding-top: 1rem !important;
            gap: 0.3rem !important;
        }
        div[data-testid="stSidebar"] img {
            margin-top: -15px !important;
            margin-bottom: -10px !important;
        }
        div[data-testid="stSidebar"] h1 {
            padding-top: 0px !important;
            margin-top: 0px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Kolom di worksheet pestisida mencakup jumlah_bayar.
# Untuk worksheet lama yang belum memiliki kolom ini, aplikasi akan
# memigrasikan nilainya di memori dan menuliskannya saat worksheet disimpan.
COLS_SETTINGS = ["key", "value"]
COLS_TRANSAKSI = [
    "id", "musim", "tanggal", "jenis", "kategori", "keterangan", "jumlah"
]
COLS_PESTISIDA = [
    "id", "musim", "no", "nama", "jumlah_tagihan", "jumlah_bayar", "status"
]
COLS_KREDIT = [
    "id", "musim", "no", "nama_anggota", "nama_barang", "harga_total",
    "dp", "angsuran_masuk", "status"
]
SCHEMAS = {
    "settings": COLS_SETTINGS,
    "transaksi": COLS_TRANSAKSI,
    "pestisida": COLS_PESTISIDA,
    "kredit": COLS_KREDIT,
}


# ============================================================
# UTILITAS
# ============================================================
def render_logo(container, width=130):
    base_dir = Path(__file__).resolve().parent
    logo_files = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.PNG"]
    for filename in logo_files:
        logo_path = base_dir / filename
        if logo_path.exists():
            container.image(str(logo_path), width=width)
            return True
    return False


def format_rp(value):
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = 0.0
    return f"Rp {number:,.0f}".replace(",", ".")


def to_number(value, default=0.0):
    """Konversi nilai tunggal menjadi angka tanpa memunculkan exception."""
    try:
        if pd.isna(value) or str(value).strip() == "":
            return float(default)
        return float(pd.to_numeric(value, errors="raise"))
    except (TypeError, ValueError):
        return float(default)


def next_id(df):
    """Buat ID berikutnya dari ID numerik terbesar yang tersedia."""
    if df is None or df.empty or "id" not in df.columns:
        return 1
    ids = pd.to_numeric(df["id"], errors="coerce").dropna()
    return int(ids.max()) + 1 if not ids.empty else 1


def current_date_jakarta():
    return pd.Timestamp.now(tz="Asia/Jakarta").strftime("%Y-%m-%d")


def get_pin_pengurus():
    """Ambil PIN dari Streamlit secrets atau environment variable."""
    try:
        pin = st.secrets.get("PIN_PENGURUS", None)
    except Exception:
        pin = None
    if pin is None or str(pin).strip() == "":
        pin = os.getenv("PIN_PENGURUS", "1234")
        using_default = "PIN_PENGURUS" not in os.environ
    else:
        using_default = False
    return str(pin), using_default


# ============================================================
# GOOGLE SHEETS: MEMBACA DAN MENYIMPAN DATA
# ============================================================
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except Exception as exc:
    st.error(f"Koneksi Google Sheets tidak dapat dibuat: {exc}")
    st.stop()


def load_sheet_data(worksheet_name, default_cols):
    """Baca worksheet; kegagalan baca tidak dianggap sebagai data kosong."""
    try:
        df = conn.read(
            spreadsheet=SPREADSHEET_URL,
            worksheet=worksheet_name,
            ttl=0,
        )
    except Exception as exc:
        st.error(
            f"Gagal membaca worksheet **{worksheet_name}**. "
            "Periksa nama worksheet, koneksi, dan izin Google Sheets. "
            f"Detail teknis: {exc}"
        )
        st.stop()

    if df is None or df.empty:
        return pd.DataFrame(columns=default_cols)

    df = df.copy()
    missing = [column for column in default_cols if column not in df.columns]

    # Kolom jumlah_bayar memang baru pada versi ini. Kolom tersebut boleh
    # belum tersedia pada worksheet pestisida versi lama.
    if worksheet_name == "pestisida" and missing == ["jumlah_bayar"]:
        amount = pd.to_numeric(df.get("jumlah_tagihan", 0), errors="coerce").fillna(0)
        status_lama = df.get("status", pd.Series("Belum Lunas", index=df.index))
        df["jumlah_bayar"] = amount.where(
            status_lama.astype(str).str.strip().str.lower().eq("lunas"), 0
        )
        missing = []

    if missing:
        st.error(
            f"Struktur worksheet **{worksheet_name}** tidak sesuai. "
            f"Kolom yang tidak ditemukan: {', '.join(missing)}. "
            "Periksa nama header pada baris pertama Google Sheets."
        )
        st.stop()

    # Pertahankan kolom tambahan yang mungkin sudah ada di spreadsheet.
    ordered = list(default_cols) + [c for c in df.columns if c not in default_cols]
    return df[ordered].copy()


def save_sheet_data(worksheet_name, df):
    conn.update(
        spreadsheet=SPREADSHEET_URL,
        worksheet=worksheet_name,
        data=df.reset_index(drop=True),
    )


# Memuat data satu kali untuk satu siklus eksekusi Streamlit.
data = {
    name: load_sheet_data(name, columns)
    for name, columns in SCHEMAS.items()
}


def save_multiple_sheets(updates):
    """Simpan beberapa worksheet; coba kembalikan worksheet lama bila gagal.

    Google Sheets tidak menyediakan transaksi atomik lintas worksheet. Rollback
    di sini merupakan upaya terbaik, bukan jaminan seperti transaksi database.
    """
    previous = {name: data[name].copy(deep=True) for name in updates}
    attempted = []
    try:
        for name, frame in updates.items():
            attempted.append(name)
            save_sheet_data(name, frame)
    except Exception as exc:
        rollback_errors = []
        for name in reversed(attempted):
            try:
                save_sheet_data(name, previous[name])
            except Exception as rollback_exc:
                rollback_errors.append(f"{name}: {rollback_exc}")

        st.error(
            f"Penyimpanan gagal: {exc}. Periksa Google Sheets sebelum mencoba lagi."
        )
        if rollback_errors:
            st.warning(
                "Pemulihan otomatis untuk sebagian worksheet juga gagal: "
                + "; ".join(rollback_errors)
                + ". Silakan periksa worksheet tersebut secara manual."
            )
        return False

    data.update({name: frame.copy(deep=True) for name, frame in updates.items()})
    return True


# Normalisasi tipe data setelah membaca spreadsheet.
for column in ["id"]:
    for sheet_name in ["transaksi", "pestisida", "kredit"]:
        data[sheet_name][column] = pd.to_numeric(
            data[sheet_name][column], errors="coerce"
        )

for column in ["jumlah"]:
    data["transaksi"][column] = pd.to_numeric(
        data["transaksi"][column], errors="coerce"
    ).fillna(0)

for column in ["jumlah_tagihan", "jumlah_bayar"]:
    data["pestisida"][column] = pd.to_numeric(
        data["pestisida"][column], errors="coerce"
    ).fillna(0)

for column in ["harga_total", "dp", "angsuran_masuk"]:
    data["kredit"][column] = pd.to_numeric(
        data["kredit"][column], errors="coerce"
    ).fillna(0)


# ============================================================
# PENGATURAN DAN MUSIM
# ============================================================
def get_setting(key, default_val=""):
    settings = data["settings"]
    if not settings.empty and "key" in settings.columns:
        match = settings[settings["key"].astype(str) == str(key)]
        if not match.empty:
            value = match.iloc[0].get("value", default_val)
            if pd.isna(value) or str(value).strip() == "":
                return default_val
            return str(value)
    return default_val


def upsert_settings(settings_df, values):
    updated = settings_df.copy(deep=True)
    for key, value in values.items():
        mask = updated["key"].astype(str) == str(key) if not updated.empty else pd.Series(dtype=bool)
        if not updated.empty and mask.any():
            first_index = updated.index[mask][0]
            updated.at[first_index, "value"] = str(value)
            # Bila key duplikat pernah terbentuk, sisakan satu baris saja.
            duplicates = updated.index[mask].tolist()[1:]
            if duplicates:
                updated = updated.drop(index=duplicates)
        else:
            updated = pd.concat(
                [updated, pd.DataFrame([{"key": str(key), "value": str(value)}])],
                ignore_index=True,
            )
    return updated.reset_index(drop=True)


def get_saldo_awal_musim(musim):
    value = get_setting(f"saldo_awal_{musim}", None)
    if value is None:
        value = get_setting("saldo_awal", str(DEFAULT_SALDO_AWAL))
    return to_number(value, DEFAULT_SALDO_AWAL)


def season_sort_key(name):
    """Urutkan nama musim berbasis bulan/tahun; fallback alfabetis jika tak dikenali."""
    import re

    text = str(name).upper()
    month_aliases = {
        "JAN": 1, "JANUARI": 1,
        "FEB": 2, "FEBRUARI": 2,
        "MAR": 3, "MARET": 3,
        "APR": 4, "APRIL": 4,
        "MEI": 5, "MAY": 5,
        "JUN": 6, "JUNI": 6,
        "JUL": 7, "JULI": 7,
        "AGU": 8, "AGUSTUS": 8,
        "SEP": 9, "SEPTEMBER": 9,
        "OKT": 10, "OKTOBER": 10,
        "NOV": 11, "NOVEMBER": 11,
        "DES": 12, "DESEMBER": 12,
    }
    year_match = re.search(r"\b(20\d{2})\b", text)
    year = int(year_match.group(1)) if year_match else -1
    month = -1
    for alias, month_number in month_aliases.items():
        if re.search(rf"\b{re.escape(alias)}\b", text):
            month = month_number
            break
    return (year, month, text)


def get_all_musim():
    active = get_setting("musim_aktif", DEFAULT_MUSIM)
    seasons = {active}
    for sheet_name in ["transaksi", "pestisida", "kredit"]:
        df = data[sheet_name]
        if not df.empty and "musim" in df.columns:
            seasons.update(
                str(item).strip()
                for item in df["musim"].dropna().tolist()
                if str(item).strip()
            )
    settings = data["settings"]
    if not settings.empty:
        for key in settings["key"].dropna().astype(str):
            if key.startswith("saldo_awal_"):
                name = key[len("saldo_awal_"):]
                if name.strip():
                    seasons.add(name)
    seasons.discard("")
    arsip = sorted(seasons - {active}, key=season_sort_key, reverse=True)
    return [active] + arsip


musim_aktif = get_setting("musim_aktif", DEFAULT_MUSIM)

# ============================================================
# SIDEBAR: MUSIM DAN HAK AKSES
# ============================================================
render_logo(st.sidebar, width=130)
st.sidebar.title("POKTAN SUKA MAJU")
st.sidebar.caption("Aplikasi Kas & Unit Usaha (Google Sheets)")
st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Pilih Musim Laporan")

daftar_musim = get_all_musim()
if musim_aktif not in daftar_musim:
    daftar_musim.insert(0, musim_aktif)
musim_laporan = st.sidebar.selectbox(
    "Lihat Data Musim:",
    options=daftar_musim,
    index=daftar_musim.index(musim_aktif),
)
saldo_musim_lalu = get_saldo_awal_musim(musim_laporan)

if musim_laporan == musim_aktif:
    st.sidebar.info(f"📍 **{musim_laporan}** (Musim Aktif Operasional)")
else:
    st.sidebar.warning(f"📜 **{musim_laporan}** (Arsip Musim Lalu)")

st.sidebar.markdown("---")
st.sidebar.subheader("👤 Hak Akses Pengguna")
mode_akses = st.sidebar.selectbox(
    "Pilih Peran:",
    ["👁️ Mode Anggota (Lihat Laporan)", "🔐 Mode Pengurus (Akses Edit)"],
)
PIN_PENGURUS, USING_DEFAULT_PIN = get_pin_pengurus()
is_admin = False
if mode_akses == "🔐 Mode Pengurus (Akses Edit)":
    pin_input = st.sidebar.text_input(
        "Masukkan PIN Pengurus:",
        type="password",
        help="Atur PIN lewat Streamlit secrets atau environment variable PIN_PENGURUS.",
    )
    if pin_input == PIN_PENGURUS:
        is_admin = True
        st.sidebar.success("Akses Pengurus Aktif")
        if USING_DEFAULT_PIN:
            st.sidebar.warning(
                "PIN masih memakai nilai uji coba 1234. Ganti sebelum aplikasi dipublikasikan."
            )
    elif pin_input:
        st.sidebar.error("PIN Salah!")

if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Ubah Saldo Awal Musim")
    new_saldo_awal = st.sidebar.number_input(
        f"Saldo Awal ({musim_laporan}):",
        min_value=0.0,
        value=float(saldo_musim_lalu),
        step=1000000.0,
        key=f"saldo_awal_input_{musim_laporan}",
    )
    if st.sidebar.button("Simpan Saldo Awal", key="btn_simpan_saldo_awal"):
        settings_baru = upsert_settings(
            data["settings"], {f"saldo_awal_{musim_laporan}": new_saldo_awal}
        )
        if save_multiple_sheets({"settings": settings_baru}):
            st.sidebar.success("Saldo awal tersimpan.")
            st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Pilih Menu Laporan:",
    [
        "📊 Dasbor Utama",
        "🚜 Unit Combine (Panen)",
        "⚙️ Unit Rotavator (Lahan)",
        "🧪 Unit Pestisida & Kios",
        "💳 Kredit & Cicilan Barang",
        "💸 Rincian Pengeluaran",
        "➕ Tambah Transaksi Manual",
        "🔴 Tutup Buku & Reset Musim",
    ],
)

# ============================================================
# DATA MUSIM YANG DIPILIH DAN PERHITUNGAN KEUANGAN
# ============================================================
df_transaksi_all = data["transaksi"].copy(deep=True)
df_pestisida_all = data["pestisida"].copy(deep=True)
df_kredit_all = data["kredit"].copy(deep=True)

df_transaksi = (
    df_transaksi_all[df_transaksi_all["musim"].astype(str) == musim_laporan].copy()
    if not df_transaksi_all.empty
    else pd.DataFrame(columns=COLS_TRANSAKSI)
)
df_pestisida = (
    df_pestisida_all[df_pestisida_all["musim"].astype(str) == musim_laporan].copy()
    if not df_pestisida_all.empty
    else pd.DataFrame(columns=COLS_PESTISIDA)
)
df_kredit = (
    df_kredit_all[df_kredit_all["musim"].astype(str) == musim_laporan].copy()
    if not df_kredit_all.empty
    else pd.DataFrame(columns=COLS_KREDIT)
)

# Untuk pestisida, status diturunkan dari jumlah tagihan dan pembayaran.
if not df_pestisida.empty:
    df_pestisida["jumlah_tagihan"] = pd.to_numeric(
        df_pestisida["jumlah_tagihan"], errors="coerce"
    ).fillna(0)
    df_pestisida["jumlah_bayar"] = pd.to_numeric(
        df_pestisida["jumlah_bayar"], errors="coerce"
    ).fillna(0)
    df_pestisida["sisa_tagihan"] = (
        df_pestisida["jumlah_tagihan"] - df_pestisida["jumlah_bayar"]
    ).clip(lower=0)
    df_pestisida["status"] = df_pestisida["sisa_tagihan"].apply(
        lambda x: "Lunas" if x <= 0 else "Belum Lunas"
    )

# Perhitungan kredit dibuat per transaksi sehingga kelebihan bayar satu kredit
# tidak mengurangi piutang milik anggota lain.
if not df_kredit.empty:
    for col in ["harga_total", "dp", "angsuran_masuk"]:
        df_kredit[col] = pd.to_numeric(df_kredit[col], errors="coerce").fillna(0)
    df_kredit["TOTAL_TERBAYAR"] = df_kredit["dp"] + df_kredit["angsuran_masuk"]
    df_kredit["SISA_PIUTANG"] = (
        df_kredit["harga_total"] - df_kredit["TOTAL_TERBAYAR"]
    ).clip(lower=0)
    df_kredit["KELEBIHAN_BAYAR"] = (
        df_kredit["TOTAL_TERBAYAR"] - df_kredit["harga_total"]
    ).clip(lower=0)
    df_kredit["status"] = df_kredit["SISA_PIUTANG"].apply(
        lambda x: "Lunas" if x <= 0 else "Berjalan"
    )

# Hanya transaksi kas aktual yang dihitung sebagai pemasukan/pengeluaran.
if not df_transaksi.empty:
    df_transaksi["jumlah"] = pd.to_numeric(
        df_transaksi["jumlah"], errors="coerce"
    ).fillna(0)
    df_transaksi["jenis"] = df_transaksi["jenis"].astype(str).str.strip()
    df_transaksi["kategori"] = df_transaksi["kategori"].astype(str).str.strip()
    df_pemasukan = df_transaksi[df_transaksi["jenis"] == "Pemasukan"].copy()
    df_pengeluaran = df_transaksi[df_transaksi["jenis"] == "Pengeluaran"].copy()
else:
    df_pemasukan = pd.DataFrame(columns=COLS_TRANSAKSI)
    df_pengeluaran = pd.DataFrame(columns=COLS_TRANSAKSI)

def total_kategori(df, kategori):
    if df.empty or "kategori" not in df.columns or "jumlah" not in df.columns:
        return 0.0
    return float(df.loc[df["kategori"] == kategori, "jumlah"].sum())


tot_combine = total_kategori(df_pemasukan, "Combine")
tot_rotavator = total_kategori(df_pemasukan, "Rotavator")
tot_pestisida_trans = total_kategori(df_pemasukan, "Pestisida")
tot_oven = total_kategori(df_pemasukan, "Oven")
tot_kredit_masuk = float(
    df_pemasukan.loc[
        df_pemasukan["kategori"].isin(["Kredit Barang", "Kredit Cicilan Barang"]),
        "jumlah",
    ].sum()
) if not df_pemasukan.empty else 0.0

known_categories = {
    "Combine", "Rotavator", "Pestisida", "Oven",
    "Kredit Barang", "Kredit Cicilan Barang",
}
pemasukan_tambahan = float(
    df_pemasukan.loc[~df_pemasukan["kategori"].isin(known_categories), "jumlah"].sum()
) if not df_pemasukan.empty else 0.0

tot_pemasukan_usaha = float(df_pemasukan["jumlah"].sum()) if not df_pemasukan.empty else 0.0
tot_pengeluaran = float(df_pengeluaran["jumlah"].sum()) if not df_pengeluaran.empty else 0.0
saldo_akhir_kas = saldo_musim_lalu + tot_pemasukan_usaha - tot_pengeluaran

tot_tagihan_pestisida = (
    float(df_pestisida["jumlah_tagihan"].sum()) if not df_pestisida.empty else 0.0
)
tot_pembayaran_pestisida = (
    float(df_pestisida["jumlah_bayar"].sum()) if not df_pestisida.empty else 0.0
)
tot_sisa_tagihan_pestisida = (
    float(df_pestisida["sisa_tagihan"].sum()) if not df_pestisida.empty else 0.0
)
tot_nilai_kredit = float(df_kredit["harga_total"].sum()) if not df_kredit.empty else 0.0
tot_kredit_terbayar = float(df_kredit["TOTAL_TERBAYAR"].sum()) if not df_kredit.empty else 0.0
tot_sisa_piutang = float(df_kredit["SISA_PIUTANG"].sum()) if not df_kredit.empty else 0.0


# ============================================================
# DASBOR UTAMA
# ============================================================
if menu == "📊 Dasbor Utama":
    st.title("Dasbor Utama Kas POKTAN SUKA MAJU")
    st.caption(
        f"Status Pengguna: **{mode_akses}** | Menampilkan laporan musim: **{musim_laporan}**"
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Pemasukan Kas", format_rp(tot_pemasukan_usaha))
    col2.metric("Total Pengeluaran Kas", format_rp(tot_pengeluaran))
    col3.metric("Saldo Awal Musim", format_rp(saldo_musim_lalu))
    col4.metric("SALDO AKHIR KAS", format_rp(saldo_akhir_kas))

    st.markdown("---")
    extra1, extra2 = st.columns(2)
    extra1.metric("Sisa Tagihan Pestisida", format_rp(tot_sisa_tagihan_pestisida))
    extra2.metric("Sisa Piutang Kredit Barang", format_rp(tot_sisa_piutang))

    chart1, chart2 = st.columns(2)
    with chart1:
        st.subheader("📈 Pemasukan Kas per Kategori")
        if not df_pemasukan.empty:
            df_chart = (
                df_pemasukan.groupby("kategori", dropna=False)["jumlah"]
                .sum().reset_index()
            )
            df_chart = df_chart[df_chart["jumlah"] > 0]
            if not df_chart.empty:
                fig_pie = px.pie(
                    df_chart, values="jumlah", names="kategori", hole=0.4
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            else:
                st.info("Belum ada pemasukan positif untuk divisualisasikan.")
        else:
            st.info("Belum ada transaksi pemasukan pada musim ini.")

    with chart2:
        st.subheader("📊 Ringkasan Kas (Juta Rupiah)")
        df_bar = pd.DataFrame({
            "Kategori": ["Pemasukan", "Saldo Awal", "Pengeluaran", "Saldo Akhir"],
            "Jumlah": [
                tot_pemasukan_usaha / 1_000_000,
                saldo_musim_lalu / 1_000_000,
                tot_pengeluaran / 1_000_000,
                saldo_akhir_kas / 1_000_000,
            ],
        })
        fig_bar = px.bar(df_bar, x="Kategori", y="Jumlah", text="Jumlah", color="Kategori")
        fig_bar.update_traces(texttemplate="%{text:,.1f} Jt", textposition="outside")
        fig_bar.update_layout(yaxis_title="Juta Rupiah", yaxis_tickformat=",.1f")
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown(f"### 📝 Rekap Pemasukan Musim ({musim_laporan})")
    rekap = pd.DataFrame({
        "Sumber Pemasukan": [
            "Combine", "Rotavator", "Pestisida", "Oven",
            "Kredit Barang dan Cicilan", "Pemasukan Kategori Lain", "TOTAL PEMASUKAN KAS",
        ],
        "Nilai Total": [
            format_rp(tot_combine), format_rp(tot_rotavator),
            format_rp(tot_pestisida_trans), format_rp(tot_oven),
            format_rp(tot_kredit_masuk), format_rp(pemasukan_tambahan),
            format_rp(tot_pemasukan_usaha),
        ],
    })
    st.dataframe(rekap, use_container_width=True, hide_index=True)


# ============================================================
# UNIT COMBINE
# ============================================================
elif menu == "🚜 Unit Combine (Panen)":
    st.title("🚜 Laporan Hasil Panen - Combine Harvester")
    st.caption(f"Menampilkan data musim: **{musim_laporan}**")
    st.metric("TOTAL PENDAPATAN COMBINE", format_rp(tot_combine))
    rows = df_pemasukan[df_pemasukan["kategori"] == "Combine"] if not df_pemasukan.empty else pd.DataFrame()
    if rows.empty:
        st.info("Belum ada pemasukan Combine pada musim ini.")
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True)


# ============================================================
# UNIT ROTAVATOR
# ============================================================
elif menu == "⚙️ Unit Rotavator (Lahan)":
    st.title("⚙️ Laporan Pengolahan Lahan - Rotavator")
    st.caption(f"Menampilkan data musim: **{musim_laporan}**")
    st.metric("TOTAL PENDAPATAN ROTAVATOR", format_rp(tot_rotavator))
    rows = df_pemasukan[df_pemasukan["kategori"] == "Rotavator"] if not df_pemasukan.empty else pd.DataFrame()
    if rows.empty:
        st.info("Belum ada pemasukan Rotavator pada musim ini.")
    else:
        st.dataframe(rows, use_container_width=True, hide_index=True)


# ============================================================
# PESTISIDA & KIOS
# ============================================================
elif menu == "🧪 Unit Pestisida & Kios":
    st.title("🧪 Laporan Tagihan, Pembayaran, dan Pestisida")
    st.caption(f"Menampilkan data musim: **{musim_laporan}**")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Tagihan", format_rp(tot_tagihan_pestisida))
    m2.metric("Total Dibayar", format_rp(tot_pembayaran_pestisida))
    m3.metric("Sisa Tagihan", format_rp(tot_sisa_tagihan_pestisida))

    st.markdown("---")
    if not df_pestisida.empty:
        tampil_pestisida = df_pestisida.copy()
        tampil_pestisida = tampil_pestisida.rename(columns={
            "jumlah_tagihan": "Jumlah Tagihan",
            "jumlah_bayar": "Jumlah Dibayar",
            "sisa_tagihan": "Sisa Tagihan",
        })
        st.dataframe(tampil_pestisida, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada tagihan pestisida pada musim ini.")

    pst_transactions = df_pemasukan[df_pemasukan["kategori"] == "Pestisida"] if not df_pemasukan.empty else pd.DataFrame()
    if not pst_transactions.empty:
        st.subheader("📜 Riwayat Penerimaan Pembayaran Pestisida")
        st.dataframe(pst_transactions, use_container_width=True, hide_index=True)

    if is_admin and musim_laporan == musim_aktif:
        st.markdown("---")
        col_add, col_pay = st.columns(2)
        with col_add:
            st.subheader("➕ Tambah Tagihan Anggota")
            with st.form("form_add_pestisida", clear_on_submit=True):
                nama_p = st.text_input("Nama Anggota")
                tagihan_p = st.number_input(
                    "Jumlah Tagihan (Rp)", min_value=1, step=50000, value=50000
                )
                simpan_tagihan = st.form_submit_button("Simpan Tagihan")
                if simpan_tagihan:
                    if not nama_p.strip():
                        st.error("Nama anggota wajib diisi.")
                    else:
                        new_id = next_id(data["pestisida"])
                        row = pd.DataFrame([{
                            "id": new_id,
                            "musim": musim_aktif,
                            "no": new_id,
                            "nama": nama_p.strip(),
                            "jumlah_tagihan": float(tagihan_p),
                            "jumlah_bayar": 0.0,
                            "status": "Belum Lunas",
                        }])
                        updated = pd.concat([data["pestisida"], row], ignore_index=True)
                        if save_multiple_sheets({"pestisida": updated}):
                            st.success("Tagihan pestisida berhasil ditambahkan.")
                            st.rerun()

        with col_pay:
            st.subheader("💰 Catat Pembayaran Tagihan")
            if not df_pestisida.empty:
                belum_lunas = df_pestisida[df_pestisida["sisa_tagihan"] > 0].copy()
            else:
                belum_lunas = pd.DataFrame()

            if belum_lunas.empty:
                st.info("Tidak ada tagihan pestisida yang belum lunas.")
            else:
                id_options = belum_lunas["id"].dropna().tolist()
                label_lookup = {
                    row["id"]: (
                        f"{row['id']} - {row['nama']} | sisa {format_rp(row['sisa_tagihan'])}"
                    )
                    for _, row in belum_lunas.iterrows()
                }
                with st.form("form_bayar_pestisida", clear_on_submit=True):
                    pestisida_id = st.selectbox(
                        "Pilih tagihan anggota:", id_options,
                        format_func=lambda item: label_lookup.get(item, str(item)),
                    )
                    selected_row = belum_lunas[
                        pd.to_numeric(belum_lunas["id"], errors="coerce") == float(pestisida_id)
                    ].iloc[0]
                    sisa_pilih = float(selected_row["sisa_tagihan"])
                    jumlah_bayar_p = st.number_input(
                        "Nominal Pembayaran (Rp)", min_value=1,
                        max_value=max(1, int(sisa_pilih)), step=50000,
                        value=min(50000, max(1, int(sisa_pilih))),
                    )
                    ket_p = st.text_input("Keterangan", value="Pembayaran tagihan pestisida")
                    bayar_p = st.form_submit_button("Simpan Pembayaran")
                    if bayar_p:
                        idmask = pd.to_numeric(data["pestisida"]["id"], errors="coerce") == float(pestisida_id)
                        matching = data["pestisida"].index[idmask].tolist()
                        if len(matching) != 1:
                            st.error("ID tagihan tidak unik atau tidak ditemukan. Periksa worksheet pestisida.")
                        elif jumlah_bayar_p > sisa_pilih:
                            st.error("Pembayaran tidak boleh melebihi sisa tagihan.")
                        else:
                            idx = matching[0]
                            pst_new = data["pestisida"].copy(deep=True)
                            paid_before = to_number(pst_new.at[idx, "jumlah_bayar"])
                            paid_after = paid_before + float(jumlah_bayar_p)
                            bill_total = to_number(pst_new.at[idx, "jumlah_tagihan"])
                            pst_new.at[idx, "jumlah_bayar"] = paid_after
                            pst_new.at[idx, "status"] = "Lunas" if paid_after >= bill_total else "Belum Lunas"

                            trans_id = next_id(data["transaksi"])
                            trans_row = pd.DataFrame([{
                                "id": trans_id,
                                "musim": musim_aktif,
                                "tanggal": current_date_jakarta(),
                                "jenis": "Pemasukan",
                                "kategori": "Pestisida",
                                "keterangan": f"{ket_p.strip() or 'Pembayaran pestisida'} - {selected_row['nama']}",
                                "jumlah": float(jumlah_bayar_p),
                            }])
                            trans_new = pd.concat([data["transaksi"], trans_row], ignore_index=True)
                            if save_multiple_sheets({"pestisida": pst_new, "transaksi": trans_new}):
                                st.success("Pembayaran pestisida berhasil dicatat.")
                                st.rerun()


# ============================================================
# KREDIT BARANG
# ============================================================
elif menu == "💳 Kredit & Cicilan Barang":
    st.title("💳 Laporan Kredit & Cicilan Barang Anggota")
    st.caption(f"Menampilkan data musim: **{musim_laporan}**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Nilai Barang", format_rp(tot_nilai_kredit))
    c2.metric("Total Terbayar (DP + Angsuran)", format_rp(tot_kredit_terbayar))
    c3.metric("Sisa Piutang Anggota", format_rp(tot_sisa_piutang))

    st.markdown("---")
    if not df_kredit.empty:
        st.dataframe(df_kredit, use_container_width=True, hide_index=True)
        if (df_kredit["KELEBIHAN_BAYAR"] > 0).any():
            st.warning("Ada data kredit lama dengan pembayaran melebihi harga barang. Periksa catatan terkait.")
    else:
        st.info("Belum ada data kredit barang pada musim ini.")

    credit_transactions = df_pemasukan[
        df_pemasukan["kategori"].isin(["Kredit Barang", "Kredit Cicilan Barang"])
    ] if not df_pemasukan.empty else pd.DataFrame()
    if not credit_transactions.empty:
        st.subheader("📜 Riwayat DP dan Setoran Cicilan")
        st.dataframe(credit_transactions, use_container_width=True, hide_index=True)

    if is_admin and musim_laporan == musim_aktif:
        st.markdown("---")
        col_form1, col_form2 = st.columns(2)
        with col_form1:
            st.subheader("➕ Buat Kredit Barang Baru")
            with st.form("form_add_kredit", clear_on_submit=True):
                nama_k = st.text_input("Nama Anggota")
                barang_k = st.text_input("Nama Barang")
                harga_k = st.number_input("Harga Total (Rp)", min_value=1, step=100000, value=100000)
                dp_k = st.number_input("DP / Uang Muka (Rp)", min_value=0, step=50000, value=0)
                simpan_kredit = st.form_submit_button("Simpan Data Kredit")
                if simpan_kredit:
                    if not nama_k.strip() or not barang_k.strip():
                        st.error("Nama anggota dan nama barang wajib diisi.")
                    elif dp_k > harga_k:
                        st.error("DP tidak boleh melebihi harga total barang.")
                    else:
                        kredit_id = next_id(data["kredit"])
                        status = "Lunas" if dp_k >= harga_k else "Berjalan"
                        row = pd.DataFrame([{
                            "id": kredit_id,
                            "musim": musim_aktif,
                            "no": kredit_id,
                            "nama_anggota": nama_k.strip(),
                            "nama_barang": barang_k.strip(),
                            "harga_total": float(harga_k),
                            "dp": float(dp_k),
                            "angsuran_masuk": 0.0,
                            "status": status,
                        }])
                        kredit_new = pd.concat([data["kredit"], row], ignore_index=True)
                        updates = {"kredit": kredit_new}

                        # DP yang benar-benar diterima juga dicatat sebagai kas masuk.
                        if dp_k > 0:
                            trans_id = next_id(data["transaksi"])
                            trans_row = pd.DataFrame([{
                                "id": trans_id,
                                "musim": musim_aktif,
                                "tanggal": current_date_jakarta(),
                                "jenis": "Pemasukan",
                                "kategori": "Kredit Barang",
                                "keterangan": f"DP kredit - {nama_k.strip()} - {barang_k.strip()}",
                                "jumlah": float(dp_k),
                            }])
                            updates["transaksi"] = pd.concat(
                                [data["transaksi"], trans_row], ignore_index=True
                            )

                        if save_multiple_sheets(updates):
                            st.success("Data kredit berhasil disimpan.")
                            st.rerun()

        with col_form2:
            st.subheader("💰 Catat Pembayaran Angsuran")
            if not df_kredit.empty:
                kredit_berjalan = df_kredit[df_kredit["SISA_PIUTANG"] > 0].copy()
            else:
                kredit_berjalan = pd.DataFrame()

            if kredit_berjalan.empty:
                st.info("Tidak ada kredit berjalan yang memiliki sisa piutang.")
            else:
                credit_ids = kredit_berjalan["id"].dropna().tolist()
                credit_labels = {
                    row["id"]: (
                        f"{row['id']} - {row['nama_anggota']} ({row['nama_barang']}) "
                        f"| sisa {format_rp(row['SISA_PIUTANG'])}"
                    )
                    for _, row in kredit_berjalan.iterrows()
                }
                with st.form("form_bayar_angsuran", clear_on_submit=True):
                    kredit_id_pilihan = st.selectbox(
                        "Pilih Anggota & Barang:", credit_ids,
                        format_func=lambda item: credit_labels.get(item, str(item)),
                    )
                    selected_credit = kredit_berjalan[
                        pd.to_numeric(kredit_berjalan["id"], errors="coerce") == float(kredit_id_pilihan)
                    ].iloc[0]
                    sisa_kredit = float(selected_credit["SISA_PIUTANG"])
                    nominal_angsuran = st.number_input(
                        "Nominal Angsuran (Rp)", min_value=1,
                        max_value=max(1, int(sisa_kredit)), step=50000,
                        value=min(50000, max(1, int(sisa_kredit))),
                    )
                    keterangan_angsuran = st.text_input(
                        "Keterangan", value="Angsuran Cicilan"
                    )
                    bayar_kredit = st.form_submit_button("Simpan Angsuran")
                    if bayar_kredit:
                        idmask = pd.to_numeric(data["kredit"]["id"], errors="coerce") == float(kredit_id_pilihan)
                        matching = data["kredit"].index[idmask].tolist()
                        if len(matching) != 1:
                            st.error("ID kredit tidak unik atau tidak ditemukan. Periksa worksheet kredit.")
                        elif nominal_angsuran > sisa_kredit:
                            st.error("Angsuran tidak boleh melebihi sisa piutang.")
                        else:
                            idx = matching[0]
                            kredit_new = data["kredit"].copy(deep=True)
                            sebelumnya = to_number(kredit_new.at[idx, "angsuran_masuk"])
                            kredit_new.at[idx, "angsuran_masuk"] = sebelumnya + float(nominal_angsuran)
                            total_terbayar = (
                                to_number(kredit_new.at[idx, "dp"])
                                + to_number(kredit_new.at[idx, "angsuran_masuk"])
                            )
                            harga = to_number(kredit_new.at[idx, "harga_total"])
                            kredit_new.at[idx, "status"] = "Lunas" if total_terbayar >= harga else "Berjalan"

                            trans_id = next_id(data["transaksi"])
                            trans_row = pd.DataFrame([{
                                "id": trans_id,
                                "musim": musim_aktif,
                                "tanggal": current_date_jakarta(),
                                "jenis": "Pemasukan",
                                "kategori": "Kredit Cicilan Barang",
                                "keterangan": (
                                    f"{keterangan_angsuran.strip() or 'Angsuran Cicilan'} - "
                                    f"{selected_credit['nama_anggota']} - {selected_credit['nama_barang']}"
                                ),
                                "jumlah": float(nominal_angsuran),
                            }])
                            trans_new = pd.concat([data["transaksi"], trans_row], ignore_index=True)
                            if save_multiple_sheets({"kredit": kredit_new, "transaksi": trans_new}):
                                st.success("Pembayaran angsuran berhasil dicatat.")
                                st.rerun()


# ============================================================
# RINCIAN PENGELUARAN
# ============================================================
elif menu == "💸 Rincian Pengeluaran":
    st.title("💸 Laporan Pengeluaran & Belanja Modal")
    st.caption(f"Menampilkan data musim: **{musim_laporan}**")
    st.metric("TOTAL PENGELUARAN MUSIM INI", format_rp(tot_pengeluaran))
    st.markdown("---")
    if not df_pengeluaran.empty:
        df_exp_cat = (
            df_pengeluaran.groupby("kategori", dropna=False)["jumlah"]
            .sum().reset_index().sort_values(by="jumlah", ascending=False)
        )
        fig_exp = px.bar(
            df_exp_cat, x="kategori", y="jumlah", text="jumlah", color="kategori"
        )
        fig_exp.update_traces(texttemplate="Rp %{text:,.0f}", textposition="outside")
        fig_exp.update_layout(yaxis_title="Rupiah")
        st.plotly_chart(fig_exp, use_container_width=True)
        st.dataframe(df_pengeluaran, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada pengeluaran yang dicatat pada musim ini.")


# ============================================================
# TRANSAKSI MANUAL
# ============================================================
elif menu == "➕ Tambah Transaksi Manual":
    st.title("📝 Input Transaksi Kas Manual")
    st.caption(
        "Gunakan menu ini untuk transaksi kas umum. Pembayaran pestisida dan cicilan "
        "dicatat dari menu masing-masing agar saldo tagihan/piutang ikut diperbarui."
    )

    if not is_admin:
        st.warning("Halaman ini khusus pengurus. Masukkan PIN di panel sebelah kiri.")
    elif musim_laporan != musim_aktif:
        st.warning(
            "Anda sedang melihat arsip musim. Untuk mencegah transaksi masuk ke musim yang salah, "
            "input dan penghapusan hanya tersedia ketika musim aktif dipilih."
        )
    else:
        with st.form("form_transaksi", clear_on_submit=True):
            jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
            if jenis == "Pemasukan":
                kategori_options = ["Combine", "Rotavator", "Oven", "Lainnya"]
            else:
                kategori_options = [
                    "Belanja Modal", "Bahan Bakar", "Operasional", "Perawatan", "Lainnya"
                ]
            kategori = st.selectbox("Unit / Kategori", kategori_options)
            keterangan = st.text_input("Keterangan Transaksi")
            jumlah_rp = st.number_input(
                "Jumlah (Rupiah)", min_value=1, step=50000, value=50000
            )
            submitted = st.form_submit_button("Simpan Transaksi")
            if submitted:
                if not keterangan.strip():
                    st.error("Keterangan transaksi wajib diisi.")
                else:
                    trans_id = next_id(data["transaksi"])
                    new_row = pd.DataFrame([{
                        "id": trans_id,
                        "musim": musim_aktif,
                        "tanggal": current_date_jakarta(),
                        "jenis": jenis,
                        "kategori": kategori,
                        "keterangan": keterangan.strip(),
                        "jumlah": float(jumlah_rp),
                    }])
                    trans_new = pd.concat([data["transaksi"], new_row], ignore_index=True)
                    if save_multiple_sheets({"transaksi": trans_new}):
                        st.success(f"Transaksi {jenis.lower()} berhasil disimpan.")
                        st.rerun()

        st.markdown("---")
        st.subheader("🗑️ Hapus Transaksi Manual")
        current_transactions = df_transaksi.copy()
        # Transaksi yang menjadi pasangan catatan kredit/pestisida dilindungi
        # agar penghapusan tidak memutus rekonsiliasi antarworksheet.
        protected_categories = {"Pestisida", "Kredit Barang", "Kredit Cicilan Barang"}
        deletable = current_transactions[
            ~current_transactions["kategori"].astype(str).isin(protected_categories)
        ].copy() if not current_transactions.empty else pd.DataFrame()

        if deletable.empty:
            st.info("Tidak ada transaksi manual yang dapat dihapus pada musim ini.")
        else:
            st.dataframe(deletable, use_container_width=True, hide_index=True)
            delete_options = deletable["id"].dropna().tolist()
            labels = {
                row["id"]: (
                    f"ID {row['id']} | {row['jenis']} - {row['kategori']} - "
                    f"{row['keterangan']} ({format_rp(row['jumlah'])})"
                )
                for _, row in deletable.iterrows()
            }
            with st.form("form_hapus_transaksi"):
                selected_delete_id = st.selectbox(
                    "Pilih transaksi yang akan dihapus:",
                    delete_options,
                    format_func=lambda item: labels.get(item, str(item)),
                )
                konfirmasi_hapus = st.checkbox("Saya yakin ingin menghapus transaksi ini.")
                hapus_transaksi = st.form_submit_button("Hapus Transaksi")
                if hapus_transaksi:
                    if not konfirmasi_hapus:
                        st.error("Centang konfirmasi sebelum menghapus.")
                    else:
                        mask = pd.to_numeric(data["transaksi"]["id"], errors="coerce") == float(selected_delete_id)
                        matches = data["transaksi"].index[mask].tolist()
                        if len(matches) != 1:
                            st.error("ID transaksi tidak unik atau tidak ditemukan.")
                        else:
                            trans_new = data["transaksi"].drop(index=matches[0]).reset_index(drop=True)
                            if save_multiple_sheets({"transaksi": trans_new}):
                                st.success(f"Transaksi ID {selected_delete_id} berhasil dihapus.")
                                st.rerun()


# ============================================================
# TUTUP BUKU DAN RESET MUSIM
# ============================================================
elif menu == "🔴 Tutup Buku & Reset Musim":
    st.title("🔴 Tutup Buku & Mulai Musim Baru")
    if not is_admin:
        st.warning("Halaman ini khusus pengurus. Masukkan PIN di panel sebelah kiri.")
    elif musim_laporan != musim_aktif:
        st.error(
            f"Tutup buku tidak tersedia karena Anda sedang melihat arsip **{musim_laporan}**. "
            f"Pilih musim aktif **{musim_aktif}** terlebih dahulu."
        )
    else:
        st.info(
            "Saldo yang ditampilkan dihitung dari saldo awal musim aktif + pemasukan kas "
            "− pengeluaran kas. Pastikan seluruh transaksi sudah dicatat sebelum menutup buku."
        )
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric("Musim Aktif Saat Ini", musim_aktif)
            st.metric("Saldo Akhir Kas Terhitung", format_rp(saldo_akhir_kas))
            saldo_final_alihkan = st.number_input(
                "Saldo Akhir Kas yang Dialihkan (Rp)",
                min_value=0.0,
                value=float(saldo_akhir_kas),
                step=100000.0,
                key="saldo_final_alihkan",
            )
        with col_t2:
            nama_musim_baru = st.text_input("Ketik Nama Musim Baru")
            st.warning(
                "Tindakan ini mengubah musim aktif. Data musim lama tidak dihapus, "
                "tetapi saldo awal musim baru akan dibuat dari nilai yang Anda masukkan."
            )
            konfirmasi_tutup = st.checkbox(
                "Saya sudah memeriksa laporan dan yakin ingin membuka musim baru."
            )
            tombol_tutup = st.button("🚀 Konfirmasi Tutup Buku & Mulai Musim Baru")
            if tombol_tutup:
                nama_baru = nama_musim_baru.strip()
                if not nama_baru:
                    st.error("Nama musim baru wajib diisi.")
                elif nama_baru == musim_aktif:
                    st.error("Nama musim baru harus berbeda dari musim aktif saat ini.")
                elif nama_baru in get_all_musim():
                    st.error("Nama musim tersebut sudah ada. Gunakan nama yang berbeda.")
                elif not konfirmasi_tutup:
                    st.error("Centang konfirmasi sebelum melanjutkan.")
                else:
                    settings_baru = upsert_settings(
                        data["settings"],
                        {
                            f"saldo_awal_{nama_baru}": saldo_final_alihkan,
                            "musim_aktif": nama_baru,
                        },
                    )
                    if save_multiple_sheets({"settings": settings_baru}):
                        st.success(
                            f"Musim baru **{nama_baru}** berhasil diaktifkan dengan saldo awal "
                            f"{format_rp(saldo_final_alihkan)}."
                        )
                        st.rerun()

st.sidebar.markdown("---")
st.sidebar.caption("Versi uji coba penyempurnaan • Periksa hasil pada salinan Google Sheets terlebih dahulu.")
