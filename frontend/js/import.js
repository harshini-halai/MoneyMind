// Import transactions from a payment-app screenshot.
// Flow: upload -> server reads the image and returns DRAFT rows -> you review
// and edit them here -> only the rows you tick are saved.

const IMPORT_CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Other"];
const MAX_UPLOAD_BYTES = 5 * 1024 * 1024;
let importPreviewUrl = null;

function makeCell(labelText, control, extraClass) {
  const cell = document.createElement("label");
  cell.className = `import-cell ${extraClass}`;
  const caption = document.createElement("span");
  caption.textContent = labelText;
  cell.appendChild(caption);
  cell.appendChild(control);
  return cell;
}

function makeSelect(values, selected, className) {
  const select = document.createElement("select");
  select.className = className;
  values.forEach(function (value) {
    const option = document.createElement("option");
    option.value = value;
    option.textContent = value.charAt(0).toUpperCase() + value.slice(1);
    select.appendChild(option);
  });
  select.value = selected;
  return select;
}

function makeBadge(text) {
  const badge = document.createElement("span");
  badge.className = "badge";
  badge.textContent = text;
  return badge;
}

function buildImportRow(candidate) {
  const row = document.createElement("div");
  row.className = "import-row";
  row.dataset.original = String(candidate.amount);
  row.dataset.alt =
    candidate.alt_amount === null || candidate.alt_amount === undefined
      ? ""
      : String(candidate.alt_amount);

  const include = document.createElement("input");
  include.type = "checkbox";
  include.className = "row-include";
  include.checked = !candidate.possible_duplicate;
  include.setAttribute("aria-label", "Include this transaction");

  const description = document.createElement("input");
  description.type = "text";
  description.className = "row-description";
  description.maxLength = 255;
  description.value = candidate.description;

  const amount = document.createElement("input");
  amount.type = "number";
  amount.className = "row-amount";
  amount.min = "0.01";
  amount.step = "0.01";
  amount.value = candidate.amount;
  amount.addEventListener("input", function () {
    row.dataset.edited = "1"; // never overwrite an amount the user typed
  });

  const date = document.createElement("input");
  date.type = "date";
  date.className = "row-date";
  date.value = candidate.date;

  const type = makeSelect(["expense", "income"], candidate.type, "row-type");
  const category = makeSelect(
    IMPORT_CATEGORIES,
    candidate.category,
    "row-category",
  );
  type.addEventListener("change", function () {
    if (type.value === "income") {
      category.value = "Other";
    }
  });

  const notes = document.createElement("div");
  notes.className = "import-notes";
  if (candidate.possible_duplicate) {
    notes.appendChild(makeBadge("Possible duplicate - unticked"));
  }
  if (candidate.date_guessed) {
    notes.appendChild(makeBadge("Date guessed - please check"));
  }
  if (row.dataset.alt !== "") {
    notes.appendChild(makeBadge("Check amount against your screenshot"));
  }

  const includeCell = document.createElement("div");
  includeCell.className = "import-include";
  includeCell.appendChild(include);

  row.appendChild(includeCell);
  row.appendChild(makeCell("Description", description, "cell-description"));
  row.appendChild(makeCell("Amount (₹)", amount, "cell-amount"));
  row.appendChild(makeCell("Date", date, "cell-date"));
  row.appendChild(makeCell("Type", type, "cell-type"));
  row.appendChild(makeCell("Category", category, "cell-category"));
  row.appendChild(notes);
  return row;
}

function applyDropFirstDigit(enabled) {
  document.querySelectorAll(".import-row").forEach(function (row) {
    if (row.dataset.edited === "1" || row.dataset.alt === "") {
      return;
    }
    row.querySelector(".row-amount").value = enabled
      ? row.dataset.alt
      : row.dataset.original;
  });
}

function renderImportResults(data, file) {
  const results = document.getElementById("import-results");
  const rows = document.getElementById("import-rows");
  rows.innerHTML = "";

  if (data.transactions.length === 0) {
    results.hidden = true;
    showMessage(
      "import-message",
      "No transactions were found. Try a clearer screenshot, crop it to just the list, or use a screenshot that shows amounts with the ₹ sign.",
      "error",
    );
    return;
  }

  data.transactions.forEach(function (candidate) {
    rows.appendChild(buildImportRow(candidate));
  });

  if (importPreviewUrl) {
    URL.revokeObjectURL(importPreviewUrl);
  }
  importPreviewUrl = URL.createObjectURL(file);
  document.getElementById("import-preview").src = importPreviewUrl;

  const anyAlt = data.transactions.some(function (item) {
    return item.alt_amount !== null && item.alt_amount !== undefined;
  });
  document.getElementById("import-drop-digit-row").hidden = !anyAlt;
  document.getElementById("import-drop-digit").checked = false;

  document.getElementById("import-raw").textContent = data.text;
  showMessage("import-save-message", "");
  results.hidden = false;
  results.scrollIntoView({ behavior: "smooth" });
}

function collectSelectedRows() {
  const items = [];

  document.querySelectorAll(".import-row").forEach(function (row) {
    if (!row.querySelector(".row-include").checked) {
      return;
    }

    const description = row.querySelector(".row-description").value.trim();
    const amount = Number(row.querySelector(".row-amount").value);
    const date = row.querySelector(".row-date").value;

    if (!description) {
      throw new Error("Every ticked row needs a description");
    }
    if (!(amount > 0)) {
      throw new Error("Every ticked row needs an amount above 0");
    }
    if (!date) {
      throw new Error("Every ticked row needs a date");
    }

    items.push({
      description: description,
      amount: amount,
      date: date,
      type: row.querySelector(".row-type").value,
      category: row.querySelector(".row-category").value,
    });
  });

  if (items.length === 0) {
    throw new Error("Tick at least one transaction to save");
  }
  return items;
}

document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("import-form");
  if (!form) {
    return;
  }

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    showMessage("import-message", "");

    const fileInput = document.getElementById("import-file");
    const file = fileInput.files[0];
    if (!file) {
      showMessage("import-message", "Choose a screenshot first", "error");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      showMessage("import-message", "Image is too large (max 5 MB)", "error");
      return;
    }

    const button = document.getElementById("import-scan");
    button.disabled = true;
    button.textContent = "Reading screenshot...";

    try {
      const formData = new FormData();
      formData.append("file", file);
      formData.append(
        "default_type",
        document.getElementById("import-default-type").value,
      );

      const result = await apiFetch("/import/screenshot", {
        method: "POST",
        body: formData,
      });

      if (result.ok) {
        renderImportResults(result.data, file);
      } else {
        showMessage(
          "import-message",
          errorMessage(result.data, "Unable to read the screenshot"),
          "error",
        );
      }
    } catch (error) {
      showMessage("import-message", "Unable to read the screenshot", "error");
    }

    button.disabled = false;
    button.textContent = "Scan screenshot";
  });

  document
    .getElementById("import-drop-digit")
    .addEventListener("change", function (event) {
      applyDropFirstDigit(event.target.checked);
    });

  document
    .getElementById("import-save")
    .addEventListener("click", async function () {
      const saveButton = document.getElementById("import-save");
      showMessage("import-save-message", "");

      let items;
      try {
        items = collectSelectedRows();
      } catch (error) {
        showMessage("import-save-message", error.message, "error");
        return;
      }

      saveButton.disabled = true;
      try {
        const result = await apiFetch("/transactions/bulk", {
          method: "POST",
          body: JSON.stringify({ transactions: items }),
        });

        if (result.ok) {
          flashAndGo(`${result.data.count} transactions imported`, "/");
          return;
        }
        showMessage(
          "import-save-message",
          errorMessage(result.data, "Unable to save transactions"),
          "error",
        );
      } catch (error) {
        showMessage(
          "import-save-message",
          "Unable to save transactions",
          "error",
        );
      }
      saveButton.disabled = false;
    });
});
