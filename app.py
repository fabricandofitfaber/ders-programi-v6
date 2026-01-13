import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter
import random
import re

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="Akademik Ders Programı (Signature Edition)", layout="wide")

# --- CSS İLE ŞIK İMZA EKLEME ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Dancing+Script:wght@500&display=swap');
    .signature-container {
        position: fixed;
        bottom: 80px;
        right: 25px;
        z-index: 9999;
        pointer-events: none;
        text-align: right;
    }
    .signature-text {
        font-family: 'Dancing Script', cursive;
        font-size: 28px;
        color: #888888;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.5);
        opacity: 0.7;
        transform: rotate(-5deg);
    }
    .signature-subtext {
         font-family: sans-serif;
         font-size: 10px;
         color: #AAAAAA;
         margin-top: -5px;
         opacity: 0.6;
    }
    </style>
    
    <div class="signature-container">
        <div class="signature-text">AOÖ</div>
        <div class="signature-subtext">Designed with precision</div>
    </div>
""", unsafe_allow_html=True)

st.title("🎓 FİF Akademik Ders Programı Oluşturucu")
st.markdown("""
Bu sistem; **Çakışma Önleme, Hoca Yükü Dengeleme, Alttan Ders Koruması, Akıllı İsim Tanıma ve DERSLİK KAPASİTESİ** özelliklerine sahip tam kapsamlı bir çözümleyicidir.
Sol menüden **'Örnek Şablonu İndir'** diyerek, içinde kullanım rehberi olan Excel dosyasını alabilirsiniz.
""")

# --- YARDIMCI FONKSİYON: İSİM NORMALLEŞTİRME ---
def normalize_name(raw_name):
    if not isinstance(raw_name, str):
        return "BILINMEYEN"
    rep = {"ğ": "G", "Ğ": "G", "ü": "U", "Ü": "U", "ş": "S", "Ş": "S", "ı": "I", "İ": "I", "ö": "O", "Ö": "O", "ç": "C", "Ç": "C"}
    text = raw_name
    for k, v in rep.items():
        text = text.replace(k, v)
    text = text.upper()
    text = re.sub(r'\b(PROF|DOC|DR|ARS|GOR|UYESI|YRD|OGR)\b\.?', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = " ".join(text.split())
    return text

# --- YARDIMCI FONKSİYON: İSTENMEYEN GÜNLERİ PARSE ET ---
def parse_istenmeyen_gunler(gun_str):
    """PZT_CUM veya Pazartesi formatlarını parse eder"""
    if not gun_str:
        return []
    
    gun_str = str(gun_str).strip().upper()
    gunler_tam = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    istenmeyen_gunler = []
    
    # Önce tam gün adı kontrolü (büyük/küçük harf duyarsız)
    for gun in gunler_tam:
        if gun.upper() == gun_str or gun.lower() == gun_str.lower():
            return [gun]  # Tek gün bulundu
    
    # PZT_CUM formatı parse et
    if "PZT" in gun_str:
        istenmeyen_gunler.append("Pazartesi")
    if "SAL" in gun_str:
        istenmeyen_gunler.append("Salı")
    if "CAR" in gun_str or "ÇAR" in gun_str:
        istenmeyen_gunler.append("Çarşamba")
    if "PER" in gun_str:
        istenmeyen_gunler.append("Perşembe")
    if "CUM" in gun_str:
        istenmeyen_gunler.append("Cuma")
    
    return istenmeyen_gunler

# --- PARAMETRELER ---
with st.sidebar:
    st.header("⚙️ Simülasyon Ayarları")
    st.info("Sistem, en zor kısıtlardan başlayarak çözüm arar.")
    
    DERSLIK_KAPASITESI = st.number_input("Okuldaki Toplam Derslik Sayısı", value=10, min_value=1)
    
    # CUMA ÖĞLE KISITI
    st.markdown("---")
    CUMA_OGLE_YASAK = st.checkbox(
        "🕌 Cuma Öğle Seansına Ders Koyma (Cuma Namazı)",
        value=False,
        help="Aktif edilirse Cuma günü 11:30 seansına TÜM BÖLÜMLERDE hiçbir ders konulmaz. Cuma 08:30 ve 14:30 seansları normal çalışır."
    )
    
    # GÜNLÜK LİMİT STRATEJİSİ
    st.markdown("---")
    GUNLUK_LIMIT_STRATEJISI = st.radio(
        "📅 Hoca Günlük Ders Limiti",
        ["Katı (Yük Dağıtımı)", "Esnek (Verimli)"],
        help="Katı: 3 ders ve altı hocalar günde max 1 ders. Esnek: 2 ders aynı gün olabilir."
    )
    
    st.markdown("---")
    MAX_DENEME_SAYISI = st.slider("Seviye Başına Deneme Sayısı", 10, 5000, 50)

# --- 1. VERİ ŞABLONU OLUŞTURUCU ---
def temiz_veri_sablonu():
    raw_data = [
        # --- TURİZM ---
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
        
        # --- EKONOMİ VE FİNANS ---
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
        
        # --- İŞLETME ---
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
        
        # --- YBS ---
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
        
        # --- UTL ---
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
    
    # KOLONLAR
    for item in raw_data:
        if "Unvan" not in item: item["Unvan"] = ""
        if "OzelIstek" not in item: item["OzelIstek"] = ""
        if "ZorunluGun" not in item: item["ZorunluGun"] = ""
        if "ZorunluSeans" not in item: item["ZorunluSeans"] = ""
        if "Istenmeyen Gun" not in item: item["Istenmeyen Gun"] = ""
        if "Istenmeyen Seans" not in item: item["Istenmeyen Seans"] = ""
        if "TekGunSenkron" not in item: item["TekGunSenkron"] = ""
    
    # ÖRNEK VERİ
    if len(raw_data) > 0:
        raw_data[0]["OzelIstek"] = "PZT_SAL"
        raw_data[0]["Istenmeyen Gun"] = "PZT_CUM"  # ✅ Birden fazla istenmeyen gün örneği
    if len(raw_data) > 1:
        raw_data[1]["OzelIstek"] = "ARDISIK_3"
        raw_data[1]["Istenmeyen Seans"] = "08:30"
    if len(raw_data) > 2:
        raw_data[2]["ZorunluGun"] = "Perşembe"
        raw_data[2]["ZorunluSeans"] = "08:30"
        raw_data[2]["TekGunSenkron"] = "EVET"
    
    df_dersler = pd.DataFrame(raw_data)
    cols = ["Bolum", "Sinif", "DersKodu", "HocaAdi", "Unvan", "OzelIstek",
            "ZorunluGun", "ZorunluSeans", "Istenmeyen Gun", "Istenmeyen Seans",
            "TekGunSenkron", "OrtakDersID"]
    df_dersler = df_dersler.reindex(columns=cols)
    
    # REHBER SAYFALARI
    rehber_temel = [
        ["📋 KOLON ADI", "📝 AÇIKLAMA", "✅ KABUL EDİLEN DEĞERLER"],
        ["Bolum", "Bölüm adı (Aynen yazılmalı)", "Turizm İşletmeciliği, İşletme, Ekonomi ve Finans, vb."],
        ["Sinif", "Sınıf seviyesi", "1, 2, 3, 4"],
        ["DersKodu", "Dersin kodu", "İŞL 1001, TUİ 2507, vb."],
        ["HocaAdi", "Hocanın tam adı (unvan dahil)", "Prof. Dr. Ali Yılmaz, Öğr.Gör. Ayşe Kaya"],
        ["Unvan", "Akademik unvan", "Prof. Dr., Doç. Dr., Dr. Öğr. Üyesi, Arş. Gör., Öğr.Gör."],
        ["OrtakDersID", "Farklı bölümlerdeki aynı dersi birleştirir", "ORT_MAT, ORT_YABANCI_DIL"],
    ]
    
    # GÜN YAZIM KURALLARI SAYFASI
    gun_yazim = [
        ["🎯 KOLON", "📖 NE YAZILIR", "✅ DOĞRU ÖRNEK", "❌ YANLIŞ ÖRNEK"],
        ["OzelIstek (İstenen Günler)", "PZT, SAL, CAR, PER, CUM (Alt çizgi ile)", "PZT_SAL (Pazartesi veya Salı)", "Pazartesi_Salı"],
        ["OzelIstek (Birden fazla)", "Alt çizgi ile ayırın", "SAL_CAR_PER (Salı, Çarşamba veya Perşembe)", "Salı Çarşamba"],
        ["OzelIstek (Ardışık)", "ARDISIK_X (X = gün sayısı)", "ARDISIK_3 (3 ardışık gün)", "ARDISIK 3"],
        ["ZorunluGun", "Tam gün adı", "Pazartesi", "PZT"],
        ["ZorunluSeans", "08:30, 11:30, 14:30", "08:30 (Sabah)", "Sabah"],
        ["Istenmeyen Gun", "Tam gün adı VEYA PZT_CUM formatı", "Cuma VEYA PZT_CUM", "Cuma Pazartesi"],
        ["Istenmeyen Seans", "08:30, 11:30, 14:30 (SADECE 1 SAAT!)", "11:30 (Öğle)", "08:30 11:30"],
        ["TekGunSenkron", "EVET veya boş", "EVET", "Evet"],
    ]
    
    # GÜN KISALTMALARI
    gun_kisalt = [
        ["GÜN ADI", "KISALTMA", "KULLANIM YERİ"],
        ["Pazartesi", "PZT", "OzelIstek ve Istenmeyen Gun"],
        ["Salı", "SAL", "OzelIstek ve Istenmeyen Gun"],
        ["Çarşamba", "CAR", "OzelIstek ve Istenmeyen Gun"],
        ["Perşembe", "PER", "OzelIstek ve Istenmeyen Gun"],
        ["Cuma", "CUM", "OzelIstek ve Istenmeyen Gun"],
        ["", "", ""],
        ["TAM GÜN ADLARI", "NE YAZILIR", "KULLANIM YERİ"],
        ["Pazartesi gelmesin", "Pazartesi", "Istenmeyen Gun"],
        ["Salı gelmesin", "Salı", "Istenmeyen Gun"],
        ["Çarşamba gelmesin", "Çarşamba", "Istenmeyen Gun"],
        ["Perşembe gelmesin", "Perşembe", "Istenmeyen Gun"],
        ["Cuma gelmesin", "Cuma", "Istenmeyen Gun"],
        ["Pazartesi VE Cuma gelmesin", "PZT_CUM", "Istenmeyen Gun"],
        ["", "", ""],
        ["SEANS SAATLERİ", "NE YAZILIR", "KULLANIM YERİ"],
        ["Sabah (08:30)", "08:30", "ZorunluSeans veya Istenmeyen Seans"],
        ["Öğle (11:30)", "11:30", "ZorunluSeans veya Istenmeyen Seans"],
        ["Öğleden Sonra (14:30)", "14:30", "ZorunluSeans veya Istenmeyen Seans"],
    ]
    
    # ÖRNEKLER
    ornekler = [
        ["DURUM", "OzelIstek", "ZorunluGun", "ZorunluSeans", "Istenmeyen Gun", "Istenmeyen Seans", "SONUÇ"],
        ["Pazartesi veya Salı istiyor", "PZT_SAL", "", "", "", "", "Sadece Pazartesi VEYA Salı günlerinde olur"],
        ["Cuma gelmesin", "", "", "", "Cuma", "", "Cuma günü hiç ders yok"],
        ["Pazartesi VE Cuma gelmesin", "", "", "", "PZT_CUM", "", "Pazartesi ve Cuma günleri hiç ders yok"],
        ["Sabah istemiyorum", "", "", "", "", "08:30", "Sabah (08:30) hiç ders yok"],
        ["Mutlaka Perşembe Sabah", "", "Perşembe", "08:30", "", "", "⛔ Kesinlikle Perşembe 08:30'da olur"],
        ["Pzt/Sal istiyorum, Cuma istemiyorum", "PZT_SAL", "", "", "Cuma", "", "Pazartesi veya Salı + Cuma'da değil"],
        ["2 dersim tek günde", "", "", "", "", "", "TekGunSenkron: EVET"],
        ["Ardışık 3 gün", "ARDISIK_3", "", "", "", "", "3 ardışık günde olur"],
    ]
    
    df_rehber_temel = pd.DataFrame(rehber_temel[1:], columns=rehber_temel[0])
    df_gun_yazim = pd.DataFrame(gun_yazim[1:], columns=gun_yazim[0])
    df_gun_kisalt = pd.DataFrame(gun_kisalt[1:], columns=gun_kisalt[0])
    df_ornekler = pd.DataFrame(ornekler[1:], columns=ornekler[0])
    
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    
    df_dersler.to_excel(writer, index=False, sheet_name='Dersler')
    df_rehber_temel.to_excel(writer, index=False, sheet_name='1_TEMEL_KULLANIM')
    df_gun_yazim.to_excel(writer, index=False, sheet_name='2_GUN_YAZIM_KURALLARI')
    df_gun_kisalt.to_excel(writer, index=False, sheet_name='3_GUN_KISALTMALARI')
    df_ornekler.to_excel(writer, index=False, sheet_name='4_ORNEKLER')
    
    wb = writer.book
    ws_ders = writer.sheets['Dersler']
    ws_temel = writer.sheets['1_TEMEL_KULLANIM']
    ws_yazim = writer.sheets['2_GUN_YAZIM_KURALLARI']
    ws_kisalt = writer.sheets['3_GUN_KISALTMALARI']
    ws_ornek = writer.sheets['4_ORNEKLER']
    
    fmt_header = wb.add_format({'bold': True, 'bg_color': '#4472C4', 'font_color': 'white', 'text_wrap': True, 'valign': 'top'})
    fmt_wrap = wb.add_format({'text_wrap': True, 'valign': 'top'})
    
    # ✅ FREEZE PANES - BAŞLIK SATIRINI DONDUR
    ws_ders.freeze_panes(1, 0)  # İlk satır (başlıklar) sabit kalacak
    ws_temel.freeze_panes(1, 0)
    ws_yazim.freeze_panes(1, 0)
    ws_kisalt.freeze_panes(1, 0)
    ws_ornek.freeze_panes(1, 0)
    
    ws_ders.set_column('A:D', 20)
    ws_ders.set_column('E:L', 18)
    
    for ws in [ws_temel, ws_yazim, ws_kisalt, ws_ornek]:
        ws.set_row(0, 30, fmt_header)
        ws.set_column('A:G', 25, fmt_wrap)
    
    writer.close()
    return output.getvalue()
    # --- 2. ÇAKIŞMA ANALİZÖRÜ ---
def cakisma_analizi(df_veri, derslik_kapasitesi, cuma_ogle_yasak):
    """Çözüm bulunamazsa hangi kısıtların sorunlu olduğunu tespit eder"""
    
    uyarilar = []
    kritik_sorunlar = []
    
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['08:30', '11:30', '14:30']
    
    # 1. ZORUNLU GÜN ANALİZİ
    zorunlu_gun_sayaci = {g: 0 for g in gunler}
    for _, row in df_veri.iterrows():
        if pd.notna(row.get('ZorunluGun')):
            gun_str = str(row['ZorunluGun']).strip()
            if gun_str in gunler:
                zorunlu_gun_sayaci[gun_str] += 1
    
    for gun, sayi in zorunlu_gun_sayaci.items():
        if sayi > derslik_kapasitesi * 3:
            kritik_sorunlar.append(f"🔴 KRİTİK: {gun} gününe {sayi} ders zorunlu atanmış, ama kapasite {derslik_kapasitesi*3} ders!")
    
    # 2. HOCA İSTEK ÇAKIŞMA ANALİZİ
    hoca_istekleri = {}
    for _, row in df_veri.iterrows():
        hoca = normalize_name(str(row['HocaAdi']))
        if hoca not in hoca_istekleri:
            hoca_istekleri[hoca] = {'real_name': str(row['HocaAdi']), 'istenen': None, 'istenmeyen': []}
        
        if pd.notna(row.get('OzelIstek')):
            hoca_istekleri[hoca]['istenen'] = str(row['OzelIstek']).strip().upper()
        if pd.notna(row.get('Istenmeyen Gun')):
            istenmeyen_gunler = parse_istenmeyen_gunler(str(row['Istenmeyen Gun']))
            hoca_istekleri[hoca]['istenmeyen'] = istenmeyen_gunler
    
    for hoca, bilgi in hoca_istekleri.items():
        if bilgi['istenen'] and bilgi['istenmeyen']:
            istenen_gunler = []
            istek_str = bilgi['istenen']
            if "PZT" in istek_str: istenen_gunler.append("Pazartesi")
            if "SAL" in istek_str: istenen_gunler.append("Salı")
            if "CAR" in istek_str: istenen_gunler.append("Çarşamba")
            if "PER" in istek_str: istenen_gunler.append("Perşembe")
            if "CUM" in istek_str: istenen_gunler.append("Cuma")
            
            # İstenen ve istenmeyen çakışıyor mu?
            cakisan_gunler = set(istenen_gunler) & set(bilgi['istenmeyen'])
            if cakisan_gunler:
                kritik_sorunlar.append(f"🔴 KRİTİK: {bilgi['real_name']} - İstenen günler içinde istenmeyen gün var: {', '.join(cakisan_gunler)}")
    
    # 3. CUMA ÖĞLE ÇAKIŞMASI
    if cuma_ogle_yasak:
        cuma_ogle_zorunlu = 0
        for _, row in df_veri.iterrows():
            zg = str(row.get('ZorunluGun', '')).strip()
            zs = str(row.get('ZorunluSeans', '')).strip()
            if zg == 'Cuma' and zs == '11:30':
                cuma_ogle_zorunlu += 1
        
        if cuma_ogle_zorunlu > 0:
            kritik_sorunlar.append(f"🔴 KRİTİK: {cuma_ogle_zorunlu} ders Cuma 11:30'a zorunlu atanmış ama Cuma Öğle yasak!")
    
    # 4. TEK GÜN SENKRON KONTROLÜ
    for _, row in df_veri.iterrows():
        if pd.notna(row.get('TekGunSenkron')) and str(row['TekGunSenkron']).strip().upper() == 'EVET':
            hoca = normalize_name(str(row['HocaAdi']))
            hoca_ders_sayisi = len(df_veri[df_veri['HocaAdi'].apply(lambda x: normalize_name(str(x))) == hoca])
            if hoca_ders_sayisi != 2:
                uyarilar.append(f"⚠️ {row['HocaAdi']} - TekGunSenkron EVET ama {hoca_ders_sayisi} dersi var (sadece 2 ders için geçerli)")
    
    # 5. DERSLİK KAPASİTESİ
    toplam_ders = len(df_veri)
    if cuma_ogle_yasak:
        max_slot = (5 * 3 - 1) * derslik_kapasitesi  # Cuma öğle hariç
    else:
        max_slot = 5 * 3 * derslik_kapasitesi
    
    if toplam_ders > max_slot * 0.85:
        uyarilar.append(f"⚠️ Derslik kapasitesi sınırda: {toplam_ders} ders, {max_slot} slot (doluluk %{(toplam_ders/max_slot)*100:.0f})")
    
    return kritik_sorunlar, uyarilar

# --- 3. ANA ÇÖZÜCÜ ---
def cozucu_calistir(df_veri, deneme_id, zorluk_seviyesi, derslik_kapasitesi, cuma_ogle_yasak, gunluk_limit_stratejisi):
    model = cp_model.CpModel()
    
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['08:30', '11:30', '14:30']
    
    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    bolum_sinif_dersleri = {}
    ortak_ders_gruplari = {}
    hoca_yukleri = {}
    hoca_bilgileri = {}
    
    # 1. HOCA BİLGİLERİNİ TOPLA
    unique_load_tracker = {}
    for index, row in df_veri.iterrows():
        raw_hoca = str(row['HocaAdi']).strip()
        hoca = normalize_name(raw_hoca)
        
        oid = str(row.get('OrtakDersID', '')).strip() if pd.notna(row.get('OrtakDersID')) and str(row.get('OrtakDersID', '')).strip() else None
        unvan = str(row.get('Unvan', 'OgrGor')).strip() if pd.notna(row.get('Unvan')) else "OgrGor"
        istek = str(row.get('OzelIstek', '')).strip().upper() if pd.notna(row.get('OzelIstek')) else ""
        
        # ✅ İSTENMEYEN GÜNLERİ PARSE ET (BİRDEN FAZLA DESTEĞİ)
        istenmeyen_gunler = []
        if pd.notna(row.get('Istenmeyen Gun')):
            istenmeyen_gunler = parse_istenmeyen_gunler(str(row['Istenmeyen Gun']))
        
        # İSTENMEYEN SEANS
        istenmeyen_seans = None
        if pd.notna(row.get('Istenmeyen Seans')):
            seans_str = str(row['Istenmeyen Seans']).strip()
            if seans_str in seanslar:
                istenmeyen_seans = seans_str
        
        # TEK GÜN SENKRON
        tek_gun_senkron = False
        if pd.notna(row.get('TekGunSenkron')) and str(row['TekGunSenkron']).strip().upper() == 'EVET':
            tek_gun_senkron = True
        
        if hoca not in hoca_bilgileri:
            hoca_bilgileri[hoca] = {
                'unvan': unvan,
                'istek': istek,
                'real_name': raw_hoca,
                'istenmeyen_gunler': istenmeyen_gunler,  # ✅ Liste
                'istenmeyen_seans': istenmeyen_seans,
                'tek_gun_senkron': tek_gun_senkron
            }
        
        if hoca not in unique_load_tracker:
            unique_load_tracker[hoca] = set()
        
        if oid:
            unique_load_tracker[hoca].add(oid)
        else:
            unique_load_tracker[hoca].add(f"UNIQUE_{index}")
    
    hoca_yukleri = {h: len(unique_load_tracker[h]) for h in unique_load_tracker}
    
    # 2. DERSLERİ OLUŞTUR
    for index, row in df_veri.iterrows():
        d_id = f"{index}_{row['Bolum']}_{row['DersKodu']}"
        raw_hoca = str(row['HocaAdi']).strip()
        hoca = normalize_name(raw_hoca)
        bolum = str(row['Bolum']).strip()
        sinif = int(row['Sinif'])
        
        # ZORUNLU GÜN
        zg = None
        if pd.notna(row.get('ZorunluGun')):
            gun_str = str(row['ZorunluGun']).strip()
            if gun_str in gunler:
                zg = gun_str
        
        # ZORUNLU SEANS
        zs = None
        if pd.notna(row.get('ZorunluSeans')):
            seans_str = str(row['ZorunluSeans']).strip()
            if seans_str in seanslar:
                zs = seans_str
        
        oid = str(row.get('OrtakDersID', '')).strip() if pd.notna(row.get('OrtakDersID')) and str(row.get('OrtakDersID', '')).strip() else None
        
        tum_dersler.append(d_id)
        ders_detaylari[d_id] = {
            'kod': row['DersKodu'],
            'hoca_key': hoca,
            'hoca_real': raw_hoca,
            'bolum': bolum,
            'sinif': sinif,
            'z_gun': zg,
            'z_seans': zs,
            'oid': oid
        }
        
        if hoca not in hoca_dersleri:
            hoca_dersleri[hoca] = []
        hoca_dersleri[hoca].append(d_id)
        
        bs_key = (bolum, sinif)
        if bs_key not in bolum_sinif_dersleri:
            bolum_sinif_dersleri[bs_key] = []
        bolum_sinif_dersleri[bs_key].append(d_id)
        
        if oid:
            if oid not in ortak_ders_gruplari:
                ortak_ders_gruplari[oid] = []
            ortak_ders_gruplari[oid].append(d_id)
    
    # --- DEĞİŞKENLER ---
    program = {}
    ortak_ders_degiskenleri = []
    hoca_gun_var = {}
    
    for h in hoca_dersleri:
        hoca_gun_var[h] = []
        for g_idx in range(5):
            hoca_gun_var[h].append(model.NewBoolVar(f'hoca_var_{h}_{g_idx}'))
    
    for d in tum_dersler:
        is_ortak = (ders_detaylari[d]['oid'] is not None)
        for g_idx, g in enumerate(gunler):
            for s in seanslar:
                var = model.NewBoolVar(f'{d}_{g}_{s}')
                program[(d, g, s)] = var
                if is_ortak:
                    ortak_ders_degiskenleri.append(var)
    
    if ortak_ders_degiskenleri:
        model.AddDecisionStrategy(ortak_ders_degiskenleri, cp_model.CHOOSE_FIRST, cp_model.SELECT_MIN_VALUE)
    
    # --- KISITLAR ---
    
    # 1. Her ders 1 kez
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)
    
    # 2. Zorunlu Alanlar
    for d in tum_dersler:
        detay = ders_detaylari[d]
        if detay['z_gun']:
            for g in gunler:
                if g != detay['z_gun']:
                    for s in seanslar:
                        model.Add(program[(d, g, s)] == 0)
        if detay['z_seans']:
            for s in seanslar:
                if s != detay['z_seans']:
                    for g in gunler:
                        model.Add(program[(d, g, s)] == 0)
    
    # 2b. ✅ İSTENMEYEN GÜNLER - DERS SEVİYESİNDE UYGULA (BİRDEN FAZLA GÜN DESTEĞİ)
    for d in tum_dersler:
        hoca = ders_detaylari[d]['hoca_key']
        hoca_info = hoca_bilgileri.get(hoca, {})
        
        # İSTENMEYEN GÜNLER (Liste olarak)
        istenmeyen_gunler = hoca_info.get('istenmeyen_gunler', [])
        for istenmeyen_gun in istenmeyen_gunler:
            for s in seanslar:
                model.Add(program[(d, istenmeyen_gun, s)] == 0)
        
        # İSTENMEYEN SEANS
        if hoca_info.get('istenmeyen_seans'):
            for g in gunler:
                model.Add(program[(d, g, hoca_info['istenmeyen_seans'])] == 0)
    
    # 2c. ✅ CUMA ÖĞLE KISITI - SADECE 11:30 YASAK (08:30 ve 14:30 serbest)
    if cuma_ogle_yasak:
        for d in tum_dersler:
            model.Add(program[(d, 'Cuma', '11:30')] == 0)
    
    # 2d. TEK GÜN SENKRON
    for hoca, dersler in hoca_dersleri.items():
        hoca_info = hoca_bilgileri.get(hoca, {})
        if hoca_info.get('tek_gun_senkron') and hoca_yukleri[hoca] == 2:
            ders1, ders2 = dersler[0], dersler[1]
            
            for g_idx, g in enumerate(gunler):
                ders1_bu_gunde = model.NewBoolVar(f'senkron_{hoca}_{g}_d1')
                ders2_bu_gunde = model.NewBoolVar(f'senkron_{hoca}_{g}_d2')
                
                model.Add(sum(program[(ders1, g, s)] for s in seanslar) == 1).OnlyEnforceIf(ders1_bu_gunde)
                model.Add(sum(program[(ders1, g, s)] for s in seanslar) == 0).OnlyEnforceIf(ders1_bu_gunde.Not())
                
                model.Add(sum(program[(ders2, g, s)] for s in seanslar) == 1).OnlyEnforceIf(ders2_bu_gunde)
                model.Add(sum(program[(ders2, g, s)] for s in seanslar) == 0).OnlyEnforceIf(ders2_bu_gunde.Not())
                
                model.Add(ders1_bu_gunde == ders2_bu_gunde)
            
            for g in gunler:
                ders1_ogle = program[(ders1, g, '11:30')]
                ders2_oglesonra = program[(ders2, g, '14:30')]
                
                model.AddImplication(ders1_ogle, ders2_oglesonra)
                model.AddImplication(ders2_oglesonra, ders1_ogle)
    
    # 3. DERSLİK KAPASİTESİ
    for g in gunler:
        for s in seanslar:
            model.Add(sum(program[(d, g, s)] for d in tum_dersler) <= derslik_kapasitesi)
    
    # 4. Hoca Kısıtları
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
        
        if gunluk_limit_stratejisi == "Esnek (Verimli)":
            gunluk_limit = 2 if yuk <= 3 else 3
        else:
            gunluk_limit = 1 if yuk <= 3 else 2
        
        for g_idx, g in enumerate(gunler):
            gunluk_dersler = [program[(t, g, s)] for t in hoca_gorevleri for s in seanslar]
            
            for s in seanslar:
                model.Add(sum(program[(t, g, s)] for t in hoca_gorevleri) <= 1)
            
            gunluk_toplam = sum(gunluk_dersler)
            model.Add(gunluk_toplam <= gunluk_limit)
            
            model.Add(gunluk_toplam > 0).OnlyEnforceIf(hoca_gun_var[hoca][g_idx])
            model.Add(gunluk_toplam == 0).OnlyEnforceIf(hoca_gun_var[hoca][g_idx].Not())
        
        # GÜN YAYILIMI
        if zorluk_seviyesi <= 2:
            if yuk >= 3:
                model.Add(sum(hoca_gun_var[hoca]) >= 3)
            elif yuk == 2:
                model.Add(sum(hoca_gun_var[hoca]) == 2)
            else:
                model.Add(sum(hoca_gun_var[hoca]) == 1)
        else:
            if yuk >= 4:
                model.Add(sum(hoca_gun_var[hoca]) >= 2)
            else:
                model.Add(sum(hoca_gun_var[hoca]) == yuk)
        
        # İSTEKLER - HOCA SEVİYESİNDE UYGULA
        hoca_info = hoca_bilgileri.get(hoca, {})
        unvan = hoca_info.get('unvan', '')
        istek = hoca_info.get('istek', '')
        
        kural_uygula = False
        if zorluk_seviyesi == 1:
            kural_uygula = True
        elif zorluk_seviyesi == 2:
            if any(u in unvan for u in ["Prof", "Doç", "Doc"]):
                kural_uygula = True
        
        if kural_uygula and istek:
            if "_" in istek and "ARDISIK" not in istek:
                istenilen_gunler = []
                if "PZT" in istek: istenilen_gunler.append(0)
                if "SAL" in istek: istenilen_gunler.append(1)
                if "CAR" in istek: istenilen_gunler.append(2)
                if "PER" in istek: istenilen_gunler.append(3)
                if "CUM" in istek: istenilen_gunler.append(4)
                
                for g_idx in range(5):
                    if g_idx not in istenilen_gunler:
                        model.Add(hoca_gun_var[hoca][g_idx] == 0)
            
            elif "ARDISIK" in istek and yuk > 1:
                ilk = model.NewIntVar(0, 4, f'ilk_{hoca}')
                son = model.NewIntVar(0, 4, f'son_{hoca}')
                model.AddMinEquality(ilk, [g * hoca_gun_var[hoca][g] + 99 * (1 - hoca_gun_var[hoca][g]) for g in range(5)])
                model.AddMaxEquality(son, [g * hoca_gun_var[hoca][g] for g in range(5)])
                model.Add(son - ilk + 1 == sum(hoca_gun_var[hoca]))
        else:
            if yuk > 1:
                ilk = model.NewIntVar(0, 4, f'ilk_std_{hoca}')
                son = model.NewIntVar(0, 4, f'son_std_{hoca}')
                model.AddMinEquality(ilk, [g * hoca_gun_var[hoca][g] + 99 * (1 - hoca_gun_var[hoca][g]) for g in range(5)])
                model.AddMaxEquality(son, [g * hoca_gun_var[hoca][g] for g in range(5)])
                model.Add(son - ilk + 1 <= 4)
    
    # 5. Sınıf Çakışma
    for (bolum, sinif), dersler in bolum_sinif_dersleri.items():
        for g in gunler:
            gunluk_toplam = sum(program[(d, g, s)] for d in dersler for s in seanslar)
            model.Add(gunluk_toplam <= 2)
        
        n = len(dersler)
        for i in range(n):
            for j in range(i + 1, n):
                d1 = dersler[i]
                d2 = dersler[j]
                oid1 = ders_detaylari[d1]['oid']
                oid2 = ders_detaylari[d2]['oid']
                
                if not ((oid1 is not None) and (oid1 == oid2)):
                    for g in gunler:
                        for s in seanslar:
                            model.Add(program[(d1, g, s)] + program[(d2, g, s)] <= 1)
    
    # 6. Dikey Çakışma
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
                        top = sum(program[(d, g, s)] for d in dersler_alt) + sum(program[(d, g, s)] for d in dersler_ust)
                        model.Add(top <= 1)
    
    # 7. Ortak Ders
    for oid, dlist in ortak_ders_gruplari.items():
        ref = dlist[0]
        for other in dlist[1:]:
            for g in gunler:
                for s in seanslar:
                    model.Add(program[(ref, g, s)] == program[(other, g, s)])
    
    # SOLVER
    solver = cp_model.CpSolver()
    timeout = 30 if deneme_id % 50 < 10 else (60 if deneme_id % 50 < 30 else 120)
    solver.parameters.max_time_in_seconds = timeout
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
    st.download_button("📥 Örnek Şablonu İndir", temiz_veri_sablonu(), "Ornek_Sablon_Final.xlsx")

uploaded_file = st.file_uploader("Excel Yükle", type=['xlsx'])

if uploaded_file and st.button("🚀 Programı Hesapla"):
    df_input = pd.read_excel(uploaded_file, sheet_name='Dersler')
    
    st.info("🔍 Veri analiz ediliyor...")
    kritik_sorunlar, uyarilar = cakisma_analizi(df_input, DERSLIK_KAPASITESI, CUMA_OGLE_YASAK)
    
    if kritik_sorunlar:
        st.error("### ⛔ KRİTİK SORUNLAR TESPİT EDİLDİ!")
        for sorun in kritik_sorunlar:
            st.error(sorun)
        st.warning("⚠️ Bu sorunlar çözülmeden program oluşturulamaz. Excel dosyasını düzeltin ve tekrar deneyin.")
        st.stop()
    
    if uyarilar:
        st.warning("### ⚠️ UYARILAR:")
        for uyari in uyarilar:
            st.warning(uyari)
    
    final_cozum = None
    basari_seviyesi = ""
    
    seviyeler = [
        (1, "🥇 ALTIN MOD (Tüm İstekler)"),
        (2, "🥈 GÜMÜŞ MOD (Sadece Prof/Doç)"),
        (3, "🥉 BRONZ MOD (Kurallar Esnetildi)")
    ]
    
    pbar = st.progress(0)
    status_text = st.empty()
    
    for sev_id, sev_ad in seviyeler:
        status_text.markdown(f"### {sev_ad} deneniyor...")
        bulundu = False
        
        for i in range(MAX_DENEME_SAYISI):
            seed = random.randint(0, 1000000)
            sonuc, solver, program, tum_dersler, ders_detaylari = cozucu_calistir(
                df_input, seed, sev_id, DERSLIK_KAPASITESI, CUMA_OGLE_YASAK, GUNLUK_LIMIT_STRATEJISI
            )
            
            if sonuc:
                final_cozum = (solver, program, tum_dersler, ders_detaylari)
                basari_seviyesi = sev_ad
                bulundu = True
                break
            
            base_prog = (sev_id - 1) * 0.33
            step_prog = (i / MAX_DENEME_SAYISI) * 0.33
            pbar.progress(min(base_prog + step_prog, 1.0))
        
        if bulundu:
            break
    
    if final_cozum:
        st.success(f"✅ Çözüm Bulundu! Kullanılan Seviye: **{basari_seviyesi}**")
        solver, program, tum_dersler, ders_detaylari = final_cozum
        
        gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
        seanslar = ['08:30', '11:30', '14:30']
        seans_display = {
            '08:30': 'Sabah (08:30)',
            '11:30': 'Öğle (11:30)',
            '14:30': 'Öğleden Sonra (14:30)'
        }
        
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        bolumler = sorted(list(set(d['bolum'] for d in ders_detaylari.values())))
        
        for b in bolumler:
            sheet_name = str(b)[:30]
            data_map = {s: {g: {1:"", 2:"", 3:"", 4:""} for g in gunler} for s in seanslar}
            
            for d in tum_dersler:
                if ders_detaylari[d]['bolum'] == b:
                    sinif = ders_detaylari[d]['sinif']
                    for g in gunler:
                        for s in seanslar:
                            if solver.Value(program[(d, g, s)]) == 1:
                                val = f"{ders_detaylari[d]['kod']}\n{ders_detaylari[d]['hoca_real']}"
                                if data_map[s][g][sinif]:
                                    data_map[s][g][sinif] += "\n!!! HATA !!!\n" + val
                                else:
                                    data_map[s][g][sinif] = val
            
            rows_list = []
            for g in gunler:
                for s in seanslar:
                    row = {"Gün": g, "Seans": seans_display[s]}
                    for snf in [1, 2, 3, 4]:
                        row[f"{snf}. Sınıf"] = data_map[s][g][snf]
                    rows_list.append(row)
            
            df_out = pd.DataFrame(rows_list)
            df_out.to_excel(writer, sheet_name=sheet_name, index=False)
            
            wb = writer.book
            ws = writer.sheets[sheet_name]
            
            fmt_header = wb.add_format({'bold': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#D9D9D9'})
            fmt_white = wb.add_format({'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#FFFFFF'})
            fmt_gray = wb.add_format({'text_wrap': True, 'align': 'center', 'valign': 'vcenter', 'border': 1, 'bg_color': '#F2F2F2'})
            
            # ✅ FREEZE PANES - ÇIKTI DOSYASINDA DA BAŞLIK SABİT
            ws.freeze_panes(1, 0)
            
            ws.set_column('A:B', 18)
            ws.set_column('C:F', 25)
            
            headers = ["Gün", "Seans", "1. Sınıf", "2. Sınıf", "3. Sınıf", "4. Sınıf"]
            for col_num, val in enumerate(headers):
                ws.write(0, col_num, val, fmt_header)
            
            for r_idx, row_data in df_out.iterrows():
                day_idx = r_idx // 3
                current_fmt = fmt_white if day_idx % 2 == 0 else fmt_gray
                
                excel_row = r_idx + 1
                ws.write(excel_row, 0, row_data["Gün"], current_fmt)
                ws.write(excel_row, 1, row_data["Seans"], current_fmt)
                ws.write(excel_row, 2, row_data["1. Sınıf"], current_fmt)
                ws.write(excel_row, 3, row_data["2. Sınıf"], current_fmt)
                ws.write(excel_row, 4, row_data["3. Sınıf"], current_fmt)
                ws.write(excel_row, 5, row_data["4. Sınıf"], current_fmt)
        
        writer.close()
        st.balloons()
        st.download_button("📥 Final Programı İndir", output.getvalue(), "Akilli_Program_Final.xlsx")
    else:
        st.error("❌ Çözüm Bulunamadı. Detaylı Analiz:")
        
        st.markdown("### 📊 Sorun Giderme Önerileri (Öncelik Sırasına Göre)")
        
        st.markdown(f"""
        #### 1️⃣ **EN ÖNCELİKLİ: Zorunlu Kısıtları Azaltın**
        - ⛔ **Zorunlu Gün** sayısını azaltın
        - ⛔ **Zorunlu Seans** sayısını azaltın
        - ✅ Öneri: Zorunlu yerine "İstenen Gün" kullanın
        
        #### 2️⃣ **İkinci Öncelik: İstenmeyen Kısıtları Gevşetin**
        - ⚠️ "Istenmeyen Gun" olan hocaların sayısını azaltın
        
        #### 3️⃣ **Üçüncü Öncelik: Derslik Kapasitesini Artırın**
        - 📐 Şu anki: **{DERSLIK_KAPASITESI}** → Önerilen: **{DERSLIK_KAPASITESI + 2}**
        
        #### 4️⃣ **Dördüncü Öncelik: Günlük Limit Stratejisini Değiştirin**
        - 🔄 Sidebar'dan "Esnek (Verimli)" moduna geçin
        
        #### 5️⃣ **Beşinci Öncelik: ARDISIK_X Değerini Düşürün**
        - 📅 ARDISIK_4 → ARDISIK_3 yapın
        
        #### 6️⃣ **Son Çare: Cuma Öğle Yasağını Kaldırın**
        - 🕌 Eğer aktifse, Sidebar'dan kapatın
        """)
        
        st.info(f"💡 Program **{seviyeler[-1][1]}** seviyesine kadar denedi ama çözüm bulamadı.")
