from backend.app.verifiers.linear_equation import simple_linear_equation_plug_in
from backend.app.verifiers.step_checker import check_step_consistency, extract_equations_from_steps


class TestLinearEquationPlugIn:
    def test_correct_answer(self):
        ok, note = simple_linear_equation_plug_in("2x + 5 = 17", 6.0)
        assert ok is True
        assert note == "plug_in_ok"

    def test_wrong_answer(self):
        ok, note = simple_linear_equation_plug_in("2x + 5 = 17", 5.0)
        assert ok is False
        assert "plug_in_failed" in note

    def test_no_equation(self):
        ok, note = simple_linear_equation_plug_in("What is 2 plus 3?", 5.0)
        assert ok is False
        assert note == "no_equation_found"

    def test_implicit_multiplication(self):
        # 3(x-2) = 9 => x = 5
        ok, note = simple_linear_equation_plug_in("3(x-2) = 9", 5.0)
        assert ok is True


class TestStepChecker:
    def test_consistent_steps(self):
        answer = "2x + 5 = 17 -> 2x = 12 -> x = 6"
        ok, note = check_step_consistency(answer)
        assert ok == 1
        assert "consistent" in note

    def test_inconsistent_steps(self):
        answer = "2x + 5 = 17 -> 2x = 10 -> x = 5"
        ok, note = check_step_consistency(answer)
        assert ok == 0

    def test_single_equation(self):
        ok, note = check_step_consistency("x = 6")
        assert ok == 0
        assert "not_enough" in note

    def test_extract_equations_arrow(self):
        eqs = extract_equations_from_steps("2x = 4 -> x = 2")
        assert len(eqs) == 2

    def test_extract_equations_newline(self):
        eqs = extract_equations_from_steps("2x = 4\nx = 2")
        assert len(eqs) == 2
