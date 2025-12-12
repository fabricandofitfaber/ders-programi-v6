import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter
import random

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V21.0 (Final)", layout="wide")

st.title("🎓 Akademik Ders Programı (V21.0 - Tam Veri & İnatçı Mod)")
st.info("""
Bu sistem, paylaştığınız **gerçek ders verilerini** içerir. 
Sistem 'Hard Constraint' (Katı Kural) prensibiyle çalışır. Çakışmaya izin vermez. 
Çözüm bulana kadar farklı kombinasyonları dener.
""")

# --- PARAMETRELER ---
with st.sidebar:
    st.header("⚙️ Ayarlar")
    MAX_DENEME_SAYISI = st.slider("Maksimum Deneme Sayısı", 10, 100, 20)
    HER_DENEME_SURESI = st.number_input("Her Deneme İçin Süre (Saniye)", value=10)
    st.caption("Not: Eğer çözüm 'Infeasible' çıkıyorsa deneme sayısını değil, Excel'deki kısıtları kontrol edin.")

# --- 1. VERİ SETİ (SİZİN VERDİĞİNİZ TAM LİSTE) ---
def tam_veri_sablonu():
    data = [
        # TURİZM
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "ATB 1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "ENF 1805", "HocaAdi": "Öğr.Gör.Feriha Meral KALAY", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ENF_ISL_TUR"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "İŞL 1825", "HocaAdi": "Doç. Dr. Pelin ARSEZEN", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "İŞL 1803", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_MAT_EKF"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "KAY 1805", "HocaAdi": "Dr.Öğr.Üyesi Sevda YAŞAR COŞKUN", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_HUKUK_TEMEL_UTL"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "İKT 1809", "HocaAdi": "Doç.Dr. Ali Rıza AKTAŞ", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "TUİ 1007", "HocaAdi": "Doç. Dr. Hakan KİRACI", "ZorunluGun": "Cuma", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_MUH_UTL_TUR"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2507", "HocaAdi": "Dr. Öğr. Üyesi Cemal ARTUN", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2503", "HocaAdi": "Prof. Dr. Ayşe ÇELİK YETİM", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2009", "HocaAdi": "Doç.Dr. Ali Naci KARABULUT", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2501", "HocaAdi": "Arş. Gör. Dr. Doğan ÇAPRAK", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2001", "HocaAdi": "Doç. Dr. Onur AKBULUT", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2011", "HocaAdi": "Doç. Dr. Pelin ARSEZEN", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3013", "HocaAdi": "Doç. Dr. Onur AKBULUT", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3011", "HocaAdi": "Arş. Gör. Dr. Doğan ÇAPRAK", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3009", "HocaAdi": "Doç. Dr. Pelin ARSEZEN", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "ORD0080", "HocaAdi": "Doç. Dr. Arzu AKDENİZ", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3509", "HocaAdi": "Prof.Dr. Ayşe ÇELİK YETİM", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "İSG 3901", "HocaAdi": "Öğr.Gör.Mümin GÜMÜŞLÜ", "ZorunluGun": "Cuma", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ISG"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "YDB 3809", "HocaAdi": "Öğr.Gör.İsmail Zeki DİKİCİ", "ZorunluGun": "Cuma", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4539", "HocaAdi": "Arş.Gör.Dr. Doğan ÇAPRAK", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4525", "HocaAdi": "Prof.Dr. Ayşe Çelik YETİM", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4005", "HocaAdi": "Dr. Öğr. Üyesi Cemal ARTUN", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4515", "HocaAdi": "Doç. Dr. Onur AKBULUT", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4533", "HocaAdi": "Doç. Dr. Ali Naci KARABULUT", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_MARKA"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "YDB 4907", "HocaAdi": "Öğr. Gör. Ümit KONAÇ", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "YDB 4821", "HocaAdi": "Öğr.Gör.İsmail Zeki DİKİCİ", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        # EKONOMİ VE FİNANS
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "KAY 1805", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_HUKUK_GENEL"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "ENF 1805", "HocaAdi": "Öğr.Gör.İsmail BAĞCI", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ENF_EKF_UTL"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "ATB 1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "EKF 1003", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_MAT_EKF"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "EKF 1001", "HocaAdi": "Doç. Dr. Ali Rıza AKTAŞ", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_EKONOMI_1"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "İŞL1827", "HocaAdi": "Dr. Öğr. Üyesi Cemal ARTUN", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "İŞL1829", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "ZorunluGun": "Cuma", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_FIN_MUH"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2005", "HocaAdi": "Doç. Dr. Ceren ORAL", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2009", "HocaAdi": "Dr. Öğr. Üyesi Mehmet Ali AKKAYA", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2007", "HocaAdi": "Dr. Öğr. Üyesi Özgül UYAN", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2003", "HocaAdi": "Öğr. Gör. Dr. Nergis ÜNLÜ", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_MAKRO"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "İŞL 2819", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_ISTATISTIK"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2001", "HocaAdi": "Doç. Dr. Aynur YILDIRIM", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "İŞL 3907", "HocaAdi": "Prof. Dr. Faruk ŞAHİN", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_ULUS_ISL"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "İŞL 3901", "HocaAdi": "Dr. Öğr. Üyesi Sevda COŞKUN", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3511", "HocaAdi": "Doç. Dr. Ceren ORAL", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3001", "HocaAdi": "Öğr. Gör. Dr. Nergis ÜNLÜ", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3005", "HocaAdi": "Dr. Öğr. Üyesi Ali Osman ÖZTOP", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3003", "HocaAdi": "Doç. Dr. Aynur YILDIRIM", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "İŞL4911", "HocaAdi": "Doç. Dr. Fatma ÇAKMAK", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4003", "HocaAdi": "Öğr. Gör. Dr. Yahya NAS", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4507", "HocaAdi": "Dr. Öğr. Üyesi Ali Osman ÖZTOP", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4001", "HocaAdi": "Doç. Dr. Aynur YILDIRIM", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4503", "HocaAdi": "Doç. Dr. Ceren ORAL", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF4505", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        # İŞLETME
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İŞL1005", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "ENF1805", "HocaAdi": "Öğr.Gör.Feriha Meral KALAY", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ENF_ISL_TUR"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İŞL1001", "HocaAdi": "Prof. Dr. İlknur KOCA", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ISL_MAT"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "ATB1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ATB_ISL"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "KAY1805", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İKT1801", "HocaAdi": "Öğr. Gör. Dr. Yahya NAS", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_IKT_GIRIS"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İŞL1003", "HocaAdi": "Prof. Dr. Ali Ender ALTUNOĞLU", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2005", "HocaAdi": "Prof. Dr. Recai COŞKUN", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2003", "HocaAdi": "Öğr. Gör. Dr. Hatice CENGER", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2007", "HocaAdi": "Doç. Dr. Ali Naci KARABULUT", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İKT2803", "HocaAdi": "Öğr. Gör. Dr. Nergis ÜNLÜ", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_MAKRO"},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2001", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_ISTATISTIK"},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2009", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "ZorunluGun": "Cuma", "ZorunluSeans": "Sabah", "OrtakDersID": ""},

        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3003", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_SAYISAL"},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3503", "HocaAdi": "Prof. Dr. Recai COŞKUN", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İKT3905", "HocaAdi": "Dr. Öğr. Üyesi Mehmet Ali AKKAYA", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3515", "HocaAdi": "Doç. Dr. Ali Naci KARABULUT", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_MARKA"},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3001", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3005", "HocaAdi": "Öğr. Gör. Dr. Hatice CENGER", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4003", "HocaAdi": "Öğr. Gör. Dr. Hatice CENGER", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4001", "HocaAdi": "Doç. Dr. Fatma ÇAKMAK", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4523", "HocaAdi": "Prof. Dr. Ali Ender ALTUNOĞLU", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4521", "HocaAdi": "Doç. Dr. Fatma ÇAKMAK", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4511", "HocaAdi": "Prof. Dr. Recai COŞKUN", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "ÇEİ4901", "HocaAdi": "Dr. Öğr. Üyesi Mehmet Ali AKKAYA", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        # YBS
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "KAY 1811", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_HUKUK_GENEL"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "ATB 1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "İŞL 1833", "HocaAdi": "Prof.Dr.İlknur KOCA", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "İŞL 1837", "HocaAdi": "Doç.Dr.Muhammet DAMAR", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "YBS 1001", "HocaAdi": "Dr. Öğretim Üyesi İsmail BAĞCI", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "İŞL 1835", "HocaAdi": "Prof. Dr. Mine ŞENEL", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "YBS 2001", "HocaAdi": "Doç.Dr.Muhammet DAMAR", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "YBS 2003", "HocaAdi": "Prof. Dr. Bilgin ŞENEL", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "YBS 2511", "HocaAdi": "Doç. Dr. Muhammer İLKUÇAR", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "İKT 2813", "HocaAdi": "Öğr. Gör. Dr. Yahya NAS", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_IKT_GIRIS"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "İŞL 2827", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "İŞL 2829", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "ZorunluGun": "Cuma", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_FIN_MUH"},

        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "İŞL 3809", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_SAYISAL"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "YBS 3511", "HocaAdi": "Doç. Dr. Evrim ERDOĞAN YAZAR", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "İŞL 3001", "HocaAdi": "Prof. Dr. Mine ŞENEL", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "YBS 3505", "HocaAdi": "Dr.Öğr.Üyesi Murat SAKAL", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "YBS 3003", "HocaAdi": "Dr. Öğretim Üyesi İsmail BAĞCI", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4001", "HocaAdi": "Doç. Dr. Muhammer İLKUÇAR", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4003", "HocaAdi": "Doç.Dr.Muhammet DAMAR", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4005", "HocaAdi": "Prof. Dr. Mine ŞENEL", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4515", "HocaAdi": "Öğr.Gör. Cengiz Gök", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4501", "HocaAdi": "Prof. Dr. Bilgin ŞENEL", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4509", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "ZorunluGun": "Cuma", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ETICARET"},

        # UTL
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "ENF1805", "HocaAdi": "Öğr.Gör.İsmail BAĞCI", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ENF_EKF_UTL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "UTL1005", "HocaAdi": "Prof. Dr. İlknur KOCA", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ISL_MAT"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "ATB1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "İŞL1003", "HocaAdi": "Prof.Dr.Ali Ender ALTUNOĞLU", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "KAY1805", "HocaAdi": "Dr.Öğr.Üyesi Sevda YAŞAR COŞKUN", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_HUKUK_TEMEL_UTL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "UTL1003", "HocaAdi": "Doç. Dr. Ali Rıza AKTAŞ", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_EKONOMI_1"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "UTL1001", "HocaAdi": "Doç.Dr. Evrim ERDOĞAN YAZAR", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2005", "HocaAdi": "Dr.Öğr.Üyesi Ali Rıza AKTAŞ", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2009", "HocaAdi": "Prof. Dr. Faruk ŞAHİN", "ZorunluGun": "Pazartesi", "ZorunluSeans": "Öğle", "OrtakDersID": "ORT_ULUS_ISL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2007", "HocaAdi": "Doç.Dr. Evrim ERDOĞAN YAZAR", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2503", "HocaAdi": "Dr.Öğr.Üyesi Sevda YAŞAR COŞKUN", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2003", "HocaAdi": "Prof. Dr. Derya ATLAY IŞIK", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "İŞL2001", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2011", "HocaAdi": "Doç. Dr. Hakan KİRACI", "ZorunluGun": "Cuma", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_MUH_UTL_TUR"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2001", "HocaAdi": "Doç.Dr. Evrim ERDOĞAN YAZAR", "ZorunluGun": "Cuma", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},

        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3003", "HocaAdi": "Prof. Dr. Derya ATLAY IŞIK", "ZorunluGun": "Pazartesi", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3509", "HocaAdi": "Prof. Dr. Faruk ŞAHİN", "ZorunluGun": "Salı", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3001", "HocaAdi": "Doç. Dr. Hakan KİRACI", "ZorunluGun": "Salı", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3503", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "ZorunluGun": "Çarşamba", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3519", "HocaAdi": "Öğr.Gör.Cengiz GÖK", "ZorunluGun": "Perşembe", "ZorunluSeans": "Sabah", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3005", "HocaAdi": "Öğr.Gör.Dr.Göksel KARTUM", "ZorunluGun": "Cuma", "ZorunluSeans": "Öğle", "OrtakDersID": ""},

        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4003", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "ZorunluGun": "Salı", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4513", "HocaAdi": "Dr. Öğr. Üyesi Ali Osman ÖZTOP", "ZorunluGun": "Çarşamba", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4001", "HocaAdi": "Doç. Dr. Hakan KİRACI", "ZorunluGun": "Perşembe", "ZorunluSeans": "Öğle", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4501", "HocaAdi": "Öğr.Gör.Cengiz GÖK", "ZorunluGun": "Perşembe", "ZorunluSeans": "OgledenSonra", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4517", "HocaAdi": "Öğr.Gör.Mümin GÜMÜŞLÜ", "ZorunluGun": "Cuma", "ZorunluSeans": "Sabah", "OrtakDersID": "ORT_ISG"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4515", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "ZorunluGun": "Cuma", "ZorunluSeans": "OgledenSonra", "OrtakDersID": "ORT_ETICARET"},
    ]
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Dersler')
    writer.close()
    return output.getvalue()

# --- 2. ÇÖZÜCÜ FONKSİYONU ---
def cozucu_calistir(df_veri, deneme_id):
    model = cp_model.CpModel()
    
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['Sabah', 'Öğle', 'OgledenSonra']
    
    # Veri İşleme
    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    bolum_sinif_dersleri = {} 
    ortak_ders_gruplari = {}
    
    for index, row in df_veri.iterrows():
        # Veri temizliği
        d_id = f"{index}_{row['Bolum']}_{row['DersKodu']}" 
        hoca = str(row['HocaAdi']).strip()
        bolum = str(row['Bolum']).strip()
        sinif = str(row['Sinif']).strip()
        
        zg = str(row['ZorunluGun']).strip() if pd.notna(row['ZorunluGun']) and str(row['ZorunluGun']).strip() in gunler else None
        zs = str(row['ZorunluSeans']).strip() if pd.notna(row['ZorunluSeans']) and str(row['ZorunluSeans']).strip() in seanslar else None
        oid = str(row['OrtakDersID']).strip() if pd.notna(row['OrtakDersID']) else None
        
        tum_dersler.append(d_id)
        ders_detaylari[d_id] = {
            'kod': row['DersKodu'],
            'hoca': hoca,
            'bolum': bolum,
            'sinif': sinif,
            'z_gun': zg,
            'z_seans': zs,
            'oid': oid
        }
        
        if hoca not in hoca_dersleri: hoca_dersleri[hoca] = []
        hoca_dersleri[hoca].append(d_id)
        
        bs_key = (bolum, sinif)
        if bs_key not in bolum_sinif_dersleri: bolum_sinif_dersleri[bs_key] = []
        bolum_sinif_dersleri[bs_key].append(d_id)
        
        if oid:
            if oid not in ortak_ders_gruplari: ortak_ders_gruplari[oid] = []
            ortak_ders_gruplari[oid].append(d_id)

    # Değişkenler
    program = {}
    for d in tum_dersler:
        for g in gunler:
            for s in seanslar:
                program[(d, g, s)] = model.NewBoolVar(f'{d}_{g}_{s}')

    # --- KISITLAR (HARD) ---
    
    # 1. Her ders 1 kez
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)

    # 2. Zorunlu Gün/Saat
    for d in tum_dersler:
        detay = ders_detaylari[d]
        if detay['z_gun']:
            for g in gunler:
                if g != detay['z_gun']:
                    for s in seanslar: model.Add(program[(d, g, s)] == 0)
        if detay['z_seans']:
            for s in seanslar:
                if s != detay['z_seans']:
                    for g in gunler: model.Add(program[(d, g, s)] == 0)

    # 3. Hoca Çakışması (Senkronize dersler hariç)
    # Hoca aynı anda 'X' dersi ve 'Y' dersini veriyorsa:
    # Eğer X ve Y'nin OrtakID'si aynıysa bu 1 sayılır.
    # Değilse 2 sayılır (ve yasaklanır).
    for hoca, dersler in hoca_dersleri.items():
        # Hocanın derslerini OrtakID'ye göre grupla
        # { 'ORT_ATB': [d1, d2], 'None_1': [d3], ... }
        hoca_gorevleri = []
        islenen_oidler = set()
        
        for d in dersler:
            oid = ders_detaylari[d]['oid']
            if oid:
                if oid not in islenen_oidler:
                    hoca_gorevleri.append(d) # Temsilci olarak sadece ilkini ekle
                    islenen_oidler.add(oid)
            else:
                hoca_gorevleri.append(d) # OID yoksa her ders ayrı bir görevdir
        
        # Kısıt: Hocanın toplam görevi o saatte <= 1 olmalı
        for g in gunler:
            for s in seanslar:
                model.Add(sum(program[(t, g, s)] for t in hoca_gorevleri) <= 1)

    # 4. Sınıf Çakışması
    for key, dersler in bolum_sinif_dersleri.items():
        for g in gunler:
            for s in seanslar:
                model.Add(sum(program[(d, g, s)] for d in dersler) <= 1)

    # 5. Ortak Ders Senkronizasyonu
    for oid, dlist in ortak_ders_gruplari.items():
        ref = dlist[0]
        for other in dlist[1:]:
            for g in gunler:
                for s in seanslar:
                    model.Add(program[(ref, g, s)] == program[(other, g, s)])

    # Çözücü
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = HER_DENEME_SURESI
    solver.parameters.num_search_workers = 8 
    solver.parameters.random_seed = deneme_id # Kritik Nokta: Her döngüde farklı seed
    
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return True, solver, program, tum_dersler, ders_detaylari
    else:
        return False, None, None, None, None

# --- ARAYÜZ ---
col1, col2 = st.columns([1,2])
with col1:
    st.download_button("📥 Tam Verili Şablonu İndir", tam_veri_sablonu(), "Ders_Listesi_Tam.xlsx")

uploaded_file = st.file_uploader("Excel Dosyasını Yükleyin", type=['xlsx'])

if uploaded_file and st.button("Programı Oluştur"):
    df_input = pd.read_excel(uploaded_file)
    
    basari = False
    cozum = None
    
    pbar = st.progress(0)
    durum = st.empty()
    
    # DÖNGÜ BAŞLIYOR
    for i in range(MAX_DENEME_SAYISI):
        deneme_no = i + 1
        durum.info(f"Deneme {deneme_no}/{MAX_DENEME_SAYISI} - Strateji {random.randint(1000,9999)} uygulanıyor...")
        
        # Her seferinde farklı bir random seed
        seed = random.randint(0, 1000000)
        sonuc, solver, program, tum_dersler, ders_detaylari = cozucu_calistir(df_input, seed)
        
        if sonuc:
            basari = True
            cozum = (solver, program, tum_dersler, ders_detaylari)
            pbar.progress(100)
            durum.success(f"✅ Çözüm {deneme_no}. denemede bulundu!")
            break
        
        pbar.progress(int((deneme_no / MAX_DENEME_SAYISI) * 100))
    
    if basari:
        # Excel Çıktısı Üretme
        solver, program, tum_dersler, ders_detaylari = cozum
        gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        seanslar = ['Sabah', 'Öğle', 'OgledenSonra']
        
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        bolumler = sorted(list(set(d['bolum'] for d in ders_detaylari.values())))
        
        for b in bolumler:
            sheet_name = str(b)[:30]
            # Matris oluştur
            data_map = {s: {g: "" for g in gunler} for s in seanslar}
            
            for d in tum_dersler:
                if ders_detaylari[d]['bolum'] == b:
                    for g in gunler:
                        for s in seanslar:
                            if solver.Value(program[(d, g, s)]) == 1:
                                val = f"{ders_detaylari[d]['kod']}\n{ders_detaylari[d]['hoca']}"
                                if data_map[s][g]:
                                    data_map[s][g] += "\n---\n" + val
                                else:
                                    data_map[s][g] = val
            
            df_out = pd.DataFrame.from_dict(data_map, orient='index')[gunler]
            df_out.to_excel(writer, sheet_name=sheet_name)
            
            # Format
            wb = writer.book
            ws = writer.sheets[sheet_name]
            fmt = wb.add_format({'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1})
            ws.set_column('A:F', 20, fmt)

        writer.close()
        st.balloons()
        st.download_button(
            "📥 Final Ders Programını İndir (XLSX)",
            output.getvalue(),
            "Final_Program_V21.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Çözüm bulunamadı. Lütfen Excel'deki çelişkili 'Zorunlu Gün/Saat' kısıtlarını kontrol edin.")
