/* ═══════════════════════════════════════════════════════════════
   Frontend Logic — Secure Auth System
   ═══════════════════════════════════════════════════════════════ */

// ── Helpers ────────────────────────────────────────────────────
function showAlert(id, msg, type = "error") {
  const el = document.getElementById(id);
  if (!el) return;
  el.className = `alert show alert-${type}`;
  el.innerHTML = `<span>${type === "error" ? "⚠️" : "✅"}</span> ${msg}`;
  if (type === "success") setTimeout(() => (el.className = "alert"), 5000);
}

function hideAlert(id) {
  const el = document.getElementById(id);
  if (el) el.className = "alert";
}

function setLoading(btn, loading) {
  if (loading) {
    btn.classList.add("loading");
    btn.disabled = true;
  } else {
    btn.classList.remove("loading");
    btn.disabled = false;
  }
}

async function api(url, data) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
    credentials: "same-origin",
  });
  const json = await res.json();
  return { ok: res.ok, status: res.status, data: json };
}

// ── Password strength meter ───────────────────────────────────
function checkStrength(pw) {
  let score = 0;
  if (pw.length >= 8) score++;
  if (/[A-Z]/.test(pw) && /[a-z]/.test(pw)) score++;
  if (/\d/.test(pw)) score++;
  if (/[!@#$%^&*()\-_=+\[\]{}|;:',.<>?\/`~]/.test(pw)) score++;
  if (pw.length >= 12) score++;
  if (score <= 2) return "weak";
  if (score <= 3) return "medium";
  return "strong";
}

function bindPasswordStrength(inputId, barId) {
  const input = document.getElementById(inputId);
  const bar = document.getElementById(barId);
  if (!input || !bar) return;
  input.addEventListener("input", () => {
    const s = checkStrength(input.value);
    bar.className = `bar ${input.value ? s : ""}`;
  });
}

// ── Password visibility toggle ────────────────────────────────
function bindPasswordToggle(toggleId, inputId) {
  const toggle = document.getElementById(toggleId);
  const input = document.getElementById(inputId);
  if (!toggle || !input) return;
  toggle.addEventListener("click", () => {
    const isPassword = input.type === "password";
    input.type = isPassword ? "text" : "password";
    toggle.textContent = isPassword ? "🙈" : "👁️";
  });
}

// ── Register ──────────────────────────────────────────────────
function initRegister() {
  const form = document.getElementById("register-form");
  if (!form) return;

  bindPasswordStrength("reg-password", "reg-pw-bar");
  bindPasswordToggle("toggle-reg-pw", "reg-password");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert("reg-alert");
    const btn = form.querySelector("button[type=submit]");
    setLoading(btn, true);

    const { ok, data } = await api("/api/register", {
      full_name: document.getElementById("reg-fullname").value,
      username: document.getElementById("reg-username").value,
      email: document.getElementById("reg-email").value,
      password: document.getElementById("reg-password").value,
    });

    setLoading(btn, false);
    if (ok) {
      showAlert("reg-alert", data.message + " Redirecting...", "success");
      setTimeout(() => (window.location.href = "/login"), 1500);
    } else {
      showAlert("reg-alert", data.error || "Registration failed.");
    }
  });
}

// ── Login ─────────────────────────────────────────────────────
function initLogin() {
  const form = document.getElementById("login-form");
  if (!form) return;

  bindPasswordToggle("toggle-login-pw", "login-password");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert("login-alert");
    const btn = form.querySelector("button[type=submit]");
    setLoading(btn, true);

    const { ok, data } = await api("/api/login", {
      username: document.getElementById("login-username").value,
      password: document.getElementById("login-password").value,
    });

    setLoading(btn, false);
    if (ok) {
      showAlert("login-alert", "Login successful! Redirecting...", "success");
      setTimeout(() => (window.location.href = "/dashboard"), 1000);
    } else {
      showAlert("login-alert", data.error || "Login failed.");
    }
  });
}

// ── Dashboard actions ─────────────────────────────────────────
function initDashboard() {
  // Logout
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await api("/api/logout", {});
      window.location.href = "/login";
    });
  }
}

// ── Sessions page ─────────────────────────────────────────────
function initSessions() {
  // Revoke single session
  document.querySelectorAll(".btn-revoke").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const sid = btn.dataset.id;
      const { ok, data } = await api(`/api/revoke-session/${sid}`, {});
      if (ok) location.reload();
      else alert(data.error || "Failed to revoke.");
    });
  });

  // Revoke all
  const revokeAllBtn = document.getElementById("btn-revoke-all");
  if (revokeAllBtn) {
    revokeAllBtn.addEventListener("click", async () => {
      if (!confirm("Revoke all other sessions? You will remain logged in."))
        return;
      const { ok } = await api("/api/revoke-all", {});
      if (ok) location.reload();
    });
  }

  // Logout
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await api("/api/logout", {});
      window.location.href = "/login";
    });
  }
}

// ── Change Password ───────────────────────────────────────────
function initChangePassword() {
  const form = document.getElementById("change-pw-form");
  if (!form) return;

  bindPasswordStrength("new-password", "new-pw-bar");
  bindPasswordToggle("toggle-new-pw", "new-password");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    hideAlert("pw-alert");
    const btn = form.querySelector("button[type=submit]");
    setLoading(btn, true);

    const { ok, data } = await api("/api/change-password", {
      current_password: document.getElementById("current-password").value,
      new_password: document.getElementById("new-password").value,
    });

    setLoading(btn, false);
    if (ok) {
      showAlert("pw-alert", data.message, "success");
      form.reset();
    } else {
      showAlert("pw-alert", data.error || "Failed to change password.");
    }
  });

  // Logout button on change-password page
  const logoutBtn = document.getElementById("btn-logout");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      await api("/api/logout", {});
      window.location.href = "/login";
    });
  }
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  initRegister();
  initLogin();
  initDashboard();
  initSessions();
  initChangePassword();
});
