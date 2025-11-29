# 🚀 Synergee App – Deployment Guide (Windows Server)

This guide explains how to set up, run, and maintain the Synergee Flask application as a **production-like server** on Windows using **PM2 (Node.js process manager)**.

---

# 📦 1. Initial Setup

## 1. Install Required Software

### ✔ Python

👉 [https://www.python.org/downloads/](https://www.python.org/downloads/)
Make sure to check:
✅ **"Add Python to PATH"**

### ✔ Git

👉 [https://git-scm.com/downloads](https://git-scm.com/downloads)

### ✔ Node.js (required for PM2 option)

👉 [https://nodejs.org/en/download/](https://nodejs.org/en/download/)

This will also install `npm`.

### ✔ NSSM (required for Windows Service option)

👉 [https://nssm.cc/download](https://nssm.cc/download)

Download **NSSM**, extract it, and keep:

```
C:\nssm\nssm.exe
```

---

# 📥 2. Get the Project

1. Clone or download from GitHub:
   👉 [https://github.com/osama2kabdullah/synergee-app](https://github.com/osama2kabdullah/synergee-app)

2. Place the provided files into the project root:

   - `.env` file  
   - `db_export.json` file  

---

# 🏗 3. Setup the Python Environment

Open **Command Prompt (CMD)** in the project folder:

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

---

# 🗄 4. Database Setup

Run each command:

```bash
python create_db.py
python import_data.py
python check_data.py
```

---

# 🧪 5. Test Run the Application (Flask Dev Server)

```bash
.venv\Scripts\activate
flask run
```

Open browser:

👉 [http://127.0.0.1:5000](http://127.0.0.1:5000)

Press **CTRL+C** to stop the dev server.

---

# 🧪 6. Test Run with Waitress (Production WSGI Server)

```bash
waitress-serve --host=0.0.0.0 --port=8080 wsgi:app
```

Open:

👉 [http://localhost:8080](http://localhost:8080)

❗ If this works, you are ready for production deployment.

---

<br>

# ⚙️ 7. Deployment Option A (Recommended): Run with PM2

PM2 keeps the app running in the background and auto-restarts on system boot.

## 7.1 Install PM2 Globally

```bash
npm install -g pm2
```

## 7.2 Start the App with PM2

```bash
pm2 start .venv/Scripts/python.exe --name synergee-app -- -m waitress --host=0.0.0.0 --port=8080 wsgi:app
```

PM2 explanation:

* `.venv/Scripts/python.exe` → uses your virtual environment
* `--name synergee-app` → gives the process a readable name
* After `--`, the arguments go to Python
* It starts Waitress with your WSGI file

## 7.3 Save PM2 Boot Configuration

```bash
pm2 save
pm2 startup
```

PM2 will show a command to run once—copy & paste it.

## 7.4 PM2 Management Commands

```bash
pm2 list
pm2 restart synergee-app
pm2 stop synergee-app
pm2 logs synergee-app
```

👍 Your app now runs 24/7 and auto-starts after reboot.

---

<br>

# ⚙️ 8. Deployment Option B (BEST for reliability): Run as a Windows Service (NSSM)

This is the **most stable** long-term solution.
Windows Services:

✔ Run in the background
✔ Start automatically on boot
✔ Restart if they crash
✔ Require no terminal

---

## 8.1 Download NSSM

👉 [https://nssm.cc/download](https://nssm.cc/download)

Extract it and put:

```
C:\nssm\nssm.exe
```

---

## 8.3 Install the Service Using NSSM

Open CMD **as Administrator**: Go to the folder where NSSM extracted, and inside that have nss.exe. need to go into that folder.

```
nssm.exe install synergee-app
```

A GUI window opens.

Fill it out:

### **Application tab**

**Path:**

```
C:\path\to\synergee-app\.venv\Scripts\python.exe
```

**Arguments:**

```
-m waitress --host=0.0.0.0 --port=8080 wsgi:app
```

**Startup Directory:**

```
C:\path\to\synergee-app
```

Click **Install Service**.

---

## 8.4 Start the Service

Open Windows Services:
Search → **services.msc**

Find:

```
synergee-app
```

Right-click → **Start**

Now the Flask app is running in the background.

---

## 8.5 (Optional but Recommended) Enable Logs

Run:

```
C:\nssm\nssm.exe edit synergee-app
```

Under **I/O** tab:

```
stdout: C:\synergee-app\logs\output.log
stderr: C:\synergee-app\logs\error.log
```

Click **Save**.

---

## 8.6 Windows Service Management

Stop:

```
nssm stop synergee-app
```

Start:

```
nssm start synergee-app
```

Remove:

```
nssm remove synergee-app
```

---

<br>

# 🔄 9. Updating the Application

Whenever new updates are available:

```bash
cd C:\synergee-app
pm2 stop synergee-app   # if using PM2
nssm stop synergee-app  # if using Windows Service
```

Then pull updates:

```bash
git pull origin main
git checkout main   # ensure correct branch
```

Replace `.env` or `db_export.json` if provided.

Reinstall dependencies:

```bash
.venv\Scripts\activate
pip install -r requirements.txt
```

Reset & import database:

```bash
python delete_db.py
python create_db.py
python import_data.py
python check_data.py
```

Restart app:

PM2:

```bash
pm2 start synergee-app
```

Windows Service:

```
nssm start synergee-app
```

---

<br>

# 🎉 Deployment Complete

Your Synergee App now supports:

✔ Flask dev server (testing)
✔ **Waitress + PM2** (simple + stable)
✔ **Waitress + Windows Service (NSSM)** (maximum reliability)
✔ Auto-restart
✔ Auto-boot startup
✔ Background operation
✔ Production-safe WSGI server
✔ Works with your internal 3-hour scheduler

Open the app at:

👉 [http://localhost:8080](http://localhost:8080)