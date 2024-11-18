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
        data = {
            "Voltage": [-0.50017, -0.50017, -0.50017, -0.50017, -0.50017],
            "Current": [8.06396, 13.2719, 20.4399, 27.5519, 32.7599],
            "Concentration": [200, 400, 600, 800, 1000]
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