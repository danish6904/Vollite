# volLite Proactive Frontend (Flask + HTML/JS/CSS)

This is a starter frontend web app for *volLite – AI-Based Memory Forensics Assistant*.
It includes:
- Home, About, Contact, Dashboard pages
- Dashboard UI: file upload, summary, risk meter, process tree, alerts
- Report export to **HTML** (download and "Print to PDF" via browser)

## Quickstart
```bash
# 1) Create & activate a virtual environment (Windows PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt

# 3) Run the app
python app.py
# Open http://127.0.0.1:5000
```

### Notes
- PDF export uses the browser's "Print -> Save as PDF".
- Replace the demo analysis in `/api/analyze` with real Volatility + model logic later.
