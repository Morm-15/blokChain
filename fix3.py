import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix 1: Plot axis labels and title
old_axes = '''    ax.set_xlabel("سعر الغاز (Gas Price)", color='#a0b4c8', fontsize=11)
    ax.set_ylabel("حد الغاز (Gas Limit)", color='#a0b4c8', fontsize=11)'''
new_axes = '''    ax.set_xlabel(t("سعر الغاز (Gas Price)", "Gaz Fiyatı (Gas Price)"), color='#a0b4c8', fontsize=11)
    ax.set_ylabel(t("حد الغاز (Gas Limit)", "Gaz Sınırı (Gas Limit)"), color='#a0b4c8', fontsize=11)'''
content = content.replace(old_axes, new_axes)

old_title = 'title = f"تصنيف {algo_name} - {len(plot_df):,} معاملة"'
new_title = 'title = t(f"تصنيف {algo_name} - {len(plot_df):,} معاملة", f"{algo_name} Sınıflandırması - {len(plot_df):,} işlem")'
content = content.replace(old_title, new_title)

# Fix 2: Sidebar caption
old_caption = '''st.sidebar.caption(
    f"🎲 البذرة الحالية: `{st.session_state['random_seed']}`  "
    "*(تتغير عند كل ضغطة)*"
)'''
new_caption = '''st.sidebar.caption(
    t(f"🎲 البذرة الحالية: `{st.session_state['random_seed']}`  *(تتغير عند كل ضغطة)*", 
      f"🎲 Mevcut Tohum: `{st.session_state['random_seed']}`  *(Her tıklamada değişir)*")
)'''
content = content.replace(old_caption, new_caption)

# Fix 3: KeyError in dist_df
old_dist_block = '''    dist_df = pd.Series(labels).value_counts().sort_index().reset_index()
    dist_df.columns = [t('رقم المجموعة', 'Küme Numarası'), t('عدد المعاملات', 'İşlem Sayısı')]
    dist_df[t('التسمية', 'Etiket')] = dist_df['رقم المجموعة'].apply(
        lambda x: t('⚠️ Noise (مُستبعد)', '⚠️ Gürültü (Hariç Tutuldu)') if x == -1 else f'Cluster {x}'
    )
    dist_df[t('النسبة %', 'Yüzde %')] = (dist_df['عدد المعاملات'] / n_txs * 100).round(2)
    st.dataframe(
        dist_df[[t('التسمية', 'Etiket'), 'عدد المعاملات', t('النسبة %', 'Yüzde %')]],'''
new_dist_block = '''    dist_df = pd.Series(labels).value_counts().sort_index().reset_index()
    
    col_group_num = t('رقم المجموعة', 'Küme Numarası')
    col_tx_count = t('عدد المعاملات', 'İşlem Sayısı')
    col_label = t('التسمية', 'Etiket')
    col_pct = t('النسبة %', 'Yüzde %')
    
    dist_df.columns = [col_group_num, col_tx_count]
    dist_df[col_label] = dist_df[col_group_num].apply(
        lambda x: t('⚠️ Noise (مُستبعد)', '⚠️ Gürültü (Hariç Tutuldu)') if x == -1 else f'Cluster {x}'
    )
    dist_df[col_pct] = (dist_df[col_tx_count] / n_txs * 100).round(2)
    st.dataframe(
        dist_df[[col_label, col_tx_count, col_pct]],'''
content = content.replace(old_dist_block, new_dist_block)

# Check if replacements were successful
if old_dist_block not in content and old_caption not in content and old_axes not in content:
    with codecs.open('app.py', 'w', 'utf-8') as f:
        f.write(content)
    print("All fixes applied successfully!")
else:
    print("Some replacements failed.")
    if old_axes in content: print("- Axes failed")
    if old_caption in content: print("- Caption failed")
    if old_dist_block in content: print("- Dist block failed")
