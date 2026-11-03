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
