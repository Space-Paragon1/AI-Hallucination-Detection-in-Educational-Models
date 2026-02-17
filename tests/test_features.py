from backend.app.features.algebra_features import (
    math_text_features,
    detect_final_answer,
    extract_numbers,
)


class TestExtractNumbers:
    def test_basic(self):
        assert extract_numbers("x + 5 = 17") == [5.0, 17.0]

    def test_negative(self):
        assert extract_numbers("x = -3") == [-3.0]

    def test_no_numbers(self):
        assert extract_numbers("solve for x") == []


class TestDetectFinalAnswer:
    def test_answer_prefix(self):
        found, val = detect_final_answer("Answer: 6")
        assert found is True
        assert val == 6.0

    def test_variable_equals(self):
        found, val = detect_final_answer("so x = 12")
        assert found is True
        assert val == 12.0

    def test_last_number_fallback(self):
        found, val = detect_final_answer("We get 3 then 5 then 7")
        assert found is True
        assert val == 7.0

    def test_no_answer(self):
        found, val = detect_final_answer("no numbers here")
        assert found is False
        assert val is None


class TestMathTextFeatures:
    def test_returns_expected_keys(self):
        feats = math_text_features("Solve 2x = 10", "x = 5")
        expected = {
            "hedge_count", "confident_count", "has_steps",
            "num_count_q", "num_count_a", "final_found",
            "final_val", "new_final", "answer_len", "is_calc_prompt",
        }
        assert expected.issubset(feats.keys())

    def test_hedge_detection(self):
        feats = math_text_features("Solve x + 1 = 2", "I think maybe x = 1")
        assert feats["hedge_count"] >= 2

    def test_calc_prompt_detection(self):
        feats = math_text_features("Find the derivative of x^2", "2x")
        assert feats["is_calc_prompt"] == 1

    def test_non_calc_prompt(self):
        feats = math_text_features("Solve 2x = 10", "x = 5")
        assert feats["is_calc_prompt"] == 0
