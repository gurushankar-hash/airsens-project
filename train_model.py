import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib

# Load the dataset
data = pd.read_csv("dataset/respiratory_data.csv")

# Split into features (X) and answer/label (y)
X = data[["AQI", "PM25", "Cough", "Wheezing", "Breathing", "Sneezing", "Dust", "Previous"]]
y = data["Risk"]

# Split — most for training, some for testing
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Create and train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Test accuracy
predictions = model.predict(X_test)
accuracy = accuracy_score(y_test, predictions)
print(f"Model accuracy: {accuracy * 100:.2f}%")

# Save the trained model
joblib.dump(model, "risk_model.pkl")
print("Model saved as risk_model.pkl")