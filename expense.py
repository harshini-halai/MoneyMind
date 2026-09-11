from datetime import datetime
from database import get_connection


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

        transaction_date = datetime.now().strftime("%Y-%m-%d")

        # Connect to MySQL
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

        print("Expense added successfully")

        choice = input("Add another expense? yes/no: ").lower()

        if choice == "no":
            return


def view_expenses():

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    SELECT description, category, amount, date
    FROM transactions
    WHERE type = 'expense'
    ORDER BY date DESC
    """

    cursor.execute(query)

    expenses = cursor.fetchall()

    print("\nYour Expenses:")

    if len(expenses) == 0:
        print("No expenses found")

    else:

        for expense in expenses:

            print(
                expense[0],
                "-",
                expense[1],
                "- ₹",
                expense[2],
                "-",
                expense[3]
            )

    cursor.close()
    connection.close()


def view_expenses_by_category():

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

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    SELECT description, amount, date
    FROM transactions
    WHERE type = 'expense'
    AND category = %s
    ORDER BY date DESC
    """

    cursor.execute(query, (selected_category,))

    expenses = cursor.fetchall()

    print("\n", selected_category, "Expenses:")

    if len(expenses) == 0:

        print("No expenses found in this category")

    else:

        total = 0

        for expense in expenses:

            print(
                expense[0],
                "- ₹",
                expense[1],
                "-",
                expense[2]
            )

            total += expense[1]

        print("Total", selected_category, "Spending: ₹", total)

    cursor.close()
    connection.close()


def view_expenses_by_date():

    selected_date = input("Enter date (YYYY-MM-DD): ")

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    SELECT description, category, amount
    FROM transactions
    WHERE type = 'expense'
    AND date = %s
    """

    cursor.execute(query, (selected_date,))

    expenses = cursor.fetchall()

    print("\nExpenses on", selected_date, ":")

    if len(expenses) == 0:

        print("No expenses found for this date")

    else:

        total = 0

        for expense in expenses:

            print(
                expense[0],
                "-",
                expense[1],
                "- ₹",
                expense[2]
            )

            total += expense[2]

        print("Total Spending: ₹", total)

    cursor.close()
    connection.close()