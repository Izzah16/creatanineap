import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.neural_network import MLPRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from tkinter import Tk, Button, Label, messagebox

class CholestroCalcApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CholestroCalc")

        # Load the DPV data from the Excel file
        self.oxy_dpv_data = pd.read_excel('OXY DPV.xlsx', header=[0, 1])  # Update the path accordingly

        # Prepare data for model training
        self.prepare_data()

        # Create UI elements
        self.create_ui()

    def prepare_data(self):
        # Flatten the multi-level columns
        self.oxy_dpv_data.columns = ['_'.join(col).strip() for col in self.oxy_dpv_data.columns.values]

        # Extract the concentration values
        concentrations = self.oxy_dpv_data['Concentration'].values

        # Create a list to hold the features and targets
        features = []
        targets = []

        # Iterate over the columns to extract voltage and current values
        for i in range(1, len(self.oxy_dpv_data.columns), 2):
            voltage_col = self.oxy_dpv_data.columns[i]
            current_col = self.oxy_dpv_data.columns[i + 1]

            # Append voltage and current readings to features
            for j in range(len(self.oxy_dpv_data)):
                features.append([self.oxy_dpv_data[voltage_col][j], self.oxy_dpv_data[current_col][j]])
                targets.append(concentrations[j])

        # Convert features and targets to numpy arrays
        self.X = np.array(features)
        self.y = np.array(targets)

        # Split the data into training and testing sets (80% train, 20% test)
        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(self.X, self.y, test_size=0.2, random_state=42)

        # Train models and evaluate performance
        self.models = {
            'GBoost': GradientBoostingRegressor(),
            'MLP': MLPRegressor(max_iter=1000),
            'Linear Regression': LinearRegression(),
            'Random Forest': RandomForestRegressor()
        }
        self.model_performance = {}
        for name, model in self.models.items():
            model.fit(self.X_train, self.y_train)
            predictions = model.predict(self.X_test)
            mse = mean_squared_error(self.y_test, predictions)
            self.model_performance[name] = mse

        # Select the best model
        self.best_model_name = min(self.model_performance, key=self.model_performance.get)
        self.best_model = self.models[self.best_model_name]

    def create_ui(self):
        # Create a button to get results
        self.get_results_button = Button(self.root, text="Get Results", command=self.get_results)
        self.get_results_button.pack(pady=10)

        # Label to display the best model
        self.best_model_label = Label(self.root, text=f"Best Model: {self.best_model_name}")
        self.best_model_label.pack(pady=10)

    def get_results(self):
        # Generate synthetic data for testing
        synthetic_data = np.random.rand(5, 2) * 10  # Generate 5 samples of random voltage and current values
        # Example: 5 samples of voltages between 0 and 10 V and currents between 0 and 20 µA
        synthetic_data[:, 0] = np.random.uniform(-0.5, 0.5, 5)  # Voltages
        synthetic_data[:, 1] = np.random.uniform(0, 20, 5)  # Currents

        # Make predictions using the best model
        predictions = self.best_model.predict(synthetic_data)
        
        # Display the predictions in a message box
        prediction_text = "\n".join(f"Sample {i+1}: Predicted Concentration = {pred:.2f}" for i, pred in enumerate(predictions))
        messagebox.showinfo("Predictions", prediction_text)

if __name__ == "__main__":
    root = Tk()
    app = CholestroCalcApp(root)
    root.mainloop()
