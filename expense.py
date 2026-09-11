from datetime import datetime
from database import get_connection


def add_expense(expenses):

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

        # Get current date
        transaction_date = datetime.now().strftime("%Y-%m-%d")

        # Save expense temporarily in Python list
        expenses.append({
            "description": description,
            "category": category,
            "amount": amount,
            "date": transaction_date
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
            transaction_date,
            "expense"
        )

        cursor.execute(query, data)
        connection.commit()

        cursor.close()
        connection.close()

        print("Expense added")

        # Add another expense
        while True:
            choice = input("Aur kharcha? yes/no: ").lower()

            if choice == "yes":
                break

            elif choice == "no":
                return

            else:
                print("Enter valid choice: yes or no")


def view_expenses(expenses):

    print("\nYour Expenses:")

    if len(expenses) == 0:
        print("No expenses found")

    else:
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


def view_expenses_by_category(expenses):

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


def view_expenses_by_date(expenses):

    selected_date = input("Enter date (YYYY-MM-DD): ")

    print("\nExpenses on", selected_date, ":")

    total = 0
    found = False

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

    print("Total Spending: ₹", total)