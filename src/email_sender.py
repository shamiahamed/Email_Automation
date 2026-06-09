import smtplib
import socket
import base64
import os
import json
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders


def build_email(config, recipient_email, role, company_name=None, resume_path=None, cc_self=False):
    sender_email = config["sender_email"]
    your_name = config["your_name"]
    your_phone = config["your_phone"]
    your_linkedin = config["your_linkedin"]

    subject = f"Application for {role} - {your_name}"

    body = f"""Dear HR,

I am writing to apply for the {role} position at {company_name}. Please find my resume attached for your review.

I am confident that my skills and experience make me a strong fit for this role. I would welcome the opportunity to discuss how I can contribute to your team.

Thank you for your time and consideration.

Best regards,
{your_name}
{your_phone}
{sender_email}
{your_linkedin}"""

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject

    all_recipients = [recipient_email]
    if cc_self:
        msg["Cc"] = sender_email
        all_recipients.append(sender_email)

    msg.attach(MIMEText(body, "plain"))

    attachment_name = None
    if resume_path and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(resume_path)
            part.add_header("Content-Disposition", f"attachment; filename={filename}")
            msg.attach(part)
            attachment_name = filename

    return msg, all_recipients, attachment_name


def send_via_brevo_api(config, recipient_email, role, resume_path, cc_self, company_name):
    sender_email = config["sender_email"]
    your_name = config["your_name"]
    your_phone = config["your_phone"]
    your_linkedin = config["your_linkedin"]
    subject = f"Application for {role} - {your_name}"

    body = f"""Dear HR,

I am writing to apply for the {role} position at {company_name}. Please find my resume attached for your review.

I am confident that my skills and experience make me a strong fit for this role. I would welcome the opportunity to discuss how I can contribute to your team.

Thank you for your time and consideration.

Best regards,
{your_name}
{your_phone}
{your_linkedin}
{sender_email}"""

    payload = {
        "sender": {"name": your_name, "email": sender_email},
        "to": [{"email": recipient_email}],
        "subject": subject,
        "textContent": body,
    }

    if cc_self:
        payload["cc"] = [{"email": sender_email}]

    if resume_path and os.path.exists(resume_path):
        with open(resume_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        payload["attachment"] = [{
            "content": encoded,
            "name": os.path.basename(resume_path),
        }]

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=data,
        headers={
            "api-key": config["brevo_api_key"],
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status == 201
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8")
        raise Exception(f"Brevo API error ({e.code}): {err}")
    except urllib.error.URLError as e:
        raise Exception(f"Brevo API connection failed: {e.reason}")


def send_email(config, recipient_email, role, resume_path, cc_self=False, company_name=None):
    if config.get("brevo_api_key"):
        return send_via_brevo_api(config, recipient_email, role, resume_path, cc_self, company_name)

    sender_email = config["sender_email"]
    sender_password = config["sender_password"]
    smtp_login = config.get("smtp_login", sender_email)

    msg, all_recipients, _ = build_email(config, recipient_email, role, company_name, resume_path, cc_self)

    socket.setdefaulttimeout(15)
    last_error = None
    ports = [465, 587]
    for port in ports:
        try:
            if port == 465:
                server = smtplib.SMTP_SSL(config["smtp_server"], port, timeout=15)
            else:
                server = smtplib.SMTP(config["smtp_server"], port, timeout=15)
                server.starttls()
            with server:
                server.login(smtp_login, sender_password)
                server.sendmail(sender_email, all_recipients, msg.as_string())
            return True
        except Exception as e:
            last_error = e
            continue

    raise last_error


def preview_email(config, recipient_email, role, company_name=None, resume_path=None, cc_self=False):
    msg, all_recipients, attachment_name = build_email(config, recipient_email, role, company_name, resume_path, cc_self)
    return {
        "to": recipient_email,
        "cc": config["sender_email"] if cc_self else None,
        "subject": msg["Subject"],
        "body": msg.get_payload(0).get_payload(decode=True).decode("utf-8") if isinstance(msg.get_payload(0), MIMEText) else "",
        "attachment": attachment_name,
    }
