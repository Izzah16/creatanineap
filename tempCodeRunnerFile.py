import tkinter as tk
from tkinter import messagebox

class ChemistryCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chemistry Calculator")
        self.root.geometry("500x400")
        
        # Heading
        tk.Label(root, text="Chemistry Calculator", font=("Arial", 16)).pack(pady=10)
        
        # Stock Solution Preparation
        tk.Label(root, text="Stock Solution Preparation", font=("Arial", 12)).pack(pady=5)
        self.stock_conc = tk.Entry(root)
        self.stock_conc.insert(0, "Stock Concentration (M)")
        self.stock_conc.pack()
        
        self.desired_conc = tk.Entry(root)
        self.desired_conc.insert(0, "Desired Concentration (M)")
        self.desired_conc.pack()
        
        self.desired_vol = tk.Entry(root)
        self.desired_vol.insert(0, "Desired Volume (L)")
        self.desired_vol.pack()
        
        tk.Button(root, text="Calculate Stock Volume", command=self.calculate_stock_volume).pack(pady=10)
        
        # Standard Solution Preparation
        tk.Label(root, text="Standard Solution Preparation", font=("Arial", 12)).pack(pady=5)
        self.standard_conc = tk.Entry(root)
        self.standard_conc.insert(0, "Standard Concentration (M)")
        self.standard_conc.pack()
        
        self.standard_vol = tk.Entry(root)
        self.standard_vol.insert(0, "Volume (L)")
        self.standard_vol.pack()
        
        tk.Button(root, text="Calculate Solute Mass", command=self.calculate_solute_mass).pack(pady=10)
        
        # Result display
        self.result_label = tk.Label(root, text="", font=("Arial", 10))
        self.result_label.pack(pady=20)
    
    def calculate_stock_volume(self):
        try:
            stock_concentration = float(self.stock_conc.get())
            desired_concentration = float(self.desired_conc.get())
            desired_volume = float(self.desired_vol.get())
            
            # Calculate volume needed from stock solution
            stock_volume = (desired_concentration * desired_volume) / stock_concentration
            self.result_label.config(text=f"Volume of stock needed: {stock_volume:.4f} L")
        
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for the concentrations and volume.")
    
    def calculate_solute_mass(self):
        try:
            standard_concentration = float(self.standard_conc.get())
            volume = float(self.standard_vol.get())
            
            # Assuming molar mass is required and given; for demo purposes, we'll assume a value or add a prompt for input
            molar_mass = 58.44  # example for NaCl in g/mol
            solute_mass = standard_concentration * volume * molar_mass
            self.result_label.config(text=f"Mass of solute needed: {solute_mass:.4f} g")
        
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for the concentration and volume.")
        
if __name__ == "__main__":
    root = tk.Tk()
    app = ChemistryCalculatorApp(root)
    root.mainloop()
