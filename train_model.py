import pandas as pd
import numpy as np
import pickle

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

# =========================
# LOAD DATASET
# =========================

df = pd.read_csv("WA_Fn-UseC_-HR-Employee-Attrition.csv")

print("\nDataset Loaded Successfully\n")

print(df.head())

# =========================
# REMOVE UNNECESSARY COLUMNS
# =========================

df.drop(
    ['EmployeeCount', 'EmployeeNumber', 'Over18', 'StandardHours'],
    axis=1,
    inplace=True
)

# =========================
# ENCODE ALL NON-NUMERIC COLUMNS
# =========================

le = LabelEncoder()

for column in df.columns:

    # Encode every non-numeric column
    if not pd.api.types.is_numeric_dtype(df[column]):

        df[column] = le.fit_transform(
            df[column].astype(str)
        )

# =========================
# CHECK DATA TYPES
# =========================

print("\nData Types After Encoding:\n")

print(df.dtypes)

# =========================
# FEATURES & TARGET
# =========================

X = df.drop('Attrition', axis=1)

y = df['Attrition']

# =========================
# K-MEANS CLUSTERING
# =========================

kmeans = KMeans(
    n_clusters=2,
    random_state=42,
    n_init=10
)

clusters = kmeans.fit_predict(X)

# Add cluster feature
X['Cluster'] = clusters

print("\nK-Means Clustering Completed\n")

# =========================
# STORE FEATURE ORDER (NEW ADDITION - IMPORTANT)
# =========================

feature_columns = list(X.columns)

# =========================
# SCALE DATA
# =========================

scaler = StandardScaler()

X_scaled = scaler.fit_transform(X)

# =========================
# TRAIN TEST SPLIT
# =========================

X_train, X_test, y_train, y_test = train_test_split(
    X_scaled,
    y,
    test_size=0.2,
    random_state=42
)

# =========================
# DECISION TREE MODEL
# =========================

model = DecisionTreeClassifier(
    criterion='gini',
    max_depth=5,
    random_state=42
)

# Train model
model.fit(X_train, y_train)

# =========================
# PREDICTIONS
# =========================

predictions = model.predict(X_test)

# =========================
# MODEL ACCURACY
# =========================

accuracy = accuracy_score(y_test, predictions)

print("\nModel Accuracy:", accuracy)

# =========================
# SAVE MODEL & SCALER
# =========================

pickle.dump(
    model,
    open("model.pkl", "wb")
)

pickle.dump(
    scaler,
    open("scaler.pkl", "wb")
)

# 🔥 NEW ADDITION (IMPORTANT FOR FIXING FLASK MISMATCH)
pickle.dump(
    feature_columns,
    open("columns.pkl", "wb")
)

print("\nModel Saved Successfully")