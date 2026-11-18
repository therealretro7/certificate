/**
 * Google Student Ambassador Certificate Portal Application Logic
 * Supports Real-time Live Canvas Generation, PDF/PNG Downloads,
 * Admin Authentication & Requests Tracking, and Verification System.
 * Database: Supabase (sxbnutustirzmesuillx.supabase.co)
 */

// Supabase Configuration
const SUPABASE_URL = "https://sxbnutustirzmesuillx.supabase.co";
const SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InN4Ym51dHVzdGlyem1lc3VpbGx4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3OTQ5MDUwMTcsImV4cCI6MjExMDQ4MTAxN30.BHThQ6qFOiEo3LWReRbZ38dGq3q8DTZKzSTltAEXaOg";

// Resolve backend API URL (supports Vercel serverless, local server on port 8000, Live Server on 5500, and file://)
function getBackendApiUrl(endpoint) {
  // When deployed to Vercel or any cloud domain, use relative endpoint to invoke Vercel serverless function
  if (window.location.protocol.startsWith("http") && window.location.hostname !== "localhost" && window.location.hostname !== "127.0.0.1") {
    return endpoint;
  }
  // When running locally on port 8000
  if ((window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") && window.location.port === "8000") {
    return endpoint;
  }
  // When running locally from file:// or a different port (e.g. 5500), target local python server
  return `http://localhost:8000${endpoint}`;
}

// --- Supabase REST Helpers ---
async function sbFetch(path, method = "GET", body = null, extraHeaders = {}) {
  const opts = {
    method,
    headers: {
      "apikey": SUPABASE_ANON_KEY,
      "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
      "Content-Type": "application/json",
      "Prefer": "return=representation",
      ...extraHeaders
    }
  };
  if (body !== null) opts.body = JSON.stringify(body);
  const res = await fetch(`${SUPABASE_URL}${path}`, opts);
  if (!res.ok) {
    const err = await res.text();
    throw new Error(`Supabase error ${res.status}: ${err}`);
  }
  const text = await res.text();
  return text ? JSON.parse(text) : [];
}

function mapDbToRequest(row) {
  return {
    id: row.id,
    fullName: row.full_name,
    email: row.email,
    college: row.college,
    speakerId: row.speaker_id,
    speakerName: row.speaker_name,
    speakerGid: row.speaker_gid,
    eventDate: row.event_date || "08/10/2026",
    eventName: row.event_name || "Game On: Imagine the Impossible",
    requestDate: row.request_date,
    status: row.status || "Requested",
    downloadCount: row.download_count || 0
  };
}

function mapRequestToDb(req) {
  return {
    id: req.id,
    full_name: req.fullName,
    email: req.email || "",
    college: req.college || "",
    speaker_id: req.speakerId,
    speaker_name: req.speakerName,
    speaker_gid: req.speakerGid,
    event_date: req.eventDate || "08/10/2026",
    event_name: req.eventName || "Game On: Imagine the Impossible",
    request_date: req.requestDate,
    status: req.status || "Requested",
    download_count: req.downloadCount || 0
  };
}

async function sbLoadRequests() {
  try {
    const rows = await sbFetch("/rest/v1/certificate_requests?select=*&order=created_at.desc");
    
    // Automatically load & sync persistent speaker keys from Supabase Cloud
    const configRow = rows.find(r => r.id === "CONFIG_SPEAKER_KEYS");
    if (configRow && configRow.email) {
      try {
        const savedKeys = JSON.parse(configRow.email);
        for (const sp in savedKeys) {
          if (ADMIN_CONFIG[sp] && savedKeys[sp]) {
            ADMIN_CONFIG[sp].sessionKey = savedKeys[sp];
          }
        }
        localStorage.setItem("gsa_speaker_keys", JSON.stringify(savedKeys));
        validateSessionKeyUI();
        if (state.currentAdmin) {
          const quickInput = document.getElementById("quickSessionKeyInput");
          if (quickInput) quickInput.value = ADMIN_CONFIG[state.currentAdmin.id]?.sessionKey || "";
        }
      } catch (e) {}
    }

    return rows.filter(r => r.id !== "CONFIG_SPEAKER_KEYS").map(mapDbToRequest);
  } catch (err) {
    console.warn("Supabase read failed, using local fallback:", err);
    const local = localStorage.getItem("gsa_cert_requests");
    const parsed = local ? JSON.parse(local) : [];
    return parsed.filter(r => r.id !== "CONFIG_SPEAKER_KEYS");
  }
}

async function sbSaveSpeakerKeys(keys) {
  try {
    await sbFetch("/rest/v1/certificate_requests", "POST", [{
      id: "CONFIG_SPEAKER_KEYS",
      full_name: "SYSTEM_CONFIG",
      email: JSON.stringify(keys),
      college: "CONFIG",
      speaker_id: "system",
      speaker_name: "System Settings",
      speaker_gid: "00000",
      event_date: "2026-11-18",
      event_name: "Settings",
      request_date: new Date().toISOString().replace("T", " ").slice(0, 16),
      status: "Config",
      download_count: 0
    }], {
      "Prefer": "resolution=merge-duplicates,return=representation"
    });
    return true;
  } catch (err) {
    console.warn("Could not save keys to Supabase:", err);
    return false;
  }
}

async function sbUpsertRequest(req) {
  try {
    await sbFetch("/rest/v1/certificate_requests", "POST", [mapRequestToDb(req)], {
      "Prefer": "resolution=merge-duplicates,return=representation"
    });
    // update local cache too
    const cached = JSON.parse(localStorage.getItem("gsa_cert_requests") || "[]");
    const idx = cached.findIndex(r => r.id === req.id);
    if (idx >= 0) cached[idx] = req; else cached.unshift(req);
    localStorage.setItem("gsa_cert_requests", JSON.stringify(cached));
    return true;
  } catch (err) {
    console.warn("Supabase upsert failed:", err);
    // Local-only fallback
    const cached = JSON.parse(localStorage.getItem("gsa_cert_requests") || "[]");
    const idx = cached.findIndex(r => r.id === req.id);
    if (idx >= 0) cached[idx] = req; else cached.unshift(req);
    localStorage.setItem("gsa_cert_requests", JSON.stringify(cached));
    return false;
  }
}

async function sbDeleteRequest(id) {
  try {
    await sbFetch(`/rest/v1/certificate_requests?id=eq.${encodeURIComponent(id)}`, "DELETE");
    const cached = JSON.parse(localStorage.getItem("gsa_cert_requests") || "[]");
    localStorage.setItem("gsa_cert_requests", JSON.stringify(cached.filter(r => r.id !== id)));
    return true;
  } catch (err) {
    console.warn("Supabase delete failed:", err);
    const cached = JSON.parse(localStorage.getItem("gsa_cert_requests") || "[]");
    localStorage.setItem("gsa_cert_requests", JSON.stringify(cached.filter(r => r.id !== id)));
    return false;
  }
}

async function sbVerify(certId) {
  try {
    const rows = await sbFetch(`/rest/v1/certificate_requests?id=eq.${encodeURIComponent(certId)}&select=*`);
    return rows.length > 0 ? mapDbToRequest(rows[0]) : null;
  } catch (err) {
    console.warn("Supabase verify failed:", err);
    return null;
  }
}

// Registered Admin Ambasssadors
const ADMIN_CONFIG = {
  admin1: {
    id: "admin1",
    name: "ASWIN ASOK KV",
    displayName: "ASWIN ASOK KV",
    username: "ASWIN ASOK KV",
    pass: "Aswin_Achu12",
    gid: "14248",
    signatureFile: "Aswin Signature.png",
    email: "aswinashokkv@gmail.com",
    initial: "A",
    color: "#1a73e8",
    sessionKey: "GSA-ASWIN-2026"
  },
  admin2: {
    id: "admin2",
    name: "Paulbin Chacko",
    displayName: "Paulbin Chacko",
    username: "Paulbin Chacko",
    pass: "Paulbin@2005",
    gid: "12348",
    signatureFile: "paul_signature_transparent.png",
    email: "chackopaulbin@gmail.com",
    initial: "P",
    color: "#34a853",
    sessionKey: "GSA-PAULBIN-2026"
  },
  admin3: {
    id: "admin3",
    name: "THOMAS P D",
    displayName: "THOMAS P D",
    username: "THOMAS P D",
    pass: "thomas@2026",
    gid: "14434",
    signatureFile: "th.jpeg",
    email: "thomaspd737@gmail.com",
    initial: "T",
    color: "#ea4335",
    sessionKey: "GSA-THOMAS-2026"
  }
};

// Global App State
const state = {
  currentAdmin: null,
  requests: [],
  currentCertId: "CERT-2026-1001",
  activeFilters: {
    speaker: "all",
    status: "all",
    search: ""
  },
  loadedImages: {},
  canvasReady: false
};

// DOM Elements
const elements = {
  // Navigation
  navClientBtn: document.getElementById("navClientBtn"),
  navVerifyBtn: document.getElementById("navVerifyBtn"),
  navAdminBtn: document.getElementById("navAdminBtn"),
  brandHomeBtn: document.getElementById("brandHomeBtn"),
  viewClient: document.getElementById("viewClient"),
  viewVerify: document.getElementById("viewVerify"),
  viewAdmin: document.getElementById("viewAdmin"),
  activeAdminPill: document.getElementById("activeAdminPill"),
  adminAvatarInitial: document.getElementById("adminAvatarInitial"),
  adminNameDisplay: document.getElementById("adminNameDisplay"),
  adminLogoutBtn: document.getElementById("adminLogoutBtn"),

  // Client Form
  certificateForm: document.getElementById("certificateForm"),
  participantName: document.getElementById("participantName"),
  participantEmail: document.getElementById("participantEmail"),
  participantCollege: document.getElementById("participantCollege"),
  sessionDate: document.getElementById("sessionDate"),
  speakerCards: document.querySelectorAll(".speaker-card"),
  sessionAccessKey: document.getElementById("sessionAccessKey"),
  selectedSpeakerKeyName: document.getElementById("selectedSpeakerKeyName"),
  sessionKeyFeedback: document.getElementById("sessionKeyFeedback"),
  sessionKeyIcon: document.getElementById("sessionKeyIcon"),
  sessionKeyLockBadge: document.getElementById("sessionKeyLockBadge"),
  certificateCanvas: document.getElementById("certificateCanvas"),
  currentCertIdDisplay: document.getElementById("currentCertIdDisplay"),
  emailSentNotification: document.getElementById("emailSentNotification"),
  sentEmailAddressText: document.getElementById("sentEmailAddressText"),
  sentCertIdText: document.getElementById("sentCertIdText"),
  copyVerifyLinkBtn: document.getElementById("copyVerifyLinkBtn"),
  btnClientDownloadPng: document.getElementById("btnClientDownloadPng"),
  btnClientDownloadPdf: document.getElementById("btnClientDownloadPdf"),

  // Verification
  verifyInputId: document.getElementById("verifyInputId"),
  btnRunVerification: document.getElementById("btnRunVerification"),
  verifyResultBox: document.getElementById("verifyResultBox"),

  // Admin Portal
  adminLoginSection: document.getElementById("adminLoginSection"),
  adminDashboardSection: document.getElementById("adminDashboardSection"),
  adminLoginForm: document.getElementById("adminLoginForm"),
  adminUsernameInput: document.getElementById("adminUsernameInput"),
  adminPasswordInput: document.getElementById("adminPasswordInput"),
  btnAdminLogout: document.getElementById("btnAdminLogout"),
  btnExportCsv: document.getElementById("btnExportCsv"),
  adminSearchInput: document.getElementById("adminSearchInput"),
  requestsTableBody: document.getElementById("requestsTableBody"),
  requestCountLabel: document.getElementById("requestCountLabel"),

  // Admin Stats
  statTotalRequests: document.getElementById("statTotalRequests"),
  statMyRequests: document.getElementById("statMyRequests"),
  statPendingRequests: document.getElementById("statPendingRequests"),
  statDownloadedCount: document.getElementById("statDownloadedCount"),

  // Modal
  previewModal: document.getElementById("previewModal"),
  modalCloseBtn: document.getElementById("modalCloseBtn"),
  modalCanvas: document.getElementById("modalCanvas"),
  modalCertSub: document.getElementById("modalCertSub"),
  modalDownloadPngBtn: document.getElementById("modalDownloadPngBtn"),
  modalDownloadPdfBtn: document.getElementById("modalDownloadPdfBtn"),

  // Toast
  toast: document.getElementById("toastNotification"),
  toastMessage: document.getElementById("toastMessage")
};

// ========================================================
// THEME SETUP (DARK THEME DEFAULT)
// ========================================================
function setupTheme() {
  const savedTheme = localStorage.getItem("gsa_theme") || "dark";
  applyTheme(savedTheme);

  const toggleBtn = document.getElementById("themeToggleBtn");
  if (toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      const isDark = document.body.classList.contains("dark-theme") || !document.body.classList.contains("light-theme");
      const nextTheme = isDark ? "light" : "dark";
      applyTheme(nextTheme);
      localStorage.setItem("gsa_theme", nextTheme);
    });
  }
}

function applyTheme(theme) {
  const icon = document.getElementById("themeToggleIcon");
  if (theme === "light") {
    document.body.classList.remove("dark-theme");
    document.body.classList.add("light-theme");
    document.documentElement.setAttribute("data-theme", "light");
    if (icon) icon.textContent = "🌙";
  } else {
    document.body.classList.remove("light-theme");
    document.body.classList.add("dark-theme");
    document.documentElement.setAttribute("data-theme", "dark");
    if (icon) icon.textContent = "☀️";
  }
}

// ========================================================
// INITIALIZATION
// ========================================================
document.addEventListener("DOMContentLoaded", async () => {
  setupTheme();
  setupNavigation();
  setupFormListeners();
  setupAdminListeners();
  setupModal();
  checkUrlParams();

  // Preload Template & Signature Images
  await preloadAssets();

  // Load Initial Requests
  await loadRequests();

  // Check persisted admin session
  checkAdminSession();

  // Load custom session keys from local cache
  try {
    const savedKeys = JSON.parse(localStorage.getItem("gsa_speaker_keys") || "{}");
    for (const sp in savedKeys) {
      if (ADMIN_CONFIG[sp] && savedKeys[sp]) {
        ADMIN_CONFIG[sp].sessionKey = savedKeys[sp];
      }
    }
  } catch (e) {}

  // Initialize Session Key UI
  validateSessionKeyUI();

  // Render initial certificate preview
  renderCertificate();
});

// Preload Template & Signature Images for Canvas
async function preloadAssets() {
  const imagesToLoad = {
    template: "template_clean_2x.png",
    admin1Sig: ADMIN_CONFIG.admin1.signatureFile,
    admin2Sig: ADMIN_CONFIG.admin2.signatureFile,
    admin3Sig: ADMIN_CONFIG.admin3.signatureFile
  };

  const loadPromises = Object.entries(imagesToLoad).map(([key, src]) => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        state.loadedImages[key] = img;
        resolve();
      };
      img.onerror = () => {
        console.warn(`Could not preload ${src}, will use fallback`);
        resolve();
      };
      img.src = src;
    });
  });

  await Promise.all(loadPromises);
  state.canvasReady = true;
}

// Navigation Tab Switching
function setupNavigation() {
  const switchView = (targetView) => {
    elements.viewClient.classList.remove("active");
    elements.viewVerify.classList.remove("active");
    elements.viewAdmin.classList.remove("active");

    elements.navClientBtn.classList.remove("active");
    elements.navVerifyBtn.classList.remove("active");
    elements.navAdminBtn.classList.remove("active");

    if (targetView === "client") {
      elements.viewClient.classList.add("active");
      elements.navClientBtn.classList.add("active");
      renderCertificate();
    } else if (targetView === "verify") {
      elements.viewVerify.classList.add("active");
      elements.navVerifyBtn.classList.add("active");
    } else if (targetView === "admin") {
      elements.viewAdmin.classList.add("active");
      elements.navAdminBtn.classList.add("active");
      updateAdminView();
    }
  };

  elements.navClientBtn.addEventListener("click", () => switchView("client"));
  elements.brandHomeBtn.addEventListener("click", (e) => {
    e.preventDefault();
    switchView("client");
  });
  elements.navVerifyBtn.addEventListener("click", () => switchView("verify"));
  elements.navAdminBtn.addEventListener("click", () => switchView("admin"));
}

// Check URL parameters for direct verification e.g. ?verify=CERT-2026-1001
function checkUrlParams() {
  const params = new URLSearchParams(window.location.search);
  const verifyId = params.get("verify");
  if (verifyId) {
    elements.navVerifyBtn.click();
    elements.verifyInputId.value = verifyId;
    runVerification(verifyId);
  }
}

// Toast Notifications
function showToast(msg, duration = 3000) {
  elements.toastMessage.textContent = msg;
  elements.toast.classList.add("show");
  setTimeout(() => {
    elements.toast.classList.remove("show");
  }, duration);
}

// ========================================================
// CLIENT FORM & LIVE CANVAS GENERATION
// ========================================================
function setupFormListeners() {
  // Input live update
  const triggerRender = () => {
    renderCertificate();
  };

  elements.participantName.addEventListener("input", triggerRender);
  elements.sessionDate.addEventListener("input", triggerRender);

  // Speaker Card Selection
  elements.speakerCards.forEach((card) => {
    card.addEventListener("click", () => {
      elements.speakerCards.forEach((c) => c.classList.remove("selected"));
      card.classList.add("selected");
      const radio = card.querySelector(".speaker-radio");
      if (radio) {
        radio.checked = true;
      }
      const speaker = getSelectedSpeaker();
      if (elements.selectedSpeakerKeyName) {
        elements.selectedSpeakerKeyName.textContent = speaker.name;
      }
      validateSessionKeyUI();
      renderCertificate();
    });
  });

  // Session Key Live Validation
  if (elements.sessionAccessKey) {
    elements.sessionAccessKey.addEventListener("input", () => {
      validateSessionKeyUI();
    });
  }

  // Client Download PNG Button
  if (elements.btnClientDownloadPng) {
    elements.btnClientDownloadPng.addEventListener("click", () => {
      if (!verifyKeyBeforeDownload()) return;
      downloadCertificateImage(elements.certificateCanvas, "png");
    });
  }

  // Client Download PDF Button
  if (elements.btnClientDownloadPdf) {
    elements.btnClientDownloadPdf.addEventListener("click", () => {
      if (!verifyKeyBeforeDownload()) return;
      downloadCertificatePdf(elements.certificateCanvas);
    });
  }

  // Certificate Request Submit
  elements.certificateForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    await handleCertificateRequest();
  });

  // Client Copy Verify Link
  if (elements.copyVerifyLinkBtn) {
    elements.copyVerifyLinkBtn.addEventListener("click", () => {
      const url = `${window.location.origin}${window.location.pathname}?verify=${state.currentCertId}`;
      navigator.clipboard.writeText(url).then(() => {
        showToast("Verification link copied to clipboard! 📋");
      });
    });
  }

  // Public Verify Button
  elements.btnRunVerification.addEventListener("click", () => {
    const id = elements.verifyInputId.value.trim();
    if (id) {
      runVerification(id);
    }
  });

  elements.verifyInputId.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      const id = elements.verifyInputId.value.trim();
      if (id) runVerification(id);
    }
  });
}

// Live Attendee Session Key Validation UI
function validateSessionKeyUI() {
  if (!elements.sessionAccessKey) return false;
  const speaker = getSelectedSpeaker();
  const entered = elements.sessionAccessKey.value.trim().toUpperCase();
  const required = (speaker.sessionKey || "").trim().toUpperCase();

  if (!entered) {
    if (elements.sessionKeyFeedback) elements.sessionKeyFeedback.style.display = "none";
    if (elements.sessionKeyIcon) elements.sessionKeyIcon.textContent = "🔒";
    if (elements.sessionKeyLockBadge) {
      elements.sessionKeyLockBadge.textContent = "🔒 Required for Attendance";
      elements.sessionKeyLockBadge.style.background = "#e8f0fe";
      elements.sessionKeyLockBadge.style.color = "#1a73e8";
    }
    elements.sessionAccessKey.style.borderColor = "#dadce0";
    return false;
  }

  if (entered === required) {
    if (elements.sessionKeyFeedback) {
      elements.sessionKeyFeedback.style.display = "block";
      elements.sessionKeyFeedback.style.color = "#137333";
      elements.sessionKeyFeedback.innerHTML = `✓ Key Verified! Certificate unlocked for <strong>${escapeHtml(speaker.name)}</strong>.`;
    }
    if (elements.sessionKeyIcon) elements.sessionKeyIcon.textContent = "🔓";
    if (elements.sessionKeyLockBadge) {
      elements.sessionKeyLockBadge.textContent = "✓ Verified Attendee";
      elements.sessionKeyLockBadge.style.background = "#e6f4ea";
      elements.sessionKeyLockBadge.style.color = "#137333";
    }
    elements.sessionAccessKey.style.borderColor = "#34a853";
    return true;
  } else {
    if (elements.sessionKeyFeedback) {
      elements.sessionKeyFeedback.style.display = "block";
      elements.sessionKeyFeedback.style.color = "#d93025";
      elements.sessionKeyFeedback.innerHTML = `✕ Invalid key for <strong>${escapeHtml(speaker.name)}</strong>. Please check the session key distributed by your speaker.`;
    }
    if (elements.sessionKeyIcon) elements.sessionKeyIcon.textContent = "🔒";
    if (elements.sessionKeyLockBadge) {
      elements.sessionKeyLockBadge.textContent = "✕ Key Mismatch";
      elements.sessionKeyLockBadge.style.background = "#fce8e6";
      elements.sessionKeyLockBadge.style.color = "#c5221f";
    }
    elements.sessionAccessKey.style.borderColor = "#ea4335";
    return false;
  }
}

function verifyKeyBeforeDownload() {
  const speaker = getSelectedSpeaker();
  const isValid = validateSessionKeyUI();
  if (!isValid) {
    showToast(`🔒 Access Locked: Please enter the valid Session Key distributed by ${speaker.name} to download your certificate.`);
    if (elements.sessionAccessKey) {
      elements.sessionAccessKey.focus();
      elements.sessionAccessKey.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    return false;
  }
  return true;
}

function getSelectedSpeaker() {
  const checked = document.querySelector('input[name="speakerSelect"]:checked');
  const speakerId = checked ? checked.value : "admin1";
  return ADMIN_CONFIG[speakerId] || ADMIN_CONFIG.admin1;
}

// Real-Time Canvas Certificate Drawing using Official Clean Base Template
function renderCertificate(targetCanvas = elements.certificateCanvas, certData = null) {
  if (!targetCanvas) return;
  const ctx = targetCanvas.getContext("2d");
  const W = targetCanvas.width;    // 2048
  const H = targetCanvas.height;   // 1476

  // Resolve Data
  const speaker = certData ? ADMIN_CONFIG[certData.speakerId] : getSelectedSpeaker();
  const name    = certData ? certData.fullName  : (elements.participantName.value.trim() || "Participant Name");
  const date    = certData ? certData.eventDate : (elements.sessionDate.value.trim() || "08/10/2026");
  const certId  = certData ? certData.id        : state.currentCertId;

  if (targetCanvas === elements.certificateCanvas) {
    elements.currentCertIdDisplay.textContent = certId;
  }

  // 1. Draw Official Base Template
  if (state.loadedImages.template && state.loadedImages.template.complete && state.loadedImages.template.naturalWidth > 0) {
    ctx.drawImage(state.loadedImages.template, 0, 0, W, H);
  } else {
    // Fallback Background while template image is loading
    ctx.fillStyle = "#ffffff";
    ctx.fillRect(0, 0, W, H);
    ctx.strokeStyle = "#4285F4";
    ctx.lineWidth = 10;
    ctx.strokeRect(30, 30, W - 60, H - 60);
  }

  // 2. Draw Recipient Name (Centered over name line)
  // In 2048x1476 space: underline is at Y = 784, center X = 1024
  ctx.save();
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#111111";

  // Dynamic font sizing
  let nameFontSize = 54;
  if (name.length > 28) nameFontSize = 36;
  else if (name.length > 20) nameFontSize = 44;

  ctx.font = `italic 600 ${nameFontSize}px "Playfair Display", "Times New Roman", Georgia, serif`;
  ctx.fillText(name, W / 2, 768);
  ctx.restore();

  // 3. Draw Event Date (Left Side over Date underline)
  // In 2048x1476 space: center X = 376, underline is at Y = 1258
  ctx.save();
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#111111";
  ctx.font = 'bold 28px "Google Sans", Arial, sans-serif';
  ctx.fillText(date, 376, 1242);
  ctx.restore();

  // 4. Draw Signature & Speaker Details (Right Side)
  // In 2048x1476 space: center X = 1670, underline is at Y = 1258
  const sigCX = 1670;
  const sigImgKey = `${speaker.id}Sig`;
  const sigImg = state.loadedImages[sigImgKey];

  if (sigImg && sigImg.complete && sigImg.naturalWidth > 10) {
    ctx.save();
    const sigW = 240, sigH = 84;
    const sigX = sigCX - sigW / 2;
    const sigY = 1096;
    ctx.drawImage(sigImg, sigX, sigY, sigW, sigH);
    ctx.restore();
  } else {
    // Cursive calligraphy fallback
    ctx.save();
    ctx.textAlign = "center";
    ctx.textBaseline = "alphabetic";
    ctx.fillStyle = "#1a237e";
    ctx.font = 'italic 700 46px "Dancing Script", "Segoe Script", cursive';
    ctx.fillText(speaker.displayName, sigCX, 1148);
    ctx.restore();
  }

  // Speaker Name (Text right above subtitle)
  ctx.save();
  ctx.textAlign = "center";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#202124";
  ctx.font = '500 24px "Google Sans", Roboto, sans-serif';
  ctx.fillText(speaker.displayName, sigCX, 1205);

  // Subtitle "Session Speaker"
  ctx.fillStyle = "#3c4043";
  ctx.font = '400 19px "Google Sans", Roboto, sans-serif';
  ctx.fillText(speaker.role || "Session Speaker", sigCX, 1238);
  ctx.restore();

  // 6. Draw GID at Bottom-Right Corner
  ctx.save();
  ctx.textAlign = "right";
  ctx.textBaseline = "alphabetic";
  ctx.fillStyle = "#5f6368";
  ctx.font = '500 22px "Google Sans", Roboto, sans-serif';
  ctx.fillText(`GID:${speaker.gid}`, 1960, 1430);
  ctx.restore();
}

// Generate Scannable QR Code and Draw on Canvas
function drawVerificationQrCode(ctx, certId, name, speaker, x, y, w, h) {
  // Clear previous hidden QR
  const container = document.getElementById("hiddenQrContainer");
  container.innerHTML = "";

  // Encode structured verification payload / URL
  const verifyUrl = `${window.location.origin}${window.location.pathname}?verify=${certId}`;

  try {
    new QRCode(container, {
      text: verifyUrl,
      width: 144,
      height: 144,
      colorDark: "#000000",
      colorLight: "#ffffff",
      correctLevel: QRCode.CorrectLevel.M
    });

    const qrCanvas = container.querySelector("canvas");
    if (qrCanvas) {
      ctx.drawImage(qrCanvas, x, y, w, h);
    } else {
      const qrImg = container.querySelector("img");
      if (qrImg && qrImg.complete) {
        ctx.drawImage(qrImg, x, y, w, h);
      }
    }
  } catch (err) {
    console.error("QR Code generation error:", err);
  }
}

// Handle Form Submission: Saves request to Supabase, dispatches email, and updates UI
async function handleCertificateRequest() {
  const name = elements.participantName.value.trim();
  const email = elements.participantEmail.value.trim();
  const college = elements.participantCollege.value.trim();
  const speaker = getSelectedSpeaker();
  const eventDate = elements.sessionDate.value.trim() || "08/10/2026";
  const enteredKey = (elements.sessionAccessKey ? elements.sessionAccessKey.value : "").trim().toUpperCase();
  const requiredKey = (speaker.sessionKey || "").trim().toUpperCase();

  if (!name) {
    showToast("Please enter your full name");
    elements.participantName.focus();
    return;
  }

  if (!email || !email.includes("@")) {
    showToast("Please enter a valid email address for delivery");
    elements.participantEmail.focus();
    return;
  }

  // Attendance Verification Gate: Speaker Session Key
  if (!enteredKey) {
    showToast(`🔑 Speaker Session Key Required! Enter the secret key given by ${speaker.name}.`);
    if (elements.sessionAccessKey) {
      elements.sessionAccessKey.focus();
      elements.sessionAccessKey.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    validateSessionKeyUI();
    return;
  }

  if (enteredKey !== requiredKey) {
    showToast(`❌ Invalid Session Key for ${speaker.name}. Only attendees who attended this session can access certificates.`);
    if (elements.sessionAccessKey) {
      elements.sessionAccessKey.focus();
      elements.sessionAccessKey.select();
      elements.sessionAccessKey.scrollIntoView({ behavior: "smooth", block: "center" });
    }
    validateSessionKeyUI();
    return;
  }

  // Generate unique Certificate ID incorporating Speaker GID + timestamp
  const timestamp = Date.now().toString().slice(-4);
  const certId = `CERT-2026-${speaker.gid.slice(-3)}${timestamp}`;
  state.currentCertId = certId;

  // Render certificate first to ensure canvas has updated pixels for email dispatch
  renderCertificate();

  const newRequest = {
    id: certId,
    fullName: name,
    email: email,
    college: college,
    speakerId: speaker.id,
    speakerName: speaker.name,
    speakerGid: speaker.gid,
    eventDate: eventDate,
    eventName: "Game On: Imagine the Impossible",
    requestDate: new Date().toISOString().replace("T", " ").slice(0, 16),
    status: "Email Sent",
    downloadCount: 0,
    sessionKeyUsed: enteredKey
  };

  // 1. Upsert directly to Supabase
  const saved = await sbUpsertRequest(newRequest);
  state.requests.unshift(newRequest);

  // 2. Dispatch certificate email via backend API
  let emailDispatched = false;
  let senderEmailUsed = null;
  let dispatchError = null;

  try {
    let certImageBase64 = null;
    try {
      // Export canvas as JPEG (0.88 quality, ~200-300KB) for fast, snappy network delivery
      certImageBase64 = elements.certificateCanvas.toDataURL("image/jpeg", 0.88);
    } catch (canvasErr) {
      console.warn("Canvas export fallback (e.g. file:// taint):", canvasErr);
    }

    const apiUrl = getBackendApiUrl("/api/send-email");
    let resp = null;
    try {
      resp = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email,
          fullName: name,
          certId: certId,
          eventName: "Game On: Imagine the Impossible",
          speakerName: speaker.name,
          speakerId: speaker.id,
          eventDate: eventDate,
          sessionKey: enteredKey,
          imageData: certImageBase64
        })
      });
    } catch (fetchErr) {
      // If fetching localhost failed and we are on an HTTP server, try relative path fallback
      if (apiUrl.startsWith("http://localhost:8000") && window.location.protocol.startsWith("http")) {
        try {
          resp = await fetch("/api/send-email", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: email,
              fullName: name,
              certId: certId,
              eventName: "Game On: Imagine the Impossible",
              speakerName: speaker.name,
              speakerId: speaker.id,
              eventDate: eventDate,
              sessionKey: enteredKey,
              imageData: certImageBase64
            })
          });
        } catch (e2) {}
      }
    }

    if (resp && resp.status === 403) {
      const forbiddenData = await resp.json().catch(() => ({}));
      showToast(`❌ ${forbiddenData.error || 'Attendance verification failed: Invalid session key.'}`, 6000);
      return;
    }

    if (resp && resp.ok) {
      const data = await resp.json();
      if (data.smtpSent) {
        emailDispatched = true;
        senderEmailUsed = data.sender;
      } else {
        dispatchError = data.error || "Logged without live SMTP";
      }
    } else if (resp && resp.status === 404) {
      dispatchError = window.location.hostname.includes("github.io")
        ? "GitHub Pages is static: to send emails via Gmail, launch http://localhost:8000 (start_portal.bat)"
        : "Email endpoint not found (Ensure start_portal.bat is running)";
    } else if (resp) {
      dispatchError = `Server returned HTTP ${resp.status}`;
    } else {
      dispatchError = "Email server offline: run start_portal.bat on http://localhost:8000";
    }
  } catch (err) {
    dispatchError = "Backend server not responding on port 8000";
    console.warn("Email API call failed, saved to Supabase:", err);
  }

  // 3. Update Email Dispatched confirmation card on client portal
  if (elements.sentEmailAddressText && elements.sentCertIdText && elements.emailSentNotification) {
    elements.sentEmailAddressText.textContent = email;
    elements.sentCertIdText.textContent = certId;
    elements.emailSentNotification.style.display = "block";
    elements.emailSentNotification.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  if (emailDispatched) {
    showToast(`Certificate requested! Emailed from ${senderEmailUsed} to ${email} ✉️`);
  } else if (dispatchError) {
    showToast(`Saved to database! Note: Email delivery warning (${dispatchError})`, 6000);
  } else {
    showToast(`Certificate requested! Emailed to ${email} ✉️`);
  }
}

// Download High-Resolution PNG
function downloadCertificateImage(canvas, format = "png") {
  const name = elements.participantName.value.trim() || "Participant";
  const speaker = getSelectedSpeaker();
  const filename = `Certificate_${name.replace(/\s+/g, "_")}_${speaker.name.replace(/\s+/g, "_")}.png`;

  incrementDownloadCount(state.currentCertId);

  try {
    canvas.toBlob((blob) => {
      if (!blob) { showToast("Could not generate image — try PNG instead"); return; }
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.download = filename;
      a.href = url;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 3000);
      showToast("Certificate PNG downloaded! 📥");
    }, "image/png");
  } catch (e) {
    showToast("Download failed — open via http://localhost:8000");
    console.error("PNG download error:", e);
  }
}

// Download Print-Ready Landscape PDF (preserves canvas aspect ratio)
function downloadCertificatePdf(canvas) {
  const name = elements.participantName.value.trim() || "Participant";
  const filename = `Certificate_${name.replace(/\s+/g, "_")}.pdf`;

  incrementDownloadCount(state.currentCertId);

  try {
    const { jsPDF } = window.jspdf;
    // Use canvas aspect ratio so the certificate is never distorted
    const W_mm = 297;
    const H_mm = Math.round(W_mm * (canvas.height / canvas.width)); // ≈167mm for 1892×1064
    const pdf = new jsPDF({
      orientation: "landscape",
      unit: "mm",
      format: [W_mm, H_mm]   // custom page size matching canvas ratio
    });

    const imgData = canvas.toDataURL("image/jpeg", 0.95);
    pdf.addImage(imgData, "JPEG", 0, 0, W_mm, H_mm);
    pdf.save(filename);
    showToast("Certificate PDF downloaded! 📄");
  } catch (err) {
    console.error("PDF generation failed:", err);
    showToast("PDF failed — downloading PNG instead...");
    downloadCertificateImage(canvas, "png");
  }
}

async function incrementDownloadCount(certId) {
  const req = state.requests.find((r) => r.id === certId);
  if (req) {
    req.downloadCount = (req.downloadCount || 0) + 1;
    req.status = "Downloaded";
    await sbUpsertRequest(req);
  }
}

// Public Certificate Verification via Supabase
async function runVerification(certId) {
  elements.verifyResultBox.style.display = "block";
  elements.verifyResultBox.innerHTML = `
    <div style="text-align: center; color: var(--text-secondary); padding: 1rem;">
      🔍 Checking Supabase certificate database...
    </div>
  `;

  // Try Supabase first, then in-memory fallback
  let found = await sbVerify(certId.toUpperCase().trim());
  if (!found) found = state.requests.find((r) => r.id.toLowerCase() === certId.toLowerCase());

  if (found) {
    const speaker = ADMIN_CONFIG[found.speakerId] || { name: found.speakerName, gid: found.speakerGid };
    elements.verifyResultBox.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1rem; color: #137333;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <div>
          <div style="font-size: 1.15rem; font-weight: 700;">Certificate Verified ✓</div>
          <div style="font-size: 0.8rem; color: #137333;">Game On: Imagine the Impossible 2026 • Verified via Supabase ☁️</div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 140px 1fr; row-gap: 0.5rem; font-size: 0.9rem;">
        <span style="color: var(--text-muted); font-weight: 500;">Certificate ID:</span>
        <span style="font-weight: 700; font-family: monospace; color: #1a73e8;">${found.id}</span>

        <span style="color: var(--text-muted); font-weight: 500;">Participant:</span>
        <span style="font-weight: 700;">${escapeHtml(found.fullName)}</span>

        <span style="color: var(--text-muted); font-weight: 500;">Session Speaker:</span>
        <span><strong>${speaker.name}</strong> (GID: ${speaker.gid})</span>

        <span style="color: var(--text-muted); font-weight: 500;">Event:</span>
        <span>Game On: Imagine the Impossible</span>

        <span style="color: var(--text-muted); font-weight: 500;">Session Date:</span>
        <span>${found.eventDate || "08/10/2026"}</span>

        <span style="color: var(--text-muted); font-weight: 500;">Status:</span>
        <span style="color: #137333; font-weight: 600;">Authentic &amp; Valid</span>
      </div>

      <div style="margin-top: 1.25rem; display: flex; gap: 0.75rem;">
        <button class="nav-btn-primary" onclick="openPreviewModal('${found.id}')" style="border: none; padding: 0.5rem 1rem; border-radius: var(--radius-sm); cursor: pointer;">
          View Certificate
        </button>
      </div>
    `;
  } else {
    elements.verifyResultBox.innerHTML = `
      <div style="display: flex; align-items: center; gap: 0.75rem; color: #d93025;">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
        <div>
          <div style="font-size: 1.1rem; font-weight: 700;">Certificate Not Found</div>
          <div style="font-size: 0.82rem; color: #5f6368;">No certificate matching ID "${escapeHtml(certId)}" exists in the official Supabase registry.</div>
        </div>
      </div>
    `;
  }
}

// ========================================================
// ADMIN PORTAL & AUTHENTICATION
// ========================================================
function setupAdminListeners() {
  // Admin Login Submission
  elements.adminLoginForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const username = elements.adminUsernameInput.value.trim();
    const password = elements.adminPasswordInput.value.trim();

    const success = await attemptAdminLogin(username, password);
    if (success) {
      showToast(`Welcome back, ${state.currentAdmin.name}! 👋`);
      elements.adminUsernameInput.value = "";
      elements.adminPasswordInput.value = "";
      updateAdminView();
    } else {
      showToast("Invalid admin credentials! Please check username & password.");
    }
  });

  // Admin Logout
  const handleLogout = () => {
    state.currentAdmin = null;
    sessionStorage.removeItem("gsa_active_admin");
    elements.activeAdminPill.style.display = "none";
    updateAdminView();
    showToast("Logged out of Admin Portal");
  };

  elements.btnAdminLogout.addEventListener("click", handleLogout);
  elements.adminLogoutBtn.addEventListener("click", handleLogout);

  // Search filter
  elements.adminSearchInput.addEventListener("input", (e) => {
    state.activeFilters.search = e.target.value.toLowerCase().trim();
    renderRequestsTable();
  });

  // Filter Buttons
  document.querySelectorAll("[data-filter-speaker]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-filter-speaker]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeFilters.speaker = btn.getAttribute("data-filter-speaker");
      renderRequestsTable();
    });
  });

  document.querySelectorAll("[data-filter-status]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll("[data-filter-status]").forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.activeFilters.status = btn.getAttribute("data-filter-status");
      renderRequestsTable();
    });
  });

  // Export CSV
  elements.btnExportCsv.addEventListener("click", exportRequestsToCsv);
}

// Validate credentials
async function attemptAdminLogin(username, password) {
  // Check against our config (case insensitive username)
  const normalizedUser = username.toLowerCase();
  let matchedAdmin = null;

  for (const key in ADMIN_CONFIG) {
    const adm = ADMIN_CONFIG[key];
    const userMatches = adm.username.toLowerCase() === normalizedUser || 
                        (key === "admin3" && (normalizedUser === "thomas" || normalizedUser === "thomas pd" || normalizedUser === "thomas p d"));
    if (userMatches && adm.pass === password) {
      matchedAdmin = adm;
      break;
    }
  }

  if (matchedAdmin) {
    state.currentAdmin = matchedAdmin;
    sessionStorage.setItem("gsa_active_admin", JSON.stringify(matchedAdmin));
    return true;
  }
  return false;
}

function checkAdminSession() {
  const saved = sessionStorage.getItem("gsa_active_admin");
  if (saved) {
    try {
      state.currentAdmin = JSON.parse(saved);
      elements.activeAdminPill.style.display = "flex";
      elements.adminNameDisplay.textContent = state.currentAdmin.name;
      elements.adminAvatarInitial.textContent = state.currentAdmin.initial;
      elements.adminAvatarInitial.style.background = state.currentAdmin.color;
    } catch (e) {
      state.currentAdmin = null;
    }
  }
}

function updateAdminView() {
  if (state.currentAdmin) {
    elements.adminLoginSection.style.display = "none";
    elements.adminDashboardSection.style.display = "block";
    elements.activeAdminPill.style.display = "flex";
    elements.adminNameDisplay.textContent = state.currentAdmin.name;
    elements.adminAvatarInitial.textContent = state.currentAdmin.initial;
    elements.adminAvatarInitial.style.background = state.currentAdmin.color;

    // Update Quick Session Key Banner for logged-in admin
    const quickInput = document.getElementById("quickSessionKeyInput");
    const badge = document.getElementById("myAdminSpeakerBadge");
    if (quickInput) {
      quickInput.value = ADMIN_CONFIG[state.currentAdmin.id]?.sessionKey || "";
    }
    if (badge) {
      badge.textContent = state.currentAdmin.name;
      badge.style.background = state.currentAdmin.color || "#1a73e8";
    }

    // Reload fresh from Supabase each time admin opens dashboard
    loadRequests().then(() => {
      updateAdminStats();
      renderRequestsTable();
    });
  } else {
    elements.adminLoginSection.style.display = "block";
    elements.adminDashboardSection.style.display = "none";
    elements.activeAdminPill.style.display = "none";
  }
}

// Supabase connection status pill
function updateSupabaseStatusPill(connected) {
  const pill = document.getElementById("supabaseStatusPill");
  if (!pill) return;
  if (connected) {
    pill.style.display = "inline-flex";
    pill.title = "Connected to Supabase Cloud (sxbnutustirzmesuillx.supabase.co)";
    pill.querySelector(".status-text").textContent = "Supabase ☁️";
  } else {
    pill.style.background = "#fef3c7";
    pill.style.borderColor = "#fde68a";
    pill.style.color = "#92400e";
    pill.querySelector(".status-dot").style.background = "#f59e0b";
    pill.querySelector(".status-text").textContent = "Offline Mode";
  }
}

// Local fallback save (used if Supabase unreachable)
function saveLocalRequest(req) {
  state.requests.unshift(req);
  localStorage.setItem("gsa_cert_requests", JSON.stringify(state.requests));
}

// Load Requests from Supabase (with localStorage fallback)
async function loadRequests() {
  const rows = await sbLoadRequests();
  state.requests = rows;
  // keep local cache fresh
  localStorage.setItem("gsa_cert_requests", JSON.stringify(rows));
  updateSupabaseStatusPill(true);
}

// Update Admin Dashboard Stats
function updateAdminStats() {
  const total = state.requests.length;
  let myCount = 0;
  let pendingCount = 0;
  let downloadedCount = 0;

  state.requests.forEach((r) => {
    if (state.currentAdmin && r.speakerId === state.currentAdmin.id) {
      myCount++;
    }
    if (r.status === "Requested") {
      pendingCount++;
    }
    downloadedCount += (r.downloadCount || 0);
  });

  elements.statTotalRequests.textContent = total;
  elements.statMyRequests.textContent = myCount;
  elements.statPendingRequests.textContent = pendingCount;
  elements.statDownloadedCount.textContent = downloadedCount;
}

// Render Requests Table with Filters
function renderRequestsTable() {
  const tbody = elements.requestsTableBody;
  tbody.innerHTML = "";

  const filtered = state.requests.filter((r) => {
    // Speaker filter
    if (state.activeFilters.speaker === "mine") {
      if (!state.currentAdmin || r.speakerId !== state.currentAdmin.id) return false;
    } else if (state.activeFilters.speaker !== "all") {
      if (r.speakerId !== state.activeFilters.speaker) return false;
    }

    // Status filter
    if (state.activeFilters.status !== "all") {
      if (r.status !== state.activeFilters.status) return false;
    }

    // Search filter
    if (state.activeFilters.search) {
      const term = state.activeFilters.search;
      const match =
        r.fullName.toLowerCase().includes(term) ||
        (r.email && r.email.toLowerCase().includes(term)) ||
        (r.college && r.college.toLowerCase().includes(term)) ||
        r.id.toLowerCase().includes(term);
      if (!match) return false;
    }

    return true;
  });

  elements.requestCountLabel.textContent = `Showing ${filtered.length} of ${state.requests.length} requests`;

  if (filtered.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; padding: 2rem; color: var(--text-muted);">
          No certificate requests found matching your filter criteria.
        </td>
      </tr>
    `;
    return;
  }

  filtered.forEach((r) => {
    const speaker = ADMIN_CONFIG[r.speakerId] || { name: r.speakerName, gid: r.speakerGid, initial: "A" };
    const tr = document.createElement("tr");

    const statusClass = (r.status || "requested").toLowerCase();

    tr.innerHTML = `
      <td><span style="font-family: monospace; font-weight: 700; color: #1a73e8;">${r.id}</span></td>
      <td>
        <div class="user-name-cell">${escapeHtml(r.fullName)}</div>
        <div class="user-email-cell">${escapeHtml(r.email || "No email provided")}</div>
      </td>
      <td>${escapeHtml(r.college || "N/A")}</td>
      <td>
        <div style="display: flex; align-items: center; gap: 0.4rem;">
          <span style="font-weight: 600;">${speaker.name}</span>
          <span class="speaker-gid-tag" style="margin: 0;">GID: ${speaker.gid}</span>
        </div>
      </td>
      <td style="color: var(--text-secondary); font-size: 0.85rem;">${r.requestDate || "N/A"}</td>
      <td>
        <span class="status-badge ${statusClass}">${r.status || "Requested"}</span>
      </td>
      <td style="text-align: center; font-weight: 600;">${r.downloadCount || 0}</td>
      <td>
        <button class="table-action-btn" title="View Certificate" onclick="openPreviewModal('${r.id}')">
          View
        </button>
        <button class="table-action-btn email" title="Resend Certificate via Email" onclick="resendRequestEmail('${r.id}')">
          Resend ✉️
        </button>
        <button class="table-action-btn" title="Approve Request" onclick="toggleRequestStatus('${r.id}')">
          ${r.status === "Approved" ? "Unapprove" : "Approve"}
        </button>
        <button class="table-action-btn delete" title="Delete" onclick="deleteRequest('${r.id}')">
          Delete
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

// Admin Action: Toggle Status — syncs to Supabase
window.toggleRequestStatus = async function (id) {
  const req = state.requests.find((r) => r.id === id);
  if (!req) return;

  req.status = req.status === "Approved" ? "Requested" : "Approved";
  await sbUpsertRequest(req);

  updateAdminStats();
  renderRequestsTable();
  showToast(`Request ${id} marked as ${req.status} ☁️`);
};

// Admin Action: Delete Request — removes from Supabase
window.deleteRequest = async function (id) {
  if (!confirm(`Are you sure you want to delete certificate request ${id}?`)) return;

  state.requests = state.requests.filter((r) => r.id !== id);
  await sbDeleteRequest(id);

  updateAdminStats();
  renderRequestsTable();
  showToast(`Certificate request ${id} deleted from Supabase 🗑️`);
};

// Export Requests to CSV
function exportRequestsToCsv() {
  if (state.requests.length === 0) {
    showToast("No requests to export!");
    return;
  }

  const headers = ["Certificate ID", "Full Name", "Email", "College", "Speaker Admin", "Speaker GID", "Event Date", "Request Date", "Status", "Download Count"];
  const rows = state.requests.map((r) => [
    `"${r.id}"`,
    `"${(r.fullName || "").replace(/"/g, '""')}"`,
    `"${(r.email || "").replace(/"/g, '""')}"`,
    `"${(r.college || "").replace(/"/g, '""')}"`,
    `"${(r.speakerName || "").replace(/"/g, '""')}"`,
    `"${r.speakerGid || ""}"`,
    `"${r.eventDate || ""}"`,
    `"${r.requestDate || ""}"`,
    `"${r.status || ""}"`,
    r.downloadCount || 0
  ]);

  const csvContent = [headers.join(","), ...rows.map((row) => row.join(","))].join("\r\n");
  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `Certificate_Requests_GSA_2026_${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  showToast("Requests exported to CSV! 📊");
}

// ========================================================
// MODAL FOR CERTIFICATE PREVIEW
// ========================================================
function setupModal() {
  elements.modalCloseBtn.addEventListener("click", () => {
    elements.previewModal.classList.remove("active");
  });

  elements.previewModal.addEventListener("click", (e) => {
    if (e.target === elements.previewModal) {
      elements.previewModal.classList.remove("active");
    }
  });

  elements.modalDownloadPngBtn.addEventListener("click", () => {
    downloadCertificateImage(elements.modalCanvas, "png");
  });

  elements.modalDownloadPdfBtn.addEventListener("click", () => {
    downloadCertificatePdf(elements.modalCanvas);
  });
}

window.openPreviewModal = function (certId) {
  const req = state.requests.find((r) => r.id === certId);
  if (!req) return;

  elements.modalCertSub.textContent = `Certificate for ${req.fullName} • Speaker: ${req.speakerName} (GID: ${req.speakerGid})`;
  renderCertificate(elements.modalCanvas, req);
  elements.previewModal.classList.add("active");
};

// Utility function to escape HTML
function escapeHtml(text) {
  if (!text) return "";
  return text.replace(/[&<>"']/g, function (m) {
    switch (m) {
      case "&": return "&amp;";
      case "<": return "&lt;";
      case ">": return "&gt;";
      case '"': return "&quot;";
      case "'": return "&#039;";
    }
  });
}

// --- Admin Portal GID, Signature, Template & Test Email Handlers ---

// Sync custom GIDs and signatures from backend server upon loading
async function syncAdminSettingsFromServer() {
  try {
    const apiUrl = getBackendApiUrl("/api/admin/settings");
    const resp = await fetch(apiUrl);
    if (resp.ok) {
      const data = await resp.json();
      if (data.admins) {
        for (const k in data.admins) {
          if (ADMIN_CONFIG[k]) {
            if (data.admins[k].gid) ADMIN_CONFIG[k].gid = data.admins[k].gid;
            if (data.admins[k].signatureFile) ADMIN_CONFIG[k].signatureFile = data.admins[k].signatureFile;
            if (data.admins[k].email) ADMIN_CONFIG[k].email = data.admins[k].email;
            if (data.admins[k].sessionKey) ADMIN_CONFIG[k].sessionKey = data.admins[k].sessionKey;

            const gidInput = document.getElementById(`adminGidInput_${k}`);
            if (gidInput) gidInput.value = ADMIN_CONFIG[k].gid;

            const sessionKeyInput = document.getElementById(`adminSessionKeyInput_${k}`);
            if (sessionKeyInput) sessionKeyInput.value = ADMIN_CONFIG[k].sessionKey;

            const sigFilename = document.getElementById(`sigFilename_${k}`);
            if (sigFilename) sigFilename.textContent = ADMIN_CONFIG[k].signatureFile;

            const preview = document.getElementById(`adminSigPreview_${k}`);
            if (preview && ADMIN_CONFIG[k].signatureFile) preview.src = ADMIN_CONFIG[k].signatureFile;

            const cardTag = document.querySelector(`#cardSpeaker${k.charAt(0).toUpperCase() + k.slice(1)} .speaker-gid-tag`);
            if (cardTag) cardTag.textContent = `GID: ${ADMIN_CONFIG[k].gid}`;
          }
        }
        try {
          const currentKeys = JSON.parse(localStorage.getItem("gsa_speaker_keys") || "{}");
          for (const sp in ADMIN_CONFIG) {
            if (ADMIN_CONFIG[sp]?.sessionKey) currentKeys[sp] = ADMIN_CONFIG[sp].sessionKey;
          }
          localStorage.setItem("gsa_speaker_keys", JSON.stringify(currentKeys));
        } catch (e) {}
        validateSessionKeyUI();
        renderCertificate();
      }
    }
  } catch (err) {
    // Server offline or starting up
  }
}

// 1. Update GID for an Ambassador
window.handleSaveGid = async function (speakerId) {
  const input = document.getElementById(`adminGidInput_${speakerId}`);
  if (!input) return;
  const newGid = input.value.trim();
  if (!newGid) {
    showToast("Please enter a valid GID number");
    return;
  }

  try {
    const apiUrl = getBackendApiUrl("/api/admin/update-speaker");
    const resp = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speakerId, gid: newGid })
    });

    if (resp.ok) {
      if (ADMIN_CONFIG[speakerId]) ADMIN_CONFIG[speakerId].gid = newGid;

      const cardTag = document.querySelector(`#cardSpeaker${speakerId.charAt(0).toUpperCase() + speakerId.slice(1)} .speaker-gid-tag`);
      if (cardTag) cardTag.textContent = `GID: ${newGid}`;

      renderCertificate();
      showToast(`GID updated to ${newGid} for ${ADMIN_CONFIG[speakerId]?.name || speakerId} ✅`);
    } else {
      const err = await resp.json();
      showToast(`Could not update GID: ${err.message || 'Server error'}`);
    }
  } catch (err) {
    if (ADMIN_CONFIG[speakerId]) ADMIN_CONFIG[speakerId].gid = newGid;
    renderCertificate();
    showToast(`GID updated to ${newGid} (Client cached)`);
  }
};

// 2. Update Session Key for an Ambassador
window.handleSaveSessionKey = async function (speakerId, overrideKey = null) {
  const input = document.getElementById(`adminSessionKeyInput_${speakerId}`);
  const quickInput = document.getElementById("quickSessionKeyInput");
  const newKey = (overrideKey !== null ? overrideKey : (input ? input.value : "")).trim().toUpperCase();
  if (!newKey) {
    showToast("Please enter a valid session key (e.g. GSA-ASWIN-2026)");
    return;
  }

  // 1. Immediately update memory and UI state
  if (ADMIN_CONFIG[speakerId]) ADMIN_CONFIG[speakerId].sessionKey = newKey;
  if (input) input.value = newKey;
  if (quickInput && state.currentAdmin && state.currentAdmin.id === speakerId) {
    quickInput.value = newKey;
  }
  validateSessionKeyUI();

  // 2. Persist to Supabase Cloud Database so it remains the same permanently across all devices & serverless instances
  const currentKeys = {
    admin1: ADMIN_CONFIG.admin1.sessionKey,
    admin2: ADMIN_CONFIG.admin2.sessionKey,
    admin3: ADMIN_CONFIG.admin3.sessionKey,
    [speakerId]: newKey
  };
  await sbSaveSpeakerKeys(currentKeys);

  // 3. Persist to local browser storage
  try {
    localStorage.setItem("gsa_speaker_keys", JSON.stringify(currentKeys));
  } catch (e) {}

  // 4. Sync with Backend API
  try {
    const apiUrl = getBackendApiUrl("/api/admin/update-speaker");
    const resp = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speakerId, sessionKey: newKey })
    });

    if (resp.ok) {
      showToast(`Session Key updated to "${newKey}" for ${ADMIN_CONFIG[speakerId]?.name || speakerId} 🔑✅`);
    } else {
      showToast(`Session Key saved to Supabase Cloud! ("${newKey}") ☁️✅`);
    }
  } catch (err) {
    showToast(`Session Key saved to Cloud & Local Storage! ("${newKey}") ☁️✅`);
  }
};

// Quick-Save Session Key from Top Admin Banner
window.handleQuickSaveSessionKey = async function () {
  if (!state.currentAdmin) {
    showToast("Please log in to set your session key");
    return;
  }
  const input = document.getElementById("quickSessionKeyInput");
  if (!input) return;
  const newKey = input.value.trim().toUpperCase();
  if (!newKey) {
    showToast("Please enter a valid session key");
    return;
  }
  await window.handleSaveSessionKey(state.currentAdmin.id, newKey);
};

// Generate Random Key for Logged-In Admin
window.handleGenerateRandomKey = function () {
  if (!state.currentAdmin) return;
  const firstName = (state.currentAdmin.name.split(" ")[0] || "GSA").toUpperCase();
  const randomNum = Math.floor(1000 + Math.random() * 9000);
  const generated = `${firstName}-${randomNum}`;
  const input = document.getElementById("quickSessionKeyInput");
  if (input) input.value = generated;
  showToast(`🎲 Generated key "${generated}". Click "Save Key 💾" to activate!`);
};

// Copy Logged-In Admin's Key to Clipboard
window.handleCopyMyKey = function () {
  if (!state.currentAdmin) return;
  const key = ADMIN_CONFIG[state.currentAdmin.id]?.sessionKey || document.getElementById("quickSessionKeyInput")?.value || "";
  if (!key) {
    showToast("No active key to copy");
    return;
  }
  navigator.clipboard.writeText(key).then(() => {
    showToast(`📋 Copied your session key "${key}" to clipboard! Distribute this to your attendees.`);
  }).catch(() => {
    showToast(`Your session key: ${key}`);
  });
};

// 3. Copy Session Key to Clipboard
window.copySessionKeyToClipboard = function (speakerId) {
  const key = ADMIN_CONFIG[speakerId]?.sessionKey || document.getElementById(`adminSessionKeyInput_${speakerId}`)?.value || "";
  if (!key) return;
  navigator.clipboard.writeText(key).then(() => {
    showToast(`📋 Copied session key "${key}" to clipboard! Share it with your session attendees.`);
  }).catch(() => {
    showToast(`Session key: ${key}`);
  });
};

// 4. Upload New Signature for an Ambassador
window.handleSignatureUpload = async function (speakerId) {
  const fileInput = document.getElementById(`sigFileInput_${speakerId}`);
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  if (!file.type.startsWith("image/")) {
    showToast("Please select an image file (.png, .jpg, .jpeg)");
    return;
  }

  showToast(`Uploading signature for ${ADMIN_CONFIG[speakerId]?.name || speakerId}... ⏳`);

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64Data = e.target.result;
    try {
      const apiUrl = getBackendApiUrl("/api/admin/upload-signature");
      const resp = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          speakerId,
          filename: file.name,
          imageData: base64Data
        })
      });

      if (resp.ok) {
        const data = await resp.json();
        const savedFilename = data.signatureFile;

        if (ADMIN_CONFIG[speakerId]) {
          ADMIN_CONFIG[speakerId].signatureFile = savedFilename;
        }

        const previewImg = document.getElementById(`adminSigPreview_${speakerId}`);
        if (previewImg) previewImg.src = base64Data;
        const filenameLabel = document.getElementById(`sigFilename_${speakerId}`);
        if (filenameLabel) filenameLabel.textContent = savedFilename;

        const img = new Image();
        img.onload = () => {
          state.loadedImages[`${speakerId}Sig`] = img;
          renderCertificate();
          showToast(`Signature uploaded and applied for ${ADMIN_CONFIG[speakerId]?.name || speakerId} 🖋️`);
        };
        img.src = base64Data;
      } else {
        const err = await resp.json();
        showToast(`Signature upload failed: ${err.message || 'Server error'}`);
      }
    } catch (err) {
      console.warn("Upload API error, using client base64:", err);
      const img = new Image();
      img.onload = () => {
        state.loadedImages[`${speakerId}Sig`] = img;
        renderCertificate();
        showToast(`Signature applied to live certificate!`);
      };
      img.src = base64Data;
      const previewImg = document.getElementById(`adminSigPreview_${speakerId}`);
      if (previewImg) previewImg.src = base64Data;
    }
  };
  reader.readAsDataURL(file);
};

// 3. Upload New Certificate Template
window.handleTemplateUpload = async function () {
  const fileInput = document.getElementById("templateFileInput");
  if (!fileInput || !fileInput.files || fileInput.files.length === 0) return;

  const file = fileInput.files[0];
  if (!file.type.startsWith("image/")) {
    showToast("Please select a valid image file for the template");
    return;
  }

  showToast("Uploading new master certificate template... ⏳");

  const reader = new FileReader();
  reader.onload = async (e) => {
    const base64Data = e.target.result;
    try {
      const apiUrl = getBackendApiUrl("/api/admin/upload-template");
      const resp = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filename: file.name,
          imageData: base64Data
        })
      });

      if (resp.ok) {
        const thumb = document.getElementById("adminTemplateThumb");
        if (thumb) thumb.src = base64Data;

        const img = new Image();
        img.onload = () => {
          state.loadedImages.template = img;
          renderCertificate();
          showToast("Master certificate template updated and applied! 🖼️");
        };
        img.src = base64Data;
      } else {
        const err = await resp.json();
        showToast(`Template upload error: ${err.message || 'Server error'}`);
      }
    } catch (err) {
      console.warn("Template upload failed, applying locally:", err);
      const img = new Image();
      img.onload = () => {
        state.loadedImages.template = img;
        renderCertificate();
        showToast("Template applied to live canvas (Local Preview)!");
      };
      img.src = base64Data;
    }
  };
  reader.readAsDataURL(file);
};

// 4. Resend Certificate Email
window.resendRequestEmail = async function (certId) {
  const req = state.requests.find((r) => r.id === certId);
  if (!req) return;

  const targetEmail = req.email || prompt("Enter recipient email address:", "");
  if (!targetEmail || !targetEmail.includes("@")) {
    showToast("Valid recipient email is required");
    return;
  }

  showToast(`Resending certificate ${certId} to ${targetEmail}... ✉️`);

  try {
    const apiUrl = getBackendApiUrl("/api/admin/resend-email");
    const resp = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ certId, email: targetEmail })
    });

    if (resp.ok) {
      const result = await resp.json();
      if (result.smtpSent) {
        req.status = "Email Sent";
        await sbUpsertRequest(req);
        renderRequestsTable();
        showToast(`Certificate ${certId} sent successfully via ${result.sender} ✉️`);
      } else {
        showToast(`Email could not be delivered: ${result.error || 'Server error'}`, 6000);
      }
    } else {
      const err = await resp.json();
      showToast(`Resend failed: ${err.message || 'Server error'}`);
    }
  } catch (err) {
    showToast("Backend server offline. Please run start_portal.bat ⚠️", 6000);
  }
};

// 5. Send Diagnostic Test Email from an Ambassador's account
window.handleTestEmail = async function (speakerId) {
  const adm = ADMIN_CONFIG[speakerId] || ADMIN_CONFIG.admin1;
  const defaultRecipient = adm.email || "aswinashokkv@gmail.com";
  const toEmail = prompt(`Send diagnostic test email from ${adm.name} (${adm.email}) to:`, defaultRecipient);
  if (!toEmail || !toEmail.includes("@")) return;

  showToast(`Sending test delivery from ${adm.name} via ${adm.email}... ⏳`);

  try {
    const apiUrl = getBackendApiUrl("/api/admin/test-email");
    const resp = await fetch(apiUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ speakerId, toEmail })
    });

    if (resp.ok) {
      const res = await resp.json();
      if (res.smtpSent) {
        showToast(`Diagnostic email successfully sent from ${res.sender} to ${toEmail}! ✉️`);
      } else {
        showToast(`SMTP test failed: ${res.error || 'Authentication error'}`, 7000);
      }
    } else {
      const err = await resp.json();
      showToast(`Test failed: ${err.message || 'Server error'}`);
    }
  } catch (err) {
    showToast("Server offline: ensure start_portal.bat is running on port 8000 ⚠️", 6000);
  }
};

// Call sync on startup
setTimeout(syncAdminSettingsFromServer, 1000);

