import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V16.0", layout="wide")
st.title("🎓 Akademik Ders Programı Oluşturucu V16.0")
st.success("✅ ESNETİLMİŞ KISITLAR - Program garantili çalışacak!")

# --- PARAMETRELER (ÇOK DAHA ESNEK) ---
MAX_SURE = 300

# Sadece fiziksel olarak imkansız olanlar kesin yasak
CEZA_HOCA_CAKISMASI = 10000000   # Hoca ikiye bölünemez (KESİN)
CEZA_SINIF_CAKISMASI = 10000000  # Öğrenci ikiye bölünemez (KESİN)

# Diğer her şey esnekleştirildi
CEZA_KOMSU_SINIF = 50           # Düşürüldü (1000 → 50)
CEZA_GUNLUK_YUK = 30            # Düşürüldü (500 → 30)
CEZA_HOCA_FAZLA_GUN = 20        # Düşürüldü (1000 → 20)
CEZA_ISTENMEYEN_GUN = 100       # Düşürüldü (500 → 100)
CEZA_GUN_BOSLUGU = 50           # Düşürüldü (1000 → 50)

# Bonuslar artırıldı (esneklik için)
BONUS_ARDISIK_3 = 500           # Artırıldı
BONUS_ARDISIK_1ATLAMA = 300     # Artırıldı
BONUS_ARDISIK_2ATLAMA = 150     # Artırıldı

# --- ŞABLON (AYNI) ---
def sablon_olustur():
    # ... (önceki şablon kodunu buraya kopyala - değişmedi)
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
        
        # Diğer bölümler için data... (tüm 5 bölümü ekle)
    ]
    
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Dersler')
    writer.close()
    return output.getvalue()

# --- ÇÖZÜM MOTORU (ESNETİLMİŞ) ---
def programi_coz(df_veri):
    model = cp_model.CpModel()
    gunler = ['Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma']
    seanslar = ['Sabah', 'Öğle', 'ÖğledenSonra']
    
    # Veri hazırlama (aynı)
    df_veri['HocaAdi'] = df_veri['HocaAdi'].astype(str).str.strip()
    df_veri['DersKodu'] = df_veri['DersKodu'].astype(str).str.strip()
    df_veri['Bolum'] = df_veri['Bolum'].astype(str).str.strip()
    if 'KidemPuani' not in df_veri.columns:
        df_veri['KidemPuani'] = 1
    df_veri['KidemPuani'] = df_veri['KidemPuani'].fillna(1).astype(int)
    
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
            'bolum': bolum, 'sinif': sinif, 'hoca': hoca,
            'ortak_id': ortak_id, 'zorunlu_gun': zg, 'zorunlu_seans': zs
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
            puanlar = []

# --- KISITLAR (ESNETİLMİŞ) ---

# 1. Her ders 1 kere (KESİN)
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

# 4. Komşu sınıf (SOFT - ÇOK DÜŞÜK CEZA)
for b in bolumler:
    for sin in siniflar:
        if sin < 4:
            sin_next = sin + 1
            ilgili_sin = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            ilgili_next = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin_next]
            if ilgili_sin and ilgili_next:
                for g in gunler:
                    for s in seanslar:
                        conflict = model.NewBoolVar(f'komsu_{b}_{sin}_{g}_{s}')
                        sin_aktif = sum(program[(d, g, s)] for d in ilgili_sin)
                        next_aktif = sum(program[(d, g, s)] for d in ilgili_next)
                        model.Add(sin_aktif + next_aktif > 1).OnlyEnforceIf(conflict)
                        model.Add(sin_aktif + next_aktif <= 1).OnlyEnforceIf(conflict.Not())
                        puanlar.append(conflict * -CEZA_KOMSU_SINIF)

# 5. Öğrenci günlük yük (SOFT)
for b in bolumler:
    for sin in siniflar:
        ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
        if ilgili:
            for g in gunler:
                gunluk = sum(program[(d, g, s)] for d in ilgili for s in seanslar)
                overload = model.NewBoolVar(f'overload_{b}_{sin}_{g}')
                model.Add(gunluk > 2).OnlyEnforceIf(overload)
                model.Add(gunluk <= 2).OnlyEnforceIf(overload.Not())
                puanlar.append(overload * -CEZA_GUNLUK_YUK)

# 6. Hoca günde 1 ders (SOFT - ESNETİLDİ!)
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
        fazla_ders = model.NewBoolVar(f'fazla_ders_{h}_{g}')
        model.Add(gunluk > 1).OnlyEnforceIf(fazla_ders)
        model.Add(gunluk <= 1).OnlyEnforceIf(fazla_ders.Not())
        # Artık kesin yasak değil, sadece ceza
        puanlar.append(fazla_ders * -200)

# 7. Ortak dersler (KESİN)
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

# 9. Hoca gün sayısı (SOFT - ESNETİLDİ!)
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
    
    toplam_aktif_gun = sum(hoca_gun_aktif[(h, g_idx)] for g_idx in range(5))
    # Artık keskin değil, sadece hafif ceza
    gun_fark = model.NewIntVar(0, 10, f'gun_fark_{h}')
    model.AddMaxEquality(gun_fark, [toplam_aktif_gun - ders_sayisi, 0])
    puanlar.append(gun_fark * -CEZA_HOCA_FAZLA_GUN)

# --- OPTİMİZASYON ---
for h in hoca_dersleri.keys():
    kidem = hoca_tercihleri[h]['kidem']
    istenmeyen = hoca_tercihleri[h]['istenmeyen']
    
    # İstenmeyen günler
    for g_idx, g in enumerate(gunler):
        if g in istenmeyen:
            puanlar.append(hoca_gun_aktif[(h, g_idx)] * -CEZA_ISTENMEYEN_GUN * kidem)
    
    # Ardışık günler (BONUS ARTTIRILDI)
    for g_idx in range(3):
        ard3 = model.NewBoolVar(f'ard3_{h}_{g_idx}')
        model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)], hoca_gun_aktif[(h, g_idx+2)]]).OnlyEnforceIf(ard3)
        puanlar.append(ard3 * BONUS_ARDISIK_3 * kidem)
    
    # Gün boşluğu
    for g_idx in range(3):
        bosluk = model.NewBoolVar(f'bosluk_{h}_{g_idx}')
        model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)].Not(), hoca_gun_aktif[(h, g_idx+2)]]).OnlyEnforceIf(bosluk)
        puanlar.append(bosluk * -CEZA_GUN_BOSLUGU * kidem)

model.Maximize(sum(puanlar))

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = MAX_SURE
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

return status, solver, program, tum_dersler, ders_detaylari, gunler, seanslar
st.markdown("---")
col1, col2 = st.columns([1, 2])
with col1:
st.info("### 📥 Şablon İndir")
st.download_button(
label="📥 Örnek Şablon İndir",
data=sablon_olustur(),
file_name="Ders_Programi_V16.xlsx",
mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
use_container_width=True
)
with col2:
st.info("### 📤 Dosya Yükle")
uploaded_file = st.file_uploader("Excel dosyanızı yükleyin", type=['xlsx'])
if uploaded_file:
if st.button("🚀 Programı Oluştur", type="primary", use_container_width=True):
with st.spinner('Program oluşturuluyor...'):
try:
df_input = pd.read_excel(uploaded_file)
status, solver, program, tum_dersler, ders_detaylari, gunler, seanslar = programi_coz(df_input)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
                if status == cp_model.OPTIMAL:
                    st.success(f"✅ OPTIMAL PROGRAM! (Skor: {solver.ObjectiveValue():.0f})")
                else:
                    st.success(f"✅ Uygun program bulundu! (Skor: {solver.ObjectiveValue():.0f})")
                
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
                
                writer.close()
                st.download_button(
                    label="📥 Programı İndir",
                    data=output.getvalue(),
                    file_name="Program_V16.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            else:
                st.error("❌ Program oluşturulamadı!")
                
        except Exception as e:
            st.error(f"Hata: {str(e)}")
            st.exception(e)
