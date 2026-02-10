
# PerezBoost Manager V11.0 ☁️ (Hybrid Cloud Edition)

**Enterprise-grade management suite** designed for high-performance Elo Boosting services. Now powered by a  **Dual-Cloud Architecture (Supabase + AWS)** , combining the speed of local computing with the accessibility of the cloud.

**Version:** 11.0 | **Architecture:** Hybrid (Local-First + Cloud Sync) | **Stack:** Python 3.10+, SQLite, PostgreSQL (Supabase/AWS)

---

## 🚀 What's New in V11.0 (The Hybrid Update)

* **🔄 Dual-Cloud Redundancy:** "Dual-Push" engine that simultaneously synchronizes data to:
  1. **AWS RDS/S3:** For historical cold storage and auditing.
  2. **Supabase (PostgreSQL):** For real-time data access via Mobile/Web.
* **⚡ Non-Blocking Sync:** Background threading architecture allows database synchronization to happen silently without freezing the user interface.
* **🛡️ Local-First Reliability:** The system operates on a local SQLite core, ensuring zero latency and full offline functionality. Internet is only required for backups.
* **🔧 Self-Healing Data:** Automated integrity checks that sanitize `NULL` values and correct ID sequences during cloud migration.

---

## 🛠️ Core Capabilities

*Designed to streamline high-volume boosting operations through three strategic pillars:*

### ⚡ Operational Efficiency

* **Smart SLA Tracking:** "Traffic Light" system (Red/Yellow/Green) to visually prioritize orders based on delivery deadlines.
* **Automated Logistics:** Real-time calculation of "Days per Order" efficiency metrics based on cloud timestamps.

### 🤖 Automation & Notification

* **Discord Webhooks:** High-impact, automated notifications for completed orders, ranking updates, and critical stock alerts sent directly to staff channels.
* **One-Click Payroll:** Automated payroll settlement system. Groups completed orders by booster and calculates precise debt/payouts instantly.

### 💰 Financial Intelligence

* **Audit-Ready Logs:** Immutable logging of all financial transactions and rate changes.
* **Hybrid Security:** Local SQLite for low-latency operations + Cloud PostgreSQL for data integrity and remote access.

---

## 🗺️ Engineering Roadmap

We are following a strict development timeline to transform PerezBoost into a fully automated, headless platform.

| **Version** | **Codename**         | **Status**     | **Key Objective**                                                                                                      |
| ----------------- | -------------------------- | -------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **V10.0**   | **Cloud Foundation** | ✅**Done**     | AWS Infrastructure Integration. Initial migration to cloud storage.                                                          |
| **V11.0**   | **Hybrid Sync**      | ✅**Deployed** | ***Dual-Cloud Engine*** Simultaneous sync to Supabase & AWS with background threading and local-first architecture. |
| **V11.5**   | **The Owner's Eye**  | 🔜*Next Step*      | **Web Dashboard (Streamlit)** Remote monitoring interface to view real-time profits and KPIs via Mobile/Web.          |
| **V12.0**   | **Staff Portal**     | 📅 Planned           | **Booster Web App** A dedicated portal for staff to self-report wins and progress, automating data entry.             |

---

## ⚙️ Quick Start

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

*(Core libs: `customtkinter`, `psycopg2-binary`, `python-dotenv`, `pandas`)*

**3. Environment Setup:**

Create a `.env` file in the root directory and add your Supabase credentials:

**Fragmento de código**

```
DATABASE_URL="postgresql://postgres:[PASSWORD]@db.[PROJECT].supabase.co:5432/postgres"
```

**4. Launch:**

**Bash**

```
python main.py
```

---

## 👨‍💻 Developed by

**Andres Perez** - *High-Performance Software Specialist & Business Automation Expert*
