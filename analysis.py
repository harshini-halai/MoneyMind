def view_balance(expenses, income):

    total = 0

    # Calculate total spending
    for expense in expenses:
        total = total + expense.get("amount")

    # Calculate remaining balance
    balance = income - total

    print("\nIncome: ₹", income)
    print("Total Spending: ₹", total)
    print("Balance: ₹", balance)


def category_totals(expenses):

    category_totals = {}

    # Calculate category-wise spending
    for expense in expenses:
        category = expense.get("category")
        amount = expense.get("amount")

        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    print("\nCategory Totals:")

    # Display category totals
    for category, total in category_totals.items():
        print(category, "- ₹", total)


def category_percentages(expenses):

    total_spending = 0

    # Calculate total spending
    for expense in expenses:
        total_spending = total_spending + expense.get("amount")

    if total_spending == 0:
        print("\nNo expenses found")
        return

    # Store category totals
    category_totals = {}

    for expense in expenses:
        category = expense.get("category")
        amount = expense.get("amount")

        if category in category_totals:
            category_totals[category] += amount
        else:
            category_totals[category] = amount

    print("\nCategory Spending Percentage:")

    # Calculate percentage
    for category, total in category_totals.items():
        percentage = (total / total_spending) * 100

        print(
            category,
            "- ₹",
            total,
            "-",
            round(percentage, 2),
            "%"
        )