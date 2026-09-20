"""
E-Commerce Cohort Retention & RFM Customer Segmentation
Dataset: Online Retail Transaction Logs (541,909 records)

Analysis of customer lifecycle dynamics, 12-month cohort retention decay,
and value-based customer segmentation (Recency, Frequency, Monetary).
"""

# %%
import os
import datetime as dt
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Resolve data path whether executing from repo root or analysis folder
data_path = 'Online_Retail.csv' if os.path.exists('Online_Retail.csv') else os.path.join('..', 'Online_Retail.csv')
df_raw = pd.read_csv(data_path, encoding='ISO-8859-1')

print(f"Raw transaction logs loaded: {len(df_raw):,} rows, {df_raw.shape[1]} columns")
print(df_raw.head(5))

# %%
# Data Hygiene: Address guest checkouts and return transactions
# 1. Unauthenticated guest checkouts (missing CustomerID) cannot be tracked longitudinally
missing_customers = df_raw['CustomerID'].isna().sum()
print(f"Guest transactions without CustomerID: {missing_customers:,} ({missing_customers/len(df_raw)*100:.2f}%)")

# 2. Retain authenticated accounts and enforce integer identifier
df = df_raw.dropna(subset=['CustomerID']).copy()
df['CustomerID'] = df['CustomerID'].astype(int)

# 3. Filter out cancellations (InvoiceNo starting with 'C') and non-positive prices/quantities
df = df[~df['InvoiceNo'].str.startswith('C', na=False) & (df['Quantity'] > 0) & (df['UnitPrice'] > 0)].copy()

# 4. Derive total monetary spend per line item
df['TotalSpend'] = df['Quantity'] * df['UnitPrice']

print(f"Cleaned purchase logs: {len(df):,} transactions ({len(df)/len(df_raw)*100:.2f}% retained)")
print(f"Unique tracked customer accounts: {df['CustomerID'].nunique():,}")

# %%
# Cohort Assignment: Map acquisition cohorts and elapsed active months
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])
df['InvoiceMonth'] = df['InvoiceDate'].dt.to_period('M')

# Identify the acquisition month (first purchase) for each customer
df['CohortMonth'] = df.groupby('CustomerID')['InvoiceMonth'].transform('min')

# Calculate CohortIndex (months elapsed since initial acquisition)
years_diff = df['InvoiceMonth'].dt.year - df['CohortMonth'].dt.year
months_diff = df['InvoiceMonth'].dt.month - df['CohortMonth'].dt.month
df['CohortIndex'] = years_diff * 12 + months_diff

print("Sample customer cohort mapping:")
print(df[['CustomerID', 'InvoiceDate', 'InvoiceMonth', 'CohortMonth', 'CohortIndex']].head(8))

# %%
# Cohort Retention Matrix: Compute monthly returning percentage per cohort
cohort_data = df.groupby(['CohortMonth', 'CohortIndex'])['CustomerID'].nunique().reset_index()
cohort_counts = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values='CustomerID')

# Base cohort sizes (Month 0 active customer volume)
cohort_sizes = cohort_counts.iloc[:, 0]
retention_matrix = cohort_counts.divide(cohort_sizes, axis=0) * 100

print("=== COHORT BASE SIZES (Month 0 Customer Volume) ===")
print(cohort_sizes)

print("\n=== COHORT RETENTION MATRIX (% Active Returning) ===")
print(retention_matrix.round(1).iloc[:6, :7])

# %%
# Visualizing Cohort Retention Decay (The Retention Triangle Heatmap)
plt.figure(figsize=(15, 8))
plt.title('12-Month Cohort Retention Triangle (% Customers Returning)', fontsize=14, fontweight='bold', pad=15)

# Mask unpopulated upper-right cells
mask = retention_matrix.isnull()

sns.heatmap(
    data=retention_matrix,
    annot=True,
    fmt='.1f',
    cmap='YlGnBu',
    vmin=0,
    vmax=50,
    mask=mask,
    cbar_kws={'label': 'Retention Rate (%)'}
)

plt.ylabel('Cohort Acquisition Month', fontsize=12)
plt.xlabel('Cohort Index (Months Elapsed Since First Purchase)', fontsize=12)
plt.yticks(rotation=0)
plt.tight_layout()
plt.show()

# %%
# RFM Metrics Calculation
# Use the day following the latest transaction as the fixed reference analysis point
reference_date = df['InvoiceDate'].max() + dt.timedelta(days=1)

rfm = df.groupby('CustomerID').agg(
    Recency=('InvoiceDate', lambda x: (reference_date - x.max()).days),
    Frequency=('InvoiceNo', 'nunique'),
    Monetary=('TotalSpend', 'sum')
).reset_index()

rfm = rfm[rfm['Monetary'] > 0].copy()

print(f"Total customers profiled for RFM: {len(rfm):,}")
print(f"Reference analysis date: {reference_date.strftime('%Y-%m-%d')}")
print("\nSample RFM profiles:")
print(rfm.head(5).round(2))

# %%
# RFM Scoring & Segment Categorization
# Quartile binning: R inverted (lower days = higher score), F and M standard (higher = higher score)
rfm['R_Score'] = pd.qcut(rfm['Recency'], 4, labels=[4, 3, 2, 1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 4, labels=[1, 2, 3, 4]).astype(int)

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

# Executive Segment Summary
rfm_summary = rfm.groupby('Segment').agg(
    Customers=('CustomerID', 'count'),
    Avg_Recency_Days=('Recency', 'mean'),
    Avg_Orders=('Frequency', 'mean'),
    Total_Revenue=('Monetary', 'sum'),
    Avg_Spend_LTV=('Monetary', 'mean')
).reset_index()

total_rev = rfm_summary['Total_Revenue'].sum()
total_cust = rfm_summary['Customers'].sum()

rfm_summary['Customer_Share_%'] = (rfm_summary['Customers'] / total_cust) * 100
rfm_summary['Revenue_Share_%'] = (rfm_summary['Total_Revenue'] / total_rev) * 100
rfm_summary = rfm_summary.sort_values(by='Revenue_Share_%', ascending=False)

print("=== RFM EXECUTIVE SEGMENTATION SUMMARY ===")
print(rfm_summary[['Segment', 'Customers', 'Customer_Share_%', 'Total_Revenue', 'Revenue_Share_%', 'Avg_Recency_Days', 'Avg_Spend_LTV']].round(2))

# %%
# Visualizing Pareto Value Concentration
melted_summary = rfm_summary.melt(
    id_vars='Segment',
    value_vars=['Customer_Share_%', 'Revenue_Share_%'],
    var_name='Metric',
    value_name='Percentage'
)

plt.figure(figsize=(13, 6))
sns.barplot(
    data=melted_summary,
    x='Segment',
    y='Percentage',
    hue='Metric',
    palette=['#6baed6', '#3182bd']
)

plt.title('Customer Share vs Revenue Share by RFM Segment (Pareto Principle)', fontsize=14, fontweight='bold', pad=15)
plt.ylabel('Percentage (%)', fontsize=12)
plt.xlabel('Customer Segment', fontsize=12)
plt.xticks(rotation=15, ha='right', fontsize=10)
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.legend(title='Metric', frameon=True)
plt.tight_layout()
plt.show()
