# PerezBoost Manager V11.5 🚀 (The Owner's Eye Edition)

**Enterprise-grade management suite** designed for high-performance Elo Boosting services. Now evolved into a  **Triple-Layer Hybrid Architecture** , combining local processing power with global cloud accessibility.

**Version:** 11.5 | **Architecture:** Hybrid (Local-First + Cloud Sync + Web Dashboard) | **Stack:** Python 3.10+, PostgreSQL (Supabase/AWS), Streamlit.

---

## 🚀 What's New in V11.5 (The Owner's Eye)

* **🌐 Operational Web Dashboard:** Remote interface deployed via  **Streamlit Cloud** , allowing the owner to monitor net profits, stock, and active orders from any smartphone in real-time.
* **🛡️ Hardened Security:** Migrated sensitive authentication and database strings to  **Secured Environment Variables (Secrets)** , implementing a zero-hardcode policy for production environments.
* **🔗 Connection Pooling Optimization:** Resolved IPv6/IPv4 network bottlenecks by implementing  **Transaction Pooling (Port 6543)** , ensuring high-availability access from mobile networks.
* **📊 Pro Reports & UX:** Enhanced financial tracking with **Visual ID Indexing (#)** and dynamic KPI cards that calculate net margins and "Ranking Pool" (Bote) deductions on the fly.
* **🔄 Dual-Cloud Redundancy:** "Dual-Push" engine that synchronizes data simultaneously to:
  1. **AWS RDS:** For historical cold storage and auditing.
  2. **Supabase (PostgreSQL):** For high-availability real-time data access.

---

## 🛠️ Core Capabilities

### ⚡ Operational Efficiency

* **Non-Blocking Sync:** Background threading architecture that allows database synchronization to happen silently without freezing the local UI.
* **Local-First Reliability:** Core powered by a local SQLite database for zero-latency operations. The system is fully functional offline; the cloud acts as a remote monitoring channel.

### 💰 Financial Intelligence

* **KPI-Contingent Overhead Modeling:** Deployment of a dynamic contribution engine that optimizes net margins based on performance-driven metrics (Win Rate & Delivery Time).
* **Automated Settlement Workflows:** Intelligent financial reconciliation module that aggregates closed cycles and executes precise payout calculations.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**            | **Status**      | **Key Objective**                                                              |
| ----------------- | ----------------------------- | --------------------- | ------------------------------------------------------------------------------------ |
| **V10.0**   | **Cloud Foundation**    | ✅**Completed** | AWS RDS integration and initial relational schema mapping for cloud storage.         |
| **V11.0**   | **Hybrid Sync**         | ✅**Completed** | Implementation of the Dual-Cloud engine with non-blocking background threading.      |
| **V11.5**   | **The Owner's Eye**     | 🚀**Deployed**  | Streamlit Cloud Dashboard for remote KPI monitoring and secure secrets management.   |
| **V12.0**   | **Fiscal Forensics**    | 📅**Planned**   | Automated anomaly detection and risk-margin auditing via defensive logic.            |
| **V13.0**   | **Proactive Telemetry** | 📅**Planned**   | Real-time mission-critical alerts via Telegram/Discord API integration.              |
| **V14.0**   | **Analytics Hub**       | 📅**Planned**   | Advanced Business Intelligence (BI) suite with professional PDF financial reporting. |
| **V15.0**   | **DevOps Standard**     | 📅**Planned**   | Deployment of CI/CD pipelines and automated Unit Testing for financial integrity.    |

## ⚙️ Quick Start (Local)

**1. Clone & Install:**

**Bash**

```
git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git
cd PerezBoost-Manager
pip install -r requirements.txt
```

**2. Environment Setup:**

Create a `.env` file for local use. For Cloud deployment, use **Streamlit Secrets** with the following keys:

* `DATABASE_URL` (Pooler Connection / Port 6543)
* `ADMIN_PASSWORD` (Encrypted Access Key)

**3. Launch:**

* **Desktop App:** `python main.py`
* **Web Dashboard:** `streamlit run dashboard_web.py`

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
