import sys
sys.path.insert(0, 'C:/Users/moham/blockzincir')
from modules.data_loader import load_data, get_summary_stats, get_block_stats
from modules.feature_engineering import build_features
from modules.dbscan_model import run_dbscan, evaluate_fraud_detection
from modules.blockchain_sim import compute_reduction, human_size

print('Loading data...')
df = load_data()
print('  Loaded:', len(df), 'rows')

stats = get_summary_stats(df)
print('  Total size:', human_size(int(stats['total_size_mb']*1048576)))
print('  Scam rate:', round(stats['scam_rate'],1), '%')

print('Building features...')
X_scaled, coords_2d, coords_3d = build_features(df)
print('  Feature matrix:', X_scaled.shape)

print('Running DBSCAN (eps=0.5, min_samples=5)...')
labels, t = run_dbscan(X_scaled, eps=0.5, min_samples=5)
n_clusters = len(set(labels) - {-1})
n_noise = int((labels==-1).sum())
print('  Clusters:', n_clusters, '  Noise:', n_noise, '  Time:', round(t,2), 's')

print('Computing reduction (strategy_both)...')
res = compute_reduction(df, labels, 'strategy_both')
print('  Before:', human_size(res['total_before']))
print('  After: ', human_size(res['total_after']))
print('  Saved: ', human_size(res['bytes_saved']), '(' + str(round(res['pct_saved'],1)) + '%)')

print('Evaluating fraud detection...')
fraud = evaluate_fraud_detection(df, labels)
print('  Precision:', round(fraud['precision'],3))
print('  Recall:   ', round(fraud['recall'],3))
print('  F1:       ', round(fraud['f1'],3))
print('')
print('ALL MODULES OK')
