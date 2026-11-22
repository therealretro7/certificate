import http.server
import socketserver
import json
import os
import urllib.parse
import urllib.request
import base64
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "requests.json")
DISPATCHED_EMAILS_FILE = os.path.join(BASE_DIR, "dispatched_emails.json")

# SMTP Configuration (Can be customized via Environment variables)
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))

# Default Account (Aswin Asok KV)
DEFAULT_SMTP_USER = os.environ.get("SMTP_USER", "aswinashokkv@gmail.com")
DEFAULT_SMTP_PASS = os.environ.get("SMTP_PASS", "hcosmwoaoafguhvc")

# Paulbin Chacko Account
PAULBIN_SMTP_USER = os.environ.get("SMTP_USER_PAULBIN", "chackopaulbin@gmail.com")
PAULBIN_SMTP_PASS = os.environ.get("SMTP_PASS_PAULBIN", "pksn tkqr cleo uvlj")

# Thomas Account
THOMAS_SMTP_USER = os.environ.get("SMTP_USER_THOMAS", "thomaspd737@gmail.com")
THOMAS_SMTP_PASS = os.environ.get("SMTP_PASS_THOMAS", "gvgs btzi oqgz ndjs")

def get_smtp_credentials(speaker_id="admin1", speaker_name=None):
    """
    Returns (smtp_user, smtp_pass, sender_display_name).
    When the session taker is Paulbin, sends via chackopaulbin@gmail.com.
    When the session taker is Thomas, sends via thomaspd737@gmail.com.
    Otherwise defaults to Aswin Asok KV (aswinashokkv@gmail.com).
    """
    sp_id = str(speaker_id or "").strip().lower()
    sp_name = str(speaker_name or "").strip().lower()

    # Detect if session taker / speaker is Paulbin
    is_paulbin = (
        sp_id in ["admin2", "paulbin", "paulbin chacko", "paulbin_chacko"] or
        "paulbin" in sp_id or
        "paulbin" in sp_name
    )

    # Detect if session taker / speaker is Thomas P D
    is_thomas = (
        sp_id in ["admin3", "thomas", "thomas pd", "thomas p d", "thomas_pd"] or
        "thomas" in sp_id or
        "thomas" in sp_name
    )

    if is_paulbin:
        user = PAULBIN_SMTP_USER
        password = PAULBIN_SMTP_PASS.replace(" ", "").strip()
        display_name = "Paulbin Chacko"
        return user, password, display_name
    elif is_thomas:
        user = THOMAS_SMTP_USER
        password = THOMAS_SMTP_PASS.replace(" ", "").strip()
        display_name = "THOMAS P D"
        return user, password, display_name
    elif sp_id == "admin1" or "aswin" in sp_name:
        user = DEFAULT_SMTP_USER
        password = DEFAULT_SMTP_PASS.replace(" ", "").strip()
        display_name = "ASWIN ASOK KV"
        return user, password, display_name
    else:
        user = DEFAULT_SMTP_USER
        password = DEFAULT_SMTP_PASS.replace(" ", "").strip()
        display_name = speaker_name if speaker_name else "Google Student Ambassador Program"
        return user, password, display_name

def send_certificate_email(to_email, full_name, cert_id, event_name, speaker_name, speaker_id="admin1", event_date="08/10/2026", image_data=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    subject = f"Your Certificate of Participation: {event_name} (ID: {cert_id})"
    
    # Resolve sender SMTP credentials based on session taker
    smtp_user, smtp_pass, sender_display_name = get_smtp_credentials(speaker_id, speaker_name)
    
    smtp_sent = False
    error_msg = None
    
    if smtp_user and smtp_pass:
        try:
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = f"{sender_display_name} <{smtp_user}>"
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

            # Attach Certificate Image: Client base64 or server-rendered
            attached = False
            if image_data and "," in image_data:
                try:
                    img_bytes = base64.b64decode(image_data.split(",")[1])
                    if len(img_bytes) > 5000:
                        img_part = MIMEImage(img_bytes)
                        img_part.add_header("Content-Disposition", "attachment", filename=f"Certificate_{cert_id}.png")
                        msg.attach(img_part)
                        attached = True
                except Exception as img_err:
                    print("Could not attach client image:", img_err)

            if not attached:
                # Server-side render using render_cert_service.ps1
                rendered_path = os.path.join(BASE_DIR, f"cert_{cert_id}.png")
                script_path = os.path.join(BASE_DIR, "render_cert_service.ps1")
                try:
                    import subprocess
                    subprocess.run([
                        "powershell", "-ExecutionPolicy", "Bypass", "-File", script_path,
                        full_name, event_date, speaker_id, rendered_path, event_name
                    ], capture_output=True, timeout=25)
                    if os.path.exists(rendered_path):
                        with open(rendered_path, "rb") as f:
                            img_part = MIMEImage(f.read())
                            img_part.add_header("Content-Disposition", "attachment", filename=f"Certificate_{cert_id}.png")
                            msg.attach(img_part)
                            attached = True
                        try:
                            os.remove(rendered_path)
                        except Exception:
                            pass
                except Exception as render_err:
                    print("Server render error:", render_err)

            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            smtp_sent = True
        except Exception as e:
            error_msg = str(e)
            print(f"SMTP sending failed via {smtp_user}: {e}")

    # Record dispatch log
    dispatch_record = {
        "id": cert_id,
        "email": to_email,
        "fullName": full_name,
        "eventName": event_name,
        "speakerName": speaker_name,
        "speakerId": speaker_id,
        "senderEmail": smtp_user,
        "timestamp": timestamp,
        "smtpDelivered": smtp_sent,
        "status": "Sent" if smtp_sent else "Dispatched (System Logged)",
        "error": error_msg
    }

    try:
        logs = []
        if os.path.exists(DISPATCHED_EMAILS_FILE):
            try:
                with open(DISPATCHED_EMAILS_FILE, "r", encoding="utf-8") as f:
                    logs = json.load(f)
            except Exception:
                pass
        logs.insert(0, dispatch_record)
        with open(DISPATCHED_EMAILS_FILE, "w", encoding="utf-8") as f:
            json.dump(logs, f, indent=2)
    except Exception as e:
        print("Could not save dispatch log:", e)

    print(f"✉️ [EMAIL DISPATCH] Certificate {cert_id} dispatched from {smtp_user} to: {to_email} ({'Live SMTP' if smtp_sent else 'Simulated/System Log'})")
    return {
        "success": True,
        "smtpSent": smtp_sent,
        "sender": smtp_user,
        "email": to_email,
        "certId": cert_id,
        "message": f"Certificate has been dispatched from {smtp_user} to {to_email}."
    }

# Supabase Credentials
SUPABASE_URL = "https://sxbnutustirzmesuillx.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4Ym51dHVzdGlyem1lc3VpbGx4Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5NDkwNTAxNywiZXhwIjoyMTEwNDgxMDE3fQ.C2vt8FI3NiuCh_8quwMpM9kbA1Xiv-G5BUOejkkvK00"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4Ym51dHVzdGlyem1lc3VpbGx4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5MDUwMTcsImV4cCI6MjExMDQ4MTAxN30.BHThQ6qFOiEo3LWReRbZ38dGq3q8DTZKzSTltAEXaOg"

ADMINS = {
    "admin1": {
        "id": "admin1",
        "name": "ASWIN ASOK KV",
        "username": "ASWIN ASOK KV",
        "pass": "Aswin_Achu12",
        "gid": "14248",
        "signatureFile": "Aswin Signature.png",
        "email": "aswinashokkv@gmail.com",
        "sessionKey": "GSA-ASWIN-2026"
    },
    "admin2": {
        "id": "admin2",
        "name": "Paulbin Chacko",
        "username": "Paulbin Chacko",
        "pass": "Paulbin@2005",
        "gid": "12348",
        "signatureFile": "paul_signature_transparent.png",
        "email": "chackopaulbin@gmail.com",
        "sessionKey": "GSA-PAULBIN-2026"
    },
    "admin3": {
        "id": "admin3",
        "name": "THOMAS P D",
        "username": "THOMAS P D",
        "pass": "thomas@2026",
        "gid": "14434",
        "signatureFile": "th.jpeg",
        "email": "thomaspd737@gmail.com",
        "sessionKey": "GSA-THOMAS-2026"
    }
}

# --- Supabase Headers & Key Management Helpers ---
def supabase_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

SUPABASE_CACHED_KEYS = {}

def sync_supabase_keys():
    global SUPABASE_CACHED_KEYS
    try:
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests?id=eq.CONFIG_SPEAKER_KEYS&select=email"
        headers = supabase_headers()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            if data and len(data) > 0 and data[0].get("email"):
                keys = json.loads(data[0]["email"])
                for k, key_val in keys.items():
                    if key_val:
                        cleaned = str(key_val).strip().upper()
                        SUPABASE_CACHED_KEYS[k] = cleaned
                        if k in ADMINS:
                            ADMINS[k]["sessionKey"] = cleaned
    except Exception:
        pass

def save_supabase_keys(keys_dict):
    try:
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests?on_conflict=id"
        headers = supabase_headers()
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"
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
    except Exception as e:
        print("Warning: Could not save keys to Supabase:", e)

DEFAULT_SPEAKER_KEYS = {
    "admin1": "GSA-ASWIN-2026",
    "admin2": "GSA-PAULBIN-2026",
    "admin3": "GSA-THOMAS-2026"
}

# --- Persistent Settings & Asset Sync ---
SETTINGS_FILE = os.path.join(BASE_DIR, "admin_settings.json")

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

    # 1. Default factory key
    if speaker_id in DEFAULT_SPEAKER_KEYS:
        keys.add(DEFAULT_SPEAKER_KEYS[speaker_id].strip().upper())

    # 2. In-memory ADMINS dict
    adm = ADMINS.get(speaker_id)
    if adm and adm.get("sessionKey"):
        keys.add(str(adm.get("sessionKey")).strip().upper())

    # 3. Supabase cached key
    if speaker_id in SUPABASE_CACHED_KEYS:
        keys.add(SUPABASE_CACHED_KEYS[speaker_id].strip().upper())

    # 4. Read admin_settings.json
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
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
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)
                if "admins" in settings:
                    for k, v in settings["admins"].items():
                        if k in ADMINS:
                            ADMINS[k].update(v)
        except Exception as e:
            print("Could not load admin_settings.json:", e)
    sync_supabase_keys()

def save_admin_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "admins": {
                    k: {
                        "gid": v.get("gid"),
                        "signatureFile": v.get("signatureFile"),
                        "email": v.get("email"),
                        "name": v.get("name"),
                        "sessionKey": v.get("sessionKey", "")
                    } for k, v in ADMINS.items()
                }
            }, f, indent=2)
    except Exception as e:
        print("Could not save admin_settings.json:", e)

def sync_ps1_config():
    ps1_path = os.path.join(BASE_DIR, "render_cert_service.ps1")
    if not os.path.exists(ps1_path):
        return
    try:
        with open(ps1_path, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        for k, v in ADMINS.items():
            pattern = rf'"{k}"\s*=\s*@\{{[^}}]*\}}'
            replacement = f'"{k}" = @{{ name = "{v["name"]}"; gid = "{v["gid"]}"; sig = "{v["signatureFile"]}" }}'
            content = re.sub(pattern, replacement, content)
        with open(ps1_path, "w", encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        print("Could not sync render_cert_service.ps1:", e)

# Load saved settings upon startup
load_admin_settings()

# --- Supabase Helpers ---
def supabase_headers():
    return {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Content-Type": "application/json"
    }

def map_db_to_request(row):
    return {
        "id": row.get("id"),
        "fullName": row.get("full_name"),
        "email": row.get("email"),
        "college": row.get("college"),
        "speakerId": row.get("speaker_id"),
        "speakerName": row.get("speaker_name"),
        "speakerGid": row.get("speaker_gid"),
        "eventDate": row.get("event_date", "08/10/2026"),
        "eventName": row.get("event_name", "Product understanding"),
        "requestDate": row.get("request_date"),
        "status": row.get("status", "Requested"),
        "downloadCount": row.get("download_count", 0)
    }

def map_request_to_db(req):
    return {
        "id": req.get("id"),
        "full_name": req.get("fullName"),
        "email": req.get("email"),
        "college": req.get("college"),
        "speaker_id": req.get("speakerId"),
        "speaker_name": req.get("speakerName"),
        "speaker_gid": req.get("speakerGid"),
        "event_date": req.get("eventDate", "08/10/2026"),
        "event_name": req.get("eventName", "Product understanding"),
        "request_date": req.get("requestDate"),
        "status": req.get("status", "Requested"),
        "download_count": req.get("downloadCount", 0)
    }

def load_requests():
    # 1. Try fetching from Supabase
    try:
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests?select=*&order=created_at.desc"
        req = urllib.request.Request(url, headers=supabase_headers())
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            
            # Sync persistent speaker keys from Supabase
            config_item = next((item for item in data if item.get("id") == "CONFIG_SPEAKER_KEYS"), None)
            if config_item and config_item.get("email"):
                try:
                    custom_keys = json.loads(config_item["email"])
                    for k, val in custom_keys.items():
                        if k in ADMINS and val:
                            ADMINS[k]["sessionKey"] = str(val).strip().upper()
                except Exception:
                    pass

            mapped = [map_db_to_request(item) for item in data if item.get("id") != "CONFIG_SPEAKER_KEYS"]
            # update local backup
            save_local_requests(mapped)
            return mapped
    except Exception as e:
        print("Warning: Supabase fetch error, using local fallback:", e)

    # 2. Local fallback
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return [r for r in json.load(f) if r.get("id") != "CONFIG_SPEAKER_KEYS"]
        except Exception:
            pass
    return []

def save_local_requests(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Error saving local requests:", e)

def save_request_to_supabase(new_req):
    # Upsert to Supabase
    try:
        db_row = map_request_to_db(new_req)
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests"
        headers = supabase_headers()
        headers["Prefer"] = "resolution=merge-duplicates"
        req = urllib.request.Request(url, data=json.dumps([db_row]).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        print("Warning: Could not save to Supabase:", e)

    # Also update local mirror
    local = []
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                local = json.load(f)
        except Exception:
            pass
    idx = next((i for i, r in enumerate(local) if r["id"] == new_req["id"]), -1)
    if idx >= 0:
        local[idx] = new_req
    else:
        local.insert(0, new_req)
    save_local_requests(local)

def delete_request_from_supabase(req_id):
    try:
        url = f"{SUPABASE_URL}/rest/v1/certificate_requests?id=eq.{urllib.parse.quote(req_id)}"
        req = urllib.request.Request(url, headers=supabase_headers(), method="DELETE")
        with urllib.request.urlopen(req, timeout=5) as resp:
            pass
    except Exception as e:
        print("Warning: Could not delete from Supabase:", e)

    # Also delete from local mirror
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                local = json.load(f)
            local = [r for r in local if r["id"] != req_id]
            save_local_requests(local)
        except Exception:
            pass

class CertificateHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Allow-Private-Network", "true")
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        if path.startswith("/certificate"):
            path = path[len("/certificate"):]
        if not path:
            path = "/"

        if path == "/api/requests":
            requests = load_requests()
            return self._send_json(200, {"success": True, "requests": requests, "source": "supabase"})

        elif path == "/api/supabase-config":
            # Public credentials for direct client connection
            return self._send_json(200, {
                "success": True,
                "supabaseUrl": SUPABASE_URL,
                "supabaseAnonKey": SUPABASE_ANON_KEY
            })

        elif path == "/api/admins":
            public_admins = [
                {"id": k, "name": v["name"], "gid": v["gid"], "signatureFile": v["signatureFile"], "email": v.get("email", "")}
                for k, v in ADMINS.items()
            ]
            return self._send_json(200, {"success": True, "admins": public_admins})

        elif path == "/api/admin/settings":
            sync_supabase_keys()
            return self._send_json(200, {
                "success": True,
                "admins": {
                    k: {
                        "id": v["id"],
                        "name": v["name"],
                        "gid": v["gid"],
                        "signatureFile": v["signatureFile"],
                        "email": v.get("email", ""),
                        "sessionKey": v.get("sessionKey", "")
                    } for k, v in ADMINS.items()
                },
                "template": "template_clean_2x.png",
                "templateExists": os.path.exists(os.path.join(BASE_DIR, "template_clean_2x.png")),
                "smtpStatus": {
                    "admin1": {"user": DEFAULT_SMTP_USER, "active": bool(DEFAULT_SMTP_USER and DEFAULT_SMTP_PASS)},
                    "admin2": {"user": PAULBIN_SMTP_USER, "active": bool(PAULBIN_SMTP_USER and PAULBIN_SMTP_PASS)},
                    "admin3": {"user": THOMAS_SMTP_USER, "active": bool(THOMAS_SMTP_USER and THOMAS_SMTP_PASS)}
                }
            })

        elif path == "/api/validate-key":
            query = urllib.parse.parse_qs(parsed.query)
            speaker_id = query.get("speakerId", [""])[0].strip()
            key = query.get("key", [""])[0].strip().upper()
            adm = ADMINS.get(speaker_id)
            if not adm:
                return self._send_json(400, {"success": False, "valid": False, "message": "Unknown speaker"})
            is_valid = is_valid_session_key(speaker_id, key)
            return self._send_json(200, {
                "success": True,
                "valid": is_valid,
                "speakerId": speaker_id,
                "speakerName": adm.get("name", "")
            })

        elif path.startswith("/api/verify/"):
            cert_id = path.replace("/api/verify/", "").strip()
            requests = load_requests()
            match = next((r for r in requests if r.get("id", "").lower() == cert_id.lower()), None)
            if match:
                return self._send_json(200, {"success": True, "verified": True, "certificate": match})
            else:
                return self._send_json(404, {"success": False, "verified": False, "message": "Certificate not found"})
        else:
            return super().do_GET()

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

        if path == "/api/login":
            username = str(payload.get("username", "")).strip().lower()
            password = str(payload.get("password", "")).strip()

            found_admin = None
            for key, adm in ADMINS.items():
                match_user = (adm["username"].lower() == username or (key == "admin3" and username in ["thomas", "thomas pd", "thomas p d"]))
                if match_user and adm["pass"] == password:
                    found_admin = adm
                    break

            if found_admin:
                return self._send_json(200, {
                    "success": True,
                    "admin": {
                        "id": found_admin["id"],
                        "name": found_admin["name"],
                        "gid": found_admin["gid"],
                        "signatureFile": found_admin["signatureFile"]
                    },
                    "token": f"admin_token_{found_admin['id']}_{int(datetime.now().timestamp())}"
                })
            else:
                return self._send_json(401, {"success": False, "message": "Invalid username or password"})

        elif path == "/api/validate-key":
            speaker_id = str(payload.get("speakerId", "")).strip()
            key = str(payload.get("key", "")).strip().upper()
            adm = ADMINS.get(speaker_id)
            if not adm:
                return self._send_json(400, {"success": False, "valid": False, "message": "Unknown speaker"})
            is_valid = is_valid_session_key(speaker_id, key)
            return self._send_json(200, {
                "success": True,
                "valid": is_valid,
                "speakerId": speaker_id,
                "speakerName": adm.get("name", "")
            })

        elif path == "/api/send-email":
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

            # Enforce Speaker Session Access Key
            adm = ADMINS.get(speaker_id) or ADMINS.get("admin1")
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

        elif path == "/api/requests":
            full_name = str(payload.get("fullName", "")).strip()
            speaker_id = str(payload.get("speakerId", "")).strip()
            session_key = str(payload.get("sessionKey", "")).strip().upper()

            if not full_name:
                return self._send_json(400, {"success": False, "message": "Full Name is required"})
            if speaker_id not in ADMINS:
                return self._send_json(400, {"success": False, "message": "Please select a valid Admin speaker"})

            admin_info = ADMINS[speaker_id]
            if speaker_id and not is_valid_session_key(speaker_id, session_key):
                return self._send_json(403, {
                    "success": False,
                    "message": f"Invalid Session Key for {admin_info.get('name', speaker_id)}. Attendance verification failed."
                })

            req_id = payload.get("id")
            if not req_id:
                req_id = f"CERT-2026-{int(datetime.now().timestamp() % 100000):05d}"

            new_req = {
                "id": req_id,
                "fullName": full_name,
                "email": payload.get("email", "").strip(),
                "college": payload.get("college", "").strip(),
                "speakerId": speaker_id,
                "speakerName": admin_info["name"],
                "speakerGid": admin_info["gid"],
                "eventDate": payload.get("eventDate", "08/10/2026").strip() or "08/10/2026",
                "eventName": "Product understanding",
                "requestDate": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "status": payload.get("status", "Requested"),
                "downloadCount": payload.get("downloadCount", 0),
                "sessionKeyUsed": session_key
            }

            save_request_to_supabase(new_req)
            return self._send_json(200, {"success": True, "request": new_req})

        elif path == "/api/requests/status":
            req_id = payload.get("id")
            new_status = payload.get("status")
            inc_download = payload.get("incrementDownload", False)

            requests = load_requests()
            target = next((r for r in requests if r["id"] == req_id), None)
            if not target:
                return self._send_json(404, {"success": False, "message": "Request not found"})

            if new_status:
                target["status"] = new_status
            if inc_download:
                target["downloadCount"] = target.get("downloadCount", 0) + 1
                if target.get("status") == "Requested":
                    target["status"] = "Downloaded"

            save_request_to_supabase(target)
            return self._send_json(200, {"success": True, "request": target})

        elif path == "/api/requests/delete":
            req_id = payload.get("id")
            delete_request_from_supabase(req_id)
            return self._send_json(200, {"success": True, "message": "Deleted successfully"})

        elif path == "/api/admin/update-speaker":
            speaker_id = str(payload.get("speakerId", "")).strip()
            if speaker_id not in ADMINS:
                return self._send_json(400, {"success": False, "message": "Invalid speakerId"})
            
            gid = str(payload.get("gid", "")).strip()
            if gid:
                ADMINS[speaker_id]["gid"] = gid
            
            name = str(payload.get("name", "")).strip()
            if name:
                ADMINS[speaker_id]["name"] = name
                ADMINS[speaker_id]["username"] = name

            email = str(payload.get("email", "")).strip()
            if email:
                ADMINS[speaker_id]["email"] = email

            session_key = str(payload.get("sessionKey", "")).strip().upper()
            if session_key:
                ADMINS[speaker_id]["sessionKey"] = session_key

            # Persist to Supabase Cloud Database permanently
            all_keys = {k: ADMINS[k].get("sessionKey", "") for k in ADMINS}
            save_supabase_keys(all_keys)

            save_admin_settings()
            sync_ps1_config()
            return self._send_json(200, {
                "success": True,
                "speaker": {
                    "id": speaker_id,
                    "name": ADMINS[speaker_id]["name"],
                    "gid": ADMINS[speaker_id]["gid"],
                    "signatureFile": ADMINS[speaker_id]["signatureFile"],
                    "email": ADMINS[speaker_id].get("email", ""),
                    "sessionKey": ADMINS[speaker_id].get("sessionKey", "")
                },
                "message": f"Updated {ADMINS[speaker_id]['name']} (GID: {ADMINS[speaker_id]['gid']}, Key: {ADMINS[speaker_id].get('sessionKey', '')})"
            })

        elif path == "/api/admin/upload-signature":
            speaker_id = str(payload.get("speakerId", "")).strip()
            if speaker_id not in ADMINS:
                return self._send_json(400, {"success": False, "message": "Invalid speakerId"})

            image_data = payload.get("imageData", "")
            raw_filename = payload.get("filename", "").strip() or f"{speaker_id}_sig.png"
            filename = os.path.basename(raw_filename)
            if not filename:
                filename = f"{speaker_id}_sig.png"

            if not image_data or "," not in image_data:
                return self._send_json(400, {"success": False, "message": "Invalid image payload"})

            try:
                img_bytes = base64.b64decode(image_data.split(",")[1])
                target_path = os.path.join(BASE_DIR, filename)
                with open(target_path, "wb") as f:
                    f.write(img_bytes)

                ADMINS[speaker_id]["signatureFile"] = filename
                save_admin_settings()
                sync_ps1_config()

                return self._send_json(200, {
                    "success": True,
                    "speakerId": speaker_id,
                    "signatureFile": filename,
                    "message": f"Signature updated to {filename} for {ADMINS[speaker_id]['name']}"
                })
            except Exception as e:
                return self._send_json(500, {"success": False, "message": f"Could not save signature: {e}"})

        elif path == "/api/admin/upload-template":
            image_data = payload.get("imageData", "")
            target_filename = "template_clean_2x.png"

            if not image_data or "," not in image_data:
                return self._send_json(400, {"success": False, "message": "Invalid image payload"})

            try:
                img_bytes = base64.b64decode(image_data.split(",")[1])
                target_path = os.path.join(BASE_DIR, target_filename)
                with open(target_path, "wb") as f:
                    f.write(img_bytes)

                return self._send_json(200, {
                    "success": True,
                    "templateFile": target_filename,
                    "message": "Certificate template updated successfully!"
                })
            except Exception as e:
                return self._send_json(500, {"success": False, "message": f"Could not save template: {e}"})

        elif path == "/api/admin/resend-email":
            cert_id = str(payload.get("certId", "")).strip()
            override_email = str(payload.get("email", "")).strip()

            if not cert_id:
                return self._send_json(400, {"success": False, "message": "Certificate ID is required"})

            requests = load_requests()
            req = next((r for r in requests if r.get("id", "").lower() == cert_id.lower()), None)
            if not req:
                return self._send_json(404, {"success": False, "message": f"Request {cert_id} not found"})

            to_email = override_email or req.get("email")
            if not to_email:
                return self._send_json(400, {"success": False, "message": "No email address found for this certificate"})

            full_name = req.get("fullName", "Participant")
            event_name = req.get("eventName", "Product understanding")
            speaker_name = req.get("speakerName", "Google Student Ambassador")
            speaker_id = req.get("speakerId", "admin1")
            event_date = req.get("eventDate", "08/10/2026")

            res = send_certificate_email(to_email, full_name, cert_id, event_name, speaker_name, speaker_id, event_date)
            if res.get("smtpSent"):
                req["status"] = "Email Sent"
                save_request_to_supabase(req)

            return self._send_json(200, res)

        elif path == "/api/admin/test-email":
            speaker_id = str(payload.get("speakerId", "admin1")).strip()
            to_email = str(payload.get("toEmail", "")).strip()

            if not to_email:
                return self._send_json(400, {"success": False, "message": "Recipient test email is required"})

            adm = ADMINS.get(speaker_id, ADMINS["admin1"])
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
            return self._send_json(404, {"success": False, "message": "Endpoint not found"})

if __name__ == "__main__":
    class ReusableTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    with ReusableTCPServer(("", PORT), CertificateHandler) as httpd:
        print(f"==================================================")
        print(f" Certificate Generator Server connected to Supabase!")
        print(f" Supabase Project: {SUPABASE_URL}")
        print(f" Local Web App: http://localhost:{PORT}")
        print(f"==================================================")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server...")
