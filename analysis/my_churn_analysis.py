"""
Subscription Churn Analysis & Revenue Risk Modeling
Dataset: Telco Customer Churn (7,043 customer accounts)

Exploratory analysis identifying structural churn drivers across contracts,
services, billing friction, and tenure cohorts.
"""

# %%
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Resolve data path whether executing from repo root or analysis folder
data_path = 'Telco-Customer-Churn.csv' if os.path.exists('Telco-Customer-Churn.csv') else os.path.join('..', 'Telco-Customer-Churn.csv')
df = pd.read_csv(data_path)

print(f"Dataset ingested: {df.shape[0]:,} rows, {df.shape[1]} columns")
print(df.head(5))

# %%
# Data Hygiene: Identify and resolve data type discrepancies
# TotalCharges contains whitespace strings for zero-tenure accounts
blank_charges = df[df['TotalCharges'].str.strip() == '']
print(f"Zero-tenure records with blank TotalCharges: {len(blank_charges)}")

# Coerce non-numeric entries to NaN and impute with 0.0 for newly onboarded customers
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce').fillna(0.0)

# Encode churn indicator as binary integer (1 = Churned, 0 = Retained)
df['Churn_Numeric'] = (df['Churn'] == 'Yes').astype(int)

# %%
# Baseline Executive Scorecard
total_customers = len(df)
churned_customers = df['Churn_Numeric'].sum()
churn_rate = (churned_customers / total_customers) * 100

total_mrr = df['MonthlyCharges'].sum()
churned_mrr = df[df['Churn_Numeric'] == 1]['MonthlyCharges'].sum()
annual_arr_lost = churned_mrr * 12

print("=== BASELINE CHURN SCORECARD ===")
print(f"Total Active Accounts  : {total_customers:,}")
print(f"Churned Accounts       : {churned_customers:,} ({churn_rate:.2f}%)")
print(f"Monthly Recurring (MRR): ${total_mrr:,.2f}")
print(f"MRR Lost to Churn      : ${churned_mrr:,.2f} / month")
print(f"Annual ARR at Risk     : ${annual_arr_lost:,.2f} / year")

# Reusable filter for churned accounts
churned_filter = df[df['Churn_Numeric'] == 1]

# %%
# Contract Type Analysis: Evaluate churn concentration across contract horizons
contract_analysis = df.groupby('Contract').agg(
    Total_Customers=('customerID', 'count'),
    Churned_Customers=('Churn_Numeric', 'sum'),
    Avg_Monthly_Bill=('MonthlyCharges', 'mean')
)

contract_analysis['Churn_Rate_%'] = (contract_analysis['Churned_Customers'] / contract_analysis['Total_Customers']) * 100
contract_analysis['Monthly_Revenue_Lost_$'] = churned_filter.groupby('Contract')['MonthlyCharges'].sum()

print("=== CHURN BY CONTRACT STRUCTURE ===")
print(contract_analysis.round(2))

# %%
# Internet Service Breakdown: Compare retention across infrastructure tiers
internet_analysis = df.groupby('InternetService').agg(
    Total_Customers=('customerID', 'count'),
    Churned_Customers=('Churn_Numeric', 'sum'),
    Avg_Monthly_Bill=('MonthlyCharges', 'mean')
)

internet_analysis['Churn_Rate_%'] = (internet_analysis['Churned_Customers'] / internet_analysis['Total_Customers']) * 100
internet_analysis['Monthly_Revenue_Lost_$'] = churned_filter.groupby('InternetService')['MonthlyCharges'].sum()

print("=== CHURN BY INTERNET SERVICE TIER ===")
print(internet_analysis.round(2))

# %%
# Fiber Optic & Tech Support Reality:
# Empirical comparison of churn rates and ARPU with vs. without technical support.
# Note: Recommendations to bundle free support are intentionally withheld because
# the dataset does not include operational cost-to-serve / technician overhead data.
fiber_df = df[df['InternetService'] == 'Fiber optic']

tech_support_analysis = fiber_df.groupby('TechSupport').agg(
    Total_Customers=('customerID', 'count'),
    Churned_Customers=('Churn_Numeric', 'sum'),
    Avg_Monthly_Bill=('MonthlyCharges', 'mean')
)

tech_support_analysis['Churn_Rate_%'] = (tech_support_analysis['Churned_Customers'] / tech_support_analysis['Total_Customers']) * 100
tech_support_analysis['Monthly_Revenue_Lost_$'] = fiber_df[fiber_df['Churn_Numeric'] == 1].groupby('TechSupport')['MonthlyCharges'].sum()

print("=== FIBER OPTIC: TECH SUPPORT EMPIRICAL COMPARISON ===")
print(tech_support_analysis.round(2))

# %%
# Payment Method Friction: Contrast manual billing vs automated recurring payments
payment_analysis = df.groupby('PaymentMethod').agg(
    Total_Customers=('customerID', 'count'),
    Churned_Customers=('Churn_Numeric', 'sum'),
    Avg_Monthly_Bill=('MonthlyCharges', 'mean')
)

payment_analysis['Churn_Rate_%'] = (payment_analysis['Churned_Customers'] / payment_analysis['Total_Customers']) * 100
payment_analysis['Monthly_Revenue_Lost_$'] = churned_filter.groupby('PaymentMethod')['MonthlyCharges'].sum()

print("=== CHURN BY PAYMENT METHOD ===")
print(payment_analysis.round(2).sort_values(by='Churn_Rate_%', ascending=False))

# %%
# Tenure Cohort Analysis: Identify churn timing across customer lifecycle
tenure_bins = [0, 12, 24, 48, 72]
tenure_labels = ['0-12 Months (Year 1)', '13-24 Months (Year 2)', '25-48 Months (Year 3-4)', '49-72 Months (Year 5-6)']

df['Tenure_Cohort'] = pd.cut(df['tenure'], bins=tenure_bins, labels=tenure_labels, include_lowest=True)

tenure_analysis = df.groupby('Tenure_Cohort', observed=False).agg(
    Total_Customers=('customerID', 'count'),
    Churned_Customers=('Churn_Numeric', 'sum'),
    Avg_Monthly_Bill=('MonthlyCharges', 'mean')
)

tenure_analysis['Churn_Rate_%'] = (tenure_analysis['Churned_Customers'] / tenure_analysis['Total_Customers']) * 100
tenure_analysis['Monthly_Revenue_Lost_$'] = churned_filter.groupby(df['Tenure_Cohort'], observed=False)['MonthlyCharges'].sum()

print("=== TENURE COHORT LIFECYCLE DECAY ===")
print(tenure_analysis.round(2))

# %%
# Visualizing Core Churn Dimensions
sns.set_theme(style="whitegrid")
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Contract churn visualization
sns.barplot(
    data=contract_analysis.reset_index(),
    x='Contract',
    y='Churn_Rate_%',
    hue='Contract',
    palette=['#d9534f', '#f0ad4e', '#5cb85c'],
    legend=False,
    ax=axes[0]
)
axes[0].set_title('Churn Rate by Contract Horizon', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Churn Rate (%)')
axes[0].set_xlabel('')

# Payment method churn visualization
sns.barplot(
    data=payment_analysis.reset_index(),
    x='Churn_Rate_%',
    y='PaymentMethod',
    hue='PaymentMethod',
    palette=['#d9534f', '#f0ad4e', '#5bc0de', '#5cb85c'],
    legend=False,
    ax=axes[1]
)
axes[1].set_title('Churn Rate by Payment Mechanism', fontsize=12, fontweight='bold')
axes[1].set_xlabel('Churn Rate (%)')
axes[1].set_ylabel('')

plt.tight_layout()
plt.show()
