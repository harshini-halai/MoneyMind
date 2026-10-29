// Add income / add expense forms, and the transactions list (edit + delete).

let transactionsById = {};

// ---------- list ----------

function buildTransactionItem(transaction) {
  const item = document.createElement("div");
  item.className = "transaction-item";

  const main = document.createElement("div");
  main.className = "transaction-main";
  const title = document.createElement("strong");
  title.textContent = transaction.description;
  const meta = document.createElement("span");
  meta.className = "transaction-meta";
  meta.textContent = `${transaction.category} · ${transaction.date}`;
  main.appendChild(title);
  main.appendChild(meta);

  const amount = document.createElement("div");
  const isIncome = transaction.type === "income";
  amount.className = `transaction-amount ${isIncome ? "income" : "expense"}`;
  amount.textContent = `${isIncome ? "+" : "-"}${formatMoney(transaction.amount)}`;

  const actions = document.createElement("div");
  actions.className = "transaction-actions";

  const editButton = document.createElement("button");
  editButton.type = "button";
  editButton.className = "update-button";
  editButton.dataset.action = "edit";
  editButton.dataset.id = transaction.id;
  editButton.textContent = "Update";

  const deleteButton = document.createElement("button");
  deleteButton.type = "button";
  deleteButton.className = "delete-button";
  deleteButton.dataset.action = "delete";
  deleteButton.dataset.id = transaction.id;
  deleteButton.textContent = "Delete";

  actions.appendChild(editButton);
  actions.appendChild(deleteButton);

  item.appendChild(main);
  item.appendChild(amount);
  item.appendChild(actions);
  return item;
}

async function loadTransactions() {
  const list = document.querySelector(".transactions-list");
  if (!list) {
    return;
  }

  try {
    const result = await apiFetch("/transactions");
    if (!result.ok) {
      throw new Error(errorMessage(result.data, "Unable to load transactions"));
    }

    transactionsById = {};
    list.innerHTML = "";

    if (result.data.length === 0) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "No transactions yet.";
      list.appendChild(empty);
      return;
    }

    result.data.forEach(function (transaction) {
      transactionsById[transaction.id] = transaction;
      list.appendChild(buildTransactionItem(transaction));
    });
  } catch (error) {
    console.error(error);
    showMessage(
      "transactions-message",
      "Unable to load transactions.",
      "error",
    );
  }
}

// ---------- edit dialog ----------

function openEditDialog(id) {
  const transaction = transactionsById[id];
  const dialog = document.getElementById("edit-dialog");
  if (!transaction || !dialog) {
    return;
  }

  document.getElementById("edit-id").value = transaction.id;
  document.getElementById("edit-description").value = transaction.description;
  document.getElementById("edit-amount").value = transaction.amount;
  document.getElementById("edit-category").value = transaction.category;
  document.getElementById("edit-date").value = String(transaction.date).slice(
    0,
    10,
  );
  document.getElementById("edit-type").value = transaction.type;
  showMessage("edit-message", "");
  dialog.showModal();
}

async function saveEdit(event) {
  event.preventDefault();
  const id = document.getElementById("edit-id").value;
  const saveButton = document.getElementById("edit-save");
  saveButton.disabled = true;

  const data = {
    description: document.getElementById("edit-description").value.trim(),
    category: document.getElementById("edit-category").value,
    amount: Number(document.getElementById("edit-amount").value),
    date: document.getElementById("edit-date").value,
    type: document.getElementById("edit-type").value,
  };

  try {
    const result = await apiFetch(`/transactions/${encodeURIComponent(id)}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });

    if (result.ok) {
      document.getElementById("edit-dialog").close();
      showMessage("transactions-message", "Transaction updated", "success");
      await loadTransactions();
    } else {
      showMessage(
        "edit-message",
        errorMessage(result.data, "Unable to update transaction"),
        "error",
      );
    }
  } catch (error) {
    showMessage("edit-message", "Unable to update transaction", "error");
  }

  saveButton.disabled = false;
}

// ---------- delete ----------

async function deleteTransaction(id) {
  if (!confirm("Are you sure you want to delete this transaction?")) {
    return;
  }

  try {
    const result = await apiFetch(`/transactions/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });

    if (result.ok) {
      showMessage("transactions-message", "Transaction deleted", "success");
      await loadTransactions();
    } else {
      showMessage(
        "transactions-message",
        errorMessage(result.data, "Unable to delete transaction"),
        "error",
      );
    }
  } catch (error) {
    showMessage(
      "transactions-message",
      "Unable to delete transaction",
      "error",
    );
  }
}

// ---------- page setup ----------

document.addEventListener("DOMContentLoaded", function () {
  setDefaultDate("income-date");
  setDefaultDate("expense-date");

  bindSimpleForm({
    formId: "income-form",
    endpoint: "/transactions",
    messageId: "income-message",
    successText: "Income added successfully",
    failText: "Unable to add income",
    buildPayload: function () {
      return {
        description: document.getElementById("income-description").value.trim(),
        category: "Other",
        amount: Number(document.getElementById("income-amount").value),
        date: document.getElementById("income-date").value,
        type: "income",
      };
    },
  });

  bindSimpleForm({
    formId: "expense-form",
    endpoint: "/transactions",
    messageId: "expense-message",
    successText: "Expense added successfully",
    failText: "Unable to add expense",
    buildPayload: function () {
      return {
        description: document
          .getElementById("expense-description")
          .value.trim(),
        category: document.getElementById("expense-category").value,
        amount: Number(document.getElementById("expense-amount").value),
        date: document.getElementById("expense-date").value,
        type: "expense",
      };
    },
  });

  const list = document.querySelector(".transactions-list");
  if (list) {
    list.addEventListener("click", function (event) {
      const button = event.target.closest("button[data-action]");
      if (!button) {
        return;
      }
      if (button.dataset.action === "edit") {
        openEditDialog(button.dataset.id);
      } else if (button.dataset.action === "delete") {
        deleteTransaction(button.dataset.id);
      }
    });

    const refreshButton = document.getElementById("refresh-transactions");
    if (refreshButton) {
      refreshButton.addEventListener("click", loadTransactions);
    }

    const editForm = document.getElementById("edit-form");
    if (editForm) {
      editForm.addEventListener("submit", saveEdit);
    }

    const cancelEdit = document.getElementById("edit-cancel");
    if (cancelEdit) {
      cancelEdit.addEventListener("click", function () {
        document.getElementById("edit-dialog").close();
      });
    }

    loadTransactions();
  }
});
