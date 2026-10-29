// Login and register pages.

async function loginRequest(email, password) {
  const result = await apiFetch("/login", {
    method: "POST",
    public: true,
    body: JSON.stringify({ email: email, password: password }),
  });

  if (!result.ok) {
    throw new Error(errorMessage(result.data, "Unable to log in"));
  }

  setToken(result.data.access_token);
}

document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");

  if (loginForm) {
    loginForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const button = loginForm.querySelector('button[type="submit"]');
      showMessage("auth-message", "");
      button.disabled = true;

      try {
        await loginRequest(
          document.getElementById("login-email").value.trim(),
          document.getElementById("login-password").value,
        );
        window.location.href = "/";
      } catch (error) {
        showMessage("auth-message", error.message, "error");
        button.disabled = false;
      }
    });
  }

  if (registerForm) {
    registerForm.addEventListener("submit", async function (event) {
      event.preventDefault();
      const button = registerForm.querySelector('button[type="submit"]');
      showMessage("auth-message", "");

      const name = document.getElementById("register-name").value.trim();
      const email = document.getElementById("register-email").value.trim();
      const password = document.getElementById("register-password").value;
      const confirm = document.getElementById("register-confirm").value;

      if (password !== confirm) {
        showMessage("auth-message", "Passwords do not match", "error");
        return;
      }

      button.disabled = true;

      try {
        const result = await apiFetch("/register", {
          method: "POST",
          public: true,
          body: JSON.stringify({
            name: name,
            email: email,
            password: password,
          }),
        });

        if (!result.ok) {
          showMessage(
            "auth-message",
            errorMessage(result.data, "Unable to create account"),
            "error",
          );
          button.disabled = false;
          return;
        }

        await loginRequest(email, password);
        window.location.href = "/";
      } catch (error) {
        showMessage("auth-message", error.message, "error");
        button.disabled = false;
      }
    });
  }
});
