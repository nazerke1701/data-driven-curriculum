import numpy as np
import pandas as pd
from pathlib import Path

SEED = 42
rng = np.random.default_rng(SEED)

TOPICS = {
    5: ["Натуральные числа", "Обыкновенные дроби", "Десятичные дроби",
        "Проценты", "Геометрические фигуры", "Единицы измерения"],
    6: ["Делимость чисел", "Отношения и пропорции", "Рациональные числа",
        "Координатная плоскость", "Уравнения", "Симметрия"],
    7: ["Линейные функции", "Системы уравнений", "Степень с натуральным показателем",
        "Многочлены", "Треугольники", "Параллельные прямые"],
    8: ["Квадратные корни", "Квадратные уравнения", "Неравенства",
        "Четырёхугольники", "Подобие треугольников", "Теорема Пифагора"],
    9: ["Квадратичная функция", "Прогрессии", "Тригонометрия",
        "Окружность", "Векторы", "Вероятность и статистика"],
}

HARD = {
    "Проценты": 0.13, "Системы уравнений": 0.10, "Квадратные уравнения": 0.15,
    "Подобие треугольников": 0.12, "Тригонометрия": 0.18,
}
GEOMETRY = {"Геометрические фигуры", "Симметрия", "Треугольники", "Параллельные прямые",
            "Четырёхугольники", "Подобие треугольников", "Теорема Пифагора",
            "Окружность", "Векторы"}
HARD_ALGEBRA = {"Проценты", "Системы уравнений", "Квадратные уравнения", "Тригонометрия"}

TEXTBOOKS = ["Учебник А", "Учебник Б", "Учебник В"]
N_SCHOOLS = 40
STUDENTS_PER_CLASS = 22
CURRENT_HOURS = {t: int(rng.integers(8, 13)) for ts in TOPICS.values() for t in ts}


def textbook_effect(textbook, topic):
    if textbook == "Учебник Б" and topic in GEOMETRY:
        return 0.08
    if textbook == "Учебник В" and topic in HARD_ALGEBRA:
        return 0.07
    if textbook == "Учебник В" and topic in GEOMETRY:
        return -0.03
    return 0.0


def main():
    rows = []
    topic_noise = {t: rng.normal(0, 0.02) for ts in TOPICS.values() for t in ts}
    regions = ["Тараз", "Жамбылский р-н", "Байзак", "Шу", "Мерке", "Кордай"]
    for s in range(N_SCHOOLS):
        school_id = f"Школа-{s + 1:02d}"
        region = regions[s % len(regions)]
        school_level = rng.normal(0, 0.06)
        for grade, topics in TOPICS.items():
            textbook = rng.choice(TEXTBOOKS)
            for k in range(STUDENTS_PER_CLASS):
                student_id = f"{school_id}-{grade}-{k + 1:02d}"
                ability = rng.normal(0, 0.10)
                pre = np.clip(0.60 + school_level + ability + rng.normal(0, 0.05), 0, 1) * 100
                for topic in topics:
                    expected = (0.64 + school_level + ability
                                - HARD.get(topic, 0) + topic_noise[topic]
                                + textbook_effect(textbook, topic))
                    score = np.clip(expected + rng.normal(0, 0.09), 0, 1) * 100
                    rows.append({
                        "school": school_id, "region": region, "grade": grade,
                        "textbook": textbook, "student_id": student_id,
                        "topic": topic, "pre_score": round(pre, 1),
                        "score": round(score, 1),
                        "hours_current": CURRENT_HOURS[topic],
                    })
    df = pd.DataFrame(rows)
    Path("data").mkdir(exist_ok=True)
    df.to_csv("data/results.csv", index=False, encoding="utf-8")
    print(f"Сохранено {len(df)} записей -> data/results.csv")
    print(df.groupby("textbook").size())


if __name__ == "__main__":
    main()