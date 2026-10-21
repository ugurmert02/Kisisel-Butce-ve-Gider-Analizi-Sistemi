import csv
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import json
DOSYA_ADI = "harcamalarim.csv"
LIMIT_DOSYASI = "limitler.json"
KATEGORILER = ["Yemek", "Ulaşım", "Fatura", "Eğlence", "Diğer"]
def kategori_sec() :
    print("\nKategori seçin :")
    for sira, kategori in enumerate (KATEGORILER, start=1):
        print(f"{sira}- {kategori}")
    while True :
        try :
            secim = int(input("Kategori Numarası : "))
            if 1 <= secim <= len(KATEGORILER):
                return KATEGORILER[secim - 1]
            print(f"HATA: 1 ile {len(KATEGORILER)} arasında bir sayı girin!")
        except ValueError :
            print("Hata: Lütfen sadece rakam girin!")


def rapor_goster():
    if not os.path.isfile(DOSYA_ADI):
        print("Henüz Kayıtlı Harcama Yok.")
        return
    df = pd.read_csv(DOSYA_ADI)
    toplam = df["Tutar(TL)"].sum()

    print("\n--- HARCAMA RAPORU ---")
    print(f"Harcama sayısı : {len(df)}")
    print(f"Toplam harcama : {toplam:.2f} TL")
    print("\nKategorilere göre :")
    kategori_toplamlari = df.groupby("Kategori")["Tutar(TL)"].sum()
    for kategori, tutar in kategori_toplamlari.items():
        yuzde = tutar / toplam * 100
        print(f"  {kategori:<10} {tutar:>10.2f} TL (%{yuzde:.1f})")
    plt.pie(kategori_toplamlari, labels=kategori_toplamlari.index, autopct="%1.1f%%")
    plt.title("Kategorilere Göre Harcamalar")
    plt.show()
def harcamalari_listele():
    if not os.path.isfile(DOSYA_ADI):
        print("Henüz kayıtlı harcama yok.")
        return

    df = pd.read_csv(DOSYA_ADI)
    print("\n--- TÜM HARCAMALAR ---")
    print(df.to_string())

def harcama_sil():
    if not os.path.isfile(DOSYA_ADI):
        print("Henüz kayıtlı harcama yok.")
        return
def limitleri_yukle():
    if not os.path.isfile(LIMIT_DOSYASI):
        return {}
    with open(LIMIT_DOSYASI, mode="r", encoding="utf-8") as dosya:
        return json.load(dosya)
def limit_belirle():
    print("\n--- AYLIK LİMİT BELİRLE ---")
    kategori = kategori_sec()

    try:
        limit = float(input(f"{kategori} için aylık limit (TL): ").replace(",", "."))
    except ValueError:
        print("HATA: Lütfen sadece rakam girin!")
        return

    if limit <= 0:
        print("HATA: Limit sıfırdan büyük olmalı!")
        return

    limitler = limitleri_yukle()
    limitler[kategori] = limit

    with open(LIMIT_DOSYASI, mode="w", encoding="utf-8") as dosya:
        json.dump(limitler, dosya, ensure_ascii=False, indent=2)

    print(f"[BAŞARILI] {kategori} için aylık limit {limit:.2f} TL olarak ayarlandı.")
def limit_kontrol(kategori):
    limit = limitleri_yukle().get(kategori)
    if limit is None:
        return

    df = pd.read_csv(DOSYA_ADI)
    bu_ay = datetime.now().strftime("%Y-%m")
    secili = df[(df["Kategori"] == kategori) & (df["Tarih"].str.startswith(bu_ay))]
    harcanan = secili["Tutar(TL)"].sum()

    if harcanan > limit:
        print(f"⚠ UYARI: {kategori} aylık limitini aştınız! ({harcanan:.2f} / {limit:.2f} TL)")

    df = pd.read_csv(DOSYA_ADI)
    if df.empty:
        print("Henüz kayıtlı harcama yok.")
        return

    harcamalari_listele()

    try:
        numara = int(input("\nSilinecek harcamanın numarası: "))
    except ValueError:
        print("HATA: Lütfen sadece rakam girin!")
        return

    if numara not in df.index:
        print("HATA: Bu numarada bir harcama yok!")
        return

    silinecek = df.loc[numara]
    onay = input(f"'{silinecek['Aciklama']}' ({silinecek['Tutar(TL)']} TL) silinsin mi? (e/h): ")

    if onay.lower() == "e":
        df = df.drop(numara)
        df.to_csv(DOSYA_ADI, index=False, encoding="utf-8")
        print("[BAŞARILI] Harcama silindi.")
    else:
        print("Silme iptal edildi.")

while True :
    print("\n--- BÜTÇE ASİSTANI")
    print("1- Yeni Harcama Ekle")
    print("2- Rapor Gör")
    print("3- Harcamaları Listele")
    print("4- Harcama Sil")
    print("5- Limit Belirle")
    print("6- Çıkış")
    secim = input ("Lütfen bir işlem seçin")
    if secim == "6" :
        print("Sistem kapatılıyor. Kayıtlar güvende!")
        break
    elif secim == "1":
        print("\n--- YENİ HARCAMA GİRİŞİ ---")
        aciklama = input("Ne aldınız?")
        try:
            tutar = float(input("Tutar(TL): "))
            kategori = kategori_sec()
            dosya_var_mi = os.path.isfile(DOSYA_ADI)
            
            with open(DOSYA_ADI, mode="a", newline="", encoding="utf-8") as dosya:
                yazici = csv.writer(dosya)
                
                if not dosya_var_mi:
                    yazici.writerow(["Tarih", "Aciklama","Kategori", "Tutar(TL)"])                   
                tarih = datetime.now().strftime("%Y-%m-%d %H:%M")
                yazici.writerow([tarih, aciklama, kategori, tutar])
                
            print(f"[BAŞARILI] {tutar} TL tutarındaki harcama kaydedildi!")
            limit_kontrol(kategori)
            
        except ValueError:
            print("HATA: Lütfen tutarı sadece rakamla girin!")

    elif secim == "2":
        rapor_goster()
    elif secim == "3":
        harcamalari_listele()
    elif secim == "4":
        harcama_sil()
    elif secim == "5":
        limit_belirle()
    else:
        print("Hata: Sadece 1,2,3,4,5 veya 6 tuşlayın!")
    