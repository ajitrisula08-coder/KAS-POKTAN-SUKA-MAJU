import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import os

# Config Halaman Streamlit
st.set_page_config(
    page_title="Sistem Kas POKTAN SUKA MAJU",
    page_icon="🌾",
    layout="wide"
)

# Helper Fungsi Tampil Logo Aman & Kecil
def render_logo(width=70):
    logo_files = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.PNG"]
    for logo_file in logo_files:
        if os.path.exists(logo_file):
            st.image(logo_file, width=width)
            return True
    return False

# -------------------- DATABASE INIT & STORAGE --------------------
def get_db_connection():
    conn = sqlite3.connect('kas_tani.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Table SETTINGS
    c.execute('''
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    ''')
    
    # Table PESTISIDA
    c.execute('''
    CREATE TABLE IF NOT EXISTS pestisida (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musim TEXT,
        no INTEGER,
        nama TEXT,
        jumlah_tagihan REAL,
        status TEXT
    )
    ''')
    
    # Table KREDIT BARANG
    c.execute('''
    CREATE TABLE IF NOT EXISTS kredit (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musim TEXT,
        no INTEGER,
        nama_anggota TEXT,
        nama_barang TEXT,
        harga_total REAL,
        dp REAL,
        angsuran_masuk REAL,
        status TEXT
    )
    ''')
    
    # Table TRANSAKSI TAMBAHAN
    c.execute('''
    CREATE TABLE IF NOT EXISTS transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musim TEXT,
        tanggal TEXT,
        jenis TEXT,
        kategori TEXT,
        keterangan TEXT,
        jumlah REAL
    )
    ''')
    
    # Default Settings
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('musim_aktif', 'OKT 2026 (Musim Rendeng)')")
    c.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('saldo_awal', '206744480')")
    
    # Populate Default Pestisida Data if Empty
    c.execute("SELECT COUNT(*) FROM pestisida")
    if c.fetchone()[0] == 0:
        default_pestisida = [
            ("OKT 2026 (Musim Rendeng)", 1, "AZIZ", 6675000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 2, "DANANG", 9087649, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 3, "RONI", 18051950, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 4, "JAKA", 15648000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 5, "CAHYO", 13470000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 6, "HARTOYO", 18810000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 7, "WARDI", 16736000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 8, "TB", 3300000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 9, "GIMAN", 10506000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 10, "AJI", 5960000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 11, "ANTO", 3022500, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 12, "IHSAN", 775000, "Belum Lunas"),
            ("OKT 2026 (Musim Rendeng)", 13, "SUTAR", 1085000, "Belum Lunas")
        ]
        c.executemany("INSERT INTO pestisida (musim, no, nama, jumlah_tagihan, status) VALUES (?,?,?,?,?)", default_pestisida)
        
    # Populate Default Kredit Data if Empty
    c.execute("SELECT COUNT(*) FROM kredit")
    if c.fetchone()[0] == 0:
        default_kredit = [
            ("OKT 2026 (Musim Rendeng)", 1, "PAK JOKO", "Motor Honda", 28360000, 5000000, 12000000, "Berjalan"),
            ("OKT 2026 (Musim Rendeng)", 2, "PAK RONI", "Motor Yamaha", 23840000, 4000000, 10000000, "Berjalan"),
            ("OKT 2026 (Musim Rendeng)", 3, "PAK GIMAN", "Motor Honda", 26520000, 5000000, 21520000, "Lunas"),
            ("OKT 2026 (Musim Rendeng)", 4, "PAK TONO", "Motor Honda", 26520000, 5000000, 15000000, "Berjalan"),
            ("OKT 2026 (Musim Rendeng)", 5, "WARDI", "Sprayer Elektrik", 1500000, 300000, 1200000, "Lunas")
        ]
        c.executemany("INSERT INTO kredit (musim, no, nama_anggota, nama_barang, harga_total, dp, angsuran_masuk, status) VALUES (?,?,?,?,?,?,?,?)", default_kredit)
        
    conn.commit()
    conn.close()

init_db()

# Helper DB Functions
def get_setting(key, default_val=""):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = c.fetchone()
    conn.close()
    return row['value'] if row else default_val

def set_setting(key, value):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

# -------------------- DEFAULT STATIC DATA --------------------
@st.cache_data
def get_static_data():
    combine_data = [
        {"NO": 1, "NAMA": "SUR", "HASIL_1": 37, "JML_KARUNG": 37, "HARGA": 45000, "JUMLAH_RP": 1665000},
        {"NO": 2, "NAMA": "MARUF", "HASIL_1": 55, "JML_KARUNG": 83, "HARGA": 45000, "JUMLAH_RP": 3735000},
        {"NO": 3, "NAMA": "GIAT", "HASIL_1": 53, "JML_KARUNG": 53, "HARGA": 45000, "JUMLAH_RP": 2385000},
        {"NO": 4, "NAMA": "SUMAWAN", "HASIL_1": 110, "JML_KARUNG": 110, "HARGA": 45000, "JUMLAH_RP": 4950000},
        {"NO": 5, "NAMA": "UDIN B", "HASIL_1": 50, "JML_KARUNG": 94, "HARGA": 45000, "JUMLAH_RP": 4230000},
        {"NO": 6, "NAMA": "GRES", "HASIL_1": 59, "JML_KARUNG": 81, "HARGA": 46000, "JUMLAH_RP": 3726000},
        {"NO": 7, "NAMA": "MUS", "HASIL_1": 65, "JML_KARUNG": 89, "HARGA": 46000, "JUMLAH_RP": 4094000},
        {"NO": 8, "NAMA": "SURAT", "HASIL_1": 63, "JML_KARUNG": 101, "HARGA": 45000, "JUMLAH_RP": 4545000},
        {"NO": 9, "NAMA": "TUT D", "HASIL_1": 30, "JML_KARUNG": 96, "HARGA": 45000, "JUMLAH_RP": 4320000},
        {"NO": 10, "NAMA": "ERNA", "HASIL_1": 22, "JML_KARUNG": 72, "HARGA": 45000, "JUMLAH_RP": 3240000},
        {"NO": 11, "NAMA": "HADI", "HASIL_1": 35, "JML_KARUNG": 35, "HARGA": 45000, "JUMLAH_RP": 1575000},
        {"NO": 12, "NAMA": "KOPRAL", "HASIL_1": 28, "JML_KARUNG": 28, "HARGA": 45000, "JUMLAH_RP": 1260000},
        {"NO": 19, "NAMA": "MALAS", "HASIL_1": 94, "JML_KARUNG": 94, "HARGA": 45000, "JUMLAH_RP": 4230000},
        {"NO": 20, "NAMA": "IKHSAN", "HASIL_1": 36, "JML_KARUNG": 66, "HARGA": 45000, "JUMLAH_RP": 2970000},
        {"NO": 21, "NAMA": "SUTAR", "HASIL_1": 94, "JML_KARUNG": 174, "HARGA": 45000, "JUMLAH_RP": 7830000},
        {"NO": 22, "NAMA": "WAHID", "HASIL_1": 47, "JML_KARUNG": 47, "HARGA": 45000, "JUMLAH_RP": 2115000},
        {"NO": 23, "NAMA": "MATORI", "HASIL_1": 10, "JML_KARUNG": 10, "HARGA": 45000, "JUMLAH_RP": 450000},
        {"NO": 24, "NAMA": "KOMENG", "HASIL_1": 42, "JML_KARUNG": 42, "HARGA": 45000, "JUMLAH_RP": 1890000},
        {"NO": 25, "NAMA": "HENDRIK", "HASIL_1": 26, "JML_KARUNG": 47, "HARGA": 45000, "JUMLAH_RP": 2115000},
        {"NO": 26, "NAMA": "SUKADA", "HASIL_1": 57, "JML_KARUNG": 57, "HARGA": 45000, "JUMLAH_RP": 2565000},
        {"NO": 27, "NAMA": "SANTRE", "HASIL_1": 40, "JML_KARUNG": 40, "HARGA": 45000, "JUMLAH_RP": 1800000},
        {"NO": 28, "NAMA": "SUBEK", "HASIL_1": 20, "JML_KARUNG": 20, "HARGA": 45000, "JUMLAH_RP": 900000},
        {"NO": 29, "NAMA": "DEDI", "HASIL_1": 43, "JML_KARUNG": 43, "HARGA": 45000, "JUMLAH_RP": 1935000},
        {"NO": 30, "NAMA": "AJIZ", "HASIL_1": 157, "JML_KARUNG": 157, "HARGA": 45000, "JUMLAH_RP": 7065000},
        {"NO": 31, "NAMA": "RONI", "HASIL_1": 204, "JML_KARUNG": 204, "HARGA": 45000, "JUMLAH_RP": 9180000},
        {"NO": 32, "NAMA": "JAKA", "HASIL_1": 123, "JML_KARUNG": 123, "HARGA": 45000, "JUMLAH_RP": 5535000},
        {"NO": 33, "NAMA": "SURYA", "HASIL_1": 41, "JML_KARUNG": 41, "HARGA": 45000, "JUMLAH_RP": 1845000},
        {"NO": 34, "NAMA": "HARTOYO", "HASIL_1": 193, "JML_KARUNG": 193, "HARGA": 45000, "JUMLAH_RP": 8685000},
        {"NO": 35, "NAMA": "WARDI", "HASIL_1": 119, "JML_KARUNG": 119, "HARGA": 45000, "JUMLAH_RP": 5355000},
        {"NO": 36, "NAMA": "TB", "HASIL_1": 87, "JML_KARUNG": 87, "HARGA": 45000, "JUMLAH_RP": 3915000}
    ]
    
    rotavator_data = [
        {"NO": 1, "NAMA": "JAKA", "LUAS_HA": 1.50, "HARGA": 2000000, "JMLH_BRUTO": 3000000, "SOLAR_L": 50, "SUBSIDI_SOLAR": 750000, "SISA_NETTO": 2250000},
        {"NO": 2, "NAMA": "MBAH KUN", "LUAS_HA": 1.10, "HARGA": 2000000, "JMLH_BRUTO": 2200000, "SOLAR_L": 60, "SUBSIDI_SOLAR": 900000, "SISA_NETTO": 1300000},
        {"NO": 3, "NAMA": "AJIZ", "LUAS_HA": 2.00, "HARGA": 2000000, "JMLH_BRUTO": 4000000, "SOLAR_L": 0, "SUBSIDI_SOLAR": 0, "SISA_NETTO": 4000000},
        {"NO": 4, "NAMA": "RONI", "LUAS_HA": 3.70, "HARGA": 2000000, "JMLH_BRUTO": 7400000, "SOLAR_L": 160, "SUBSIDI_SOLAR": 2400000, "SISA_NETTO": 5000000},
        {"NO": 5, "NAMA": "TB", "LUAS_HA": 1.20, "HARGA": 2000000, "JMLH_BRUTO": 2400000, "SOLAR_L": 55, "SUBSIDI_SOLAR": 825000, "SISA_NETTO": 1575000},
        {"NO": 6, "NAMA": "SUTAR", "LUAS_HA": 2.55, "HARGA": 2000000, "JMLH_BRUTO": 5100000, "SOLAR_L": 80, "SUBSIDI_SOLAR": 1200000, "SISA_NETTO": 3900000},
        {"NO": 7, "NAMA": "WARDI", "LUAS_HA": 1.25, "HARGA": 2000000, "JMLH_BRUTO": 2500000, "SOLAR_L": 35, "SUBSIDI_SOLAR": 525000, "SISA_NETTO": 1975000},
        {"NO": 8, "NAMA": "SURYA", "LUAS_HA": 0.50, "HARGA": 2000000, "JMLH_BRUTO": 1000000, "SOLAR_L": 30, "SUBSIDI_SOLAR": 450000, "SISA_NETTO": 550000},
        {"NO": 9, "NAMA": "HARTOYO", "LUAS_HA": 0.60, "HARGA": 2000000, "JMLH_BRUTO": 1200000, "SOLAR_L": 20, "SUBSIDI_SOLAR": 300000, "SISA_NETTO": 900000},
        {"NO": 10, "NAMA": "HENDRIK", "LUAS_HA": 0.90, "HARGA": 2000000, "JMLH_BRUTO": 1800000, "SOLAR_L": 50, "SUBSIDI_SOLAR": 750000, "SISA_NETTO": 1050000},
        {"NO": 11, "NAMA": "IHSAN", "LUAS_HA": 0.50, "HARGA": 1200000, "JMLH_BRUTO": 600000, "SOLAR_L": 0, "SUBSIDI_SOLAR": 0, "SISA_NETTO": 600000},
        {"NO": 12, "NAMA": "CAHYO", "LUAS_HA": 0.50, "HARGA": 1200000, "JMLH_BRUTO": 600000, "SOLAR_L": 20, "SUBSIDI_SOLAR": 300000, "SISA_NETTO": 300000},
        {"NO": 13, "NAMA": "KIRMAN", "LUAS_HA": 0.50, "HARGA": 1200000, "JMLH_BRUTO": 600000, "SOLAR_L": 0, "SUBSIDI_SOLAR": 0, "SISA_NETTO": 600000},
        {"NO": 14, "NAMA": "SUHADI", "LUAS_HA": 1.25, "HARGA": 1200000, "JMLH_BRUTO": 1500000, "SOLAR_L": 20, "SUBSIDI_SOLAR": 300000, "SISA_NETTO": 1200000},
        {"NO": 15, "NAMA": "RISWAN", "LUAS_HA": 1.50, "HARGA": 1200000, "JMLH_BRUTO": 1800000, "SOLAR_L": 40, "SUBSIDI_SOLAR": 600000, "SISA_NETTO": 1200000}
    ]
    
    pengeluaran_data = [
        {"NO": 1, "RINCIAN": "BELANJA KIOS", "JUMLAH": 16305000, "KATEGORI": "Pupuk & Obat"},
        {"NO": 2, "RINCIAN": "BELANJA KIOS", "JUMLAH": 2845000, "KATEGORI": "Pupuk & Obat"},
        {"NO": 3, "RINCIAN": "BELANJA OBAT2 (MS RONI PEMADAM)", "JUMLAH": 1458000, "KATEGORI": "Pupuk & Obat"},
        {"NO": 4, "RINCIAN": "BLNJA OBT P JOKO", "JUMLAH": 270000, "KATEGORI": "Pupuk & Obat"},
        {"NO": 12, "RINCIAN": "BELANJA KIOS", "JUMLAH": 2835000, "KATEGORI": "Pupuk & Obat"},
        {"NO": 5, "RINCIAN": "wadah kios", "JUMLAH": 50000, "KATEGORI": "Operasional Kios"},
        {"NO": 6, "RINCIAN": "KONSUMSI SYUKURAN", "JUMLAH": 675000, "KATEGORI": "Konsumsi & Dinas"},
        {"NO": 7, "RINCIAN": "SOLAR MS RONI 1", "JUMLAH": 800000, "KATEGORI": "Bahan Bakar"},
        {"NO": 8, "RINCIAN": "SOLAR MS RONI 2", "JUMLAH": 1500000, "KATEGORI": "Bahan Bakar"},
        {"NO": 9, "RINCIAN": "HP MS RONI", "JUMLAH": 3889000, "KATEGORI": "Operasional Tani"},
        {"NO": 10, "RINCIAN": "HP AJI", "JUMLAH": 4900000, "KATEGORI": "Operasional Tani"},
        {"NO": 11, "RINCIAN": "SERVIS VIAR", "JUMLAH": 100000, "KATEGORI": "Servis & Maintenance"},
        {"NO": 13, "RINCIAN": "ONGKOS LEK TEGUH", "JUMLAH": 100000, "KATEGORI": "Upah Kerja"},
        {"NO": 14, "RINCIAN": "BAYAR OPERATOR ROTAVATOR 20.15 Ha", "JUMLAH": 5610000, "KATEGORI": "Upah Kerja"},
        {"NO": 15, "RINCIAN": "CUCI TLAKTOR", "JUMLAH": 200000, "KATEGORI": "Servis & Maintenance"},
        {"NO": 16, "RINCIAN": "FILTER COMBINE +ONGKIR 40", "JUMLAH": 660000, "KATEGORI": "Servis & Maintenance"},
        {"NO": 17, "RINCIAN": "ARCO MS RONI", "JUMLAH": 660000, "KATEGORI": "Peralatan"},
        {"NO": 18, "RINCIAN": "OLI COMBINE 10L", "JUMLAH": 670000, "KATEGORI": "Servis & Maintenance"},
        {"NO": 19, "RINCIAN": "TALI", "JUMLAH": 120000, "KATEGORI": "Peralatan"},
        {"NO": 20, "RINCIAN": "UPAH SURYA MESIN PANEN", "JUMLAH": 1640000, "KATEGORI": "Upah Kerja"},
        {"NO": 21, "RINCIAN": "STICK SPRAYER WARDI", "JUMLAH": 110000, "KATEGORI": "Peralatan"},
        {"NO": 22, "RINCIAN": "ONGKOS MOBIL AMBIL PUPUK SUB", "JUMLAH": 3090000, "KATEGORI": "Transportasi"},
        {"NO": 23, "RINCIAN": "BENSIN 5L", "JUMLAH": 75000, "KATEGORI": "Bahan Bakar"},
        {"NO": 24, "RINCIAN": "SOLAR 200L", "JUMLAH": 3600000, "KATEGORI": "Bahan Bakar"},
        {"NO": 25, "RINCIAN": "SOLAR 340L", "JUMLAH": 6120000, "KATEGORI": "Bahan Bakar"},
        {"NO": 26, "RINCIAN": "FILTER 4 BIJI", "JUMLAH": 1600000, "KATEGORI": "Servis & Maintenance"},
        {"NO": 27, "RINCIAN": "KUKUMACAN", "JUMLAH": 260000, "KATEGORI": "Peralatan"},
        {"NO": 28, "RINCIAN": "SOLAR 200L", "JUMLAH": 3600000, "KATEGORI": "Bahan Bakar"},
        {"NO": 29, "RINCIAN": "BENSIN VIAR", "JUMLAH": 100000, "KATEGORI": "Bahan Bakar"},
        {"NO": 30, "RINCIAN": "SOLAR 200L", "JUMLAH": 3600000, "KATEGORI": "Bahan Bakar"},
        {"NO": 31, "RINCIAN": "BEARING 4 BIJI", "JUMLAH": 100000, "KATEGORI": "Servis & Maintenance"},
        {"NO": 32, "RINCIAN": "SOLAR 200L", "JUMLAH": 3600000, "KATEGORI": "Bahan Bakar"},
        {"NO": 33, "RINCIAN": "SOLAR 160L", "JUMLAH": 2880000, "KATEGORI": "Bahan Bakar"},
        {"NO": 34, "RINCIAN": "BENSIN 5L", "JUMLAH": 75000, "KATEGORI": "Bahan Bakar"},
        {"NO": 35, "RINCIAN": "MOTOR PAK JOKO", "JUMLAH": 28360000, "KATEGORI": "Belanja Modal (Motor)"},
        {"NO": 36, "RINCIAN": "MOTOR PAK RONI", "JUMLAH": 23840000, "KATEGORI": "Belanja Modal (Motor)"},
        {"NO": 37, "RINCIAN": "MOTOR PAK GIMAN", "JUMLAH": 26520000, "KATEGORI": "Belanja Modal (Motor)"},
        {"NO": 38, "RINCIAN": "MOTOR PAK TONO", "JUMLAH": 26520000, "KATEGORI": "Belanja Modal (Motor)"},
        {"NO": 39, "RINCIAN": "BAYAR PUPUK SUBSIDI", "JUMLAH": 21962000, "KATEGORI": "Pupuk & Obat"},
        {"NO": 40, "RINCIAN": "KONSUMSI DINAS", "JUMLAH": 500000, "KATEGORI": "Konsumsi & Dinas"},
        {"NO": 41, "RINCIAN": "BERAS DINAS", "JUMLAH": 700000, "KATEGORI": "Konsumsi & Dinas"},
        {"NO": 43, "RINCIAN": "PENGELUARAN OPRT & HLPER COMBINE", "JUMLAH": 22157000, "KATEGORI": "Upah Kerja"}
    ]

    oven_data = [
        {"NO": 1, "NAMA": "ANTO", "JML_KARUNG": 3150, "HARGA": 150, "JUMLAH_RP": 472500, "KET": "Bed Dryer"}
    ]

    return pd.DataFrame(combine_data), pd.DataFrame(rotavator_data), pd.DataFrame(pengeluaran_data), pd.DataFrame(oven_data)

df_combine, df_rotavator, df_pengeluaran, df_oven = get_static_data()

# -------------------- LOAD SETTINGS & DB --------------------
musim_aktif = get_setting('musim_aktif', 'OKT 2026 (Musim Rendeng)')
saldo_musim_lalu = float(get_setting('saldo_awal', '206744480'))

conn = get_db_connection()
df_pestisida = pd.read_sql_query("SELECT * FROM pestisida WHERE musim = ?", conn, params=(musim_aktif,))
df_kredit = pd.read_sql_query("SELECT * FROM kredit WHERE musim = ?", conn, params=(musim_aktif,))
df_transaksi = pd.read_sql_query("SELECT * FROM transaksi WHERE musim = ?", conn, params=(musim_aktif,))
conn.close()

if not df_kredit.empty:
    df_kredit["TOTAL_TERBAYAR"] = df_kredit["dp"] + df_kredit["angsuran_masuk"]
    df_kredit["SISA_PIUTANG"] = df_kredit["harga_total"] - df_kredit["TOTAL_TERBAYAR"]
else:
    df_kredit = pd.DataFrame(columns=["id", "musim", "no", "nama_anggota", "nama_barang", "harga_total", "dp", "angsuran_masuk", "status", "TOTAL_TERBAYAR", "SISA_PIUTANG"])

# Total Perhitungan Pemasukan & Pengeluaran Per Musim
tot_combine = df_combine["JUMLAH_RP"].sum() if "OKT 2026" in musim_aktif else 0
tot_rotavator = df_rotavator["SISA_NETTO"].sum() if "OKT 2026" in musim_aktif else 0
tot_pestisida = df_pestisida["jumlah_tagihan"].sum() if not df_pestisida.empty else 0
tot_oven = df_oven["JUMLAH_RP"].sum() if "OKT 2026" in musim_aktif else 0

pemasukan_kios = 9519000 if "OKT 2026" in musim_aktif else 0
pemasukan_tambahan = df_transaksi[df_transaksi["jenis"] == "Pemasukan"]["jumlah"].sum() if not df_transaksi.empty else 0
tot_pemasukan_usaha = tot_combine + tot_rotavator + tot_pestisida + tot_oven + pemasukan_tambahan

pengeluaran_tambahan = df_transaksi[df_transaksi["jenis"] == "Pengeluaran"]["jumlah"].sum() if not df_transaksi.empty else 0
tot_pengeluaran = (df_pengeluaran["JUMLAH"].sum() if "OKT 2026" in musim_aktif else 0) + pengeluaran_tambahan

sisa_saldo_kios = (saldo_musim_lalu + pemasukan_kios) - tot_pengeluaran
saldo_akhir_kas = tot_pemasukan_usaha + sisa_saldo_kios

tot_nilai_kredit = df_kredit["harga_total"].sum() if not df_kredit.empty else 0
tot_kredit_terbayar = df_kredit["TOTAL_TERBAYAR"].sum() if not df_kredit.empty else 0
tot_sisa_piutang = df_kredit["SISA_PIUTANG"].sum() if not df_kredit.empty else 0

# -------------------- SIDEBAR SETTINGS & LOGIN --------------------
# Tampilkan logo kecil di pojok kiri atas sidebar (width=70)
if not render_logo(width=70):
    st.sidebar.markdown("### 🌾 POKTAN SUKA MAJU")

st.sidebar.title("POKTAN SUKA MAJU")
st.sidebar.caption("Aplikasi Kas & Unit Usaha")

# Mode Akses
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Hak Akses Pengguna")
mode_akses = st.sidebar.selectbox("Pilih Peran:", ["👁️ Mode Anggota (Lihat Laporan)", "🔐 Mode Pengurus (Akses Edit)"])

is_admin = False
if mode_akses == "🔐 Mode Pengurus (Akses Edit)":
    pin_input = st.sidebar.text_input("Masukkan PIN Pengurus:", type="password", help="PIN Default adalah 1234")
    if pin_input == "1234":
        is_admin = True
        st.sidebar.success("Akses Pengurus Aktif")
    elif pin_input != "":
        st.sidebar.error("PIN Salah!")

# Tampil Musim Aktif
st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Musim Aktif Tanam")
st.sidebar.info(f"📍 **{musim_aktif}**")

# Input Saldo Awal Musim Manual
if is_admin:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Ubah Saldo Awal")
    new_saldo_awal = st.sidebar.number_input("Saldo Awal Musim (Rp):", value=float(saldo_musim_lalu), step=1000000.0)
    if new_saldo_awal != saldo_musim_lalu:
        set_setting('saldo_awal', new_saldo_awal)
        st.sidebar.success("Saldo awal disimpan!")
        st.rerun()

# Menu Radio Navigasi
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
        "➕ Tambah Transaksi",
        "🔴 Tutup Buku & Reset Musim"
    ]
)

# -------------------- DASHBOARD UTAMA --------------------
if menu == "📊 Dasbor Utama":
    col_logo, col_title = st.columns([1, 6])
    with col_logo:
        if not render_logo(width=80):
            st.title("🌾")
    with col_title:
        st.title("Dasbor Utama Kas POKTAN SUKA MAJU")
        st.caption(f"Status Pengguna: **{mode_akses}** | Musim Tanam Aktif: **{musim_aktif}**")
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Hasil Usaha", f"Rp {tot_pemasukan_usaha:,.0f}".replace(',', '.'))
    col2.metric("Total Pengeluaran", f"Rp {tot_pengeluaran:,.0f}".replace(',', '.'))
    col3.metric("Sisa Saldo Kios/Lalu", f"Rp {sisa_saldo_kios:,.0f}".replace(',', '.'))
    col4.metric("SALDO AKHIR KAS", f"Rp {saldo_akhir_kas:,.0f}".replace(',', '.'))

    st.markdown("---")
    
    st.info(f"💡 **Informasi Ringkasan Kas:** Saldo Awal Musim Ini = **Rp {saldo_musim_lalu:,.0f}** | Sisa Piutang Kredit = **Rp {tot_sisa_piutang:,.0f}**.")
    
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Pemasukan Per Unit Usaha")
        df_pemasukan = pd.DataFrame({
            "Unit Usaha": ["Combine", "Rotavator", "Pestisida", "Oven", "Lainnya"],
            "Pendapatan": [tot_combine, tot_rotavator, tot_pestisida, tot_oven, pemasukan_tambahan]
        })
        fig_pie = px.pie(df_pemasukan, values="Pendapatan", names="Unit Usaha", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_chart2:
        st.subheader("📊 Perbandingan Hasil vs Pengeluaran")
        df_bar = pd.DataFrame({
            "Kategori": ["Hasil Usaha", "Saldo Lalu", "Total Pengeluaran", "Saldo Akhir"],
            "Jumlah": [tot_pemasukan_usaha, saldo_musim_lalu, tot_pengeluaran, saldo_akhir_kas]
        })
        fig_bar = px.bar(df_bar, x="Kategori", y="Jumlah", text="Jumlah", color="Kategori")
        fig_bar.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### 📝 Tabel Rekap Pemasukan Musim Ini")
    df_rekap_show = pd.DataFrame({
        "Sumber Pemasukan": ["1. REKAP COMBINE", "2. REKAP ROTAVATOR", "3. REKAP PESTISIDA", "4. REKAP OVEN", "5. PEMASUKAN LAINNYA", "TOTAL PEMASUKAN USAHA"],
        "Nilai Total": [f"Rp {tot_combine:,.0f}".replace(',', '.'), f"Rp {tot_rotavator:,.0f}".replace(',', '.'), f"Rp {tot_pestisida:,.0f}".replace(',', '.'), f"Rp {tot_oven:,.0f}".replace(',', '.'), f"Rp {pemasukan_tambahan:,.0f}".replace(',', '.'), f"Rp {tot_pemasukan_usaha:,.0f}".replace(',', '.')]
    })
    st.dataframe(df_rekap_show, use_container_width=True)
    st.download_button("📥 Unduh Ringkasan Kas (CSV)", df_rekap_show.to_csv(index=False), "Ringkasan_Kas_Poktan.csv", "text/csv")

# -------------------- UNIT COMBINE --------------------
elif menu == "🚜 Unit Combine (Panen)":
    st.title("🚜 Laporan Hasil Panen - Combine Harvester")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    if "OKT 2026" in musim_aktif:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Karung Gabah", f"{df_combine['JML_KARUNG'].sum():,} Karung".replace(',', '.'))
        c2.metric("Total Pendapatan Combine", f"Rp {tot_combine:,.0f}".replace(',', '.'))
        c3.metric("Jumlah Petani", f"{len(df_combine)} Orang")
        
        st.markdown("---")
        search_nama = st.text_input("🔍 Cari Nama Petani:")
        df_filtered = df_combine if not search_nama else df_combine[df_combine['NAMA'].str.contains(search_nama, case=False, na=False)]
        st.dataframe(df_filtered, use_container_width=True)
        st.download_button("📥 Unduh Data Combine (CSV)", df_combine.to_csv(index=False), "Laporan_Combine.csv", "text/csv")
    else:
        st.info("💡 Belum ada data transaksi Combine bawaan untuk musim baru ini. Gunakan menu 'Tambah Transaksi' untuk mencatat pemasukan baru.")

# -------------------- UNIT ROTAVATOR --------------------
elif menu == "⚙️ Unit Rotavator (Lahan)":
    st.title("⚙️ Laporan Pengolahan Lahan - Rotavator")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    if "OKT 2026" in musim_aktif:
        r1, r2, r3 = st.columns(3)
        r1.metric("Total Luas Tergarap", f"{df_rotavator['LUAS_HA'].sum():.2f} Ha")
        r2.metric("Total Subsidi Solar", f"Rp {df_rotavator['SUBSIDI_SOLAR'].sum():,.0f}".replace(',', '.'))
        r3.metric("Pendapatan Bersih", f"Rp {tot_rotavator:,.0f}".replace(',', '.'))
        
        st.markdown("---")
        st.dataframe(df_rotavator, use_container_width=True)
        st.download_button("📥 Unduh Data Rotavator (CSV)", df_rotavator.to_csv(index=False), "Laporan_Rotavator.csv", "text/csv")
    else:
        st.info("💡 Belum ada data transaksi Rotavator untuk musim baru ini.")

# -------------------- UNIT PESTISIDA & KIOS --------------------
elif menu == "🧪 Unit Pestisida & Kios":
    st.title("🧪 Laporan Belanja Obat & Pestisida Anggota")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    p1, p2, p3 = st.columns(3)
    p1.metric("Total Tagihan Pestisida", f"Rp {tot_pestisida:,.0f}".replace(',', '.'))
    p2.metric("Pemasukan Obat Kios KES", f"Rp {pemasukan_kios:,.0f}".replace(',', '.'))
    p3.metric("Jumlah Anggota Belanja", f"{len(df_pestisida)} Orang")
    
    st.markdown("---")
    
    if not df_pestisida.empty:
        col_p_s1, col_p_s2 = st.columns([2, 1])
        with col_p_s1:
            cari_pestisida = st.text_input("🔍 Cari Nama Anggota:")
        with col_p_s2:
            filter_pestisida_status = st.selectbox("Status Tagihan:", ["Semua Status", "Belum Lunas", "Lunas"])
            
        df_p_show = df_pestisida.copy()
        if cari_pestisida:
            df_p_show = df_p_show[df_p_show['nama'].str.contains(cari_pestisida, case=False, na=False)]
        if filter_pestisida_status != "Semua Status":
            df_p_show = df_p_show[df_p_show['status'] == filter_pestisida_status]
            
        st.dataframe(df_p_show, use_container_width=True)
        st.download_button("📥 Unduh Tagihan Pestisida (CSV)", df_pestisida.to_csv(index=False), "Tagihan_Pestisida.csv", "text/csv")
        
        if is_admin:
            st.markdown("---")
            st.subheader("⚙️ Update Status Pelunasan Pestisida")
            with st.form("form_update_pestisida"):
                pilih_anggota_p = st.selectbox("Pilih Anggota:", df_pestisida['nama'].tolist())
                status_baru_p = st.selectbox("Status Baru:", ["Belum Lunas", "Lunas"])
                submit_p = st.form_submit_button("Update Status")
                
                if submit_p:
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE pestisida SET status = ? WHERE nama = ? AND musim = ?", (status_baru_p, pilih_anggota_p, musim_aktif))
                    conn.commit()
                    conn.close()
                    st.success(f"Status tagihan **{pilih_anggota_p}** diperbarui menjadi **{status_baru_p}**!")
                    st.rerun()
    else:
        st.info("💡 Belum ada tagihan pestisida untuk musim baru ini.")

# -------------------- KREDIT BARANG --------------------
elif menu == "💳 Kredit & Cicilan Barang":
    st.title("💳 Laporan Kredit & Cicilan Barang Anggota")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Nilai Barang", f"Rp {tot_nilai_kredit:,.0f}".replace(',', '.'))
    k2.metric("Total Terbayar (DP + Angsuran)", f"Rp {tot_kredit_terbayar:,.0f}".replace(',', '.'))
    k3.metric("Sisa Piutang Anggota", f"Rp {tot_sisa_piutang:,.0f}".replace(',', '.'))
    
    st.markdown("---")
    
    if not df_kredit.empty:
        col_k1, col_k2 = st.columns([2, 1])
        with col_k1:
            cari_kredit = st.text_input("🔍 Cari Nama Anggota / Barang:")
        with col_k2:
            filter_status = st.selectbox("Status Pembayaran", ["Semua Status", "Berjalan", "Lunas"])
            
        df_kredit_show = df_kredit.copy()
        if cari_kredit:
            df_kredit_show = df_kredit_show[
                df_kredit_show['nama_anggota'].str.contains(cari_kredit, case=False, na=False) |
                df_kredit_show['nama_barang'].str.contains(cari_kredit, case=False, na=False)
            ]
        if filter_status != "Semua Status":
            df_kredit_show = df_kredit_show[df_kredit_show['status'] == filter_status]
            
        st.dataframe(df_kredit_show, use_container_width=True)
        st.download_button("📥 Unduh Laporan Kredit (CSV)", df_kredit.to_csv(index=False), "Laporan_Kredit.csv", "text/csv")
        
        if is_admin:
            st.markdown("---")
            st.subheader("➕ Form Catat Pembayaran Angsuran")
            with st.form("form_angsuran"):
                pilih_pembayar = st.selectbox("Pilih Anggota", df_kredit[df_kredit['status'] == "Berjalan"]['nama_anggota'].tolist() if not df_kredit[df_kredit['status'] == "Berjalan"].empty else ["Tidak Ada Kredit Berjalan"])
                nominal_angsuran = st.number_input("Nominal Angsuran (Rp)", min_value=10000, step=50000)
                
                simpan_angsuran = st.form_submit_button("Simpan Angsuran")
                if simpan_angsuran and pilih_pembayar != "Tidak Ada Kredit Berjalan":
                    conn = get_db_connection()
                    c = conn.cursor()
                    c.execute("UPDATE kredit SET angsuran_masuk = angsuran_masuk + ? WHERE nama_anggota = ? AND musim = ?", (nominal_angsuran, pilih_pembayar, musim_aktif))
                    
                    c.execute("SELECT harga_total, (dp + angsuran_masuk) as total FROM kredit WHERE nama_anggota = ? AND musim = ?", (pilih_pembayar, musim_aktif))
                    row = c.fetchone()
                    if row and row['total'] >= row['harga_total']:
                        c.execute("UPDATE kredit SET status = 'Lunas' WHERE nama_anggota = ? AND musim = ?", (pilih_pembayar, musim_aktif))
                        
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil mencatat angsuran **{pilih_pembayar}** sebesar **Rp {nominal_angsuran:,.0f}**!")
                    st.rerun()
    else:
        st.info("💡 Belum ada data kredit barang untuk musim baru ini.")

# -------------------- PENGELUARAN --------------------
elif menu == "💸 Rincian Pengeluaran":
    st.title("💸 Laporan Pengeluaran & Belanja Modal")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    st.metric("TOTAL PENGELUARAN MUSIM INI", f"Rp {tot_pengeluaran:,.0f}".replace(',', '.'))
    st.markdown("---")
    
    if "OKT 2026" in musim_aktif:
        df_exp_cat = df_pengeluaran.groupby("KATEGORI")["JUMLAH"].sum().reset_index().sort_values(by="JUMLAH", ascending=False)
        fig_exp = px.bar(df_exp_cat, x="KATEGORI", y="JUMLAH", text="JUMLAH", color="KATEGORI")
        fig_exp.update_traces(texttemplate='Rp %{text:,.0f}', textposition='outside')
        st.plotly_chart(fig_exp, use_container_width=True)
        st.dataframe(df_pengeluaran, use_container_width=True)
        st.download_button("📥 Unduh Rincian Pengeluaran (CSV)", df_pengeluaran.to_csv(index=False), "Rincian_Pengeluaran.csv", "text/csv")
    else:
        if not df_transaksi.empty:
            df_peng_baru = df_transaksi[df_transaksi['jenis'] == 'Pengeluaran']
            st.dataframe(df_peng_baru, use_container_width=True)
        else:
            st.info("💡 Belum ada pengeluaran yang dicatat untuk musim baru ini.")

# -------------------- TAMBAH TRANSAKSI --------------------
elif menu == "➕ Tambah Transaksi":
    st.title("📝 Input Transaksi Kas Baru")
    st.caption(f"Musim Tanam Aktif: **{musim_aktif}**")
    
    if not is_admin:
        st.warning("🔒 Halaman ini khusus Pengurus. Silakan masukkan PIN Pengurus di panel samping kiri terlebih dahulu.")
    else:
        with st.form("form_transaksi"):
            jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
            kategori = st.selectbox("Unit / Kategori", ["Combine", "Rotavator", "Pestisida", "Oven", "Kredit Barang", "Belanja Modal", "Bahan Bakar"])
            keterangan = st.text_input("Keterangan Transaksi")
            jumlah_rp = st.number_input("Jumlah (Rupiah)", min_value=0, step=50000)
            
            submitted = st.form_submit_button("Simpan Transaksi")
            if submitted and keterangan:
                conn = get_db_connection()
                c = conn.cursor()
                c.execute("INSERT INTO transaksi (musim, tanggal, jenis, kategori, keterangan, jumlah) VALUES (?, date('now'), ?, ?, ?, ?)",
                          (musim_aktif, jenis, kategori, keterangan, jumlah_rp))
                conn.commit()
                conn.close()
                st.success(f"Berhasil menyimpan {jenis}: **{keterangan}** sebesar **Rp {jumlah_rp:,.0f}**!")
                st.rerun()

# -------------------- TUTUP BUKU & RESET MUSIM --------------------
elif menu == "🔴 Tutup Buku & Reset Musim":
    st.title("🔴 Fitur Tutup Buku & Reset untuk Musim Baru")
    
    if not is_admin:
        st.warning("🔒 Halaman ini khusus Pengurus. Silakan masukkan PIN Pengurus di panel samping kiri terlebih dahulu.")
    else:
        st.error("⚠️ **Perhatian Pengurus:** Fitur ini akan menutup pembukuan musim aktif saat ini dan memindahkan Saldo Akhir Kas sebagai Saldo Awal Musim Baru.")
        
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            st.metric("Musim Aktif Saat Ini", musim_aktif)
            saldo_final_alihkan = st.number_input("Saldo Akhir Kas Yang Dialihkan (Rp):", value=float(saldo_akhir_kas), step=100000.0)
            
        with col_t2:
            nama_musim_baru = st.text_input("Ketik Nama Musim Baru:", value="APRIL 2027 (Musim Gadu)")
            konfirmasi_tutup = st.button("🚀 Konfirmasi Tutup Buku & Mulai Musim Baru")
            
            if konfirmasi_tutup and nama_musim_baru:
                set_setting('saldo_awal', saldo_final_alihkan)
                set_setting('musim_aktif', nama_musim_baru)
                
                st.balloons()
                st.success(f"✅ Berhasil Tutup Buku! Musim baru **'{nama_musim_baru}'** telah aktif dengan Saldo Awal **Rp {saldo_final_alihkan:,.0f}**.")
                st.rerun()
