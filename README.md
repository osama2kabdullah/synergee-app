# 🚀 Synergee App – Deployment Guide (Windows Server)

This guide explains how to set up, run, and maintain the Synergee Flask application as a **production-like server** on Windows using **PM2 (Node.js process manager)**.

---

## Initial Setup

#### 1. Install Required Software

1. **Install Python**  
   👉 [Download Python](https://www.python.org/downloads/)  
   Make sure to check **“Add Python to PATH”** during installation.

2. **Install Git**  
   👉 [Download Git](https://git-scm.com/downloads)

3. **Install Node.js (for PM2)**  
   👉 [Download Node.js](https://nodejs.org/en/download/)  
   (This also installs `npm` which we’ll use to install PM2.)

---

#### 2. Get the Project

1. Download the project from GitHub:  
   👉 [Synergee App Repository](https://github.com/osama2kabdullah/synergee-app)

2. Place the provided files into the project root:

   - `.env` file  
   - `db_export.json` file  

---

#### 3. Setup the Environment

Open **Command Prompt (CMD)** inside the project folder and run:

```bash
# Create virtual environment
python -m venv .venv

# Activate environment
.venv\Scripts\activate

# Install project dependencies
pip install -r requirements.txt
````

---

#### 4. Database Setup

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

#### 5. Test Run the Application with Flask

Before using PM2, you can test the app with Flask:

```bash
# Activate environment if not already
.venv\Scripts\activate

# Run Flask app
flask run
```

👉 Open browser at:
`http://127.0.0.1:5000/api-button`

1. You will see a page with a Call API button.
2. Click the button and check the terminal for the output.

Once verified, press **CTRL+C** to stop the Flask server.

---

#### 6. Test Run with Waitress

Run the app using Waitress for production-like behavior:

```bash
waitress-serve --host=0.0.0.0 --port=8080 wsgi:app
```

👉 Open browser at:
`http://localhost:8080`

If the app runs correctly, press **CTRL+C** to stop it.

---

#### 7. Run with PM2 (Production Mode)

Now we’ll use **PM2** to keep the app running in the background.

1. Install PM2 globally (only once per server):

```bash
npm install -g pm2
```

2. Start the app with PM2:

```bash
pm2 start .venv/Scripts/python.exe --name synergee-app -- -m waitress --host=0.0.0.0 --port=8080 wsgi:app
```

Explanation:

* `pm2 start` → runs the process
* `.venv/Scripts/python.exe` → Python from your virtual environment
* `--name synergee-app` → gives the process a name
* The rest are the arguments for running Waitress with your `wsgi:app`.

3. Save the process list so PM2 restarts it on reboot:

```bash
pm2 save
```

4. Enable PM2 startup (so it launches on system boot):

```bash
pm2 startup
```

👉 Follow the printed instructions (PM2 will show a command you need to copy-paste once).

---

#### 8. Manage the Service

Useful PM2 commands:

```bash
# List running apps
pm2 list

# Restart app
pm2 restart synergee-app

# Stop app
pm2 stop synergee-app

# View logs
pm2 logs synergee-app
```

---

#### 🎉 Done!

The **Synergee App** is now running in the background under **PM2**.
It will automatically restart on crashes and also on server reboot.

👉 Open in browser:
`http://localhost:8080`

---

## Updating the Application on the Server

When you push new updates to GitHub, follow these steps on the server to deploy the latest version:

1. **Go to the project folder**:

```bash
cd C:\synergee-app
```

2. **Stop the running app with PM2**:

```bash
pm2 stop synergee-app
```

3. **Pull the latest changes from GitHub**:

```bash
git pull origin main

# ensure you are on the main branch
git checkout main
```

*(If your default branch is `master`, replace `main` with `master`.)*

4. **Replace the existing `db_export.json` file** with the new one if you received it.

5. **Activate the virtual environment**:

```bash
.venv\Scripts\activate
```

6. **Install updated dependencies**:

```bash
pip install -r requirements.txt
```

7. **Reset the database**:

```bash
# Delete old database
python delete_db.py   # (or manually remove the file if delete_db.py is not available)

# Create a fresh database
python create_db.py

# Import new data
python import_data.py

# Verify data integrity
python check_data.py
```

8. **Start the application again with PM2**:

```bash
pm2 start synergee-app
```

9. **Test the application**:
   Open your browser and navigate to:

```
http://localhost:8080
```

✅ If the app runs correctly, the update is complete.

---
