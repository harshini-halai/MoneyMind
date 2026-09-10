from expense import (
    add_expense,
    view_expenses,
    view_expenses_by_category,
    view_expenses_by_date
)

from analysis import (
    view_balance,
    category_totals,
    category_percentages
)


# Store all expenses
expenses = []

# Store total income
income = 0


def add_income():

    global income

    # Income validation
    while True:
        try:
            amount = int(input("Enter income: "))

            if amount > 0:
                break
            else:
                print("Income should be positive")

        except ValueError:
            print("Please enter a valid number")

    # Update income
    income = income + amount

    print("Income added")


# Main Menu
while True:

    print("\n===== MoneyMind =====")
    print("1. Add Income")
    print("2. Add Expense")
    print("3. View Expenses")
    print("4. View Balance")
    print("5. Category Totals")
    print("6. View Expenses by Category")
    print("7. Category Spending Percentage")
    print("8. View Expenses by Date")
    print("9. Exit")

    choice = input("Enter your choice: ")

    if choice == "1":
        add_income()

    elif choice == "2":
        add_expense(expenses)

    elif choice == "3":
        view_expenses(expenses)

    elif choice == "4":
        view_balance(expenses, income)

    elif choice == "5":
        category_totals(expenses)

    elif choice == "6":
        view_expenses_by_category(expenses)

    elif choice == "7":
        category_percentages(expenses)

    elif choice == "8":
        view_expenses_by_date(expenses)

    elif choice == "9":
        print("Thank you for using MoneyMind!")
        break

    else:
        print("Enter a valid choice")