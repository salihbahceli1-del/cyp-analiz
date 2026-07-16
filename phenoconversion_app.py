import json
import math
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

import pandas as pd
import streamlit as st
import altair as alt


st.set_page_config(
    page_title="Farmakogenetik Fenokonversiyon Portalı V3",
    page_icon="🧬",
    layout="wide",
)

ASSET_DIR = Path(__file__).parent / "assets"

st.markdown("""
<style>
.hero-kicker {color:#76d7ff; font-size:.82rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;}
.hero-title {font-size:2.25rem; line-height:1.08; font-weight:800; margin:.25rem 0 .6rem; color:#f7fbff;}
.hero-subtitle {font-size:1.04rem; line-height:1.6; color:#d8e9f5; max-width:860px;}
.hero-box {background:linear-gradient(135deg,#071b35 0%,#0b3554 55%,#123d52 100%); border:1px solid #275575; border-radius:22px; padding:1.45rem 1.65rem; margin-bottom:1rem; box-shadow:0 16px 40px rgba(2,18,38,.22);}
.step-card {height:100%; border-radius:18px; padding:1.15rem 1.2rem; border:1px solid rgba(52,125,167,.24); background:linear-gradient(145deg,rgba(231,247,255,.96),rgba(244,239,255,.96)); color:#14283a;}
.step-number {display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:50%; background:#0c6b9a; color:white; font-weight:800; margin-bottom:.55rem;}
.step-title {font-size:1.08rem; font-weight:800; margin-bottom:.45rem;}
.step-example {margin-top:.55rem; padding:.55rem .65rem; border-radius:10px; background:rgba(255,255,255,.72); font-size:.9rem;}
.article-lead {font-size:1.08rem; line-height:1.78; color:var(--text-color);}
</style>
""", unsafe_allow_html=True)

DRUG_INFO = {
    "Kodein (ön ilaç)": ("Opioid analjezik", "Hafif–orta şiddette ağrıda kullanılan bir ön ilaçtır. Analjezik etkisinin önemli bir bölümü CYP2D6 aracılığıyla morfine dönüşmesine bağlıdır. Düşük CYP2D6 işlevinde ağrı yanıtı yetersiz kalabilir; çok yüksek işlevde aktif metabolit maruziyeti ve ciddi opioid yan etkileri artabilir."),
    "Tramadol (ön ilaç)": ("Opioid etkili analjezik", "Orta şiddette ağrıda kullanılan, opioid ve monoaminerjik etkileri bulunan bir ilaçtır. CYP2D6 daha güçlü opioid etkili O-desmetiltramadol metabolitinin oluşumuna katkı sağlar. Düşük işlev etkinliği azaltabilir; yüksek işlev yan etki maruziyetini artırabilir."),
    "Metoprolol": ("Selektif beta-1 bloker", "Hipertansiyon, kalp hızı kontrolü, angina ve bazı kalp yetmezliği tablolarında kullanılır. CYP2D6 işlevinin azalması ilacın vücuttan uzaklaştırılmasını yavaşlatabilir; nabız düşmesi ve hipotansiyon gibi etkiler açısından klinik izlem önemlidir."),
    "Amitriptilin": ("Trisiklik antidepresan", "Depresyonun yanı sıra nöropatik ağrı ve migren profilaksisinde kullanılabilir. CYP2D6 ve CYP2C19 metabolizmaya farklı aşamalarda katkı sağlar. Değişen işlev, aktif ilaç/metabolit dengesini ve tolerabiliteyi etkileyebilir."),
    "Klopidogrel (ön ilaç)": ("P2Y12 antiplatelet", "Kalp krizi ve iskemik inme gibi trombotik olayların önlenmesinde trombosit aktivasyonunu azaltır. Etkinleşmesi için CYP2C19 dahil çeşitli enzimlerle aktif metabolite dönüşmesi gerekir. İşlev kaybı alelleri antiplatelet yanıtı azaltabilir."),
    "Omeprazol": ("Proton pompası inhibitörü", "Reflü, peptik ülser ve asit ilişkili hastalıklarda mide asidi üretimini azaltır. CYP2C19 metabolizmaya katkı sağlar; düşük işlev daha yüksek maruziyet ve daha güçlü/uzun asit baskılanmasıyla ilişkili olabilir."),
    "Lansoprazol": ("Proton pompası inhibitörü", "Reflü ve ülser gibi asit ilişkili hastalıklarda kullanılır. CYP2C19 aktivitesi ilacın uzaklaştırılmasını etkileyebilir; yorum tedavi amacı, doz ve klinik yanıta göre yapılır."),
    "Escitalopram": ("SSRI antidepresan", "Depresyon ve bazı anksiyete bozukluklarında serotonerjik iletimi düzenlemek amacıyla kullanılır. CYP2C19 metabolizmaya katkı sağlar; düşük işlev maruziyeti, yüksek işlev ise yetersiz düzey olasılığını etkileyebilir."),
    "Varfarin": ("Vitamin K antagonisti antikoagülan", "Pıhtı oluşumunu azaltmak için kullanılır ve dar terapötik aralığa sahiptir. CYP2C9, daha etkin S-varfarinin metabolizmasına katkı sağlar; ancak güvenli doz için VKORC1, CYP4F2, yaş, INR, beslenme ve etkileşen ilaçlar da gereklidir."),
    "Flurbiprofen": ("NSAİİ", "Ağrı ve inflamasyonu azaltır. CYP2C9 metabolizmaya katkı sağlar; düşük işlev maruziyet ve gastrointestinal, renal veya kanama ile ilişkili yan etkiler açısından önem taşıyabilir."),
    "Meloksikam": ("NSAİİ", "Kas-iskelet sistemi ağrısı ve inflamasyonda kullanılır. CYP2C9 metabolizmaya katkı sağlar; genetik sonuç böbrek fonksiyonu, ülser/kanama riski ve eş zamanlı ilaçlarla birlikte ele alınır."),
    "Piroksikam": ("NSAİİ", "Ağrı ve inflamasyonda kullanılan, uzun etkili bir NSAİİ'dir. CYP2C9 işlevinin azalması maruziyeti artırabilir; gastrointestinal ve renal güvenlik bağlamı ayrıca değerlendirilir."),
    "Simvastatin": ("HMG-CoA redüktaz inhibitörü", "LDL kolesterolü ve kardiyovasküler riski azaltmak amacıyla kullanılır. SLCO1B1'in kodladığı OATP1B1 taşıyıcısı hepatik alıma katkı sağlar; düşük taşıyıcı işlevi kas maruziyeti ve miyopati riskini artırabilir."),
    "Atorvastatin": ("HMG-CoA redüktaz inhibitörü", "LDL kolesterolü azaltır. Hepatik alımda taşıyıcılar rol oynar; SLCO1B1 işlevi, doz, etkileşen ilaçlar ve kas semptomları birlikte değerlendirilmelidir."),
    "Rosuvastatin": ("HMG-CoA redüktaz inhibitörü", "LDL kolesterolü azaltır ve taşınmasında çeşitli hepatik taşıyıcılar rol alır. SLCO1B1 sonucu tek başına risk veya doz kararı değildir; genetik köken ve diğer taşıyıcılar da önem taşıyabilir."),
    "Pravastatin": ("HMG-CoA redüktaz inhibitörü", "LDL kolesterolü azaltır. Karaciğere taşınması farmakolojik etki ve sistemik maruziyet açısından önemlidir; SLCO1B1 işlevi klinik ve ilaç etkileşimi bağlamında yorumlanır."),
}

GENE_EXPLANATIONS = {
    "CYP2D6": "Karaciğerde bulunan CYP450 enzimlerinden biridir ve birçok ilacın dönüşümüne katkı sağlar. CYP: aileyi, 2: gen ailesini, D: alt aileyi, 6: ilgili geni belirtir.",
    "CYP2C19": "Bazı antiplatelet, mide asidi azaltıcı ve psikiyatrik ilaçların metabolizmasında rol alan bir CYP450 enzimidir.",
    "CYP2C9": "Varfarin ve bazı NSAİİ'ler dahil çeşitli ilaçların hepatik metabolizmasına katkı sağlayan bir CYP450 enzimidir.",
    "SLCO1B1": "Bir enzim değil, karaciğer hücrelerine ilaç taşınmasına yardım eden OATP1B1 taşıyıcısını kodlayan gendir; özellikle statinlerle önemlidir.",
}

INHIBITOR_INFO = {
    "Fluoksetin": ("SSRI antidepresan", "CYP2D6 aktivitesini güçlü biçimde azaltabilir; genetik olarak normal bir kişide işlevsel aktivite daha düşük görünebilir."),
    "Paroksetin": ("SSRI antidepresan", "Güçlü CYP2D6 inhibitörüdür ve CYP2D6 substratlarının maruziyetini artırabilir."),
    "Bupropion": ("Antidepresan / sigara bırakma tedavisi", "CYP2D6'yı güçlü inhibe edebilir; eş zamanlı CYP2D6 ilaçları açısından önemlidir."),
    "Duloksetin": ("SNRI antidepresan", "CYP2D6 üzerinde orta düzey inhibitör etki gösterebilir."),
    "Terbinafin": ("Antifungal", "CYP2D6 inhibisyonu uzun sürebilir ve bazı substratların uzaklaştırılmasını yavaşlatabilir."),
    "Fluvoksamin": ("SSRI antidepresan", "CYP2C19 dahil birden fazla CYP enzimi üzerinde inhibitör etki gösterebilir."),
    "Omeprazol": ("Proton pompası inhibitörü", "CYP2C19 substratı olmasının yanında enzimi inhibe ederek bazı eş zamanlı ilaçları etkileyebilir."),
    "Esomeprazol": ("Proton pompası inhibitörü", "CYP2C19 inhibisyonu nedeniyle özellikle ön ilaç aktivasyonu bağlamında değerlendirilir."),
    "Flukonazol": ("Azol antifungal", "CYP2C9'u güçlü inhibe edebilir; varfarin gibi dar terapötik aralıklı ilaçlarda önemlidir."),
    "Amiodaron": ("Antiaritmik", "Birden fazla metabolik yolu etkileyebilir; CYP2C9 substratlarıyla klinik etkileşim gösterebilir."),
    "Metronidazol": ("Antimikrobiyal", "CYP2C9 ile ilişkili klinik etkileşimler, özellikle varfarin bağlamında önem taşıyabilir."),
    "Sulfametoksazol": ("Antibakteriyel kombinasyon bileşeni", "CYP2C9 inhibisyonu ve etkileşim potansiyeli nedeniyle birlikte kullanılan ilaçlar değerlendirilir."),
    "Siklosporin": ("İmmünsüpresan", "Hepatik taşıyıcıları inhibe ederek bazı statinlerin sistemik maruziyetini belirgin artırabilir."),
    "Gemfibrozil": ("Lipid düşürücü fibrat", "Statin taşınması/metabolizmasıyla etkileşebilir ve kas toksisitesi bağlamında önemlidir."),
}

PHENOTYPE_TR = {"Poor": "Zayıf", "Intermediate": "Ara", "Normal": "Normal", "Rapid": "Hızlı", "Ultrarapid": "Çok hızlı", "Poor function": "Düşük taşıyıcı işlevi", "Decreased function": "Azalmış taşıyıcı işlevi", "Normal function": "Normal taşıyıcı işlevi"}

ALLELE_FUNCTION_TR = {0.0: "İşlevsiz", 0.25: "Çok düşük işlev", 0.5: "Azalmış işlev", 1.0: "Normal işlev", 1.5: "Artmış işlev"}

def explain_allele(gene_name, allele, value):
    meaning = ALLELE_FUNCTION_TR.get(value, "Değişken işlev")
    return f"{allele}, {gene_name} geninin 'yıldız alel' adı verilen tanımlı bir sürümüdür. Bu uygulamada {value:g} işlev değeriyle ({meaning.lower()}) temsil edilir. Yıldız numarası önem sırası değildir; *17'nin *2'den daha iyi veya daha yeni olduğu anlamına gelmez."

PHENOTYPE_ORDER = {
    "Poor": 0, "Poor function": 0,
    "Intermediate": 1, "Decreased function": 1,
    "Normal": 2, "Normal function": 2,
    "Rapid": 3, "Ultrarapid": 4,
}

VARIANT_LIBRARY = {
    "CYP2D6*4 / rs3892097": {"gene": "CYP2D6", "type": "Splice-site", "dna": "c.506-1G>A", "protein": "İşlevsiz protein", "mechanism": "Kesip-ekleme bozukluğu", "effect": "İşlev kaybı", "method": "TaqMan, Sanger veya hedefli NGS"},
    "CYP2D6*10 / rs1065852": {"gene": "CYP2D6", "type": "Missense", "dna": "c.100C>T", "protein": "p.Pro34Ser", "mechanism": "Protein stabilitesi/aktivitesinde azalma", "effect": "Azalmış işlev", "method": "TaqMan, Sanger veya hedefli NGS"},
    "CYP2C19*2 / rs4244285": {"gene": "CYP2C19", "type": "Splice-site", "dna": "c.681G>A", "protein": "Aberan mRNA", "mechanism": "Kriptik splice bölgesi oluşumu", "effect": "İşlev kaybı", "method": "TaqMan, PCR-RFLP, Sanger"},
    "CYP2C19*17 / rs12248560": {"gene": "CYP2C19", "type": "Promotör", "dna": "-806C>T", "protein": "Ekspresyon artışı", "mechanism": "Transkripsiyonel aktivitede artış", "effect": "Artmış işlev", "method": "TaqMan veya Sanger"},
    "CYP2C9*2 / rs1799853": {"gene": "CYP2C9", "type": "Missense", "dna": "c.430C>T", "protein": "p.Arg144Cys", "mechanism": "Elektron transferi/katalitik aktivitede azalma", "effect": "Azalmış işlev", "method": "TaqMan, Sanger, hedefli NGS"},
    "CYP2C9*3 / rs1057910": {"gene": "CYP2C9", "type": "Missense", "dna": "c.1075A>C", "protein": "p.Ile359Leu", "mechanism": "Substrat bağlanması ve katalizde azalma", "effect": "Belirgin azalmış işlev", "method": "TaqMan, Sanger, hedefli NGS"},
    "SLCO1B1*5 / rs4149056": {"gene": "SLCO1B1", "type": "Missense", "dna": "c.521T>C", "protein": "p.Val174Ala", "mechanism": "Membran taşıyıcı işlevinde azalma", "effect": "Azalmış hepatik alım", "method": "TaqMan, Sanger, hedefli NGS"},
}

LAB_METHODS = {
    "PCR-RFLP": {"best": "Bilinen SNP restriksiyon bölgesi oluşturuyor/kaldırıyorsa", "output": "Jelde bant deseni", "limits": "Her varyant için uygun enzim bulunmayabilir; kontaminasyon ve kısmi kesim yanıltabilir."},
    "TaqMan qPCR": {"best": "Az sayıda bilinen alelin hızlı genotiplenmesi", "output": "FAM/VIC alelik ayrım kümeleri", "limits": "Yeni varyantları keşfetmez; prob tasarımı gerekir."},
    "Sanger dizileme": {"best": "Belirli bir amplikonun baz düzeyinde doğrulanması", "output": "Kromatogram ve dizi", "limits": "Düşük oranlı mozaikliği ve kompleks CNV/haplotipi sınırlı yakalar."},
    "Hedefli NGS": {"best": "Birden çok farmakogen ve varyantın paralel analizi", "output": "FASTQ/BAM/VCF ve kalite metrikleri", "limits": "Faz, psödogenler ve yapısal varyantlar özel tasarım ister."},
    "MLPA/qPCR CNV": {"best": "Gen delesyonu veya kopya sayısı", "output": "Göreli kopya sayısı", "limits": "Hangi kopyanın hangi yıldız alele ait olduğunu tek başına çözmeyebilir."},
    "Long-read": {"best": "Kompleks haplotip, hibrit gen ve faz çözümü", "output": "Uzun okumalar ve fazlanmış haplotipler", "limits": "Maliyet, analiz altyapısı ve doğrulama gereksinimi."},
}

GLOSSARY = {
    "Alel 1 / Alel 2": "Aynı genin iki kopyasını temsil eder; genellikle biri anneden, biri babadan gelir.",
    "Yıldız alel (*1, *2…)": "Bir veya daha fazla genetik varyantla tanımlanan, standart adlandırılmış haplotiptir. Numara tek başına iyi/kötü anlamına gelmez.",
    "Diplotip": "Bir kişide birlikte bulunan iki yıldız alelin birleşimidir; örneğin *1/*4.",
    "SNP": "DNA dizisindeki tek nükleotit farklılığıdır. Her SNP klinik açıdan anlamlı değildir.",
    "rsID": "dbSNP veritabanındaki varyant kimliğidir; örneğin rs3892097.",
    "Aktivite skoru": "Bazı farmakogenler için alel işlevlerinin sayısal birleşimidir; fenotip atamasına yardımcı olur.",
    "Fenotip": "Genetik ve çevresel etkenler sonucunda gözlenen/tahmin edilen enzim veya taşıyıcı işlev sınıfıdır.",
    "Fenokonversiyon": "İlaçlar, hastalık veya çevresel faktörler nedeniyle genetik tahmin ile işlevsel fenotipin farklılaşmasıdır.",
    "Substrat": "Bir enzim veya taşıyıcı tarafından işlenen ilaç/maddedir.",
    "İnhibitör": "Enzim veya taşıyıcı aktivitesini azaltabilen maddedir.",
    "İndükleyici": "Bazı enzimlerin miktarını veya aktivitesini artırabilen etkendir.",
    "Ön ilaç": "Farmakolojik etkisini göstermek için vücutta aktif metabolite dönüşmesi gereken ilaçtır.",
}


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


@st.cache_data(ttl=3600, show_spinner=False)
def clinvar_search(gene, limit=8):
    params = urllib.parse.urlencode({"db": "clinvar", "term": f"{gene}[gene] AND drug response[clinical significance]", "retmode": "json", "retmax": limit, "tool": "cyp_analiz_edu"})
    with urllib.request.urlopen(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?{params}", timeout=8) as response:
        ids = json.load(response)["esearchresult"]["idlist"]
    if not ids:
        return []
    summary_params = urllib.parse.urlencode({"db": "clinvar", "id": ",".join(ids), "retmode": "json", "tool": "cyp_analiz_edu"})
    with urllib.request.urlopen(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?{summary_params}", timeout=8) as response:
        result = json.load(response)["result"]
    records = []
    for uid in ids:
        item = result.get(uid, {})
        records.append({"uid": uid, "title": item.get("title", "ClinVar kaydı"), "accession": item.get("accession", ""), "updated": item.get("date_last_updated", "")})
    return records


st.title("🧬 Farmakogenetik Fenokonversiyon Portalı V3")
st.caption("Genotip, ilaçlar, yaşam biçimi ve klinik bağlamın eğitim amaçlı açıklanabilir analizi")
st.warning("Bu uygulama eğitim/araştırma demosudur; tanı, reçete veya doz kararı vermez. Sonuçlar klinik kılavuz ve uzman değerlendirmesinin yerine geçmez.")

with st.sidebar:
    st.header("Analiz girdileri")
    gene = st.selectbox("Gen / sistem", list(GENES))
    info = GENES[gene]
    gene_role = "Hepatik ilaç taşıyıcısı" if gene == "SLCO1B1" else "Sitokrom P450 ilaç metabolizma enzimi"
    st.caption(f"🧬 **{gene_role}:** {GENE_EXPLANATIONS[gene]}")
    if gene.startswith("CYP"):
        family_text = {"CYP2D6": "CYP = sitokrom P450; 2 = gen ailesi; D = alt aile; 6 = gen numarası.", "CYP2C19": "CYP = sitokrom P450; 2 = gen ailesi; C = alt aile; 19 = gen numarası.", "CYP2C9": "CYP = sitokrom P450; 2 = gen ailesi; C = alt aile; 9 = gen numarası."}[gene]
        st.caption(f"ℹ️ {family_text}")
    allele1 = st.selectbox("Alel 1", list(info["alleles"]), index=0)
    st.caption(f"🧬 {explain_allele(gene, allele1, info['alleles'][allele1])}")
    allele2 = st.selectbox("Alel 2", list(info["alleles"]), index=min(1, len(info["alleles"]) - 1))
    st.caption(f"🧬 {explain_allele(gene, allele2, info['alleles'][allele2])}")
    st.caption(f"**Neden iki alel?** Genin genellikle biri anneden, biri babadan gelen iki kopyası birlikte diplotipi oluşturur: {allele1}/{allele2}.")
    drug = st.selectbox("İlaç", list(info["drugs"]))
    selected_drug_class, selected_drug_description = DRUG_INFO[drug]
    selected_drug_type = "Ön ilaç" if info["drugs"][drug] == "prodrug" else "Aktif ilaç"
    st.caption(f"💊 **{selected_drug_class} · {selected_drug_type}**")
    st.caption(selected_drug_description)
    selected_inhibitors = st.multiselect("Eş zamanlı inhibitörler", list(info["inhibitors"]))
    if selected_inhibitors:
        st.markdown("**Seçilen inhibitörler ne yapar?**")
        for inhibitor in selected_inhibitors:
            inhibitor_class, inhibitor_note = INHIBITOR_INFO[inhibitor]
            strength = "Güçlü" if info["inhibitors"][inhibitor] >= 2 else "Orta"
            st.caption(f"🧪 **{inhibitor} — {inhibitor_class} · {strength} etki:** {inhibitor_note}")
    else:
        st.caption("İnhibitör; enzimin/taşıyıcının işlevini azaltabilen ilaçtır. Seçim yapıldığında etkisi burada açıklanır.")
    st.subheader("Klinik bağlam")
    age = st.number_input("Yaş", 18, 100, 40)
    weight = st.number_input("Kilo (kg)", 35.0, 250.0, 70.0, 1.0)
    height = st.number_input("Boy (cm)", 120.0, 220.0, 170.0, 1.0)
    hepatic = st.select_slider("Karaciğer fonksiyon bozukluğu", ["Yok", "Hafif", "Orta", "İleri"])
    renal = st.select_slider("Böbrek fonksiyon bozukluğu", ["Yok", "Hafif", "Orta", "İleri"])
    inflammation = st.checkbox("Aktif ciddi inflamasyon/enfeksiyon")
    diabetes = st.selectbox("Diyabet", ["Yok", "Tip 1", "Tip 2", "Gestasyonel/diğer"])
    cardiovascular = st.multiselect("Kalp-damar hastalıkları", ["Hipertansiyon", "Koroner arter hastalığı", "Kalp yetmezliği", "Ritim bozukluğu", "İnme öyküsü"])
    respiratory = st.multiselect("Solunum hastalıkları", ["Astım", "KOAH", "Uyku apnesi"])
    endocrine = st.multiselect("Endokrin/metabolik hastalıklar", ["Tiroid hastalığı", "Dislipidemi", "Metabolik sendrom", "Gut"])
    gi_conditions = st.multiselect("Sindirim sistemi", ["Reflü/ülser", "İnflamatuvar bağırsak hastalığı", "Malabsorpsiyon", "Bariatrik cerrahi öyküsü"])
    neuropsych = st.multiselect("Nörolojik/psikiyatrik", ["Depresyon/anksiyete", "Epilepsi", "Parkinson hastalığı", "Demans", "Kronik ağrı"])
    other_conditions = st.multiselect("Diğer önemli durumlar", ["Otoimmün hastalık", "Kanser/aktif tedavi", "Anemi", "Gebelik/emzirme", "Transplantasyon", "Çoklu ilaç kullanımı (≥5)"])
    smoking = st.selectbox("Sigara", ["Kullanmıyor", "Ara sıra", "Düzenli"])
    alcohol = st.selectbox("Alkol", ["Kullanmıyor", "Ara sıra", "Düzenli/yüksek"])

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
bmi = weight / ((height / 100) ** 2)
context_notes = []
if bmi >= 30:
    context_notes.append("Obezite (BMI ≥30): ilaç dağılımı ve eşlik eden hastalıklar açısından bağlamsal faktör; bu modelde enzime sabit puan verilmez.")
if diabetes != "Yok":
    context_notes.append(f"Diyabet ({diabetes}): glisemik kontrol, böbrek/karaciğer fonksiyonu ve eşlik eden ilaçlarla birlikte değerlendirilir; doğrudan CYP puanı değildir.")
if renal != "Yok":
    context_notes.append(f"Böbrek fonksiyon bozukluğu ({renal}): renal atılımı olan ilaçlar için önemlidir; otomatik CYP puanı olarak kullanılmaz.")
if smoking != "Kullanmıyor":
    context_notes.append("Sigara özellikle CYP1A2 indüksiyonuyla ilişkilidir; seçili genlere otomatik puan eklenmez.")
if alcohol != "Kullanmıyor":
    context_notes.append("Alkolün etkisi akut/kronik kullanım ve karaciğer durumuna bağlıdır; otomatik puan eklenmez.")
if age >= 65:
    context_notes.append("İleri yaş; organ fonksiyonu, çoklu ilaç kullanımı ve advers etki riski açısından ayrıca değerlendirilmelidir.")
condition_groups = {
    "Kalp-damar": cardiovascular,
    "Solunum": respiratory,
    "Endokrin/metabolik": endocrine,
    "Sindirim sistemi": gi_conditions,
    "Nörolojik/psikiyatrik": neuropsych,
    "Diğer": other_conditions,
}
for group, conditions in condition_groups.items():
    if conditions:
        context_notes.append(f"{group}: {', '.join(conditions)}. İlaç seçimi, organ fonksiyonu ve etkileşimler açısından ayrıca değerlendirilmelidir.")

if basal != final or burden >= 2:
    rule_level = "Yüksek"
elif burden >= 0.5 or context_notes:
    rule_level = "Orta / değerlendirme gerekli"
else:
    rule_level = "Düşük"

home, tab1, tab2, tab3, tab4, drug_tab, clinical_tab, variant_tab, mechanism_tab, wetlab_tab, star_tab, protein_tab, pathway_tab, population_tab, file_tab, tab5, tab6, tab7, glossary_tab = st.tabs([
    "Ana sayfa", "Klinik özet", "Grafikler", "Simülasyon", "Alel kütüphanesi",
    "İlaç & gen kartları", "Klinik faktörler", "Varyant anotasyonu", "DNA→RNA→Protein",
    "Sanal Wet-Lab", "Yıldız alel çözücü", "Protein", "Yolaklar", "Popülasyon genetiği",
    "Dosya analizi", "Literatür", "Veri merkezi", "Araştırma", "Sözlük"
])

with home:
    st.image(str(ASSET_DIR / "pharmacogenetics-hero-v1.png"), width="stretch")
    st.markdown("""
    <div class="hero-box">
      <div class="hero-kicker">Farmakogenetik · Fenokonversiyon · Açıklanabilir Eğitim</div>
      <div class="hero-title">Genetik yapıdan gerçek ilaç yanıtına</div>
      <div class="hero-subtitle">DNA'daki kalıtsal farklılıkların, ilaç metabolizmasının ve hastaya özgü klinik koşulların aynı karar zincirinde nasıl buluştuğunu inceleyen etkileşimli bir araştırma ve eğitim portalı.</div>
    </div>
    """, unsafe_allow_html=True)
    st.header("Farmakogenetik ve fenokonversiyon")
    st.markdown("""
    <div class="article-lead">
    Aynı ilacı aynı dozda kullanan iki kişide etkinlik ve advers etki profili farklı olabilir. Bu değişkenliğin bir bölümü yaş, organ fonksiyonları, beslenme ve eş zamanlı ilaçlarla; bir bölümü ise ilaç metabolizmasında, taşınmasında veya hedefe bağlanmasında görev alan genlerdeki kalıtsal farklılıklarla ilişkilidir. **Farmakogenetik**, bu genetik farklılıkların ilaç yanıtıyla ilişkisini inceleyen alandır.
    </div>

    İlaç vücuda alındıktan sonra emilim, dağılım, metabolizma ve atılım aşamalarından geçer. CYP2D6, CYP2C19 ve CYP2C9 gibi sitokrom P450 enzimleri birçok molekülün kimyasal dönüşümüne katkı sağlar. Bu dönüşüm aktif bir ilacın uzaklaştırılmasını kolaylaştırabileceği gibi, kodein veya klopidogrel örneklerinde olduğu gibi bir **ön ilacı** etkin metabolite de dönüştürebilir. Bu nedenle düşük enzim işlevi her zaman aynı klinik sonuca yol açmaz: aktif ilaçta maruziyet artabilirken, ön ilaçta etkinlik azalabilir.

    Genetik test çoğu zaman iki aleli ve bunların oluşturduğu diplotipi bildirir. Yıldız alellere atanan işlev değerleri bazı genlerde bir **aktivite skoruna**, skor da bazal fenotip sınıfına dönüştürülebilir. Ancak bu sonuç değişmez bir kader değildir. Güçlü enzim inhibitörleri, inflamasyon, karaciğer işlev bozukluğu ve başka çevresel etkenler genetik olarak öngörülen işlevi değiştirebilir. Genotipten beklenen fenotiple gözlenen işlev arasındaki bu farklılaşma **fenokonversiyon** olarak adlandırılır.
    """)
    st.subheader("Portal sonucu nasıl oluşturuyor?")
    c1, c2, c3 = st.columns(3)
    c1.markdown("""<div class="step-card"><div class="step-number">1</div><div class="step-title">Genetik başlangıç bulunur</div>Anne ve babadan gelen iki alelin işlev değerleri birleştirilir. Böylece diplotip, aktivite skoru ve genetik olarak beklenen bazal işlev sınıfı oluşturulur.<div class="step-example"><b>Örnek:</b> CYP2D6 *1 (1 puan) + *4 (0 puan) → skor 1 → ara metabolizör.</div></div>""", unsafe_allow_html=True)
    c2.markdown("""<div class="step-card"><div class="step-number">2</div><div class="step-title">Genetik dışı etkiler incelenir</div>Güçlü inhibitör ilaçlar, inflamasyon ve karaciğer işlevi enzimin gerçek aktivitesini azaltabilir. Diğer kronik durumlar yorum ve belirsizlik bağlamında gösterilir.<div class="step-example"><b>Örnek:</b> Normal genotip + güçlü CYP2D6 inhibitörü → işlevsel olarak daha düşük aktivite.</div></div>""", unsafe_allow_html=True)
    c3.markdown("""<div class="step-card"><div class="step-number">3</div><div class="step-title">Gerçek kaynaklarla doğrulanır</div>Bazal ve faktörler sonrası sınıf açıklanır; ardından ClinVar, PubMed, ClinPGx ve CPIC üzerindeki gerçek kayıtlar gösterilir.<div class="step-example"><b>İlke:</b> Kaynakta veri yoksa sistem sonuç uydurmaz ve “kayıt bulunamadı” der.</div></div>""", unsafe_allow_html=True)
    st.subheader("Bu eğitim portalının yaklaşımı")
    st.markdown("""
    Portal, seçilen iki alelden bazal işlev tahmini üretir; gen–ilaç çiftine ilişkin inhibitörleri ve klinik bağlamı aynı ekranda toplar. Grafikler genetik başlangıç ile faktörler sonrası eğitimsel etkin skoru karşılaştırır. Simülasyon bölümü metabolizma hızındaki değişimin konsantrasyon–zaman eğrisine olası yönsel etkisini anlatır; gerçek doz veya farmakokinetik tahmin yapmaz.

    Obezite, diyabet, böbrek hastalığı, kalp-damar hastalıkları, sigara ve alkol gibi durumlar önemlidir; ancak etkileri her gen ve ilaçta aynı değildir. Bu nedenle portal yalnızca tanımlanmış inhibitör, karaciğer işlevi ve inflamasyon için sadeleştirilmiş katkı kullanır. Diğer kronik durumları klinik bağlam ve belirsizlik olarak görünür hale getirir. Böylece bilimsel dayanağı olmayan kesin yüzdeler üretmek yerine, sonucun hangi bilgilerle oluştuğunu açıklar.
    """)
    st.subheader("Enzim, taşıyıcı ve ilaç hedefi aynı şey değildir")
    st.write("Enzimler ilaçları kimyasal olarak dönüştürür. SLCO1B1 gibi taşıyıcılar molekülün hücre içine veya dışına hareketine yardım eder. VKORC1 gibi ilaç hedefleri ise ilacın etki gösterdiği biyolojik yapıdır. Klinik yorum, ilgili genin bu rollerden hangisini taşıdığına göre yapılmalıdır.")
    st.subheader("Klinik kullanım ve sınırlamalar")
    st.write("Farmakogenetik sonuç; tanı, reçete veya doz kararını tek başına belirlemez. Endikasyon, yaş, organ fonksiyonları, eş zamanlı ilaçlar, laboratuvar sonuçları ve güncel kılavuz birlikte değerlendirilir. Bu portal eğitim ve araştırma amacıyla geliştirilmiş açıklanabilir bir prototiptir; doğrulanmış tıbbi cihaz veya yapay zekâ toksisite modeli değildir.")
    with st.expander("Neden klinik risk yüzdesi göstermiyoruz?"):
        st.write("Doğrulanmış bir klinik olasılık için temsil edici hasta verisi, açıkça tanımlanmış sonuç, bağımsız test, dış doğrulama ve kalibrasyon gerekir. Portalda böyle bir onaylı model bulunmadığından yapay yüzde kaldırılmıştır.")
        st.write("Bunun yerine her yorumun hangi alel kuralından geldiği ve gerçek ClinVar, PubMed, ClinPGx/PharmGKB ve CPIC kayıtları gösterilir. Kaynakta veri yoksa tahmin üretilmez.")
    st.subheader("Kullanılan bilgi kaynakları")
    sources = pd.DataFrame([
        ["NCBI Gene / dbSNP", "Gen kayıtları ve varyant kimlikleri", "https://www.ncbi.nlm.nih.gov/"],
        ["PubMed", "Biyomedikal yayın taraması", "https://pubmed.ncbi.nlm.nih.gov/"],
        ["ClinPGx / PharmGKB", "Gen–ilaç anotasyonları ve kılavuz bağlantıları", "https://www.pharmgkb.org/"],
        ["CPIC", "Farmakogenetik klinik uygulama kılavuzları", "https://cpicpgx.org/guidelines/"],
        ["PharmVar", "Farmakogen yıldız alel adlandırması", "https://www.pharmvar.org/"],
        ["ClinVar / Ensembl", "Klinik varyant ve genom anotasyonları", "https://www.ncbi.nlm.nih.gov/clinvar/"],
        ["PubChem", "İlaç ve kimyasal madde bilgileri", "https://pubchem.ncbi.nlm.nih.gov/"],
    ], columns=["Kaynak", "Portalda kullanım amacı", "Adres"])
    st.dataframe(sources, width="stretch", hide_index=True)
    st.caption("Kaynak bağlantısı bulunması, verinin otomatik olarak içe aktarıldığı veya klinik olarak doğrulandığı anlamına gelmez.")

with tab1:
    st.header("Klinik analiz özeti")
    st.write("Bu bölüm genetik başlangıcı, seçilen ilaç ve klinik faktörleri tek bir yorum zincirinde birleştirir. Sonuç eğitim amaçlıdır; reçete veya doz kararı değildir.")
    st.subheader(info["title"])
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Diplotip", f"{allele1}/{allele2}")
    c2.metric("Aktivite skoru", f"{base_score:g}")
    c3.metric("Bazal sınıf", PHENOTYPE_TR.get(basal, basal), basal)
    c4.metric("Tahmini son sınıf", PHENOTYPE_TR.get(final, final), f"Etkin skor {effective_score:g} · {final}")
    st.subheader("Genetik başlangıçtan nihai tahmine")
    factor_summary = ", ".join(row["Faktör"] for row in factor_rows) if factor_rows else "İşlevi azaltan ek faktör seçilmedi"
    change_text = "Daha düşük işleve kayma" if PHENOTYPE_ORDER.get(final, 2) < PHENOTYPE_ORDER.get(basal, 2) else "Daha yüksek işleve kayma" if PHENOTYPE_ORDER.get(final, 2) > PHENOTYPE_ORDER.get(basal, 2) else "Fenotip sınıfı değişmedi"
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr auto 1.25fr auto 1fr;gap:.65rem;align-items:stretch;margin:.7rem 0 1rem;">
      <div style="background:linear-gradient(145deg,#e0f2fe,#dbeafe);border:1px solid #7dd3fc;border-radius:18px;padding:1rem;text-align:center;color:#0c2942;">
        <div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;color:#0369a1;">GENETİK BAŞLANGIÇ</div>
        <div style="font-size:1.6rem;font-weight:850;margin:.35rem 0;">{PHENOTYPE_TR.get(basal, basal)}</div>
        <div>{allele1}/{allele2} · skor {base_score:g}</div>
      </div>
      <div style="display:flex;align-items:center;font-size:1.7rem;color:#64748b;">→</div>
      <div style="background:linear-gradient(145deg,#fff7ed,#ffedd5);border:1px solid #fdba74;border-radius:18px;padding:1rem;text-align:center;color:#43230c;">
        <div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;color:#c2410c;">ETKİLEYEN FAKTÖRLER</div>
        <div style="font-size:1rem;font-weight:750;margin:.42rem 0;">{factor_summary}</div>
        <div>Karaciğer: {hepatic} · İnflamasyon: {'Var' if inflammation else 'Yok'}</div>
      </div>
      <div style="display:flex;align-items:center;font-size:1.7rem;color:#64748b;">→</div>
      <div style="background:linear-gradient(145deg,#ede9fe,#f3e8ff);border:1px solid #c4b5fd;border-radius:18px;padding:1rem;text-align:center;color:#27104d;">
        <div style="font-size:.78rem;font-weight:800;letter-spacing:.08em;color:#6d28d9;">NİHAİ TAHMİN</div>
        <div style="font-size:1.6rem;font-weight:850;margin:.35rem 0;">{PHENOTYPE_TR.get(final, final)}</div>
        <div>Etkin skor {effective_score:g}</div>
      </div>
    </div>
    <div style="border-left:5px solid {'#ef4444' if 'düşük' in change_text.lower() else '#22c55e' if 'yüksek' in change_text.lower() else '#64748b'};background:rgba(148,163,184,.12);padding:.8rem 1rem;border-radius:8px;"><b>Karşılaştırma sonucu:</b> {change_text}</div>
    """, unsafe_allow_html=True)

    phenotype_labels = ["Zayıf", "Ara", "Normal", "Hızlı", "Çok hızlı"] if gene != "SLCO1B1" else ["Düşük", "Azalmış", "Normal"]
    max_position = len(phenotype_labels) - 1
    basal_position = min(PHENOTYPE_ORDER.get(basal, 2), max_position)
    final_position = min(PHENOTYPE_ORDER.get(final, 2), max_position)
    scale_rows = []
    for idx, label in enumerate(phenotype_labels):
        marker = "Bazal + Nihai" if idx == basal_position == final_position else "Bazal" if idx == basal_position else "Nihai" if idx == final_position else ""
        scale_rows.append({"Fenotip": label, "Konum": idx, "İşaret": marker})
    scale_df = pd.DataFrame(scale_rows)
    scale_base = alt.Chart(scale_df).mark_line(point=alt.OverlayMarkDef(filled=True, size=120), strokeWidth=6, color="#cbd5e1").encode(
        x=alt.X("Fenotip:N", sort=phenotype_labels, axis=alt.Axis(title=None, labelAngle=0)),
        y=alt.value(35),
        order="Konum:Q",
    ).properties(height=100)
    markers_df = pd.DataFrame([
        {"Fenotip": phenotype_labels[basal_position], "Tür": "Bazal", "Satır": 35},
        {"Fenotip": phenotype_labels[final_position], "Tür": "Nihai", "Satır": 35},
    ])
    markers = alt.Chart(markers_df).mark_point(filled=True, size=360, stroke="white", strokeWidth=2).encode(
        x=alt.X("Fenotip:N", sort=phenotype_labels), y=alt.Y("Satır:Q", axis=None),
        color=alt.Color("Tür:N", scale=alt.Scale(domain=["Bazal", "Nihai"], range=["#0284c7", "#7c3aed"]), legend=alt.Legend(title=None, orient="top")),
        tooltip=["Tür", "Fenotip"],
    )
    st.altair_chart(scale_base + markers, use_container_width=True)
    with st.expander("Aktivite skoru nedir?", expanded=True):
        st.write("Aktivite skoru, bazı farmakogenlerde iki alelin beklenen işlev değerlerinin toplamıdır. Genin DNA miktarını veya laboratuvar enzim düzeyini doğrudan ölçmez; genotipten fenotip sınıfı üretmek için kullanılan standartlaştırılmış bir yorum aracıdır.")
        st.info(f"Bu analizde: {allele1} = {info['alleles'][allele1]:g} puan, {allele2} = {info['alleles'][allele2]:g} puan. Toplam aktivite skoru {base_score:g}; bazal sınıf: {PHENOTYPE_TR.get(basal, basal)} ({basal}).")
        st.caption("Skor eşikleri gene özgüdür. Aynı sayı farklı bir gen için aynı fenotip anlamına gelmeyebilir.")
    st.metric("Fenokonversiyon için kural tabanlı değerlendirme", rule_level)
    st.info("Bu sınıf alel işlevi ve seçilen faktörlerin açıklanabilir kurallarla birleştirilmesidir; hasta sonucu veya klinik risk yüzdesi değildir.")
    st.subheader("Sonucun adım adım açıklaması")
    drug_kind_text = "ön ilaç" if info["drugs"][drug] == "prodrug" else "aktif ilaç"
    low_function = final in {"Poor", "Intermediate", "Poor function", "Decreased function"}
    if info["drugs"][drug] == "prodrug" and low_function:
        molecular_consequence = "Etkin metabolite dönüşüm azalabilir; ilaçtan beklenen yanıt yetersiz kalabilir."
        main_problem = "Temel sorun olası tedavi yanıtsızlığıdır; bu durum otomatik olarak toksisite anlamına gelmez."
    elif info["drugs"][drug] == "active" and low_function:
        molecular_consequence = "İlacın metabolizması/karaciğere taşınması azalabilir ve sistemik maruziyet uzayabilir veya artabilir."
        main_problem = "İlaca özgü advers etki ve tolerabilite açısından daha dikkatli değerlendirme gerekebilir."
    else:
        molecular_consequence = "Seçilen kurallara göre belirgin düşük işlev sınıfı oluşmadı."
        main_problem = "Bu sonuç risk olmadığı anlamına gelmez; genetik dışı etkenler ve ilaca özgü klinik koşullar ayrıca değerlendirilir."

    explanation_rows = [
        ["1 · Ne girdik?", f"{gene} için {allele1}/{allele2} diplotipi; hedef ilaç {drug} ({drug_kind_text})."],
        ["2 · Genetik ne söyledi?", f"Alel işlev değerleri {info['alleles'][allele1]:g} + {info['alleles'][allele2]:g} = {base_score:g}. Bazal tahmin: {PHENOTYPE_TR.get(basal, basal)} ({basal})."],
        ["3 · Neler etkiledi?", factor_summary + (f". Toplam eğitimsel baskı yükü: {burden:g}." if factor_rows else ".")],
        ["4 · Ne değişti?", f"Etkin skor {effective_score:g}; nihai tahmini sınıf {PHENOTYPE_TR.get(final, final)} (uluslararası terim: {final}). {change_text}."],
        ["5 · Moleküler anlamı", molecular_consequence],
        ["6 · Olası temel sorun", main_problem],
        ["7 · Sonuç", interpretation(gene, drug, info["drugs"][drug], basal, final, burden)],
        ["8 · Nasıl doğrulanır?", f"Genotip uygun bir yöntemle doğrulanmalı; güncel CPIC/ClinPGx kaydı, eş zamanlı ilaçlar, organ fonksiyonları ve klinik/laboratuvar bulguları birlikte incelenmelidir. {info['note']}"],
    ]
    st.dataframe(pd.DataFrame(explanation_rows, columns=["Soru", "Açıklama"]), width="stretch", hide_index=True)

    st.subheader("Kısa sonuç cümlesi")
    if basal != final:
        st.warning(f"{gene} {allele1}/{allele2} genotipi başlangıçta {PHENOTYPE_TR.get(basal, basal)} işlev öngörürken, seçilen faktörlerle {PHENOTYPE_TR.get(final, final)} işlev sınıfına kaymıştır. {molecular_consequence}")
    else:
        st.success(f"{gene} {allele1}/{allele2} için bazal ve faktörler sonrası sınıf {PHENOTYPE_TR.get(final, final)} olarak aynı kalmıştır. {molecular_consequence}")
    st.caption("Bu anlatım seçili girdilerin açıklanabilir özetidir; gerçek hastada klinik sonuç veya kesin tanı değildir.")
    message = interpretation(gene, drug, info["drugs"][drug], basal, final, burden)
    (st.warning if basal != final else st.info)(message)
    st.caption(info["note"])
    st.markdown(f"[NCBI Gene kaydını aç](https://www.ncbi.nlm.nih.gov/gene/{info['gene_id']}) · [ClinPGx üzerinde ara](https://www.pharmgkb.org/search?query={gene}) · [CPIC kılavuzlarını aç](https://cpicpgx.org/guidelines/)")
    with st.expander("Bu sonuç neden oluştu?"):
        st.write(f"{allele1} ({info['alleles'][allele1]:g}) + {allele2} ({info['alleles'][allele2]:g}) = {base_score:g} bazal aktivite skoru.")
        if factor_rows:
            for row in factor_rows:
                st.write(f"• {row['Faktör']}: eğitimsel baskı katkısı {row['Katkı']:g}")
        else:
            st.write("• İşlevi azaltan seçili inhibitör/puanlanmış faktör yok.")
        st.write(f"Etkin eğitimsel skor: {effective_score:g}. Değerlendirme: {rule_level}.")
        st.markdown("**Kaynağa dayalı doğrulama**")
        st.write("Bu hesap sonrasında Literatür sekmesindeki ClinVar, PubMed, ClinPGx ve CPIC kayıtlarıyla karşılaştırılmalıdır.")

with tab2:
    st.header("Analiz panosu")
    st.write("Genetik başlangıç, seçilen baskı faktörleri ve nihai eğitimsel işlev tahmini aynı ölçekte gösterilir.")
    activity_df = pd.DataFrame([
        {"Durum": "Genetik bazal", "Skor": base_score, "Sınıf": basal},
        {"Durum": "Faktörler sonrası", "Skor": effective_score, "Sınıf": final},
    ])
    activity_chart = alt.Chart(activity_df).mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=72).encode(
        x=alt.X("Durum:N", title=None, sort=["Genetik bazal", "Faktörler sonrası"]),
        y=alt.Y("Skor:Q", title="Göreli işlev skoru", scale=alt.Scale(domain=[0, max(2.5, base_score + .4)])),
        color=alt.Color("Durum:N", scale=alt.Scale(domain=["Genetik bazal", "Faktörler sonrası"], range=["#38bdf8", "#8b5cf6"]), legend=None),
        tooltip=["Durum", alt.Tooltip("Skor:Q", format=".2f"), "Sınıf"],
    ).properties(height=330)
    labels = alt.Chart(activity_df).mark_text(dy=-14, fontSize=15, fontWeight="bold").encode(x="Durum:N", y="Skor:Q", text=alt.Text("Skor:Q", format=".2f"))
    st.altair_chart(activity_chart + labels, use_container_width=True)
    delta = base_score - effective_score
    a, b, c = st.columns(3)
    a.metric("Bazal skor", f"{base_score:.2f}", basal)
    b.metric("Etkin skor", f"{effective_score:.2f}", final)
    c.metric("İşlev değişimi", f"-{delta:.2f}" if delta else "0.00", "Azalma" if delta else "Değişim yok")

    st.subheader("Faktörlerin işlev üzerindeki katkısı")
    contribution_rows = [{"Faktör": "Genetik başlangıç", "Değişim": base_score, "Tür": "Başlangıç"}]
    for row in factor_rows:
        contribution_rows.append({"Faktör": row["Faktör"], "Değişim": -min(row["Katkı"] * .5, base_score), "Tür": "Baskı"})
    if not factor_rows:
        contribution_rows.append({"Faktör": "Ek baskı seçilmedi", "Değişim": 0, "Tür": "Nötr"})
    contribution_df = pd.DataFrame(contribution_rows)
    contribution_chart = alt.Chart(contribution_df).mark_bar(cornerRadiusEnd=6).encode(
        y=alt.Y("Faktör:N", sort=None, title=None),
        x=alt.X("Değişim:Q", title="İşlev skoruna yönsel katkı"),
        color=alt.Color("Tür:N", scale=alt.Scale(domain=["Başlangıç", "Baskı", "Nötr"], range=["#22c55e", "#ef4444", "#94a3b8"]), legend=alt.Legend(title=None)),
        tooltip=["Faktör", alt.Tooltip("Değişim:Q", format="+.2f"), "Tür"],
    ).properties(height=max(180, len(contribution_df) * 48))
    st.altair_chart(contribution_chart, use_container_width=True)

    st.subheader("Grafiklerin yorumu")
    st.caption("Grafikler genotipten hesaplanan bazal işlev ile seçilen faktörler sonrası eğitimsel işlev sınıfını gösterir. Klinik olay olasılığı göstermez.")

with tab3:
    st.header("Karşılaştırmalı senaryo laboratuvarı")
    st.write("Aynı ilacın referans işlev ile seçilen genetik/klinik senaryodaki yönsel davranışını karşılaştır. Parametreler normalize edilmiştir; gerçek doz önerisi değildir.")
    p1, p2, p3 = st.columns(3)
    dose = p1.slider("Başlangıç dozu (normalize)", 25, 200, 100, 25)
    interval = p2.select_slider("İzlem süresi (saat)", [12, 24, 36, 48], value=24)
    repeat_doses = p3.selectbox("Doz sayısı", [1, 2, 3, 4], index=0)
    dose_interval = 12
    hours = [x / 2 for x in range(0, interval * 2 + 1)]
    reference_k = 0.18
    scenario_k = max(0.04, reference_k * max(effective_score, 0.25) / 2)

    def concentration_at(t, elimination_k):
        total = 0.0
        for n in range(repeat_doses):
            given_at = n * dose_interval
            if t >= given_at:
                total += dose * math.exp(-elimination_k * (t - given_at))
        return total

    sim_rows = []
    for hour in hours:
        sim_rows.append({"Saat": hour, "Profil": "Referans işlev", "Normalize konsantrasyon": concentration_at(hour, reference_k)})
        sim_rows.append({"Saat": hour, "Profil": "Seçilen senaryo", "Normalize konsantrasyon": concentration_at(hour, scenario_k)})
    sim_df = pd.DataFrame(sim_rows)
    line = alt.Chart(sim_df).mark_line(strokeWidth=4, interpolate="monotone").encode(
        x=alt.X("Saat:Q", title="Zaman (saat)"),
        y=alt.Y("Normalize konsantrasyon:Q", title="Normalize ilaç düzeyi"),
        color=alt.Color("Profil:N", scale=alt.Scale(domain=["Referans işlev", "Seçilen senaryo"], range=["#38bdf8", "#f97316"]), legend=alt.Legend(title=None, orient="top")),
        tooltip=[alt.Tooltip("Saat:Q", format=".1f"), "Profil", alt.Tooltip("Normalize konsantrasyon:Q", format=".1f")],
    ).properties(height=390)
    st.altair_chart(line, use_container_width=True)

    ref_values = sim_df[sim_df["Profil"] == "Referans işlev"]["Normalize konsantrasyon"].tolist()
    scenario_values = sim_df[sim_df["Profil"] == "Seçilen senaryo"]["Normalize konsantrasyon"].tolist()
    step = .5
    ref_auc = sum(ref_values) * step
    scenario_auc = sum(scenario_values) * step
    ref_half = math.log(2) / reference_k
    scenario_half = math.log(2) / scenario_k
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Referans AUC", f"{ref_auc:.0f}")
    m2.metric("Senaryo AUC", f"{scenario_auc:.0f}", f"%{((scenario_auc/ref_auc)-1)*100:+.0f}")
    m3.metric("Referans yarı ömür", f"{ref_half:.1f} sa")
    m4.metric("Senaryo yarı ömür", f"{scenario_half:.1f} sa", f"{scenario_half-ref_half:+.1f} sa")

    st.subheader("Eğri nasıl okunur?")
    if scenario_auc > ref_auc * 1.2:
        st.warning("Seçilen senaryoda normalize maruziyet referansın üzerinde. Aktif ilaçlarda bu yön daha yüksek maruziyeti; ön ilaçlarda ise ana ilaç ve aktif metabolit için farklı sonuçları temsil edebilir.")
    elif scenario_auc < ref_auc * .8:
        st.info("Seçilen senaryoda normalize maruziyet referansın altında.")
    else:
        st.success("Seçilen senaryo ile referans arasında belirgin yönsel maruziyet farkı oluşmadı.")
    st.caption("Bu tek bölmeli, normalize eğitim simülasyonudur. Emilim, dağılım hacmi, aktif metabolit, gerçek doz, yaşa özgü parametreler ve terapötik aralık modellenmez; klinik PK hesabı olarak kullanılamaz.")

with tab4:
    st.header("Alel kütüphanesi nasıl okunur?")
    st.write("Yıldız alel, bir gen üzerindeki bir veya daha fazla varyantın birlikte tanımladığı standart isimdir. *1 her zaman bütün genlerde aynı anlamı taşımaz; işlev değeri ve diplotip birlikte yorumlanır.")
    st.info("**Yıldız ve sayı ne demek?** `*1`, `*2`, `*4` veya `*17` bir başarı puanı ya da hastalık evresi değildir. PharmVar gibi kaynakların, belirli varyant kombinasyonlarına verdiği katalog adıdır. Örneğin CYP2C19*2 çoğunlukla işlev kaybıyla, CYP2C19*17 artmış işlevle ilişkilidir; fakat aynı numara başka bir gende aynı anlama gelmez.")
    st.markdown("""
    **Eğitimsel değer ne demek?** Bu uygulama alellerin beklenen işlevini hesaplayabilmek için sade bir sayı kullanır:

    - `0`: işlev yok veya çok düşük
    - `0,25–0,5`: azalmış işlev
    - `1`: normal işlev
    - `1,5`: artmış işlev

    İki alelin değeri toplanarak aktivite skoru elde edilir. Bu sayı gerçek kan enzimi ölçümü değildir; genotipi yorumlamak için kullanılan bir modeldir.
    """)
    function_text = lambda score: "Normal/yüksek işlev" if score >= 1 else "Azalmış işlev" if score > 0 else "İşlevsiz"
    rows = [{"Alel": allele, "Sade işlev": function_text(score), "Eğitimsel değer": score, "Bu analizde": "Alel 1 / 2" if allele1 == allele2 == allele else "Alel 1" if allele == allele1 else "Alel 2" if allele == allele2 else "—"} for allele, score in info["alleles"].items()]
    st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
    st.info(f"Seçilen diplotip: **{allele1}/{allele2}**. İki alelin eğitimsel toplamı: **{base_score:g}**. Tahmini bazal sınıf: **{PHENOTYPE_TR.get(basal, basal)}**.")
    st.caption("Alel işlev değerleri eğitimsel sadeleştirmedir. Klinik kullanımda güncel CPIC/PharmVar sürümü, kopya sayısı ve diplotip kuralları doğrulanmalıdır.")

with drug_tab:
    st.header("Gen ve ilaç monografisi")
    st.markdown(f"### {gene}: biyolojik rolü ve klinik önemi")
    st.info(GENE_EXPLANATIONS[gene])
    st.write(f"Bu analizde {gene}, **{drug}** ile birlikte değerlendiriliyor. Genetik başlangıç {allele1}/{allele2} diplotipi ve {base_score:g} aktivite skorudur.")
    st.markdown(f"### {drug}: ilaç profili")
    drug_class, drug_use = DRUG_INFO[drug]
    c1, c2, c3 = st.columns(3)
    c1.metric("İlaç sınıfı", drug_class)
    c2.metric("Molekül tipi", "Ön ilaç" if info["drugs"][drug] == "prodrug" else "Aktif ilaç")
    c3.metric("İlgili sistem", gene)
    st.write(drug_use)
    st.markdown("**Farmakogenetik yorumun yönü**")
    st.write(interpretation(gene, drug, info["drugs"][drug], basal, final, burden))
    if info["drugs"][drug] == "prodrug":
        st.warning("Ön ilaçlarda düşük enzim işlevi, her zaman toksisite değil; aktif metabolit oluşumunun ve tedavi yanıtının azalması anlamına gelebilir.")
    st.subheader("Eş zamanlı inhibitör bağlamı")
    if selected_inhibitors:
        for inhibitor in selected_inhibitors:
            cls, note = INHIBITOR_INFO[inhibitor]
            with st.expander(f"{inhibitor} · {cls}"):
                st.write(note)
                st.write(f"Bu eğitim modelindeki baskı ağırlığı: {info['inhibitors'][inhibitor]:g}.")
    else:
        st.info("Eş zamanlı inhibitör seçilmedi. Sol panelden seçim yapıldığında her ilacın sınıfı ve olası mekanizması burada açıklanır.")

with clinical_tab:
    st.header("Klinik bağlam ve kronik durumlar")
    st.write("Genetik sonuç ilaç yanıtının yalnızca bir parçasıdır. Organ fonksiyonu, hastalıklar, yaşam biçimi ve çoklu ilaç kullanımı maruziyeti veya tolerabiliteyi değiştirebilir. Aşağıdaki değerlendirme seçilen durumları görünür kılar; her hastalığı aynı CYP puanına dönüştürmez.")
    st.info("**Klinik faktör nedir?** Genin kendisi dışında ilaç yanıtını değiştirebilecek hasta özellikleridir. Örneğin böbrek işlevi ilacın atılmasını, karaciğer işlevi metabolizmayı, sigara bazı enzimlerin üretimini, eş zamanlı ilaçlar ise enzimin çalışmasını etkileyebilir.")
    st.markdown("**Bu bölümü nasıl kullanırsın?** Sol panelden gerçek veya örnek bir hastanın yaş, vücut ölçüsü, organ fonksiyonu, hastalık ve yaşam biçimi bilgilerini seç. Sistem bunları kesin hastalık puanına çevirmek yerine, hangi noktaların sonuç yorumunda ayrıca dikkate alınması gerektiğini açıklar.")
    c1, c2, c3 = st.columns(3)
    c1.metric("BMI", f"{bmi:.1f}", "Obezite" if bmi >= 30 else "Obezite yok")
    c2.metric("Karaciğer", hepatic)
    c3.metric("Böbrek", renal)
    if context_notes:
        for note in context_notes:
            st.warning(note)
    else:
        st.success("Seçilen bağlamda ek klinik belirsizlik işareti yok.")
    selected_condition_rows = []
    if diabetes != "Yok":
        selected_condition_rows.append(["Diyabet", diabetes])
    for group, conditions in condition_groups.items():
        for condition in conditions:
            selected_condition_rows.append([group, condition])
    if selected_condition_rows:
        st.subheader("Seçilen kronik durumlar")
        st.dataframe(pd.DataFrame(selected_condition_rows, columns=["Sistem", "Durum"]), width="stretch", hide_index=True)
    st.markdown("**Neden bütün faktörler puanlanmıyor?**")
    st.write("Obezite, diyabet, sigara, alkol ve böbrek hastalığının etkisi her gen–ilaç çiftinde aynı değildir. Yanlış kesinlik üretmemek için yalnızca seçili inhibitör, karaciğer işlevi ve inflamasyon eğitimsel etkin skora katılır; diğerleri yorumlanması gereken bağlam olarak gösterilir.")
    st.subheader("Klinik kontrol listesi")
    st.dataframe(pd.DataFrame([
        ["Karaciğer", hepatic, "Hepatik metabolizma ve ilk-geçiş etkisi"],
        ["Böbrek", renal, "İlaç/metabolit atılımı ve doz aralığı"],
        ["Diyabet", diabetes, "Organ fonksiyonu, glisemik durum ve eş ilaçlar"],
        ["BMI", f"{bmi:.1f}", "Dağılım hacmi ve eşlik eden metabolik durum"],
        ["Sigara", smoking, "Özellikle CYP1A2 indüksiyonu bağlamı"],
        ["Alkol", alcohol, "Akut/kronik kullanım ve karaciğer bağlamı"],
        ["İnflamasyon", "Var" if inflammation else "Yok", "Bazı CYP aktivitelerinde baskılanma olasılığı"],
    ], columns=["Faktör", "Seçilen durum", "Neden önemli?"]), width="stretch", hide_index=True)

with variant_tab:
    st.header("Varyant anotasyon laboratuvarı")
    st.write("Varyant anotasyonu, DNA'da bulunan bir değişikliğe biyolojik anlam ekleme işlemidir. 'Değişiklik nerede, RNA'yı veya proteini etkiliyor mu, gen işlevini artırıyor mu azaltıyor mu ve hangi deneyle doğrulanabilir?' sorularını yanıtlar.")
    st.info("**Amaç:** Yalnızca `rs3892097` gibi bir kod görmek yerine, bu kodun hangi gende olduğunu ve moleküler sonucunun ne olabileceğini anlamak.")
    selected_variant_record = st.selectbox("Örnek varyant", list(VARIANT_LIBRARY))
    vr = VARIANT_LIBRARY[selected_variant_record]
    v1, v2, v3, v4 = st.columns(4)
    v1.metric("Gen", vr["gene"])
    v2.metric("Varyant türü", vr["type"])
    v3.metric("DNA/HGVS", vr["dna"])
    v4.metric("İşlev", vr["effect"])
    st.dataframe(pd.DataFrame([
        ["DNA değişimi", vr["dna"]], ["RNA/protein sonucu", vr["protein"]],
        ["Moleküler mekanizma", vr["mechanism"]], ["Uygun yöntem", vr["method"]],
    ], columns=["Katman", "Anotasyon"]), width="stretch", hide_index=True)
    st.markdown("""
    **Tablodaki terimler:**

    - **HGVS:** DNA değişimini standart biçimde yazan adlandırma sistemi.
    - **Missense:** Bir aminoasidin başka bir aminoaside dönüşmesi.
    - **Splice-site:** RNA kesip-ekleme sürecinin bozulabilmesi.
    - **Promotör:** Genin ne kadar üretileceğini düzenleyen DNA bölgesi.
    - **Eksik bilgi:** Bu yerleşik özet, popülasyon frekansı, tüm transkriptler ve güncel klinik sınıflandırmayı tek başına içermez; canlı kaynaklardan doğrulanır.
    """)
    st.markdown(f"[dbSNP/NCBI'da ara](https://www.ncbi.nlm.nih.gov/snp/?term={urllib.parse.quote_plus(selected_variant_record.split('/')[-1].strip())}) · [ClinVar'da ara](https://www.ncbi.nlm.nih.gov/clinvar/?term={urllib.parse.quote_plus(selected_variant_record)}) · [Ensembl VEP](https://www.ensembl.org/Tools/VEP)")
    st.caption("Yerleşik kayıtlar eğitimsel özetlerdir; canlı klinik sınıflandırma için bağlantılı kaynakların güncel sürümü kullanılmalıdır.")

with mechanism_tab:
    st.header("DNA → RNA → protein → hücresel fenotip")
    st.write("Bu bölüm bir DNA değişikliğinin hücresel sonuca nasıl dönüşebileceğini adım adım gösterir. DNA talimattır; RNA bu talimatın okunmuş kopyasıdır; protein ise hücrede işi yapan üründür.")
    mech_variant = st.selectbox("Mekanizma varyantı", list(VARIANT_LIBRARY), key="mech_variant")
    mv = VARIANT_LIBRARY[mech_variant]
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:.7rem;margin:1rem 0;">
      <div class="step-card"><div class="step-title">1 · DNA</div><b>{mv['dna']}</b><br>{mv['type']} varyant</div>
      <div class="step-card"><div class="step-title">2 · RNA</div>{'Kesip-ekleme/transkript değişikliği' if 'Splice' in mv['type'] else 'Kodon veya ekspresyon değişikliği'}</div>
      <div class="step-card"><div class="step-title">3 · Protein</div>{mv['protein']}<br>{mv['mechanism']}</div>
      <div class="step-card"><div class="step-title">4 · Fenotip</div><b>{mv['effect']}</b><br>İlaç dönüşümü/taşınmasında değişim</div>
    </div>
    """, unsafe_allow_html=True)
    st.info("Bu zincir nedensel mekanizmayı öğretir; klinik etki ilacın ön ilaç/aktif ilaç olmasına ve diğer biyolojik faktörlere bağlıdır.")
    st.markdown("**Nasıl okunur?** Soldan sağa ilerle: önce DNA değişir; bu değişiklik RNA oluşumunu veya kodonu etkiler; protein miktarı/yapısı değişebilir; son olarak enzim ya da taşıyıcının işlevi ve ilaç yanıtı etkilenebilir. Her DNA değişikliği mutlaka protein veya hastalık etkisi oluşturmaz.")

with wetlab_tab:
    st.header("Sanal Wet-Lab ve yöntem seçici")
    st.write("Wet-lab, pipet, PCR cihazı, jel veya dizileme cihazıyla yapılan deneysel laboratuvar çalışmasıdır. Bu bölüm analiz etmek istediğin değişikliğe göre uygun yöntemi seçmeyi ve beklenen çıktıyı öğrenmeyi amaçlar.")
    st.markdown("**1 · Analiz hedefini seç:** Tek bir bilinen SNP mi, çok sayıda gen mi, yoksa kopya sayısı gibi büyük bir değişim mi arıyorsun?")
    lab_variant_type = st.selectbox("Analiz hedefi", ["Bilinen tek SNP", "Küçük indel", "Çoklu gen paneli", "Kopya sayısı/CNV", "Kompleks haplotip/hibrit gen"])
    recommendation = {"Bilinen tek SNP": "TaqMan qPCR", "Küçük indel": "Sanger dizileme", "Çoklu gen paneli": "Hedefli NGS", "Kopya sayısı/CNV": "MLPA/qPCR CNV", "Kompleks haplotip/hibrit gen": "Long-read"}[lab_variant_type]
    st.success(f"Önerilen başlangıç yöntemi: {recommendation}")
    st.markdown("**2 · Yöntemi incele:** Önerilen yöntemi kullanabilir veya alternatif bir yöntemi seçip avantaj–sınırlamalarını karşılaştırabilirsin.")
    method = st.selectbox("Yöntemi incele", list(LAB_METHODS), index=list(LAB_METHODS).index(recommendation))
    method_info = LAB_METHODS[method]
    st.dataframe(pd.DataFrame([["En uygun kullanım", method_info["best"]], ["Ana çıktı", method_info["output"]], ["Sınırlamalar", method_info["limits"]]], columns=["Başlık", "Açıklama"]), width="stretch", hide_index=True)
    st.markdown("**3 · Sonucu yorumla:** Çıktı bir jel bandı, floresan kümesi, kromatogram veya VCF olabilir. Tek başına cihaz çıktısı yeterli değildir; pozitif/negatif kontrol ve kalite ölçümleri gerekir.")
    if method == "PCR-RFLP":
        fragment = st.slider("PCR ürünü (bp)", 100, 1000, 400, 25)
        cut = st.slider("Kesim noktası (bp)", 25, fragment - 25, fragment // 2, 25)
        gel = pd.DataFrame({"Fragman": ["Kesilmemiş", "Kesilmiş A", "Kesilmiş B"], "bp": [fragment, cut, fragment-cut]})
        st.bar_chart(gel.set_index("Fragman"))
        st.caption("Bant boyları eğitimsel jel deseni olarak gösterilir; gerçek göç mesafesi logaritmiktir.")
    elif method == "TaqMan qPCR":
        clusters = pd.DataFrame({"Genotip": ["Ref/Ref", "Ref/Alt", "Alt/Alt"], "FAM": [10, 55, 90], "VIC": [90, 55, 10]})
        st.scatter_chart(clusters, x="FAM", y="VIC", color="Genotip")
    else:
        st.info("Bu prototip yöntemin karar mantığını ve beklenen çıktısını gösterir. Ham cihaz verisinin tam analizi ayrıca geliştirilebilir.")

with star_tab:
    st.header("Eğitimsel yıldız alel çözücü")
    st.write("Yıldız alel, bir gen üzerindeki bir veya daha fazla varyantın birlikte bulunduğu haplotipe verilen katalog adıdır. `*1`, `*2`, `*17` sıralama, şiddet veya sürüm numarası değildir.")
    st.info("**Örnek:** CYP2C19*2 genellikle işlev kaybı belirteçlerini; CYP2C19*17 ise artmış ekspresyonla ilişkili promotör değişikliğini temsil eder. İki kromozomdaki yıldız aleller birleşince *1/*2 gibi diplotip oluşur.")
    st.markdown("**Bu çözücü ne yapıyor?** Seçtiğin iki alel etiketini yan yana getirir ve yerleşik işlev değerlerini toplar. **Ne yapmıyor?** Ham VCF'den gerçek haplotip fazı, psödogen ayrımı veya kompleks CYP2D6 alel çağrımı yapmaz.")
    resolver_gene = st.selectbox("Gen", list(GENES), key="resolver_gene")
    observed = st.multiselect("Gözlenen alel belirteçleri", list(GENES[resolver_gene]["alleles"]), key="observed_markers")
    copy_number = st.selectbox("Kopya sayısı", [0, 1, 2, 3, "Bilinmiyor"], index=2)
    if len(observed) >= 2:
        candidate = f"{observed[0]}/{observed[1]}"
        st.success(f"Basitleştirilmiş diplotip adayı: {candidate}")
        st.write(f"Aktivite toplamı: {GENES[resolver_gene]['alleles'][observed[0]] + GENES[resolver_gene]['alleles'][observed[1]]:g}")
    elif observed:
        st.warning("Tek belirteç seçildi; ikinci haplotip ve faz bilgisi eksik.")
    else:
        st.info("En az bir belirteç seç. Sonuç doğrulanmış yıldız alel çağrımı değildir.")
    if copy_number != 2:
        st.warning("Kopya sayısı 2 değil veya bilinmiyor; basit iki-alel diplotip modeli yeterli olmayabilir.")

with protein_tab:
    st.header("Protein yapı ve fonksiyon stüdyosu")
    st.write("Aminoasit değişiminin yük, polarite, hidrofobiklik, aktif bölge ve membran yerleşimi üzerindeki olası etkisini düşünmek için bir yorum çerçevesi.")
    protein_variant = st.selectbox("Protein varyantı", [k for k,v in VARIANT_LIBRARY.items() if "p." in v["protein"]])
    pv = VARIANT_LIBRARY[protein_variant]
    st.info(f"{protein_variant}: {pv['protein']} — {pv['mechanism']}")
    st.dataframe(pd.DataFrame([
        ["Birincil yapı", "Aminoasit değişimi veya dizisel bozukluk"],
        ["Katlanma/stabilite", "Yan zincir özelliklerine göre değişebilir"],
        ["Kataliz/bağlanma", pv["mechanism"]],
        ["Hücresel sonuç", pv["effect"]],
    ], columns=["Düzey", "İncelenecek etki"]), width="stretch", hide_index=True)
    st.markdown(f"[UniProt'ta {pv['gene']} ara](https://www.uniprot.org/uniprotkb?query={pv['gene']}) · [AlphaFold DB](https://alphafold.ebi.ac.uk/search/text/{pv['gene']}) · [PDB](https://www.rcsb.org/search?request={{%22query%22:{{%22type%22:%22terminal%22,%22service%22:%22full_text%22,%22parameters%22:{{%22value%22:%22{pv['gene']}%22}}}}}})")

with pathway_tab:
    st.header("İlaç yolak ve sistem biyolojisi")
    st.write("Yolak, bir ilacın vücuda girişinden hücresel etkisine kadar ardışık biyolojik basamakların haritasıdır. Tek bir CYP geni bütün yanıtı açıklamaz; taşıyıcılar, Faz I/Faz II enzimleri, hedef proteinler ve immün sistem birlikte rol oynayabilir.")
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:.6rem;">
      <div class="step-card"><b>1 · Giriş</b><br>{drug}</div><div class="step-card"><b>2 · Taşıma</b><br>SLCO/ABC sistemleri</div>
      <div class="step-card"><b>3 · Faz I</b><br>{gene if gene.startswith('CYP') else 'CYP enzimleri'}</div><div class="step-card"><b>4 · Faz II/Hedef</b><br>UGT/GST/NAT veya reseptör</div>
      <div class="step-card"><b>5 · Sonuç</b><br>Aktif/inaktif metabolit ve hücresel yanıt</div>
    </div>""", unsafe_allow_html=True)
    network = pd.DataFrame([["Taşıyıcı", "SLCO1B1, ABCB1"], ["Faz I", "CYP2D6, CYP2C19, CYP2C9, CYP3A"], ["Faz II", "UGT, GST, NAT"], ["İlaç hedefi", "VKORC1, reseptör/enzimler"], ["İmmün yanıt", "HLA alelleri"]], columns=["Katman", "Örnek sistemler"])
    st.dataframe(network, width="stretch", hide_index=True)
    st.markdown("""
    **Basamakların anlamı:** Taşıyıcı ilacı hücreye sokar/çıkarır; Faz I enzimi molekülü oksidasyon gibi işlemlerle değiştirir; Faz II enzimi atılımı kolaylaştıran grup ekleyebilir; hedef protein ilacın farmakolojik etkisini oluşturur; HLA gibi immün genler bazı aşırı duyarlılık reaksiyonlarını etkileyebilir.
    """)

with population_tab:
    st.header("Popülasyon genetiği laboratuvarı")
    st.write("Popülasyon genetiği, tek bir hastayı değil bir gruptaki genetik çeşitliliği inceler. Bu araç, örneklemindeki Ref/Ref, Ref/Alt ve Alt/Alt birey sayılarını kullanarak alel frekanslarını ve Hardy–Weinberg altında beklenen genotip sayılarını hesaplar.")
    st.info("**Ref ne demek?** Referans alel, genom referans dizisindeki bazdır. **Alt ne demek?** Alternatif alel, gözlenen diğer bazdır. Ref/Alt birey heterozigot; Alt/Alt birey alternatif alel için homozigottur.")
    st.markdown("**Amaç:** Gözlenen genotip dağılımı, rastgele eşleşen ideal bir popülasyonda beklenen dağılıma yakın mı? Büyük farklar örnekleme, popülasyon yapısı, seçilim, akrabalık veya teknik hata gibi nedenlerle oluşabilir.")
    ref_hom = st.number_input("Ref/Ref birey", 0, 100000, 50)
    het = st.number_input("Ref/Alt birey", 0, 100000, 40)
    alt_hom = st.number_input("Alt/Alt birey", 0, 100000, 10)
    total_n = ref_hom + het + alt_hom
    if total_n:
        p = (2*ref_hom + het)/(2*total_n); q = 1-p
        expected = pd.DataFrame({"Genotip": ["Ref/Ref", "Ref/Alt", "Alt/Alt"], "Gözlenen": [ref_hom, het, alt_hom], "HWE beklenen": [p*p*total_n, 2*p*q*total_n, q*q*total_n]})
        st.bar_chart(expected.set_index("Genotip"))
        st.metric("Referans alel frekansı (p)", f"{p:.3f}"); st.metric("Alternatif alel frekansı (q)", f"{q:.3f}")
        chi = sum((o-e)**2/e for o,e in zip(expected["Gözlenen"], expected["HWE beklenen"]) if e > 0)
        st.write(f"Eğitimsel ki-kare istatistiği: {chi:.3f}. Anlamlılık yorumu için serbestlik derecesi, örnekleme ve test varsayımları dikkate alınmalıdır.")

with file_tab:
    st.header("Biyoinformatik dosya analiz merkezi")
    st.write("Bu bölüm kendi moleküler verini yapıştırman veya yüklemen için hazırlanmıştır. Ekranda görünen FASTA ve VCF, aracın nasıl çalıştığını göstermek için konmuş **değiştirilebilir örnek metindir**; sabit sonuç değildir.")
    st.info("FASTA DNA/protein dizisini, VCF genomik varyantları, CSV ise satır–sütun biçimindeki herhangi bir tabloyu taşır. Kişisel hasta verisi yükleme.")
    file_type = st.radio("Girdi türü", ["FASTA metni", "VCF metni", "CSV yükle"], horizontal=True)
    if file_type == "FASTA metni":
        st.markdown("**Ne yapar?** `>` ile başlayan başlığı ayırır; dizinin uzunluğunu ve G+C bazlarının yüzdesini hesaplar; geçersiz karakterleri kontrol eder.")
        fasta = st.text_area("FASTA dizisi", ">ornek\nATGCGTACCGTTAGC", height=140)
        sequence = "".join(line.strip() for line in fasta.splitlines() if not line.startswith(">") and line.strip()).upper()
        valid = set(sequence) <= set("ACGTN")
        gc = ((sequence.count("G") + sequence.count("C"))/len(sequence)*100) if sequence else 0
        st.metric("Dizi uzunluğu", len(sequence)); st.metric("GC oranı", f"%{gc:.1f}")
        (st.success if valid else st.error)("Dizi karakterleri geçerli." if valid else "ACGTN dışında karakter bulundu.")
    elif file_type == "VCF metni":
        st.markdown("**Ne yapar?** Her varyant satırından kromozom, konum, rsID, referans/alternatif baz, kalite ve filtre alanlarını ayırır. Bu prototip tam VCF anotasyonu veya genotip çağrımı yapmaz.")
        vcf = st.text_area("VCF satırları", "#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\n22\t42128945\trs3892097\tG\tA\t99\tPASS", height=150)
        records = []
        for line in vcf.splitlines():
            if line and not line.startswith("#"):
                parts = line.split("\t")
                if len(parts) >= 7: records.append(parts[:7])
        if records: st.dataframe(pd.DataFrame(records, columns=["CHROM","POS","ID","REF","ALT","QUAL","FILTER"]), width="stretch", hide_index=True)
        else: st.info("Geçerli varyant satırı bulunamadı.")
    else:
        st.markdown("**Ne yapar?** Yüklediğin CSV tablosunun ilk 100 satırını, satır ve sütun sayısını gösterir. İleride alel frekansı veya kalite analizi için kolon eşleme eklenebilir.")
        uploaded = st.file_uploader("CSV dosyası", type=["csv"])
        if uploaded:
            try:
                df_upload = pd.read_csv(uploaded)
                st.dataframe(df_upload.head(100), width="stretch")
                st.write(f"{len(df_upload)} satır · {len(df_upload.columns)} sütun")
            except Exception as exc:
                st.error(f"CSV okunamadı: {exc}")
    st.caption("Dosyalar bu oturumda analiz edilir; prototip kalıcı hasta verisi depolamaz. Kişisel/kimliklenebilir sağlık verisi yüklemeyin.")

with tab5:
    st.header("Literatür ve kanıt taraması")
    st.write("Seçilen gen–ilaç çifti için PubMed kayıtlarını getirir. Bir makalenin listelenmesi, sonucun klinik olarak kanıtlandığı anlamına gelmez; çalışma tasarımı, örneklem, kılavuz uyumu ve güncellik ayrıca değerlendirilmelidir.")
    st.subheader(f"Otomatik sorgu: {gene} + {drug}")
    st.code(f'({gene}[Title/Abstract]) AND ({drug.split(" (")[0]}[Title/Abstract]) AND pharmacogen*', language=None)
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
    st.subheader("Gerçek kaynak kanıt paneli")
    e1, e2, e3, e4 = st.columns(4)
    e1.link_button("ClinVar'da aç", f"https://www.ncbi.nlm.nih.gov/clinvar/?term={urllib.parse.quote_plus(gene + ' drug response')}")
    e2.link_button("ClinPGx'te aç", f"https://www.pharmgkb.org/search?query={urllib.parse.quote_plus(gene + ' ' + drug.split(' (')[0])}")
    e3.link_button("CPIC kılavuzları", "https://cpicpgx.org/guidelines/")
    e4.link_button("ClinicalTrials.gov", f"https://clinicaltrials.gov/search?term={urllib.parse.quote_plus(gene + ' ' + drug.split(' (')[0])}")
    if st.button("ClinVar ilaç yanıtı kayıtlarını getir"):
        try:
            clinvar_records = clinvar_search(gene)
            if clinvar_records:
                st.success(f"ClinVar'da {len(clinvar_records)} gerçek kayıt getirildi.")
                for record in clinvar_records:
                    label = f"{record['accession']} · {record['title']}" if record["accession"] else record["title"]
                    st.markdown(f"- [{label}](https://www.ncbi.nlm.nih.gov/clinvar/variation/{record['uid']}/) {('· Güncelleme: ' + record['updated']) if record['updated'] else ''}")
            else:
                st.info("ClinVar'da bu gen için 'drug response' etiketli kayıt bulunamadı. Sistem örnek sonuç üretmedi.")
        except Exception:
            st.error("ClinVar'a şu anda ulaşılamadı; sonuç uydurulmadı. Daha sonra yeniden deneyin.")
    st.caption(f"Kaynak sorgu zamanı: {date.today().isoformat()}. Canlı sonuçlar kaynak veritabanlarının kendi kayıtlarına bağlıdır.")
    st.subheader("Kanıtı okurken sorulacak sorular")
    st.dataframe(pd.DataFrame([
        ["Çalışma türü", "Kılavuz, sistematik derleme, randomize çalışma, kohort veya vaka raporu mu?"],
        ["Popülasyon", "Alel sıklığı ve etki, genetik kökene göre farklılaşabilir mi?"],
        ["Sonuç", "İlaç düzeyi mi, klinik yanıt mı, advers olay mı ölçülmüş?"],
        ["Doğrulama", "Bulgular bağımsız bir grupta tekrar edilmiş mi?"],
        ["Uygulanabilirlik", "CPIC/DPWG veya düzenleyici ilaç etiketinde öneri var mı?"],
    ], columns=["Başlık", "Kontrol sorusu"]), width="stretch", hide_index=True)

with tab6:
    st.header("📥 Veri merkezi")
    st.write("Bu bölüm analizini saklamak, Excel'de incelemek veya başka bir araştırma aracına aktarmak için dosya üretir. Hiçbir dosya otomatik olarak bir hastane sistemine gönderilmez.")
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
        "bobrek_fonksiyon_bozuklugu": renal,
        "yas": age,
        "bmi": round(bmi, 1),
        "diyabet": diabetes,
        "kronik_durumlar": "; ".join(f"{group}: {', '.join(items)}" for group, items in condition_groups.items() if items) or "Yok",
        "sigara": smoking,
        "alkol": alcohol,
        "inflamasyon_enfeksiyon": "Evet" if inflammation else "Hayır",
        "kural_tabanli_degerlendirme": rule_level,
        "sonuc_turu": "Kural tabanlı genotip-fenotip tahmini; klinik risk yüzdesi değildir",
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
    st.markdown("""
    - **CSV:** Excel veya istatistik programında satır–sütun biçiminde açılır.
    - **JSON:** Yazılımlar ve web servisleri için yapılandırılmış veri biçimidir.
    - **TXT rapor:** İnsan tarafından okunabilen sade analiz özetidir.
    """)

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
    st.download_button("Tüm alel veri setini CSV indir", library_df.to_csv(index=False).encode("utf-8-sig"), "farmakogenetik_alel_verisi_v3.csv", "text/csv")
    st.info("İndirilen veriler eğitimsel ve sadeleştirilmiştir. Klinik kullanım öncesinde güncel CPIC, PharmVar ve ClinPGx kaynaklarıyla doğrulanmalıdır.")

with tab7:
    st.header("📰 Araştırma ve öğrenme merkezi")
    st.write("Kavram yazıları, açık klinik bilgi kaynakları ve kontrollü hasta düzeyi veri platformları bu bölümde bir araya getirilir.")
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
    st.subheader("Hasta düzeyi ve klinik-genomik veri kaynakları")
    ipd_sources = pd.DataFrame([
        ["ClinVar", "Varyant sınıflandırmaları, ilaç yanıtı ve bazen kimliksiz vaka gözlemleri", "Büyük ölçüde açık", "Hasta profili değil; varyant merkezlidir", "https://www.ncbi.nlm.nih.gov/clinvar/"],
        ["dbGaP", "Kimliksiz bireysel genotip, fenotip ve çalışma verileri", "Kontrollü araştırmacı erişimi", "Kurumsal başvuru ve veri kullanım onayı gerekir", "https://www.ncbi.nlm.nih.gov/gap/"],
        ["All of Us", "EHR, anket, fiziksel ölçüm ve genom verileri", "Katmanlı/kontrollü erişim", "Araştırmacı Workbench ve kurum uygunluğu gerekir", "https://www.researchallofus.org/"],
        ["ClinicalTrials.gov IPD", "Çalışmanın bireysel katılımcı verisi paylaşım planı ve erişim bağlantısı", "Çalışmaya göre değişir", "Genellikle veri doğrudan sitede değil, istekle başka depoda paylaşılır", "https://clinicaltrials.gov/"],
    ], columns=["Kaynak", "Ne içerir?", "Erişim", "Önemli sınırlama", "Adres"])
    st.dataframe(ipd_sources, width="stretch", hide_index=True)
    st.info("IPD (Individual Participant Data), bireysel katılımcı düzeyindeki kimliksiz araştırma verisidir. Açık web sitesindeki toplu sonuçlarla aynı değildir ve çoğunlukla etik/kurumsal izin gerektirir.")
    st.warning("Bu portal kontrollü dbGaP veya All of Us hasta verisini çekmez, depolamaz ya da yeniden yayımlamaz. Böyle bir entegrasyon için araştırma protokolü, etik onay, veri kullanım sözleşmesi ve güvenli analiz ortamı gerekir.")

with glossary_tab:
    st.header("📖 Farmakogenetik sözlük ve öğrenme rehberi")
    st.write("Örneğin **Alel 1** ve **Alel 2**, genin iki kopyasını; **CYP2D6 *1/*4** ise bu iki kopyadaki yıldız alellerden oluşan diplotipi anlatır.")
    for term, definition in GLOSSARY.items():
        with st.expander(term):
            st.write(definition)
    with st.expander("IPD — Individual Participant Data"):
        st.write("Bir klinik çalışmadaki her katılımcı için ayrı satırda tutulan kimliksiz verilerdir. Toplu ortalama veya yüzde değildir. Genomik veriler yeniden kimliklendirme riski taşıdığı için çoğu IPD kontrollü erişim altında tutulur.")
    with st.expander("Klinik anotasyon"):
        st.write("Bir gen–ilaç veya varyant–ilaç ilişkisinin yayınlar ve kılavuzlar temelinde yapılandırılmış yorumudur. Tek başına reçete önerisi değildir.")
    st.subheader("Fenotip sınıfları")
    st.dataframe(pd.DataFrame([
        ["Poor", "Zayıf işlev / metabolizör", "İşlev çok düşük veya yok"],
        ["Intermediate", "Ara işlev / metabolizör", "İşlev normalin altında"],
        ["Normal", "Normal işlev / metabolizör", "Beklenen referans aralık"],
        ["Rapid", "Hızlı metabolizör", "Bazı genlerde normalden yüksek işlev"],
        ["Ultrarapid", "Çok hızlı metabolizör", "Belirgin yüksek işlev; bazı genlerde kopya sayısıyla ilişkili olabilir"],
    ], columns=["Terim", "Türkçe", "Sade açıklama"]), width="stretch", hide_index=True)

st.divider()
st.caption(f"V3 prototipi · Veri sürümü: {date.today().isoformat()} · Açıklanabilir kural tabanlı eğitim aracı · Sonuçlar kaynak sürümü ve klinik bağlamla doğrulanmalıdır.")
