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

function cssVar(name) {
  return getComputedStyle(document.documentElement)
    .getPropertyValue(name)
    .trim();
}

// Draws the spending doughnut with the plain canvas API (no chart library needed).
function renderSpendingChart(categories) {
  lastCategories = categories;
  const canvas = document.getElementById("spending-chart");
  const legend = document.getElementById("chart-legend");
  const emptyState = document.getElementById("chart-empty");
  if (!canvas) {
    return;
  }

  const items = (categories || []).filter(function (item) {
    return Number(item.total) > 0;
  });

  if (items.length === 0) {
    canvas.hidden = true;
    if (legend) {
      legend.hidden = true;
    }
    if (emptyState) {
      emptyState.hidden = false;
    }
    return;
  }

  canvas.hidden = false;
  if (legend) {
    legend.hidden = false;
  }
  if (emptyState) {
    emptyState.hidden = true;
  }

  const total = items.reduce(function (sum, item) {
    return sum + Number(item.total);
  }, 0);

  const size = 600;
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, size, size);

  const center = size / 2;
  const ringWidth = 110;
  const radius = center - ringWidth / 2 - 10;
  const gap = items.length > 1 ? 0.025 : 0;
  let angle = -Math.PI / 2;

  items.forEach(function (item, index) {
    const sweep = (Number(item.total) / total) * Math.PI * 2;
    ctx.beginPath();
    ctx.arc(center, center, radius, angle + gap / 2, angle + sweep - gap / 2);
    ctx.lineWidth = ringWidth;
    ctx.strokeStyle = CHART_COLORS[index % CHART_COLORS.length];
    ctx.stroke();
    angle += sweep;
  });

  ctx.textAlign = "center";
  ctx.fillStyle = cssVar("--muted");
  ctx.font = "600 28px -apple-system, Segoe UI, Roboto, Arial, sans-serif";
  ctx.fillText("Total spent", center, center - 12);
  ctx.fillStyle = cssVar("--text");
  ctx.font = "700 40px -apple-system, Segoe UI, Roboto, Arial, sans-serif";
  ctx.fillText(formatMoney(total), center, center + 34);

  if (legend) {
    legend.innerHTML = "";
    items.forEach(function (item, index) {
      const row = document.createElement("li");
      const dot = document.createElement("span");
      dot.className = "legend-dot";
      dot.style.background = CHART_COLORS[index % CHART_COLORS.length];
      const name = document.createElement("span");
      name.className = "legend-name";
      name.textContent = item.category;
      const value = document.createElement("span");
      value.className = "legend-value";
      const percent = ((Number(item.total) / total) * 100).toFixed(1);
      value.textContent = `${formatMoney(item.total)} (${percent}%)`;
      row.appendChild(dot);
      row.appendChild(name);
      row.appendChild(value);
      legend.appendChild(row);
    });
  }
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
