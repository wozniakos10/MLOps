from lab01_lib_homework.api.inference import load_joblib_model, load_sentence_transformer_model


class TestLoadModels:
    def test_load_sentence_transformer_model_valid(self):
        model = load_sentence_transformer_model()
        assert model is not None

    def test_load_sentence_transformer_model_invalid(self):
        model = load_sentence_transformer_model(path="invalid/model/path/not/exist")
        assert model is None

    def test_load_joblib_model(self):
        model = load_joblib_model()
        assert model is not None

    def test_load_joblib_model_invalid(self):
        model = load_joblib_model(path="invalid/model/path")
        assert model is None
