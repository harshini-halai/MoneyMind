// Khata chat page: ask questions about your own money, see proactive insights.

function addBubble(text, who) {
  const log = document.getElementById("chat-log");
  const bubble = document.createElement("div");
  bubble.className = `bubble ${who}`;
  bubble.textContent = text;
  log.appendChild(bubble);
  log.scrollTop = log.scrollHeight;
  return bubble;
}

function renderChips(questions) {
  const holder = document.getElementById("chat-suggestions");
  holder.innerHTML = "";
  (questions || []).forEach(function (question) {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "chip";
    chip.textContent = question;
    chip.addEventListener("click", function () {
      askKhata(question);
    });
    holder.appendChild(chip);
  });
}

let khataBusy = false;

async function askKhata(question) {
  const text = String(question || "").trim();
  if (!text || khataBusy) {
    return;
  }
  khataBusy = true;

  const input = document.getElementById("chat-input");
  const send = document.getElementById("chat-send");
  input.value = "";
  send.disabled = true;

  addBubble(text, "user");
  const typing = addBubble("Khata is checking your numbers...", "khata typing");

  try {
    const result = await apiFetch("/khata/ask", {
      method: "POST",
      body: JSON.stringify({ question: text }),
    });
    typing.remove();
    if (result.ok) {
      addBubble(result.data.answer, "khata");
      if (result.data.suggestions) {
        renderChips(result.data.suggestions);
      }
    } else {
      addBubble(
        errorMessage(result.data, "Sorry, I could not answer that right now."),
        "khata",
      );
    }
  } catch (error) {
    typing.remove();
    addBubble("Sorry, I could not answer that right now.", "khata");
  }

  khataBusy = false;
  send.disabled = false;
  input.focus();
}

async function loadKhataInsights() {
  const list = document.getElementById("insights-list");
  try {
    const result = await apiFetch("/khata/insights");
    if (!result.ok) {
      throw new Error("insights failed");
    }
    renderInsights(result.data.insights);
    renderChips(result.data.suggested_questions);
  } catch (error) {
    console.error(error);
    list.innerHTML = "";
    const failed = document.createElement("li");
    failed.className = "empty-state";
    failed.textContent = "Insights are not available right now.";
    list.appendChild(failed);
  }
}

// renderInsights() lives in script.js, so this page loads script.js too.
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("chat-form");
  if (!form) {
    return;
  }

  addBubble(
    "Hi, I am Khata. Ask me about your balance, spending, budgets, goals or bills. " +
      "You can write in English or Hinglish.",
    "khata",
  );

  form.addEventListener("submit", function (event) {
    event.preventDefault();
    askKhata(document.getElementById("chat-input").value);
  });

  loadKhataInsights();
});
