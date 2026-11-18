# Google Student Ambassador Certificate Generator & Portal

A complete, dual-portal web application for requesting, generating, verifying, and managing official participation certificates for the **Google Student Ambassador Program 2026** event: **Build Your Fest Stall Edition**.

---

## 🌟 Key Features

### 1. Client Portal (Attendee Certificate Generator)
* **Interactive Request Form:**
  * Participant Full Name (with live real-time canvas preview).
  * Email Address & College / Institution / Department.
  * **Session Taken By (Mandatory Admin Selection):**
    * **Admin 1:** `ASWIN ASOK KV` (GID: 14248)
    * **Admin 2:** `Paulbin Chacko` (GID: 12348)
    * **Admin 3:** `THOMAS PD` (GID: 14434)
  * Event / Session Date (defaults to `08/10/2026`).
* **Pixel-Perfect Certificate Canvas Preview:**
  * Exact replica of the official reference template with Google logo, colorful GSA emblem, award ribbon badge, title card with rainbow underline, and cute Google doodles.
  * Dynamic recipient name in elegant italic serif typography.
  * Real scannable **QR Code** linking to online certificate verification.
  * Individual digital signatures assigned per speaker:
    * Aswin Asok KV: `Aswin Signature.png`
    * Paulbin Chacko: `paul_signature_transparent.png`
    * Thomas PD: `th.jpeg`
  * Dynamic **GID** in the bottom-right corner (`GID:14248`, `GID:12348`, or `GID:14434`).
* **High-Definition Downloads:**
  * **Download PNG (High-Res):** Crystal clear 1892 x 1064 resolution image.
  * **Download PDF:** Print-ready Landscape A4 vector certificate.
  * **Copy Verification Link:** Direct link to online authenticity verification.

---

### 2. Public Verification Portal
* Public verification tab where anyone can verify certificate authenticity by entering a Certificate ID or scanning the QR code.
* Shows official verified badge, participant name, event title, speaker name, GID, and issue date.

---

### 3. Admin Portal (Restricted to Authorized Admins)
* **Access Control:** Restricted strictly to the 3 authorized admins:
  * **Admin 1:** Username: `ASWIN ASOK KV` | Password: `Aswin_Achu12` | GID: `14248`
  * **Admin 2:** Username: `Paulbin Chacko` | Password: `Paulbin@2005` | GID: `12348`
  * **Admin 3:** Username: `THOMAS PD` | Password: `thomas@2026` | GID: `14434`
* **Admin Dashboard & Management:**
  * **Real-time Metrics:** Total Requests, My Session Requests (filtered to the logged-in admin), Pending Reviews, and Total Certificates Downloaded.
  * **Request Tracking Table:** Full table of all requesters with their name, email, college, chosen session speaker, status, and download counter.
  * **Interactive Actions:**
    * **View Certificate Modal:** Full-screen rendering of any participant's certificate.
    * **Download (PNG / PDF):** Direct download on behalf of attendees.
    * **Approve / Toggle Status:** Mark as Approved or Requested.
    * **Delete Request:** Remove invalid entries.
  * **Export to CSV:** One-click download of all request data in spreadsheet format for Excel or Google Sheets.
  * **Speaker Profiles & Signature Showcase:** Visual gallery of all 3 admin credentials, signatures, and assigned GIDs.

---

## 🚀 How to Run

### Method 1: Using the Startup Script (Recommended)
Double-click [start_portal.bat](file:///c:/Users/ASWIN/Downloads/certificate/start_portal.bat). It will start the Python server on `http://localhost:8000` and open it directly in your browser.

### Method 2: Manual Terminal Run
```powershell
cd C:\Users\ASWIN\Downloads\certificate
& "C:\Program Files\BorisFX\Mocha Pro 2023\python\python.exe" server.py
```
Then visit `http://localhost:8000` in any web browser.

### Method 3: Offline Direct Browser Open
You can also directly double-click [index.html](file:///c:/Users/ASWIN/Downloads/certificate/index.html) to open it in Chrome, Edge, or Firefox. All features (canvas rendering, QR generation, PDF export, admin login, and storage) will function offline via browser `localStorage`.

