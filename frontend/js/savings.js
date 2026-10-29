document.addEventListener("DOMContentLoaded", function () {
  setDefaultDate("savings-date");

  bindSimpleForm({
    formId: "savings-form",
    endpoint: "/savings",
    messageId: "savings-message",
    successText: "Savings added successfully",
    failText: "Unable to add savings",
    buildPayload: function () {
      return {
        amount: Number(document.getElementById("savings-amount").value),
        description: document
          .getElementById("savings-description")
          .value.trim(),
        date: document.getElementById("savings-date").value,
      };
    },
  });
});
