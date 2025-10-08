import joblib
import pandas as pd


def load_model(path="model.pkl"):
    return joblib.load(path)


def iris_predict(model, X):
    # Map feature names from API format to model format
    feature_mapping = {
        "sepal_length": "sepal length (cm)",
        "sepal_width": "sepal width (cm)",
        "petal_length": "petal length (cm)",
        "petal_width": "petal width (cm)",
    }

    # mapping of model output to species names
    output_mapping = {0: "setosa", 1: "versicolor", 2: "virginica"}

    # Convert the input dictionary to use the correct feature names
    mapped_features = {feature_mapping[k]: v for k, v in X.items()}

    # Create DataFrame with correct column names
    df = pd.DataFrame([mapped_features])

    # Return single prediction
    return output_mapping[model.predict(df)[0]]
