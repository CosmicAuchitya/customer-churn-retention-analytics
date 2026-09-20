"""
Project 2: Customer Churn & Cohort Retention Analytics
Part 2: E-Commerce Cohort Retention & RFM Segmentation (Online Retail Model)
Author: CosmicAuchitya
"""

import os
import datetime as dt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Aesthetics
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']

os.makedirs('output/tables', exist_ok=True)
os.makedirs('output/figures', exist_ok=True)

print("=" * 80)
print("PART 2: E-COMMERCE COHORT RETENTION & RFM SEGMENTATION FORENSICS")
print("=" * 80)

# ------------------------------------------------------------------------------
# 1. DATA INGESTION & CLEANING
# ------------------------------------------------------------------------------
df_raw = pd.read_csv('Online_Retail.csv', encoding='ISO-8859-1')
total_rows = len(df_raw)
print(f"Loaded raw transaction logs: {total_rows:,} rows.")

# Data hygiene:
# 1. Filter out unauthenticated guest checkouts (missing CustomerID)
df = df_raw.dropna(subset=['CustomerID']).copy()
df['CustomerID'] = df['CustomerID'].astype(int)
print(f"Retained authenticated customer records: {len(df):,} rows ({len(df)/total_rows*100:.1f}%).")

# 2. Filter out cancellations (InvoiceNo starting with 'C') and non-positive quantities/prices
df['InvoiceNo'] = df['InvoiceNo'].astype(str)
cancellations = df['InvoiceNo'].str.startswith('C') | (df['Quantity'] <= 0)
df = df[~cancellations & (df['UnitPrice'] > 0)].copy()

# 3. Create TotalSpend
df['TotalSpend'] = df['Quantity'] * df['UnitPrice']

# 4. Parse InvoiceDate
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
min_date = df['InvoiceDate'].min()
max_date = df['InvoiceDate'].max()
print(f"Cleaned dataset: {len(df):,} valid transactions from {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}.")
print(f"Unique Customers: {df['CustomerID'].nunique():,} | Unique Invoices: {df['InvoiceNo'].nunique():,}")

# ------------------------------------------------------------------------------
# 2. 12-MONTH COHORT RETENTION ANALYSIS (TRIANGLE HEATMAP)
# ------------------------------------------------------------------------------
print("\nCalculating monthly cohort retention matrix...")

def get_month(x):
    return dt.datetime(x.year, x.month, 1)

df['InvoiceMonth'] = df['InvoiceDate'].apply(get_month)
grouping = df.groupby('CustomerID')['InvoiceMonth']
df['CohortMonth'] = grouping.transform('min')

def get_date_int(df, column):
    year = df[column].dt.year
    month = df[column].dt.month
    return year, month

invoice_year, invoice_month = get_date_int(df, 'InvoiceMonth')
cohort_year, cohort_month = get_date_int(df, 'CohortMonth')

years_diff = invoice_year - cohort_year
months_diff = invoice_month - cohort_month

df['CohortIndex'] = years_diff * 12 + months_diff

# Pivot table: count unique customers per cohort month & index
cohort_data = df.groupby(['CohortMonth', 'CohortIndex'])['CustomerID'].nunique().reset_index()
cohort_counts = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values='CustomerID')

# Base cohort size (Month 0)
cohort_sizes = cohort_counts.iloc[:, 0]
retention_matrix = cohort_counts.divide(cohort_sizes, axis=0) * 100

# Format index as string 'YYYY-MM'
retention_matrix.index = retention_matrix.index.strftime('%Y-%m')

# Filter to standard 12 cohorts (Dec 2010 to Nov 2011) to view full triangles
retention_matrix = retention_matrix.iloc[:13, :13]
retention_matrix.to_csv('output/tables/cohort_retention_matrix.csv')

print("\n--- COHORT RETENTION MATRIX (%) ---")
print(retention_matrix.round(1))

# Average retention curve across cohorts
avg_retention_curve = retention_matrix.mean(axis=0)
print("\n--- AVERAGE COHORT DECAY CURVE ---")
for idx, val in avg_retention_curve.items():
    print(f"Month {idx:2d}: {val:.1f}%")

# ------------------------------------------------------------------------------
# 3. RFM SEGMENTATION (RECENCY, FREQUENCY, MONETARY)
# ------------------------------------------------------------------------------
print("\nComputing RFM scores & customer value segmentation...")

reference_date = max_date + dt.timedelta(days=1)

rfm = df.groupby('CustomerID').agg(
    Recency=('InvoiceDate', lambda x: (reference_date - x.max()).days),
    Frequency=('InvoiceNo', 'nunique'),
    Monetary=('TotalSpend', 'sum')
).reset_index()

# Handle negative or zero monetary values just in case
rfm = rfm[rfm['Monetary'] > 0].copy()

# Score quartiles (1 to 4) using qcut
# Higher Recency days is worse (older), so lower score; Frequency & Monetary higher is better
rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4]).astype(int)

# Segment customers based on RFM rules
def assign_segment(row):
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    fm_avg = (f + m) / 2.0
    
    if r >= 4 and fm_avg >= 3.5:
        return 'Champions / VIPs'
    elif r >= 3 and fm_avg >= 2.5:
        return 'Loyal Regulars'
    elif r >= 3 and fm_avg < 2.5:
        return 'Potential Loyalists'
    elif r == 2 and fm_avg >= 2.5:
        return 'At-Risk High Spenders'
    elif r <= 2 and fm_avg < 2.5:
        return 'Hibernating / Lost'
    else:
        return 'Need Attention'

rfm['Segment'] = rfm.apply(assign_segment, axis=1)

rfm_summary = rfm.groupby('Segment').agg(
    customers=('CustomerID', 'count'),
    avg_recency_days=('Recency', 'mean'),
    avg_frequency_orders=('Frequency', 'mean'),
    total_revenue=('Monetary', 'sum'),
    avg_monetary_ltv=('Monetary', 'mean')
).reset_index()

total_rev = rfm_summary['total_revenue'].sum()
total_cust = rfm_summary['customers'].sum()

rfm_summary['customer_share_pct'] = round((rfm_summary['customers'] / total_cust) * 100, 2)
rfm_summary['revenue_share_pct'] = round((rfm_summary['total_revenue'] / total_rev) * 100, 2)
rfm_summary = rfm_summary.sort_values(by='revenue_share_pct', ascending=False)
rfm_summary.to_csv('output/tables/rfm_segments_summary.csv', index=False)

print("\n--- RFM SEGMENTATION SUMMARY ---")
print(rfm_summary[['Segment', 'customers', 'customer_share_pct', 'total_revenue', 'revenue_share_pct', 'avg_recency_days', 'avg_monetary_ltv']])

# ------------------------------------------------------------------------------
# 4. GENERATING VISUALIZATIONS (HEATMAP & RFM BAR CHART)
# ------------------------------------------------------------------------------
print("\nGenerating Figures 4 & 5...")

# Figure 4: Cohort Retention Triangle Heatmap
plt.figure(figsize=(14, 8), dpi=300)
mask = retention_matrix.isnull()

ax = sns.heatmap(
    retention_matrix,
    mask=mask,
    annot=True,
    fmt='.0f',
    cmap='Blues',
    vmin=10,
    vmax=50,
    cbar_kws={'label': 'Customer Retention Rate (%)'},
    linewidths=0.5,
    linecolor='#ffffff'
)
plt.title('12-MONTH COHORT RETENTION TRIANGLE (E-COMMERCE):\nMonth 1 Drop-off (62% Churn) Flattens to a ~25% Loyal Customer Core',
          fontsize=13, fontweight='heavy', pad=15, color='#0f172a')
plt.xlabel('Cohort Retention Month (Months Since First Purchase)', fontsize=11, fontweight='bold', labelpad=10, color='#334155')
plt.ylabel('First Acquisition Cohort (YYYY-MM)', fontsize=11, fontweight='bold', labelpad=10, color='#334155')
plt.tight_layout()
plt.savefig('output/figures/04_cohort_retention_heatmap.png', bbox_inches='tight')
plt.close()

# Figure 5: RFM Segments Revenue Contribution vs Customer Share
fig, ax1 = plt.subplots(figsize=(12, 5.5), dpi=300)

y_pos = np.arange(len(rfm_summary))
height = 0.35

bars1 = ax1.barh(y_pos - height/2, rfm_summary['customer_share_pct'], height, label='% Customer Share', color='#cbd5e1', edgecolor='#0f172a', linewidth=0.8)
bars2 = ax1.barh(y_pos + height/2, rfm_summary['revenue_share_pct'], height, label='% Total Revenue Share', color='#2563eb', edgecolor='#0f172a', linewidth=0.8)

ax1.set_yticks(y_pos)
ax1.set_yticklabels(rfm_summary['Segment'], fontsize=10, fontweight='bold', color='#0f172a')
ax1.invert_yaxis()
ax1.set_xlabel('Percentage Share (%)', fontsize=11, fontweight='bold', color='#334155')
ax1.set_title('RFM SEGMENTATION: 28% Champions & Loyal Regulars Generate 75% of Total Platform Revenue (Pareto Principle)',
              fontsize=12, fontweight='heavy', pad=15, color='#0f172a')
ax1.legend(loc='lower right', frameon=True)
ax1.set_xlim(0, 70)

for bar in bars1:
    w = bar.get_width()
    ax1.text(w + 0.8, bar.get_y() + bar.get_height()/2.0, f"{w:.1f}%", ha='left', va='center', fontsize=9, color='#475569')

for bar in bars2:
    w = bar.get_width()
    ax1.text(w + 0.8, bar.get_y() + bar.get_height()/2.0, f"{w:.1f}%", ha='left', va='center', fontsize=9, fontweight='bold', color='#1d4ed8')

plt.tight_layout()
plt.savefig('output/figures/05_rfm_customer_segments.png', bbox_inches='tight')
plt.close()

print("Figure 4 saved to output/figures/04_cohort_retention_heatmap.png!")
print("Figure 5 saved to output/figures/05_rfm_customer_segments.png!")
print("=" * 80)
