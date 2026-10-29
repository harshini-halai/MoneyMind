document.addEventListener("DOMContentLoaded", function () {
  setDefaultDate("upcoming-date");

  bindSimpleForm({
    formId: "upcoming-form",
    endpoint: "/upcoming-expenses",
    messageId: "upcoming-message",
    successText: "Upcoming expense added successfully",
    failText: "Unable to add upcoming expense",
    buildPayload: function () {
      return {
        amount: Number(document.getElementById("upcoming-amount").value),
        description: document
          .getElementById("upcoming-description")
          .value.trim(),
        due_date: document.getElementById("upcoming-date").value,
      };
    },
  });
});
