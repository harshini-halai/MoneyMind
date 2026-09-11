from database import get_connection


def view_balance():

    connection = get_connection()
    cursor = connection.cursor()

    # Get total income
    income_query = """
    SELECT COALESCE(SUM(amount), 0)
    FROM transactions
    WHERE type = 'income'
    """

    cursor.execute(income_query)

    total_income = cursor.fetchone()[0]

    # Get total expenses
    expense_query = """
    SELECT COALESCE(SUM(amount), 0)
    FROM transactions
    WHERE type = 'expense'
    """

    cursor.execute(expense_query)

    total_expenses = cursor.fetchone()[0]

    balance = total_income - total_expenses

    print("\nIncome: ₹", total_income)
    print("Total Spending: ₹", total_expenses)
    print("Balance: ₹", balance)

    cursor.close()
    connection.close()


def category_totals():

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    SELECT category, SUM(amount)
    FROM transactions
    WHERE type = 'expense'
    GROUP BY category
    """

    cursor.execute(query)

    categories = cursor.fetchall()

    print("\nCategory Totals:")

    if len(categories) == 0:

        print("No expenses found")

    else:

        for category in categories:

            print(
                category[0],
                "- ₹",
                category[1]
            )

    cursor.close()
    connection.close()


def category_percentages():

    connection = get_connection()
    cursor = connection.cursor()

    query = """
    SELECT category, SUM(amount)
    FROM transactions
    WHERE type = 'expense'
    GROUP BY category
    """

    cursor.execute(query)

    categories = cursor.fetchall()

    if len(categories) == 0:

        print("\nNo expenses found")

        cursor.close()
        connection.close()

        return

    total_query = """
    SELECT COALESCE(SUM(amount), 0)
    FROM transactions
    WHERE type = 'expense'
    """

    cursor.execute(total_query)

    total_spending = cursor.fetchone()[0]

    print("\nCategory Spending Percentage:")

    for category in categories:

        category_name = category[0]
        category_total = category[1]

        percentage = (category_total / total_spending) * 100

        print(
            category_name,
            "- ₹",
            category_total,
            "-",
            round(percentage, 2),
            "%"
        )

    cursor.close()
    connection.close()