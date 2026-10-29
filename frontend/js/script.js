// Dashboard (index.html): one request fills the whole overview.

function renderSpendingChart(categories) {
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
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
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

document.addEventListener("DOMContentLoaded", loadDashboard);
