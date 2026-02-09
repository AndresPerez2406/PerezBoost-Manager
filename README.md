
# PerezBoost Manager V10.0 ☁️ (Cloud Architecture Edition)

**Enterprise-grade management suite** designed for high-performance Elo Boosting services. Now powered by  **AWS Cloud Infrastructure** , enabling hybrid data synchronization, financial auditing, and scalable remote operations.

**Version:** 10.0 | **Architecture:** Hybrid Cloud | **Stack:** Python 3.10+ & PostgreSQL (AWS RDS)

---

## 🚀 What's New in V10.0 (The Cloud Update)

* **☁️ AWS RDS Integration:** Full migration to Amazon Web Services (Virginia). Data is no longer siloed on a local machine, ensuring enterprise-level durability.
* **🔄 Bi-Directional Synchronization:**
  * **Cloud Push (Backup):** Encrypted upload of local operational data to the cloud.
  * **Cloud Pull (Restore):** Instant data retrieval to any authorized device, complete with automatic local failover backups.
* **📈 Dynamic Financial Engines:** Advanced algorithms for calculating performance-based staff incentives and real-time net profit margins.
* **🛡️ Resilient Infrastructure:** Zero-downtime architecture. Business data remains accessible and secure even in the event of local hardware failure.

---

## 🛠️ Core Capabilities

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

| **Version** | **Codename**        | **Status**     | **Key Objective**                                                                                      |
| ----------------- | ------------------------- | -------------------- | ------------------------------------------------------------------------------------------------------------ |
| **V10.0**   | **Cloud Hybrid**    | ✅**Deployed** | **AWS Infrastructure Integration.**Bi-directional Sync, Cloud Backups, and PostgreSQL Migration.             |
| **V10.5**   | **The Owner's Eye** | 🔜*Next Step*      | **Web Dashboard (Streamlit).**Remote monitoring interface to view real-time profits and KPIs via Mobile/Web. |
| **V11.0**   | **Multiplayer**     | 📅 Planned           | **Direct Cloud Connection.**Removal of local SQLite to enable concurrent multi-admin operations.             |
| **V12.0**   | **Staff Portal**    | 🔮 Future            | **Booster Web App.**A dedicated portal for staff to self-report wins and progress, automating data entry.    |

---

## ⚙️ Quick Start

1. **Clone Repository:**
   `git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git`
   `cd PerezBoost-Manager`
2. **Install Dependencies:**
   `pip install -r requirements.txt`
   *(Core libs: `customtkinter`, `psycopg2`, `pandas`, `matplotlib`)*
3. **Cloud Configuration:**
   Set up your AWS Endpoint and Credentials in `gui_main.py`.
4. **Launch:**
   `python main.py`

---

## 👨‍💻 Developed by

**Andres Perez** - *High-Performance Software Specialist & Business Automation Expert*
