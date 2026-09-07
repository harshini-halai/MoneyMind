expenses = []

description = input("Enter description: ")
amount = int(input("Enter amount: "))

expenses.append({
    "description": description,
    "amount": amount
})

for expense in expenses:
    print(expense.get("description"), "- ₹", expense.get("amount"))