import json
import math
import urllib.parse
import urllib.request
from datetime import date

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Farmakogenetik Fenokonversiyon Portalı V2",
    page_icon="🧬",
    layout="wide",
)


GENES = {
    "CYP2D6": {
        "title": "CYP2D6 — İlaç metabolizması",
        "gene_id": "1565",
        "alleles": {"*1": 1.0, "*2": 1.0, "*4": 0.0, "*5": 0.0, "*9": 0.5, "*10": 0.25, "*17": 0.5, "*29": 0.5, "*41": 0.5},
        "drugs": {
            "Kodein (ön ilaç)": "prodrug",
            "Tramadol (ön ilaç)": "prodrug",
            "Metoprolol": "active",
            "Amitriptilin": "active",
        },
        "inhibitors": {
            "Fluoksetin": 2.0,
            "Paroksetin": 2.0,
            "Bupropion": 2.0,
            "Duloksetin": 1.0,
            "Terbinafin": 1.0,
        },
        "phenotype": [(0, 0, "Poor"), (0.25, 1.0, "Intermediate"), (1.25, 2.25, "Normal"), (2.25, 99, "Ultrarapid")],
        "note": "CYP2D6 için kopya sayısı ve hibrit aleller sonucu değiştirebilir; bu demo CNV çözümlemesi yapmaz.",
    },
    "CYP2C19": {
        "title": "CYP2C19 — Antiplatelet ve PPI metabolizması",
        "gene_id": "1557",
        "alleles": {"*1": 1.0, "*2": 0.0, "*3": 0.0, "*9": 0.5, "*10": 0.5, "*17": 1.5},
        "drugs": {
            "Klopidogrel (ön ilaç)": "prodrug",
            "Omeprazol": "active",
            "Lansoprazol": "active",
            "Escitalopram": "active",
        },
        "inhibitors": {"Fluvoksamin": 2.0, "Fluoksetin": 1.0, "Omeprazol": 1.0, "Esomeprazol": 1.0},
        "phenotype": [(0, 0, "Poor"), (0.5, 0.5, "Intermediate"), (1.0, 1.0, "Normal"), (1.5, 1.5, "Rapid"), (2.0, 99, "Ultrarapid")],
        "note": "*17 ile işlevsiz bir alelin birlikte bulunduğu bazı diplotipler kılavuza göre ayrıca ele alınmalıdır.",
    },
    "CYP2C9": {
        "title": "CYP2C9 — Varfarin ve NSAİİ metabolizması",
        "gene_id": "1559",
        "alleles": {"*1": 1.0, "*2": 0.5, "*3": 0.0, "*5": 0.0, "*6": 0.0, "*8": 0.5, "*11": 0.5},
        "drugs": {"Varfarin": "active", "Flurbiprofen": "active", "Meloksikam": "active", "Piroksikam": "active"},
        "inhibitors": {"Flukonazol": 2.0, "Amiodaron": 1.0, "Metronidazol": 1.0, "Sulfametoksazol": 1.0},
        "phenotype": [(0, 0, "Poor"), (0.5, 1.0, "Intermediate"), (1.5, 99, "Normal")],
        "note": "Varfarin değerlendirmesinde VKORC1, CYP4F2, yaş ve klinik değişkenler de gereklidir; tek başına CYP2C9 doz belirlemez.",
    },
    "SLCO1B1": {
        "title": "SLCO1B1 — Statin taşınması",
        "gene_id": "10599",
        "alleles": {"*1A": 1.0, "*1B": 1.0, "*5": 0.0, "*15": 0.5, "*17": 0.5, "*37": 1.0},
        "drugs": {"Simvastatin": "active", "Atorvastatin": "active", "Rosuvastatin": "active", "Pravastatin": "active"},
        "inhibitors": {"Siklosporin": 2.0, "Gemfibrozil": 1.0},
        "phenotype": [(0, 0.5, "Poor function"), (1.0, 1.0, "Decreased function"), (1.5, 99, "Normal function")],
        "note": "SLCO1B1 sonucu metabolizör fenotipi değil, taşıyıcı fonksiyonu olarak raporlanır.",
    },
}

BLOG_POSTS = [
    {
        "title": "Fenokonversiyon: Genotip neden her zaman fenotip değildir?",
        "category": "Temel kavramlar",
        "summary": "İnhibitör ilaçlar, inflamasyon ve organ fonksiyonları genetik olarak öngörülen enzim aktivitesini değiştirebilir. Bu değişime fenokonversiyon denir.",
        "points": ["Genotip başlangıç tahminidir.", "Eş zamanlı ilaçlar gerçek aktiviteyi azaltabilir.", "Yorum gen–ilaç çiftine özgü yapılmalıdır."],
        "query": "phenoconversion pharmacogenetics",
    },
    {
        "title": "Alel, varyant, diplotip ve aktivite skoru",
        "category": "Genetik sözlük",
        "summary": "Yıldız aleller bir veya daha fazla varyantı temsil edebilir. Anne ve babadan gelen iki alel diplotipi, işlev değerlerinin birleşimi ise aktivite skorunu oluşturur.",
        "points": ["SNP ile yıldız alel aynı kavram değildir.", "Bazı genlerde kopya sayısı önemlidir.", "Fenotip eşikleri gene göre değişir."],
        "query": "star allele diplotype activity score pharmacogenomics",
    },
    {
        "title": "CYP2D6 ve ön ilaçlar",
        "category": "Klinik örnek",
        "summary": "Kodein ve tramadol gibi bazı ilaçlar etkin metabolitlerine dönüşmek için CYP2D6 aktivitesine ihtiyaç duyar. Düşük aktivite, toksisiteden çok yetersiz yanıtla ilişkili olabilir.",
        "points": ["Ön ilaç ve aktif ilaç ayrımı önemlidir.", "İnhibitörler fenotipi değiştirebilir.", "Kopya sayısı ayrıca değerlendirilmelidir."],
        "query": "CYP2D6 codeine tramadol pharmacogenetics",
    },
    {
        "title": "CYP2C19 ve klopidogrel yanıtı",
        "category": "Klinik örnek",
        "summary": "CYP2C19 işlev kaybı alelleri klopidogrelin aktif metabolite dönüşümünü azaltabilir. Klinik öneri; fenotip, endikasyon ve güncel kılavuza bağlıdır.",
        "points": ["Klopidogrel bir ön ilaçtır.", "*2 ve *3 işlev kaybı alellerindendir.", "Sonuç tek başına tedavi değişikliği değildir."],
        "query": "CYP2C19 clopidogrel CPIC",
    },
    {
        "title": "Farmakogenetik kanıt nasıl okunur?",
        "category": "Araştırma okuryazarlığı",
        "summary": "Bir PubMed yayını bulunması klinik uygulanabilirlik anlamına gelmez. Kılavuz, çalışma tasarımı, popülasyon, etki büyüklüğü ve güncellik birlikte değerlendirilmelidir.",
        "points": ["Kılavuz ile tekil çalışma ayrılmalıdır.", "Kaynak sürümü ve erişim tarihi gösterilmelidir.", "Kanıt düzeyi açıkça yazılmalıdır."],
        "query": "pharmacogenomics clinical evidence guidelines",
    },
]


def phenotype_for(score, ranges):
    for low, high, label in ranges:
        if low <= score <= high:
            return label
    return "Belirsiz"


def shifted_phenotype(base_score, burden, ranges):
    effective_score = max(0.0, base_score - burden * 0.5)
    return effective_score, phenotype_for(effective_score, ranges)


def interpretation(gene, drug, drug_type, basal, final, burden):
    if burden == 0 and basal == final:
        return "Seçilen faktörlerle fenokonversiyon sinyali görülmedi."
    low_function = final in {"Poor", "Intermediate", "Poor function", "Decreased function"}
    if drug_type == "prodrug" and low_function:
        return f"{drug} için aktivasyon ve tedavi yanıtı azalabilir; ilgili güncel kılavuz değerlendirilmelidir."
    if low_function:
        return f"{drug} maruziyeti veya advers etki olasılığı artabilir; ilaca özgü kılavuz doğrulaması gerekir."
    return "Fonksiyon değişimi sınırlı görünüyor; sonuç yine de ilaca özgü kılavuzla yorumlanmalıdır."


@st.cache_data(ttl=3600, show_spinner=False)
def pubmed_search(gene, drug, limit=6):
    term = f'({gene}[Title/Abstract]) AND ({drug.split(" (")[0]}[Title/Abstract]) AND pharmacogen*'
    params = urllib.parse.urlencode({"db": "pubmed", "term": term, "retmode": "json", "retmax": limit, "sort": "pub date", "tool": "cyp_analiz_edu"})
    with urllib.request.urlopen(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}", timeout=8) as response:
        ids = json.load(response)["esearchresult"]["idlist"]
    if not ids:
        return []
    summary_params = urllib.parse.urlencode({"db": "pubmed", "id": ",".join(ids), "retmode": "json", "tool": "cyp_analiz_edu"})
    with urllib.request.urlopen(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{summary_params}", timeout=8) as response:
        data = json.load(response)["result"]
    return [{"pmid": pmid, "title": data[pmid].get("title", "Başlık yok"), "date": data[pmid].get("pubdate", "") } for pmid in ids]


st.title("🧬 Farmakogenetik Fenokonversiyon Portalı V2")
st.caption("Genotip, eş zamanlı ilaçlar ve klinik faktörlerin eğitim amaçlı birlikte incelenmesi")
st.warning("Bu uygulama eğitim/araştırma demosudur; tanı, reçete veya doz kararı vermez. Sonuçlar klinik kılavuz ve uzman değerlendirmesinin yerine geçmez.")

with st.sidebar:
    st.header("Analiz girdileri")
    gene = st.selectbox("Gen / sistem", list(GENES))
    info = GENES[gene]
    allele1 = st.selectbox("Alel 1", list(info["alleles"]), index=0)
    allele2 = st.selectbox("Alel 2", list(info["alleles"]), index=min(1, len(info["alleles"]) - 1))
    drug = st.selectbox("İlaç", list(info["drugs"]))
    selected_inhibitors = st.multiselect("Eş zamanlı inhibitörler", list(info["inhibitors"]))
    st.subheader("Klinik bağlam")
    hepatic = st.select_slider("Karaciğer fonksiyon bozukluğu", ["Yok", "Hafif", "Orta", "İleri"])
    inflammation = st.checkbox("Aktif ciddi inflamasyon/enfeksiyon")
    grapefruit = st.checkbox("Düzenli greyfurt tüketimi", disabled=gene != "CYP3A4")

base_score = info["alleles"][allele1] + info["alleles"][allele2]
basal = phenotype_for(base_score, info["phenotype"])
factor_rows = [{"Faktör": med, "Katkı": info["inhibitors"][med]} for med in selected_inhibitors]
hepatic_burden = {"Yok": 0.0, "Hafif": 0.25, "Orta": 0.5, "İleri": 1.0}[hepatic]
if hepatic_burden:
    factor_rows.append({"Faktör": f"Karaciğer bozukluğu ({hepatic})", "Katkı": hepatic_burden})
if inflammation:
    factor_rows.append({"Faktör": "İnflamasyon (genel, belirsizlik yüksek)", "Katkı": 0.25})
burden = sum(row["Katkı"] for row in factor_rows)
effective_score, final = shifted_phenotype(base_score, burden, info["phenotype"])

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "Klinik özet", "Grafikler", "Senaryo simülasyonu", "Varyant kütüphanesi",
    "Literatür", "Veri merkezi", "Araştırma merkezi"
])

with tab1:
    st.subheader(info["title"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Diplotip", f"{allele1}/{allele2}")
    c2.metric("Aktivite skoru", f"{base_score:g}")
    c3.metric("Bazal sınıf", basal)
    c4.metric("Tahmini son sınıf", final, delta=f"Etkin skor {effective_score:g}")
    message = interpretation(gene, drug, info["drugs"][drug], basal, final, burden)
    (st.warning if basal != final else st.info)(message)
    st.caption(info["note"])
    st.markdown(f"[NCBI Gene kaydını aç](https://www.ncbi.nlm.nih.gov/gene/{info['gene_id']}) · [ClinPGx üzerinde ara](https://www.pharmgkb.org/search?query={gene}) · [CPIC kılavuzlarını aç](https://cpicpgx.org/guidelines/)")

with tab2:
    st.subheader("Bazal ve faktörler sonrası karşılaştırma")
    chart = pd.DataFrame({"Durum": ["Genetik bazal", "Faktörler sonrası"], "Göreli aktivite": [base_score, effective_score]}).set_index("Durum")
    st.bar_chart(chart, color="#5B8FF9")
    st.subheader("Sonuca katkı yapan faktörler")
    if factor_rows:
        st.bar_chart(pd.DataFrame(factor_rows).set_index("Faktör"), color="#E8684A")
    else:
        st.info("Henüz ek faktör seçilmedi.")

with tab3:
    st.subheader("Eğitim amaçlı doz–maruziyet simülasyonu")
    dose = st.slider("Göreli doz", 25, 200, 100, 25)
    hours = list(range(0, 25, 2))
    normal_k = 0.18
    patient_k = max(0.04, normal_k * max(effective_score, 0.25) / 2)
    simulation = pd.DataFrame({
        "Saat": hours,
        "Referans profil": [dose * math.exp(-normal_k * h) for h in hours],
        "Seçilen senaryo": [dose * math.exp(-patient_k * h) for h in hours],
    }).set_index("Saat")
    st.line_chart(simulation)
    st.caption("Bu eğri gerçek bir PK modeli değildir; yalnızca metabolizma/taşıma farkının yönünü öğretmek için normalize edilmiştir.")

with tab4:
    rows = [{"Alel": allele, "İşlev değeri": score, "Seçildi": "✓" if allele in {allele1, allele2} else ""} for allele, score in info["alleles"].items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.caption("Alel işlev değerleri eğitimsel sadeleştirmedir. Nihai klinik kullanımda CPIC/PharmVar sürümü ve diplotip kuralları doğrulanmalıdır.")

with tab5:
    st.subheader(f"PubMed: {gene} + {drug}")
    if st.button("Güncel yayınları getir", type="primary"):
        try:
            papers = pubmed_search(gene, drug)
            if not papers:
                st.info("Bu sorguyla yayın bulunamadı.")
            for paper in papers:
                st.markdown(f"- [{paper['title']}](https://pubmed.ncbi.nlm.nih.gov/{paper['pmid']}/) — {paper['date']} · PMID: {paper['pmid']}")
        except Exception:
            st.error("PubMed'e şu anda ulaşılamadı. Bir süre sonra yeniden deneyin.")
    st.caption("Yayınlar NCBI E-utilities üzerinden getirilmektedir; listelenmesi klinik kanıt kalitesi değerlendirmesi değildir.")

with tab6:
    st.subheader("📥 Veri ve analiz çıktıları")
    analysis_record = {
        "olusturma_tarihi": date.today().isoformat(),
        "gen": gene,
        "ilac": drug,
        "alel_1": allele1,
        "alel_2": allele2,
        "diplotip": f"{allele1}/{allele2}",
        "aktivite_skoru": base_score,
        "bazal_sinif": basal,
        "etkin_skor": effective_score,
        "tahmini_son_sinif": final,
        "es_zamanli_inhibitorler": ", ".join(selected_inhibitors) or "Yok",
        "karaciger_fonksiyon_bozuklugu": hepatic,
        "inflamasyon_enfeksiyon": "Evet" if inflammation else "Hayır",
        "yorum": interpretation(gene, drug, info["drugs"][drug], basal, final, burden),
        "kullanim": "Yalnızca eğitim ve araştırma amaçlıdır",
    }
    analysis_csv = pd.DataFrame([analysis_record]).to_csv(index=False).encode("utf-8-sig")
    analysis_json = json.dumps(analysis_record, ensure_ascii=False, indent=2).encode("utf-8")
    report_text = "\n".join(["FARMAKOGENETİK EĞİTİM RAPORU", "=" * 35] + [f"{key}: {value}" for key, value in analysis_record.items()])
    c1, c2, c3 = st.columns(3)
    c1.download_button("Analizi CSV indir", analysis_csv, f"{gene}_{drug.split(' (')[0]}_analiz.csv", "text/csv")
    c2.download_button("Analizi JSON indir", analysis_json, f"{gene}_{drug.split(' (')[0]}_analiz.json", "application/json")
    c3.download_button("Raporu TXT indir", report_text.encode("utf-8"), f"{gene}_egitim_raporu.txt", "text/plain")

    library_rows = []
    for gene_name, gene_info in GENES.items():
        for allele, function_value in gene_info["alleles"].items():
            library_rows.append({
                "Gen": gene_name,
                "Alel": allele,
                "Eğitimsel işlev değeri": function_value,
                "NCBI Gene ID": gene_info["gene_id"],
                "Sınırlama": gene_info["note"],
            })
    library_df = pd.DataFrame(library_rows)
    st.subheader("Alel veri seti")
    st.dataframe(library_df, width="stretch", hide_index=True)
    st.download_button("Tüm alel veri setini CSV indir", library_df.to_csv(index=False).encode("utf-8-sig"), "farmakogenetik_alel_verisi_v2_1.csv", "text/csv")
    st.info("İndirilen veriler eğitimsel ve sadeleştirilmiştir. Klinik kullanım öncesinde güncel CPIC, PharmVar ve ClinPGx kaynaklarıyla doğrulanmalıdır.")

with tab7:
    st.subheader("📰 Araştırma ve öğrenme merkezi")
    category = st.selectbox("Konu filtresi", ["Tümü"] + sorted({post["category"] for post in BLOG_POSTS}))
    visible_posts = BLOG_POSTS if category == "Tümü" else [post for post in BLOG_POSTS if post["category"] == category]
    for post in visible_posts:
        with st.expander(f"{post['title']} · {post['category']}"):
            st.write(post["summary"])
            for point in post["points"]:
                st.markdown(f"- {point}")
            query = urllib.parse.quote_plus(post["query"])
            st.markdown(f"[Bu konu için PubMed araştırmalarını aç](https://pubmed.ncbi.nlm.nih.gov/?term={query})")
    st.caption("Bu kısa yazılar eğitim amaçlı özgün özetlerdir; tıbbi öneri veya sistematik literatür değerlendirmesi değildir.")

st.divider()
st.caption(f"V2.1 · Veri sürümü: {date.today().isoformat()} · Kural tabanlı eğitim aracı · Sonuçlar kaynak sürümü ve klinik bağlamla doğrulanmalıdır.")
