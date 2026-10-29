// Budgets: the add-budget form and the dashboard budget overview.

function monthToDate(monthValue) {
  // <input type="month"> gives "YYYY-MM"; the API wants a full date.
  if (!/^\d{4}-\d{2}$/.test(monthValue)) {
    throw new Error("Choose a month");
  }
  return `${monthValue}-01`;
}

function defaultMonthValue() {
  return todayISO().slice(0, 7);
}

function renderBudgets(budgets) {
  const budgetList = document.getElementById("budget-list");
  if (!budgetList) {
    return;
  }

  budgetList.innerHTML = "";

  if (budgets.length === 0) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "No budgets added yet.";
    budgetList.appendChild(empty);
    return;
  }

  budgets.forEach(function (budget) {
    const item = document.createElement("div");
    item.className = "budget-item";

    const title = document.createElement("p");
    const name = document.createElement("strong");
    name.textContent = budget.category;
    title.appendChild(name);
    title.appendChild(
      document.createTextNode(` · ${formatMonth(budget.month)}`),
    );

    const progress = document.createElement("div");
    progress.className = "progress";
    const fill = document.createElement("div");
    fill.className = "progress-fill";
    fill.style.width = `${Math.min(budget.percent_used, 100)}%`;
    if (budget.percent_used >= 100) {
      fill.classList.add("over");
    } else if (budget.percent_used >= 80) {
      fill.classList.add("warn");
    }
    progress.appendChild(fill);

    const details = document.createElement("p");
    details.className = "budget-details";
    details.textContent =
      `Spent ${formatMoney(budget.spent)} of ${formatMoney(budget.budget)} ` +
      `(${budget.percent_used}%) · ` +
      (budget.remaining >= 0
        ? `${formatMoney(budget.remaining)} left`
        : `${formatMoney(Math.abs(budget.remaining))} over budget`);

    item.appendChild(title);
    item.appendChild(progress);
    item.appendChild(details);
    budgetList.appendChild(item);
  });
}

async function loadBudgetAnalysis() {
  if (!document.getElementById("budget-list")) {
    return;
  }

  try {
    const result = await apiFetch("/budgets/analysis");
    if (!result.ok) {
      throw new Error(errorMessage(result.data, "Unable to load budgets"));
    }
    renderBudgets(result.data);
  } catch (error) {
    console.error(error);
    const budgetList = document.getElementById("budget-list");
    budgetList.innerHTML = "";
    const failed = document.createElement("p");
    failed.className = "empty-state";
    failed.textContent = "Unable to load budgets.";
    budgetList.appendChild(failed);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const monthInput = document.getElementById("budget-month");
  if (monthInput && !monthInput.value) {
    monthInput.value = defaultMonthValue();
  }

  bindSimpleForm({
    formId: "budget-form",
    endpoint: "/budgets",
    messageId: "budget-message",
    successText: "Budget added successfully",
    failText: "Unable to add budget",
    buildPayload: function () {
      return {
        category: document.getElementById("budget-category").value,
        amount: Number(document.getElementById("budget-amount").value),
        month: monthToDate(document.getElementById("budget-month").value),
      };
    },
  });

  loadBudgetAnalysis();
});
