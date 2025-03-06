import json
import os

# Путь к файлу, где будет храниться JSON
filename = "storage.json"
current_path = r"C:\Users\ZERRASH\Desktop\Project BardDO\BardDo\chatbot_0.1\chatbot\scripts\classes"  # Используем сырую строку

def save_file_name(file_name, filename=current_path + '\\' + filename):  # Добавляем путь и имя файла
    try:
        # Убираем путь и расширение из имени файла
        file_name_without_extension = os.path.splitext(os.path.basename(file_name))[0]
        
        # Открываем файл для записи и сохраняем имя
        with open(filename, "w") as file:
            json.dump({"file_name": file_name_without_extension}, file)
        print(f"Файл '{filename}' успешно создан и сохранен.")
    except Exception as e:
        print(f"Ошибка при сохранении файла: {e}")

def load_file_name(filename=current_path + '\\' + filename):  # Добавляем путь и имя файла
    try:
        # Открываем файл для чтения и возвращаем имя
        if os.path.exists(filename):  # Проверка на существование файла
            with open(filename, "r") as file:
                data = json.load(file)
            return data.get("file_name")
        else:
            print(f"Файл '{filename}' не найден.")
            return None
    except Exception as e:
        print(f"Ошибка при чтении файла: {e}")
        return None

print(load_file_name())
