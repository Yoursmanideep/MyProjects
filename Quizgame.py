questions = [
    {
        "question": "What is the capital of France?",
        "options": ["A) London", "B) Berlin", "C) Paris", "D) Madrid"],
        "correct_answer": "C"
    },
    {
        "question": "Which programming language is this code written in?",
        "options": ["A) Java", "B) C++", "C) Python", "D) Ruby"],
        "correct_answer": "C"
    },
    {
        "question": "What is 2 + 2?",
        "options": ["A) 3", "B) 4", "C) 5", "D) 6"],
        "correct_answer": "B"
    },
    {
        "question": "What is the largest planet in our solar system?",
        "options": ["A) Earth", "B) Mars", "C) Jupiter", "D) Saturn"],
        "correct_answer": "C"
    }
]
def administer_questionnaire(questions):
    n = 0
    for i, question in enumerate(questions, 1):
        print(f"Question {i}: {question['question']}")
        for option in question['options']:
            print(option)
        user_answer = input("Your answer (enter your choice): ").upper()
        if user_answer == question['correct_answer']:
            n += 1
            print("Correct!\n")
        else:
            print(f"Wrong! The correct answer is {question['correct_answer']}\n")
    print(f"You got {n} out of {len(questions)} questions correct.")
administer_questionnaire(questions)
