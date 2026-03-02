import json
import os
from datetime import datetime

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def calculate_epf(total_received):
    # Total received is inclusive of employer EPF (13% of basic)
    # Total = Basic + 0.13 * Basic = 1.13 * Basic
    base_salary = total_received / 1.13
    employer_epf = round(base_salary * 0.13)
    employee_epf = round(base_salary * 0.11)
    total_epf = employer_epf + employee_epf
    net_salary = total_received - total_epf
    return base_salary, employer_epf, employee_epf, net_salary, total_epf

def input_data(data):
    try:
        total_received = float(input("\nEnter your total salary received (inclusive of employer EPF) (e.g. 5650): "))
    except ValueError:
        print("Invalid input. Please enter a valid number.")
        return

    base_salary, employer_epf, employee_epf, net_salary, total_epf = calculate_epf(total_received)
    
    print("\n--- EPF Details ---")
    print(f"Total Received: RM {total_received:.2f}")
    print(f"Derived Basic Salary: RM {base_salary:.2f}")
    print(f"Employer EPF (13% of basic): RM {employer_epf} (Contributed by employer, included in your total)")
    print(f"Employee EPF (11% of basic): RM {employee_epf} (Deducted from basic salary)")
    print(f"Total EPF Contribution: RM {total_epf}")
    print(f"Net Salary (After EPF): RM {net_salary:.2f}")
    
    try:
        saving_percentage = float(input("\nEnter saving percentage (e.g., 20 for 20%): "))
    except ValueError:
        print("Invalid input. Defaulting to 0%.")
        saving_percentage = 0.0
        
    saving_amount = net_salary * (saving_percentage / 100)
    remaining_balance = net_salary - saving_amount
    
    print(f"\n--- Saving Details ---")
    print(f"Saving Target ({saving_percentage}%): RM {saving_amount:.2f}")
    print(f"Remaining Balance to Spend: RM {remaining_balance:.2f}")
    
    save_option = input("\nDo you want to save this record? (y/n): ").strip().lower()
    if save_option == 'y':
        year = input("Enter Year (e.g., 2026) [Leave blank for current year]: ").strip()
        if not year:
            year = str(datetime.now().year)
            
        month = input("Enter Month (e.g., February or 02) [Leave blank for current month]: ").strip()
        if not month:
            month = datetime.now().strftime("%B")
            
        if year not in data:
            data[year] = {}
        
        data[year][month] = {
            "total_received": total_received,
            "basic_salary": base_salary,
            "employer_epf": employer_epf,
            "employee_epf": employee_epf,
            "total_epf": total_epf,
            "net_salary": net_salary,
            "saving_percentage": saving_percentage,
            "saving_amount": saving_amount,
            "remaining_balance": remaining_balance
        }
        
        save_data(data)
        print(f"Data for {month} {year} saved successfully!")

def check_data(data):
    if not data:
        print("\nNo data found. Please add some first.")
        return
        
    print("\n--- Saved Data ---")
    
    # Table Header
    heading = (
        f"{'Year':<6} | {'Month':<10} | {'Total Rcvd':<12} | {'Basic Salary':<12} | "
        f"{'Emplr EPF':<9} | {'Emply EPF':<9} | {'Total EPF':<9} | {'Net Salary':<12} | "
        f"{'Saving':<10} | {'Remaining':<12}"
    )
    print("=" * len(heading))
    print(heading)
    print("-" * len(heading))
    
    # Tracking Totals
    totals = {
        'total_received': 0, 'basic_salary': 0, 'employer_epf': 0,
        'employee_epf': 0, 'total_epf': 0, 'net_salary': 0,
        'saving_amount': 0, 'remaining_balance': 0
    }
    
    # Print Rows
    for year, months in sorted(data.items()):
        for month, details in months.items():
            tr = details.get('total_received', 0)
            bs = details.get('basic_salary', 0)
            er_epf = details.get('employer_epf', 0)
            ee_epf = details.get('employee_epf', 0)
            t_epf = details.get('total_epf', 0)
            ns = details.get('net_salary', 0)
            sv = details.get('saving_amount', 0)
            rb = details.get('remaining_balance', 0)
            
            # Accumulate totals
            totals['total_received'] += tr
            totals['basic_salary'] += bs
            totals['employer_epf'] += er_epf
            totals['employee_epf'] += ee_epf
            totals['total_epf'] += t_epf
            totals['net_salary'] += ns
            totals['saving_amount'] += sv
            totals['remaining_balance'] += rb
            
            # Format row strings
            row = (
                f"{year:<6} | {month:<10} | {tr:>12.2f} | {bs:>12.2f} | "
                f"{er_epf:>9} | {ee_epf:>9} | {t_epf:>9} | {ns:>12.2f} | "
                f"{sv:>10.2f} | {rb:>12.2f}"
            )
            print(row)
            
    print("-" * len(heading))
    
    # Format and print Total Row
    total_row = (
        f"{'TOTAL':<6} | {'':<10} | {totals['total_received']:>12.2f} | {totals['basic_salary']:>12.2f} | "
        f"{totals['employer_epf']:>9} | {totals['employee_epf']:>9} | {totals['total_epf']:>9} | {totals['net_salary']:>12.2f} | "
        f"{totals['saving_amount']:>10.2f} | {totals['remaining_balance']:>12.2f}"
    )
    print(total_row)
    print("=" * len(heading))

def main():
    data = load_data()
    
    while True:
        print("\n=== Income, EPF & Saving Calculator ===")
        print("1. Input new data")
        print("2. Check saved data")
        print("3. Exit")
        
        choice = input("Enter your choice (1/2/3): ").strip()
        
        if choice == '1':
            input_data(data)
        elif choice == '2':
            check_data(data)
        elif choice == '3':
            print("Exiting. Have a great day!")
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()
