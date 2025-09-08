
"""
*NOTE: THIS SERVES ONLY AS A PROTOTYPE WITH THE ACTUAL DATA THAT WE HAVE. 
*NOTE 2: KPI METRICS USED:
- Overview tab → GWP, Loss Ratio, Claims Frequency, Average Settlement Time.
- Claims tab → Paid vs Reserve, Severity distribution, Open vs Closed ratio.
- Risk & Fraud tab → Claims by Peril, Regional Catastrophe Exposure.
- Operations tab → FNOL, SLA Breaches, Backlog.
- Customer 360 tab → Retention, Cross-Sell, Channel Mix, Demographics.
"""

import streamlit as st # type: ignore
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Insurer Live Dashboard", layout="wide")

st.title("🏛️ Insurer Live Dashboard")

# ---- Sidebar: data ingest ----
st.sidebar.header("Data")
policies_file = st.sidebar.file_uploader("Upload policies.csv", type=["csv"])
customers_file = st.sidebar.file_uploader("Upload customers.csv", type=["csv"])
claims_file = st.sidebar.file_uploader("Upload claims.csv", type=["csv"])

@st.cache_data(show_spinner=False)
def load_csv(file):
    return pd.read_csv(file)

def coerce_dates(df, cols):
    for c in cols:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    return df

# Light demo mode if nothing is uploaded
if policies_file is not None:
    policies = load_csv(policies_file)
else:
    policies = pd.DataFrame(columns=["policy_id","customer_id","product_type","start_date","end_date","status","channel","discount_pct","gross_premium"])

if customers_file is not None:
    customers = load_csv(customers_file)
else:
    customers = pd.DataFrame(columns=["customer_id","full_name","email","phone","county_code","county_name","city","postal_code","crime_risk","hail_risk","flood_risk","wind_risk","fire_risk","dob"])

if claims_file is not None:
    claims = load_csv(claims_file)
else:
    claims = pd.DataFrame(columns=["claim_id","policy_id","product_type","loss_date","peril","status","reserve","paid","report_date","close_date","severity_band"])

# Coerce to dates
policies = coerce_dates(policies, ["start_date","end_date"])
customers = coerce_dates(customers, ["dob"])
claims   = coerce_dates(claims,   ["loss_date","report_date","close_date"])

TODAY = pd.Timestamp.today()
SLA_DAYS = st.sidebar.number_input("SLA Days (settlement)", min_value=1, value=30)
FREQ_DENOMINATOR = st.sidebar.number_input("Frequency per N policies", min_value=100, value=1000, step=100)

# Helper period columns
if not policies.empty:
    policies["start_month"] = policies["start_date"].dt.to_period("M").dt.to_timestamp()
    policies["end_month"]   = policies["end_date"].dt.to_period("M").dt.to_timestamp()
if not claims.empty:
    claims["loss_month"]   = claims["loss_date"].dt.to_period("M").dt.to_timestamp()
    claims["report_month"] = claims["report_date"].dt.to_period("M").dt.to_timestamp()
    claims["close_month"]  = claims["close_date"].dt.to_period("M").dt.to_timestamp()

# Policies in force expanded by month
@st.cache_data(show_spinner=False)
def expand_policies_monthly(policies_df: pd.DataFrame) -> pd.DataFrame:
    if policies_df.empty:
        return pd.DataFrame(columns=["policy_id","month","gross_premium","product_type","channel","customer_id"])
    start_min = policies_df["start_date"].min().to_period("M").to_timestamp()
    end_max   = policies_df["end_date"].max().to_period("M").to_timestamp()
    months = pd.date_range(start_min, end_max, freq="MS")
    rows = []
    for _, r in policies_df.iterrows():
        rng = pd.date_range(r["start_date"].to_period("M").to_timestamp(),
                            r["end_date"].to_period("M").to_timestamp(),
                            freq="MS")
        rows.append(pd.DataFrame({
            "policy_id": r["policy_id"],
            "month": rng,
            "gross_premium": r["gross_premium"],
            "product_type": r.get("product_type", np.nan),
            "channel": r.get("channel", np.nan),
            "customer_id": r.get("customer_id", np.nan),
        }))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame(columns=["policy_id","month","gross_premium","product_type","channel","customer_id"])

policies_if = expand_policies_monthly(policies)

# ---- KPI header cards (Overview) ----
def kpi_card(label, value, help_text=None, cols=None):
    if cols is None:
        cols = st.columns(1)
    with cols:
        st.metric(label, value, help=help_text)

def format_money(x):
    if pd.isna(x):
        return "—"
    return f"€{x:,.0f}"

def render_overview():
    st.subheader("Overview")
    c1,c2,c3,c4 = st.columns(4)

    # GWP (by start month total)
    gwp_total = policies["gross_premium"].sum() if "gross_premium" in policies else 0.0
    kpi_card("GWP (Total)", format_money(gwp_total), cols=c1)

    # Loss Ratio proxy
    paid_total = claims["paid"].sum() if "paid" in claims else 0.0
    earned_proxy = policies_if["gross_premium"].sum() if not policies_if.empty else np.nan
    lr = (paid_total / earned_proxy) if earned_proxy and earned_proxy>0 else np.nan
    kpi_card("Loss Ratio", f"{lr:.1%}" if pd.notna(lr) else "—", "Paid / Earned proxy", cols=c2)

    # Claims Frequency (overall)
    policies_count = policies["policy_id"].nunique() if "policy_id" in policies else 0
    claims_count = claims["claim_id"].nunique() if "claim_id" in claims else 0
    freq = (claims_count / policies_count * FREQ_DENOMINATOR) if policies_count > 0 else np.nan
    kpi_card(f"Claims Freq (/ {FREQ_DENOMINATOR})", f"{freq:.2f}" if pd.notna(freq) else "—", cols=c3)

    # Avg Settlement Time
    closed = claims.dropna(subset=["report_date","close_date"]).copy()
    closed["settlement_days"] = (closed["close_date"] - closed["report_date"]).dt.days
    avg_settle = closed["settlement_days"].mean() if not closed.empty else np.nan
    kpi_card("Avg Settlement (days)", f"{avg_settle:.1f}" if pd.notna(avg_settle) else "—", cols=c4)

    # Charts
    with st.container():
        left, right = st.columns([2,1])
        with left:
            st.markdown("**GWP by Month**")
            if "start_month" in policies:
                gwp_m = (policies.groupby("start_month", as_index=False)["gross_premium"].sum()
                                  .rename(columns={"start_month":"month","gross_premium":"gwp"}))
                fig, ax = plt.subplots()
                ax.plot(gwp_m["month"], gwp_m["gwp"], marker="o")
                ax.set_title("GWP by Month"); ax.set_xlabel("Month"); ax.set_ylabel("GWP")
                ax.grid(True, linestyle="--", alpha=0.4); plt.xticks(rotation=45)
                st.pyplot(fig, clear_figure=True)
            else:
                st.info("Upload policies.csv to see GWP by Month")
        with right:
            st.markdown("**Claims Mix (Severity Band)**")
            if "severity_band" in claims:
                sev = claims["severity_band"].value_counts().sort_index()
                fig, ax = plt.subplots()
                ax.bar(sev.index, sev.values)
                ax.set_title("Claims by Severity Band"); ax.set_xlabel("Band"); ax.set_ylabel("Count")
                st.pyplot(fig, clear_figure=True)
            else:
                st.info("Upload claims.csv to see Severity Mix")

# ---- Tabs ----
tab_overview, tab_claims, tab_risk, tab_ops, tab_c360 = st.tabs(["Overview","Claims","Risk & Fraud","Operations","Customer 360"])

with tab_overview:
    render_overview()

with tab_claims:
    st.subheader("Claims")
    c1,c2 = st.columns([1,1])
    with c1:
        st.markdown("**Paid vs Reserve by Product**")
        if not claims.empty:
            agg = claims.groupby("product_type", as_index=False)[["paid","reserve"]].sum()
            fig, ax = plt.subplots()
            x = np.arange(len(agg))
            ax.bar(x, agg["paid"], label="Paid")
            ax.bar(x, agg["reserve"], bottom=agg["paid"], label="Reserve")
            ax.set_title("Paid vs Reserve by Product Type")
            ax.set_xticks(x); ax.set_xticklabels(agg["product_type"], rotation=25, ha="right")
            ax.set_ylabel("Amount"); ax.legend()
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Upload claims.csv")
    with c2:
        st.markdown("**Open vs Closed**")
        if not claims.empty:
            status_counts = claims["status"].value_counts()
            fig, ax = plt.subplots()
            ax.pie(status_counts.values, labels=status_counts.index, autopct="%1.1f%%", startangle=90)
            ax.set_title("Open vs Closed Claims")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Upload claims.csv")

with tab_risk:
    st.subheader("Risk & Fraud")
    c1, c2 = st.columns([1,1])
    with c1:
        st.markdown("**Claims by Peril**")
        if not claims.empty:
            perils = claims["peril"].value_counts().sort_values(ascending=False)
            fig, ax = plt.subplots()
            ax.bar(perils.index, perils.values)
            ax.set_title("Claims by Peril"); ax.set_xlabel("Peril"); ax.set_ylabel("Count")
            plt.setp(ax.get_xticklabels(), rotation=25, ha="right")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Upload claims.csv")
    with c2:
        st.markdown("**Regional Catastrophe Exposure**")
        if not policies.empty and not customers.empty:
            pol_cust = policies.merge(customers, on="customer_id", how="left")
            hazards = ["hail_risk","flood_risk","fire_risk","wind_risk","crime_risk"]
            for h in hazards:
                if h not in pol_cust.columns:
                    pol_cust[h] = 0.0
            pol_cust["hazard_score"] = pol_cust[hazards].max(axis=1)
            exposure = (pol_cust.groupby("county_name", as_index=False)
                                .apply(lambda g: pd.Series({"exposure": (g["gross_premium"]*g["hazard_score"]).sum()}))
                                .sort_values("exposure", ascending=False)
                        )
            topN = exposure.head(10)
            fig, ax = plt.subplots()
            ax.bar(topN["county_name"], topN["exposure"])
            ax.set_title("Top 10 Exposure (Premium × Max Hazard)")
            ax.set_xlabel("County"); ax.set_ylabel("Exposure")
            plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Upload policies.csv and customers.csv")

with tab_ops:
    st.subheader("Operations")
    c1, c2 = st.columns([1,1])
    with c1:
        st.markdown("**FNOL (Avg days Loss → Report)**")
        if not claims.empty:
            has_dates = claims.dropna(subset=["loss_date","report_date"]).copy()
            if not has_dates.empty:
                has_dates["report_month"] = has_dates["report_date"].dt.to_period("M").dt.to_timestamp()
                has_dates["fnol_days"] = (has_dates["report_date"] - has_dates["loss_date"]).dt.total_seconds() / (24*3600)
                fnol = has_dates.groupby("report_month", as_index=False)["fnol_days"].mean().rename(columns={"report_month":"month"})
                fig, ax = plt.subplots()
                ax.plot(fnol["month"], fnol["fnol_days"], marker="o")
                ax.set_title("FNOL (Avg days)"); ax.set_xlabel("Month"); ax.set_ylabel("Days")
                ax.grid(True, linestyle="--", alpha=0.4)
                plt.xticks(rotation=45)
                st.pyplot(fig, clear_figure=True)
            else:
                st.info("No claims with both loss_date and report_date")
        else:
            st.info("Upload claims.csv")
    with c2:
        st.markdown("**SLA Breach Rate**")
        if not claims.empty:
            c = claims.dropna(subset=["report_date","close_date"]).copy()
            if not c.empty:
                c["close_month"] = c["close_date"].dt.to_period("M").dt.to_timestamp()
                c["settlement_days"] = (c["close_date"] - c["report_date"]).dt.days
                monthly = (c.groupby("close_month")
                            .agg(total=("claim_id","count"),
                                 breached=("settlement_days", lambda s: (s > SLA_DAYS).sum()))
                            .reset_index()
                            .rename(columns={"close_month":"month"}))
                monthly["breach_pct"] = np.where(monthly["total"]>0, monthly["breached"]/monthly["total"], np.nan)
                fig, ax = plt.subplots()
                ax.plot(monthly["month"], monthly["breach_pct"], marker="o")
                ax.set_title(f"SLA Breach Rate (> {SLA_DAYS} days)")
                ax.set_xlabel("Month"); ax.set_ylabel("Breach Rate")
                ax.grid(True, linestyle="--", alpha=0.4)
                plt.xticks(rotation=45)
                st.pyplot(fig, clear_figure=True)
            else:
                st.info("No closed claims with both report_date and close_date")
        else:
            st.info("Upload claims.csv")

    st.markdown("**Backlog (Open Claims) by Month**")
    if not claims.empty and claims["report_date"].notna().any():
        start = claims["report_date"].min().to_period("M").to_timestamp()
        end = (claims["close_date"].dropna().max().to_period("M").to_timestamp()
               if claims["close_date"].notna().any() else TODAY.to_period("M").to_timestamp())
        months = pd.date_range(start, end, freq="MS")

        def open_as_of(month):
            month_end = month + pd.offsets.MonthEnd(0)
            reported = claims["report_date"] <= month_end
            not_closed_yet = claims["close_date"].isna() | (claims["close_date"] > month_end)
            return int((reported & not_closed_yet).sum())

        backlog = pd.DataFrame({"month": months})
        backlog["open_claims"] = backlog["month"].apply(open_as_of)
        fig, ax = plt.subplots()
        ax.plot(backlog["month"], backlog["open_claims"], marker="o")
        ax.set_title("Backlog (Open Claims) by Month")
        ax.set_xlabel("Month"); ax.set_ylabel("Open Claims")
        ax.grid(True, linestyle="--", alpha=0.4)
        plt.xticks(rotation=45)
        st.pyplot(fig, clear_figure=True)
    else:
        st.info("Upload claims.csv")

with tab_c360:
    st.subheader("Customer 360")
    c1, c2 = st.columns([1,1])

    with c1:
        st.markdown("**Retention (30-day Renewal Proxy)**")
        if not policies.empty:
            p = policies.sort_values(["customer_id","start_date"]).copy()
            p["next_start"] = p.groupby("customer_id")["start_date"].shift(-1)
            p["this_end"]   = p["end_date"]
            p["retained"]   = (p["next_start"] - p["this_end"]).dt.days.between(0, 30)
            ret = (p.groupby(p["this_end"].dt.to_period("M").dt.to_timestamp())
                    .agg(customers=("customer_id","nunique"),
                         retained=("retained", lambda s: s.fillna(False).sum()))
                    .reset_index()
                    .rename(columns={"this_end":"month"}))
            ret["retention_rate"] = np.where(ret["customers"]>0, ret["retained"]/ret["customers"], np.nan)
            fig, ax = plt.subplots()
            ax.plot(ret["month"], ret["retention_rate"], marker="o")
            ax.set_title("Retention Rate (30d)"); ax.set_xlabel("Month"); ax.set_ylabel("Rate")
            ax.grid(True, linestyle="--", alpha=0.4); plt.xticks(rotation=45)
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Upload policies.csv")

    with c2:
        st.markdown("**Channel Mix by Premium**")
        if not policies.empty and "channel" in policies and "gross_premium" in policies:
            channel_prem = policies.groupby("channel", as_index=False)["gross_premium"].sum()
            fig, ax = plt.subplots()
            ax.bar(channel_prem["channel"], channel_prem["gross_premium"])
            ax.set_title("Channel Mix by Premium")
            ax.set_xlabel("Channel"); ax.set_ylabel("Gross Premium")
            st.pyplot(fig, clear_figure=True)
        else:
            st.info("Upload policies.csv")

    st.markdown("**Customer Age Distribution**")
    if not customers.empty and "dob" in customers:
        cust = customers.copy()
        cust["dob"] = pd.to_datetime(cust["dob"], errors="coerce")
        cust["age"] = ((TODAY - cust["dob"]).dt.days / 365.25).astype("float")
        fig, ax = plt.subplots()
        bins = [0,18,25,35,45,55,65,75,120]
        ax.hist(cust["age"].dropna(), bins=bins, edgecolor="black")
        ax.set_title("Customer Age Distribution"); ax.set_xlabel("Age"); ax.set_ylabel("Count")
        st.pyplot(fig, clear_figure=True)
    else:
        st.info("Upload customers.csv")
