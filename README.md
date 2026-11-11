# AirSense - Allergy & Respiratory Monitor

## Description
AirSense is a Python-based respiratory monitoring system. It combines
symptom information with environmental factors (AQI, PM2.5) and uses
Machine Learning to predict respiratory risk, calculate a risk score,
and generate alerts.

## Modules
1. **User & Login** - login.py (SQLite users table)
2. **Data Collection** - age, AQI, PM2.5, cough, wheezing, breathing, sneezing, dust exposure, previous symptoms
3. **Data Preprocessing** - encoding using functional programming (lambda, map, filter)
4. **Feature Extraction** - feature selection from collected data
5. **Machine Learning** - Random Forest classifier (train_model.py, risk_model.pkl)
6. **Risk Score & Alert** - SymPy risk formula, Low / Moderate / High alerts
7. **Database & History** - SQLite (airsense.db, users & records tables)
8. **Socket Programming** - client-server request/response
9. **Multiprocessing** - parallel processing for ML, scoring and database work
10. **Tkinter GUI** - main window with Analyze, History, Logout

## Tech Stack
Python, Tkinter, SQLite, scikit-learn, pandas, SymPy, Socket, Multiprocessing

## Project Structure
- login.py - login screen
- gui.py - main application window
- generate_dataset.py - creates the dataset
- train_model.py - trains the ML model
- risk_model.pkl - trained model
- airsense.db / database.sql - database

## How to Run
1. Install libraries: `pip install -r requirements.txt`
2. Generate dataset: `python generate_dataset.py`
3. Train model: `python train_model.py`
4. Run the app: `python login.py`

## Note
`credentials.json` is not uploaded for security reasons.
Create your own `credentials.json` file before running.

## Screenshots


![Login](screenshots/login.jpge)




![Dashboard](screenshots/dashboard.jpge)




![Result](screenshots/result.jpge)



## Team
- Guru Shankar B
- Janavarshini D
- Dhamarai Kannan T
- Mukeshdharan K