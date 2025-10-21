from flask import Flask, render_template, request, jsonify, send_file, make_response
import os, io, json, datetime

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")
app.config["SAMPLE_DATA"] = os.path.join(os.path.dirname(__file__), "sample_data")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

def load_json(name):
    with open(os.path.join(app.config["SAMPLE_DATA"], name), "r", encoding="utf-8") as f:
        return json.load(f)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.post("/api/analyze")
def api_analyze():
    """
    Demo endpoint.
    - If 'simulate' in form/json -> return demo data.
    - If a file is uploaded under 'dump', we store it and still return demo data (stub pipeline).
    Replace this with real Volatility + AI logic later.
    """
    # Check for simulate flag
    simulate = False
    if request.is_json:
        simulate = request.json.get("simulate", False)
    else:
        simulate = request.form.get("simulate", "false").lower() == "true"

    if "dump" in request.files:
        f = request.files["dump"]
        if f.filename:
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], f.filename)
            f.save(save_path)

    # Load demo data
    summary = load_json("demo_summary.json")
    alerts = load_json("demo_alerts.json")
    process_tree = load_json("demo_process_tree.json")

    # Compose response
    out = {
        "summary": summary["summary"],
        "key_findings": summary["key_findings"],
        "risk_score": summary["risk_score"],
        "alerts": alerts,
        "process_tree": process_tree,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds")
    }
    return jsonify(out)

@app.post("/export_report")
def export_report():
    """
    Accepts JSON payload with summary, findings, risk, alerts, and process tree.
    Renders an HTML report and returns it as a downloadable .html file.
    """
    data = request.get_json(force=True)

    html = render_template(
        "report.html",
        title="volLite Forensic Report",
        generated_at=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        summary=data.get("summary", ""),
        findings=data.get("key_findings", []),
        risk_score=data.get("risk_score", 0),
        alerts=data.get("alerts", []),
        process_tree=data.get("process_tree", {}),
    )

    # Return as attachment
    fname = f"volLite_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    response = make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    response.headers["Content-Disposition"] = f"attachment; filename={fname}"
    return response

if __name__ == "__main__":
    app.run(debug=True)
