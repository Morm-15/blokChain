import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# Add Language Selector
old_sidebar = 'st.sidebar.markdown("## ⚙️ لوحة التحكم")\nst.sidebar.markdown("---")'
new_sidebar = '''st.sidebar.markdown(t("## ⚙️ لوحة التحكم", "## ⚙️ Kontrol Paneli"))
st.sidebar.markdown("---")
st.sidebar.markdown("**🌍 اللغة / Language / Dil**")
col1, col2 = st.sidebar.columns(2)
if col1.button("🇹🇷 Türkçe", use_container_width=True):
    st.session_state["lang"] = "Türkçe"
    st.rerun()
if col2.button("🇸🇦 العربية", use_container_width=True):
    st.session_state["lang"] = "العربية"
    st.rerun()
st.sidebar.markdown("---")
'''
content = content.replace(old_sidebar, new_sidebar)

# Replace the Main Header
old_header = '<h1>🛡️ نظام دعم القرار لتحسين البلوكشين</h1>'
new_header = '<h1>{t("🛡️ نظام دعم القرار لتحسين البلوكشين", "🛡️ Blokzincir Optimizasyonu Karar Destek Sistemi")}</h1>'
content = content.replace(old_header, new_header)

old_sub = 'مقارنة شاملة بين <strong>FIFO التقليدية</strong> وطرق التجميع الذكية'
new_sub = '{t("مقارنة شاملة بين <strong>FIFO التقليدية</strong> وطرق التجميع الذكية", "<strong>Geleneksel FIFO</strong> ve Akıllı Kümeleme Yöntemlerinin Kapsamlı Karşılaştırması")}'
content = content.replace(old_sub, new_sub)

old_sub2 = '(<strong>DBSCAN</strong> و <strong>K-Means</strong>) لتعظيم كفاءة استغلال الغاز.'
new_sub2 = '{t("(<strong>DBSCAN</strong> و <strong>K-Means</strong>) لتعظيم كفاءة استغلال الغاز.", "(<strong>DBSCAN</strong> ve <strong>K-Means</strong>) ile gaz kullanım verimliliğini en üst düzeye çıkarma.")}'
content = content.replace(old_sub2, new_sub2)

# Make the f-string for markdown
content = content.replace('st.markdown("""\n<div class="main-header">', 'st.markdown(f"""\n<div class="main-header">')

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)

print('Done')
