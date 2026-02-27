
# PerezBoost Manager V16.0 🚀 (Hybrid Master & Cloud Orchestration)

**Enterprise-grade Business Automation suite**. This version marks the transition from a local script to a  **Fully Containerized Ecosystem** , integrating a high-performance Desktop GUI with a real-time Analytics Dashboard via Docker Orchestration.

**Version:** 16.0 | **Focus:** Infrastructure as Code (IaC), Containerization & GUI Forwarding | **Stack:** Docker, Python 3.12, PostgreSQL/SQLite, Streamlit, CustomTkinter (X11).

---

## 🚀 What's New in V16.0 (The Container Era)

* **🐳 Full Dockerization:** The entire ecosystem (Desktop App + Web Dashboard) now runs in isolated Linux containers. No more "it works on my machine" errors; the environment is identical everywhere.
* **🖥️ Hybrid X11 Forwarding:** Implementation of an X11 bridge (VcXsrv) allowing the high-performance Python GUI to be rendered natively on Windows while the logic stays secured inside a Docker container.
* **🧩 Intelligent UI (Smart-ComboBox):** Replaced manual staff entry with a dynamic database-linked ComboBox. This enforces data integrity by only allowing assignments to registered staff members.
* **🌐 Unified Orchestration:** Single-command deployment using `docker-compose`. Automatic synchronization between the management desktop app and the staff-facing web dashboard.
* **🛠️ Tech Debt Cleanup:** Upgraded to Python 3.12-slim for better performance and reduced image size. Fixed UTF-8 emoji rendering issues across Linux/Windows boundaries.

---

## 🗺️ Engineering Roadmap

| **Version** | **Codename**         | **Status**      | **Key Objective**                                               |
| ----------------- | -------------------------- | --------------------- | --------------------------------------------------------------------- |
| **V14.0**   | **Auto-Pilot Ops**   | ✅**Completed** | Background Sentinels, Discord EOD Reporting, and Bulk Payroll CSV.    |
| **V15.0**   | **Scale Master**     | ✅**Completed** | Dockerization, RBAC preparation, and Python 3.12 Migration.           |
| **V16.0**   | **Hybrid Master**    | 🚀**Deployed**  | X11 Forwarding, Smart UI Bindings, and Unified Compose Orchestration. |
| **V17.0**   | **Smart Dispatcher** | 📅**Planned**   | Algorithmic order assignment & 2-way Discord Bot Sync.                |

---

## 🛠️ Infrastructure & Tech Stack

* **Orchestration:** Docker Compose (Multi-container architecture).
* **GUI Bridge:** VcXsrv / XLaunch (X11 Server for Windows).
* **Backend Engine:** Python 3.12 (Asynchronous execution & multi-threading).
* **Data Layer:** PostgreSQL (Cloud) & SQLite (Local Persistent Volume).
* **Frontend:** Streamlit (Web) & CustomTkinter (Desktop) with Emerald UI Theme.

---

## ⚙️ Quick Start (The Docker Way)

**1. Prerequisites:**

* Install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
* Install [VcXsrv (XLaunch)](https://sourceforge.net/projects/vcxsrv/) for GUI rendering.

**2. Setup X11 Bridge:**

1. Run  **XLaunch** .
2. Select: `Multiple Windows` -> `Start no client`.
3. **CRITICAL:** Check `Disable access control`.

**3. Launch System:**

**Bash**

```
git clone https://github.com/AndresPerez2406/PerezBoost-Manager.git
cd PerezBoost-Manager
docker compose up --build -d
```

**4. Access:**

* **Desktop App:** Will pop up on your screen automatically.
* **Web Dashboard:** Navigate to `http://localhost:8501`.

---

## 👨‍💻 Developed by

**Andres Perez** - *High Performance Software Specialist & Business Automation Expert*
