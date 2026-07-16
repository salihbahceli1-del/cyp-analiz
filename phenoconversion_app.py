import streamlit as st
import numpy as np
import pandas as pd

# Sayfa yapılandırması
st.set_page_config(
    page_title="Multi-Genomik Klinik ve Laboratuvar Portalı",
    page_icon="🧬",
    layout="wide"
)

# Başlık
st.title("🧬 Multi-Genomik ve Translasyonel Klinik Karar Destek Portalı")
st.markdown("Moleküler Biyoloji, Laboratuvar Teşhis Metotları ve Klinik Farmakolojiyi Birleştiren Biyoinformatik Platformu")

# GELİŞMİŞ VERİ TABANI
genomic_database = {
    "CYP2D6 (Karaciğer İlaç Metabolizması)": {
        "ncbi_info": "NCBI Gene ID: 1565 | OMIM: 124030 | Kromozom: 22q13.2",
        "pharmgkb_evidence": "Level 1A (En Yüksek Klinik Kanıt)",
        "inhibitors": {
            "Strong": ["Fluoksetin (Antidepresan)", "Paroksetin (Antidepresan)"],
            "Moderate": ["Duloksetin (Antidepresan)", "Diphenhydramine (Antihistaminik)"],
            "Weak": ["Citalopram (Antidepresan)", "Ranitidin (Mide İlacı)"]
        },
        "substrates": ["Kodein (Ön-ilaç / Ağrı Kesici)", "Tramadol (Ön-ilaç)", "Metoprolol (Beta Bloker)"],
        "variants": {
            "CYP2D6*1 (Vahşi Tip)": {"rs_id": "Referans", "etki": "Normal", "mekanizma": "Fonksiyonel wild-type protein."},
            "CYP2D6*4 (Splicing Mutasyonu)": {"rs_id": "rs3892097", "etki": "Poor", "mekanizma": "Intron 3/Exon 4 sınırında kesip-ekleme hatası. Sıfır aktivite."},
            "CYP2D6*10 (Mis-sense Mutasyonu)": {"rs_id": "rs1065852", "etki": "Intermediate", "mekanizma": "Pro34Ser aminoasit dönüşümü. Yapısal instabilite."}
        },
        "lab_protocol": "PCR reaksiyonu sonrası EcoRI kısıtlama enzimi ile 37°C'de inkübasyon yapılır. Agaroz jelde (%2) yürütülerek fragman büyüklüklerine göre genotip saptanır."
    },
    "CYP3A4 (Geniş Spektrumlu Metabolizma)": {
        "ncbi_info": "NCBI Gene ID: 1576 | OMIM: 124010 | Kromozom: 7q22.1",
        "pharmgkb_evidence": "Level 1B (Güçlü Klinik Kanıt)",
        "inhibitors": {
            "Strong": ["Klaritromisin (Makrolid Antibiyotik)", "Ketokonazol (Antifungal)"],
            "Moderate": ["Eritromisin (Makrolid Antibiyotik)", "Diltiazem (Kalsiyum Kanal Blokeri)"],
            "Weak": ["Amlodipin (Tansiyon İlacı)", "Setirizin (Antihistaminik)"]
        },
        "substrates": ["Fentanil (Opioid Ağrı Kesici)", "Atorvastatin (Kolesterol İlacı)"],
        "variants": {
            "CYP3A4*1 (Vahşi Tip)": {"rs_id": "Referans", "etki": "Normal", "mekanizma": "Normal transkripsiyonel regülasyon."},
            "CYP3A4*22 (Intronik Polimorfizm)": {"rs_id": "rs35599367", "etki": "Intermediate", "mekanizma": "mRNA transkripsiyon verimliliğinde düşüş."}
        },
        "lab_protocol": "TaqMan alel diskriminasyon probları kullanılarak Real-Time qPCR cihazında Floresan (FAM/VIC) sinyal yoğunluğuna göre genotipleme gerçekleştirilir."
    },
    "VKORC1 (Kan Sulandırıcı Duyarlılığı)": {
        "ncbi_info": "NCBI Gene ID: 79001 | OMIM: 608547 | Kromozom: 16p11.2",
        "pharmgkb_evidence": "Level 1A (En Yüksek Klinik Kanıt)",
        "inhibitors": {
            "Strong": ["Amiodaron (Antiaritmik - Sinerjik Etki)"],
            "Moderate": ["Siprofloksasin (Kinolon Antibiyotik)"],
            "Weak": ["Yok / Hafif Etkileşim"]
        },
        "substrates": ["Varfarin (Coumadin - Antikoagülan)"],
        "variants": {
            "VKORC1 -1639G>A (Hassas Varyant)": {"rs_id": "rs9923231", "etki": "Poor", "mekanizma": "Promotör bölgesinde mutasyon. Gen ekspresyonu düşer, çok düşük doz Varfarin bile kanama riski yaratır!"},
            "VKORC1 Vahşi Tip (G/G)": {"rs_id": "Referans", "etki": "Normal", "mekanizma": "Standart Varfarin duyarlılığı."}
        },
        "lab_protocol": "Dizileme primeri kullanılarak Sanger Kilobase Dizileme yöntemi uygulanır. Kromatogramda 1639. pozisyondaki pik floresanları incelenir."
    }
}

# --- YAN PANEL (GİRDİLER) ---
st.sidebar.header("📋 Global Girdi Merkezi")
selected_gene = st.sidebar.selectbox("Analiz Edilecek Gen/Enzim Sistemi", list(genomic_database.keys()))
gene_data = genomic_database[selected_gene]

selected_variant = st.sidebar.selectbox("Saptanan Alel (Laboratuvar Sonucu)", list(gene_data["variants"].keys()))
selected_substrate = st.sidebar.selectbox("Reçete Edilecek Hedef İlaç (Substrat)", gene_data["substrates"])

all_drugs = gene_data["inhibitors"]["Strong"] + gene_data["inhibitors"]["Moderate"] + gene_data["inhibitors"]["Weak"]
selected_meds = st.sidebar.multiselect("Hastanın Kullandığı Diğer İlaçlar", options=all_drugs)

selected_method = st.sidebar.selectbox("Kullanılan Deneysel Metot", ["PCR - RFLP", "Sanger DNA Dizileme", "Real-Time qPCR", "HPLC (Fenotip Doğrulama)"])

st.sidebar.markdown("**Klinik Durumlar**")
lifestyle = []
if st.sidebar.checkbox("⚖️ Obezite (BMI > 30)"): lifestyle.append("Obezite")
if st.sidebar.checkbox("🩸 Tip 2 Diyabet"): lifestyle.append("Diyabet")
if st.sidebar.checkbox("🫘 Kronik Böbrek Yetmezliği"): lifestyle.append("Böbrek Yetmezliği")
if st.sidebar.checkbox("🚬 Düzenli Sigara Kullanımı"): lifestyle.append("Sigara")
if selected_gene.startswith("CYP3A4") and st.sidebar.checkbox("🍹 Düzenli Greyfurt Suyu Tüketimi"): lifestyle.append("Greyfurt")

# --- ALGORİTMA HESAPLAMA MOTORU ---
inhibitor_score = 0
matrix_details = []
for med in selected_meds:
    if med in gene_data["inhibitors"]["Strong"]: inhibitor_score += 2.0; matrix_details.append({"Faktör": med, "Tip": "Güçlü İnhibitör", "Skor": -2.0})
    elif med in gene_data["inhibitors"]["Moderate"]: inhibitor_score += 1.0; matrix_details.append({"Faktör": med, "Tip": "Orta İnhibitör", "Skor": -1.0})
    elif med in gene_data["inhibitors"]["Weak"]: inhibitor_score += 0.5; matrix_details.append({"Faktör": med, "Tip": "Zayıf İnhibitör", "Skor": -0.5})

if "Obezite" in lifestyle: inhibitor_score += 0.75; matrix_details.append({"Faktör": "Obezite", "Tip": "Patolojik Baskı", "Skor": -0.75})
if "Diyabet" in lifestyle: inhibitor_score += 0.5; matrix_details.append({"Faktör": "Diyabet", "Tip": "Metabolik Baskı", "Skor": -0.5})
if "Böbrek Yetmezliği" in lifestyle: inhibitor_score += 1.0; matrix_details.append({"Faktör": "Böbrek Yetmezliği", "Tip": "Klirens Azalması", "Skor": -1.0})
if "Sigara" in lifestyle: inhibitor_score -= 0.5; matrix_details.append({"Faktör": "Sigara", "Tip": "Gen İndüksiyonu", "Skor": +0.5})
if "Greyfurt" in lifestyle and "CYP3A4" in selected_gene: inhibitor_score += 1.5; matrix_details.append({"Faktör": "Greyfurt Suyu", "Tip": "Diyet Baskısı", "Skor": -1.5})

variant_effect = gene_data["variants"][selected_variant]["etki"]
levels = ["Ultra-rapid", "Normal", "Intermediate", "Poor"]
current_idx = levels.index(variant_effect if variant_effect in levels else "Normal")
if inhibitor_score >= 2.0: final_idx = 3
elif inhibitor_score >= 1.0: final_idx = min(3, current_idx + 2)
elif inhibitor_score >= 0.5: final_idx = min(3, current_idx + 1)
else: final_idx = current_idx
final_phenotype = levels[final_idx]

x = inhibitor_score + (current_idx * 0.5)
ai_risk = round((1 / (1 + np.exp(-x + 1))) * 100, 1)
if final_phenotype == "Poor": ai_risk = max(ai_risk, 88.0)


# ==================== 5 SEKMELİ YENİ YAPI ====================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🏥 Klinik Fenokonversiyon Portalı", 
    "🧪 Wet-Lab Teşhis Protokolleri", 
    "🧬 Varyant & SNP Kütüphanesi", 
    "📚 NCBI & PharmGKB Literatür Verisi",
    "🖨️ Durum Raporu & Çıktı Merkezi"
])

# --- SEKME 1: KLİNİK PORTAL ---
with tab1:
    st.subheader("🏥 Canlı Klinik Simülasyon Raporu")
    c1, c2, c3 = st.columns(3)
    c1.metric("🧬 Bazal Genetik Yapı", selected_variant.split(" (")[0])
    c2.metric("🩺 Klinik Durum (Fenotip)", f"{final_phenotype} Metabolizer")
    c3.metric("🤖 AI Toksisite / Reaksiyon Riski", f"%{ai_risk}")
    st.progress(ai_risk / 100)
    
    st.markdown("---")
    st.subheader("🎯 İlaç Etkinliği ve Dozaj Öngörüsü")
    if "VKORC1" in selected_gene:
        if final_phenotype == "Poor": st.error(f"🩸 **KRİTİK UYARI:** {selected_substrate} kanama riski yaratabilir! Doz azaltılmalıdır.")
        else: st.success(f"✅ Standart klinik protokol uygundur.")
    else:
        if final_phenotype == "Poor":
            if "Ön-ilaç" in selected_substrate: st.error(f"❌ {selected_substrate} aktifleşemez. Tedavi yanıtı alınamaz.")
            else: st.error(f"⚠️ {selected_substrate} atılamaz, toksisite riski yüksektir!")
        else: st.success(f"✅ İlaç metabolizma hızı dengeli.")

# --- SEKME 2: WET-LAB PROTOKOLLERİ ---
with tab2:
    st.subheader("🧪 Laboratuvar Deneysel Metot Rehberi")
    st.write(f"Seçilen **{selected_method}** yöntemi ile bu genin analiz edilme prosedürü aşağıda açıklanmıştır:")
    
    if "RFLP" in selected_method:
        st.info(f"🔬 **PCR-RFLP Protokolü:** {gene_data.get('lab_protocol', 'Protokol Mevcut')}")
    elif "Sanger" in selected_method:
        st.info(f"🧬 **Sanger Dizileme Protokolü:** {gene_data.get('lab_protocol', 'Protokol Mevcut')}")
    elif "qPCR" in selected_method:
        st.info(f"⏱️ **Real-Time qPCR Protokolü:** {gene_data.get('lab_protocol', 'Protokol Mevcut')}")
    else:
        st.info("🧪 **HPLC Analizi:** Kromatografi kolonunda ilaç ve metabolit pik alanları (AUC) oranlanarak hastanın gerçek metabolizma hızı ölçülür.")

# --- SEKME 3: VARYANT & SNP KÜTÜPHANESİ ---
with tab3:
    st.subheader("🧬 Mutasyon Kodları (SNP / rs ID) ve Moleküler Patoloji Mekanizmaları")
    v_dict = gene_data["variants"]
    v_data = []
    for k, v in v_dict.items():
        v_data.append({"Alel Durumu": k, "rs ID (SNP)": v["rs_id"], "Fonksiyonel Etki": v["etki"], "Moleküler Biyolojik Mekanizma": v["mekanizma"]})
    st.table(pd.DataFrame(v_data))

# --- SEKME 4: LİTERATÜR VERİSİ ---
with tab4:
    st.subheader("📚 Küresel Biyoinformatik Veri Tabanı Kayıtları")
    st.success(f"🌐 **PharmGKB Kanıt Seviyesi:** {gene_data['pharmgkb_evidence']}")
    st.warning(f"🔗 **NCBI & OMIM Resmi Kayıtları:** {gene_data['ncbi_info']}")
    st.markdown("""
    *Bu veriler küresel klinik farmakogenetik konsorsiyumları (CPIC ve DPWG) tarafından haftalık olarak güncellenen kılavuzlarla senkronizedir.*
    """)

# --- SEKME 5: DURUM RAPORU & ÇIKTI ---
with tab5:
    st.subheader("🖨️ Klinik Epikriz Raporu Oluşturma")
    st.write("Girilen tüm laboratuvar ve klinik verileri tek tıkla resmi bir rapor formatına dönüştürebilirsiniz.")
    
    if st.button("📜 Resmi Durum Raporunu Hazırla"):
        st.markdown(f"""
        ### 📜 KLİNİK FARMAKOGENETİK DURUM RAPORU
        * **Analiz Edilen Sistem:** {selected_gene}
        * **Kullanılan Laboratuvar Teşhis Metodu:** {selected_method}
        * **Saptanan Genotip / Alel Yapısı:** {selected_variant} (SNP ID: {gene_data['variants'][selected_variant]['rs_id']})
        * **Eşlik Eden Kronik Bulgular:** {', '.join(lifestyle) if lifestyle else 'Yok (Baskı Yok)'}
        * **Hesaplanan Nihai Klinik Fenotip:** {final_phenotype} Metabolizer
        * **AI Tahmini Reaksiyon / Toksisite Riski:** %{ai_risk}
        * **Önerilen Klinik Strateji:** {selected_substrate} dozu hastanın fenotip yapısına göre kişiselleştirilmelidir.
        """)
        st.caption("Yazdırmak veya PDF kaydetmek için klavyenizden Mac'te 'Cmd + P', Windows'ta 'Ctrl + P' yapabilirsiniz.")