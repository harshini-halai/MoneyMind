expenses = []


def add_expense():
    description = input("Enter description: ")
    amount = int(input("Enter amount: "))

    expenses.append({
        "description": description,
        "amount": amount
    })

    print("Expense added")


def add_income():
    income = int(input("Enter your income: "))
    return income


while True:

    add_expense()

    while True:
        choice = input("Aur kharcha? yes/no: ").lower()

        if choice == "yes":
            break

        elif choice == "no":
            break

        else:
            print("Enter valid choice: yes or no")

    if choice == "no":
        break


print("\nYour Expenses:")

for expense in expenses:
    print(expense.get("description"), "- ₹", expense.get("amount"))


total = 0

for expense in expenses:
    total = total + expense.get("amount")

print("\nTotal Spending: ₹", total)


income = add_income()

balance = income - total

print("Income: ₹", income)
print("Balance: ₹", balance)