# PerezBoost Manager V14.0 🤖 (Auto-Pilot Ops)

**Enterprise-grade management & Business Automation suite** designed for high-performance Elo Boosting services. A **Stateful Hybrid Architecture** that transforms raw operational data into actionable financial insights and automates daily workflows.

**Version:** 14.0 | **Focus:** Workflow Automation, Auto-Pilot & Payroll | **Stack:** Python 3.10+, PostgreSQL, Streamlit, Plotly, CustomTkinter.

---

## 🚀 What's New in V14.0 (Auto-Pilot Ops)

* **🤖 Background Sentinel (Auto-Pilot):** Implementation of a multi-threaded background daemon that scans the database continuously, triggering automated 24-hour risk alerts for overdue orders without blocking the main UI thread.
* **🔀 Segregated Notification Architecture:** Multi-channel Discord Webhook integration. Operations are strictly divided into three tiers: General Logs, Hall of Fame (Ranking), and Red Alerts (Critical overdue monitoring for CEOs).
* **📑 1-Click Executive Close:** Automated End-of-Day (EOD) financial reporting. Generates a comprehensive breakdown of gross sales, staff payouts, ranking pools, and net profit, pushing it directly to Discord.
* **💸 Bulk Payout Engine (Payroll):** Replaced manual debt calculation with an automated CSV generator that exports consolidated pending balances per staff member.
* **🛡️ Bulletproof Data Parsing:** Overhauled the date-handling logic across the entire software. The new multi-format parser silently catches and normalizes irregular date inputs (slashes, hyphens) to ISO 8601 standard, preventing fatal system crashes.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**           | **Status**      | **Key Objective**                                                                                         |
| ----------------- | ---------------------------- | --------------------- | --------------------------------------------------------------------------------------------------------------- |
| **V13.0**   | **The BI Era**         | ✅**Completed** | **Advanced Data Mining:**Financial Truth Logic, Plotly Analytics, and Emerald UI consistency.                   |
| **V14.0**   | **Auto-Pilot Ops**     | ✅**Deployed**  | **Automated Workflows:**Background Sentinel, Bulk CSV Payroll, Executive Discord Reporting & Alert segregation. |
| **V15.0**   | **Scale Master**       | 🏗️**In Dev**  | **SaaS Multi-Tenancy & RBAC:**Data isolation via Tenant IDs, Dockerization, and Owner vs. Admin Access Control. |
| **V16.0**   | **Enterprise Routing** | 📅**Planned**   | **Smart Dispatcher:**Algorithmic order assignment, Discord Bot 2-way sync (Click-to-claim orders).              |

---

## 🛠️ Tech Stack & Optimization

* **Data Engine:** PostgreSQL (Cloud/Supabase) & SQLite (Local) with atomic transaction handling.
* **Automation:** Python `threading` for non-blocking background daemons and `requests` for robust API communication.
* **Analytics:** High-performance data processing via `pandas` and interactive visualization with `Plotly Express`.
* **Reliability:** RAM Caching with intelligent TTL and bulletproof try-except wrappers for data normalization.
* **Security:** Multi-layer environment protection, segregated webhook routing, and base64-encoded tokenization for staff telemetry.

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

Create a `.env` file with `APP_VERSION=V14.0`, `DATABASE_URL`, and `ADMIN_PASSWORD`. Ensure your database includes the `sistema_config` table for Webhook storage.

**3. Launch:**

* **Desktop Engine:** `python main.py`
* **Performance Dashboard:** `streamlit run dashboard_web.py`

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
