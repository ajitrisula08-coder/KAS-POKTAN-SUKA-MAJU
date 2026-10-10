import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# Config Halaman Streamlit
st.set_page_config(
    page_title="Sistem Informasi & Kas Kelompok Tani",
    page_icon="🌾",
    layout="wide"
)

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
    
    rotav
