import json
import os
from flask import Flask, render_template, request, jsonify
from email_sender import send_email, preview_email
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = os.path.join(os.path.dirname(__file__), "uploads")

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(BASE_DIR, "config.json")
if os.path.exists(config_path):
    with open(config_path) as f:
        config = json.load(f)
else:
    config = {}

config.setdefault("sender_email", os.getenv("SENDER_EMAIL", ""))
config.setdefault("sender_password", os.getenv("SENDER_PASSWORD", ""))
config.setdefault("your_name", os.getenv("YOUR_NAME", ""))
config.setdefault("your_phone", os.getenv("YOUR_PHONE", ""))
config.setdefault("your_linkedin", os.getenv("YOUR_LINKEDIN", ""))
config.setdefault("smtp_server", os.getenv("SMTP_SERVER", "smtp.gmail.com"))
config.setdefault("smtp_port", int(os.getenv("SMTP_PORT", "587")))
config.setdefault("roles", [
    "Software Engineer", "Full Stack Developer", "Frontend Developer",
    "Backend Developer", "Data Analyst", "Data Scientist",
    "DevOps Engineer", "Product Manager", "Project Manager",
    "QA Engineer", "Other"
])


def extract_form_data():
    recipient = request.form.get("recipient", "").strip()
    role = request.form.get("role", "").strip()
    company_name = request.form.get("company_name", "").strip()
    cc_self = request.form.get("cc_self") == "on"
    file = request.files.get("resume")
    resume_path = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        resume_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(resume_path)
    return recipient, role, company_name, cc_self, resume_path


@app.route("/")
def index():
    return render_template("index.html", roles=config["roles"], sender_email=config["sender_email"])


@app.route("/preview", methods=["POST"])
def preview():
    recipient, role, company_name, cc_self, resume_path = extract_form_data()

    if not recipient or not role or not company_name:
        return jsonify({"success": False, "message": "Recipient email, role, and company name are required."}), 400

    try:
        data = preview_email(config, recipient, role, company_name, resume_path, cc_self)
        data["company"] = company_name
        data["success"] = True
        return jsonify(data)
    except Exception as e:
        return jsonify({"success": False, "message": f"Preview failed: {str(e)}"}), 500
    finally:
        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)


@app.route("/send", methods=["POST"])
def send():
    recipient, role, company_name, cc_self, resume_path = extract_form_data()

    if not recipient or not role or not company_name:
        return jsonify({"success": False, "message": "Recipient email, role, and company name are required."}), 400

    try:
        send_email(config, recipient, role, resume_path, cc_self, company_name)
        msg = f"Resume sent successfully to {recipient}!"
        if cc_self:
            msg += f" (CC'd to {config['sender_email']})"
        return jsonify({"success": True, "message": msg})
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to send: {str(e)}"}), 500
    finally:
        if resume_path and os.path.exists(resume_path):
            os.remove(resume_path)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
