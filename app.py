import os
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_gsheets import GSheetsConnection

# URL Google Sheets Database Kas Poktan
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1WrnS3pFzkIzIF8ekYGo1fHtMLfJ7QSEPYprJrdhdy48/edit?usp=drive_web"

# Config Halaman Streamlit
st.set_page_config(
    page_title="Sistem Kas POKTAN SUKA MAJU", page_icon="🌾", layout="wide"
)

# CSS Kustom
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


def render_logo(container, width=130):
  logo_files = ["logo.png", "logo.jpg", "logo.jpeg", "Logo.png", "LOGO.PNG"]
  for logo_file in logo_files:
    if os.path.exists(logo_file):
      container.image(logo_file, width=width)
      return True
  return False


# -------------------- GOOGLE SHEETS CONNECTION --------------------
conn = st.connection("gsheets", type=GSheetsConnection)


def load_sheet_data(worksheet_name, default_cols):
  try:
    df = conn.read(spreadsheet=SPREADSHEET_URL, worksheet=worksheet_name, ttl=0)
    if df.empty:
      return pd.DataFrame(columns=default_cols)
    return df
  except Exception:
    return pd.DataFrame(columns=default_cols)


def save_sheet_data(worksheet_name, df):
  conn.update(spreadsheet=SPREADSHEET_URL, worksheet=worksheet_name, data=df)


# Columns Definition
cols_settings = ["key", "value"]
cols_transaksi = [
    "id",
    "musim",
    "tanggal",
    "jenis",
    "kategori",
    "keterangan",
    "jumlah",
]
cols_pestisida = ["id", "musim", "no", "nama", "jumlah_tagihan", "status"]
cols_kredit = [
    "id",
    "musim",
    "no",
    "nama_anggota",
    "nama_barang",
    "harga_total",
    "dp",
    "angsuran_masuk",
    "status",
]

# Load All Dataframes from Sheets
df_settings = load_sheet_data("settings", cols_settings)
df_transaksi_all = load_sheet_data("transaksi", cols_transaksi)
df_pestisida_all = load_sheet_data("pestisida", cols_pestisida)
df_kredit_all = load_sheet_data("kredit", cols_kredit)


# Helper Functions
def get_setting(key, default_val=""):
  if not df_settings.empty and "key" in df_settings.columns:
    match = df_settings[df_settings["key"] == key]
    if not match.empty:
      return str(match.iloc[0]["value"])
  return default_val


def set_setting(key, value):
  global df_settings
  if df_settings.empty or "key" not in df_settings.columns:
    df_settings = pd.DataFrame([{"key": key, "value": str(value)}])
  else:
    if key in df_settings["key"].values:
      df_settings.loc[df_settings["key"] == key, "value"] = str(value)
    else:
      new_row = pd.DataFrame([{"key": key, "value": str(value)}])
      df_settings = pd.concat([df_settings, new_row], ignore_index=True)
  save_sheet_data("settings", df_settings)


def get_saldo_awal_musim(musim):
  val = get_setting(f"saldo_awal_{musim}", None)
  if val is None or str(val).strip() == "":
    return float(get_setting("saldo_awal", "233235079"))
  try:
    return float(val)
  except ValueError:
    return 233235079.0


def set_saldo_awal_musim(musim, val):
  set_setting(f"saldo_awal_{musim}", val)


def get_all_musim():
  musim_set = set()
  musim_aktif_val = get_setting("musim_aktif", "APRIL 2027 (Musim Gadu)")
  musim_set.add(musim_aktif_val)

  for df in [df_pestisida_all, df_kredit_all, df_transaksi_all]:
    if not df.empty and "musim" in df.columns:
      for m in df["musim"].dropna().unique():
        if str(m) and "OKT 2026" not in str(m):
          musim_set.add(str(m))

  if not df_settings.empty and "key" in df_settings.columns:
    for k in df_settings["key"].dropna().unique():
      if str(k).startswith("saldo_awal_"):
        key_name = str(k).replace("saldo_awal_", "")
        if key_name and "OKT 2026" not in key_name:
          musim_set.add(key_name)

  return sorted(list(musim_set), reverse=True)


# Load Musim Aktif
musim_aktif = get_setting("musim_aktif", "APRIL 2027 (Musim Gadu)")

# -------------------- SIDEBAR SETTINGS & LOGIN --------------------
render_logo(st.sidebar, width=130)

st.sidebar.title("POKTAN SUKA MAJU")
st.sidebar.caption("Aplikasi Kas & Unit Usaha (Google Sheets)")

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

# Filter Data Berdasarkan Musim
df_pestisida = (
    df_pestisida_all[df_pestisida_all["musim"] == musim_laporan]
    if not df_pestisida_all.empty and "musim" in df_pestisida_all.columns
    else pd.DataFrame(columns=cols_pestisida)
)
df_kredit = (
    df_kredit_all[df_kredit_all["musim"] == musim_laporan]
    if not df_kredit_all.empty and "musim" in df_kredit_all.columns
    else pd.DataFrame(columns=cols_kredit)
)
df_transaksi = (
    df_transaksi_all[df_transaksi_all["musim"] == musim_laporan]
    if not df_transaksi_all.empty and "musim" in df_transaksi_all.columns
    else pd.DataFrame(columns=cols_transaksi)
)

if not df_kredit.empty:
  df_kredit["dp"] = pd.to_numeric(df_kredit["dp"], errors="coerce").fillna(0)
  df_kredit["angsuran_masuk"] = pd.to_numeric(
      df_kredit["angsuran_masuk"], errors="coerce"
  ).fillna(0)
  df_kredit["harga_total"] = pd.to_numeric(
      df_kredit["harga_total"], errors="coerce"
  ).fillna(0)
  df_kredit["TOTAL_TERBAYAR"] = df_kredit["dp"] + df_kredit["angsuran_masuk"]
  df_kredit["SISA_PIUTANG"] = (
      df_kredit["harga_total"] - df_kredit["TOTAL_TERBAYAR"]
  )

# Hitung Rekap Pemasukan & Pengeluaran
if not df_transaksi.empty:
  df_transaksi["jumlah"] = pd.to_numeric(
      df_transaksi["jumlah"], errors="coerce"
  ).fillna(0)
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
    pd.to_numeric(df_pestisida["jumlah_tagihan"], errors="coerce")
    .fillna(0)
    .sum()
    if not df_pestisida.empty
    else 0
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
    st.dataframe(df_pestisida, use_container_width=True)

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
        next_id = (
            int(df_pestisida_all["id"].max()) + 1
            if not df_pestisida_all.empty and "id" in df_pestisida_all.columns
            else 1
        )
        new_row = pd.DataFrame([{
            "id": next_id,
            "musim": musim_aktif,
            "no": next_id,
            "nama": nama_p,
            "jumlah_tagihan": tagihan_p,
            "status": status_p,
        }])
        df_pestisida_all = pd.concat(
            [df_pestisida_all, new_row], ignore_index=True
        )
        save_sheet_data("pestisida", df_pestisida_all)
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
        next_id = (
            int(df_kredit_all["id"].max()) + 1
            if not df_kredit_all.empty and "id" in df_kredit_all.columns
            else 1
        )
        st_k = "Lunas" if dp_k >= harga_k else "Berjalan"
        new_row = pd.DataFrame([{
            "id": next_id,
            "musim": musim_aktif,
            "no": next_id,
            "nama_anggota": nama_k,
            "nama_barang": barang_k,
            "harga_total": harga_k,
            "dp": dp_k,
            "angsuran_masuk": 0,
            "status": st_k,
        }])
        df_kredit_all = pd.concat([df_kredit_all, new_row], ignore_index=True)
        save_sheet_data("kredit", df_kredit_all)
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

# -------------------- TAMBAH TRANSAKSI --------------------
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
        next_id = (
            int(df_transaksi_all["id"].max()) + 1
            if not df_transaksi_all.empty and "id" in df_transaksi_all.columns
            else 1
        )
        new_row = pd.DataFrame([{
            "id": next_id,
            "musim": musim_aktif,
            "tanggal": str(pd.Timestamp.now().strftime("%Y-%m-%d")),
            "jenis": jenis,
            "kategori": kategori,
            "keterangan": keterangan,
            "jumlah": jumlah_rp,
        }])
        df_transaksi_all = pd.concat(
            [df_transaksi_all, new_row], ignore_index=True
        )
        save_sheet_data("transaksi", df_transaksi_all)
        st.success(
            f"Berhasil menyimpan {jenis}: **{keterangan}** sebesar **Rp"
            f" {jumlah_rp:,.0f}**!"
        )
        st.rerun()

    # Form Hapus Transaksi
    st.markdown("---")
    st.subheader("🗑️ Hapus / Kelola Transaksi Manual")
    if not df_transaksi.empty:
      st.dataframe(df_transaksi, use_container_width=True)
      with st.form("form_hapus_transaksi"):
        options_trans = [
            f"ID: {row['id']} | {row['jenis']} - {row['kategori']} -"
            f" {row['keterangan']} (Rp {row['jumlah']:,.0f})"
            for _, row in df_transaksi.iterrows()
        ]
        trans_to_delete = st.selectbox(
            "Pilih Transaksi yang Mau Dihapus:", options_trans
        )
        btn_delete = st.form_submit_button("🗑️ Hapus Transaksi Ini")

        if btn_delete and trans_to_delete:
          selected_id = int(
              trans_to_delete.split("|")[0].replace("ID:", "").strip()
          )
          df_transaksi_all = df_transaksi_all[
              df_transaksi_all["id"] != selected_id
          ]
          save_sheet_data("transaksi", df_transaksi_all)
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
