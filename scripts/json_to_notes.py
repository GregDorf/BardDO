import sys
import os
import classes.storage as storage

file_name = storage.load_file_name()

# Добавляем корневую директорию проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from classes.notes import Notes
import json

def load_json(file_path: str) -> Notes:
    """
    Загрузка данных из JSON-файла и преобразование в объект Notes.

    :param file_path: Путь к JSON-файлу.
    :return: Объект Notes.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return Notes.from_json(data)


if __name__ == "__main__":
    input_path = f"../data/{file_name}_input.json"
    notes = load_json(input_path)
    print("Загруженные ноты:", notes.notes)
