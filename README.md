# Email Automation

Upload your resume and send it to recruiters with a single click. Features company name personalization, role selection, preview before sending, and auto-CC.

## Structure

```
Email_Automation/
├── src/
│   ├── app.py            # Flask web server
│   └── email_sender.py   # Gmail SMTP sender
├── templates/
│   └── index.html        # Mobile-friendly form
├── uploads/              # Temp resume storage
├── config.json           # Credentials & contact info
├── requirements.txt
├── Procfile              # Render deployment
└── .gitignore
```

## Usage

```bash
pip install -r requirements.txt
python src/app.py
```

Access on your phone at `http://YOUR_PC_IP:5000`.

## Deploy on Render

1. Push this repo to GitHub
2. Go to [Render](https://dashboard.render.com) → New Web Service → connect your repo
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn src.app:app --bind 0.0.0.0:$PORT`
5. Add env vars: `SENDER_EMAIL`, `SENDER_PASSWORD`, `YOUR_NAME`, `YOUR_PHONE`, `YOUR_LINKEDIN`
