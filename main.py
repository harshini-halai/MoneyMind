expenses = []

while True:
    description = input("Enter description: ")
    amount = int(input("Enter amount: "))

    expenses.append({
        "description": description,
        "amount": amount
    })

    print("Expense added! 💸")

    choice = input("Aur kharcha? yes/no: ")

    if choice == "no":
        break

print("\nYour Expenses:")

for expense in expenses:
    print(expense.get("description"), "- ₹", expense.get("amount"))