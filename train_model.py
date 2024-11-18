import pandas as pd
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.ensemble import RandomForestRegressor, StackingRegressor
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import LinearRegression
import joblib  # For saving the model

# Load the CSV file
data = pd.read_csv('data.csv')  # Make sure 'data.csv' is in the same directory or provide the full path

# Preprocess the data
X = data[['Voltage', 'Current']]
y = data['Concentration']

# Add polynomial features
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X)

# Feature Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_poly)

# Split the data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Hyperparameter tuning and model training
rf_param_grid = {
    'n_estimators': [100, 200, 500],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4]
}
rf_random_search = RandomizedSearchCV(
    RandomForestRegressor(random_state=42),
    param_distributions=rf_param_grid,
    n_iter=20,
    cv=5,
    scoring='neg_mean_squared_error',
    random_state=42
)
rf_random_search.fit(X_train, y_train)
best_rf_model = rf_random_search.best_estimator_

# Stacking Ensemble Model
stacking_model = StackingRegressor(
    estimators=[('rf', best_rf_model)],
    final_estimator=LinearRegression()
)
stacking_model.fit(X_train, y_train)

# Save the model, polynomial features, and scaler
joblib.dump(stacking_model, 'stacking_model.pkl')
joblib.dump(poly, 'poly.pkl')
joblib.dump(scaler, 'scaler.pkl')

print("Model, polynomial features, and scaler saved successfully.")