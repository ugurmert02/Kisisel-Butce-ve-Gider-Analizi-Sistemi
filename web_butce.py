import streamlit as st
import pandas as pd
import os
import json
import csv
from datetime import datetime
import matplotlib.pyplot as plt

st.set_page_config(page_title="Bütçe Asistanı", page_icon="💰")

# --- KULLANICI VERİ TABANI AYARLARI ---
KULLANICI_DOSYASI = "kullanicilar.json"

def kullanicilari_yukle():
    if not os.path.isfile(KULLANICI_DOSYASI):
        return {}
    with open(KULLANICI_DOSYASI, mode="r", encoding="utf-8") as dosya:
        return json.load(dosya)

def kullanici_kaydet(kadi, sifre):
    kullanicilar = kullanicilari_yukle()
    kullanicilar[kadi] = sifre
    with open(KULLANICI_DOSYASI, mode="w", encoding="utf-8") as dosya:
        json.dump(kullanicilar, dosya)

# --- OTURUM (SESSION) KONTROLÜ ---
if "kullanici" not in st.session_state:
    st.session_state.kullanici = None

# --- 1. GİRİŞ VE KAYIT EKRANI ---
if st.session_state.kullanici is None:
    st.title("🔐 Bütçe Asistanına Hoş Geldiniz")
    
    tab_giris, tab_kayit = st.tabs(["🔑 Giriş Yap", "📝 Yeni Kayıt Ol"])
    
    with tab_giris:
        with st.form("giris_formu"):
            giris_kadi = st.text_input("Kullanıcı Adı").strip().lower()
            giris_sifre = st.text_input("Şifre", type="password") # Şifreyi gizler
            giris_butonu = st.form_submit_button("Giriş Yap")
            
            if giris_butonu:
                kullanicilar = kullanicilari_yukle()
                if giris_kadi in kullanicilar and kullanicilar[giris_kadi] == giris_sifre:
                    st.session_state.kullanici = giris_kadi
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı!")
                    
    with tab_kayit:
        with st.form("kayit_formu"):
            yeni_kadi = st.text_input("Belirlemek İstediğiniz Kullanıcı Adı").strip().lower()
            yeni_sifre = st.text_input("Şifre Belirleyin", type="password")
            sifre_tekrar = st.text_input("Şifrenizi Tekrar Girin", type="password")
            kayit_butonu = st.form_submit_button("Kayıt Ol")
            
            if kayit_butonu:
                kullanicilar = kullanicilari_yukle()
                if yeni_kadi == "":
                    st.error("Kullanıcı adı boş olamaz!")
                elif yeni_kadi in kullanicilar:
                    st.error("Bu kullanıcı adı zaten alınmış. Lütfen başka bir tane seçin.")
                elif yeni_sifre != sifre_tekrar:
                    st.error("Şifreler birbiriyle uyuşmuyor!")
                elif len(yeni_sifre) < 4:
                    st.error("Şifreniz en az 4 karakter olmalı!")
                else:
                    kullanici_kaydet(yeni_kadi, yeni_sifre)
                    st.success("✅ Kayıt başarılı! Yandaki sekmeden giriş yapabilirsiniz.")

# --- 2. UYGULAMA ANA EKRANI (GİRİŞ BAŞARILIYSA) ---
else:
    aktif_kullanici = st.session_state.kullanici
    DOSYA_ADI = f"{aktif_kullanici}_harcamalar.csv"
    LIMIT_DOSYASI = f"{aktif_kullanici}_limitler.json"
    KATEGORILER = ["Yemek", "Ulaşım", "Fatura", "Eğlence", "Diğer"]

    def limitleri_yukle():
        if not os.path.isfile(LIMIT_DOSYASI):
            return {}
        with open(LIMIT_DOSYASI, mode="r", encoding="utf-8") as dosya:
            return json.load(dosya)

    col1, col2 = st.columns([4, 1])
    with col1:
        st.title(f"💰 {aktif_kullanici.capitalize()} - Bütçe")
    with col2:
        if st.button("🚪 Çıkış"):
            st.session_state.kullanici = None
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs(["🛒 Yeni Harcama", "📊 Raporlar", "🗑️ Harcama Sil", "⚙️ Limitler"])

    with tab1:
        st.header("Yeni Harcama Ekle")
        with st.form("harcama_formu"):
            aciklama = st.text_input("Ne aldınız?")
            tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
            kategori = st.selectbox("Kategori Seçin", KATEGORILER)
            kaydet = st.form_submit_button("Kaydet")

            if kaydet:
                if aciklama != "" and tutar > 0:
                    dosya_var_mi = os.path.isfile(DOSYA_ADI)
                    with open(DOSYA_ADI, mode="a", newline="", encoding="utf-8") as dosya:
                        yazici = csv.writer(dosya)
                        if not dosya_var_mi:
                            yazici.writerow(["Tarih", "Aciklama", "Kategori", "Tutar(TL)"])
                        tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                        yazici.writerow([tarih, aciklama, kategori, tutar])
                    st.success("✅ Kaydedildi!")
                    
                    limitler = limitleri_yukle()
                    if kategori in limitler:
                        limit = limitler[kategori]
                        df = pd.read_csv(DOSYA_ADI)
                        bu_ay = datetime.now().strftime("%Y-%m")
                        secili = df[(df["Kategori"] == kategori) & (df["Tarih"].str.startswith(bu_ay))]
                        harcanan = secili["Tutar(TL)"].sum()
                        if harcanan > limit:
                            st.error(f"🚨 {kategori} limiti aşıldı! (Harcanan: {harcanan} / Limit: {limit})")
                else:
                    st.error("Geçerli değer girin!")

    with tab2:
        if os.path.isfile(DOSYA_ADI):
            df = pd.read_csv(DOSYA_ADI)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                st.info(f"**Toplam: {df['Tutar(TL)'].sum():.2f} TL**")
                
                fig, ax = plt.subplots()
                kat_toplam = df.groupby("Kategori")["Tutar(TL)"].sum()
                ax.pie(kat_toplam, labels=kat_toplam.index, autopct="%1.1f%%", startangle=90)
                ax.axis('equal')
                st.pyplot(fig)
            else:
                st.warning("Harcama yok.")
        else:
            st.warning("Dosya yok.")

    with tab3:
        if os.path.isfile(DOSYA_ADI):
            df = pd.read_csv(DOSYA_ADI)
            if not df.empty:
                st.dataframe(df, use_container_width=True)
                silinecek = st.number_input("Silinecek Index:", min_value=0, max_value=len(df)-1, step=1)
                if st.button("🗑️ Sil"):
                    if silinecek in df.index:
                        df = df.drop(silinecek)
                        df.to_csv(DOSYA_ADI, index=False)
                        st.success("✅ Silindi!")
                        st.rerun()
            else:
                st.warning("Silinecek kayıt yok.")

    with tab4:
        limitler = limitleri_yukle()
        if limitler:
            for kat, lim in limitler.items():
                st.info(f"**{kat}:** {lim} TL")
        with st.form("limit_formu"):
            limit_kategori = st.selectbox("Kategori", KATEGORILER)
            yeni_limit = st.number_input("Limit (TL)", min_value=0.0, step=50.0)
            if st.form_submit_button("Kaydet") and yeni_limit > 0:
                limitler[limit_kategori] = yeni_limit
                with open(LIMIT_DOSYASI, mode="w", encoding="utf-8") as d:
                    json.dump(limitler, d)
                st.success("✅ Kaydedildi!")
                st.rerun()

    st.markdown("---")
    st.markdown("<p style='text-align: center; color: gray;'>💻 Developed by Uğur Mert Yıldırım © 2026</p>", unsafe_allow_html=True)