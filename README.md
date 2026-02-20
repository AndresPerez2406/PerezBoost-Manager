
# PerezBoost Manager V13.0 📈 (The BI Era)

**Enterprise-grade management & Business Intelligence suite** designed for high-performance Elo Boosting services. A **Stateful Hybrid Architecture** that transforms raw operational data into actionable financial insights.

**Version:** 13.0 | **Focus:** Data Intelligence & Financial Integrity | **Stack:** Python 3.10+, PostgreSQL, Streamlit, Plotly, CustomTkinter.

---

## 🚀 What's New in V13.0 (The BI Era)

* **💎 Cash-Basis Financial Logic:** Refactored the entire accounting engine. KPIs, daily profit, and analytics now strictly follow a  **"Realized Payment"**, ensuring the dashboard reflects actual cash flow, not just projected revenue.
* **📊 GitAnalytics BI Module:** Implementation of advanced data visualization using  **Plotly** :
  * **Quality-Value Matrix:** Scatter plots correlating Booster Win Rates vs. Revenue Generated.
  * **Financial Run-Rate:** Cumulative area charts for real-time liquidity tracking.
  * **Efficiency Rankings:** Heuristic scoring based on delivery speed and game performance.
* **🛡️ Secure Validation Gate (Management Tab):** A dedicated treasury module designed for  **one-way payment confirmation** . Data integrity is protected via read-only stateful forms, preventing accidental overrides during mass disbursements.
* **🎨 Unified Emerald UX:** Standardized UI/UX with a high-contrast  **Emerald Green theme** . 2026-compliant Streamlit syntax (using `width='stretch'`) for a fully responsive enterprise experience.
* **⚙️ Centralized Versioning:** Global version control injected via `.env` architecture, syncing the Desktop Engine, Discord Notifiers, and the Web Dashboard.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**       | **Status**      | **Key Objective**                                                                       |
| ----------------- | ------------------------ | --------------------- | --------------------------------------------------------------------------------------------- |
| **V10-V12** | **Foundations**    | ✅**Completed** | Hybrid Sync, Cloud Engine, and Mobile Dispatch Inventory.                                     |
| **V13.0**   | **The BI Era**     | ✅**Deployed**  | **Advanced Data Mining:**Financial Truth Logic, Plotly Analytics, and Emerald UI consistency. |
| **V14.0**   | **Auto-Pilot Ops** | 🏗️**In Dev**  | **Automated Payouts:**Bulk JSON/CSV dispersion files & "Red Alert" Discord Webhooks for KPIs. |
| **V15.0**   | **Scale Master**   | 📅**Planned**   | **SaaS Multi-Tenancy:**Data isolation for multiple teams and full Dockerization.              |

## 🛠️ Tech Stack & Optimization

* **Data Engine:** PostgreSQL (Cloud/Supabase) & SQLite (Local) with atomic transaction handling.
* **Analytics:** High-performance data processing via `pandas` and interactive visualization with `Plotly Express`.
* **Reliability:** RAM Caching with intelligent TTL and 2026-standard responsive layouts.
* **Security:** Multi-layer environment protection and base64-encoded tokenization for staff telemetry.

---

## ⚙️ Quick Start (Local)

**1. Clone & Install:**

**Bash**

```
git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git
cd PerezBoost-Manager
pip install -r requirements.txt
```

**2. Configure Environment:**

Create a `.env` file with `APP_VERSION=V13.0`, `DATABASE_URL`, and `ADMIN_PASSWORD`.

**3. Launch:**

* **Desktop Engine:** `python main.py`
* **Performance Dashboard:** `streamlit run dashboard_web.py`

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
