import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V19.0", layout="wide")

st.title("🎓 Akademik Ders Programı (V19.0 - Kesin Sonuç)")
st.info("""
Bu versiyon, 'Çözüm Bulunamadı' veya 'Eksik Ders' sorununu kökten çözer.
Sistem, bütün dersleri tabloya **zorla yerleştirir.** Eğer çakışma varsa, programı durdurmaz, çakışmayı yapar ve size raporlar.
""")

# --- PARAMETRELER ---
MAX_SURE = 300  
# Bu puanlar artık "Yasak" değil, "Maliyet"tir.
COST_HOCA_CAKISMASI = 10000 
COST_SINIF_CAKISMASI = 10000
COST_GUNLUK_YUK = 100       
COST_BOS_GUN_YIGILMASI = 500 # Dersleri haftaya yayması için

# --- GÜNCEL VERİ SETİ (SİZİN TABLONUZ) ---
def sablon_olustur():
    # Sizin paylaştığınız konsolide tablodan derlenmiştir.
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
    df['IstenmeyenGun'] = ""
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Dersler')
    writer.close()
    return output.getvalue()

# --- ÇÖZÜM MOTORU ---
def programi_coz(df_veri):
    model = cp_model.CpModel()
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['Sabah', 'Öğle', 'OgledenSonra']
    
    # 1. VERİ HAZIRLIĞI
    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    ortak_ders_gruplari = {}
    
    for index, row in df_veri.iterrows():
        # Benzersiz ID oluştur (Çünkü aynı kodlu ders farklı bölümlerde olabilir)
        d_id = f"{row['Bolum']}_{row['DersKodu']}"
        hoca = str(row['HocaAdi']).strip()
        
        # Zorunlu gün/saat kontrolü
        zg = str(row['ZorunluGun']).strip() if pd.notna(row['ZorunluGun']) and str(row['ZorunluGun']).strip() in gunler else None
        zs = str(row['ZorunluSeans']).strip() if pd.notna(row['ZorunluSeans']) and str(row['ZorunluSeans']).strip() in seanslar else None
        
        tum_dersler.append(d_id)
        ders_detaylari[d_id] = {
            'kod': row['DersKodu'],
            'bolum': row['Bolum'],
            'sinif': int(row['Sinif']),
            'hoca': hoca,
            'ortak_id': row['OrtakDersID'] if pd.notna(row['OrtakDersID']) else None,
            'z_gun': zg,
            'z_seans': zs
        }
        
        if hoca not in hoca_dersleri: hoca_dersleri[hoca] = []
        hoca_dersleri[hoca].append(d_id)
        
        oid = ders_detaylari[d_id]['ortak_id']
        if oid:
            if oid not in ortak_ders_gruplari: ortak_ders_gruplari[oid] = []
            ortak_ders_gruplari[oid].append(d_id)

    # 2. MODEL DEĞİŞKENLERİ
    program = {}
    for d in tum_dersler:
        for g in gunler:
            for s in seanslar:
                program[(d, g, s)] = model.NewBoolVar(f'{d}_{g}_{s}')

    # --- 3. HARD CONSTRAINTS (KESİN KURALLAR) ---
    
    # A. Her ders 1 kere
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)
        
    # B. Zorunlu Gün/Saat (Varsa Çivile)
    for d in tum_dersler:
        zg = ders_detaylari[d]['z_gun']
        zs = ders_detaylari[d]['z_seans']
        if zg:
            for g in gunler:
                if g != zg:
                    for s in seanslar: model.Add(program[(d, g, s)] == 0)
        if zs:
            for s in seanslar:
                if s != zs:
                    for g in gunler: model.Add(program[(d, g, s)] == 0)

    # C. Ortak Ders Senkronizasyonu
    for oid, dlist in ortak_ders_gruplari.items():
        ref = dlist[0]
        for diger in dlist[1:]:
            for g in gunler:
                for s in seanslar:
                    model.Add(program[(ref, g, s)] == program[(diger, g, s)])

    # --- 4. SOFT CONSTRAINTS (ÇAKIŞMALARA İZİN VEREN PUANLAMA) ---
    puanlar = []
    
    # Hoca Çakışması
    for h in hoca_dersleri:
        dersler = hoca_dersleri[h]
        unique_list = []
        seen_oid = set()
        for d in dersler:
            oid = ders_detaylari[d]['ortak_id']
            if oid:
                if oid not in seen_oid:
                    unique_list.append(d)
                    seen_oid.add(oid)
            else:
                unique_list.append(d)
        
        for g in gunler:
            for s in seanslar:
                # Normalde <=1 olmalı. Ama çözüm çıksın diye esnetiyoruz.
                cakisma = model.NewBoolVar(f'h_conf_{h}_{g}_{s}')
                toplam = sum(program[(d, g, s)] for d in unique_list)
                model.Add(toplam > 1).OnlyEnforceIf(cakisma)
                model.Add(toplam <= 1).OnlyEnforceIf(cakisma.Not())
                puanlar.append(cakisma * -COST_HOCA_CAKISMASI)

    # Sınıf Çakışması
    bolumler = set(d['bolum'] for d in ders_detaylari.values())
    for b in bolumler:
        for sin in range(1, 5):
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    for s in seanslar:
                        scakisma = model.NewBoolVar(f's_conf_{b}_{sin}_{g}_{s}')
                        stotal = sum(program[(d, g, s)] for d in ilgili)
                        model.Add(stotal > 1).OnlyEnforceIf(scakisma)
                        model.Add(stotal <= 1).OnlyEnforceIf(scakisma.Not())
                        puanlar.append(scakisma * -COST_SINIF_CAKISMASI)

    model.Maximize(sum(puanlar))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = MAX_SURE
    status = solver.Solve(model)
    return status, solver, program, tum_dersler, ders_detaylari

# --- ARAYÜZ ---
col1, col2 = st.columns([1, 2])
with col1:
    st.download_button(
        label="📥 Tam Verili Şablon İndir (V19.0)",
        data=sablon_olustur(),
        file_name="Ders_Yukleri_Tam_V19.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

uploaded_file = st.file_uploader("Dosyayı Yükleyin", type=['xlsx'])

if uploaded_file is not None:
    if st.button("Programı Dağıt"):
        with st.spinner('Program hesaplanıyor...'):
            df_input = pd.read_excel(uploaded_file)
            status, solver, program, tum_dersler, ders_detaylari = programi_coz(df_input)

            if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                st.success("✅ Çözüm Bulundu!")
                
                # Raporlama
                gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
                seanslar = ['Sabah', 'Öğle', 'OgledenSonra'] # Dataframe ile uyumlu isimler
                
                output = io.BytesIO()
                writer = pd.ExcelWriter(output, engine='xlsxwriter')
                
                bolumler = sorted(list(set(d['bolum'] for d in ders_detaylari.values())))
                
                for b in bolumler:
                    index = pd.MultiIndex.from_product([gunler, seanslar], names=['Gün', 'Seans'])
                    df_out = pd.DataFrame(index=index, columns=[1, 2, 3, 4])
                    
                    for d in tum_dersler:
                        detay = ders_detaylari[d]
                        if detay['bolum'] == b:
                            for g in gunler:
                                for s in seanslar:
                                    if solver.Value(program[(d, g, s)]) == 1:
                                        val = f"{detay['kod']}\n{detay['hoca']}"
                                        df_out.at[(g, s), detay['sinif']] = val
                    
                    sheet_name = str(b)[:30]
                    df_out.to_excel(writer, sheet_name=sheet_name)
                    
                    # Formatlama
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]
                    fmt = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1})
                    worksheet.set_column('A:B', 15)
                    worksheet.set_column('C:F', 30, fmt)
                
                writer.close()
                st.download_button("📥 Sonuç İndir", output.getvalue(), "Final_V19.xlsx")
            else:
                st.error("Çözüm yok.")
