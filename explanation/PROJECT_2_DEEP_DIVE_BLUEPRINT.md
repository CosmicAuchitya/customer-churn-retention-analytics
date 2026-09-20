# 📘 Project 2: Churn Forensics & Cohort Retention Blueprint
**Project:** Customer Churn & Cohort Retention Analytics  
**Target Role:** Insight Analyst / Product & Commercial Data Analyst  
**Author:** CosmicAuchitya

---

## Table of Contents
1. [Core Data Hygiene & The `TotalCharges` Trap](#1-core-data-hygiene--the-totalcharges-trap)
2. [Module 1: The Month-to-Month Contract Death Trap](#module-1-the-month-to-month-contract-death-trap)
3. [Module 2: The Fiber Optic Paradox & The Tech Support Moat](#module-2-the-fiber-optic-paradox--the-tech-support-moat)
4. [Module 3: Payment Psychology & Friction Analysis](#module-3-payment-psychology--friction-analysis)
5. [Module 4: 12-Month Cohort Retention Matrix (The Triangle Heatmap)](#module-4-12-month-cohort-retention-matrix-the-triangle-heatmap)
6. [Module 5: RFM Customer Value Segmentation (Pareto 80/20)](#module-5-rfm-customer-value-segmentation-pareto-8020)
7. [Golden Rules for the Interview](#7-golden-rules-for-the-interview)

---

## 1. Core Data Hygiene & The `TotalCharges` Trap

### 🧠 1. Business & Technical Mindset (Hinglish)
Jab aap `Telco-Customer-Churn.csv` load karte hain, to `TotalCharges` column float ki jagah **Object (String)** data type dikhata hai.
Kyun? Kyunki dataset mein 11 customers aise the jinka `tenure == 0` tha (matlab unhone kal hi join kiya tha, pehla bill generate nahi hua tha). Database ne unki TotalCharges mein space (`" "`) daal diya tha.
Agar koi direct `df['TotalCharges'].astype(float)` karega to error aayega: `ValueError: could not convert string to float: ' '`.

### 🔬 2. Line-by-Line Blueprint

```python
# Convert empty spaces to NaN, then impute with 0.0 for tenure == 0
df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
df['TotalCharges'] = df['TotalCharges'].fillna(0.0)
```
- `errors='coerce'`: Space `" "` ko `NaN` bana deta hai bina code crash kiye.
- `fillna(0.0)`: 0 tenure wale naye customers ka total billing abhi $0 hai, isliye 0.0 se fill kiya.

### 🗣️ 3. English Interview Script
> *"During initial data hygiene profiling, I discovered an anomaly where `TotalCharges` was typed as an object due to whitespace characters across 11 records where `tenure = 0`. These represented newly onboarded subscribers whose first billing cycle had not yet matured. I handled this by using `pd.to_numeric(errors='coerce')` and imputing zero charges, ensuring mathematical integrity across our lifetime value calculations."*

---

## Module 1: The Month-to-Month Contract Death Trap

### 🧠 1. Business Mindset (Hinglish)
- **Problem:** Company har saal $1.67M ka Annual Recurring Revenue (ARR) churn mein kho rahi hai. Churn sabse zyada kahan se leak ho raha hai?
- **Hypothesis:** Long-term contract (1-yr, 2-yr) customer ko lock karke rakhta hai. Month-to-month contracts mein koi switching barrier nahi hota.
- **Goal:** Group karo contract type se aur calculate karo churn rate aur total churn mein iska hissa (share of churn).

### 🔬 2. Line-by-Line Blueprint

```python
contract_df = df.groupby('Contract').agg(
    total_accounts=('customerID', 'count'),
    churned_accounts=('Churn_Numeric', 'sum'),
    churn_rate=('Churn_Numeric', lambda x: round(x.mean() * 100, 2)),
    monthly_revenue_at_risk=('MonthlyCharges', lambda x: df.loc[x.index][df.loc[x.index, 'Churn_Numeric'] == 1]['MonthlyCharges'].sum())
).reset_index()

contract_df['share_of_total_churn_pct'] = round((contract_df['churned_accounts'] / churned_customers) * 100, 2)
contract_df['annual_arr_lost'] = contract_df['monthly_revenue_at_risk'] * 12
```

- **Core Finding:**
  - **Month-to-month:** 42.71% churn rate. **88.55% of all platform churn** yahi se aata hai ($1.45M ARR lost!).
  - **Two-year contract:** Sirf 2.83% churn rate!
  - **15x difference!**

### 🗣️ 3. English Interview Script
> *"I evaluated churn distribution across contractual agreements. The data revealed a staggering 'Month-to-Month Death Trap': while month-to-month contracts represented 55% of the subscriber base, they drove 88.55% of all churn events, bleeding $1.45M in annual ARR at a 42.7% churn rate. Conversely, subscribers on two-year agreements exhibited an exceptional 2.8% churn rate (a 15x stability multiplier). I modeled an incentive strategy offering a $5 monthly discount to migrate month-to-month users into annual commitments, projecting a $230K net EBITDA preservation."*

---

## Module 2: The Fiber Optic Paradox & The Tech Support Moat

### 🧠 1. Business Mindset (Hinglish)
- **The Paradox:** Company ka sabse expensive internet product (**Fiber Optic**, $91.50/month bill) hai. Management soch rahi thi ki high-speed internet se log khush honge.
- **The Reality Check:** Fiber Optic ka churn rate **41.89%** tha! Adhe se zyada log chhod kar bhaag rahe the!
- **Deeper Investigation:** Kya log high price ki wajah se bhaag rahe the ya technical problems ki wajah se?
- **The Discovery:** Jin Fiber Optic customers ke paas **Tech Support** aur **Online Security** tha, unka churn rate **55% se gir kar 14.2%** ho gaya! Aur unka monthly bill aur zyada ($105/month) tha! Customer price se nahi, support na milne se bhaag raha tha!

### 🔬 2. Line-by-Line Blueprint

```python
fiber_df['protection_bundle'] = np.where(
    (fiber_df['TechSupport'] == 'Yes') & (fiber_df['OnlineSecurity'] == 'Yes'),
    'Full Security Bundle (Both Yes)',
    np.where(
        (fiber_df['TechSupport'] == 'No') & (fiber_df['OnlineSecurity'] == 'No'),
        'Zero Protection (Both No)',
        'Partial Protection (One Yes)'
    )
)
```

- **Zero Protection (No Tech Support, No Security):** **55.01% Churn Rate** ($86.10 AOV).
- **Full Protection Bundle (Both Active):** **14.17% Churn Rate** ($105.73 AOV).
- **Churn Reduction:** **40.8 percentage point drop!**

### 🗣️ 3. English Interview Script
> *"I identified a critical counter-intuitive insight termed 'The Fiber Optic Paradox'. The company's highest-tier product, Fiber Optic, was experiencing a 41.9% churn rate despite commanding a $91.50 monthly ARPU. By cross-tabulating service add-ons, I uncovered 'The Tech Support Moat': Fiber Optic subscribers with zero protection churned at 55.0%, but when bundled with Tech Support and Online Security, churn plummeted to 14.2%, while monthly billings increased to $105.73. This proved that customers were not price-sensitive, but support-sensitive; packaging Tech Support directly into the base Fiber tier creates an immediate switching barrier."*

---

## Module 3: Payment Psychology & Friction Analysis

### 🧠 1. Business Mindset (Hinglish)
- **Problem:** Kya payment method se customer churn par asar padta hai?
- **Behavioral Economics Concept:** *"The Pain of Paying"*.
  - Jab koi **Electronic Check** se payment karta hai, to use har mahine manually portal par jaakar bill dekhna padta hai aur click karna padta hai. Har mahine uske dimaag mein sawaal aata hai: *"Kya mujhe ye service chahiye?"*
  - Jab koi **Auto-Pay (Credit Card / Bank Transfer)** par hota hai, to payment background mein automatically hoti hai aur cognitive friction zero ho jaata hai.

### 🔬 2. Line-by-Line Blueprint

```python
payment_df = df.groupby('PaymentMethod').agg(
    accounts=('customerID', 'count'),
    churn_rate=('Churn_Numeric', lambda x: round(x.mean() * 100, 2)),
    monthly_churn_loss=('MonthlyCharges', lambda x: df.loc[x.index][df.loc[x.index, 'Churn_Numeric'] == 1]['MonthlyCharges'].sum())
).reset_index().sort_values(by='churn_rate', ascending=False)
```

- **Electronic Check:** **45.29% Churn Rate** (Accounts for 57.3% of total platform churn, $1.01M ARR loss!).
- **Credit Card (Auto-Pay):** **15.24% Churn Rate** (3x safer!).

### 🗣️ 3. English Interview Script
> *"I analyzed payment infrastructure through a behavioral economics lens. Customers utilizing manual 'Electronic Checks' suffered an alarming 45.3% churn rate, accounting for 57.3% of all platform revenue loss ($1.01M ARR). In contrast, automated methods like Credit Card and Bank Transfer exhibited churn rates of only 15.2% and 16.7%. Automated billing eliminates the recurring 'Pain of Paying' cognitive friction, making auto-pay opt-in promotions a high-ROI retention lever."*

---

## Module 4: 12-Month Cohort Retention Matrix (The Triangle Heatmap)

### 🧠 1. Business Mindset (Hinglish)
- **What is a Cohort?** A group of users who made their first purchase in the same month (e.g., Dec 2010 Cohort, Jan 2011 Cohort).
- **The Business Question:** Jab 100 log pehli baar aate hain, to kitne log agle mahine (Month 1), 3 mahine baad (Month 3), aur 12 mahine baad (Month 12) khareedte hain?
- **Why Triangle?** December 2010 cohort ko 12 mahine track kiya ja sakta hai. Lekin November 2011 cohort ko sirf 1 mahina track kiya ja sakta hai (kyunki dataset Dec 2011 mein khatam ho jata hai). Isliye chart ek **Triangle** banta hai!

### 🔬 2. Line-by-Line Blueprint

```python
# 1. First purchase month per customer
df['CohortMonth'] = df.groupby('CustomerID')['InvoiceMonth'].transform('min')

# 2. Months elapsed between invoice date and first purchase date
df['CohortIndex'] = (invoice_year - cohort_year) * 12 + (invoice_month - cohort_month)

# 3. Pivot table to create the retention matrix
cohort_counts = df.groupby(['CohortMonth', 'CohortIndex'])['CustomerID'].nunique().unstack()
cohort_sizes = cohort_counts.iloc[:, 0]
retention_matrix = cohort_counts.divide(cohort_sizes, axis=0) * 100
```

- **Average Retention Curve:**
  - **Month 0:** 100%
  - **Month 1:** 20.6% (Initial 80% Drop-off!)
  - **Month 3 to 12:** Stabilizes at **24% to 26%** loyal core!

### 🗣️ 3. English Interview Script
> *"On the transactional retail dataset (540K+ records), I engineered a 12-month cohort retention matrix. After cleaning unauthenticated guest sessions and refund outliers, I established customer acquisition cohorts (`CohortMonth`) and calculated monthly retention indices (`CohortIndex = 0 to 12`). The resulting triangular heatmap demonstrated a classic steep drop-off at Month 1 (averaging 20.6% retention), which then stabilized into a remarkably consistent 24% to 26% loyal core through Month 12. This proved to leadership that retention interventions must occur within the first 30 days of onboarding before customer drop-off cements."*

---

## Module 5: RFM Customer Value Segmentation (Pareto 80/20)

### 🧠 1. Business Mindset (Hinglish)
- **RFM Framework:**
  - **Recency (R):** Aakhiri baar kab kharida tha? (Recent = high score).
  - **Frequency (F):** Kitni baar kharida? (High orders = high score).
  - **Monetary (M):** Total kitne pound kharch kiye? (High spend = high score).
- **The Pareto 80/20 Rule:** Kya hamara 80% revenue sirf top 20-30% customers se aa raha hai?

### 🔬 2. Line-by-Line Blueprint

```python
reference_date = max_date + dt.timedelta(days=1)
rfm = df.groupby('CustomerID').agg(
    Recency=('InvoiceDate', lambda x: (reference_date - x.max()).days),
    Frequency=('InvoiceNo', 'nunique'),
    Monetary=('TotalSpend', 'sum')
)
```

- **The Findings:**
  - **Champions / VIPs (15.3% of customers):** Generate **53.5% of total revenue ($4.77M)**! Avg spend = $7,184.
  - **Loyal Regulars (21.9% of customers):** Generate **24.1% of revenue ($2.15M)**!
  - **The 80/20 Proof:** Top 37.2% of customers generate **77.6% of total company revenue ($6.92M)**!
  - **The At-Risk VIPs:** 550 accounts represent **$912,863 in historical spend**, but haven't bought in **84.4 days**! Inhe immediate proactive outreach chahiye!

### 🗣️ 3. English Interview Script
> *"I segmented 4,338 authenticated retail accounts using RFM analysis across quartiles. The analysis validated the classic Pareto principle: the top 37.2% of customers (Champions and Loyal Regulars) generated 77.6% of the platform's $8.9M lifetime revenue. Crucially, I isolated an 'At-Risk High Spenders' segment of 550 accounts who had spent over $912,000 historically but had gone dormant for an average of 84.4 days. I designed an automated high-touch concierge reactivation workflow, projected to recover up to $180,000 in recurring retail GMV."*

---

## 7. Golden Rules for the Interview
1. **Always lead with the business metric:** Say *$1.67M ARR lost to churn* instead of *26.5% churn*.
2. **Explain the contrast between models:** Highlight that you understand **Contractual Subscription Churn (Telco)** AND **Non-Contractual Cohort Decay (Retail)**.
3. **Use the B.Com advantage:** Explain how customer acquisition cost (CAC) payback periods fail when month-to-month contracts churn within 90 days.
