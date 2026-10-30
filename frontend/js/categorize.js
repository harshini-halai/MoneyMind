// Add Expense page: suggests a category while you type the description,
// based on the categories you chose for similar expenses before.

document.addEventListener("DOMContentLoaded", function () {
  const description = document.getElementById("expense-description");
  const category = document.getElementById("expense-category");
  const hint = document.getElementById("category-hint");

  if (!description || !category) {
    return;
  }

  let timer = null;
  let latestRequest = 0;
  let userChoseCategory = false;

  // Once you pick a category yourself, we stop changing it.
  category.addEventListener("change", function () {
    userChoseCategory = true;
  });

  function setHint(text) {
    if (hint) {
      hint.textContent = text;
    }
  }

  async function fetchSuggestion(text) {
    const thisRequest = ++latestRequest;

    try {
      const result = await apiFetch(
        `/categories/suggest?description=${encodeURIComponent(text)}`,
      );

      // Ignore stale answers and answers that arrive after you chose.
      if (thisRequest !== latestRequest || !result.ok || userChoseCategory) {
        return;
      }

      const suggestion = result.data;
      if (suggestion.source === "default") {
        setHint("");
        return;
      }

      category.value = suggestion.category;
      setHint(
        suggestion.source === "learned"
          ? `Suggested from your past choices: ${suggestion.category}`
          : `Suggested: ${suggestion.category}`,
      );
    } catch (error) {
      // Suggestions are optional, so a failure is silently ignored.
    }
  }

  description.addEventListener("input", function () {
    clearTimeout(timer);
    const text = description.value.trim();

    if (text.length < 3) {
      setHint("");
      return;
    }

    timer = setTimeout(function () {
      fetchSuggestion(text);
    }, 400);
  });
});
