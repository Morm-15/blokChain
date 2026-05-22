import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from batch_optimizer import assemble_batches

# 1. تجهيز البيانات
np.random.seed(42)
data = np.random.rand(300, 2) * 100 
df = pd.DataFrame(data, columns=["gas_price", "gas_limit"])
X = StandardScaler().fit_transform(df)

# 2. تشغيل الخوارزميات (تحديد النوعين)
# خوارزمية K-Means
kmeans = KMeans(n_clusters=3, n_init=10).fit(X)
df['cluster'] = kmeans.labels_ 
report_kmeans = assemble_batches(df)

# خوارزمية DBSCAN
dbscan = DBSCAN(eps=0.3, min_samples=5).fit(X)
df['cluster'] = dbscan.labels_ # تحديث العمود لتستخدمه دالة التجميع
report_dbscan = assemble_batches(df)

# 3. عرض النتائج للمقارنة
print("=== تقرير الباتشات (K-Means) ===")
print(report_kmeans.head())

print("\n=== تقرير الباتشات (DBSCAN) ===")
print(report_dbscan.head())

# الرسم البياني للمقارنة بينهما
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
ax1.scatter(df["gas_price"], df["gas_limit"], c=kmeans.labels_, cmap='viridis')
ax1.set_title("Result: K-Means")
ax2.scatter(df["gas_price"], df["gas_limit"], c=dbscan.labels_, cmap='plasma')
ax2.set_title("Result: DBSCAN")
plt.show()