document.addEventListener("DOMContentLoaded", function () {
  const incomeForm = document.getElementById("income-form");
  const expenseForm = document.getElementById("expense-form");
  const refreshButton = document.getElementById("refresh-transactions");

  console.log("transaction.js loaded");

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

  // REFRESH TRANSACTIONS

  if (refreshButton) {
    refreshButton.addEventListener("click", loadTransactions);
  }

  // LOAD TRANSACTIONS

  if (document.querySelector(".transactions-list")) {
    loadTransactions();
  }
});

// LOAD TRANSACTIONS

async function loadTransactions() {
  try {
    const response = await fetch("http://127.0.0.1:8000/transactions");

    const transactions = await response.json();

    const transactionsList = document.querySelector(".transactions-list");

    transactionsList.innerHTML = "";

    transactions.forEach(function (transaction) {
      const transactionDiv = document.createElement("div");

      transactionDiv.innerHTML = `
        <p><strong>${transaction.description}</strong></p>
        <p>Category: ${transaction.category}</p>
        <p>Amount: ₹${transaction.amount}</p>
        <p>Date: ${transaction.date}</p>
        <p>Type: ${transaction.type}</p>

        <button
          class="update-button"
          onclick="updateTransaction(${transaction.id})"
        >
          Update
        </button>

        <button
          class="delete-button"
          onclick="deleteTransaction(${transaction.id})"
        >
          Delete
        </button>
      `;

      transactionsList.appendChild(transactionDiv);
    });
  } catch (error) {
    console.log(error);
  }
}

// UPDATE TRANSACTION

async function updateTransaction(id) {
  const description = prompt("Enter new description");
  const amount = prompt("Enter new amount");

  const category = prompt(
    "Enter category: Food, Travel, Shopping, Bills, Other",
  );

  const date = prompt("Enter date (YYYY-MM-DD)");
  const type = prompt("Enter type: income or expense");

  if (!description || !amount || !category || !date || !type) {
    return;
  }

  const data = {
    description: description,
    category: category,
    amount: Number(amount),
    date: date,
    type: type,
  };

  try {
    const response = await fetch(`http://127.0.0.1:8000/transactions/${id}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (response.ok) {
      alert("Transaction updated successfully");
      loadTransactions();
    } else {
      alert(result.detail);
    }
  } catch (error) {
    alert("Unable to update transaction");
  }
}

// DELETE TRANSACTION

async function deleteTransaction(id) {
  const confirmDelete = confirm(
    "Are you sure you want to delete this transaction?",
  );

  if (!confirmDelete) {
    return;
  }

  try {
    const response = await fetch(`http://127.0.0.1:8000/transactions/${id}`, {
      method: "DELETE",
    });

    const result = await response.json();

    if (response.ok) {
      alert("Transaction deleted successfully");
      loadTransactions();
    } else {
      alert(result.detail);
    }
  } catch (error) {
    alert("Unable to delete transaction");
  }
}
