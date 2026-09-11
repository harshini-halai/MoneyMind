from datetime import datetime
from database import get_connection

# Store all expenses
expenses = []

# Store total income
income = 0


def add_expense():

    while True:

        description = input("Enter description: ")

        # Category selection
        while True:
            print("\nSelect Category:")
            print("1. Food")
            print("2. Travel")
            print("3. Shopping")
            print("4. Bills")
            print("5. Other")

            category_choice = input("Enter category choice: ")

            if category_choice == "1":
                category = "Food"
                break

            elif category_choice == "2":
                category = "Travel"
                break

            elif category_choice == "3":
                category = "Shopping"
                break

            elif category_choice == "4":
                category = "Bills"
                break

            elif category_choice == "5":
                category = "Other"
                break

            else:
                print("Enter a valid category choice")

        # Amount validation
        while True:
            try:
                amount = int(input("Enter amount: "))

                if amount > 0:
                    break
                else:
                    print("Amount should be positive")

            except ValueError:
                print("Please enter a valid number")

        # Save expense
        expenses.append({
            "description": description,
            "category": category,
            "amount": amount,
            "date": datetime.now().strftime("%Y-%m-%d")
        })

        # Save expense to MySQL
        connection = get_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO transactions
        (description, category, amount, date, type)
        VALUES (%s, %s, %s, %s, %s)
        """

        data = (
            description,
            category,
            amount,
            datetime.now().strftime("%Y-%m-%d"),
            "expense"
        )

        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()

        print("Expense added")

        # Add another expense
        while True:
            choice = input("Add another expense? yes/no: ").lower()

            if choice == "yes":
                break

            elif choice == "no":
                return

            else:
                print("Enter valid choice: yes or no")


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


def view_expenses():

    print("\nYour Expenses:")

    if len(expenses) == 0:
        print("No expenses found")

    else:
        # Display all expenses
        for expense in expenses:
            print(
                expense.get("description"),
                "-",
                expense.get("category"),
                "- ₹",
                expense.get("amount"),
                "-",
                expense.get("date")
            )


def view_balance():

    total = 0

    # Calculate total spending
    for expense in expenses:
        total = total + expense.get("amount")

    # Calculate remaining balance
    balance = income - total

    print("\nIncome: ₹", income)
    print("Total Spending: ₹", total)
    print("Balance: ₹", balance)


def category_totals():

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


def view_expenses_by_category():

    # Select category
    while True:
        print("\nSelect Category:")
        print("1. Food")
        print("2. Travel")
        print("3. Shopping")
        print("4. Bills")
        print("5. Other")

        category_choice = input("Enter category choice: ")

        if category_choice == "1":
            selected_category = "Food"
            break

        elif category_choice == "2":
            selected_category = "Travel"
            break

        elif category_choice == "3":
            selected_category = "Shopping"
            break

        elif category_choice == "4":
            selected_category = "Bills"
            break

        elif category_choice == "5":
            selected_category = "Other"
            break

        else:
            print("Enter a valid category choice")

    print("\n", selected_category, "Expenses:")

    total = 0
    found = False

    # Find expenses of selected category
    for expense in expenses:

        if expense.get("category") == selected_category:

            print(
                expense.get("description"),
                "- ₹",
                expense.get("amount"),
                "-",
                expense.get("date")
            )

            total = total + expense.get("amount")
            found = True

    if found == False:
        print("No expenses found in this category")

    print("Total", selected_category, "Spending: ₹", total)


def category_percentages():

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


def view_expenses_by_date():

    # Get date from user
    selected_date = input("Enter date (YYYY-MM-DD): ")

    print("\nExpenses on", selected_date, ":")

    total = 0
    found = False

    # Find expenses of selected date
    for expense in expenses:

        if expense.get("date") == selected_date:

            print(
                expense.get("description"),
                "-",
                expense.get("category"),
                "- ₹",
                expense.get("amount")
            )

            total = total + expense.get("amount")
            found = True

    if found == False:
        print("No expenses found for this date")

    print("Total Spending:", "₹", total)


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
        add_expense()

    elif choice == "3":
        view_expenses()

    elif choice == "4":
        view_balance()

    elif choice == "5":
        category_totals()

    elif choice == "6":
        view_expenses_by_category()

    elif choice == "7":
        category_percentages()

    elif choice == "8":
        view_expenses_by_date()

    elif choice == "9":
        print("Thank you for using MoneyMind!")
        break

    else:
        print("Enter a valid choice")