async function loadBalance() {
  try {
    const response = await fetch("http://127.0.0.1:8000/balance");
    const data = await response.json();

    console.log(data);

    document.getElementById("balance").textContent = `₹${data.balance}`;
    document.getElementById("total-income").textContent =
      `₹${data.total_income}`;
    document.getElementById("total-expenses").textContent =
      `₹${data.total_expenses}`;
  } catch (error) {
    console.log("Unable to load balance");
  }
}

loadBalance();

async function loadTransactions() {
  try {
    const response = await fetch("http://127.0.0.1:8000/transactions");
    const transactions = await response.json();

    const transactionsList = document.querySelector(".transactions-list");

    transactionsList.innerHTML = "";

    transactions.forEach((transaction) => {
      const transactionItem = document.createElement("div");

      transactionItem.innerHTML = `
              <p>${transaction.description}</p>
              <p>₹${transaction.amount}</p>
              <p>${transaction.category}</p>
              <p>${transaction.date}</p>
          `;

      transactionsList.appendChild(transactionItem);
    });
  } catch (error) {
    console.log("Unable to load transactions");
  }
}