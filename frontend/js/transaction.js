document.addEventListener("DOMContentLoaded", function () {
  const incomeForm = document.getElementById("income-form");
  const expenseForm = document.getElementById("expense-form");

  // ADD INCOME

  if (incomeForm) {
    incomeForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const data = {
        description: document.getElementById("income-description").value,
        category: "Other",
        amount: Number(document.getElementById("income-amount").value),
        date: document.getElementById("income-date").value,
        type: "income",
      };

      try {
        const response = await fetch("http://127.0.0.1:8000/transactions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok) {
          alert("Income added successfully");

          window.location.href = "/";
        } else {
          document.getElementById("income-message").textContent = result.detail;
        }
      } catch (error) {
        document.getElementById("income-message").textContent =
          "Unable to add income";
      }
    });
  }

  // ADD EXPENSE

  if (expenseForm) {
    expenseForm.addEventListener("submit", async function (event) {
      event.preventDefault();

      const data = {
        description: document.getElementById("expense-description").value,
        category: document.getElementById("expense-category").value,
        amount: Number(document.getElementById("expense-amount").value),
        date: document.getElementById("expense-date").value,
        type: "expense",
      };

      try {
        const response = await fetch("http://127.0.0.1:8000/transactions", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();

        if (response.ok) {
          alert("Expense added successfully");

          window.location.href = "/";
        } else {
          document.getElementById("expense-message").textContent =
            result.detail;
        }
      } catch (error) {
        document.getElementById("expense-message").textContent =
          "Unable to add expense";
      }
    });
  }
});
