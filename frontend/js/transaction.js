let extractedTransactions = [];

const allowedCategories = ["Food", "Travel", "Shopping", "Bills", "Other"];

async function loadTransactions() {
  const response = await authFetch("/transactions");
  if (!response) return;

  const transactions = await response.json();
  const listContainer = document.getElementById("transaction-list");
  if (!listContainer) return;

  listContainer.innerHTML = "";

  transactions.forEach((tx) => {
    const row = document.createElement("tr");

    const dateTd = document.createElement("td");
    dateTd.textContent = tx.date;

    const descTd = document.createElement("td");
    descTd.textContent = tx.description || tx.title;

    const catTd = document.createElement("td");
    catTd.textContent = tx.category;

    const typeTd = document.createElement("td");
    typeTd.textContent = tx.type || tx.transaction_type;

    const amountTd = document.createElement("td");
    amountTd.textContent = `₹${tx.amount}`;

    const actionTd = document.createElement("td");
    const deleteBtn = document.createElement("button");
    deleteBtn.textContent = "Delete";
    deleteBtn.style.padding = "4px 8px";
    deleteBtn.addEventListener("click", () => deleteTransaction(tx.id));
    actionTd.appendChild(deleteBtn);

    row.appendChild(dateTd);
    row.appendChild(descTd);
    row.appendChild(catTd);
    row.appendChild(typeTd);
    row.appendChild(amountTd);
    row.appendChild(actionTd);

    listContainer.appendChild(row);
  });
}

async function deleteTransaction(transactionId) {
  if (!confirm("Are you sure you want to delete this transaction?")) return;

  const response = await authFetch(`/transactions/${transactionId}`, {
    method: "DELETE",
  });

  if (response && response.ok) {
    loadTransactions();
  } else {
    alert("Failed to delete transaction.");
  }
}

async function uploadScreenshot() {
  const fileInput = document.getElementById("screenshot-file-input");
  const statusDiv = document.getElementById("import-status");
  const previewSection = document.getElementById("preview-section");

  if (!fileInput.files || fileInput.files.length === 0) {
    statusDiv.textContent = "Please select an image first.";
    statusDiv.style.color = "red";
    return;
  }

  const file = fileInput.files[0];
  const formData = new FormData();
  formData.append("file", file);

  statusDiv.textContent =
    "Processing image with vision model/OCR... Please wait.";
  statusDiv.style.color = "blue";
  previewSection.style.display = "none";

  const token = getAuthToken();
  const headers = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  try {
    const res = await fetch(`${API_BASE_URL}/transactions/import-screenshot`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      statusDiv.textContent =
        "Extraction failed. Check file format or server logs.";
      statusDiv.style.color = "red";
      return;
    }

    const data = await res.json();
    extractedTransactions = data.transactions || [];

    if (extractedTransactions.length === 0) {
      statusDiv.textContent = "No transactions found in this screenshot.";
      statusDiv.style.color = "orange";
      return;
    }

    statusDiv.textContent = `Extracted ${extractedTransactions.length} transaction(s). Please review and correct below.`;
    statusDiv.style.color = "green";
    renderPreview();
  } catch (err) {
    statusDiv.textContent = "Network error during upload.";
    statusDiv.style.color = "red";
  }
}

function renderPreview() {
  const previewSection = document.getElementById("preview-section");
  const previewList = document.getElementById("preview-list");
  previewList.innerHTML = "";

  extractedTransactions.forEach((item, index) => {
    const row = document.createElement("tr");
    if (item.needs_review) {
      row.style.backgroundColor = "#fff3cd";
    }

    const dateTd = document.createElement("td");
    const dateInput = document.createElement("input");
    dateInput.type = "date";
    dateInput.value = item.date || "";
    dateInput.addEventListener("input", (e) => {
      extractedTransactions[index].date = e.target.value;
    });
    dateTd.appendChild(dateInput);

    const descTd = document.createElement("td");
    const descInput = document.createElement("input");
    descInput.type = "text";
    descInput.value = item.description || "";
    descInput.addEventListener("input", (e) => {
      extractedTransactions[index].description = e.target.value;
    });
    descTd.appendChild(descInput);

    const amountTd = document.createElement("td");
    const amountInput = document.createElement("input");
    amountInput.type = "number";
    amountInput.step = "0.01";
    amountInput.value = item.amount || 0;
    amountInput.addEventListener("input", (e) => {
      extractedTransactions[index].amount = parseFloat(e.target.value) || 0;
    });
    amountTd.appendChild(amountInput);

    const typeTd = document.createElement("td");
    const typeSelect = document.createElement("select");
    ["expense", "income"].forEach((t) => {
      const opt = document.createElement("option");
      opt.value = t;
      opt.textContent = t;
      if (t === item.type) opt.selected = true;
      typeSelect.appendChild(opt);
    });
    typeSelect.addEventListener("change", (e) => {
      extractedTransactions[index].type = e.target.value;
    });
    typeTd.appendChild(typeSelect);

    const catTd = document.createElement("td");
    const catSelect = document.createElement("select");
    allowedCategories.forEach((c) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      if (c === item.category) opt.selected = true;
      catSelect.appendChild(opt);
    });
    catSelect.addEventListener("change", (e) => {
      extractedTransactions[index].category = e.target.value;
    });
    catTd.appendChild(catSelect);

    const statusTd = document.createElement("td");
    statusTd.textContent = item.needs_review ? "Needs review" : "Ready";
    statusTd.style.fontWeight = "bold";
    statusTd.style.color = item.needs_review ? "#856404" : "green";

    const actionTd = document.createElement("td");
    const removeBtn = document.createElement("button");
    removeBtn.type = "button";
    removeBtn.textContent = "Remove";
    removeBtn.addEventListener("click", () => {
      extractedTransactions.splice(index, 1);
      renderPreview();
    });
    actionTd.appendChild(removeBtn);

    row.appendChild(dateTd);
    row.appendChild(descTd);
    row.appendChild(amountTd);
    row.appendChild(typeTd);
    row.appendChild(catTd);
    row.appendChild(statusTd);
    row.appendChild(actionTd);

    previewList.appendChild(row);
  });

  previewSection.style.display = "block";
}

async function confirmImport() {
  if (extractedTransactions.length === 0) {
    alert("No items to save.");
    return;
  }

  for (let i = 0; i < extractedTransactions.length; i++) {
    const item = extractedTransactions[i];
    if (!item.date) {
      alert(`Row ${i + 1}: Date missing hai, please date enter karein.`);
      return;
    }
    if (item.amount <= 0) {
      alert(`Row ${i + 1}: Amount 0 se zyada hona chahiye.`);
      return;
    }
  }

  const payload = extractedTransactions.map((item) => ({
    description: item.description,
    amount: item.amount,
    category: item.category,
    type: item.type,
    date: item.date,
  }));

  const response = await authFetch("/transactions/confirm-import", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (response && response.ok) {
    alert("All transactions imported successfully!");
    extractedTransactions = [];
    document.getElementById("preview-section").style.display = "none";
    document.getElementById("import-status").textContent = "";
    document.getElementById("screenshot-file-input").value = "";
    loadTransactions();
  } else {
    alert("Failed to confirm transactions. Please check input fields.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.getElementById("transaction-list")) {
    loadTransactions();
  }

  const uploadBtn = document.getElementById("upload-screenshot-btn");
  if (uploadBtn) {
    uploadBtn.addEventListener("click", uploadScreenshot);
  }

  const confirmBtn = document.getElementById("confirm-import-btn");
  if (confirmBtn) {
    confirmBtn.addEventListener("click", confirmImport);
  }

  const cancelBtn = document.getElementById("cancel-import-btn");
  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      extractedTransactions = [];
      document.getElementById("preview-section").style.display = "none";
      document.getElementById("import-status").textContent = "";
      document.getElementById("screenshot-file-input").value = "";
    });
  }
});
