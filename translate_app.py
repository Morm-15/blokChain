import codecs
import re

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# 1. Add t_func after imports
t_func_code = """
# =============================================================================
# 🌍 دعم اللغات - Internationalization (i18n)
# =============================================================================
if "lang" not in st.session_state:
    st.session_state["lang"] = "العربية"

def t(ar: str, tr: str) -> str:
    return tr if st.session_state.get("lang", "العربية") == "Türkçe" else ar

"""

# Find a good place to insert it (after imports, around line 15)
import_end_idx = content.find('warnings.filterwarnings("ignore")')
if import_end_idx != -1:
    import_end_idx += len('warnings.filterwarnings("ignore")')
    content = content[:import_end_idx] + "\n\n" + t_func_code + content[import_end_idx:]

# 2. Add language selector at the top of the sidebar
sidebar_header = 'st.sidebar.markdown("## ⚙️ لوحة التحكم")'
sidebar_lang = '''st.sidebar.markdown(t("## ⚙️ لوحة التحكم", "## ⚙️ Kontrol Paneli"))
st.sidebar.markdown("---")
st.session_state["lang"] = st.sidebar.radio(
    t("🌍 اللغة / Language", "🌍 Dil / Language"), 
    ["العربية", "Türkçe"], 
    index=0 if st.session_state.get("lang", "العربية") == "العربية" else 1
)
'''
content = content.replace(sidebar_header + '\nst.sidebar.markdown("---")', sidebar_lang)


# 3. Replace text
replacements = [
    # Headers
    ('"🛡️ نظام دعم القرار لتحسين البلوكشين"', 't("🛡️ نظام دعم القرار لتحسين البلوكشين", "🛡️ Blokzincir Optimizasyonu Karar Destek Sistemi")'),
    ('"مقارنة شاملة بين <strong>FIFO التقليدية</strong> وطرق التجميع الذكية"', 't("مقارنة شاملة بين <strong>FIFO التقليدية</strong> وطرق التجميع الذكية", "<strong>Geleneksel FIFO</strong> ve Akıllı Kümeleme Yöntemlerinin Kapsamlı Karşılaştırması")'),
    ('"(<strong>DBSCAN</strong> و <strong>K-Means</strong>) لتعظيم كفاءة استغلال الغاز."', 't("(<strong>DBSCAN</strong> و <strong>K-Means</strong>) لتعظيم كفاءة استغلال الغاز.", "(<strong>DBSCAN</strong> ve <strong>K-Means</strong>) ile gaz kullanım verimliliğini en üst düzeye çıkarma.")'),
    
    # Sidebar
    ('"### 📊 إعدادات البيانات"', 't("### 📊 إعدادات البيانات", "### 📊 Veri Ayarları")'),
    ('"عدد المعاملات المختبرة"', 't("عدد المعاملات المختبرة", "Test Edilen İşlem Sayısı")'),
    ('"عدد المعاملات التي سيتم تحليلها من الملف"', 't("عدد المعاملات التي سيتم تحليلها من الملف", "Dosyadan analiz edilecek işlem sayısı")'),
    ('"🔀 عينة عشوائية جديدة"', 't("🔀 عينة عشوائية جديدة", "🔀 Yeni Rastgele Örnek")'),
    ('"يختار مجموعة مختلفة تماماً من المعاملات لاختبار الخوارزمية على بيانات متنوعة"', 't("يختار مجموعة مختلفة تماماً من المعاملات لاختبار الخوارزمية على بيانات متنوعة", "Algoritmayı çeşitli veriler üzerinde test etmek için tamamen farklı bir işlem kümesi seçer")'),
    ('"سعة البلوك (Gas Limit)"', 't("سعة البلوك (Gas Limit)", "Blok Kapasitesi (Gas Limit)")'),
    ('"الحد الأقصى للغاز الذي يمكن أن يستوعبه البلوك الواحد"', 't("الحد الأقصى للغاز الذي يمكن أن يستوعبه البلوك الواحد", "Tek bir bloğun barındırabileceği maksimum gaz miktarı")'),
    ('"### 🤖 إعدادات الخوارزمية"', 't("### 🤖 إعدادات الخوارزمية", "### 🤖 Algoritma Ayarları")'),
    ('"اختر خوارزمية التجميع الذكي"', 't("اختر خوارزمية التجميع الذكي", "Akıllı Kümeleme Algoritmasını Seçin")'),
    ('"DBSCAN: تجميع كثافي مع اكتشاف الضجيج | K-Means: تجميع ثابت بعدد محدد"', 't("DBSCAN: تجميع كثافي مع اكتشاف الضجيج | K-Means: تجميع ثابت بعدد محدد", "DBSCAN: Gürültü tespiti ile yoğunluk tabanlı kümeleme | K-Means: Belirli sayıda sabit kümeleme")'),
    ('"**معاملات DBSCAN:**"', 't("**معاملات DBSCAN:**", "**DBSCAN Parametreleri:**")'),
    ('"حساسية المسافة (eps)"', 't("حساسية المسافة (eps)", "Mesafe Hassasiyeti (eps)")'),
    ('"كلما قلّت القيمة، زادت صرامة التجميع وزادت نقاط الضجيج"', 't("كلما قلّت القيمة، زادت صرامة التجميع وزادت نقاط الضجيج", "Değer ne kadar düşük olursa, kümeleme o kadar katı olur ve gürültü noktaları artar")'),
    ('"الحد الأدنى للنقاط (MinPts)"', 't("الحد الأدنى للنقاط (MinPts)", "Minimum Nokta Sayısı (MinPts)")'),
    ('"الحد الأدنى من النقاط لتشكيل نواة مجموعة"', 't("الحد الأدنى من النقاط لتشكيل نواة مجموعة", "Bir küme çekirdeği oluşturmak için minimum nokta sayısı")'),
    ('"**معاملات K-Means:**"', 't("**معاملات K-Means:**", "**K-Means Parametreleri:**")'),
    ('"عدد المجموعات (K)"', 't("عدد المجموعات (K)", "Küme Sayısı (K)")'),
    ('"عدد المجموعات الثابتة التي ستُقسَّم إليها المعاملات"', 't("عدد المجموعات الثابتة التي ستُقسَّم إليها المعاملات", "İşlemlerin bölüneceği sabit küme sayısı")'),
    ('"<small style=\'color:#607080;\'>💡 غيّر الإعدادات أو اضغط 🔀 لعينة جديدة.</small>"', 't("<small style=\'color:#607080;\'>💡 غيّر الإعدادات أو اضغط 🔀 لعينة جديدة.</small>", "<small style=\'color:#607080;\'>💡 Ayarları değiştirin veya yeni bir örnek için 🔀 tuşuna basın.</small>")'),
    
    # Progress & Metrics
    ('f"⚙️ جارٍ تطبيق خوارزمية {algorithm}..."', 't(f"⚙️ جارٍ تطبيق خوارزمية {algorithm}...", f"⚙️ {algorithm} algoritması uygulanıyor...")'),
    ('f"⏱️ زمن المعالجة: {execution_time:.2f} ms"', 't(f"⏱️ زمن المعالجة: {execution_time:.2f} ms", f"⏱️ İşlem Süresi: {execution_time:.2f} ms")'),
    ('"### 📐 جودة التجميع"', 't("### 📐 جودة التجميع", "### 📐 Kümeleme Kalitesi")'),
    ('"القيم الأقرب إلى 1 تعني مجموعات متمايزة جيداً"', 't("القيم الأقرب إلى 1 تعني مجموعات متمايزة جيداً", "1\'e yakın değerler iyi ayırt edilmiş kümeler anlamına gelir")'),
    ('"القيم الأصغر تعني مجموعات أفضل تفصيلاً"', 't("القيم الأصغر تعني مجموعات أفضل تفصيلاً", "Daha küçük değerler daha iyi detaylandırılmış kümeler anlamına gelir")'),
    ('f"🗑️ نقاط الضجيج (Noise): {quality[\'noise_count\']:,}"', 't(f"🗑️ نقاط الضجيج (Noise): {quality[\'noise_count\']:,}", f"🗑️ Gürültü Noktaları (Noise): {quality[\'noise_count\']:,}")'),
    
    # Sections
    ('"## 📊 مقارنة الأداء: FIFO التقليدية مقابل الطريقة الذكية"', 't("## 📊 مقارنة الأداء: FIFO التقليدية مقابل الطريقة الذكية", "## 📊 Performans Karşılaştırması: Geleneksel FIFO vs Akıllı Yöntem")'),
    ('"🔵 FIFO | عدد المعاملات"', 't("🔵 FIFO | عدد المعاملات", "🔵 FIFO | İşlem Sayısı")'),
    ('"عدد المعاملات في البلوك بطريقة FIFO"', 't("عدد المعاملات في البلوك بطريقة FIFO", "FIFO yönteminde bloktaki işlem sayısı")'),
    ('f"🟢 {algorithm} | عدد المعاملات"', 't(f"🟢 {algorithm} | عدد المعاملات", f"🟢 {algorithm} | İşlem Sayısı")'),
    ('f"{delta_tx:+,} مقارنةً بـ FIFO"', 't(f"{delta_tx:+,} مقارنةً بـ FIFO", f"{delta_tx:+,} FIFO\'ya göre")'),
    ('"عدد المعاملات في البلوك بالطريقة الذكية"', 't("عدد المعاملات في البلوك بالطريقة الذكية", "Akıllı yöntemde bloktaki işlem sayısı")'),
    ('"🔵 FIFO | كفاءة الغاز"', 't("🔵 FIFO | كفاءة الغاز", "🔵 FIFO | Gaz Verimliliği")'),
    ('"نسبة الغاز المستخدم من إجمالي سعة البلوك"', 't("نسبة الغاز المستخدم من إجمالي سعة البلوك", "Toplam blok kapasitesinden kullanılan gaz yüzdesi")'),
    ('f"🟢 {algorithm} | كفاءة الغاز"', 't(f"🟢 {algorithm} | كفاءة الغاز", f"🟢 {algorithm} | Gaz Verimliliği")'),
    ('f"{delta_eff:+.1f}% مقارنةً بـ FIFO"', 't(f"{delta_eff:+.1f}% مقارنةً بـ FIFO", f"{delta_eff:+.1f}% FIFO\'ya göre")'),
    ('"نسبة الغاز المستخدم بالطريقة الذكية"', 't("نسبة الغاز المستخدم بالطريقة الذكية", "Akıllı yöntemde kullanılan gaz yüzdesi")'),
    ('"🔵 FIFO | الغاز المستهلك"', 't("🔵 FIFO | الغاز المستهلك", "🔵 FIFO | Tüketilen Gaz")'),
    ('f"🟢 {algorithm} | الغاز المستهلك"', 't(f"🟢 {algorithm} | الغاز المستهلك", f"🟢 {algorithm} | Tüketilen Gaz")'),
    ('"🔵 FIFO | تجزئة البلوك"', 't("🔵 FIFO | تجزئة البلوك", "🔵 FIFO | Blok Parçalanması")'),
    ('"نسبة المساحة المهدرة - كلما قلّت كان أفضل"', 't("نسبة المساحة المهدرة - كلما قلّت كان أفضل", "Boşa harcanan alan yüzdesi - ne kadar az o kadar iyi")'),
    ('f"🟢 {algorithm} | تجزئة البلوك"', 't(f"🟢 {algorithm} | تجزئة البلوك", f"🟢 {algorithm} | Blok Parçalanması")'),
    ('f"{delta_frag:+.1f}% (أقل = أفضل)"', 't(f"{delta_frag:+.1f}% (أقل = أفضل)", f"{delta_frag:+.1f}% (Daha az = Daha iyi)")'),
    ('"نسبة المساحة المهدرة بالطريقة الذكية"', 't("نسبة المساحة المهدرة بالطريقة الذكية", "Akıllı yöntemde boşa harcanan alan yüzdesi")'),
    
    # Comparison table & text
    ('"## ⚡ مقارنة ثلاثية: FIFO مقابل Dense-First مقابل Greedy Bin-Packing"', 't("## ⚡ مقارنة ثلاثية: FIFO مقابل Dense-First مقابل Greedy Bin-Packing", "## ⚡ Üçlü Karşılaştırma: FIFO vs Dense-First vs Greedy Bin-Packing")'),
    ('"FIFO\\n(تقليدي)"', 't("FIFO\\n(تقليدي)", "FIFO\\n(Geleneksel)")'),
    ('"كفاءة الغاز %"', 't("كفاءة الغاز %", "Gaz Verimliliği %")'),
    ('"كفاءة %"', 't("كفاءة %", "Verimlilik %")'),
    ('"تجزئة البلوك %"', 't("تجزئة البلوك %", "Blok Parçalanması %")'),
    ('"تجزئة %"', 't("تجزئة %", "Parçalanma %")'),
    ('"عدد المعاملات"', 't("عدد المعاملات", "İşlem Sayısı")'),
    ('"عدد"', 't("عدد", "Sayısı")'),
    ('"الطريقة"', 't("الطريقة", "Yöntem")'),
    ('"إيراد المُعدِّن (Gwei)"', 't("إيراد المُعدِّن (Gwei)", "Madenci Geliri (Gwei)")'),
    
    # Reconstruct the string concatenation
    ('f"✅ **Greedy Bin-Packing** تُحسِّن كفاءة الغاز بـ **{_greedy_gain:+.1f}%** مقارنةً بـ FIFO "\\n    f"و **{smart_greedy[\'efficiency\'] - smart_dense[\'efficiency\']:+.1f}%** مقارنةً بـ Dense-First.\\n\\n"\\n    f"💰 **زيادة أرباح المُعدِّن:** الخوارزمية رفعت الإيراد بـ **{_rev_gain:+,.2f} Gwei** (+{_rev_gain_pct:.1f}%)."', 
     't(f"✅ **Greedy Bin-Packing** تُحسِّن كفاءة الغاز بـ **{_greedy_gain:+.1f}%** مقارنةً بـ FIFO "\\n      f"و **{smart_greedy[\'efficiency\'] - smart_dense[\'efficiency\']:+.1f}%** مقارنةً بـ Dense-First.\\n\\n"\\n      f"💰 **زيادة أرباح المُعدِّن:** الخوارزمية رفعت الإيراد بـ **{_rev_gain:+,.2f} Gwei** (+{_rev_gain_pct:.1f}%).",\\n      f"✅ **Greedy Bin-Packing**, gaz verimliliğini FIFO\'ya göre **{_greedy_gain:+.1f}%** artırır "\\n      f"ve Dense-First\'e göre **{smart_greedy[\'efficiency\'] - smart_dense[\'efficiency\']:+.1f}%** artırır.\\n\\n"\\n      f"💰 **Artan Madenci Kârı:** Algoritma geliri **{_rev_gain:+,.2f} Gwei** (+{_rev_gain_pct:.1f}%) artırdı.")'),
    
    # Multi-block simulation
    ('"## 🔄 محاكاة متعددة البلوكات (Multi-Block Simulation)"', 't("## 🔄 محاكاة متعددة البلوكات (Multi-Block Simulation)", "## 🔄 Çoklu Blok Simülasyonu")'),
    ('"كيف يؤدي نظام Greedy Bin-Packing على مدى 5 بلوكات متتالية؟"', 't("كيف يؤدي نظام Greedy Bin-Packing على مدى 5 بلوكات متتالية؟", "Greedy Bin-Packing sistemi ardışık 5 blokta nasıl performans gösteriyor?")'),
    ('lambda x: f"بلوك {x}"', 'lambda x: t(f"بلوك {x}", f"Blok {x}")'),
    ('"كفاءة الغاز لكل بلوك - Greedy Bin-Packing"', 't("كفاءة الغاز لكل بلوك - Greedy Bin-Packing", "Blok başına gaz verimliliği - Greedy Bin-Packing")'),
    
    # Charts
    ('f"## 📈 مخطط التشتت: تصنيف {algorithm} للمعاملات"', 't(f"## 📈 مخطط التشتت: تصنيف {algorithm} للمعاملات", f"## 📈 Dağılım Grafiği: İşlemlerin {algorithm} Sınıflandırması")'),
    ('f"🔵 **إجمالي المعاملات:** {n_txs:,}"', 't(f"🔵 **إجمالي المعاملات:** {n_txs:,}", f"🔵 **Toplam İşlem:** {n_txs:,}")'),
    ('f"✅ **المجموعات المكتشفة:** {n_real_clusters}"', 't(f"✅ **المجموعات المكتشفة:** {n_real_clusters}", f"✅ **Bulunan Kümeler:** {n_real_clusters}")'),
    ('f"⚠️ **معاملات الضجيج (Noise):** {noise_count:,}"', 't(f"⚠️ **معاملات الضجيج (Noise):** {noise_count:,}", f"⚠️ **Gürültü İşlemleri (Noise):** {noise_count:,}")'),
    ('f"📌 **K المحدد:** {k_val} مجموعات ثابتة"', 't(f"📌 **K المحدد:** {k_val} مجموعات ثابتة", f"📌 **Belirlenen K:** {k_val} sabit küme")'),
    ('"📋 توزيع المعاملات على المجموعات"', 't("📋 توزيع المعاملات على المجموعات", "📋 İşlemlerin Kümelere Dağılımı")'),
    ("['رقم المجموعة', 'عدد المعاملات']", "[t('رقم المجموعة', 'Küme Numarası'), t('عدد المعاملات', 'İşlem Sayısı')]"),
    ("'التسمية'", "t('التسمية', 'Etiket')"),
    ("'النسبة %'", "t('النسبة %', 'Yüzde %')"),
    ("lambda x: '⚠️ Noise (مُستبعد)' if x == -1 else f'Cluster {x}'", "lambda x: t('⚠️ Noise (مُستبعد)', '⚠️ Gürültü (Hariç Tutuldu)') if x == -1 else f'Cluster {x}'"),
    
    # Tabs
    ('"## 🧠 شرح المنطق للأستاذ الجامعي (Explainable AI)"', 't("## 🧠 شرح المنطق للأستاذ الجامعي (Explainable AI)", "## 🧠 Akademik Mantık Açıklaması (Açıklanabilir Yapay Zeka)")'),
    ('"🔍 لماذا الطريقة الذكية أفضل؟"', 't("🔍 لماذا الطريقة الذكية أفضل؟", "🔍 Akıllı yöntem neden daha iyi?")'),
    ('"⚖️ DBSCAN مقابل K-Means"', 't("⚖️ DBSCAN مقابل K-Means", "⚖️ DBSCAN vs K-Means")'),
    ('"📊 تحليل الجدوى (Trade-offs)"', 't("📊 تحليل الجدوى (Trade-offs)", "📊 Fizibilite Analizi (Ödünleşimler)")'),
    ('"📐 إيجاد K الأمثل (Elbow Method)"', 't("📐 إيجاد K الأمثل (Elbow Method)", "📐 Optimum K\'yı Bulma (Dirsek Yöntemi)")'),
    
    # Optimal K
    ('"🔍 احسب K الأمثل الآن (K=2..10)"', 't("🔍 احسب K الأمثل الآن (K=2..10)", "🔍 Optimum K\'yı Şimdi Hesapla (K=2..10)")'),
    ('"⏳ جارٍ حساب Silhouette و Inertia لكل K..."', 't("⏳ جارٍ حساب Silhouette و Inertia لكل K...", "⏳ Her K için Silhouette ve Inertia hesaplanıyor...")'),
    ('f"✅ **K الأمثل الموصى به:** {_opt[\'optimal_k\']} مجموعات "\\n                   f"(Silhouette = {max(_opt[\'silhouettes\']):.3f})"', 
     't(f"✅ **K الأمثل الموصى به:** {_opt[\'optimal_k\']} مجموعات (Silhouette = {max(_opt[\'silhouettes\']):.3f})", f"✅ **Önerilen Optimum K:** {_opt[\'optimal_k\']} küme (Silhouette = {max(_opt[\'silhouettes\']):.3f})")'),
    ('"💡 اضغط الزر أعلاه لحساب K الأمثل. قد يستغرق بضع ثوانٍ."', 't("💡 اضغط الزر أعلاه لحساب K الأمثل. قد يستغرق بضع ثوانٍ.", "💡 Optimum K\'yı hesaplamak için yukarıdaki düğmeye basın. Birkaç saniye sürebilir.")'),

    # Raw Data
    ('"👀 عرض البيانات الخام مع تصنيف الخوارزمية"', 't("👀 عرض البيانات الخام مع تصنيف الخوارزمية", "👀 Algoritma sınıflandırması ile ham verileri görüntüleyin")'),
    ("'نوع النقطة'", "t('نوع النقطة', 'Nokta Türü')"),
    ("lambda x: '⚠️ Noise' if x == -1 else f'✅ Cluster {x}'", "lambda x: t('⚠️ Noise', '⚠️ Gürültü') if x == -1 else f'✅ Cluster {x}'"),
    ('f"عرض {n_txs:,} معاملة. إجمالي الملف: {n_txs:,} معاملة."', 't(f"عرض {n_txs:,} معاملة. إجمالي الملف: {n_txs:,} معاملة.", f"{n_txs:,} işlem gösteriliyor. Toplam Dosya: {n_txs:,} işlem.")'),
    
    # Footer
    ('"🛡️ Blockchain Optimization DSS v3.0 | DBSCAN + K-Means + Greedy Bin-Packing | "\\n    "نظام دعم القرار لتحسين البلوكشين"', 't("🛡️ Blockchain Optimization DSS v3.0 | DBSCAN + K-Means + Greedy Bin-Packing | نظام دعم القرار لتحسين البلوكشين", "🛡️ Blokzincir Optimizasyonu DSS v3.0 | DBSCAN + K-Means + Greedy Bin-Packing | Blokzincir Optimizasyonu Karar Destek Sistemi")')
]

for old, new in replacements:
    content = content.replace(old, new)

# Special handling for column names in the dataframe display:
content = content.replace(
    "dist_df[['التسمية', 'عدد المعاملات', 'النسبة %']]",
    "dist_df[[t('التسمية', 'Etiket'), t('عدد المعاملات', 'İşlem Sayısı'), t('النسبة %', 'Yüzde %')]]"
)

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)

print("Translation applied successfully!")
