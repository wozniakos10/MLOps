import os

import pytest
import requests

# API endpoint for the deployed application
API_BASE_URL = os.getenv("API_BASE_URL")


class TestFastAPI:
    def test_root(self):
        response = requests.get(f"{API_BASE_URL}/")
        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to the ML API"}

    def test_health(self):
        response = requests.get(f"{API_BASE_URL}/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.parametrize(
        "sentence,expected",
        [
            ("What a great MLOps lecture, I am very satisfied", {"prediction": "positive"}),
            ("That MLOps lecture was neither good or bad, I would rate it as medium", {"prediction": "neutral"}),
            ("That MLOps lecture was terrible, I did not learn anything.", {"prediction": "negative"}),
            ("I feel realy bad today, probably I would stay in bed all day", {"prediction": "negative"}),
            ("Tomorrow is friday, I am looking forward to the weekend", {"prediction": "positive"}),
        ],
    )
    def test_sentences_predictions(self, sentence, expected):
        response = requests.post(f"{API_BASE_URL}/predict", json={"text": sentence})

        assert response.status_code == 200
        assert response.json() == expected

    def test_invalid_input_field_missing(self):
        response = requests.post(f"{API_BASE_URL}/predict", json={"invalid_field": "This is an invalid input"})
        assert response.json() == {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["body", "text"],
                    "msg": "Field required",
                    "input": {"invalid_field": "This is an invalid input"},
                }
            ]
        }

    def test_invalid_input_field_type(self):
        response = requests.post(f"{API_BASE_URL}/predict", json={"text": 12345})

        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "string_type",
                    "loc": ["body", "text"],
                    "msg": "Input should be a valid string",
                    "input": 12345,
                }
            ]
        }

    def test_invalid_input_empty_string(self):
        response = requests.post(f"{API_BASE_URL}/predict", json={"text": ""})

        assert response.status_code == 422
        assert response.json() == {
            "detail": [
                {
                    "type": "string_too_short",
                    "loc": ["body", "text"],
                    "msg": "String should have at least 1 character",
                    "input": "",
                    "ctx": {"min_length": 1},
                }
            ]
        }
