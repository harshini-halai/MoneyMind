// Light/dark theme. Load this in <head> so the right theme is set before the page paints.

(function () {
  var theme = null;
  try {
    theme = localStorage.getItem("moneymind_theme");
  } catch (error) {
    theme = null;
  }
  if (theme !== "light" && theme !== "dark") {
    theme =
      window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches
        ? "dark"
        : "light";
  }
  document.documentElement.setAttribute("data-theme", theme);
})();

function currentTheme() {
  return document.documentElement.getAttribute("data-theme") === "dark"
    ? "dark"
    : "light";
}

function toggleTheme() {
  const next = currentTheme() === "dark" ? "light" : "dark";
  document.documentElement.setAttribute("data-theme", next);
  try {
    localStorage.setItem("moneymind_theme", next);
  } catch (error) {
    /* ignore */
  }
  document.dispatchEvent(new CustomEvent("themechange", { detail: next }));
}

// Site icons (favicon, phone home-screen icon, address-bar colour).
// Added here because every page already loads this file in <head>.
(function () {
  function addTag(tag, attributes) {
    var element = document.createElement(tag);
    Object.keys(attributes).forEach(function (name) {
      element.setAttribute(name, attributes[name]);
    });
    document.head.appendChild(element);
  }
  addTag("link", { rel: "icon", href: "/favicon.ico", sizes: "48x48" });
  addTag("link", {
    rel: "icon",
    href: "/frontend/favicon.svg",
    type: "image/svg+xml",
    sizes: "any",
  });
  addTag("link", {
    rel: "apple-touch-icon",
    href: "/frontend/apple-touch-icon.png",
  });
  addTag("link", { rel: "manifest", href: "/frontend/site.webmanifest" });
  addTag("meta", { name: "theme-color", content: "#0f2338" });
})();

// Demo banner: shown only while the demo account's own token is in use.
document.addEventListener("DOMContentLoaded", function () {
  var token = null;
  var demoToken = null;
  try {
    token = localStorage.getItem("moneymind_token");
    demoToken = localStorage.getItem("moneymind_demo");
  } catch (error) {
    return;
  }

  var main = document.querySelector("main.content");
  if (!main || !token || token !== demoToken) {
    return;
  }

  var banner = document.createElement("div");
  banner.className = "demo-banner";

  var text = document.createElement("span");
  text.textContent =
    "You are viewing a demo with sample data. It is deleted after 24 hours.";

  var button = document.createElement("button");
  button.type = "button";
  button.className = "demo-banner-button";
  button.textContent = "Create your free account";
  button.addEventListener("click", function () {
    try {
      localStorage.removeItem("moneymind_token");
      localStorage.removeItem("moneymind_demo");
    } catch (error) {
      /* ignore */
    }
    window.location.href = "/register";
  });

  banner.appendChild(text);
  banner.appendChild(button);
  main.insertBefore(banner, main.firstChild);
});
