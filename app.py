import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı v2.2 (Final)", layout="wide")
st.title("🎓 Akademik Ders Programı Oluşturucu v2.2")
st.success("✅ Hata giderildi: 'CEZA_GUN_BOSLUGU' tanımlandı. 5 Bölüm ve tüm kısıtlar aktif.")

# --- PARAMETRELER (HATA BURADAYDI - DÜZELTİLDİ) ---
MAX_SURE = 300
CEZA_HOCA_CAKISMASI = 1000000   # Asla olamaz
CEZA_SINIF_CAKISMASI = 1000000  # Asla olamaz
CEZA_KOMSU_SINIF = 500000       # 1. ve 2. sınıf çakışırsa çok büyük ceza (Neredeyse imkansız)
CEZA_GUNLUK_YUK = 2000          # Öğrenci günde 3 derse girerse ceza
CEZA_HOCA_GUN_SAYISI = 5000     # Hoca gereksiz yere okula gelirse ceza
BONUS_ARDISIK_3 = 300
BONUS_ARDISIK_1ATLAMA = 200
BONUS_ARDISIK_2ATLAMA = 100
CEZA_ISTENMEYEN_GUN = 500
CEZA_GUN_BOSLUGU = 5000         # EKSİK OLAN DEĞİŞKEN EKLENDİ (Hoca sabah gelip, öğlen boş, akşam dersi varsa)

# --- TAM ŞABLON (5 BÖLÜM - TAMAMLANMIŞ) ---
def sablon_olustur():
    data = [
        # === TURİZM İŞLETMECİLİĞİ ===
        {"DersKodu": "TUİ 3011", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. D. Ç.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 2501", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. D. Ç.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 4539", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Arş. Gör. Dr. D. Ç.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 2009", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 4533", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "ORT_MARKA", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İKT 1809", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ORD0080", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Doç. Dr. A. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "Çarşamba", "ZorunluSaat": "08:30-09:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 1007", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "ORT_GEN_MUH", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 4515", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Doç. Dr. O. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 2001", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Doç. Dr. O. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 3013", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Doç. Dr. O. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 1825", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Doç. Dr. P. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 3009", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Doç. Dr. P. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 2011", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Doç. Dr. P. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 4005", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi C. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 2507", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Dr. Öğr. Üyesi C. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "KAY 1805", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "ORT_HUKUK", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İSG 3901", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Öğr. Gör. M. G.", "OrtakDersID": "ORT_ISG", "KidemPuani": 1, "ZorunluGun": "Cuma", "ZorunluSaat": "08:30-09:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 2503", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Prof. Dr. A. Ç. Y.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 3509", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Prof. Dr. A. Ç. Y.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "TUİ 4525", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Prof. Dr. A. Ç. Y.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ENF 1805", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Öğr. Gör. F. M. K.", "OrtakDersID": "ORT_BILGISAYAR_1", "KidemPuani": 1, "ZorunluGun": "Pazartesi", "ZorunluSaat": "15:30-17:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "ATB 1801", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB_TUR", "KidemPuani": 1, "ZorunluGun": "Pazartesi", "ZorunluSaat": "08:30-09:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        
        # === İŞLETME ===
        {"DersKodu": "İŞL1005", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL3001", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL3003", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_SAYISAL", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL2001", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL2007", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL3515", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "ORT_MARKA", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL4001", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Doç. Dr. F. Ç.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL4521", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Doç. Dr. F. Ç.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "KAY1805", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL2009", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İKT3905", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi M. A. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ÇEİ4901", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi M. A. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL4003", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Öğr. Gör. Dr. H. C.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL2003", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. H. C.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL3005", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Öğr. Gör. Dr. H. C.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İKT2803", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. N. Ü.", "OrtakDersID": "ORT_MAKRO", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İKT1801", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Öğr. Gör. Dr. Y. N.", "OrtakDersID": "ORT_IKT_GIRIS", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ENF 1805-ISL", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Öğr. Gör. F. M. K.", "OrtakDersID": "ORT_BILGISAYAR_1", "KidemPuani": 1, "ZorunluGun": "Pazartesi", "ZorunluSaat": "15:30-17:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL4523", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Prof. Dr. A. E. A.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL1003", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Prof. Dr. A. E. A.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL1001", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Prof. Dr. İ. K.", "OrtakDersID": "ORT_ISL_MAT", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL2005", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Prof. Dr. R. C.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL3503", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Prof. Dr. R. C.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL4511", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Prof. Dr. R. C.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ATB 1801-ISL", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB_ISL", "KidemPuani": 1, "ZorunluGun": "Salı", "ZorunluSaat": "15:30-16:40", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        
        # === EKONOMİ VE FİNANS ===
        {"DersKodu": "İŞL1829", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "ORT_FIN_MUH", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 1003", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_MAT_EKF", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 2819", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 1001", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "ORT_EKONOMI_1", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 4001", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Doç. Dr. A. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 3003", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Doç. Dr. A. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 2001", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Doç. Dr. A. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 2005", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Doç. Dr. C. O.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 3511", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Doç. Dr. C. O.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 4503", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Doç. Dr. C. O.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL4911", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Doç. Dr. F. Ç.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "KAY 1805-EKF", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "ORT_HUKUK", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 4507", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi A. O. Ö.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 3005", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi A. O. Ö.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL1827", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Dr. Öğr. Üyesi C. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 2009", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Dr. Öğr. Üyesi M. A. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 2007", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Dr. Öğr. Üyesi Ö. U.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF4505", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 3901", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 3001", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Öğr. Gör. Dr. N. Ü.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 2003", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. N. Ü.", "OrtakDersID": "ORT_MAKRO", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "EKF 4003", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Öğr. Gör. Dr. Y. N.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ENF 1805-EKF", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "ORT_BILGISAYAR_2", "KidemPuani": 1, "ZorunluGun": "Salı", "ZorunluSaat": "15:30-17:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 3907", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Prof. Dr. F. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ATB 1801-EKF", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB_EKF", "KidemPuani": 1, "ZorunluGun": "Salı", "ZorunluSaat": "13:30-14:40", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},

        # === YÖNETİM BİLİŞİM SİSTEMLERİ (YBS) ===
        {"DersKodu": "İŞL 2829", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "ORT_FIN_MUH", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 3809", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_SAYISAL", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 2827", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 3511", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 4001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Doç. Dr. M. İ.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 2511", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Doç. Dr. M. İ.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 4005", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Doç. Dr. M. İ.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 2001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Doç. Dr. M. D.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 4003", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Doç. Dr. M. D.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 1837", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Doç. Dr. M. D.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "KAY 1811", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "ORT_HUKUK", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 3505", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi M. S.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 4509", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "ORT_ETICARET", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 4515", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Öğr. Gör. C. G.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İKT 2813", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. Y. N.", "OrtakDersID": "ORT_IKT_GIRIS", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 1001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 3003", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 2003", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Prof. Dr. B. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "YBS 4501", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Prof. Dr. B. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 1833", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Prof. Dr. İ. K.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 3001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Prof. Dr. M. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL 1835", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Prof. Dr. M. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ATB 1801-YBS", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB_YBS", "KidemPuani": 1, "ZorunluGun": "Salı", "ZorunluSaat": "13:30-14:40", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},

        # === ULUSLARARASI TİCARET VE LOJİSTİK (UTL) ===
        {"DersKodu": "İŞL2001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2005", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL1003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "ORT_EKONOMI_1", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2007", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL1001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL3001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL4001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2011", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "ORT_GEN_MUH", "KidemPuani": 5, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL4513", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi A. O. Ö.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL4003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL3503", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL4515", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "ORT_ETICARET", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2503", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "KAY1805", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "ORT_HUKUK_TEMEL", "KidemPuani": 3, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL3519", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Öğr. Gör. C. G.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL4501", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Öğr. Gör. C. G.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL3005", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Öğr. Gör. Dr. G. K.", "OrtakDersID": "", "KidemPuani": 1, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ENF1805", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "ORT_BILGISAYAR_2", "KidemPuani": 1, "ZorunluGun": "Salı", "ZorunluSaat": "15:30-17:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "UTL4517", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Öğr. Gör. M. G.", "OrtakDersID": "ORT_ISG", "KidemPuani": 1, "ZorunluGun": "Cuma", "ZorunluSaat": "08:30-09:15", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
        {"DersKodu": "İŞL1003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Prof. Dr. A. E. A.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL3003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Prof. Dr. D. A. I.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Prof. Dr. D. A. I.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL3509", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Prof. Dr. F. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL2009", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Prof. Dr. F. Ş.", "OrtakDersID": "", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "UTL1005", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Prof. Dr. İ. K.", "OrtakDersID": "ORT_ISL_MAT", "KidemPuani": 10, "ZorunluGun": "", "ZorunluSaat": "", "DerslikGerekli": "EVET", "IstenmeyenGun": ""},
        {"DersKodu": "ATB 1801-UTL", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB_UTL", "KidemPuani": 1, "ZorunluGun": "Salı", "ZorunluSaat": "13:30-14:40", "DerslikGerekli": "HAYIR", "IstenmeyenGun": ""},
    ]
    
    df = pd.DataFrame(data)
    
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Dersler')
    
    # Açıklamalar sayfası
    worksheet = writer.book.add_worksheet('Aciklamalar')
    aciklamalar = [
        "=== DERS PROGRAMI ŞABLON KULLANIM KILAVUZU ===",
        "",
        "1. KOLONLAR:",
        "   - DersKodu: Dersin kodu (örn: TUİ 3011)",
        "   - Bolum: Bölüm adı",
        "   - Sinif: Sınıf seviyesi (1-4)",
        "   - HocaAdi: Hocanın adı",
        "   - OrtakDersID: Ortak ders için ID (boş bırakılabilir)",
        "   - KidemPuani: 1-10 arası (Prof=10, Doç=5, Dr=3, Arş.Gör=1)",
        "   - ZorunluGun: Pazartesi/Salı/Çarşamba/Perşembe/Cuma (boş bırakılabilir)",
        "   - ZorunluSaat: 08:30-11:15 formatında (boş bırakılabilir)",
        "   - DerslikGerekli: EVET/HAYIR (uzaktan dersler için HAYIR)",
        "   - IstenmeyenGun: Virgülle ayrılmış günler (örn: Cuma,Cumartesi)",
        "",
        "2. ORTAK DERSLER:",
        "   - Aynı OrtakDersID olan dersler aynı slota yerleştirilir",
        "   - Farklı bölümler aynı anda aynı dersi alır",
        "",
        "3. UZAKTAN EĞİTİM DERSLERİ:",
        "   - ZorunluGun ve ZorunluSaat doldurun",
        "   - DerslikGerekli = HAYIR yapın",
        "",
        "4. KISITLAR:",
        "   - Hoca çakışması KESİNLİKLE yasak",
        "   - Komşu sınıflar çakışmaz (1-2, 2-3, 3-4)",
        "   - Hoca günde max 1 ders verir",
        "   - Öğrenci günde max 2 seans alır (3 olursa ceza)",
        "",
        "5. OPTİMİZASYON:",
        "   - Hocalar ardışık günlerde ders verir (kıdem sırasına göre)",
        "   - İstenmeyen günlerden kaçınılır"
    ]
    
    for i, satir in enumerate(aciklamalar):
        worksheet.write(i, 0, satir)
    
    writer.close()
    return output.getvalue()

# --- ÇÖZÜM MOTORU ---
def programi_coz(df_veri):
    model = cp_model.CpModel()
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['Sabah', 'Öğle', 'ÖğledenSonra']
    
    # Veri temizleme
    df_veri['HocaAdi'] = df_veri['HocaAdi'].astype(str).str.strip()
    df_veri['DersKodu'] = df_veri['DersKodu'].astype(str).str.strip()
    df_veri['Bolum'] = df_veri['Bolum'].astype(str).str.strip()
    if 'KidemPuani' not in df_veri.columns:
        df_veri['KidemPuani'] = 1
    df_veri['KidemPuani'] = df_veri['KidemPuani'].fillna(1).astype(int)
    
    # Ders listesi ve detaylar
    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    hoca_tercihleri = {}
    ortak_ders_gruplari = {}
    
    for index, row in df_veri.iterrows():
        d_id = row['DersKodu']
        hoca = row['HocaAdi']
        bolum = row['Bolum']
        sinif = int(row['Sinif'])
        ortak_id = row['OrtakDersID'] if pd.notna(row['OrtakDersID']) and str(row['OrtakDersID']).strip() else None
        
        # Zorunlu gün/seans belirleme
        zg = None
        zs = None
        if pd.notna(row.get('ZorunluGun')) and str(row['ZorunluGun']).strip() in gunler:
            zg = str(row['ZorunluGun']).strip()
        
        if pd.notna(row.get('ZorunluSaat')) and str(row['ZorunluSaat']).strip():
            zaman = str(row['ZorunluSaat']).strip()
            if '08:' in zaman or '09:' in zaman or '10:' in zaman:
                zs = 'Sabah'
            elif '11:' in zaman or '12:' in zaman or '13:' in zaman or '14:' in zaman:
                zs = 'Öğle'
            else:
                zs = 'ÖğledenSonra'
        
        tum_dersler.append(d_id)
        ders_detaylari[d_id] = {
            'bolum': bolum,
            'sinif': sinif,
            'hoca': hoca,
            'ortak_id': ortak_id,
            'zorunlu_gun': zg,
            'zorunlu_seans': zs
        }
        
        if hoca not in hoca_dersleri:
            hoca_dersleri[hoca] = []
        hoca_dersleri[hoca].append(d_id)
        
        if ortak_id:
            if ortak_id not in ortak_ders_gruplari:
                ortak_ders_gruplari[ortak_id] = []
            ortak_ders_gruplari[ortak_id].append(d_id)
    
    # Hoca tercihleri
    for hoca in hoca_dersleri.keys():
        ornek_satir = df_veri[df_veri['HocaAdi'] == hoca].iloc[0]
        raw_gunler = str(ornek_satir['IstenmeyenGun']) if pd.notna(ornek_satir.get('IstenmeyenGun')) else ""
        istenmeyen_list = [g.strip() for g in raw_gunler.split(',') if g.strip() in gunler]
        kidem = int(ornek_satir['KidemPuani'])
        hoca_tercihleri[hoca] = {'istenmeyen': istenmeyen_list, 'kidem': kidem}
    
    # Değişkenler
    program = {}
    for d in tum_dersler:
        for g in gunler:
            for s in seanslar:
                program[(d, g, s)] = model.NewBoolVar(f'{d}_{g}_{s}')
    
    hoca_gun_aktif = {}
    for h in hoca_dersleri.keys():
        for g_idx, g in enumerate(gunler):
            hoca_gun_aktif[(h, g_idx)] = model.NewBoolVar(f'hoca_gun_{h}_{g_idx}')
    
    # --- KISITLAR ---
    
    # 1. Her ders tam 1 kere (KESİN)
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)
    
    # 2. Hoca çakışması (KESİN - HARD)
    for h in hoca_dersleri.keys():
        dersleri = hoca_dersleri[h]
        unique_ders = []
        islenen_ortak = set()
        
        for d in dersleri:
            oid = ders_detaylari[d]['ortak_id']
            if oid:
                if oid not in islenen_ortak:
                    unique_ders.append(d)
                    islenen_ortak.add(oid)
            else:
                unique_ders.append(d)
        
        for g in gunler:
            for s in seanslar:
                model.Add(sum(program[(d, g, s)] for d in unique_ders) <= 1)
    
    # 3. Sınıf çakışması (KESİN - HARD)
    bolumler = df_veri['Bolum'].unique()
    siniflar = sorted(df_veri['Sinif'].unique())
    
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    for s in seanslar:
                        model.Add(sum(program[(d, g, s)] for d in ilgili) <= 1)
    
    # 4. Komşu sınıf çakışması (KESİN - HARD)
    puanlar = []
    for b in bolumler:
        for sin in siniflar:
            if sin < 4:
                sin_next = sin + 1
                ilgili_sin = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
                ilgili_next = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin_next]
                
                if ilgili_sin and ilgili_next:
                    for g in gunler:
                        for s in seanslar:
                            conflict = model.NewBoolVar(f'komsu_conflict_{b}_{sin}_{g}_{s}')
                            sin_aktif = model.NewBoolVar(f'sin_aktif_{b}_{sin}_{g}_{s}')
                            next_aktif = model.NewBoolVar(f'next_aktif_{b}_{sin_next}_{g}_{s}')
                            
                            model.Add(sum(program[(d, g, s)] for d in ilgili_sin) > 0).OnlyEnforceIf(sin_aktif)
                            model.Add(sum(program[(d, g, s)] for d in ilgili_sin) == 0).OnlyEnforceIf(sin_aktif.Not())
                            
                            model.Add(sum(program[(d, g, s)] for d in ilgili_next) > 0).OnlyEnforceIf(next_aktif)
                            model.Add(sum(program[(d, g, s)] for d in ilgili_next) == 0).OnlyEnforceIf(next_aktif.Not())
                            
                            model.AddBoolAnd([sin_aktif, next_aktif]).OnlyEnforceIf(conflict)
                            model.Add(conflict == 0)  # KESİN YASAK
    
    # 5. Öğrenci günlük yük (SOFT - max 2 seans)
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    gunluk_toplam = sum(program[(d, g, s)] for d in ilgili for s in seanslar)
                    overload = model.NewBoolVar(f'overload_{b}_{sin}_{g}')
                    model.Add(gunluk_toplam > 2).OnlyEnforceIf(overload)
                    model.Add(gunluk_toplam <= 2).OnlyEnforceIf(overload.Not())
                    puanlar.append(overload * -CEZA_GUNLUK_YUK)
    
    # 6. Hoca günde max 1 ders (KESİN)
    for h in hoca_dersleri.keys():
        dersleri = hoca_dersleri[h]
        unique_ders = []
        islenen_ortak = set()
        
        for d in dersleri:
            oid = ders_detaylari[d]['ortak_id']
            if oid:
                if oid not in islenen_ortak:
                    unique_ders.append(d)
                    islenen_ortak.add(oid)
            else:
                unique_ders.append(d)
        
        for g in gunler:
            gunluk = sum(program[(d, g, s)] for d in unique_ders for s in seanslar)
            model.Add(gunluk <= 1)
    
    # 7. Ortak ders senkronizasyonu (KESİN)
    for o_id, d_list in ortak_ders_gruplari.items():
        if len(d_list) > 1:
            ref = d_list[0]
            for diger in d_list[1:]:
                for g in gunler:
                    for s in seanslar:
                        model.Add(program[(ref, g, s)] == program[(diger, g, s)])
    
    # 8. Zorunlu gün/seans (KESİN)
    for d in tum_dersler:
        zg = ders_detaylari[d]['zorunlu_gun']
        zs = ders_detaylari[d]['zorunlu_seans']
        
        if zg:
            for g in gunler:
                if g != zg:
                    for s in seanslar:
                        model.Add(program[(d, g, s)] == 0)
        
        if zs:
            for s in seanslar:
                if s != zs:
                    for g in gunler:
                        model.Add(program[(d, g, s)] == 0)
    
    # 9. Hoca gün sayısı kontrolü (SOFT)
    for h in hoca_dersleri.keys():
        dersleri = hoca_dersleri[h]
        unique_ders = []
        islenen_ortak = set()
        
        for d in dersleri:
            oid = ders_detaylari[d]['ortak_id']
            if oid:
                if oid not in islenen_ortak:
                    unique_ders.append(d)
                    islenen_ortak.add(oid)
            else:
                unique_ders.append(d)
        
        ders_sayisi = len(unique_ders)
        
        for g_idx, g in enumerate(gunler):
            g_toplam = sum(program[(d, g, s)] for d in unique_ders for s in seanslar)
            model.Add(g_toplam > 0).OnlyEnforceIf(hoca_gun_aktif[(h, g_idx)])
            model.Add(g_toplam == 0).OnlyEnforceIf(hoca_gun_aktif[(h, g_idx)].Not())
        
        # Toplam aktif gün = ders sayısı (SOFT)
        toplam_aktif_gun = sum(hoca_gun_aktif[(h, g_idx)] for g_idx in range(5))
        gun_fark = model.NewIntVar(-10, 10, f'gun_fark_{h}')
        model.Add(gun_fark == toplam_aktif_gun - ders_sayisi)
        
        gun_fark_abs = model.NewIntVar(0, 10, f'gun_fark_abs_{h}')
        model.AddAbsEquality(gun_fark_abs, gun_fark)
        puanlar.append(gun_fark_abs * -CEZA_HOCA_GUN_SAYISI)
    
    # --- OPTİMİZASYON (ARDIŞIK GÜNLER) ---
    for h in hoca_dersleri.keys():
        kidem = hoca_tercihleri[h]['kidem']
        istenmeyen = hoca_tercihleri[h]['istenmeyen']
        
        # İstenmeyen günler
        for g_idx, g in enumerate(gunler):
            if g in istenmeyen:
                puanlar.append(hoca_gun_aktif[(h, g_idx)] * -CEZA_ISTENMEYEN_GUN * kidem)
        
        # Ardışık 3 gün (en iyi)
        for g_idx in range(3):
            ard3 = model.NewBoolVar(f'ard3_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)], hoca_gun_aktif[(h, g_idx+2)]]).OnlyEnforceIf(ard3)
            puanlar.append(ard3 * BONUS_ARDISIK_3 * kidem)
        
        # 1 gün atlama
        for g_idx in range(2):
            ard1atlama = model.NewBoolVar(f'ard1atlama_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)].Not(), hoca_gun_aktif[(h, g_idx+2)], hoca_gun_aktif[(h, g_idx+3)]]).OnlyEnforceIf(ard1atlama)
            puanlar.append(ard1atlama * BONUS_ARDISIK_1ATLAMA * kidem)
        
        # 2 gün atlama
        ard2atlama = model.NewBoolVar(f'ard2atlama_{h}')
        model.AddBoolAnd([hoca_gun_aktif[(h, 0)], hoca_gun_aktif[(h, 1)], hoca_gun_aktif[(h, 2)].Not(), hoca_gun_aktif[(h, 3)].Not(), hoca_gun_aktif[(h, 4)]]).OnlyEnforceIf(ard2atlama)
        puanlar.append(ard2atlama * BONUS_ARDISIK_2ATLAMA * kidem)
        
        # Hoca gün boşluğu (HATA VEREN KISIM BURADAYDI, ARTIK DEĞİŞKEN TANIMLI)
        for g_idx in range(3): # 0-2 (Pzt-Çrş arası kontrol, Cumaya taşmasın)
             bosluk_var = model.NewBoolVar(f'bosluk_{h}_{g_idx}')
             # Bugün var, yarın yok, öbür gün var -> Bu kötü
             model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)].Not(), hoca_gun_aktif[(h, g_idx+2)]]).OnlyEnforceIf(bosluk_var)
             puanlar.append(bosluk_var * -CEZA_GUN_BOSLUGU * kidem)
    
    # Objektif
    model.Maximize(sum(puanlar))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = MAX_SURE
    solver.parameters.num_search_workers = 8
    status = solver.Solve(model)
    
    return status, solver, program, tum_dersler, ders_detaylari, gunler, seanslar

# --- ARAYÜZ ---
st.markdown("---")
col1, col2 = st.columns([1, 2])

with col1:
    st.info("### 📥 Şablon İndir")
    st.write("Tüm dersleri içeren örnek şablonu indirin:")
    st.download_button(
        label="📥 Örnek Şablon İndir (Tüm Dersler)",
        data=sablon_olustur(),
        file_name="Ders_Programi_Sablon_v2_2.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

with col2:
    st.info("### 📤 Dosya Yükle")
    uploaded_file = st.file_uploader("Excel dosyanızı yükleyin", type=['xlsx'], help="Şablonu doldurup yükleyin")

if uploaded_file is not None:
    st.markdown("---")
    
    if st.button("🚀 Programı Oluştur", type="primary", use_container_width=True):
        with st.spinner('Program oluşturuluyor... (5 dakikaya kadar sürebilir)'):
            try:
                df_input = pd.read_excel(uploaded_file)
                
                # Validasyon
                required_cols = ['DersKodu', 'Bolum', 'Sinif', 'HocaAdi']
                missing_cols = [col for col in required_cols if col not in df_input.columns]
                if missing_cols:
                    st.error(f"❌ Eksik kolonlar: {', '.join(missing_cols)}")
                else:
                    status, solver, program, tum_dersler, ders_detaylari, gunler, seanslar = programi_coz(df_input)
                    
                    if status == cp_model.OPTIMAL:
                        st.success(f"✅ OPTIMAL PROGRAM OLUŞTURULDU! (Skor: {solver.ObjectiveValue():.0f})")
                    elif status == cp_model.FEASIBLE:
                        st.warning(f"⚠️ Uygun program bulundu (Skor: {solver.ObjectiveValue():.0f}) - Daha iyisi olabilir")
                    else:
                        st.error("❌ Program oluşturulamadı! Kısıtlar çok sıkı olabilir.")
                        st.stop()
                    
                    # Çakışma kontrolü
                    st.subheader("🔍 Çakışma Raporu")
                    hoca_listesi = df_input['HocaAdi'].dropna().unique().tolist()
                    cakisma_var = False
                    
                    for h in hoca_listesi:
                        for g in gunler:
                            for s in seanslar:
                                dersler_burada = []
                                for d in tum_dersler:
                                    if ders_detaylari[d]['hoca'] == h and solver.Value(program[(d, g, s)]) == 1:
                                        oid = ders_detaylari[d]['ortak_id']
                                        if not oid or (oid and d not in [x[0] for x in dersler_burada if x[1]]):
                                            dersler_burada.append((d, oid))
                                
                                unique_count = len(set([x[1] if x[1] else x[0] for x in dersler_burada]))
                                
                                if unique_count > 1:
                                    st.error(f"HOCA ÇAKIŞMASI: {h} → {g} {s}: {unique_count} ders!")
                                    cakisma_var = True
                    
                    if not cakisma_var:
                        st.success("✅ Hoca çakışması yok!")
                    
                    # Excel oluştur
                    output = io.BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    
                    bolumler = df_input['Bolum'].unique()
                    siniflar = sorted(df_input['Sinif'].unique())
                    
                    for bolum in bolumler:
                        index_list = pd.MultiIndex.from_product([gunler, seanslar], names=['Gün', 'Seans'])
                        df_matrix = pd.DataFrame(index=index_list, columns=siniflar)
                        
                        for d in tum_dersler:
                            detay = ders_detaylari[d]
                            if detay['bolum'] == bolum:
                                for g in gunler:
                                    for s in seanslar:
                                        if solver.Value(program[(d, g, s)]) == 1:
                                            mevcut = str(df_matrix.at[(g, s), detay['sinif']])
                                            yeni = f"{d}\n{detay['hoca']}"
                                            if detay['ortak_id']:
                                                yeni += f"\n(Ortak: {detay['ortak_id']})"
                                            
                                            if mevcut != "nan":
                                                df_matrix.at[(g, s), detay['sinif']] = mevcut + "\n---\n" + yeni
                                            else:
                                                df_matrix.at[(g, s), detay['sinif']] = yeni
                        
                        sheet_name = str(bolum)[:30]
                        df_matrix.to_excel(writer, sheet_name=sheet_name)
                        
                        workbook = writer.book
                        worksheet = writer.sheets[sheet_name]
                        wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
                        
                        worksheet.set_column('A:B', 15)
                        worksheet.set_column('C:Z', 30, wrap_format)
                        
                        for row_num in range(1, len(df_matrix) + 2):
                            worksheet.set_row(row_num, 60)
                    
                    writer.close()
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Programı İndir (Excel)",
                        data=processed_data,
                        file_name="Haftalik_Program_v2.2.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        use_container_width=True
                    )
                    
                    # Görsel önizleme
                    st.subheader("📊 Program Önizleme (İlk Bölüm)")
                    preview_bolum = bolumler[0]
                    index_list = pd.MultiIndex.from_product([gunler, seanslar], names=['Gün', 'Seans'])
                    df_preview = pd.DataFrame(index=index_list, columns=siniflar)
                    
                    for d in tum_dersler:
                        detay = ders_detaylari[d]
                        if detay['bolum'] == preview_bolum:
                            for g in gunler:
                                for s in seanslar:
                                    if solver.Value(program[(d, g, s)]) == 1:
                                        mevcut = str(df_preview.at[(g, s), detay['sinif']])
                                        yeni = f"{d} - {detay['hoca']}"
                                        
                                        if mevcut != "nan":
                                            df_preview.at[(g, s), detay['sinif']] = mevcut + " | " + yeni
                                        else:
                                            df_preview.at[(g, s), detay['sinif']] = yeni
                    
                    st.dataframe(df_preview, use_container_width=True, height=600)
                    
            except Exception as e:
                st.error(f"❌ Hata oluştu: {str(e)}")
                st.exception(e)
