
# PerezBoost Manager V11.5 🚀 (The Owner's Eye Edition)

**Enterprise-grade management suite** designed for high-performance Elo Boosting services. Now evolved into a  **Triple-Layer Hybrid Architecture** , combining local processing power with global cloud accessibility.

**Version:** 11.5 | **Architecture:** Hybrid (Local-First + Cloud Sync + Web Dashboard) | **Stack:** Python 3.10+, PostgreSQL (Supabase/AWS), Streamlit.

---

## 🚀 What's New in V11.5 (The Owner's Eye)

* **🌐 Operational Web Dashboard:** Remote interface deployed via  **Streamlit Cloud** , allowing the owner to monitor net profits, stock, and active orders from any smartphone in real-time.
* **📊 Pro Reports (Web Sync):** Exact replica of the desktop financial logic on the web, filtering completions by **Start Date** for impeccable accounting.
* **🔄 Dual-Cloud Redundancy:** "Dual-Push" engine that synchronizes data simultaneously to:
  1. **AWS RDS/S3:** For historical cold storage and auditing.
  2. **Supabase (PostgreSQL):** For high-availability real-time data access via Mobile/Web.
* **⚡ Non-Blocking Sync:** Background threading architecture that allows database synchronization to happen silently without freezing the user interface.
* **🛡️ Local-First Reliability:** Core powered by a local SQLite database for zero-latency operations. The system is fully functional offline; the cloud acts as a backup and remote monitoring channel.

---

## 🛠️ Core Capabilities

### ⚡ Operational Efficiency

* **Risk-Aware SLA Management:** Proactive monitoring engine utilizing a tri-stage visual matrix to enforce strict delivery compliance and mitigate operational bottlenecks.
* **Granular Data Traceability:** Multi-parameter indexing for all service lifecycles, enabling comprehensive auditing from provisioning to final settlement.

### 🤖 Automation & Notification

* **Event-Driven Telemetry:** Real-time distribution of mission-critical data via high-fidelity webhooks, ensuring instantaneous synchronization across the staff ecosystem.
* **Automated Settlement Workflows:** Intelligent financial reconciliation module that aggregates closed cycles and executes precise payout calculations, eliminating manual accounting overhead.

### 💰 Financial Intelligence

* **KPI-Contingent Overhead Modeling:** Deployment of a dynamic contribution engine (V11.5) that optimizes net margins based on performance-driven metrics.
* **Immutable Fiscal Auditing:** High-integrity ledger logging for all tariff adjustments and capital movements, providing a transparent and tamper-proof financial history.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**         | **Status**     | **Key Objective**                                                        |
| ----------------- | -------------------------- | -------------------- | ------------------------------------------------------------------------------ |
| **V10.0**   | **Cloud Foundation** | ✅**Done**     | AWS RDS integration and initial infrastructure setup.                          |
| **V11.0**   | **Hybrid Sync**      | ✅**Done**     | Dual-Cloud Engine and Background Threading implementation.                     |
| **V11.5**   | **The Owner's Eye**  | 🚀**Deployed** | **Web Dashboard (Streamlit)** for remote KPI monitoring and Pro Reports. |
| **V12.0**   | **Staff Portal**     | 📅 Planned           | **Booster Web App**for staff self-reporting and automated data entry.    |

---

## ⚙️ Quick Start (Local)

**1. Clone Repository:**

**Bash**

```
git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git
cd PerezBoost-Manager
```

**2. Install Dependencies:**

**Bash**

```
pip install -r requirements.txt
```

*(Core libs: `customtkinter`, `psycopg2-binary`, `python-dotenv`, `pandas`, `streamlit`, `plotly`)*

**3. Environment Setup:**

Create a `.env` file in the root directory and add your credentials:

**Fragmento de código**

```
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
```

**4. Launch Desktop App:**

**Bash**

```
python main.py
```

**5. Launch Web Dashboard:**

**Bash**

```
streamlit run dashboard_web.py
```

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
