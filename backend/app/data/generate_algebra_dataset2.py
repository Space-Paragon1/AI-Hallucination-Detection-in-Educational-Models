import json

questions = [
    ("x + 5 = 12", 7),
    ("x - 4 = 9", 13),
    ("2x = 10", 5),
    ("3x = 21", 7),
    ("x / 5 = 6", 30),
    ("4x + 1 = 17", 4),
    ("2(x + 3) = 14", 4),
    ("5x - 10 = 15", 5),
    ("x + 9 = 2", -7),
    ("6x = 36", 6),
]

dataset = []
id_counter = 4

for q, correct_x in questions:
    for i in range(10):  # repeat patterns to reach 100 questions
        q_text = f"Solve for x: {q}"

        # Correct
        dataset.append({
            "id": f"a{id_counter:03}",
            "question": q_text,
            "student_level": "Algebra I",
            "model_answer": f"Solving gives x = {correct_x}",
            "label_hallucinated": 0,
            "error_type": "none",
            "severity": 0
        })
        id_counter += 1

        # Wrong (arithmetic/sign error)
        dataset.append({
            "id": f"a{id_counter:03}",
            "question": q_text,
            "student_level": "Algebra I",
            "model_answer": f"Solving gives x = {correct_x + 2}",
            "label_hallucinated": 1,
            "error_type": "arithmetic",
            "severity": 2
        })
        id_counter += 1

        # Almost correct (reasoning gap)
        dataset.append({
            "id": f"a{id_counter:03}",
            "question": q_text,
            "student_level": "Algebra I",
            "model_answer": f"Subtracting constants shows x is close to {correct_x}",
            "label_hallucinated": 1,
            "error_type": "reasoning_gap",
            "severity": 3
        })
        id_counter += 1

# Write to file
with open("algebra_hallucination_dataset.jsonl", "w") as f:
    for row in dataset[:300]:
        f.write(json.dumps(row) + "\n")

print("Generated 300 algebra hallucination samples.")
