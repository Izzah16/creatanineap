import tkinter as tk
from tkinter import ttk, messagebox
import math

class PlaceholderEntry(tk.Entry):
    def __init__(self, master=None, placeholder="Enter text", color='grey', *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.placeholder = placeholder
        self.placeholder_color = color
        self.default_fg_color = self['fg']
        self.bind("<FocusIn>", self.foc_in)
        self.bind("<FocusOut>", self.foc_out)
        self.put_placeholder()

    def put_placeholder(self):
        self.insert(0, self.placeholder)
        self['fg'] = self.placeholder_color

    def foc_in(self, *args):
        if self['fg'] == self.placeholder_color:
            self.delete(0, 'end')
            self['fg'] = self.default_fg_color

    def foc_out(self, *args):
        if not self.get():
            self.put_placeholder()

class ChemistryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Chemistry Solution Calculator")
        self.root.geometry("1000x700")
        self.style = ttk.Style()
        self.style.theme_use("clam")
        
        # Set chemistry-themed colors
        self.bg_color = "#2C3E50"
        self.fg_color = "#ECF0F1"
        self.entry_bg = "#34495E"
        self.entry_fg = "#ECF0F1"
        self.highlight_color = "#3498DB"
        
        self.root.configure(bg=self.bg_color)
        self.style.configure("TNotebook", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Arial", 11))
        self.style.configure("TButton", background=self.highlight_color, foreground=self.fg_color)
        self.style.configure("TEntry", fieldbackground=self.entry_bg, foreground=self.entry_fg)
        
        self.setup_tabs()

    def setup_tabs(self):
        self.tab_control = ttk.Notebook(self.root)
        
        # Stock Solution Preparation Tab
        self.stock_tab = self.create_tab("Stock Solution Prep")
        self.build_stock_solution_tab(self.stock_tab)
        
        # Dilution Calculation Tab
        self.dilution_tab = self.create_tab("Dilution Calc")
        self.build_dilution_tab(self.dilution_tab)
        
        # Redox Calculations Tab
        self.redox_tab = self.create_tab("Redox Calc")
        self.build_redox_tab(self.redox_tab)
        
        # pH Calculations Tab
        self.ph_tab = self.create_tab("pH Calc")
        self.build_ph_tab(self.ph_tab)
        
        # Inventory Management Tab
        self.inventory_tab = self.create_tab("Inventory Management")
        self.build_inventory_tab(self.inventory_tab)
        
        self.tab_control.pack(expand=1, fill="both")

    def create_tab(self, title):
        tab = ttk.Frame(self.tab_control, style="TFrame")
        self.tab_control.add(tab, text=title)
        return tab

    # Stock Solution Preparation Tab
    def build_stock_solution_tab(self, tab):
        ttk.Label(tab, text="Stock Solution Preparation", font=("Arial", 14)).pack(pady=10)
        
        stock_concentration_label = ttk.Label(tab, text="Stock Concentration (M):")
        stock_concentration_label.pack()
        stock_entry = PlaceholderEntry(tab, "Enter stock concentration", fg="grey")
        stock_entry.pack()

        volume_label = ttk.Label(tab, text="Volume Required (L):")
        volume_label.pack()
        volume_entry = PlaceholderEntry(tab, "Enter volume", fg="grey")
        volume_entry.pack()
        
        calculate_button = ttk.Button(tab, text="Calculate Moles", command=lambda: self.calculate_moles(stock_entry, volume_entry))
        calculate_button.pack(pady=10)

    def calculate_moles(self, stock_entry, volume_entry):
        try:
            concentration = float(stock_entry.get())
            volume = float(volume_entry.get())
            moles = concentration * volume
            messagebox.showinfo("Moles Calculation", f"Moles required: {moles} mol")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for concentration and volume.")

    # Dilution Calculation Tab
    def build_dilution_tab(self, tab):
        ttk.Label(tab, text="Dilution Calculation", font=("Arial", 14)).pack(pady=10)
        
        initial_conc_label = ttk.Label(tab, text="Initial Concentration (M):")
        initial_conc_label.pack()
        initial_conc_entry = PlaceholderEntry(tab, "Enter initial concentration", fg="grey")
        initial_conc_entry.pack()
        
        final_conc_label = ttk.Label(tab, text="Final Concentration (M):")
        final_conc_label.pack()
        final_conc_entry = PlaceholderEntry(tab, "Enter final concentration", fg="grey")
        final_conc_entry.pack()
        
        calculate_button = ttk.Button(tab, text="Calculate Volume", command=lambda: self.calculate_dilution(initial_conc_entry, final_conc_entry))
        calculate_button.pack(pady=10)

    def calculate_dilution(self, initial_conc_entry, final_conc_entry):
        try:
            initial_conc = float(initial_conc_entry.get())
            final_conc = float(final_conc_entry.get())
            if final_conc > initial_conc:
                messagebox.showerror("Input Error", "Final concentration must be less than initial concentration.")
                return
            volume = initial_conc / final_conc
            messagebox.showinfo("Dilution Calculation", f"Dilution volume needed: {volume} L")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numbers for concentrations.")

    # Redox Calculation Tab
    def build_redox_tab(self, tab):
        ttk.Label(tab, text="Redox Calculations", font=("Arial", 14)).pack(pady=10)
        
        electrode_potential_label = ttk.Label(tab, text="Electrode Potential (V):")
        electrode_potential_label.pack()
        electrode_potential_entry = PlaceholderEntry(tab, "Enter electrode potential", fg="grey")
        electrode_potential_entry.pack()
        
        calculate_button = ttk.Button(tab, text="Calculate", command=lambda: self.calculate_redox(electrode_potential_entry))
        calculate_button.pack(pady=10)

    def calculate_redox(self, electrode_potential_entry):
        try:
            potential = float(electrode_potential_entry.get())
            # Assume sample calculation (e.g., calculate a potential shift)
            shifted_potential = potential + 0.059
            messagebox.showinfo("Redox Calculation", f"Shifted potential: {shifted_potential} V")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid number for electrode potential.")

    # pH Calculation Tab
    def build_ph_tab(self, tab):
        ttk.Label(tab, text="pH Calculations", font=("Arial", 14)).pack(pady=10)
        
        h_concentration_label = ttk.Label(tab, text="[H+] Concentration (M):")
        h_concentration_label.pack()
        h_concentration_entry = PlaceholderEntry(tab, "Enter H+ concentration", fg="grey")
        h_concentration_entry.pack()
        
        calculate_button = ttk.Button(tab, text="Calculate pH", command=lambda: self.calculate_ph(h_concentration_entry))
        calculate_button.pack(pady=10)

    def calculate_ph(self, h_concentration_entry):
        try:
            h_concentration = float(h_concentration_entry.get())
            if h_concentration <= 0:
                raise ValueError("Concentration must be positive.")
            ph = -math.log10(h_concentration)
            messagebox.showinfo("pH Calculation", f"Calculated pH: {ph}")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid, positive number for H+ concentration.")

    # Inventory Management Tab
    def build_inventory_tab(self, tab):
        ttk.Label(tab, text="Inventory Management", font=("Arial", 14)).pack(pady=10)
        
        # Additional inventory management features can be added here, such as tracking and alerts.

if __name__ == "__main__":
    root = tk.Tk()
    app = ChemistryApp(root)
    root.mainloop()
