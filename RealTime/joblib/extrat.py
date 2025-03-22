import joblib

# Load the file (replace 'your_file.joblib' with your filename)
data = joblib.load('realtimecloudburstmodel.joblib')

# Check the content
print(type(data))  # To see what type of object it contains
print(data)        # To view the content
