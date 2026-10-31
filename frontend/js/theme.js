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
