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

loadBalance();

async function loadSavings() {
  try {
    const response = await fetch("http://127.0.0.1:8000/savings/total");

    const data = await response.json();

    document.getElementById("protected-savings").textContent =
      `₹${data.protected_savings}`;
  } catch (error) {
    console.log("Unable to load savings");
  }
}

loadSavings();

async function loadEmergencyFund() {
  try {
    const response = await fetch("http://127.0.0.1:8000/emergency-fund/total");

    const data = await response.json();

    document.getElementById("emergency-fund").textContent =
      `₹${data.emergency_fund}`;
  } catch (error) {
    console.log("Unable to load emergency fund");
  }
}

loadEmergencyFund();

async function loadSafeToSpend() {
  try {
    const response = await fetch("http://127.0.0.1:8000/safe-to-spend");

    const data = await response.json();

    document.getElementById("safe-to-spend").textContent =
      `₹${data.safe_to_spend}`;
    document.getElementById("upcoming-expenses-summary").textContent =
      `Upcoming: ₹${data.upcoming_expenses}`;
  } catch (error) {
    console.log("Unable to load safe-to-spend");
  }
}

loadSafeToSpend();
