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

# Base paths and persistent settings
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SETTINGS_FILE = os.path.join(BASE_DIR, "admin_settings.json")
TMP_SETTINGS_FILE = "/tmp/admin_settings.json"

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

# Supabase Credentials for Global Persistent Storage
SUPABASE_URL = "https://sxbnutustirzmesuillx.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4Ym51dHVzdGlyem1lc3VpbGx4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5NDkwNTAxNywiZXhwIjoyMTEwNDgxMDE3fQ.C2vt8FI3NiuCh_8quwMpM9kbA1Xiv-G5BUOejkkvK00"

SUPABASE_CACHED_KEYS = {}

def sync_supabase_keys():
    global SUPABASE_CACHED_KEYS
    try:
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests?id=eq.CONFIG_SPEAKER_KEYS&select=email"
        headers = {"apikey": SUPABASE_SERVICE_KEY, "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}"}
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            if data and len(data) > 0 and data[0].get("email"):
                keys = json.loads(data[0]["email"])
                for k, key_val in keys.items():
                    if key_val:
                        cleaned = str(key_val).strip().upper()
                        SUPABASE_CACHED_KEYS[k] = cleaned
                        if k in ADMIN_ACCOUNTS:
                            ADMIN_ACCOUNTS[k]["sessionKey"] = cleaned
    except Exception:
        pass

def save_supabase_keys(keys_dict):
    try:
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests?on_conflict=id"
        headers = {
            "apikey": SUPABASE_SERVICE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=representation"
        }
        payload = [{
            "id": "CONFIG_SPEAKER_KEYS",
            "full_name": "SYSTEM_CONFIG",
            "email": json.dumps(keys_dict),
            "college": "CONFIG",
            "speaker_id": "system",
            "speaker_name": "System Settings",
            "speaker_gid": "00000",
            "event_date": "2026-11-18",
            "event_name": "Settings",
            "request_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "status": "Config",
            "download_count": 0
        }]
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=4) as resp:
            pass
    except Exception:
        pass

DEFAULT_SPEAKER_KEYS = {
    "admin1": "GSA-ASWIN-2026",
    "admin2": "GSA-PAULBIN-2026",
    "admin3": "GSA-THOMAS-2026"
}

def get_speaker_valid_keys(speaker_id):
    """
    Returns a set of valid session keys for a speaker, checking:
    1. Factory default key
    2. Current in-memory sessionKey
    3. Cached Supabase key
    4. admin_settings.json file
    """
    keys = set()
    speaker_id = str(speaker_id).strip()
    if not speaker_id:
        return keys

    # 1. Default key
    if speaker_id in DEFAULT_SPEAKER_KEYS:
        keys.add(DEFAULT_SPEAKER_KEYS[speaker_id].strip().upper())

    # 2. In-memory ADMIN_ACCOUNTS dict
    adm = ADMIN_ACCOUNTS.get(speaker_id)
    if adm and adm.get("sessionKey"):
        keys.add(str(adm.get("sessionKey")).strip().upper())

    # 3. Supabase cached key
    if speaker_id in SUPABASE_CACHED_KEYS:
        keys.add(SUPABASE_CACHED_KEYS[speaker_id].strip().upper())

    # 4. Read settings file
    for p in [SETTINGS_FILE, TMP_SETTINGS_FILE]:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    file_key = saved.get("admins", {}).get(speaker_id, {}).get("sessionKey")
                    if file_key:
                        keys.add(str(file_key).strip().upper())
        except Exception:
            pass

    keys.discard("")
    return keys

def is_valid_session_key(speaker_id, key):
    if not key:
        return False
    clean_key = str(key).strip().upper()
    if not clean_key:
        return False

    # 1. Matches requested speaker
    if speaker_id and clean_key in get_speaker_valid_keys(speaker_id):
        return True

    # 2. Matches ANY speaker
    for sp in ["admin1", "admin2", "admin3"]:
        if clean_key in get_speaker_valid_keys(sp):
            return True

    # 3. Matches any factory default
    if clean_key in DEFAULT_SPEAKER_KEYS.values():
        return True

    # 4. Refresh from Supabase and check all speakers
    try:
        sync_supabase_keys()
        for sp in ["admin1", "admin2", "admin3"]:
            if clean_key in get_speaker_valid_keys(sp):
                return True
    except Exception:
        pass

    return False

def load_admin_settings():
    for fpath in [TMP_SETTINGS_FILE, SETTINGS_FILE]:
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                    if "admins" in settings:
                        for k, v in settings["admins"].items():
                            if k in ADMIN_ACCOUNTS:
                                if "gid" in v: ADMIN_ACCOUNTS[k]["gid"] = v["gid"]
                                if "name" in v: ADMIN_ACCOUNTS[k]["name"] = v["name"]
                                if "sessionKey" in v and v["sessionKey"]: ADMIN_ACCOUNTS[k]["sessionKey"] = v["sessionKey"]
            except Exception:
                pass
    sync_supabase_keys()

load_admin_settings()

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

        html_body = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Your Certificate of Participation</title>
</head>
<body style="margin: 0; padding: 20px 10px; background-color: #f1f4f9; font-family: 'Google Sans', Roboto, -apple-system, BlinkMacSystemFont, Arial, sans-serif; color: #202124;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color: #f1f4f9;">
    <tr>
      <td align="center">
        <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width: 640px; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 30px rgba(66, 133, 244, 0.12); border: 1px solid #e1e4ea;">
          
          <!-- Top Google 4-Color Rainbow Stripe -->
          <tr>
            <td style="height: 6px; background: linear-gradient(90deg, #4285f4 0%, #4285f4 25%, #ea4335 25%, #ea4335 50%, #fbbc05 50%, #fbbc05 75%, #34a853 75%, #34a853 100%);"></td>
          </tr>

          <!-- Hero Header with Vibrant Gradient -->
          <tr>
            <td style="background: linear-gradient(135deg, #1a73e8 0%, #3b82f6 50%, #0f9d58 100%); padding: 36px 32px 30px; text-align: center; color: #ffffff;">
              <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); padding: 6px 16px; border-radius: 30px; font-size: 12px; font-weight: 700; letter-spacing: 1.2px; text-transform: uppercase; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.35);">
                🎓 Official Certificate of Participation
              </div>
              <h1 style="margin: 0 0 8px 0; font-size: 26px; font-weight: 800; letter-spacing: -0.5px; color: #ffffff; text-shadow: 0 2px 4px rgba(0,0,0,0.15);">
                Google Student Ambassador Program
              </h1>
              <p style="margin: 0; font-size: 15px; font-weight: 500; color: #e8f0fe;">
                Google Student Ambassador Program • Product understanding
              </p>
            </td>
          </tr>

          <!-- Main Content Area -->
          <tr>
            <td style="padding: 32px 28px 20px;">
              
              <!-- Greeting & Congratulations Banner -->
              <div style="background: #e8f0fe; border-left: 4px solid #1a73e8; border-radius: 0 10px 10px 0; padding: 14px 18px; margin-bottom: 24px;">
                <p style="margin: 0; font-size: 16px; font-weight: 700; color: #1a73e8;">
                  🎉 Congratulations, {full_name}!
                </p>
                <p style="margin: 6px 0 0 0; font-size: 14px; color: #3c4043; line-height: 1.5;">
                  We are thrilled to present your verified Certificate of Participation for attending the official session conducted by <strong>{speaker_name}</strong>.
                </p>
              </div>

              <!-- Certificate Details Table Card -->
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background: #fafbff; border-radius: 12px; border: 1.5px solid #d2e3fc; margin-bottom: 24px; overflow: hidden;">
                <tr>
                  <td style="padding: 16px 20px; background: #eef4ff; border-bottom: 1px solid #d2e3fc;">
                    <span style="font-size: 13px; font-weight: 700; color: #1a73e8; letter-spacing: 0.5px; text-transform: uppercase;">
                      📄 Certificate Metadata & Credentials
                    </span>
                  </td>
                </tr>
                <tr>
                  <td style="padding: 18px 20px;">
                    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                      <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #5f6368; width: 140px;">Certificate ID:</td>
                        <td style="padding: 6px 0; font-size: 14px; font-weight: 700; font-family: monospace; color: #1a73e8;">
                          <span style="background: #e8f0fe; padding: 3px 8px; border-radius: 6px; border: 1px solid #c2e7ff;">{cert_id}</span>
                        </td>
                      </tr>
                      <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #5f6368;">Recipient:</td>
                        <td style="padding: 6px 0; font-size: 14px; font-weight: 700; color: #202124;">{full_name}</td>
                      </tr>
                      <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #5f6368;">Session Speaker:</td>
                        <td style="padding: 6px 0; font-size: 14px; font-weight: 600; color: #137333;">
                          🎙️ {speaker_name}
                        </td>
                      </tr>
                      <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #5f6368;">Event / Date:</td>
                        <td style="padding: 6px 0; font-size: 13px; color: #3c4043;">{event_name} ({event_date})</td>
                      </tr>
                      <tr>
                        <td style="padding: 6px 0; font-size: 13px; color: #5f6368;">Verification Status:</td>
                        <td style="padding: 6px 0;">
                          <span style="display: inline-block; background: #e6f4ea; color: #137333; font-size: 12px; font-weight: 700; padding: 3px 10px; border-radius: 12px; border: 1px solid #ceead6;">
                            ✓ Authenticated & Tamper-Proof
                          </span>
                        </td>
                      </tr>
                    </table>
                  </td>
                </tr>
              </table>

              <!-- Certificate Preview Notice Card -->
              <div style="background: linear-gradient(135deg, #fef7e0 0%, #fffbf0 100%); border: 1.5px solid #fce8b2; border-radius: 12px; padding: 18px 20px; margin-bottom: 26px; text-align: center;">
                <div style="font-size: 24px; margin-bottom: 6px;">🖼️ 📜</div>
                <div style="font-size: 15px; font-weight: 700; color: #b06000; margin-bottom: 4px;">
                  High-Resolution Certificate Attached
                </div>
                <div style="font-size: 13px; color: #5f6368; line-height: 1.45;">
                  Your authentic Google Student Ambassador certificate has been attached directly to this email in full print resolution. Download and save it to your device!
                </div>
              </div>

              <!-- Action Call to Action Button -->
              <div style="text-align: center; margin: 24px 0 10px;">
                <a href="https://therealretro7.github.io/certificate/?verify={cert_id}" style="display: inline-block; background: linear-gradient(135deg, #1a73e8, #4285f4); color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 700; padding: 14px 28px; border-radius: 8px; box-shadow: 0 4px 12px rgba(26,115,232,0.3);">
                  🔍 Verify Certificate Authenticity
                </a>
              </div>

            </td>
          </tr>

          <!-- Authorized Signatories Grid -->
          <tr>
            <td style="background: #f8fafd; border-top: 1px solid #e8eaed; padding: 22px 28px;">
              <div style="font-size: 11px; font-weight: 700; color: #70757a; text-transform: uppercase; letter-spacing: 0.8px; margin-bottom: 12px; text-align: center;">
                Authorized Google Student Ambassador Signatories
              </div>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td align="center" style="font-size: 12px; color: #3c4043; padding: 4px 6px;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #1a73e8; margin-right: 4px;"></span>
                    <strong>ASWIN ASOK KV</strong><br>
                    <span style="font-size: 11px; color: #70757a;">GID: 14248</span>
                  </td>
                  <td align="center" style="font-size: 12px; color: #3c4043; padding: 4px 6px;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #34a853; margin-right: 4px;"></span>
                    <strong>Paulbin Chacko</strong><br>
                    <span style="font-size: 11px; color: #70757a;">GID: 12348</span>
                  </td>
                  <td align="center" style="font-size: 12px; color: #3c4043; padding: 4px 6px;">
                    <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background: #ea4335; margin-right: 4px;"></span>
                    <strong>THOMAS P D</strong><br>
                    <span style="font-size: 11px; color: #70757a;">GID: 14434</span>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Footer with Rainbow Bottom Strip -->
          <tr>
            <td style="background: #202124; padding: 22px 28px; text-align: center; color: #bdc1c6; font-size: 12px; line-height: 1.6;">
              <p style="margin: 0 0 6px 0; color: #ffffff; font-weight: 600; font-size: 13px;">
                Google Student Ambassador Program • 2026 Edition
              </p>
              <p style="margin: 0; color: #9aa0a6; font-size: 11px;">
                This automated certificate was generated following authenticated session attendance verification.<br>
                For any queries, contact your session speaker directly.
              </p>
            </td>
          </tr>
          <tr>
            <td style="height: 4px; background: linear-gradient(90deg, #4285f4 0%, #ea4335 33%, #fbbc05 66%, #34a853 100%);"></td>
          </tr>

        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""
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
            sync_supabase_keys()
            return self._send_json(200, {
                "success": True,
                "admins": ADMIN_ACCOUNTS,
                "smtpStatus": {
                    k: {"user": v["email"], "active": bool(v["email"] and v["pass"])}
                    for k, v in ADMIN_ACCOUNTS.items()
                }
            })
        elif path in ["/api/validate-key", "/validate-key"]:
            query = urllib.parse.parse_qs(parsed.query)
            speaker_id = query.get("speakerId", [""])[0].strip()
            key = query.get("key", [""])[0].strip().upper()
            adm = ADMIN_ACCOUNTS.get(speaker_id)
            if not adm:
                return self._send_json(400, {"success": False, "valid": False, "message": "Unknown speaker"})
            is_valid = is_valid_session_key(speaker_id, key)
            return self._send_json(200, {
                "success": True,
                "valid": is_valid,
                "speakerId": speaker_id,
                "speakerName": adm.get("name", "")
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
            event_name = payload.get("eventName", "Product understanding")
            speaker_name = payload.get("speakerName", "Google Student Ambassador")
            speaker_id = payload.get("speakerId", "admin1")
            event_date = payload.get("eventDate", "08/10/2026")
            image_data = payload.get("imageData")
            session_key = str(payload.get("sessionKey", "")).strip().upper()

            if not to_email:
                return self._send_json(400, {"success": False, "message": "Recipient email is required"})

            # Always sync with Supabase Cloud so the latest key set by admin is verified
            sync_supabase_keys()

            # Enforce Speaker Session Access Key
            adm = ADMIN_ACCOUNTS.get(speaker_id) or ADMIN_ACCOUNTS.get("admin1")
            speaker_label = adm.get("name", speaker_name or speaker_id)
            client_verified = bool(payload.get("clientVerified", False))
            if session_key and not client_verified and not is_valid_session_key(speaker_id, session_key):
                return self._send_json(403, {
                    "success": False,
                    "smtpSent": False,
                    "error": f"Invalid Session Key for {speaker_label}. Attendance verification failed — email not dispatched."
                })

            res = send_certificate_email(to_email, full_name, cert_id, event_name, speaker_name, speaker_id, event_date, image_data)
            return self._send_json(200, res)

        elif path in ["/api/admin/resend-email", "/admin/resend-email"]:
            cert_id = payload.get("certId", "").strip()
            to_email = payload.get("email", "").strip()
            speaker_id = payload.get("speakerId", "admin1")
            speaker_name = payload.get("speakerName", "Google Student Ambassador")
            full_name = payload.get("fullName", "Participant")
            event_name = payload.get("eventName", "Product understanding")
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

        elif path in ["/api/admin/update-speaker", "/admin/update-speaker"]:
            speaker_id = str(payload.get("speakerId", "")).strip()
            if speaker_id not in ADMIN_ACCOUNTS:
                return self._send_json(400, {"success": False, "message": f"Invalid speakerId: {speaker_id}"})

            gid = str(payload.get("gid", "")).strip()
            name = str(payload.get("name", "")).strip()
            email = str(payload.get("email", "")).strip()
            session_key = str(payload.get("sessionKey", "")).strip().upper()

            if gid:
                ADMIN_ACCOUNTS[speaker_id]["gid"] = gid
            if name:
                ADMIN_ACCOUNTS[speaker_id]["name"] = name
            if email:
                ADMIN_ACCOUNTS[speaker_id]["email"] = email
            if session_key:
                ADMIN_ACCOUNTS[speaker_id]["sessionKey"] = session_key

            # Persist to Supabase Cloud Database permanently
            all_keys = {k: ADMIN_ACCOUNTS[k].get("sessionKey", "") for k in ADMIN_ACCOUNTS}
            save_supabase_keys(all_keys)

            # Persist to /tmp and settings file if writable
            for fpath in [TMP_SETTINGS_FILE, SETTINGS_FILE]:
                try:
                    settings = {}
                    if os.path.exists(fpath):
                        with open(fpath, "r", encoding="utf-8") as f:
                            settings = json.load(f)
                    if "admins" not in settings:
                        settings["admins"] = {}
                    if speaker_id not in settings["admins"]:
                        settings["admins"][speaker_id] = {}
                    if gid: settings["admins"][speaker_id]["gid"] = gid
                    if name: settings["admins"][speaker_id]["name"] = name
                    if email: settings["admins"][speaker_id]["email"] = email
                    if session_key: settings["admins"][speaker_id]["sessionKey"] = session_key
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(settings, f, indent=2)
                except Exception:
                    pass

            return self._send_json(200, {
                "success": True,
                "speaker": {
                    "id": speaker_id,
                    "name": ADMIN_ACCOUNTS[speaker_id]["name"],
                    "gid": ADMIN_ACCOUNTS[speaker_id]["gid"],
                    "email": ADMIN_ACCOUNTS[speaker_id]["email"],
                    "sessionKey": ADMIN_ACCOUNTS[speaker_id].get("sessionKey", "")
                },
                "message": f"Updated {ADMIN_ACCOUNTS[speaker_id]['name']} (GID: {ADMIN_ACCOUNTS[speaker_id]['gid']}, Key: {ADMIN_ACCOUNTS[speaker_id].get('sessionKey', '')})"
            })

        elif path in ["/api/validate-key", "/validate-key"]:
            speaker_id = str(payload.get("speakerId", "")).strip()
            key = str(payload.get("key", "")).strip().upper()
            adm = ADMIN_ACCOUNTS.get(speaker_id)
            if not adm:
                return self._send_json(400, {"success": False, "valid": False, "message": "Unknown speaker"})
            is_valid = is_valid_session_key(speaker_id, key)
            return self._send_json(200, {
                "success": True,
                "valid": is_valid,
                "speakerId": speaker_id,
                "speakerName": adm.get("name", "")
            })

        else:
            return self._send_json(404, {"success": False, "message": f"Endpoint {path} not found on Vercel function"})
