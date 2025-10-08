from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
import joblib


def load_data():
    data = load_iris(as_frame=True)
    return data.data, data.target


def train_model(X, y):
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    return model


def save_model(model, path="model.joblib"):
    joblib.dump(model, path)


if __name__ == "__main__":
    X, y = load_data()
    model = train_model(X, y)
    save_model(model, "model.joblib")
