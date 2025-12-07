import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V6.0", layout="wide")

st.title("🎓 Akademik Ders Programı Dağıtıcı (V6.0)")
st.markdown("""
Bu sistem, akademik ders programlarını optimize eder ve **haftalık tablo formatında** çıktı verir.
1. Önce **Örnek Şablonu** indirin ve doldurun.
2. Dosyayı yükleyip programı çalıştırın.
""")

# --- AYARLAR ---
DERSLIK_SAYISI = 30
MAX_SURE = 120
CEZA_ISTENMEYEN_GUN_BAZ = -50
ODUL_ARDISIK_BAZ = 100
CEZA_BOSLUKLU_GUN = -200

# --- ŞABLON OLUŞTURMA FONKSİYONU ---
def sablon_olustur():
    # Örnek veri seti
    data = {
        'DersKodu': ['EKO101', 'IKT201', 'ISL301'],
        'Bolum': ['Ekonometri', 'Iktisat', 'Isletme'],
        'Sinif': [1, 2, 3],
        'HocaAdi': ['Prof. Dr. Ornek', 'Doç. Dr. Ornek', 'Dr. Öğr. Üyesi Ornek'],
        'IstenmeyenGun': ['Cuma', 'Pazartesi, Cuma', ''],
        'OrtakDersID': ['', '', ''],
        'ZorunluGun': ['', '', ''],
        'ZorunluSeans': ['', '', ''],
        'KidemPuani': [10, 5, 3]
    }
    df = pd.DataFrame(data)
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sablon')
    
    # Açıklama sayfası ekleyelim
    worksheet = writer.book.add_worksheet('Aciklamalar')
    worksheet.write(0, 0, "KidemPuani: Prof=10, Doç=5, Dr=3, Arş=1 (Öncelik sırasıdır)")
    worksheet.write(1, 0, "IstenmeyenGun: Virgülle ayırarak yazabilirsiniz (Örn: Pazartesi, Cuma)")
    
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

    # Veri Temizliği
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

    # Değişkenler
    program = {}
    for d in tum_dersler:
        for g in gunler:
            for s in seanslar:
                program[(d, g, s)] = model.NewBoolVar(f'{d}_{g}_{s}')

    hoca_gun_aktif = {}
    for h in hoca_listesi:
        for g_idx, g in enumerate(gunler):
            hoca_gun_aktif[(h, g_idx)] = model.NewBoolVar(f'{h}_{g}')

    # --- TEMEL KISITLAR ---
    # 1. Her ders 1 kere
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)

    # 2. Hoca Çakışması
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

    # 3. Bölüm/Sınıf (Yatay Çakışma ve Günlük Limit)
    bolumler = df_veri['Bolum'].unique()
    siniflar = sorted(df_veri['Sinif'].unique()) # Sıralı olsun
    
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    for s in seanslar: model.Add(sum(program[(d, g, s)] for d in ilgili) <= 1)
                    model.Add(sum(program[(d, g, s)] for d in ilgili for s in seanslar) <= 2)

    # 4. Dikey Çakışma (1-2, 2-3, 3-4)
    for b in bolumler:
        for s in seanslar:
            for g in gunler:
                # 1 vs 2
                d1 = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==1]
                d2 = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==2]
                if d1 and d2:
                    v1, v2 = model.NewBoolVar(''), model.NewBoolVar('')
                    model.Add(sum(program[(d, g, s)] for d in d1) >= 1).OnlyEnforceIf(v1)
                    model.Add(sum(program[(d, g, s)] for d in d1) == 0).OnlyEnforceIf(v1.Not())
                    model.Add(sum(program[(d, g, s)] for d in d2) >= 1).OnlyEnforceIf(v2)
                    model.Add(sum(program[(d, g, s)] for d in d2) == 0).OnlyEnforceIf(v2.Not())
                    model.Add(v1 + v2 <= 1)
                # 2 vs 3
                d3 = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==3]
                if d2 and d3:
                    v2b, v3 = model.NewBoolVar(''), model.NewBoolVar('')
                    model.Add(sum(program[(d, g, s)] for d in d2) >= 1).OnlyEnforceIf(v2b)
                    model.Add(sum(program[(d, g, s)] for d in d2) == 0).OnlyEnforceIf(v2b.Not())
                    model.Add(sum(program[(d, g, s)] for d in d3) >= 1).OnlyEnforceIf(v3)
                    model.Add(sum(program[(d, g, s)] for d in d3) == 0).OnlyEnforceIf(v3.Not())
                    model.Add(v2b + v3 <= 1)
                # 3 vs 4
                d4 = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==4]
                if d3 and d4:
                    v3b, v4 = model.NewBoolVar(''), model.NewBoolVar('')
                    model.Add(sum(program[(d, g, s)] for d in d3) >= 1).OnlyEnforceIf(v3b)
                    model.Add(sum(program[(d, g, s)] for d in d3) == 0).OnlyEnforceIf(v3b.Not())
                    model.Add(sum(program[(d, g, s)] for d in d4) >= 1).OnlyEnforceIf(v4)
                    model.Add(sum(program[(d, g, s)] for d in d4) == 0).OnlyEnforceIf(v4.Not())
                    model.Add(v3b + v4 <= 1)

    # 5. Kapasite ve Ortak Ders
    for g in gunler:
        for s in seanslar: model.Add(sum(program[(d, g, s)] for d in tum_dersler) <= DERSLIK_SAYISI)
    for o_id, d_list in ortak_ders_gruplari.items():
        if len(d_list) > 1:
            ref = d_list[0]
            for diger in d_list[1:]:
                for g in gunler:
                    for s in seanslar: model.Add(program[(ref, g, s)] == program[(diger, g, s)])
    
    # 6. Zorunlu Gün
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

    # --- OBJEKTİF (Puanlama) ---
    puanlar = []
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
                puanlar.append(hoca_gun_aktif[(h, g_idx)] * CEZA_ISTENMEYEN_GUN_BAZ * kidem)

        for g_idx in range(4):
            ard = model.NewBoolVar(f'ard_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)]]).OnlyEnforceIf(ard)
            puanlar.append(ard * ODUL_ARDISIK_BAZ * kidem)

        # Delik Deşik Gün Cezası
        for g_idx in range(3):
            bosluk_var = model.NewBoolVar(f'gap_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)].Not(), hoca_gun_aktif[(h, g_idx+2)]]).OnlyEnforceIf(bosluk_var)
            puanlar.append(bosluk_var * CEZA_BOSLUKLU_GUN * kidem)

    model.Maximize(sum(puanlar))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = MAX_SURE
    status = solver.Solve(model)
    return status, solver, program, tum_dersler, ders_detaylari

# --- ARAYÜZ ve ÇIKTI FORMATLAMA ---
col1, col2 = st.columns([1, 2])
with col1:
    st.info("Kullanmaya başlamadan önce şablonu indirin:")
    st.download_button(
        label="📥 Örnek Şablon Excel İndir",
        data=sablon_olustur(),
        file_name="Ders_Programi_Sablonu.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

uploaded_file = st.file_uploader("Doldurduğunuz Excel Dosyasını Yükleyin", type=['xlsx'])

if uploaded_file is not None:
    if st.button("Programı Dağıt"):
        with st.spinner('Matematiksel modeller çalışıyor...'):
            try:
                df_input = pd.read_excel(uploaded_file)
                status, solver, program, tum_dersler, ders_detaylari = programi_coz(df_input)

                if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
                    st.success(f"✅ Program Oluşturuldu! (Skor: {solver.ObjectiveValue()})")
                    
                    # --- ÇIKTIYI MATRİS FORMATINA ÇEVİRME ---
                    output = io.BytesIO()
                    writer = pd.ExcelWriter(output, engine='xlsxwriter')
                    
                    bolumler = df_input['Bolum'].unique()
                    gunler = ['Pazartesi', 'Sali', 'Carsamba', 'Persembe', 'Cuma']
                    seanslar = ['Sabah', 'Ogle', 'OgledenSonra']
                    siniflar = sorted(df_input['Sinif'].unique())
                    
                    for bolum in bolumler:
                        # Boş bir DataFrame matrisi oluştur
                        # Satırlar: Gün x Seans, Sütunlar: Sınıflar (1, 2, 3, 4)
                        index_list = pd.MultiIndex.from_product([gunler, seanslar], names=['Gün', 'Seans'])
                        df_matrix = pd.DataFrame(index=index_list, columns=siniflar)
                        
                        # İçini doldur
                        for d in tum_dersler:
                            detay = ders_detaylari[d]
                            if detay['bolum'] == bolum:
                                for g in gunler:
                                    for s in seanslar:
                                        if solver.Value(program[(d, g, s)]) == 1:
                                            # Hücre içeriği: Ders Kodu - Hoca
                                            icerik = f"{d}\n{detay['hoca']}"
                                            if detay['ortak_id']:
                                                icerik += f"\n(Ort: {detay['ortak_id']})"
                                            
                                            df_matrix.at[(g, s), detay['sinif']] = icerik
                        
                        # Excel'e yaz (Her bölüm ayrı sayfa)
                        sheet_name = str(bolum)[:30] # Excel sayfa adı max 31 karakter
                        df_matrix.to_excel(writer, sheet_name=sheet_name)
                        
                        # Biraz Excel Makyajı (Hücre Genişliği)
                        workbook = writer.book
                        worksheet = writer.sheets[sheet_name]
                        wrap_format = workbook.add_format({'text_wrap': True, 'valign': 'top'})
                        worksheet.set_column('A:B', 15) # Gün ve Seans sütunu
                        worksheet.set_column('C:F', 25, wrap_format) # Sınıf sütunları

                    writer.close()
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label="📥 Haftalık Programı İndir (Bölüm Bazlı)",
                        data=processed_data,
                        file_name="Haftalik_Program_V6.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                    st.write("---")
                    st.info("Not: İndirilen Excel dosyasında her bölüm için ayrı bir sayfa (tab) oluşturulmuştur.")
                    
                else:
                    st.error("❌ Çözüm bulunamadı. Kısıtlar çok katı.")
            except Exception as e:
                st.error(f"Hata: {e}")