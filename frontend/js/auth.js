(() => {
  const TOKEN_KEY = "access_token";
  const LOGIN_PAGE = "/login-page";

  window.getAuthToken = () => {
    return localStorage.getItem(TOKEN_KEY);
  };

  window.API_BASE_URL = window.location.origin;

  const originalFetch = window.fetch.bind(window);

  window.fetch = async (input, init = {}) => {
    const requestUrl = input instanceof Request ? input.url : input;
    const url = new URL(requestUrl, window.location.href);
    const headers = new Headers(
      init.headers || (input instanceof Request ? input.headers : undefined)
    );
    const token = window.getAuthToken();

    if (
      token &&
      url.origin === window.location.origin &&
      url.pathname !== "/login" &&
      url.pathname !== "/register"
    ) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await originalFetch(input, {
      ...init,
      headers
    });

    if (
      response.status === 401 &&
      token &&
      url.origin === window.location.origin &&
      !["/login", "/register", LOGIN_PAGE].includes(url.pathname)
    ) {
      localStorage.removeItem(TOKEN_KEY);
      window.location.replace(LOGIN_PAGE);
    }

    return response;
  };

  window.authFetch = (url, options = {}) => window.fetch(url, options);

  document.addEventListener("click", event => {
    const button = event.target.closest(
      "#logout-button, #logout, [data-logout]"
    );

    if (button) {
      event.preventDefault();
      localStorage.removeItem(TOKEN_KEY);
      window.location.replace(LOGIN_PAGE);
    }
  });

  if (
    window.location.pathname !== LOGIN_PAGE &&
    !window.getAuthToken()
  ) {
    window.location.replace(LOGIN_PAGE);
  }
})();
