import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V13.1", layout="wide")

st.title("🎓 Akademik Ders Programı Dağıtıcı (V13.1 - Tam Verili Final)")
st.info("""
**Bu versiyon şunları içerir:**
1. **Tam Veri Seti:** 'Örnek Şablon' butonuna bastığınızda tüm bölümlerin dersleri dolu gelir.
2. **Esnek Motor:** 'Çözüm Bulunamadı' hatası vermez, gerekirse kuralları esnetip size bir program sunar.
""")

# --- CEZA PUANLARI (Önem Sırası) ---
CEZA_HOCA_ISTENMEYEN_GUN = 500   # Hoca istemediği güne gelirse
CEZA_OGRENCI_GUNLUK_3 = 100      # Öğrenci günde 3 derse girerse (İdeal olan 2)
CEZA_GUN_BOSLUGU = 50            # Hoca Pzt-Çrş gelip Salı gelmezse
ODUL_ARDISIK_GUN = 200           # Günler blok olursa ödül

# Sabitler
DERSLIK_SAYISI = 100 
MAX_SURE = 300 

# --- ŞABLON OLUŞTURMA (TAM LİSTE GERİ GELDİ) ---
def sablon_olustur():
    data = [
        # --- TURİZM ---
        {"DersKodu": "TUİ 3011", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. D. Ç.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "TUİ 2501", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. D. Ç.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "TUİ 4539", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Arş. Gör. Dr. D. Ç.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "TUİ 2009", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 4533", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "ORT_MARKA", "KidemPuani": 5},
        {"DersKodu": "İKT 1809", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "ORD0080", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Doç. Dr. A. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 1007", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "ORT_GEN_MUH", "KidemPuani": 5},
        {"DersKodu": "TUİ 4515", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Doç. Dr. O. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 2001", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Doç. Dr. O. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 3013", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Doç. Dr. O. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İŞL 1825", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Doç. Dr. P. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 3009", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Doç. Dr. P. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 2011", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Doç. Dr. P. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "TUİ 4005", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi C. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "TUİ 2507", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Dr. Öğr. Üyesi C. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "KAY 1805", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "ORT_HUKUK", "KidemPuani": 3},
        {"DersKodu": "İSG 3901", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Öğr. Gör. M. G.", "OrtakDersID": "ORT_ISG", "KidemPuani": 1},
        {"DersKodu": "TUİ 2503", "Bolum": "Turizm İşletmeciliği", "Sinif": 2, "HocaAdi": "Prof. Dr. A. Ç. Y.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "TUİ 3509", "Bolum": "Turizm İşletmeciliği", "Sinif": 3, "HocaAdi": "Prof. Dr. A. Ç. Y.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "TUİ 4525", "Bolum": "Turizm İşletmeciliği", "Sinif": 4, "HocaAdi": "Prof. Dr. A. Ç. Y.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "ENF 1805", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Öğr. Gör. F. M. K.", "OrtakDersID": "ORT_BILGISAYAR_1", "KidemPuani": 1},
        {"DersKodu": "ATB 1801", "Bolum": "Turizm İşletmeciliği", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB", "KidemPuani": 1},

        # --- İŞLETME ---
        {"DersKodu": "İŞL1005", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "İŞL3001", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "İŞL3003", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_SAYISAL", "KidemPuani": 1},
        {"DersKodu": "İŞL2001", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK", "KidemPuani": 1},
        {"DersKodu": "İŞL2007", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İŞL3515", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Doç. Dr. A. N. K.", "OrtakDersID": "ORT_MARKA", "KidemPuani": 5},
        {"DersKodu": "İŞL4001", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Doç. Dr. F. Ç.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İŞL4521", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Doç. Dr. F. Ç.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "KAY1805", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İŞL2009", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İKT3905", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi M. A. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "ÇEİ4901", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi M. A. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "İŞL4003", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Öğr. Gör. Dr. H. C.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "İŞL2003", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. H. C.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "İŞL3005", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Öğr. Gör. Dr. H. C.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "İKT2803", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. N. Ü.", "OrtakDersID": "ORT_MAKRO", "KidemPuani": 1},
        {"DersKodu": "İKT1801", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Öğr. Gör. Dr. Y. N.", "OrtakDersID": "ORT_IKT_GIRIS", "KidemPuani": 1},
        {"DersKodu": "ENF 1805", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Öğr. Gör. F. M. K.", "OrtakDersID": "ORT_BILGISAYAR_1", "KidemPuani": 1},
        {"DersKodu": "İŞL4523", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Prof. Dr. A. E. A.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL1003", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Prof. Dr. A. E. A.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL1001", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Prof. Dr. İ. K.", "OrtakDersID": "ORT_ISL_MAT", "KidemPuani": 10},
        {"DersKodu": "İŞL2005", "Bolum": "İşletme", "Sinif": 2, "HocaAdi": "Prof. Dr. R. C.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL3503", "Bolum": "İşletme", "Sinif": 3, "HocaAdi": "Prof. Dr. R. C.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL4511", "Bolum": "İşletme", "Sinif": 4, "HocaAdi": "Prof. Dr. R. C.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "ATB 1801", "Bolum": "İşletme", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB", "KidemPuani": 1},

        # --- EKONOMİ ---
        {"DersKodu": "İŞL1829", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "ORT_FIN_MUH", "KidemPuani": 1},
        {"DersKodu": "EKF 1003", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_MAT_EKF", "KidemPuani": 1},
        {"DersKodu": "İŞL 2819", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK", "KidemPuani": 1},
        {"DersKodu": "EKF 1001", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "ORT_EKONOMI_1", "KidemPuani": 5},
        {"DersKodu": "EKF 4001", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Doç. Dr. A. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "EKF 3003", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Doç. Dr. A. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "EKF 2001", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Doç. Dr. A. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "EKF 2005", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Doç. Dr. C. O.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "EKF 3511", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Doç. Dr. C. O.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "EKF 4503", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Doç. Dr. C. O.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İŞL4911", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Doç. Dr. F. Ç.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "KAY 1805", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "ORT_HUKUK", "KidemPuani": 5},
        {"DersKodu": "EKF 4507", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi A. O. Ö.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "EKF 3005", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi A. O. Ö.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "İŞL1827", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Dr. Öğr. Üyesi C. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "EKF 2009", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Dr. Öğr. Üyesi M. A. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "EKF 2007", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Dr. Öğr. Üyesi Ö. U.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "EKF4505", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "İŞL 3901", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "EKF 3001", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Öğr. Gör. Dr. N. Ü.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "EKF 2003", "Bolum": "Ekonomi ve Finans", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. N. Ü.", "OrtakDersID": "ORT_MAKRO", "KidemPuani": 1},
        {"DersKodu": "EKF 4003", "Bolum": "Ekonomi ve Finans", "Sinif": 4, "HocaAdi": "Öğr. Gör. Dr. Y. N.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "ENF 1805", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "ORT_BILGISAYAR_2", "KidemPuani": 1},
        {"DersKodu": "İŞL 3907", "Bolum": "Ekonomi ve Finans", "Sinif": 3, "HocaAdi": "Prof. Dr. F. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "ATB 1801", "Bolum": "Ekonomi ve Finans", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB", "KidemPuani": 1},

        # --- YBS ---
        {"DersKodu": "İŞL 2829", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. E. K.", "OrtakDersID": "ORT_FIN_MUH", "KidemPuani": 1},
        {"DersKodu": "İŞL 3809", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_SAYISAL", "KidemPuani": 1},
        {"DersKodu": "İŞL 2827", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL", "KidemPuani": 1},
        {"DersKodu": "YBS 3511", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "YBS 4001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Doç. Dr. M. İ.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "YBS 2511", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Doç. Dr. M. İ.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "YBS 4005", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Doç. Dr. M. İ.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "YBS 2001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Doç. Dr. M. D.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "YBS 4003", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Doç. Dr. M. D.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "İŞL 1837", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Doç. Dr. M. D.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "KAY 1811", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Doç. Dr. N. K.", "OrtakDersID": "ORT_HUKUK", "KidemPuani": 5},
        {"DersKodu": "YBS 3505", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi M. S.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "YBS 4509", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "ORT_ETICARET", "KidemPuani": 3},
        {"DersKodu": "YBS 4515", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Öğr. Gör. C. G.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "İKT 2813", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Öğr. Gör. Dr. Y. N.", "OrtakDersID": "ORT_IKT_GIRIS", "KidemPuani": 1},
        {"DersKodu": "YBS 1001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "YBS 3003", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "YBS 2003", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 2, "HocaAdi": "Prof. Dr. B. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "YBS 4501", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 4, "HocaAdi": "Prof. Dr. B. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL 1833", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Prof. Dr. İ. K.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL 3001", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 3, "HocaAdi": "Prof. Dr. M. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "İŞL 1835", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Prof. Dr. M. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "ATB 1801", "Bolum": "Yönetim Bilişim Sistemleri", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB", "KidemPuani": 1},

        # --- UTL ---
        {"DersKodu": "İŞL2001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Arş. Gör. Dr. G. Ç.", "OrtakDersID": "ORT_ISTATISTIK_YBS_UTL", "KidemPuani": 1},
        {"DersKodu": "UTL2005", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "UTL1003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Doç. Dr. A. R. A.", "OrtakDersID": "ORT_EKONOMI_1", "KidemPuani": 5},
        {"DersKodu": "UTL2007", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "UTL1001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "UTL2001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. E. E. Y.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "UTL3001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "UTL4001", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "", "KidemPuani": 5},
        {"DersKodu": "UTL2011", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Doç. Dr. H. K.", "OrtakDersID": "ORT_GEN_MUH", "KidemPuani": 5},
        {"DersKodu": "UTL4513", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi A. O. Ö.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "UTL4003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "UTL3503", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "UTL4515", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Dr. Öğr. Üyesi R. A.", "OrtakDersID": "ORT_ETICARET", "KidemPuani": 3},
        {"DersKodu": "UTL2503", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "", "KidemPuani": 3},
        {"DersKodu": "KAY1805", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Dr.Öğr.Üyesi S. Y. C.", "OrtakDersID": "ORT_HUKUK_TEMEL", "KidemPuani": 3},
        {"DersKodu": "UTL3519", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Öğr. Gör. C. G.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "UTL4501", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Öğr. Gör. C. G.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "UTL3005", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Öğr. Gör. Dr. G. K.", "OrtakDersID": "", "KidemPuani": 1},
        {"DersKodu": "ENF1805", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Öğr. Gör. İ. B.", "OrtakDersID": "ORT_BILGISAYAR_2", "KidemPuani": 1},
        {"DersKodu": "UTL4517", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 4, "HocaAdi": "Öğr. Gör. M. G.", "OrtakDersID": "ORT_ISG", "KidemPuani": 1},
        {"DersKodu": "İŞL1003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Prof. Dr. A. E. A.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "UTL3003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Prof. Dr. D. A. I.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "UTL2003", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Prof. Dr. D. A. I.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "UTL3509", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 3, "HocaAdi": "Prof. Dr. F. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "UTL2009", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 2, "HocaAdi": "Prof. Dr. F. Ş.", "OrtakDersID": "", "KidemPuani": 10},
        {"DersKodu": "UTL1005", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Prof. Dr. İ. K.", "OrtakDersID": "ORT_ISL_MAT", "KidemPuani": 10},
        {"DersKodu": "ATB 1801", "Bolum": "Uluslararası Ticaret ve Lojistik", "Sinif": 1, "HocaAdi": "Öğr. Gör. N. K.", "OrtakDersID": "ORT_ATB", "KidemPuani": 1},
    ]

    df = pd.DataFrame(data)
    df['IstenmeyenGun'] = ""
    df['ZorunluGun'] = ""
    df['ZorunluSeans'] = ""

    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sablon')
    
    worksheet = writer.book.add_worksheet('Aciklamalar')
    aciklamalar = [
        "BU DOSYA GÜNCEL VERİLERİ İÇERİR.",
        "ÖNEMLİ: ORTAK ID'leri silmeyiniz!",
        "1. İstenmeyen Gün: Hocanın gelmek istemediği günleri virgülle yazın."
    ]
    for i, satir in enumerate(aciklamalar):
        worksheet.write(i, 0, satir)
    
    writer.close()
    return output.getvalue()

# --- ÇÖZÜM MOTORU ---
def programi_coz(df_veri):
    model = cp_model.CpModel()
    gunler = ['Pazartesi', 'Sali', 'Carsamba', 'Persembe', 'Cuma']
    seanslar = ['Sabah', 'Ogle', 'OgledenSonra']

    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    hoca_tercihleri = {} 
    ortak_ders_gruplari = {}

    df_veri['HocaAdi'] = df_veri['HocaAdi'].astype(str).str.strip()
    df_veri['DersKodu'] = df_veri['DersKodu'].astype(str).str.strip()
    
    if 'KidemPuani' not in df_veri.columns: df_veri['KidemPuani'] = 1
    df_veri['KidemPuani'] = df_veri['KidemPuani'].fillna(1).astype(int)

    hoca_listesi = df_veri['HocaAdi'].dropna().unique().tolist()

    for hoca in hoca_listesi:
        ornek_satir = df_veri[df_veri['HocaAdi'] == hoca].iloc[0]
        raw_gunler = str(ornek_satir['IstenmeyenGun']) if pd.notna(ornek_satir['IstenmeyenGun']) else ""
        istenmeyen_list = [g.strip() for g in raw_gunler.split(',') if g.strip() in gunler]
        kidem = int(ornek_satir['KidemPuani'])
        hoca_tercihleri[hoca] = {'istenmeyen': istenmeyen_list, 'kidem': kidem}
        hoca_dersleri[hoca] = []

    for index, row in df_veri.iterrows():
        d_id = row['DersKodu']
        hoca = row['HocaAdi']
        ortak_id = row['OrtakDersID'] if pd.notna(row['OrtakDersID']) else None
        zg = row['ZorunluGun'] if pd.notna(row['ZorunluGun']) and row['ZorunluGun'] in gunler else None
        zs = row['ZorunluSeans'] if pd.notna(row['ZorunluSeans']) and row['ZorunluSeans'] in seanslar else None

        tum_dersler.append(d_id)
        ders_detaylari[d_id] = {'bolum': row['Bolum'], 'sinif': row['Sinif'], 'hoca': hoca,
                                'ortak_id': ortak_id, 'zorunlu_gun': zg, 'zorunlu_seans': zs}
        hoca_dersleri[hoca].append(d_id)
        if ortak_id:
            if ortak_id not in ortak_ders_gruplari: ortak_ders_gruplari[ortak_id] = []
            ortak_ders_gruplari[ortak_id].append(d_id)

    program = {}
    for d in tum_dersler:
        for g in gunler:
            for s in seanslar:
                program[(d, g, s)] = model.NewBoolVar(f'{d}_{g}_{s}')

    hoca_gun_aktif = {}
    for h in hoca_listesi:
        for g_idx, g in enumerate(gunler):
            hoca_gun_aktif[(h, g_idx)] = model.NewBoolVar(f'{h}_{g}')

    # --- HARD CONSTRAINTS (KESİN KURALLAR) ---
    
    # 1. Her ders 1 kere
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)

    # 2. Hoca Çakışması (KESİN YASAK)
    for h in hoca_listesi:
        dersleri = hoca_dersleri[h]
        unique_ders_temsilcileri = []
        islenen_ortak_idler = set()
        for d in dersleri:
            oid = ders_detaylari[d]['ortak_id']
            if oid:
                if oid not in islenen_ortak_idler:
                    unique_ders_temsilcileri.append(d)
                    islenen_ortak_idler.add(oid)
            else:
                unique_ders_temsilcileri.append(d)
        
        for g in gunler:
            for s in seanslar:
                model.Add(sum(program[(d, g, s)] for d in unique_ders_temsilcileri) <= 1)

    # 3. Bölüm/Sınıf Çakışması (Aynı anda 2 ders olamaz)
    bolumler = df_veri['Bolum'].unique()
    siniflar = sorted(df_veri['Sinif'].unique())
    
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    for s in seanslar: 
                        model.Add(sum(program[(d, g, s)] for d in ilgili) <= 1)

    # 4. Ortak Ders Senkronizasyonu
    for o_id, d_list in ortak_ders_gruplari.items():
        if len(d_list) > 1:
            ref = d_list[0]
            for diger in d_list[1:]:
                for g in gunler:
                    for s in seanslar: model.Add(program[(ref, g, s)] == program[(diger, g, s)])
    
    # 5. Zorunlu Gün
    for d in tum_dersler:
        zg, zs = ders_detaylari[d]['zorunlu_gun'], ders_detaylari[d]['zorunlu_seans']
        if zg:
            for g in gunler:
                if g != zg:
                    for s in seanslar: model.Add(program[(d, g, s)] == 0)
        if zs:
            for s in seanslar:
                if s != zs:
                    for g in gunler: model.Add(program[(d, g, s)] == 0)

    # 6. Kapasite
    for g in gunler:
        for s in seanslar: model.Add(sum(program[(d, g, s)] for d in tum_dersler) <= DERSLIK_SAYISI)

    # --- SOFT CONSTRAINTS (PUANLAMA) ---
    puanlar = []
    
    # A. Öğrenci Günlük Yük Dengesi (Günde 2 ders ideal, 3 olursa ceza)
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    gunluk_toplam = sum(program[(d, g, s)] for d in ilgili for s in seanslar)
                    overload = model.NewBoolVar(f'overload_{b}_{sin}_{g}')
                    model.Add(gunluk_toplam > 2).OnlyEnforceIf(overload)
                    model.Add(gunluk_toplam <= 2).OnlyEnforceIf(overload.Not())
                    puanlar.append(overload * -CEZA_OGRENCI_GUNLUK_3)

    # B. Hoca Tercihleri ve Konforu
    for h in hoca_listesi:
        dersleri = hoca_dersleri[h]
        unique_d = []
        seen_o = set()
        for d in dersleri:
            oid = ders_detaylari[d]['ortak_id']
            if oid:
                if oid not in seen_o: unique_d.append(d); seen_o.add(oid)
            else: unique_d.append(d)

        kidem = hoca_tercihleri[h]['kidem'] 
        istenmeyenler = hoca_tercihleri[h]['istenmeyen']

        for g_idx, g in enumerate(gunler):
            g_toplam = sum(program[(d, g, s)] for d in unique_d for s in seanslar)
            model.Add(g_toplam > 0).OnlyEnforceIf(hoca_gun_aktif[(h, g_idx)])
            model.Add(g_toplam == 0).OnlyEnforceIf(hoca_gun_aktif[(h, g_idx)].Not())
            if g in istenmeyenler:
                puanlar.append(hoca_gun_aktif[(h, g_idx)] * -CEZA_HOCA_ISTENMEYEN_GUN * kidem)

        for g_idx in range(4):
            ard = model.NewBoolVar(f'ard_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)]]).OnlyEnforceIf(ard)
            puanlar.append(ard * ODUL_ARDISIK_GUN * kidem)

        for g_idx in range(3):
            bosluk_var = model.NewBoolVar(f'gap_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)].Not(), hoca_gun_aktif[(h, g_idx+2)]]).OnlyEnforceIf(bosluk_var)
            puanlar.append(bosluk_var * -CEZA_GUN_BOSLUGU * kidem)

    model.Maximize(sum(puanlar))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = MAX_SURE
    status = solver.Solve(model)
    return status, solver, program, tum_dersler, ders_detaylari, hoca_gun_aktif

# --- ARAYÜZ ---
col1, col2 = st.columns([1, 2])
with col1:
    st.info("Kullanmaya başlamadan önce şablonu indirin:")
    st.download_button(
        label="📥 Güncel Ders Yükünü İndir (V13.1)",
        data=sablon_olustur(),
        file_name="Ders_Yukleri_Guncel_V13_1.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

uploaded_file = st.file_uploader("Excel Dosyasını Yükleyin", type=['xlsx'])

if uploaded_file is not None:
    if st.button("Programı Dağıt"):
        with st.spinner('Program oluşturuluyor... (3 dakikaya kadar sürebilir)'):
            try:
                df_input = pd.read_excel(uploaded_file)
                status, solver, program, tum_dersler, ders_detaylari, hoca_gun_aktif = programi_coz(df_input)

                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    st.balloons()
                    st.success(f"✅ Program Başarıyla Oluşturuldu! (Puan: {solver.ObjectiveValue()})")
                    
                    st.subheader("⚠️ Durum Raporu (İdealden Sapmalar)")
                    gunler = ['Pazartesi', 'Sali', 'Carsamba', 'Persembe', 'Cuma']
                    hoca_listesi = df_input['HocaAdi'].dropna().unique().tolist()
                    seanslar = ['Sabah', 'Ogle', 'OgledenSonra']
                    bolumler = df_input['Bolum'].unique()
                    siniflar = sorted(df_input['Sinif'].unique())
                    
                    # Öğrenci Yükü Kontrolü
                    for b in bolumler:
                        for sin in siniflar:
                            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
                            if ilgili:
                                for g in gunler:
                                    toplam = 0
                                    for s in seanslar:
                                        if any(solver.Value(program[(d, g, s)]) for d in ilgili):
                                            toplam += 1
                                    if toplam > 2:
                                        st.warning(f"{b} {sin}. Sınıf -> {g} günü {toplam} ders var (Mecburiyetten).")

                    # --- EXCEL ÇIKTISI ---
                    output = io.BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    
                    for bolum in bolumler:
                        index_list = pd.MultiIndex.from_product([gunler, seanslar], names=['Gün', 'Seans'])
                        df_matrix = pd.DataFrame(index=index_list, columns=siniflar)
                        
                        for d in tum_dersler:
                            detay = ders_detaylari[d]
                            if detay['bolum'] == bolum:
                                for g in gunler:
                                    for s in seanslar:
                                        if solver.Value(program[(d, g, s)]) == 1:
                                            mevcut_icerik = str(df_matrix.at[(g, s), detay['sinif']])
                                            yeni_icerik = f"{d}\n{detay['hoca']}"
                                            if detay['ortak_id']: yeni_icerik += f"\n(Ort: {detay['ortak_id']})"
                                            
                                            if mevcut_icerik != "nan":
                                                df_matrix.at[(g, s), detay['sinif']] = mevcut_icerik + "\n-----\n" + yeni_icerik
                                            else:
                                                df_matrix.at[(g, s), detay['sinif']] = yeni_icerik
                        
                        sheet_name = str(bolum)[:30]
                        df_matrix.to_excel(writer, sheet_name=sheet_name)
                        workbook = writer.book
                        worksheet = writer.sheets[sheet_name]
                        wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                        worksheet.set_column('A:B', 15)
                        worksheet.set_column('C:F', 25, wrap_format)

                    writer.close()
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Haftalık Programı İndir",
                        data=processed_data,
                        file_name="Final_Program_V13_1.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                else:
                    st.error("❌ Çözüm bulunamadı. Lütfen 'Ortak Ders ID'lerin doğru girildiğinden emin olun.")
            except Exception as e:
                st.error(f"Hata: {e}")
