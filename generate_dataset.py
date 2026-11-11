import csv
import random

random.seed(42)

def calculate_risk(aqi, pm25, cough, wheezing, breathing, sneezing, dust, previous):
    """Domain-knowledge based rule to assign a risk label for training data."""
    score = 0
    score += (aqi / 500) * 40
    score += (pm25 / 250) * 20
    score += cough * 8
    score += wheezing * 10
    score += breathing * 8   # breathing is 0-3
    score += sneezing * 5
    score += dust * 5
    score += previous * 10

    if score < 30:
        return "Low"
    elif score < 60:
        return "Moderate"
    else:
        return "High"

rows = []
for _ in range(500):
    aqi = random.randint(10, 300)
    pm25 = round(random.uniform(5, 200), 1)
    cough = random.choice([0, 1])
    wheezing = random.choice([0, 1])
    breathing = random.choice([0, 1, 2, 3])
    sneezing = random.choice([0, 1])
    dust = random.choice([0, 1])
    previous = random.choice([0, 1])

    risk = calculate_risk(aqi, pm25, cough, wheezing, breathing, sneezing, dust, previous)

    rows.append([aqi, pm25, cough, wheezing, breathing, sneezing, dust, previous, risk])

with open("dataset/respiratory_data.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["AQI", "PM25", "Cough", "Wheezing", "Breathing", "Sneezing", "Dust", "Previous", "Risk"])
    writer.writerows(rows)

print("Dataset created: dataset/respiratory_data.csv")
print(f"Total rows: {len(rows)}")