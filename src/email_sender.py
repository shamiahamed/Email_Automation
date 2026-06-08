import smtplib
import socket
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import os


def build_email(config, recipient_email, role, company_name=None, resume_path=None, cc_self=False):
    sender_email = config["sender_email"]
    your_name = config["your_name"]
    your_phone = config["your_phone"]
    your_linkedin = config["your_linkedin"]

    subject = f"Application for {role} - {your_name}"

    body = f"""Dear HR,

I hope this message finds you well. I am writing to express my enthusiastic interest in the {role} position at {company_name}. With a strong commitment to excellence and a proven ability to deliver results, I am confident that my skills and experience make me a strong candidate for this opportunity.

Throughout my professional journey, I have cultivated a versatile skill set that allows me to adapt quickly and contribute meaningfully from day one. I am particularly drawn to this opportunity at {company_name} as it aligns perfectly with my passion for driving impact and continuous growth.

Please find my resume attached for your kind review. I would welcome the opportunity to discuss how my background and dedication can add value to your team.

Thank you sincerely for your time and consideration. I look forward to hearing from you.

Warm regards,
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

    if resume_path and os.path.exists(resume_path):
        with open(resume_path, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            filename = os.path.basename(resume_path)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename={filename}",
            )
            msg.attach(part)

    return msg, all_recipients


def send_email(config, recipient_email, role, resume_path, cc_self=False, company_name=None):
    sender_email = config["sender_email"]
    sender_password = config["sender_password"]
    smtp_login = config.get("smtp_login", sender_email)

    msg, all_recipients = build_email(config, recipient_email, role, company_name, resume_path, cc_self)

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
    msg, all_recipients = build_email(config, recipient_email, role, company_name, resume_path, cc_self)
    return {
        "to": recipient_email,
        "cc": config["sender_email"] if cc_self else None,
        "subject": msg["Subject"],
        "body": msg.get_payload(0).get_payload(decode=True).decode("utf-8") if isinstance(msg.get_payload(0), MIMEText) else "",
        "attachment": os.path.basename(resume_path) if resume_path and os.path.exists(resume_path) else None,
    }
