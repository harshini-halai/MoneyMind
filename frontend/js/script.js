async function loadBalance() {
  try {
    const response = await fetch("http://127.0.0.1:8000/balance");
    const data = await response.json();

    document.getElementById("balance").textContent = `₹${data.balance}`;
    document.getElementById("total-income").textContent =
      `₹${data.total_income}`;
    document.getElementById("total-expenses").textContent =
      `₹${data.total_expenses}`;
  } catch (error) {
    console.log("Unable to load balance");
  }
}

async function loadTransactions() {
  try {
    const response = await fetch("http://127.0.0.1:8000/transactions");
    const transactions = await response.json();

    const transactionsList = document.querySelector(".transactions-list");
    transactionsList.innerHTML = "";

    if (transactions.length === 0) {
      transactionsList.innerHTML =
        '<p class="empty-state">No transactions yet.</p>';
      return;
    }

    transactions.forEach((transaction) => {
      const transactionItem = document.createElement("div");

      transactionItem.innerHTML = `
                <p><strong>${transaction.description}</strong></p>
                <p>₹${transaction.amount}</p>
                <p>${transaction.category}</p>
                <p>${transaction.date}</p>

                <button class="update-button" type="button" onclick="updateTransaction(${transaction.id})">
                    Update
                </button>

                <button class="delete-button" type="button" onclick="deleteTransaction(${transaction.id})">
                    Delete
                </button>

                <hr>
            `;

      transactionsList.appendChild(transactionItem);
    });
  } catch (error) {
    console.log("Unable to load transactions");
  }
}

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
      loadBalance();
    } else {
      alert(result.detail);
    }
  } catch (error) {
    alert("Unable to delete transaction");
  }
}

async function updateTransaction(id) {
  const description = prompt("Enter new description");
  if (description === null) {
    return;
  }

  const amount = prompt("Enter new amount");
  if (amount === null) {
    return;
  }

  const category = prompt(
    "Enter category: Food, Travel, Shopping, Bills, Other",
  );
  if (category === null) {
    return;
  }

  const date = prompt("Enter date (YYYY-MM-DD)");
  if (date === null) {
    return;
  }

  const transactionType = prompt("Enter type: income or expense");
  if (transactionType === null) {
    return;
  }

  const data = {
    description: description,
    category: category,
    amount: Number(amount),
    date: date,
    type: transactionType,
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
      loadBalance();
    } else {
      alert(result.detail);
    }
  } catch (error) {
    alert("Unable to update transaction");
  }
}

document
  .getElementById("refresh-transactions")
  .addEventListener("click", function () {
    loadTransactions();
    loadBalance();
  });

loadBalance();
loadTransactions();
