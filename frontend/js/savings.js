const savingsForm = document.getElementById("savings-form");

savingsForm.addEventListener("submit", async function (event) {
  event.preventDefault();

  const data = {
    amount: Number(document.getElementById("savings-amount").value),
    description: document.getElementById("savings-description").value,
    date: document.getElementById("savings-date").value,
  };

  try {
    const response = await fetch("http://127.0.0.1:8000/savings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(data),
    });

    const result = await response.json();

    if (response.ok) {
      alert("Savings added successfully");
      window.location.href = "/";
    } else {
      document.getElementById("savings-message").textContent = result.detail;
    }
  } catch (error) {
    document.getElementById("savings-message").textContent =
      "Unable to add savings";
  }
});
