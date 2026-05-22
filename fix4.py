import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if "dist_df.columns = [t(" in line and "Küme Numarası" in line:
        lines[i] = "    col1 = t('رقم المجموعة', 'Küme Numarası')\n    col2 = t('عدد المعاملات', 'İşlem Sayısı')\n    dist_df.columns = [col1, col2]\n"
    elif "dist_df['رقم المجموعة'].apply" in line:
        lines[i] = line.replace("dist_df['رقم المجموعة']", "dist_df[col1]")
    elif "dist_df['عدد المعاملات']" in line and "round" in line:
        lines[i] = line.replace("dist_df['عدد المعاملات']", "dist_df[col2]")
    elif "dist_df[[t('التسمية', 'Etiket'), 'عدد المعاملات'" in line:
        lines[i] = line.replace("'عدد المعاملات'", "col2")

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.writelines(lines)
print('Done!')
