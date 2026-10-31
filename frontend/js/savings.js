// Add Savings page. You can optionally put the money towards a goal
// (a "Dream Goals" card sends you here with ?goal=ID already chosen).

async function loadGoalOptions() {
  const select = document.getElementById("savings-goal");
  if (!select) {
    return;
  }

  try {
    const result = await apiFetch("/goals");
    if (!result.ok) {
      return;
    }
    const wanted = new URLSearchParams(window.location.search).get("goal");

    result.data.forEach(function (goal) {
      if (goal.status === "achieved" && String(goal.id) !== wanted) {
        return;
      }
      const option = document.createElement("option");
      option.value = goal.id;
      option.textContent = `${goal.name} (${formatMoney(goal.saved)} of ${formatMoney(goal.target_amount)})`;
      select.appendChild(option);
    });

    if (wanted) {
      select.value = wanted;
    }
  } catch (error) {
    // Goals are optional here, so a failure is silently ignored.
  }
}

document.addEventListener("DOMContentLoaded", function () {
  setDefaultDate("savings-date");
  loadGoalOptions();

  bindSimpleForm({
    formId: "savings-form",
    endpoint: "/savings",
    messageId: "savings-message",
    successText: "Savings added successfully",
    failText: "Unable to add savings",
    redirectTo: function () {
      const goal = document.getElementById("savings-goal");
      return goal && goal.value ? "/goals-page" : "/";
    },
    buildPayload: function () {
      const goal = document.getElementById("savings-goal");
      const payload = {
        amount: Number(document.getElementById("savings-amount").value),
        description: document
          .getElementById("savings-description")
          .value.trim(),
        date: document.getElementById("savings-date").value,
      };
      if (goal && goal.value) {
        payload.goal_id = Number(goal.value);
      }
      return payload;
    },
  });
});
