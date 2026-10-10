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

# -------------------- DEFAULT STATIC DATA ----------------
