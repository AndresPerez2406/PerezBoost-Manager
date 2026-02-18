---

# PerezBoost Manager V12.5 🛡️ (Secure Horizon Edition)

**Enterprise-grade management suite** designed for high-performance Elo Boosting services. A **Stateful Hybrid Architecture** that combines robust local processing with a persistent, visually rich cloud dashboard.

**Version:** 12.5 | **Architecture:** Hybrid (Local-First + Cloud Sync + Stateful Web) | **Stack:** Python 3.10+, SQLite/PostgreSQL, Streamlit, Plotly.

---

## 🚀 What's New in V12.5 (Secure Horizon)

* **🔐 Stateful Session Persistence:** Implemented a robust **Cookie-Based Authentication System** (30-min lifespan) that survives page reloads and browser restarts. Includes latency-tolerant logic for seamless cloud deployment.
* **📈 Visual BI Suite:** New interactive **Plotly Pie Charts** and High-Impact KPI Cards in the web dashboard for instant financial breakdown (Net Profit vs. Staff Payouts vs. Ranking Pot).
* **🛠️ Master Data Editor:** Enhanced Desktop module with a **"Triple-Fallback Strategy"** to dynamically fetch Staff and Elo lists from SQL history, ensuring data integrity even without configuration tables.
* **🛡️ Operational Audit (Fiscal Forensics):** Real-time anomaly detection engine that identifies orders with critical Win Rates (<50%) and delivery delays (Red/Yellow Alerts).
* **☁️ Cloud-Native Security:** Full migration to Environment Variables/Secrets for credential protection, removing all hardcoded keys.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**         | **Status**      | **Key Objective**                                                    |
| ----------------- | -------------------------- | --------------------- | -------------------------------------------------------------------------- |
| **V10.0**   | **Cloud Foundation** | ✅**Completed** | AWS/Supabase integration and relational schema mapping.                    |
| **V11.0**   | **Hybrid Sync**      | ✅**Completed** | Dual-Cloud engine with non-blocking background threading.                  |
| **V12.0**   | **Fiscal Forensics** | ✅**Completed** | Automated anomaly detection and mobile dispatch inventory.                 |
| **V12.5**   | **Secure Horizon**   | ✅**Deployed**  | **Session Persistence (Cookies), Advanced BI Charts & Secure Auth.** |
| **V13.0**   | **Telegram Ops**     | 🏗️**In Dev**  | Real-time mission-critical alerts via Telegram Bot API.                    |
| **V14.0**   | **Analytics Hub**    | 📅**Planned**   | Advanced Business Intelligence (BI) suite with professional PDF reporting. |

## ⚙️ Quick Start (Local)

**1. Clone & Install:**

**Bash**

```
git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git
cd PerezBoost-Manager
pip install -r requirements.txt
```

**2. Launch:**

* **Desktop App:** `python main.py`
* **Web Dashboard:** `streamlit run dashboard_web.py`

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
