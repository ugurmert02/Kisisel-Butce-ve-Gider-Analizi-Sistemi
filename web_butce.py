import streamlit as st
import pandas as pd
import os
import json
import csv
from datetime import datetime
import matplotlib.pyplot as plt # Senin eklediğin grafik kütüphanesi

# --- DOSYA YOLLARI VE AYARLAR ---
DOSYA_ADI = "harcamalarim.csv"
LIMIT_DOSYASI = "limitler.json"
KATEGORILER = ["Yemek", "Ulaşım", "Fatura", "Eğlence", "Diğer"]

def limitleri_yukle():
    if not os.path.isfile(LIMIT_DOSYASI):
        return {}
    with open(LIMIT_DOSYASI, mode="r", encoding="utf-8") as dosya:
        return json.load(dosya)

# Sayfa Görünümü
st.set_page_config(page_title="Bütçe Asistanı", page_icon="💰")
st.title("💰 Kişisel Bütçe ve Gider Analizi")

# Tüm özelliklerin için 4 Sekme (Tab) oluşturuyoruz
tab1, tab2, tab3, tab4 = st.tabs(["🛒 Yeni Harcama", "📊 Raporlar (Grafik)", "🗑️ Harcama Sil", "⚙️ Limit Ayarları"])

# --- SEKME 1: YENİ HARCAMA VE LİMİT KONTROLÜ ---
with tab1:
    st.header("Yeni Harcama Ekle")
    with st.form("harcama_formu"):
        aciklama = st.text_input("Ne aldınız?")
        tutar = st.number_input("Tutar (TL)", min_value=0.0, step=10.0)
        kategori = st.selectbox("Kategori Seçin", KATEGORILER)
        kaydet = st.form_submit_button("Harcamayı Kaydet")

        if kaydet:
            if aciklama != "" and tutar > 0:
                dosya_var_mi = os.path.isfile(DOSYA_ADI)
                with open(DOSYA_ADI, mode="a", newline="", encoding="utf-8") as dosya:
                    yazici = csv.writer(dosya)
                    if not dosya_var_mi:
                        yazici.writerow(["Tarih", "Aciklama", "Kategori", "Tutar(TL)"])
                    tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                    yazici.writerow([tarih, aciklama, kategori, tutar])
                st.success(f"✅ {tutar} TL tutarındaki harcama kaydedildi!")
                
                # Senin Yazdığın Limit Kontrolü
                limitler = limitleri_yukle()
                if kategori in limitler:
                    limit = limitler[kategori]
                    df = pd.read_csv(DOSYA_ADI)
                    bu_ay = datetime.now().strftime("%Y-%m")
                    secili = df[(df["Kategori"] == kategori) & (df["Tarih"].str.startswith(bu_ay))]
                    harcanan = secili["Tutar(TL)"].sum()
                    if harcanan > limit:
                        st.error(f"🚨 DİKKAT: {kategori} aylık limitinizi aştınız! (Harcanan: {harcanan:.2f} TL / Limit: {limit:.2f} TL)")
            else:
                st.error("⚠️ Lütfen geçerli bir açıklama ve tutar girin!")

# --- SEKME 2: RAPORLAR VE PASTA GRAFİĞİ ---
with tab2:
    st.header("Geçmiş Harcamalar ve Analiz")
    if os.path.isfile(DOSYA_ADI):
        df = pd.read_csv(DOSYA_ADI)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
            st.info(f"**Toplam Harcamanız: {df['Tutar(TL)'].sum():.2f} TL**")
            
            # Senin eklediğin Matplotlib Pasta Grafiği
            st.subheader("Kategorilere Göre Dağılım")
            kategori_toplamlari = df.groupby("Kategori")["Tutar(TL)"].sum()
            
            fig, ax = plt.subplots()
            ax.pie(kategori_toplamlari, labels=kategori_toplamlari.index, autopct="%1.1f%%", startangle=90)
            ax.axis('equal') # Grafiğin tam yuvarlak görünmesi için
            st.pyplot(fig) # Streamlit içinde grafiği çizdirme komutu
        else:
            st.warning("Henüz kayıtlı harcama yok.")
    else:
        st.warning("Harcama dosyası bulunamadı.")

# --- SEKME 3: HARCAMA SİLME ---
with tab3:
    st.header("Harcama Sil")
    if os.path.isfile(DOSYA_ADI):
        df = pd.read_csv(DOSYA_ADI)
        if not df.empty:
            st.write("Silmek istediğiniz harcamanın tablodaki numarasını (en soldaki index) seçin:")
            st.dataframe(df, use_container_width=True)
            
            # Senin yazdığın index ile silme mantığı
            silinecek_index = st.number_input("Silinecek Index Numarası:", min_value=0, max_value=len(df)-1, step=1)
            sil_butonu = st.button("🗑️ Seçili Harcamayı Sil")
            
            if sil_butonu:
                if silinecek_index in df.index:
                    silinen_bilgi = df.loc[silinecek_index, 'Aciklama']
                    df = df.drop(silinecek_index)
                    df.to_csv(DOSYA_ADI, index=False, encoding="utf-8")
                    st.success(f"✅ '{silinen_bilgi}' harcaması başarıyla silindi!")
                    st.rerun() # Silme işleminden sonra sayfayı otomatik yeniler
                else:
                    st.error("Bu numarada bir harcama bulunamadı.")
        else:
            st.info("Silinecek harcama yok.")
    else:
        st.warning("Harcama dosyası bulunamadı.")

# --- SEKME 4: LİMİT AYARLARI ---
with tab4:
    st.header("Kategori Limitleri")
    limitler = limitleri_yukle()
    if limitler:
        st.write("📊 **Mevcut Limitleriniz:**")
        for kat, lim in limitler.items():
            st.info(f"**{kat}:** {lim} TL")
    else:
        st.write("Henüz limit belirlenmemiş.")
        
    st.divider()
    st.subheader("Yeni Limit Belirle")
    with st.form("limit_formu"):
        limit_kategori = st.selectbox("Limit Koyulacak Kategori", KATEGORILER)
        yeni_limit = st.number_input("Aylık Limit (TL)", min_value=0.0, step=50.0)
        limit_kaydet = st.form_submit_button("Limiti Kaydet")
        
        if limit_kaydet:
            if yeni_limit > 0:
                limitler[limit_kategori] = yeni_limit
                with open(LIMIT_DOSYASI, mode="w", encoding="utf-8") as dosya:
                    json.dump(limitler, dosya, ensure_ascii=False, indent=2)
                st.success(f"✅ {limit_kategori} kategorisi limiti {yeni_limit} TL olarak ayarlandı!")
                st.rerun() # Kayıttan sonra tabloyu güncelle
            else:
                st.error("Limit sıfırdan büyük olmalı!")
                # Sayfanın en altındaki imza kısmı
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>💻 Developed by Uğur Mert Yıldırım © 2026</p>", unsafe_allow_html=True)
