import streamlit as st
import pandas as pd
from ortools.sat.python import cp_model
import io
import xlsxwriter

# Sayfa Ayarları
st.set_page_config(page_title="Akademik Ders Programı V13.0", layout="wide")

st.title("🎓 Akademik Ders Programı Dağıtıcı (V13.0 - Elastik Mod)")
st.info("""
Bu versiyon, "Çözüm Bulunamadı" hatasını engellemek için tüm konfor kurallarını 'Esnek (Soft)' hale getirmiştir.
Program matematiksel olarak mümkün olan **en az kötü** senaryoyu size sunacaktır.
""")

# --- CEZA PUANLARI (Önem Sırası) ---
# Puan ne kadar yüksekse, yazılım o hatayı yapmamak için o kadar direnir.
CEZA_HOCA_ISTENMEYEN_GUN = 500   # Hoca istemediği güne gelirse
CEZA_OGRENCI_GUNLUK_3 = 100      # Öğrenci günde 3 derse girerse (İdeal olan 2)
CEZA_GUN_BOSLUGU = 50            # Hoca Pzt-Çrş gelip Salı gelmezse
ODUL_ARDISIK_GUN = 200           # Günler blok olursa ödül

# Sabitler
DERSLIK_SAYISI = 100 
MAX_SURE = 300  # 5 Dakika süre veriyoruz ki en iyisini bulsun

# --- ŞABLON OLUŞTURMA ---
def sablon_olustur():
    # Veri seti aynı kalıyor, sadece kodu sadeleştirmek için burayı özet geçiyorum
    # Kullanıcı zaten elindeki dosyayı yükleyecek.
    # Buraya V12'deki veri setinin aynısı gelecek (Temsili boş dataframe)
    data = [{"DersKodu": "ORNEK101", "Bolum": "Ornek", "Sinif": 1, "HocaAdi": "Ornek Hoca", "OrtakDersID": "", "KidemPuani": 1}]
    df = pd.DataFrame(data)
    df['IstenmeyenGun'] = ""
    df['ZorunluGun'] = ""
    df['ZorunluSeans'] = ""
    
    output = io.BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sablon')
    writer.close()
    return output.getvalue()

# --- ANA MOTOR ---
def programi_coz(df_veri):
    model = cp_model.CpModel()
    gunler = ['Pazartesi', 'Sali', 'Carsamba', 'Persembe', 'Cuma']
    seanslar = ['Sabah', 'Ogle', 'OgledenSonra']

    tum_dersler = []
    ders_detaylari = {}
    hoca_dersleri = {}
    hoca_tercihleri = {} 
    ortak_ders_gruplari = {}

    # 1. VERİ TEMİZLİĞİ VE HAZIRLIK
    df_veri['HocaAdi'] = df_veri['HocaAdi'].astype(str).str.strip()
    df_veri['DersKodu'] = df_veri['DersKodu'].astype(str).str.strip()
    if 'KidemPuani' not in df_veri.columns: df_veri['KidemPuani'] = 1
    df_veri['KidemPuani'] = df_veri['KidemPuani'].fillna(1).astype(int)

    hoca_listesi = df_veri['HocaAdi'].dropna().unique().tolist()

    # Hoca tercihlerini işle
    for hoca in hoca_listesi:
        ornek_satir = df_veri[df_veri['HocaAdi'] == hoca].iloc[0]
        raw_gunler = str(ornek_satir['IstenmeyenGun']) if pd.notna(ornek_satir['IstenmeyenGun']) else ""
        istenmeyen_list = [g.strip() for g in raw_gunler.split(',') if g.strip() in gunler]
        kidem = int(ornek_satir['KidemPuani'])
        hoca_tercihleri[hoca] = {'istenmeyen': istenmeyen_list, 'kidem': kidem}
        hoca_dersleri[hoca] = []

    # Dersleri işle
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

    # 2. DEĞİŞKENLER
    program = {}
    for d in tum_dersler:
        for g in gunler:
            for s in seanslar:
                program[(d, g, s)] = model.NewBoolVar(f'{d}_{g}_{s}')

    hoca_gun_aktif = {}
    for h in hoca_listesi:
        for g_idx, g in enumerate(gunler):
            hoca_gun_aktif[(h, g_idx)] = model.NewBoolVar(f'{h}_{g}')

    # --- 3. HARD CONSTRAINTS (FİZİK KURALLARI - ASLA DELİNEMEZ) ---

    # A. Her ders haftada tam 1 kez yapılacak
    for d in tum_dersler:
        model.Add(sum(program[(d, g, s)] for g in gunler for s in seanslar) == 1)

    # B. Hoca Çakışması (Aynı anda 2 yerde olamaz)
    # Ortak dersler tek sayılır.
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

    # C. Sınıf Çakışması (Öğrenci aynı anda 2 derste olamaz)
    bolumler = df_veri['Bolum'].unique()
    siniflar = sorted(df_veri['Sinif'].unique())
    
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    for s in seanslar: 
                        model.Add(sum(program[(d, g, s)] for d in ilgili) <= 1)

    # D. Ortak Ders Senkronizasyonu
    for o_id, d_list in ortak_ders_gruplari.items():
        ref = d_list[0]
        for diger in d_list[1:]:
            for g in gunler:
                for s in seanslar: model.Add(program[(ref, g, s)] == program[(diger, g, s)])

    # E. Zorunlu Gün (Varsa)
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

    # F. Kapasite (Yüksek)
    for g in gunler:
        for s in seanslar: model.Add(sum(program[(d, g, s)] for d in tum_dersler) <= DERSLIK_SAYISI)


    # --- 4. SOFT CONSTRAINTS (TERCİHLER - PUANLAMA) ---
    puanlar = []

    # A. Öğrenci Günlük Yük Dengesi (Günde 2 ders ideal, 3 olursa ceza)
    for b in bolumler:
        for sin in siniflar:
            ilgili = [d for d in tum_dersler if ders_detaylari[d]['bolum']==b and ders_detaylari[d]['sinif']==sin]
            if ilgili:
                for g in gunler:
                    gunluk_toplam = sum(program[(d, g, s)] for d in ilgili for s in seanslar)
                    # Eğer ders sayısı > 2 ise ceza uygula
                    # Boolean değişken: overload = (gunluk_toplam > 2)
                    overload = model.NewBoolVar(f'overload_{b}_{sin}_{g}')
                    model.Add(gunluk_toplam > 2).OnlyEnforceIf(overload)
                    model.Add(gunluk_toplam <= 2).OnlyEnforceIf(overload.Not())
                    puanlar.append(overload * -CEZA_OGRENCI_GUNLUK_3)

    # B. Hoca Tercihleri
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
            # Hoca o gün aktif mi?
            model.Add(g_toplam > 0).OnlyEnforceIf(hoca_gun_aktif[(h, g_idx)])
            model.Add(g_toplam == 0).OnlyEnforceIf(hoca_gun_aktif[(h, g_idx)].Not())
            
            # İstenmeyen gün cezası
            if g in istenmeyenler:
                puanlar.append(hoca_gun_aktif[(h, g_idx)] * -CEZA_HOCA_ISTENMEYEN_GUN * kidem)

        # Ardışık Gün Ödülü
        for g_idx in range(4):
            ard = model.NewBoolVar(f'ard_{h}_{g_idx}')
            model.AddBoolAnd([hoca_gun_aktif[(h, g_idx)], hoca_gun_aktif[(h, g_idx+1)]]).OnlyEnforceIf(ard)
            puanlar.append(ard * ODUL_ARDISIK_GUN * kidem)

        # Delik Deşik Gün Cezası
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
    st.info("Eğer şablonunuz hazırsa yükleyin.")
    # Not: Şablon indirme fonksiyonu yukarıda sadeleştirildi, 
    # V12.0'daki şablonunuzu kullanmaya devam edebilirsiniz.

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
                    
                    # RAPORLAMA
                    st.subheader("⚠️ İdeal Olmayan Durumlar (Mecburen Yapılanlar)")
                    gunler = ['Pazartesi', 'Sali', 'Carsamba', 'Persembe', 'Cuma']
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
                                        st.warning(f"{b} {sin}. Sınıf -> {g} günü {toplam} ders var.")

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
                                            icerik = f"{d}\n{detay['hoca']}"
                                            if detay['ortak_id']: icerik += f"\n(Ort: {detay['ortak_id']})"
                                            df_matrix.at[(g, s), detay['sinif']] = icerik
                        
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
                        file_name="Final_Program_V13.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                    
                else:
                    st.error("❌ Çözüm bulunamadı. Lütfen 'Ortak Ders ID'lerin doğru girildiğinden emin olun.")
                    st.error("İpucu: Eğer bir hoca 2 farklı bölümde BİRLEŞTİREREK ders yapacaksa, ikisine de AYNI 'OrtakDersID'yi yazmalısınız.")
            except Exception as e:
                st.error(f"Hata: {e}")
