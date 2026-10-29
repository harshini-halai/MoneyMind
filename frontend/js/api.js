// Shared helpers used by every page. Load this BEFORE any other MoneyMind script.

const TOKEN_KEY = "moneymind_token";
const FLASH_KEY = "moneymind_flash";

// ---------- token handling ----------

function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch (error) {
    return null;
  }
}

function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

function clearToken() {
  try {
    localStorage.removeItem(TOKEN_KEY);
  } catch (error) {
    /* ignore */
  }
}

function logout() {
  clearToken();
  window.location.replace("/login");
}

// ---------- API calls ----------

// Wrapper around fetch(): uses relative URLs, attaches the JWT, and sends the
// user to /login when the session is missing or expired.
// Pass { public: true } for endpoints that need no token (login/register).
async function apiFetch(path, options = {}) {
  const { public: isPublic = false, ...fetchOptions } = options;
  const headers = { ...(fetchOptions.headers || {}) };

  const isFormData =
    typeof FormData !== "undefined" && fetchOptions.body instanceof FormData;
  if (fetchOptions.body && !isFormData && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  if (!isPublic) {
    const token = getToken();
    if (!token) {
      window.location.replace("/login");
      throw new Error("Not logged in");
    }
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(path, { ...fetchOptions, headers });

  if (response.status === 401 && !isPublic) {
    clearToken();
    window.location.replace("/login");
    throw new Error("Session expired");
  }

  let data = null;
  try {
    data = await response.json();
  } catch (error) {
    data = null;
  }

  return { ok: response.ok, status: response.status, data };
}

// FastAPI returns `detail` as a string for our errors, or a list for
// validation errors (422). Turn either into readable text.
function errorMessage(data, fallback) {
  if (!data || !data.detail) {
    return fallback;
  }
  if (typeof data.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data.detail)) {
    return data.detail
      .map(function (item) {
        const field = Array.isArray(item.loc)
          ? item.loc.slice(1).join(".")
          : "";
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join("; ");
  }
  return fallback;
}

// ---------- display helpers ----------

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

const rupeeFormatter = new Intl.NumberFormat("en-IN", {
  style: "currency",
  currency: "INR",
});

function formatMoney(value) {
  return rupeeFormatter.format(Number(value) || 0);
}

function formatMonth(isoDate) {
  const parts = String(isoDate).split("-");
  const date = new Date(Number(parts[0]), Number(parts[1]) - 1, 1);
  return date.toLocaleDateString("en-IN", { month: "short", year: "numeric" });
}

function todayISO() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function setDefaultDate(inputId) {
  const input = document.getElementById(inputId);
  if (input && !input.value) {
    input.value = todayISO();
  }
}

function setText(id, text) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = text;
  }
}

// Show (or hide, when text is empty) a message box. `type` is "error" or "success".
function showMessage(target, text, type) {
  const element =
    typeof target === "string" ? document.getElementById(target) : target;
  if (!element) {
    return;
  }
  element.textContent = text || "";
  element.className = `message ${type || "error"}`;
  element.hidden = !text;
}

// Remember a one-time message, then navigate; the next page shows it.
function flashAndGo(text, url) {
  try {
    sessionStorage.setItem(FLASH_KEY, text);
  } catch (error) {
    /* ignore */
  }
  window.location.href = url;
}

function showFlash() {
  const element = document.getElementById("flash-message");
  if (!element) {
    return;
  }
  let text = null;
  try {
    text = sessionStorage.getItem(FLASH_KEY);
    sessionStorage.removeItem(FLASH_KEY);
  } catch (error) {
    text = null;
  }
  if (text) {
    showMessage(element, text, "success");
  }
}

// ---------- shared form wiring ----------

// Most forms do the same thing: build a JSON payload, POST it, go to the
// dashboard on success, show an error message on failure.
function bindSimpleForm(config) {
  const form = document.getElementById(config.formId);
  if (!form) {
    return;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    const message = document.getElementById(config.messageId);
    const submitButton = form.querySelector('button[type="submit"]');
    showMessage(message, "");

    if (submitButton) {
      submitButton.disabled = true;
    }

    try {
      const result = await apiFetch(config.endpoint, {
        method: "POST",
        body: JSON.stringify(config.buildPayload()),
      });

      if (result.ok) {
        flashAndGo(config.successText, "/");
        return;
      }

      showMessage(message, errorMessage(result.data, config.failText), "error");
    } catch (error) {
      showMessage(message, config.failText, "error");
    }

    if (submitButton) {
      submitButton.disabled = false;
    }
  });
}

// ---------- page setup ----------

document.addEventListener("DOMContentLoaded", function () {
  const mode = document.body.dataset.auth;

  if (mode === "guest" && getToken()) {
    window.location.replace("/");
    return;
  }

  const logoutButton = document.getElementById("logout-button");
  if (logoutButton) {
    logoutButton.addEventListener("click", logout);
  }

  showFlash();
});

// Protected pages: redirect immediately if there is no token.
if (document.body && document.body.dataset.auth === "required" && !getToken()) {
  window.location.replace("/login");
}
