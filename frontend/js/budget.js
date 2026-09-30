const budgetForm = document.getElementById("budget-form");

if (budgetForm) {
  budgetForm.addEventListener("submit", async function (event) {
    event.preventDefault();

    const data = {
      category: document.getElementById("budget-category").value,
      amount: Number(document.getElementById("budget-amount").value),
      month: document.getElementById("budget-month").value,
    };

    try {
      const response = await fetch("http://127.0.0.1:8000/budgets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      if (response.ok) {
        alert("Budget added successfully");
        window.location.href = "/";
      } else {
        document.getElementById("budget-message").textContent = result.detail;
      }
    } catch (error) {
      document.getElementById("budget-message").textContent =
        "Unable to add budget";
    }
  });
}

async function loadBudgetAnalysis() {
  try {
    const response = await fetch("http://127.0.0.1:8000/budgets/analysis");

    const budgets = await response.json();

    const budgetList = document.getElementById("budget-list");

    if (!budgetList) {
      return;
    }

    budgetList.innerHTML = "";

    if (budgets.length === 0) {
      budgetList.innerHTML = '<p class="empty-state">No budgets added yet.</p>';
      return;
    }

    budgets.forEach(function (budget) {
      const budgetDiv = document.createElement("div");

      budgetDiv.innerHTML = `
        <p><strong>${budget.category}</strong></p>
        <p>Budget: ₹${budget.budget}</p>
        <p>Spent: ₹${budget.spent}</p>
        <p>Remaining: ₹${budget.remaining}</p>
      `;

      budgetList.appendChild(budgetDiv);
    });
  } catch (error) {
    console.log("Unable to load budget analysis");
  }
}

loadBudgetAnalysis();
