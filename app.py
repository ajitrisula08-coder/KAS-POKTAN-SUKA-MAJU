import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

# Config Halaman Streamlit
st.set_page_config(
    page_title="Sistem Kas POKTAN SUKA MAJU", page_icon="🌾", layout="wide"
)

# CSS Kustom untuk menaikkan posisi logo dan merapatkan menu di sidebar
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


# Helper Fungsi Tampil Logo Spesifik Container
def render_logo(container, width=130):
  logo_files = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.PNG"]
  for logo_file in logo_files:
    if os.path.exists(logo_file):
      container.image(logo_file, width=width)
      return True
  return False


# -------------------- DATABASE INIT & STORAGE --------------------
def get_db_connection():
  conn = sqlite3.connect("kas_tani.db", check_same_thread=False)
  conn.row_factory = sqlite3.Row
  return conn


def init_db():
  conn = get_db_connection()
  c = conn.cursor()

  c.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

  c.execute("""
    CREATE TABLE IF NOT EXISTS pestisida (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musim TEXT,
        no INTEGER,
        nama TEXT,
        jumlah_tagihan REAL,
        status TEXT
    )
    """)

  c.execute("""
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
    """)

  c.execute("""
    CREATE TABLE IF NOT EXISTS transaksi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        musim TEXT,
        tanggal TEXT,
        jenis TEXT,
        kategori TEXT,
        keterangan TEXT,
        jumlah REAL
    )
    """)

  # Bersihkan data musim Oktober 2026 jika masih ada di database
  c.execute("DELETE FROM pestisida WHERE musim LIKE '%OKT 2026%'")
  c.execute("DELETE FROM kredit WHERE musim LIKE '%OKT 2026%'")
  c.execute("DELETE FROM transaksi WHERE musim LIKE '%OKT 2026%'")
  c.execute("DELETE FROM settings WHERE key LIKE '%OKT 2026%'")

  # Set Default Musim Sekarang & Saldo Awal Rp 233.235.079
  c.execute(
      "INSERT OR IGNORE INTO settings (key, value) VALUES ('musim_aktif',"
      " 'APRIL 2027 (Musim Gadu)')"
  )
  c.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES"
      " ('saldo_awal_APRIL 2027 (Musim Gadu)', '233235079')"
  )
  c.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES ('saldo_awal',"
      " '233235079')"
  )

  conn.commit()
  conn.close()


init_db()


def get_setting(key, default_val=""):
  conn = get_db_connection()
  c = conn.cursor()
  c.execute("SELECT value FROM settings WHERE key = ?", (key,))
  row = c.fetchone()
  conn.close()
  return row["value"] if row else default_val


def set_setting(key, value):
  conn = get_db_connection()
  c = conn.cursor()
  c.execute(
      "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
      (key, str(value)),
  )
  conn.commit()
  conn.close()


def get_saldo_awal_musim(musim):
  val = get_setting(f"saldo_awal_{musim}", None)
  if val is None:
    return float(get_setting("saldo_awal", "233235079"))
  return float(val)


def set_saldo_awal_musim(musim, val):
  set_setting(f"saldo_awal_{musim}", val)


def get_all_musim():
  conn = get_db_connection()
  c = conn.cursor()
  musim_set = set()
  musim_aktif_val = get_setting("musim_aktif", "APRIL 2027 (Musim Gadu)")
  musim_set.add(musim_aktif_val)

  for table in ["pestisida", "kredit", "transaksi"]:
    c.execute(f"SELECT DISTINCT musim FROM {table}")
    for row in c.fetchall():
      if row[0] and "OKT 2026" not in row[0]:
        musim_set.add(row[0])

  c.execute("SELECT key FROM settings WHERE key LIKE 'saldo_awal_%'")
  for row in c.fetchall():
    key_name = row[0].replace("saldo_awal_", "")
    if key_name and "OKT 2026" not in key_name:
      musim_set.add(key_name)

  conn.close()
  return sorted(list(musim_set), reverse=True)


# -------------------- LOAD SETTINGS & DB --------------------
musim_aktif = get_setting("musim_aktif", "APRIL 2027 (Musim Gadu)")

# -------------------- SIDEBAR SETTINGS & LOGIN --------------------
render_logo(st.sidebar, width=130)

st.sidebar.title("POKTAN SUKA MAJU")
st.sidebar.caption("Aplikasi Kas & Unit Usaha")

# Filter Pilih Musim Laporan
st.sidebar.markdown("---")
st.sidebar.subheader("🗓️ Pilih Musim Laporan")
daftar_musim = get_all_musim()
musim_laporan = st.sidebar.selectbox(
    "Lihat Data Musim:",
    options=daftar_musim,
    index=(
        daftar_musim.index(musim_aktif) if musim_aktif in daftar_musim else 0
    ),
)

saldo_musim_lalu = get_saldo_awal_musim(musim_laporan)

if musim_laporan == musim_aktif:
  st.sidebar.info(f"📍 **{musim_laporan}** (Musim Aktif Operasional)")
else:
  st.sidebar.warning(f"📜 **{musim_laporan}** (Arsip Musim Lalu)")

# Mode Akses
st.sidebar.markdown("---")
st.sidebar.subheader("👤 Hak Akses Pengguna")
mode_akses = st.sidebar.selectbox(
    "Pilih Peran:",
    ["👁️ Mode Anggota (Lihat Laporan)", "🔐 Mode Pengurus (Akses Edit)"],
)

is_admin = False
if mode_akses == "🔐 Mode Pengurus (Akses Edit)":
  pin_input = st.sidebar.text_input(
      "Masukkan PIN Pengurus:", type="password", help="PIN Default adalah 1234"
  )
  if pin_input == "1234":
    is_admin = True
    st.sidebar.success("Akses Pengurus Aktif")
  elif pin_input != "":
    st.sidebar.error("PIN Salah!")

# Input Saldo Awal Musim Manual
if is_admin:
  st.sidebar.markdown("---")
  st.sidebar.subheader("⚙️ Ubah Saldo Awal Musim Ini")
  new_saldo_awal = st.sidebar.number_input(
      f"Saldo Awal ({musim_laporan}):",
      value=float(saldo_musim_lalu),
      step=1000000.0,
  )
  if new_saldo_awal != saldo_musim_lalu:
    set_saldo_awal_musim(musim_laporan, new_saldo_awal)
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
        "🔴 Tutup Buku & Reset Musim",
    ],
)

# -------------------- QUERY DATA BERDASARKAN MUSIM LAPORAN --------------------
conn = get_db_connection()
df_pestisida = pd.read_sql_query(
    "SELECT * FROM pestisida WHERE musim = ?", conn, params=(musim_laporan,)
)
df_kredit = pd.read_sql_query(
    "SELECT * FROM kredit WHERE musim = ?", conn, params=(musim_laporan,)
)
df_transaksi = pd.read_sql_query(
    "SELECT * FROM transaksi WHERE musim = ?", conn, params=(musim_laporan,)
)
conn.close()

if not df_kredit.empty:
  df_kredit["TOTAL_TERBAYAR"] = df_kredit["dp"] + df_kredit["angsuran_masuk"]
  df_kredit["SISA_PIUTANG"] = (
      df_kredit["harga_total"] - df_kredit["TOTAL_TERBAYAR"]
  )
else:
  df_kredit = pd.DataFrame(columns=[
      "id",
      "musim",
      "no",
      "nama_anggota",
      "nama_barang",
      "harga_total",
      "dp",
      "angsuran_masuk",
      "status",
      "TOTAL_TERBAYAR",
      "SISA_PIUTANG",
  ])

# HITUNG TOTAL PEMASUKAN & PENGELUARAN PER MUSIM
if not df_transaksi.empty:
  df_pem_baru = df_transaksi[df_transaksi["jenis"] == "Pemasukan"]
  tot_combine = df_pem_baru[df_pem_baru["kategori"] == "Combine"][
      "jumlah"
  ].sum()
  tot_rotavator = df_pem_baru[df_pem_baru["kategori"] == "Rotavator"][
      "jumlah"
  ].sum()
  tot_pestisida_trans = df_pem_baru[df_pem_baru["kategori"] == "Pestisida"][
      "jumlah"
  ].sum()
  tot_oven = df_pem_baru[df_pem_baru["kategori"] == "Oven"]["jumlah"].sum()
  tot_kredit_masuk = df_pem_baru[
      df_pem_baru["kategori"].isin(["Kredit Barang", "Kredit Cicilan Barang"])
  ]["jumlah"].sum()
  pemasukan_tambahan = df_pem_baru[
      ~df_pem_baru["kategori"].isin([
          "Combine",
          "Rotavator",
          "Pestisida",
          "Oven",
          "Kredit Barang",
          "Kredit Cicilan Barang",
      ])
  ]["jumlah"].sum()

  tot_pengeluaran = df_transaksi[df_transaksi["jenis"] == "Pengeluaran"][
      "jumlah"
  ].sum()
else:
  tot_combine = tot_rotavator = tot_pestisida_trans = tot_oven = (
      tot_kredit_masuk
  ) = pemasukan_tambahan = tot_pengeluaran = 0

tot_pestisida_db = (
    df_pestisida["jumlah_tagihan"].sum() if not df_pestisida.empty else 0
)
tot_pestisida = tot_pestisida_db + tot_pestisida_trans

tot_pemasukan_usaha = (
    tot_combine
    + tot_rotavator
    + tot_pestisida
    + tot_oven
    + tot_kredit_masuk
    + pemasukan_tambahan
)

saldo_akhir_kas = (saldo_musim_lalu + tot_pemasukan_usaha) - tot_pengeluaran

tot_nilai_kredit = (
    df_kredit["harga_total"].sum() if not df_kredit.empty else 0
)
tot_kredit_terbayar = (
    df_kredit["TOTAL_TERBAYAR"].sum() if not df_kredit.empty else 0
) + tot_kredit_masuk
tot_sisa_piutang = max(0.0, tot_nilai_kredit - tot_kredit_terbayar)

# -------------------- DASHBOARD UTAMA --------------------
if menu == "📊 Dasbor Utama":
  st.title("Dasbor Utama Kas POKTAN SUKA MAJU")
  st.caption(
      f"Status Pengguna: **{mode_akses}** | Menampilkan Laporan Musim:"
      f" **{musim_laporan}**"
  )

  col1, col2, col3, col4 = st.columns(4)
  col1.metric(
      "Total Hasil Usaha", f"Rp {tot_pemasukan_usaha:,.0f}".replace(",", ".")
  )
  col2.metric(
      "Total Pengeluaran", f"Rp {tot_pengeluaran:,.0f}".replace(",", ".")
  )
  col3.metric("Saldo Awal Musim", f"Rp {saldo_musim_lalu:,.0f}".replace(",", "."))
  col4.metric(
      "SALDO AKHIR KAS", f"Rp {saldo_akhir_kas:,.0f}".replace(",", ".")
  )

  st.markdown("---")

  col_chart1, col_chart2 = st.columns(2)

  with col_chart1:
    st.subheader("📈 Pemasukan Per Unit Usaha")
    df_pemasukan = pd.DataFrame({
        "Unit Usaha": [
            "Combine",
            "Rotavator",
            "Pestisida",
            "Oven",
            "Kredit Barang",
            "Lainnya",
        ],
        "Pendapatan": [
            tot_combine,
            tot_rotavator,
            tot_pestisida,
            tot_oven,
            tot_kredit_masuk,
            pemasukan_tambahan,
        ],
    })
    fig_pie = px.pie(
        df_pemasukan, values="Pendapatan", names="Unit Usaha", hole=0.4
    )
    st.plotly_chart(fig_pie, use_container_width=True)

  with col_chart2:
    st.subheader("📊 Perbandingan Hasil vs Pengeluaran")
    df_bar = pd.DataFrame({
        "Kategori": [
            "Hasil Usaha",
            "Saldo Awal",
            "Total Pengeluaran",
            "Saldo Akhir",
        ],
        "Jumlah": [
            tot_pemasukan_usaha,
            saldo_musim_lalu,
            tot_pengeluaran,
            saldo_akhir_kas,
        ],
    })
    fig_bar = px.bar(
        df_bar, x="Kategori", y="Jumlah", text="Jumlah", color="Kategori"
    )
    fig_bar.update_traces(
        texttemplate="Rp %{text:,.0f}", textposition="outside"
    )
    st.plotly_chart(fig_bar, use_container_width=True)

  st.markdown(f"### 📝 Tabel Rekap Pemasukan Musim ({musim_laporan})")
  df_rekap_show = pd.DataFrame({
      "Sumber Pemasukan": [
          "1. REKAP COMBINE",
          "2. REKAP ROTAVATOR",
          "3. REKAP PESTISIDA",
          "4. REKAP OVEN",
          "5. REKAP KREDIT BARANG",
          "6. PEMASUKAN LAINNYA",
          "TOTAL PEMASUKAN USAHA",
      ],
      "Nilai Total": [
          f"Rp {tot_combine:,.0f}".replace(",", "."),
          f"Rp {tot_rotavator:,.0f}".replace(",", "."),
          f"Rp {tot_pestisida:,.0f}".replace(",", "."),
          f"Rp {tot_oven:,.0f}".replace(",", "."),
          f"Rp {tot_kredit_masuk:,.0f}".replace(",", "."),
          f"Rp {pemasukan_tambahan:,.0f}".replace(",", "."),
          f"Rp {tot_pemasukan_usaha:,.0f}".replace(",", "."),
      ],
  })
  st.dataframe(df_rekap_show, use_container_width=True)
  st.download_button(
      "📥 Unduh Ringkasan Kas (CSV)",
      df_rekap_show.to_csv(index=False),
      f"Ringkasan_Kas_{musim_laporan}.csv",
      "text/csv",
  )

# -------------------- UNIT COMBINE --------------------
elif menu == "🚜 Unit Combine (Panen)":
  st.title("🚜 Laporan Hasil Panen - Combine Harvester")
  st.caption(f"Menampilkan Data Musim: **{musim_laporan}**")

  st.metric(
      "TOTAL PENDAPATAN COMBINE", f"Rp {tot_combine:,.0f}".replace(",", ".")
  )
  st.markdown("---")

  df_cb_baru = df_transaksi[
      (df_transaksi["kategori"] == "Combine")
      & (df_transaksi["jenis"] == "Pemasukan")
  ]
  if not df_cb_baru.empty:
    st.dataframe(df_cb_baru, use_container_width=True)
  else:
    st.info(
        f"💡 Belum ada data transaksi Combine yang dicatat untuk musim"
        f" **{musim_laporan}**."
    )

# -------------------- UNIT ROTAVATOR --------------------
elif menu == "⚙️ Unit Rotavator (Lahan)":
  st.title("⚙️ Laporan Pengolahan Lahan - Rotavator")
  st.caption(f"Menampilkan Data Musim: **{musim_laporan}**")

  st.metric(
      "TOTAL PENDAPATAN ROTAVATOR", f"Rp {tot_rotavator:,.0f}".replace(",", ".")
  )
  st.markdown("---")

  df_rv_baru = df_transaksi[
      (df_transaksi["kategori"] == "Rotavator")
      & (df_transaksi["jenis"] == "Pemasukan")
  ]
  if not df_rv_baru.empty:
    st.dataframe(df_rv_baru, use_container_width=True)
  else:
    st.info(
        f"💡 Belum ada data transaksi Rotavator yang dicatat untuk musim"
        f" **{musim_laporan}**."
    )

# -------------------- UNIT PESTISIDA & KIOS --------------------
elif menu == "🧪 Unit Pestisida & Kios":
  st.title("🧪 Laporan Belanja Obat & Pestisida Anggota")
  st.caption(f"Menampilkan Data Musim: **{musim_laporan}**")

  st.metric(
      "TOTAL PEMASUKAN PESTISIDA", f"Rp {tot_pestisida:,.0f}".replace(",", ".")
  )
  st.markdown("---")

  if not df_pestisida.empty:
    col_p_s1, col_p_s2 = st.columns([2, 1])
    with col_p_s1:
      cari_pestisida = st.text_input("🔍 Cari Nama Anggota:")
    with col_p_s2:
      filter_pestisida_status = st.selectbox(
          "Status Tagihan:", ["Semua Status", "Belum Lunas", "Lunas"]
      )

    df_p_show = df_pestisida.copy()
    if cari_pestisida:
      df_p_show = df_p_show[
          df_p_show["nama"].str.contains(cari_pestisida, case=False, na=False)
      ]
    if filter_pestisida_status != "Semua Status":
      df_p_show = df_p_show[df_p_show["status"] == filter_pestisida_status]

    st.dataframe(df_p_show, use_container_width=True)

  df_pst_baru = df_transaksi[
      (df_transaksi["kategori"] == "Pestisida")
      & (df_transaksi["jenis"] == "Pemasukan")
  ]
  if not df_pst_baru.empty:
    st.subheader("➕ Transaksi Pemasukan Pestisida")
    st.dataframe(df_pst_baru, use_container_width=True)
  elif df_pestisida.empty:
    st.info(
        f"💡 Belum ada data tagihan atau transaksi pestisida untuk musim"
        f" **{musim_laporan}**."
    )

  if is_admin and musim_laporan == musim_aktif:
    st.markdown("---")
    st.subheader("➕ Tambah Tagihan Pestisida Anggota Baru")
    with st.form("form_add_pestisida"):
      nama_p = st.text_input("Nama Anggota")
      tagihan_p = st.number_input(
          "Jumlah Tagihan (Rp)", min_value=0, step=50000
      )
      status_p = st.selectbox("Status Tagihan", ["Belum Lunas", "Lunas"])
      btn_p = st.form_submit_button("Simpan Tagihan Pestisida")

      if btn_p and nama_p:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT MAX(no) FROM pestisida WHERE musim = ?", (musim_aktif,))
        max_no = c.fetchone()[0]
        next_no = (max_no or 0) + 1
        c.execute(
            "INSERT INTO pestisida (musim, no, nama, jumlah_tagihan, status)"
            " VALUES (?, ?, ?, ?, ?)",
            (musim_aktif, next_no, nama_p, tagihan_p, status_p),
        )
        conn.commit()
        conn.close()
        st.success(f"Berhasil menambahkan tagihan pestisida **{nama_p}**!")
        st.rerun()

# -------------------- KREDIT BARANG --------------------
elif menu == "💳 Kredit & Cicilan Barang":
  st.title("💳 Laporan Kredit & Cicilan Barang Anggota")
  st.caption(f"Menampilkan Data Musim: **{musim_laporan}**")

  k1, k2, k3 = st.columns(3)
  k1.metric(
      "Total Nilai Barang", f"Rp {tot_nilai_kredit:,.0f}".replace(",", ".")
  )
  k2.metric(
      "Total Terbayar", f"Rp {tot_kredit_terbayar:,.0f}".replace(",", ".")
  )
  k3.metric(
      "Sisa Piutang Anggota", f"Rp {tot_sisa_piutang:,.0f}".replace(",", ".")
  )

  st.markdown("---")

  if not df_kredit.empty:
    st.dataframe(df_kredit, use_container_width=True)

  df_kd_baru = df_transaksi[
      (
          df_transaksi["kategori"].isin(
              ["Kredit Barang", "Kredit Cicilan Barang"]
          )
      )
      & (df_transaksi["jenis"] == "Pemasukan")
  ]
  if not df_kd_baru.empty:
    st.subheader("➕ Transaksi Pemasukan Cicilan Barang")
    st.dataframe(df_kd_baru, use_container_width=True)
  elif df_kredit.empty:
    st.info(f"💡 Belum ada data kredit barang untuk musim **{musim_laporan}**.")

  if is_admin and musim_laporan == musim_aktif:
    st.markdown("---")
    st.subheader("➕ Tambah Kredit Barang Baru")
    with st.form("form_add_kredit"):
      nama_k = st.text_input("Nama Anggota")
      barang_k = st.text_input("Nama Barang")
      harga_k = st.number_input("Harga Total (Rp)", min_value=0, step=100000)
      dp_k = st.number_input("DP / Uang Muka (Rp)", min_value=0, step=50000)
      btn_k = st.form_submit_button("Simpan Data Kredit")

      if btn_k and nama_k and barang_k:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("SELECT MAX(no) FROM kredit WHERE musim = ?", (musim_aktif,))
        max_no = c.fetchone()[0]
        next_no = (max_no or 0) + 1
        st_k = "Lunas" if dp_k >= harga_k else "Berjalan"
        c.execute(
            "INSERT INTO kredit (musim, no, nama_anggota, nama_barang,"
            " harga_total, dp, angsuran_masuk, status) VALUES (?, ?, ?, ?, ?,"
            " ?, 0, ?)",
            (musim_aktif, next_no, nama_k, barang_k, harga_k, dp_k, st_k),
        )
        conn.commit()
        conn.close()
        st.success(
            f"Berhasil menambahkan data kredit **{nama_k}** ({barang_k})!"
        )
        st.rerun()

# -------------------- PENGELUARAN --------------------
elif menu == "💸 Rincian Pengeluaran":
  st.title("💸 Laporan Pengeluaran & Belanja Modal")
  st.caption(f"Menampilkan Data Musim: **{musim_laporan}**")
  st.metric(
      "TOTAL PENGELUARAN MUSIM INI", f"Rp {tot_pengeluaran:,.0f}".replace(",", ".")
  )
  st.markdown("---")

  df_peng_baru = df_transaksi[df_transaksi["jenis"] == "Pengeluaran"]
  if not df_peng_baru.empty:
    df_exp_cat = (
        df_peng_baru.groupby("kategori")["jumlah"]
        .sum()
        .reset_index()
        .sort_values(by="jumlah", ascending=False)
    )
    fig_exp = px.bar(
        df_exp_cat, x="kategori", y="jumlah", text="jumlah", color="kategori"
    )
    fig_exp.update_traces(
        texttemplate="Rp %{text:,.0f}", textposition="outside"
    )
    st.plotly_chart(fig_exp, use_container_width=True)
    st.dataframe(df_peng_baru, use_container_width=True)
  else:
    st.info(
        f"💡 Belum ada pengeluaran yang dicatat untuk musim"
        f" **{musim_laporan}**."
    )

# -------------------- TAMBAH TRANSAKSI & HAPUS TRANSAKSI --------------------
elif menu == "➕ Tambah Transaksi":
  st.title("📝 Input Transaksi Kas Baru")
  st.caption(
      f"Transaksi baru akan otomatis dicatat ke Musim Aktif:"
      f" **{musim_aktif}**"
  )

  if not is_admin:
    st.warning(
        "🔒 Halaman ini khusus Pengurus. Silakan masukkan PIN Pengurus di panel"
        " samping kiri terlebih dahulu."
    )
  else:
    with st.form("form_transaksi"):
      jenis = st.selectbox("Jenis Transaksi", ["Pemasukan", "Pengeluaran"])
      kategori = st.selectbox(
          "Unit / Kategori",
          [
              "Combine",
              "Rotavator",
              "Pestisida",
              "Oven",
              "Kredit Barang",
              "Belanja Modal",
              "Bahan Bakar",
              "Lainnya",
          ],
      )
      keterangan = st.text_input("Keterangan Transaksi")
      jumlah_rp = st.number_input("Jumlah (Rupiah)", min_value=0, step=50000)

      submitted = st.form_submit_button("Simpan Transaksi")
      if submitted and keterangan:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute(
            "INSERT INTO transaksi (musim, tanggal, jenis, kategori, keterangan,"
            " jumlah) VALUES (?, date('now'), ?, ?, ?, ?)",
            (musim_aktif, jenis, kategori, keterangan, jumlah_rp),
        )
        conn.commit()
        conn.close()
        st.success(
            f"Berhasil menyimpan {jenis}: **{keterangan}** sebesar **Rp"
            f" {jumlah_rp:,.0f}**!"
        )
        st.rerun()

    st.markdown("---")
    st.subheader("🗑️ Hapus / Kelola Transaksi Manual")

    conn = get_db_connection()
    df_all_trans = pd.read_sql_query(
        "SELECT id, tanggal, jenis, kategori, keterangan, jumlah FROM"
        " transaksi WHERE musim = ?",
        conn,
        params=(musim_aktif,),
    )
    conn.close()

    if not df_all_trans.empty:
      st.dataframe(df_all_trans, use_container_width=True)
      with st.form("form_hapus_transaksi"):
        options_trans = [
            f"ID: {row['id']} | {row['jenis']} - {row['kategori']} -"
            f" {row['keterangan']} (Rp {row['jumlah']:,.0f})"
            for _, row in df_all_trans.iterrows()
        ]
        trans_to_delete = st.selectbox(
            "Pilih Transaksi yang Mau Dihapus:", options_trans
        )
        btn_delete = st.form_submit_button("🗑️ Hapus Transaksi Ini")

        if btn_delete and trans_to_delete:
          selected_id = int(
              trans_to_delete.split("|")[0].replace("ID:", "").strip()
          )
          conn = get_db_connection()
          c = conn.cursor()
          c.execute("DELETE FROM transaksi WHERE id = ?", (selected_id,))
          conn.commit()
          conn.close()
          st.success(f"Berhasil menghapus transaksi ID {selected_id}!")
          st.rerun()
    else:
      st.info("Belum ada transaksi manual yang dicatat di musim aktif ini.")

# -------------------- TUTUP BUKU & RESET MUSIM --------------------
elif menu == "🔴 Tutup Buku & Reset Musim":
  st.title("🔴 Fitur Tutup Buku & Reset untuk Musim Baru")

  if not is_admin:
    st.warning(
        "🔒 Halaman ini khusus Pengurus. Silakan masukkan PIN Pengurus di panel"
        " samping kiri terlebih dahulu."
    )
  else:
    st.error(
        "⚠️ **Perhatian Pengurus:** Fitur ini akan menutup pembukuan musim"
        " aktif saat ini dan memindahkan Saldo Akhir Kas sebagai Saldo Awal"
        " Musim Baru."
    )

    col_t1, col_t2 = st.columns(2)
    with col_t1:
      st.metric("Musim Aktif Saat Ini", musim_aktif)
      saldo_final_alihkan = st.number_input(
          "Saldo Akhir Kas Yang Dialihkan (Rp):",
          value=float(saldo_akhir_kas),
          step=100000.0,
      )

    with col_t2:
      nama_musim_baru = st.text_input("Ketik Nama Musim Baru:")
      konfirmasi_tutup = st.button(
          "🚀 Konfirmasi Tutup Buku & Mulai Musim Baru"
      )

      if konfirmasi_tutup and nama_musim_baru:
        set_saldo_awal_musim(nama_musim_baru, saldo_final_alihkan)
        set_setting("musim_aktif", nama_musim_baru)

        st.balloons()
        st.success(
            f"✅ Berhasil Tutup Buku! Musim baru **'{nama_musim_baru}'** telah"
            f" aktif dengan Saldo Awal **Rp {saldo_final_alihkan:,.0f}**."
        )
        st.rerun()
