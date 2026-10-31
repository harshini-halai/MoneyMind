// Dream Goals: the goals page, the dashboard preview and the "new goal" form.

function goalStatusText(goal) {
  if (goal.status === "achieved") {
    return "Goal achieved. Well done!";
  }
  if (goal.status === "overdue") {
    return "The target date has passed.";
  }
  if (goal.status === "active") {
    return `Save about ${formatMoney(goal.monthly_needed)} a month · ${goal.days_left} days left`;
  }
  return "No target date set.";
}

function goalBadge(goal) {
  const badge = document.createElement("span");
  badge.className = "badge";
  if (goal.status === "achieved") {
    badge.classList.add("good");
    badge.textContent = "Achieved";
  } else if (goal.status === "overdue") {
    badge.classList.add("bad");
    badge.textContent = "Overdue";
  } else if (goal.status === "active") {
    badge.classList.add("info");
    badge.textContent = `${goal.percent}%`;
  } else {
    badge.classList.add("info");
    badge.textContent = `${goal.percent}%`;
  }
  return badge;
}

function goalProgressBar(goal) {
  const bar = document.createElement("div");
  bar.className = "progress";
  const fill = document.createElement("div");
  fill.className =
    "progress-fill " + (goal.status === "achieved" ? "done" : "goal");
  fill.style.width = `${Math.min(goal.percent, 100)}%`;
  bar.appendChild(fill);
  return bar;
}

function buildGoalCard(goal) {
  const card = document.createElement("div");
  card.className = "goal-card";

  const top = document.createElement("div");
  top.className = "goal-top";
  const name = document.createElement("div");
  name.className = "goal-name";
  name.textContent = goal.name;
  top.appendChild(name);
  top.appendChild(goalBadge(goal));

  const saved = document.createElement("div");
  saved.className = "goal-saved";
  saved.textContent = formatMoney(goal.saved) + " ";
  const target = document.createElement("small");
  target.textContent = `of ${formatMoney(goal.target_amount)}`;
  saved.appendChild(target);

  const note = document.createElement("p");
  note.className = "goal-note";
  note.textContent = goalStatusText(goal);

  const dateNote = document.createElement("p");
  dateNote.className = "goal-note";
  dateNote.textContent = goal.target_date
    ? `Target date: ${goal.target_date} · ${formatMoney(goal.remaining)} to go`
    : `${formatMoney(goal.remaining)} to go`;

  const actions = document.createElement("div");
  actions.className = "goal-actions";
  if (goal.status !== "achieved") {
    const add = document.createElement("a");
    add.className = "primary-button";
    add.href = `/add-savings?goal=${encodeURIComponent(goal.id)}`;
    add.textContent = "Add money";
    actions.appendChild(add);
  }
  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "delete-button";
  remove.dataset.action = "delete-goal";
  remove.dataset.id = goal.id;
  remove.textContent = "Delete";
  actions.appendChild(remove);

  card.appendChild(top);
  card.appendChild(saved);
  card.appendChild(goalProgressBar(goal));
  card.appendChild(note);
  card.appendChild(dateNote);
  card.appendChild(actions);
  return card;
}

function buildGoalMini(goal) {
  const item = document.createElement("div");
  item.className = "goal-mini";
  const top = document.createElement("div");
  top.className = "goal-mini-top";
  const name = document.createElement("strong");
  name.textContent = goal.name;
  const amount = document.createElement("span");
  amount.textContent = `${formatMoney(goal.saved)} / ${formatMoney(goal.target_amount)}`;
  top.appendChild(name);
  top.appendChild(amount);
  item.appendChild(top);
  item.appendChild(goalProgressBar(goal));
  return item;
}

function renderEmpty(container, text) {
  container.innerHTML = "";
  const empty = document.createElement("p");
  empty.className = "empty-state";
  empty.textContent = text;
  container.appendChild(empty);
}

async function loadGoals() {
  const page = document.getElementById("goals-list");
  const preview = document.getElementById("goals-preview");
  if (!page && !preview) {
    return;
  }

  try {
    const result = await apiFetch("/goals");
    if (!result.ok) {
      throw new Error(errorMessage(result.data, "Unable to load goals"));
    }
    const goals = result.data;

    if (page) {
      page.innerHTML = "";
      if (goals.length === 0) {
        renderEmpty(
          page,
          "No goals yet. Create your first one and start saving towards it.",
        );
      } else {
        goals.forEach(function (goal) {
          page.appendChild(buildGoalCard(goal));
        });
      }
    }

    if (preview) {
      preview.innerHTML = "";
      if (goals.length === 0) {
        renderEmpty(preview, "No goals yet. Pick something to save for.");
      } else {
        goals.slice(0, 3).forEach(function (goal) {
          preview.appendChild(buildGoalMini(goal));
        });
      }
    }
  } catch (error) {
    console.error(error);
    if (page) {
      renderEmpty(page, "Unable to load goals.");
    }
    if (preview) {
      renderEmpty(preview, "Unable to load goals.");
    }
  }
}

async function deleteGoal(id) {
  if (
    !confirm(
      "Delete this goal? The money you already saved towards it stays in your savings.",
    )
  ) {
    return;
  }
  try {
    const result = await apiFetch(`/goals/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });
    if (result.ok) {
      showMessage("goals-message", "Goal deleted", "success");
      await loadGoals();
    } else {
      showMessage(
        "goals-message",
        errorMessage(result.data, "Unable to delete goal"),
        "error",
      );
    }
  } catch (error) {
    showMessage("goals-message", "Unable to delete goal", "error");
  }
}

document.addEventListener("DOMContentLoaded", function () {
  const dateInput = document.getElementById("goal-date");
  if (dateInput) {
    dateInput.min = todayISO();
  }

  bindSimpleForm({
    formId: "goal-form",
    endpoint: "/goals",
    messageId: "goal-message",
    successText: "Goal created",
    failText: "Unable to create goal",
    redirectTo: "/goals-page",
    buildPayload: function () {
      const date = document.getElementById("goal-date").value;
      return {
        name: document.getElementById("goal-name").value.trim(),
        target_amount: Number(document.getElementById("goal-amount").value),
        target_date: date || null,
      };
    },
  });

  const list = document.getElementById("goals-list");
  if (list) {
    list.addEventListener("click", function (event) {
      const button = event.target.closest('button[data-action="delete-goal"]');
      if (button) {
        deleteGoal(button.dataset.id);
      }
    });
  }

  loadGoals();
});
