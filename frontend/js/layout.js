// Builds the sidebar + top bar around <main class="content"> on logged-in pages.
// Load it right after api.js, at the end of <body>. Pages only need:
//   <body data-auth="required" data-page="goals" data-title="Dream Goals">

(function () {
  const body = document.body;
  if (!body || body.dataset.auth !== "required") {
    return;
  }

  const ICONS = {
    home: '<path d="M3 11l9-8 9 8"/><path d="M5 10v10h14V10"/>',
    list: '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    target:
      '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1"/>',
    chat: '<path d="M21 12a8 8 0 0 1-11.6 7.1L3 21l1.9-5.6A8 8 0 1 1 21 12z"/>',
    image:
      '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M21 16l-5-5-9 9"/>',
  };

  const MAIN = [
    { key: "dashboard", href: "/", label: "Dashboard", icon: "home" },
    {
      key: "transactions",
      href: "/transactions-page",
      label: "Transactions",
      icon: "list",
    },
    { key: "goals", href: "/goals-page", label: "Dream Goals", icon: "target" },
    { key: "khata", href: "/khata", label: "Ask Khata", icon: "chat" },
    {
      key: "import",
      href: "/import-screenshot",
      label: "Import Screenshot",
      icon: "image",
    },
  ];

  const ADD = [
    { key: "add-income", href: "/add-income", label: "Add Income" },
    { key: "add-expense", href: "/add-expense", label: "Add Expense" },
    { key: "add-savings", href: "/add-savings", label: "Add Savings" },
    { key: "add-goal", href: "/add-goal", label: "New Goal" },
    {
      key: "add-emergency-fund",
      href: "/add-emergency-fund",
      label: "Emergency Fund",
    },
    {
      key: "add-upcoming-expense",
      href: "/add-upcoming-expense",
      label: "Upcoming Expense",
    },
    { key: "add-budget", href: "/add-budget", label: "Add Budget" },
  ];

  const page = body.dataset.page || "";
  const title = body.dataset.title || "MoneyMind";

  function navLink(item, isMain) {
    const link = document.createElement("a");
    link.href = item.href;
    link.className = "nav-link" + (item.key === page ? " active" : "");
    if (isMain) {
      link.innerHTML =
        '<svg viewBox="0 0 24 24" aria-hidden="true">' +
        ICONS[item.icon] +
        "</svg>";
    } else {
      const dot = document.createElement("span");
      dot.className = "dot";
      dot.textContent = "+";
      link.appendChild(dot);
    }
    link.appendChild(document.createTextNode(item.label));
    return link;
  }

  const sidebar = document.createElement("aside");
  sidebar.className = "sidebar";
  sidebar.id = "sidebar";

  const brand = document.createElement("a");
  brand.href = "/";
  brand.className = "brand";
  brand.innerHTML =
    '<span class="brand-mark" aria-hidden="true">₹</span>MoneyMind';
  sidebar.appendChild(brand);

  MAIN.forEach(function (item) {
    sidebar.appendChild(navLink(item, true));
  });

  const label = document.createElement("div");
  label.className = "nav-label";
  label.textContent = "Add";
  sidebar.appendChild(label);
  ADD.forEach(function (item) {
    sidebar.appendChild(navLink(item, false));
  });

  const footer = document.createElement("div");
  footer.className = "sidebar-footer";
  const themeButton = document.createElement("button");
  themeButton.type = "button";
  themeButton.className = "side-button";
  const logoutButton = document.createElement("button");
  logoutButton.type = "button";
  logoutButton.id = "logout-button"; // api.js attaches the logout handler to this id
  logoutButton.className = "side-button";
  logoutButton.textContent = "Log out";
  footer.appendChild(themeButton);
  footer.appendChild(logoutButton);
  sidebar.appendChild(footer);

  function themeLabel() {
    return currentTheme() === "dark" ? "☀ Light mode" : "☾ Dark mode";
  }
  themeButton.textContent = themeLabel();
  themeButton.addEventListener("click", function () {
    toggleTheme();
    themeButton.textContent = themeLabel();
  });

  const topbar = document.createElement("header");
  topbar.className = "topbar";
  const menuButton = document.createElement("button");
  menuButton.type = "button";
  menuButton.className = "icon-button";
  menuButton.setAttribute("aria-label", "Open menu");
  menuButton.textContent = "☰";
  const heading = document.createElement("h1");
  heading.textContent = title;
  topbar.appendChild(menuButton);
  topbar.appendChild(heading);

  const backdrop = document.createElement("div");
  backdrop.className = "backdrop";

  function closeMenu() {
    body.classList.remove("nav-open");
  }
  menuButton.addEventListener("click", function () {
    body.classList.toggle("nav-open");
  });
  backdrop.addEventListener("click", closeMenu);
  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      closeMenu();
    }
  });

  const shell = document.createElement("div");
  shell.className = "shell";
  const column = document.createElement("div");
  column.className = "main-col";

  const main = document.querySelector("main.content");
  if (!main) {
    return;
  }

  main.parentNode.insertBefore(shell, main);
  column.appendChild(topbar);
  column.appendChild(main);
  shell.appendChild(sidebar);
  shell.appendChild(backdrop);
  shell.appendChild(column);
})();
