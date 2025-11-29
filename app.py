import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Serverless FinOps Dashboard", layout="wide")

st.title("🔍 Serverless Cost Analysis – FinOps Dashboard")
st.write("Upload your **Serverless_Data.csv** to begin.")

uploaded = st.file_uploader("📁 Upload CSV", type=["csv"])

if not uploaded:
    st.info("Waiting for Serverless_Data.csv…")
    st.stop()

# ===========================
# AUTO-FIX FOR MALFORMED CSV
# ===========================
try:
    df = pd.read_csv(uploaded)
    
    # If only one column exists, it means the CSV is malformed
    if len(df.columns) == 1:
        st.warning("CSV detected as single-column. Attempting automatic repair…")
        
        # Re-read with no header and split manually
        uploaded.seek(0)  # reset file pointer
        temp = pd.read_csv(uploaded, header=None)
        
        # split the one column by commas
        df = temp[0].str.split(",", expand=True)
        
        # assign correct columns
        df.columns = [
            "FunctionName",
            "Environment",
            "InvocationsPerMonth",
            "AvgDurationMs",
            "MemoryMB",
            "ColdStartRate",
            "ProvisionedConcurrency",
            "GBSeconds",
            "DataTransferGB",
            "CostUSD",
        ]
except Exception as e:
    st.error(f"Failed to parse CSV: {e}")
    st.stop()

# Convert numeric fields
for col in ["InvocationsPerMonth","AvgDurationMs","MemoryMB","ColdStartRate",
            "ProvisionedConcurrency","GBSeconds","DataTransferGB","CostUSD"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

st.subheader("📄 Dataset Preview")
st.dataframe(df)

# =======================================
# EXERCISE 1 — TOP COST CONTRIBUTORS
# =======================================
st.header("1️⃣ Top Cost Contributors")

total_cost = df["CostUSD"].sum()
df_sorted = df.sort_values("CostUSD", ascending=False)
df_sorted["CostPercent"] = df_sorted["CostUSD"] / total_cost * 100
df_sorted["CumulativeCost"] = df_sorted["CostPercent"].cumsum()

top_80 = df_sorted[df_sorted["CumulativeCost"] <= 80]

st.subheader("🏆 Functions that make up 80% of total spend:")
st.dataframe(top_80)

fig1, ax1 = plt.subplots()
ax1.scatter(df["InvocationsPerMonth"], df["CostUSD"])
ax1.set_xlabel("Invocations Per Month")
ax1.set_ylabel("Cost (USD)")
ax1.set_title("Cost vs Invocation Frequency")
st.pyplot(fig1)

# =======================================
# EXERCISE 2 — MEMORY RIGHT-SIZING
# =======================================
st.header("2️⃣ Memory Right-Sizing")

right_sizing = df[(df["AvgDurationMs"] < 600) & (df["MemoryMB"] > 1024)]
st.dataframe(right_sizing)

right_sizing["EstimatedSavings"] = right_sizing["CostUSD"] * 0.30
st.subheader("💰 Estimated Savings if Memory Reduced:")
st.dataframe(right_sizing[["FunctionName","MemoryMB","AvgDurationMs","CostUSD","EstimatedSavings"]])

# =======================================
# EXERCISE 3 — PROVISIONED CONCURRENCY
# =======================================
st.header("3️⃣ Provisioned Concurrency Optimization")

pc = df[df["ProvisionedConcurrency"] > 0]
st.subheader("⚙️ Functions using Provisioned Concurrency:")
st.dataframe(pc)

pc["Recommendation"] = pc.apply(
    lambda row: "❌ Reduce / Remove PC" if row["ColdStartRate"] < 10 else "✔️ Keep PC",
    axis=1
)

st.subheader("📝 Recommendations:")
st.dataframe(pc[["FunctionName","ColdStartRate","ProvisionedConcurrency","CostUSD","Recommendation"]])

# =======================================
# EXERCISE 4 — LOW-VALUE WORKLOADS
# =======================================
st.header("4️⃣ Low-Value / Unused Workloads")

inv_threshold = df["InvocationsPerMonth"].sum() * 0.01
low_value = df[
    (df["InvocationsPerMonth"] < inv_threshold) &
    (df["CostUSD"] > df["CostUSD"].mean())
]

st.subheader("🛑 Low-Value High-Cost Functions")
st.dataframe(low_value)

# =======================================
# EXERCISE 5 — COST FORECASTING
# =======================================
st.header("5️⃣ Cost Forecasting Model")

df["ForecastedCost"] = (
    df["InvocationsPerMonth"] *
    df["AvgDurationMs"] *
    df["MemoryMB"] *
    0.00000000012 +
    df["DataTransferGB"] * 0.09
)

st.subheader("📈 Actual vs Forecasted Cost")
st.dataframe(df[["FunctionName","CostUSD","ForecastedCost"]])

fig2, ax2 = plt.subplots()
ax2.scatter(df["CostUSD"], df["ForecastedCost"])
ax2.set_xlabel("Actual Cost")
ax2.set_ylabel("Forecasted Cost")
ax2.set_title("Actual vs Forecasted Lambda Cost")
st.pyplot(fig2)

# =======================================
# EXERCISE 6 — CONTAINERIZATION CANDIDATES
# =======================================
st.header("6️⃣ Containerization Candidates (ECS/EKS/Fargate)")

containers = df[(df["AvgDurationMs"] > 3000) & (df["MemoryMB"] > 2048)]
st.subheader("🐳 Functions Better Suited for Containers")
st.dataframe(containers)

st.success("🎉 Dashboard Fully Loaded and CSV Repaired Successfully!")
