from http.server import BaseHTTPRequestHandler
import json
import os
import smtplib
import base64
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

# SMTP Configurations
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

# Ambassador SMTP Accounts
ADMIN_ACCOUNTS = {
    "admin1": {
        "name": "ASWIN ASOK KV",
        "email": os.environ.get("SMTP_USER", "aswinashokkv@gmail.com"),
        "pass": os.environ.get("SMTP_PASS", "hcosmwoaoafguhvc"),
        "gid": "14248",
        "sessionKey": os.environ.get("SESSION_KEY_ADMIN1", "GSA-ASWIN-2026")
    },
    "admin2": {
        "name": "Paulbin Chacko",
        "email": os.environ.get("SMTP_USER_PAULBIN", "chackopaulbin@gmail.com"),
        "pass": os.environ.get("SMTP_PASS_PAULBIN", "pksntkqrcleouvlj"),
        "gid": "12348",
        "sessionKey": os.environ.get("SESSION_KEY_ADMIN2", "GSA-PAULBIN-2026")
    },
    "admin3": {
        "name": "THOMAS P D",
        "email": os.environ.get("SMTP_USER_THOMAS", "thomaspd737@gmail.com"),
        "pass": os.environ.get("SMTP_PASS_THOMAS", "gvgsbtzioqgzndjs"),
        "gid": "14434",
        "sessionKey": os.environ.get("SESSION_KEY_ADMIN3", "GSA-THOMAS-2026")
    }
}

def resolve_smtp_credentials(speaker_id=None, speaker_name=None):
    sp_id = str(speaker_id or "").strip().lower()
    sp_name = str(speaker_name or "").strip().lower()

    if sp_id in ["admin2", "paulbin", "paulbin chacko"] or "paulbin" in sp_id or "paulbin" in sp_name:
        adm = ADMIN_ACCOUNTS["admin2"]
        return adm["email"], adm["pass"].replace(" ", ""), "Paulbin Chacko"
    elif sp_id in ["admin3", "thomas", "thomas pd", "thomas p d", "thomas_pd"] or "thomas" in sp_id or "thomas" in sp_name:
        adm = ADMIN_ACCOUNTS["admin3"]
        return adm["email"], adm["pass"].replace(" ", ""), "THOMAS P D"
    else:
        adm = ADMIN_ACCOUNTS["admin1"]
        return adm["email"], adm["pass"].replace(" ", ""), "ASWIN ASOK KV"

def send_certificate_email(to_email, full_name, cert_id, event_name, speaker_name, speaker_id="admin1", event_date="08/10/2026", image_data=None):
    smtp_user, smtp_pass, sender_display = resolve_smtp_credentials(speaker_id, speaker_name)
    subject = f"Your Certificate of Participation: {event_name} (ID: {cert_id})"
    
    smtp_sent = False
    error_msg = None

    try:
        msg = MIMEMultipart("related")
        msg["Subject"] = subject
        msg["From"] = f"{sender_display} <{smtp_user}>"
        msg["To"] = to_email

        html_body = f"""
        <html>
        <body style="font-family: 'Google Sans', Roboto, Arial, sans-serif; background-color: #f8f9fa; padding: 24px; color: #202124;">
          <div style="max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #dadce0; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
            <div style="background: linear-gradient(135deg, #1a73e8, #4285f4); padding: 24px; color: white; text-align: center;">
              <h1 style="margin: 0; font-size: 24px; font-weight: 600;">Google Student Ambassador Program</h1>
              <p style="margin: 6px 0 0; opacity: 0.9; font-size: 15px;">Certificate of Participation</p>
            </div>
            <div style="padding: 28px;">
              <h2 style="font-size: 20px; color: #202124; margin-top: 0;">Dear {full_name},</h2>
              <p style="font-size: 15px; line-height: 1.6; color: #3c4043;">
                Congratulations! Your official Certificate of Participation for <strong>{event_name}</strong> conducted by <strong>{speaker_name}</strong> has been generated and validated.
              </p>
              <div style="background: #f1f3f4; border-radius: 8px; padding: 16px; margin: 20px 0; font-size: 14px;">
                <div><strong>Certificate ID:</strong> <span style="font-family: monospace;">{cert_id}</span></div>
                <div style="margin-top: 6px;"><strong>Issued To:</strong> {full_name}</div>
                <div style="margin-top: 6px;"><strong>Ambassador:</strong> {speaker_name}</div>
                <div style="margin-top: 6px;"><strong>Issue Date:</strong> {event_date}</div>
                <div style="margin-top: 6px;"><strong>Status:</strong> Authenticated ✅</div>
              </div>
              <p style="font-size: 14px; color: #5f6368;">
                Your official certificate image is attached to this email. You can also verify this certificate anytime using Certificate ID <strong>{cert_id}</strong>.
              </p>
            </div>
          </div>
        </body>
        </html>
        """
        msg.attach(MIMEText(html_body, "html"))

        # Attach image if passed from canvas
        if image_data and "," in image_data:
            try:
                img_bytes = base64.b64decode(image_data.split(",")[1])
                if len(img_bytes) > 500:
                    img_part = MIMEImage(img_bytes)
                    img_part.add_header("Content-Disposition", "attachment", filename=f"Certificate_{cert_id}.jpg")
                    msg.attach(img_part)
            except Exception as e:
                print("Could not attach client image:", e)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)
        smtp_sent = True
    except Exception as e:
        error_msg = str(e)
        print(f"SMTP sending failed via {smtp_user}: {e}")

    return {
        "success": True,
        "smtpSent": smtp_sent,
        "sender": smtp_user,
        "email": to_email,
        "certId": cert_id,
        "error": error_msg,
        "message": f"Certificate dispatched from {smtp_user} to {to_email}." if smtp_sent else f"Email error: {error_msg}"
    }

class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/certificate"):
            path = path[len("/certificate"):]

        if path in ["/api/admins", "/admins"]:
            return self._send_json(200, {
                "success": True,
                "admins": [
                    {"id": k, "name": v["name"], "gid": v["gid"], "email": v["email"]}
                    for k, v in ADMIN_ACCOUNTS.items()
                ]
            })
        elif path in ["/api/admin/settings", "/admin/settings"]:
            return self._send_json(200, {
                "success": True,
                "admins": ADMIN_ACCOUNTS,
                "smtpStatus": {
                    k: {"user": v["email"], "active": bool(v["email"] and v["pass"])}
                    for k, v in ADMIN_ACCOUNTS.items()
                }
            })
        else:
            return self._send_json(200, {"success": True, "service": "GSA Certificate API (Vercel Serverless)"})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/certificate"):
            path = path[len("/certificate"):]

        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path in ["/api/send-email", "/send-email"]:
            to_email = payload.get("email", "").strip()
            full_name = payload.get("fullName", "").strip()
            cert_id = payload.get("certId", "").strip()
            event_name = payload.get("eventName", "Game On: Imagine the Impossible")
            speaker_name = payload.get("speakerName", "Google Student Ambassador")
            speaker_id = payload.get("speakerId", "admin1")
            event_date = payload.get("eventDate", "08/10/2026")
            image_data = payload.get("imageData")
            session_key = str(payload.get("sessionKey", "")).strip().upper()

            if not to_email:
                return self._send_json(400, {"success": False, "message": "Recipient email is required"})

            # Enforce Speaker Session Access Key
            adm = ADMIN_ACCOUNTS.get(speaker_id)
            if adm:
                required_key = str(adm.get("sessionKey", "")).strip().upper()
                if required_key and session_key != required_key:
                    return self._send_json(403, {
                        "success": False,
                        "smtpSent": False,
                        "error": f"Invalid Session Key for {adm.get('name', speaker_id)}. Attendance verification failed — email not dispatched."
                    })

            res = send_certificate_email(to_email, full_name, cert_id, event_name, speaker_name, speaker_id, event_date, image_data)
            return self._send_json(200, res)

        elif path in ["/api/admin/resend-email", "/admin/resend-email"]:
            cert_id = payload.get("certId", "").strip()
            to_email = payload.get("email", "").strip()
            speaker_id = payload.get("speakerId", "admin1")
            speaker_name = payload.get("speakerName", "Google Student Ambassador")
            full_name = payload.get("fullName", "Participant")
            event_name = payload.get("eventName", "Game On: Imagine the Impossible")
            event_date = payload.get("eventDate", "08/10/2026")
            image_data = payload.get("imageData")

            if not to_email:
                return self._send_json(400, {"success": False, "message": "Email is required"})

            res = send_certificate_email(to_email, full_name, cert_id, event_name, speaker_name, speaker_id, event_date, image_data)
            return self._send_json(200, res)

        elif path in ["/api/admin/test-email", "/admin/test-email"]:
            speaker_id = str(payload.get("speakerId", "admin1")).strip()
            to_email = str(payload.get("toEmail", "")).strip()

            if not to_email:
                return self._send_json(400, {"success": False, "message": "Recipient test email is required"})

            adm = ADMIN_ACCOUNTS.get(speaker_id, ADMIN_ACCOUNTS["admin1"])
            test_cert_id = f"TEST-{int(datetime.now().timestamp() % 10000)}"
            res = send_certificate_email(
                to_email=to_email,
                full_name="Ambassador Test Delivery",
                cert_id=test_cert_id,
                event_name="Diagnostic SMTP Delivery Test",
                speaker_name=adm["name"],
                speaker_id=speaker_id,
                event_date=datetime.now().strftime("%d/%m/%Y")
            )
            return self._send_json(200, res)

        else:
            return self._send_json(404, {"success": False, "message": f"Endpoint {path} not found on Vercel function"})
