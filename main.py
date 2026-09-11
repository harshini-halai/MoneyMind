from datetime import datetime

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

from database import get_connection


def add_income():

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

    transaction_date = datetime.now().strftime("%Y-%m-%d")

    # Save income to MySQL
    connection = get_connection()
    cursor = connection.cursor()

    query = """
    INSERT INTO transactions
    (description, category, amount, date, type)
    VALUES (%s, %s, %s, %s, %s)
    """

    data = (
        "Income",
        "Income",
        amount,
        transaction_date,
        "income"
    )

    cursor.execute(query, data)

    connection.commit()

    cursor.close()
    connection.close()

    print("Income added successfully")


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