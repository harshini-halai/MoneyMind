document.addEventListener("DOMContentLoaded", function () {
  setDefaultDate("emergency-fund-date");

  bindSimpleForm({
    formId: "emergency-fund-form",
    endpoint: "/emergency-fund",
    messageId: "emergency-fund-message",
    successText: "Emergency fund added successfully",
    failText: "Unable to add emergency fund",
    buildPayload: function () {
      return {
        amount: Number(document.getElementById("emergency-fund-amount").value),
        description: document
          .getElementById("emergency-fund-description")
          .value.trim(),
        date: document.getElementById("emergency-fund-date").value,
      };
    },
  });
});
