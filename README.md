# 🚀 Synergee App – Deployment Guide (Windows Server)

This guide explains how to set up and run the Synergee Flask application as a **production-like server** on Windows.

---

## 1. Install Required Software

1. **Install Python**
   👉 [Download Python](https://www.python.org/downloads/)
   Make sure to check **“Add Python to PATH”** during installation.

2. **Install Git**
   👉 [Download Git](https://git-scm.com/downloads)

3. **Install NSSM (Non-Sucking Service Manager)**
   👉 [Download NSSM](https://nssm.cc/download)

---

## 2. Get the Project

1. Download the project from GitHub:
   👉 [Synergee App Repository](https://github.com/osama2kabdullah/synergee-app)

2. Place the provided files into the project root:

   - `.env` file
   - `db_export.json` file

---

## 3. Setup the Environment

Open **Command Prompt (CMD)** inside the project folder and run:

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\activate

# Install project dependencies
pip install -r requirements.txt
```

---

## 4. Database Setup

Run the following commands one by one:

```bash
# Create an empty database with all tables
python create_db.py

# Import existing data
python import_data.py

# Verify that data is correct
python check_data.py
```

---

## 5. Test Run the Application

Run the app once manually to check everything works:

```bash
waitress-serve --host=0.0.0.0 --port=8080 wsgi:app
```

👉 Open browser at:
`http://localhost:8080`

If the app runs correctly, press **CTRL+C** to stop it.

---

## 6. Run as a Windows Service

1. Open `nssm.exe` (from the downloaded NSSM).
2. In the setup window, fill in:

- **Path** → `C:\path\to\project\.venv\Scripts\python.exe`
- **Arguments** →

  ```
  -m waitress --host=0.0.0.0 --port=8080 wsgi:app
  ```

- **Startup Directory** → project root folder (where `wsgi.py` is located).

3. Click **Install Service**.

---

## 7. Start the Service

1. Open **Windows Services** (search "Services" in Start menu).
2. Find service named **synergee-app**.
3. Right-click → **Start**.

✅ Now the app runs in the background automatically.
You can close CMD and everything else—the app stays online.

---

## 🎉 Done!

The Synergee App is now running as a production-style service on Windows.
It will automatically start whenever the server restarts.

---
