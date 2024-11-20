# calibration_model.py

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score

class CalibrationModel:
    def __init__(self, degree=2):
        self.degree = degree
        self.poly_model = None
        self.create_calibration_model()

    def create_calibration_model(self):
        # Step 2: Define your data
        voltage_values = [0.102075] * 30  # Adjusted to 30 entries
        current_values = [
            27.033878, 31.08336, 29.347368, 21.846902, 18.710916,
            15.445432, 16.491925, 14.766434, 13.25094, 12.710192,
            11.674198, 12.377695, 12.844943, 13.471439, 11.21745,
            13.57294, 13.562439, 12.066195, 13.25619, 10.673203,
            10.380953, 10.849951, 9.955705, 9.264459, 9.528707,
            8.772711, 8.96696, 8.501462, 7.883714, 8.266963
        ]  # 30 entries for Current

        # Generate Concentration values from 5 to 150 with a step of 5
        concentration_values = list(range(5, 155, 5))[:30]  # This will create a list [5, 10, 15, ..., 150] limited to 30 entries

        # Create a DataFrame
        data = {
            "Voltage": voltage_values,
            "Current": current_values,
            "Concentration": concentration_values
        }

        # Create a DataFrame
        df = pd.DataFrame(data)

        # Extract Current and Concentration for modeling
        X = df["Current"].values.reshape(-1, 1)  # Current as independent variable
        y = df["Concentration"].values           # Concentration as dependent variable

        # Step 3: Choose a regression model
        self.poly_model = make_pipeline(PolynomialFeatures(self.degree), LinearRegression())
        self.poly_model.fit(X, y)

        # Calculate R² score for the model
        predicted_y = self.poly_model.predict(X)
        r2 = r2_score(y, predicted_y)
        print(f"R² of the model: {r2:.4f}")

    def predict_concentration(self, current_value):
        """
        Predicts the concentration based on the provided current value using the polynomial model.
        """
        current_value = np.array([[current_value]])  # Reshape for prediction
        return self.poly_model.predict(current_value)[0]
