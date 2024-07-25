import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import OneHotEncoder, LabelEncoder
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error

# Load the dataset
df = pd.read_csv('path/to/your/dataset.csv')

# Convert categorical variables to numerical using OneHotEncoder
categorical_features = ['Provider']
label_encoder = LabelEncoder()
one_hot_encoder = OneHotEncoder(sparse=False)

# Apply the encoders to the categorical features
df[categorical_features] = df[categorical_features].apply(lambda x: label_encoder.fit_transform(x))
df[categorical_features] = one_hot_encoder.fit_transform(df[categorical_features])

# Split the dataset into training and test sets
X = df.drop('ClaimAmount', axis=1)
y = df['ClaimAmount']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Define the model
rf = RandomForestRegressor(n_estimators=100, max_depth=10)

# Create the pipeline
pipeline = Pipeline(steps=[('rf', rf)])

# Train the model
pipeline.fit(X_train, y_train)

# Make predictions
y_pred = pipeline.predict(X_test)

# Evaluate the model
rmse = mean_squared_error(y_test, y_pred, squared=False)
print("Root Mean Squared Error (RMSE) =", rmse)
