// Dashboard (index.html): summary numbers, Khata insights and the spending chart.

const CHART_COLORS = [
  "#2563eb",
  "#14b8a6",
  "#f59e0b",
  "#ec4899",
  "#8b5cf6",
  "#64748b",
];
let lastCategories = null;

function renderSpendingChart(categories) {
  lastCategories = categories;
  const canvas = document.getElementById("spending-chart");
  const emptyState = document.getElementById("chart-empty");
  if (!canvas) {
    return;
  }

  if (!categories || categories.length === 0) {
    canvas.hidden = true;
    if (emptyState) {
      emptyState.hidden = false;
    }
    return;
  }

  canvas.hidden = false;
  if (emptyState) {
    emptyState.hidden = true;
  }

  if (typeof Chart === "undefined") {
    if (emptyState) {
      emptyState.textContent = "Chart library could not be loaded.";
      emptyState.hidden = false;
    }
    return;
  }

  const existing = Chart.getChart(canvas);
  if (existing) {
    existing.destroy();
  }

  const textColor = getComputedStyle(document.documentElement)
    .getPropertyValue("--muted")
    .trim();
  const surface = getComputedStyle(document.documentElement)
    .getPropertyValue("--surface")
    .trim();

  new Chart(canvas, {
    type: "doughnut",
    data: {
      labels: categories.map(function (item) {
        return item.category;
      }),
      datasets: [
        {
          data: categories.map(function (item) {
            return item.total;
          }),
          backgroundColor: CHART_COLORS,
          borderColor: surface,
          borderWidth: 2,
        },
      ],
    },
    options: {
      responsive: true,
      cutout: "62%",
      plugins: {
        legend: { position: "bottom", labels: { color: textColor } },
        tooltip: {
          callbacks: {
            label: function (context) {
              const total = context.dataset.data.reduce(function (sum, value) {
                return sum + value;
              }, 0);
              const percentage = ((context.raw / total) * 100).toFixed(1);
              return `${context.label}: ${formatMoney(context.raw)} (${percentage}%)`;
            },
          },
        },
      },
    },
  });
}

function renderInsights(insights) {
  const list = document.getElementById("insights-list");
  if (!list) {
    return;
  }
  list.innerHTML = "";

  if (!insights || insights.length === 0) {
    const empty = document.createElement("li");
    empty.className = "empty-state";
    empty.textContent = "No insights yet. Add a few transactions first.";
    list.appendChild(empty);
    return;
  }

  insights.forEach(function (insight) {
    const item = document.createElement("li");
    const level = ["warn", "good", "info"].includes(insight.level)
      ? insight.level
      : "info";
    item.className = `insight ${level}`;
    item.textContent = insight.text;
    list.appendChild(item);
  });
}

async function loadInsights() {
  if (!document.getElementById("insights-list")) {
    return;
  }
  try {
    const result = await apiFetch("/khata/insights");
    if (!result.ok) {
      throw new Error("insights failed");
    }
    renderInsights(result.data.insights);
  } catch (error) {
    console.error(error);
    const list = document.getElementById("insights-list");
    list.innerHTML = "";
    const failed = document.createElement("li");
    failed.className = "empty-state";
    failed.textContent = "Khata insights are not available right now.";
    list.appendChild(failed);
  }
}

async function loadDashboard() {
  try {
    const result = await apiFetch("/khata/summary");

    if (!result.ok) {
      throw new Error(errorMessage(result.data, "Unable to load dashboard"));
    }

    const data = result.data;

    setText("balance", formatMoney(data.balance));
    setText("safe-to-spend", formatMoney(data.safe_to_spend));
    setText(
      "upcoming-expenses-summary",
      `Upcoming (next 30 days): ${formatMoney(data.upcoming_expenses)}`,
    );
    setText("total-income", formatMoney(data.income));
    setText("total-expenses", formatMoney(data.expenses));
    setText("protected-savings", formatMoney(data.protected_savings));
    setText("emergency-fund", formatMoney(data.emergency_fund));

    const safe = document.getElementById("safe-to-spend");
    if (safe) {
      safe.classList.toggle("negative", data.safe_to_spend < 0);
    }
    const balance = document.getElementById("balance");
    if (balance) {
      balance.classList.toggle("negative", data.balance < 0);
    }

    renderSpendingChart(data.category_spending);
  } catch (error) {
    console.error(error);
    showMessage(
      "dashboard-message",
      "Unable to load your dashboard. Please refresh the page.",
      "error",
    );
  }
}

document.addEventListener("DOMContentLoaded", function () {
  // The Khata page also loads this file (for renderInsights) but is not the dashboard.
  if (document.body.dataset.page !== "dashboard") {
    return;
  }
  loadDashboard();
  loadInsights();
});

// Redraw the chart in the new colours when the theme changes.
document.addEventListener("themechange", function () {
  if (lastCategories) {
    renderSpendingChart(lastCategories);
  }
});
