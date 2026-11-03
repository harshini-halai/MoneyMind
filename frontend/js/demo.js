// "Try the demo" button on the login and register pages.
// Asks the server for a throw-away account with sample data, then opens the dashboard.

document.addEventListener("DOMContentLoaded", function () {
  const button = document.getElementById("demo-button");
  if (!button) {
    return;
  }

  const label = button.textContent;

  button.addEventListener("click", async function () {
    showMessage("auth-message", "");
    button.disabled = true;
    button.textContent = "Setting up your demo...";

    try {
      const result = await apiFetch("/demo/start", { method: "POST", public: true });

      if (result.ok && result.data && result.data.access_token) {
        setToken(result.data.access_token);
        try {
          // Remember which token is the demo one, so the demo banner shows only for it.
          localStorage.setItem("moneymind_demo", result.data.access_token);
        } catch (error) {
          /* ignore */
        }
        window.location.href = "/";
        return;
      }

      showMessage(
        "auth-message",
        errorMessage(result.data, "Could not start the demo. Please try again."),
        "error",
      );
    } catch (error) {
      showMessage("auth-message", "Could not start the demo. Please try again.", "error");
    }

    button.disabled = false;
    button.textContent = label;
  });
});