import codecs
import re

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# I18N block
i18n_pattern = r'# =============================================================================\r?\n# 🌍 دعم اللغات - Internationalization \(i18n\)\r?\n# =============================================================================\r?\nif \"lang\" not in st\.session_state:\r?\n    st\.session_state\[\"lang\"\] = \"العربية\"\r?\n\r?\ndef t\(ar: str, tr: str\) -> str:\r?\n    return tr if st\.session_state\.get\(\"lang\", \"العربية\"\) == \"Türkçe\" else ar'

# Page config block
page_pattern = r'# =============================================================================\r?\n# ⚙️ إعداد الصفحة - Page Configuration\r?\n# =============================================================================\r?\nst\.set_page_config\(\r?\n    page_title=\"Blockchain DSS - تحسين البلوكشين\",\r?\n    page_icon=\"🛡️\",\r?\n    layout=\"wide\",\r?\n    initial_sidebar_state=\"expanded\"\r?\n\)'

i18n_match = re.search(i18n_pattern, content)
page_match = re.search(page_pattern, content)

if i18n_match and page_match:
    i18n_text = i18n_match.group(0)
    page_text = page_match.group(0)
    
    # remove both from their current places
    content = content.replace(i18n_text, '')
    content = content.replace(page_text, '')
    
    # insert at the top, after imports
    insert_pos = content.find('from tx_batcher import TransactionBatcher')
    insert_pos = content.find('\n', insert_pos) + 1
    insert_pos = content.find('\n', insert_pos) + 1 # skip warnings
    insert_pos = content.find('\n', insert_pos) + 1
    
    new_content = content[:insert_pos] + '\n' + page_text + '\n\n' + i18n_text + '\n' + content[insert_pos:]
    
    with codecs.open('app.py', 'w', 'utf-8') as f:
        f.write(new_content)
    print('Fixed!')
else:
    print('Could not find matches')
    if not i18n_match: print("i18n missing")
    if not page_match: print("page missing")
