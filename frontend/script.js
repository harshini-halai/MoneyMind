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
