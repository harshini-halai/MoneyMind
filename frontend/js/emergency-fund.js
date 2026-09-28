const emergencyFundForm = document.getElementById("emergency-fund-form");

emergencyFundForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const data = {
    amount: Number(document.getElementById("emergency-fund-amount").value),
    description: document.getElementById("emergency-fund-description").value,
    date: document.getElementById("emergency-fund-date").value,
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/emergency-fund", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (response.ok) {
      alert("Emergency fund added successfully");
      window.location.href = "/";
    } else {
      document.getElementById("emergency-fund-message").textContent =
        result.detail;
    }
  } catch (error) {
    document.getElementById("emergency-fund-message").textContent =
      "Unable to add emergency fund";
  }
});
