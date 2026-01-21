import json
from pathlib import Path

OUT_PATH = Path("backend/app/data/calc_all.jsonl")

def make_item(_id, question, student_level, model_answer, label, error_type, severity):
    return {
        "id": _id,
        "question": question,
        "student_level": student_level,
        "model_answer": model_answer,
        "label_hallucinated": label,
        "error_type": error_type,
        "severity": severity,
    }

# -----------------------
# 20 DERIVATIVES
# -----------------------
derivatives = [
    ("Differentiate: d/dx (x^3)", "3x^2",
     "d/dx(x^3)=3x^2", "d/dx(x^3)=2x^2", "d/dx(x^3)=3x"),
    ("Differentiate: d/dx (5x^4)", "20x^3",
     "Power rule: 5*4*x^3=20x^3", "5*4*x^4=20x^4", "Power rule gives 20x^4"),
    ("Differentiate: d/dx (1/x)", "-1/x^2",
     "Rewrite x^-1 -> -1*x^-2 = -1/x^2", "1/x^2", "Close: -1/x"),
    ("Differentiate: d/dx (sqrt(x))", "1/(2sqrt(x))",
     "x^(1/2)->(1/2)x^(-1/2)=1/(2sqrt(x))", "1/sqrt(x)", "1/(2x)"),
    ("Differentiate: d/dx (sin x)", "cos x",
     "Derivative of sin is cos", "-cos x", "sin x"),
    ("Differentiate: d/dx (cos x)", "-sin x",
     "Derivative of cos is -sin", "sin x", "-cos x"),
    ("Differentiate: d/dx (e^x)", "e^x",
     "Derivative of e^x is e^x", "x*e^x", "e^(x-1)"),
    ("Differentiate: d/dx (ln x)", "1/x",
     "Derivative of ln x is 1/x", "ln x", "1/(x^2)"),
    ("Differentiate: d/dx ((x^2)+4x)", "2x+4",
     "d/dx(x^2)=2x and d/dx(4x)=4 -> 2x+4", "2x+4x", "2x+5"),
    ("Differentiate: d/dx (x^5 - 3x^2)", "5x^4 - 6x",
     "Power rule: 5x^4 - 6x", "5x^4 - 3x", "5x^4 - 6"),
    ("Differentiate: d/dx (2x - 7)", "2",
     "Derivative of 2x is 2 and constant drops -> 2", "1", "2x"),
    ("Differentiate: d/dx ((x+1)^2)", "2(x+1)",
     "Chain rule: 2(x+1)^1 * 1 = 2(x+1)", "2x+1", "2(x+1)^2"),
    ("Differentiate: d/dx ((3x+2)^4)", "12(3x+2)^3",
     "Chain: 4(3x+2)^3 * 3 = 12(3x+2)^3", "4(3x+2)^3", "12(3x+2)^4"),
    ("Differentiate: d/dx (x^2 * x^3)", "5x^4",
     "Simplify first: x^5 -> derivative 5x^4", "6x^5", "5x^5"),
    ("Differentiate: d/dx (x^2 + 1)/(?) Use: d/dx (x^2 + 1)", "2x",
     "d/dx(x^2+1)=2x", "x", "2x+1"),
    ("Differentiate: d/dx (tan x)", "sec^2 x",
     "Derivative of tan is sec^2", "sec x", "csc^2 x"),
    ("Differentiate: d/dx (x^-2)", "-2x^-3",
     "Power rule: -2x^-3 = -2/x^3", "2x^-3", "-2/x^2"),
    ("Differentiate: d/dx (3)", "0",
     "Constant derivative is 0", "3", "1"),
    ("Differentiate: d/dx (x)", "1",
     "Derivative of x is 1", "0", "x"),
    ("Differentiate: d/dx (x^4/4)", "x^3",
     "(1/4)*4x^3 = x^3", "4x^3", "x^4"),
]

# -----------------------
# 20 INTEGRALS (basic)
# -----------------------
integrals = [
    ("Compute: ∫ x^2 dx", "(1/3)x^3 + C",
     "Power rule: x^3/3 + C", "x^3 + C", "(1/2)x^2 + C"),
    ("Compute: ∫ 4x^3 dx", "x^4 + C",
     "4*(x^4/4)=x^4 + C", "4x^4 + C", "x^4/4 + C"),
    ("Compute: ∫ (1/x) dx", "ln|x| + C",
     "Integral of 1/x is ln|x| + C", "1/ln|x| + C", "ln x"),
    ("Compute: ∫ cos x dx", "sin x + C",
     "Integral of cos is sin + C", "-sin x + C", "cos x + C"),
    ("Compute: ∫ sin x dx", "-cos x + C",
     "Integral of sin is -cos + C", "cos x + C", "-sin x + C"),
    ("Compute: ∫ e^x dx", "e^x + C",
     "Integral of e^x is e^x + C", "x e^x + C", "e^(x-1)+C"),
    ("Compute: ∫ 2 dx", "2x + C",
     "Integral of constant 2 is 2x + C", "x + C", "2 + C"),
    ("Compute: ∫ (3x^2) dx", "x^3 + C",
     "3*(x^3/3)=x^3 + C", "3x^3 + C", "x^2 + C"),
    ("Compute: ∫ (x^-2) dx", "-x^-1 + C",
     "x^-2 -> x^-1/(-1) = -x^-1 + C = -1/x + C", "1/x + C", "-1/x^2 + C"),
    ("Compute: ∫ (5x^4 - 2x) dx", "x^5 - x^2 + C",
     "Integrate termwise: x^5 - x^2 + C", "x^5 - 2x^2 + C", "5x^5 - x^2 + C"),
    ("Compute: ∫ (2x + 1) dx", "x^2 + x + C",
     "∫2x dx = x^2 and ∫1 dx = x -> x^2+x+C", "x^2 + 1 + C", "2x^2 + x + C"),
    ("Compute: ∫ (7) dx", "7x + C",
     "Constant rule: 7x + C", "7 + C", "x + C"),
    ("Compute: ∫ (1) dx", "x + C",
     "∫1 dx = x + C", "1 + C", "ln|x| + C"),
    ("Compute: ∫ (x^5) dx", "(1/6)x^6 + C",
     "Power rule: x^6/6 + C", "x^6 + C", "(1/5)x^5 + C"),
    ("Compute: ∫ (sqrt(x)) dx", "(2/3)x^(3/2) + C",
     "x^(1/2) -> x^(3/2)/(3/2) = (2/3)x^(3/2)+C", "x^(3/2)+C", "(3/2)x^(1/2)+C"),
    ("Compute: ∫ (sec^2 x) dx", "tan x + C",
     "Integral of sec^2 is tan + C", "sec x + C", "-tan x + C"),
    ("Compute: ∫ (0) dx", "C",
     "Integral of 0 is constant C", "0", "x + C"),
    ("Compute: ∫ (x^-1) dx", "ln|x| + C",
     "x^-1 integrates to ln|x| + C", "x^0 + C", "1/x + C"),
    ("Compute: ∫ (3x) dx", "(3/2)x^2 + C",
     "∫3x dx = 3*(x^2/2) = (3/2)x^2 + C", "3x^2 + C", "(1/2)x^2 + C"),
    ("Compute: ∫ (2x^2 + 4) dx", "(2/3)x^3 + 4x + C",
     "Termwise: (2/3)x^3 + 4x + C", "(2/3)x^3 + 4 + C", "(1/3)x^3 + 4x + C"),
]

# -----------------------
# 20 LIMITS
# -----------------------
limits = [
    ("Evaluate: lim_{x->2} (x^2)", "4",
     "Direct substitution: 2^2=4", "2", "3.9"),
    ("Evaluate: lim_{x->-1} (3x+2)", "-1",
     "Substitute: 3(-1)+2=-1", "1", "-2"),
    ("Evaluate: lim_{x->0} (sin x)/x", "1",
     "Standard limit: sin x / x -> 1", "0", "sin(0)/0 = 0"),
    ("Evaluate: lim_{x->0} (1 - cos x)/x", "0",
     "Numerator ~ 0, grows like x^2 so ratio -> 0", "1", "undefined so 0"),
    ("Evaluate: lim_{x->3} (x-3)", "0",
     "Substitute: 3-3=0", "3", "1"),
    ("Evaluate: lim_{x->5} (2x-1)", "9",
     "Substitute: 2(5)-1=9", "10", "8"),
    ("Evaluate: lim_{x->1} (x^3 - 1)/(x - 1)", "3",
     "Factor: (x-1)(x^2+x+1)/(x-1)=x^2+x+1 -> 3", "1", "2"),
    ("Evaluate: lim_{x->2} (x^2 - 4)/(x - 2)", "4",
     "Factor: (x-2)(x+2)/(x-2)=x+2 -> 4", "2", "3"),
    ("Evaluate: lim_{x->0} (e^x - 1)/x", "1",
     "Standard limit: (e^x-1)/x -> 1", "0", "e^0-1=0 so 0"),
    ("Evaluate: lim_{x->0} x*cos x", "0",
     "x->0 so product -> 0", "1", "cos 0 = 1 so 1"),
    ("Evaluate: lim_{x->-2} (x^2+3x+2)", "0",
     "Substitute: 4-6+2=0", "-4", "2"),
    ("Evaluate: lim_{x->4} sqrt(x)", "2",
     "Substitute: sqrt(4)=2", "4", "1.9"),
    ("Evaluate: lim_{x->1} (x+1)/(x+2)", "2/3",
     "Substitute: (2)/(3)=2/3", "3/2", "0.67"),
    ("Evaluate: lim_{x->0} (x^2)/x", "0",
     "Simplify: x -> 0", "1", "0/0 so 0"),
    ("Evaluate: lim_{x->2} (x^3 - 8)/(x - 2)", "12",
     "Factor: (x-2)(x^2+2x+4)/(x-2)-> x^2+2x+4 at 2 = 12", "6", "10"),
    ("Evaluate: lim_{x->0} (1/x)", "Does not exist",
     "Blows up to ±infinity, so DNE", "0", "infinity"),
    ("Evaluate: lim_{x->∞} (1/x)", "0",
     "As x grows, 1/x -> 0", "1", "does not exist"),
    ("Evaluate: lim_{x->-∞} (2x+1)/x", "2",
     "Divide by x: (2 + 1/x) -> 2", "0", "1"),
    ("Evaluate: lim_{x->2} (x+2)", "4",
     "Substitute: 2+2=4", "2", "5"),
    ("Evaluate: lim_{x->0} (x^3)", "0",
     "Direct substitution: 0^3=0", "1", "0.1"),
]

def build_dataset():
    items = []
    idx = 1  # for calc dataset, independent numbering
    student_level = "Calculus"

    def add_triplet(problem_text, correct_ans, correct_reason, wrong1, wrong2):
        nonlocal idx

        q = problem_text

        # Correct
        items.append(make_item(
            f"c{idx:03}", q, student_level,
            f"{correct_reason} -> Answer: {correct_ans}",
            0, "none", 0
        ))
        idx += 1

        # Wrong (common mistake)
        items.append(make_item(
            f"c{idx:03}", q, student_level,
            f"Work: {wrong1}",
            1, "arithmetic", 2
        ))
        idx += 1

        # Almost-correct (sounds confident but off)
        items.append(make_item(
            f"c{idx:03}", q, student_level,
            f"It should be {wrong2} because substituting gives something close.",
            1, "reasoning_gap", 3
        ))
        idx += 1

    for p, ans, correct_reason, w1, w2 in derivatives:
        add_triplet(f"Solve: {p}", ans, correct_reason, w1, w2)

    for p, ans, correct_reason, w1, w2 in integrals:
        add_triplet(f"Solve: {p}", ans, correct_reason, w1, w2)

    for p, ans, correct_reason, w1, w2 in limits:
        add_triplet(f"Solve: {p}", ans, correct_reason, w1, w2)

    # 60 problems * 3 answers = 180 datapoints
    assert len(items) == 180, f"Expected 180 items, got {len(items)}"
    return items

def main():
    data = build_dataset()
    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with OUT_PATH.open("w", encoding="utf-8") as f:
        for row in data:
            f.write(json.dumps(row) + "\n")

    print(f"Wrote {len(data)} rows to {OUT_PATH}")

if __name__ == "__main__":
    main()
