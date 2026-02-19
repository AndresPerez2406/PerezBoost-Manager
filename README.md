# PerezBoost Manager V12.5 🛡️ (Secure Horizon Edition)

**Enterprise-grade management suite** designed for high-performance Elo Boosting services. A **Stateful Hybrid Architecture** that combines robust local processing with a persistent, visually rich cloud dashboard.

**Version:** 12.5 | **Architecture:** Hybrid (Local-First + Cloud Sync + RAM Caching) | **Stack:** Python 3.10+, SQLite/PostgreSQL, Streamlit, Plotly.

---

## 🚀 What's New in V12.5 (Secure Horizon)

* **⚡ RAM Caching Logic:** Integrated `@st.cache_data` with intelligent TTL management, reducing database latency by 90% and providing an instantaneous UI experience.
* **💰 Binance Hub CRUD:** A dedicated financial module with  **Modal-based Transaction Management** , monthly filtering, and real-time "Net Profit" vs "Ranking Pot" reconciliation.
* **🔐 Stateful Session Persistence:** Robust **Cookie-Based Authentication** with an integrated "Security Circuit Breaker" for guaranteed logout and session protection.
* **🌐 Automated Telemetry Tracking:** Dynamic generation of OPGG tracking links for boosters via base64-encoded secure tokens.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**       | **Status**      | **Key Objective**                                                                       |
| ----------------- | ------------------------ | --------------------- | --------------------------------------------------------------------------------------------- |
| **V10-V12** | **Foundations**    | ✅**Completed** | Hybrid Sync, Cloud Engine, and Mobile Dispatch Inventory.                                     |
| **V12.5**   | **Secure Horizon** | ✅**Deployed**  | RAM Caching, Binance CRUD Modals, & Stateless Secure Auth.                                    |
| **V13.0**   | **GitAnalytics**   | 🏗️**In Dev**  | **Deep Data Mining:**Booster performance heatmaps, churn rate, and ROI per order.             |
| **V14.0**   | **Auto-Pilot Ops** | 📅**Planned**   | **Automated Booster Payouts:**One-click bulk crypto/Nequi payment generation & API alerts.    |
| **V15.0**   | **Scale Master**   | 📅**Planned**   | **Multi-Tenancy Support:**Infrastructure for managing multiple boosting teams under one SaaS. |

## 🛠️ Tech Stack & Optimization

* **Database:** PostgreSQL (Cloud/Supabase) & SQLite (Local) with atomic transaction handling.
* **Optimization:** Data frames optimized via `pandas` with vectorized operations for financial totals.
* **Security:** Multi-layer environment protection (`.env` + Streamlit Secrets) and secure URL tokenization.

---

## ⚙️ Quick Start (Local)

**1. Clone & Install:**

**Bash**

```
git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git
cd PerezBoost-Manager
pip install -r requirements.txt
```

**2. Launch Environment:**

* **Desktop Engine:** `python main.py`
* **Performance Dashboard:** `streamlit run dashboard_web.py`

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
