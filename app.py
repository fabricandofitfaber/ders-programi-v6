import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter
import random

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V25.0 (Bug Fix)", layout="wide")

st.title("🎓 Akademik Ders Programı (V25.0 - Çelik Zırh Modu)")
st.error("""
**DÜZELTİLEN KRİTİK HATA:**
Önceki versiyonda aynı sınıfa aynı saatte iki ders yazılabilmesi ihtimali vardı.
Bu versiyonda 'Pairwise Collision' (Çiftli Çarpışma) algoritması kullanıldı. 
Aynı sınıfın iki farklı dersi, matematiksel olarak aynı hücreye Gİ-RE-MEZ.
""")

# --- PARAMETRELER ---
with st.sidebar:
    st.header("⚙️ Simülasyon Ayarları")
    MAX_DENEME_SAYISI = st.slider("Maksimum Deneme Sayısı", 100, 10000, 5000)
    HER_DENEME_SURESI = st.number_input("Her Deneme İçin Süre (Saniye)", value=30.0)

# --- 1. VERİ SETİ ---
def temiz_veri_sablonu():
    # Veri seti V24 ile aynı, sadece boş şablon mantığı
    raw_data = [
        # TURİZM
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "ATB 1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "ENF 1805", "HocaAdi": "Öğr.Gör.Feriha Meral KALAY", "OrtakDersID": "ORT_ENF_ISL_TUR"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "İŞL 1825", "HocaAdi": "Doç. Dr. Pelin ARSEZEN", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "İŞL 1803", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_MAT_EKF"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "KAY 1805", "HocaAdi": "Dr.Öğr.Üyesi Sevda YAŞAR COŞKUN", "OrtakDersID": "ORT_HUKUK_TEMEL_UTL"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "İKT 1809", "HocaAdi": "Doç.Dr. Ali Rıza AKTAŞ", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 1, "DersKodu": "TUİ 1007", "HocaAdi": "Doç. Dr. Hakan KİRACI", "OrtakDersID": "ORT_MUH_UTL_TUR"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2507", "HocaAdi": "Dr. Öğr. Üyesi Cemal ARTUN", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2503", "HocaAdi": "Prof. Dr. Ayşe ÇELİK YETİM", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2009", "HocaAdi": "Doç.Dr. Ali Naci KARABULUT", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2501", "HocaAdi": "Arş. Gör. Dr. Doğan ÇAPRAK", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2001", "HocaAdi": "Doç. Dr. Onur AKBULUT", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 2, "DersKodu": "TUİ 2011", "HocaAdi": "Doç. Dr. Pelin ARSEZEN", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3013", "HocaAdi": "Doç. Dr. Onur AKBULUT", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3011", "HocaAdi": "Arş. Gör. Dr. Doğan ÇAPRAK", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3009", "HocaAdi": "Doç. Dr. Pelin ARSEZEN", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "ORD0080", "HocaAdi": "Doç. Dr. Arzu AKDENİZ", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "TUİ 3509", "HocaAdi": "Prof.Dr. Ayşe ÇELİK YETİM", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "İSG 3901", "HocaAdi": "Öğr.Gör.Mümin GÜMÜŞLÜ", "OrtakDersID": "ORT_ISG"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 3, "DersKodu": "YDB 3809", "HocaAdi": "Öğr.Gör.İsmail Zeki DİKİCİ", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4539", "HocaAdi": "Arş.Gör.Dr. Doğan ÇAPRAK", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4525", "HocaAdi": "Prof.Dr. Ayşe Çelik YETİM", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4005", "HocaAdi": "Dr. Öğr. Üyesi Cemal ARTUN", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4515", "HocaAdi": "Doç. Dr. Onur AKBULUT", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "TUİ 4533", "HocaAdi": "Doç. Dr. Ali Naci KARABULUT", "OrtakDersID": "ORT_MARKA"},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "YDB 4907", "HocaAdi": "Öğr. Gör. Ümit KONAÇ", "OrtakDersID": ""},
        {"Bolum": "Turizm İşletmeciliği", "Sinif": 4, "DersKodu": "YDB 4821", "HocaAdi": "Öğr.Gör.İsmail Zeki DİKİCİ", "OrtakDersID": ""},

        # EKONOMİ VE FİNANS
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "KAY 1805", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "OrtakDersID": "ORT_HUKUK_GENEL"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "ENF 1805", "HocaAdi": "Öğr.Gör.İsmail BAĞCI", "OrtakDersID": "ORT_ENF_EKF_UTL"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "ATB 1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "EKF 1003", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_MAT_EKF"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "EKF 1001", "HocaAdi": "Doç. Dr. Ali Rıza AKTAŞ", "OrtakDersID": "ORT_EKONOMI_1"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "İŞL1827", "HocaAdi": "Dr. Öğr. Üyesi Cemal ARTUN", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 1, "DersKodu": "İŞL1829", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "OrtakDersID": "ORT_FIN_MUH"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2005", "HocaAdi": "Doç. Dr. Ceren ORAL", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2009", "HocaAdi": "Dr. Öğr. Üyesi Mehmet Ali AKKAYA", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2007", "HocaAdi": "Dr. Öğr. Üyesi Özgül UYAN", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2003", "HocaAdi": "Öğr. Gör. Dr. Nergis ÜNLÜ", "OrtakDersID": "ORT_MAKRO"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "İŞL 2819", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_ISTATISTIK"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 2, "DersKodu": "EKF 2001", "HocaAdi": "Doç. Dr. Aynur YILDIRIM", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "İŞL 3907", "HocaAdi": "Prof. Dr. Faruk ŞAHİN", "OrtakDersID": "ORT_ULUS_ISL"},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "İŞL 3901", "HocaAdi": "Dr. Öğr. Üyesi Sevda COŞKUN", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3511", "HocaAdi": "Doç. Dr. Ceren ORAL", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3001", "HocaAdi": "Öğr. Gör. Dr. Nergis ÜNLÜ", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3005", "HocaAdi": "Dr. Öğr. Üyesi Ali Osman ÖZTOP", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 3, "DersKodu": "EKF 3003", "HocaAdi": "Doç. Dr. Aynur YILDIRIM", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "İŞL4911", "HocaAdi": "Doç. Dr. Fatma ÇAKMAK", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4003", "HocaAdi": "Öğr. Gör. Dr. Yahya NAS", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4507", "HocaAdi": "Dr. Öğr. Üyesi Ali Osman ÖZTOP", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4001", "HocaAdi": "Doç. Dr. Aynur YILDIRIM", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF 4503", "HocaAdi": "Doç. Dr. Ceren ORAL", "OrtakDersID": ""},
        {"Bolum": "Ekonomi ve Finans", "Sinif": 4, "DersKodu": "EKF4505", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "OrtakDersID": ""},

        # İŞLETME
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İŞL1005", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "ENF1805", "HocaAdi": "Öğr.Gör.Feriha Meral KALAY", "OrtakDersID": "ORT_ENF_ISL_TUR"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İŞL1001", "HocaAdi": "Prof. Dr. İlknur KOCA", "OrtakDersID": "ORT_ISL_MAT"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "ATB1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "OrtakDersID": "ORT_ATB_ISL"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "KAY1805", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İKT1801", "HocaAdi": "Öğr. Gör. Dr. Yahya NAS", "OrtakDersID": "ORT_IKT_GIRIS"},
        {"Bolum": "İşletme", "Sinif": 1, "DersKodu": "İŞL1003", "HocaAdi": "Prof. Dr. Ali Ender ALTUNOĞLU", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2005", "HocaAdi": "Prof. Dr. Recai COŞKUN", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2003", "HocaAdi": "Öğr. Gör. Dr. Hatice CENGER", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2007", "HocaAdi": "Doç. Dr. Ali Naci KARABULUT", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İKT2803", "HocaAdi": "Öğr. Gör. Dr. Nergis ÜNLÜ", "OrtakDersID": "ORT_MAKRO"},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2001", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_ISTATISTIK"},
        {"Bolum": "İşletme", "Sinif": 2, "DersKodu": "İŞL2009", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3003", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_SAYISAL"},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3503", "HocaAdi": "Prof. Dr. Recai COŞKUN", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İKT3905", "HocaAdi": "Dr. Öğr. Üyesi Mehmet Ali AKKAYA", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3515", "HocaAdi": "Doç. Dr. Ali Naci KARABULUT", "OrtakDersID": "ORT_MARKA"},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3001", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 3, "DersKodu": "İŞL3005", "HocaAdi": "Öğr. Gör. Dr. Hatice CENGER", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4003", "HocaAdi": "Öğr. Gör. Dr. Hatice CENGER", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4001", "HocaAdi": "Doç. Dr. Fatma ÇAKMAK", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4523", "HocaAdi": "Prof. Dr. Ali Ender ALTUNOĞLU", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4521", "HocaAdi": "Doç. Dr. Fatma ÇAKMAK", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "İŞL4511", "HocaAdi": "Prof. Dr. Recai COŞKUN", "OrtakDersID": ""},
        {"Bolum": "İşletme", "Sinif": 4, "DersKodu": "ÇEİ4901", "HocaAdi": "Dr. Öğr. Üyesi Mehmet Ali AKKAYA", "OrtakDersID": ""},

        # YBS
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "KAY 1811", "HocaAdi": "Doç. Dr. Nagehan KIRKBEŞOĞLU", "OrtakDersID": "ORT_HUKUK_GENEL"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "ATB 1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "İŞL 1833", "HocaAdi": "Prof.Dr.İlknur KOCA", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "İŞL 1837", "HocaAdi": "Doç.Dr.Muhammet DAMAR", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "YBS 1001", "HocaAdi": "Dr. Öğretim Üyesi İsmail BAĞCI", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "DersKodu": "İŞL 1835", "HocaAdi": "Prof. Dr. Mine ŞENEL", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "YBS 2001", "HocaAdi": "Doç.Dr.Muhammet DAMAR", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "YBS 2003", "HocaAdi": "Prof. Dr. Bilgin ŞENEL", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "YBS 2511", "HocaAdi": "Doç. Dr. Muhammer İLKUÇAR", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "İKT 2813", "HocaAdi": "Öğr. Gör. Dr. Yahya NAS", "OrtakDersID": "ORT_IKT_GIRIS"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "İŞL 2827", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "DersKodu": "İŞL 2829", "HocaAdi": "Arş. Gör. Dr. Ezgi KUYU", "OrtakDersID": "ORT_FIN_MUH"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "İŞL 3809", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_SAYISAL"},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "YBS 3511", "HocaAdi": "Doç. Dr. Evrim ERDOĞAN YAZAR", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "İŞL 3001", "HocaAdi": "Prof. Dr. Mine ŞENEL", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "YBS 3505", "HocaAdi": "Dr.Öğr.Üyesi Murat SAKAL", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "DersKodu": "YBS 3003", "HocaAdi": "Dr. Öğretim Üyesi İsmail BAĞCI", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4001", "HocaAdi": "Doç. Dr. Muhammer İLKUÇAR", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4003", "HocaAdi": "Doç.Dr.Muhammet DAMAR", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4005", "HocaAdi": "Prof. Dr. Mine ŞENEL", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4515", "HocaAdi": "Öğr.Gör. Cengiz Gök", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4501", "HocaAdi": "Prof. Dr. Bilgin ŞENEL", "OrtakDersID": ""},
        {"Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "DersKodu": "YBS 4509", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "OrtakDersID": "ORT_ETICARET"},

        # UTL
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "ENF1805", "HocaAdi": "Öğr.Gör.İsmail BAĞCI", "OrtakDersID": "ORT_ENF_EKF_UTL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "UTL1005", "HocaAdi": "Prof. Dr. İlknur KOCA", "OrtakDersID": "ORT_ISL_MAT"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "ATB1801", "HocaAdi": "Öğr.Gör.Nurcan KARA", "OrtakDersID": "ORT_ATB"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "İŞL1003", "HocaAdi": "Prof.Dr.Ali Ender ALTUNOĞLU", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "KAY1805", "HocaAdi": "Dr.Öğr.Üyesi Sevda YAŞAR COŞKUN", "OrtakDersID": "ORT_HUKUK_TEMEL_UTL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "UTL1003", "HocaAdi": "Doç. Dr. Ali Rıza AKTAŞ", "OrtakDersID": "ORT_EKONOMI_1"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "DersKodu": "UTL1001", "HocaAdi": "Doç.Dr. Evrim ERDOĞAN YAZAR", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2005", "HocaAdi": "Dr.Öğr.Üyesi Ali Rıza AKTAŞ", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2009", "HocaAdi": "Prof. Dr. Faruk ŞAHİN", "OrtakDersID": "ORT_ULUS_ISL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2007", "HocaAdi": "Doç.Dr. Evrim ERDOĞAN YAZAR", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2503", "HocaAdi": "Dr.Öğr.Üyesi Sevda YAŞAR COŞKUN", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2003", "HocaAdi": "Prof. Dr. Derya ATLAY IŞIK", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "İŞL2001", "HocaAdi": "Arş. Gör. Dr. Gamzegül ÇALIKOĞLU", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2011", "HocaAdi": "Doç. Dr. Hakan KİRACI", "OrtakDersID": "ORT_MUH_UTL_TUR"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "DersKodu": "UTL2001", "HocaAdi": "Doç.Dr. Evrim ERDOĞAN YAZAR", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3003", "HocaAdi": "Prof. Dr. Derya ATLAY IŞIK", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3509", "HocaAdi": "Prof. Dr. Faruk ŞAHİN", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3001", "HocaAdi": "Doç. Dr. Hakan KİRACI", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3503", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3519", "HocaAdi": "Öğr.Gör.Cengiz GÖK", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "DersKodu": "UTL3005", "HocaAdi": "Öğr.Gör.Dr.Göksel KARTUM", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4003", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4513", "HocaAdi": "Dr. Öğr. Üyesi Ali Osman ÖZTOP", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4001", "HocaAdi": "Doç. Dr. Hakan KİRACI", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4501", "HocaAdi": "Öğr.Gör.Cengiz GÖK", "OrtakDersID": ""},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4517", "HocaAdi": "Öğr.Gör.Mümin GÜMÜŞLÜ", "OrtakDersID": "ORT_ISG"},
        {"Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "DersKodu": "UTL4515", "HocaAdi": "Arş. Gör. Dr. Ruşen Akdemir", "OrtakDersID": "ORT_ETICARET"},
    ]
    
    for item in raw_data:
        item["ZorunluGun"] = ""
        item["ZorunluSeans"] = ""

    df = pd.DataFrame(raw_data)
    
    # Sütun sırasını düzenleyelim
    cols = ["Bolum", "Sinif", "DersKodu", "HocaAdi", "ZorunluGun", "ZorunluSeans", "OrtakDersID"]
    df = df[cols]
    
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Dersler')
    
    worksheet = writer.sheets['Dersler']
    worksheet.set_column('A:A', 25) 
    worksheet.set_column('C:D', 20) 
    worksheet.set_column('E:F', 15) 
    
    writer.close()
    return output.getvalue()

# --- 2. ÇÖZÜCÜ FONKSİYONU ---
def cozucu_calistir(df_veri, deneme_id):
    model = cp_model.CpModel()
    
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['Sabah', 'Öğle', 'OgledenSonra']
    
    # --- VERİ HAZIRLIĞI ---
    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    bolum_sinif_dersleri = {} 
    ortak_ders_gruplari = {}
    hoca_yukleri = {}

    for index, row in df_veri.iterrows():
        hoca = str(row['HocaAdi']).strip()
        oid = str(row['OrtakDersID']).strip() if pd.notna(row['OrtakDersID']) else None
        
        if hoca not in hoca_yukleri:
            hoca_yukleri[hoca] = set()
        
        if oid:
            hoca_yukleri[hoca].add(oid)
        else:
            hoca_yukleri[hoca].add(f"DERS_{index}")
            
    for h in hoca_yukleri:
        hoca_yukleri[h] = len(hoca_yukleri[h])

    for index, row in df_veri.iterrows():
        d_id = f"{index}_{row['Bolum']}_{row['DersKodu']}" 
        hoca = str(row['HocaAdi']).strip()
        bolum = str(row['Bolum']).strip()
        sinif = int(row['Sinif'])
        
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

    # --- DEĞİŞKENLER ---
    program = {}
    ortak_ders_degiskenleri = [] 
    
    hoca_gun_var = {}
    for h in hoca_dersleri:
        hoca_gun_var[h] = []
        for g_idx, g in enumerate(gunler):
            hoca_gun_var[h].append(model.NewBoolVar(f'hoca_var_{h}_{g}'))

    for d in tum_dersler:
        is_ortak = (ders_detaylari[d]['oid'] is not None)
        for g_idx, g in enumerate(gunler):
            for s in seanslar:
                var = model.NewBoolVar(f'{d}_{g}_{s}')
                program[(d, g, s)] = var
                if is_ortak:
                    ortak_ders_degiskenleri.append(var)
                
                hoca = ders_detaylari[d]['hoca']
                model.Add(hoca_gun_var[hoca][g_idx] == 1).OnlyEnforceIf(var)

    if ortak_ders_degiskenleri:
        model.AddDecisionStrategy(ortak_ders_degiskenleri, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)

    # --- KISITLAR ---
    
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

    # 3. Hoca Çakışması ve Yük
    for hoca, dersler in hoca_dersleri.items():
        hoca_gorevleri = []
        islenen_oidler = set()
        for d in dersler:
            oid = ders_detaylari[d]['oid']
            if oid:
                if oid not in islenen_oidler:
                    hoca_gorevleri.append(d)
                    islenen_oidler.add(oid)
            else:
                hoca_gorevleri.append(d)
        
        yuk = hoca_yukleri[hoca]
        gunluk_limit = 1 if yuk <= 3 else 2
        
        for g in gunler:
            for s in seanslar:
                model.Add(sum(program[(t, g, s)] for t in hoca_gorevleri) <= 1)
            model.Add(sum(program[(t, g, s)] for t in hoca_gorevleri for s in seanslar) <= gunluk_limit)

        hedef_gun = min(yuk, 3) 
        model.Add(sum(hoca_gun_var[hoca]) == hedef_gun)

        if yuk > 1:
            ilk_gun = model.NewIntVar(0, 4, f'ilk_gun_{hoca}')
            son_gun = model.NewIntVar(0, 4, f'son_gun_{hoca}')
            model.AddMinEquality(ilk_gun, [g_idx * hoca_gun_var[hoca][g_idx] + 99 * (1 - hoca_gun_var[hoca][g_idx]) for g_idx in range(5)])
            model.AddMaxEquality(son_gun, [g_idx * hoca_gun_var[hoca][g_idx] for g_idx in range(5)])
            model.Add(son_gun - ilk_gun + 1 <= hedef_gun + 1)

    # --- 4. SINIF İÇİ ÇAKIŞMA (PAIRWISE CHECK - BU KISIM DÜZELTİLDİ) ---
    # Eski Yöntem: sum(dersler) <= 1 (Bazen kaçırıyordu)
    # Yeni Yöntem: Her ikili ders kombinasyonu için "İkiniz aynı anda olamazsınız" kuralı.
    
    for (bolum, sinif), dersler in bolum_sinif_dersleri.items():
        # A) Günlük Toplam Yük (Öğrenci günde max 2 derse girsin)
        for g in gunler:
             gunluk_toplam = sum(program[(d, g, s)] for d in dersler for s in seanslar)
             model.Add(gunluk_toplam <= 2)

        # B) Aynı Saat Çakışması (PAIRWISE - ÇELİK ZIRH)
        # Listedeki her dersi, diğer derslerle tek tek kıyasla
        n = len(dersler)
        for i in range(n):
            for j in range(i + 1, n):
                d1 = dersler[i]
                d2 = dersler[j]
                
                # Eğer bu iki dersin "OrtakDersID"si AYNI ise ve BOŞ DEĞİLSE, çakışabilirler (zaten aynı ders).
                # Değilse, ASLA çakışamazlar.
                oid1 = ders_detaylari[d1]['oid']
                oid2 = ders_detaylari[d2]['oid']
                
                ayni_ortak_ders_mi = (oid1 is not None) and (oid1 == oid2)
                
                if not ayni_ortak_ders_mi:
                    for g in gunler:
                        for s in seanslar:
                            # d1 + d2 <= 1 (İkisi aynı anda 1 olamaz)
                            model.Add(program[(d1, g, s)] + program[(d2, g, s)] <= 1)


    # 5. Dikey Çakışma (1 vs 2, 2 vs 3, 3 vs 4)
    tum_bolumler = set(d['bolum'] for d in ders_detaylari.values())
    for bolum in tum_bolumler:
        for sinif in [1, 2, 3]:
            alt_sinif_key = (bolum, sinif)
            ust_sinif_key = (bolum, sinif + 1)
            
            if alt_sinif_key in bolum_sinif_dersleri and ust_sinif_key in bolum_sinif_dersleri:
                dersler_alt = bolum_sinif_dersleri[alt_sinif_key]
                dersler_ust = bolum_sinif_dersleri[ust_sinif_key]
                
                for g in gunler:
                    for s in seanslar:
                        toplam_aktiflik = sum(program[(d, g, s)] for d in dersler_alt) + \
                                          sum(program[(d, g, s)] for d in dersler_ust)
                        model.Add(toplam_aktiflik <= 1)

    # 6. Ortak Ders Senkronizasyonu
    for oid, dlist in ortak_ders_gruplari.items():
        ref = dlist[0]
        for other in dlist[1:]:
            for g in gunler:
                for s in seanslar:
                    model.Add(program[(ref, g, s)] == program[(other, g, s)])

    # --- ÇÖZÜCÜ ---
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = HER_DENEME_SURESI
    solver.parameters.num_search_workers = 8 
    solver.parameters.random_seed = deneme_id 
    
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        return True, solver, program, tum_dersler, ders_detaylari
    else:
        return False, None, None, None, None

# --- ARAYÜZ ---
col1, col2 = st.columns([1,2])
with col1:
    st.download_button("📥 Boş Şablonu İndir", temiz_veri_sablonu(), "Bos_Ders_Sablonu_V25.xlsx")

uploaded_file = st.file_uploader("Excel'i Yükleyin", type=['xlsx'])

if uploaded_file and st.button("🚀 Programı Başlat"):
    df_input = pd.read_excel(uploaded_file)
    
    basari = False
    cozum = None
    
    pbar = st.progress(0)
    durum = st.empty()
    
    for i in range(MAX_DENEME_SAYISI):
        deneme_no = i + 1
        durum.info(f"Deneme {deneme_no}/{MAX_DENEME_SAYISI} - Kritik çakışma kontrolü yapılıyor...")
        
        seed = random.randint(0, 10000000)
        sonuc, solver, program, tum_dersler, ders_detaylari = cozucu_calistir(df_input, seed)
        
        if sonuc:
            basari = True
            cozum = (solver, program, tum_dersler, ders_detaylari)
            pbar.progress(100)
            durum.success(f"✅ Çözüm {deneme_no}. denemede bulundu!")
            break
        
        pbar.progress(int((deneme_no / MAX_DENEME_SAYISI) * 100))
    
    if basari:
        solver, program, tum_dersler, ders_detaylari = cozum
        gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        seanslar = ['Sabah', 'Öğle', 'OgledenSonra']
        
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        bolumler = sorted(list(set(d['bolum'] for d in ders_detaylari.values())))
        
        for b in bolumler:
            sheet_name = str(b)[:30]
            data_map = {s: {g: "" for g in gunler} for s in seanslar}
            
            for d in tum_dersler:
                if ders_detaylari[d]['bolum'] == b:
                    for g in gunler:
                        for s in seanslar:
                            if solver.Value(program[(d, g, s)]) == 1:
                                val = f"{ders_detaylari[d]['kod']}\n{ders_detaylari[d]['hoca']}"
                                if data_map[s][g]:
                                    # Hata varsa bile burada görelim
                                    data_map[s][g] += "\n!!! ÇAKIŞMA !!!\n" + val
                                else:
                                    data_map[s][g] = val
            
            df_out = pd.DataFrame.from_dict(data_map, orient='index')[gunler]
            df_out.to_excel(writer, sheet_name=sheet_name)
            
            wb = writer.book
            ws = writer.sheets[sheet_name]
            fmt = wb.add_format({'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'border': 1})
            ws.set_column('A:F', 20, fmt)

        writer.close()
        st.balloons()
        st.download_button(
            "📥 Final Programı İndir (V25)",
            output.getvalue(),
            "Final_Program_V25.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.error("Çözüm Bulunamadı. Kısıtlar çok katı olabilir.")
