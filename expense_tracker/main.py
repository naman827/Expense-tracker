# importing required modules
import json
import os
from datetime import datetime

DATA_FILE = "expense.json"

def load_expenses():
    #load the expenses from the json file
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError:
        return []

def save_expenses(expenses):
    #save expenses to json file
    with open(DATA_FILE,"w", encoding="utf-8") as file:
        json.dump(expenses,file,indent=4)


def add_expenses(expenses):
    #add a new expense to the expense tracker
    print("\n Add new expense")
    while True:
        try:
            amount=float(input("Enter the amount spent($): "))
            if amount <=0:
                print("Amount should be greater than 0.please try again")
            break
        except ValueError:
            print("invalid input.please enter a valid number.")
    
    category=input("Enter category eg: Food, Transport, Entertainment: ").strip().capitalize()

    description=input("Enter the brief description of the expense: ").strip()

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    expense={
        "amount":amount,
        "category":category,
        "description":description,
        "date":date_str
    }

    expenses.append(expense)
    save_expenses(expenses)
    print(f"Successfully added ${amount:.2f} under '{category}")

def view_expenses(expenses):
    #display all expenses in a formatted format
    print("\n All expenses")

    if not expenses:
        print("No expenses found yet.")
        return
    
    print(f"{'Date':<18} | {'Category':<15} | {'Amount':<10} | {'Description'}")
    print("-"*65)

    total = 0
    for exp in expenses:
        print(f"{exp['date']:<18} | {exp['category']:<15} | ${exp['amount']:<9.2f} | {exp['description']}")
        total += exp["amount"]

    print("-"*65)
    print(f"{'Total spent':<36} | ${total:.2f}")

def show_summary(expenses):
    #display a full summary of all the expenses added
    print("\n data available to summarize")
    if not expenses:
        print("No data available to summarize")
        return
    summary={}
    for exp in expenses:
        cat=exp["category"]
        summary[cat]=summary.get(cat,0)+exp["amount"]

    for cat,total in summary.items():
        print(f".{cat}:${total:.2f}")
    
def main():
    #main function to run expense tracker application
    expenses = load_expenses()

    while True:
        print("\n======================")
        print(" PERSONAL EXPENSE TRACKER ")
        print("========================")
        print("1. Add an expense")
        print("2. View all expenses")
        print("3. View category summary")
        print("4. Exit")

        choice = input("choose an option (1-4): ").strip()

        if choice == "1":
            add_expenses(expenses)
        elif choice == "2":
            view_expenses(expenses)
        elif choice == "3":
            show_summary(expenses)
        elif choice == "4":
            print("\n thanks. stay on budget: 💰")
            break
        else:
            print("Invalid choice. please try again")

if __name__=="__main__":
    main()
