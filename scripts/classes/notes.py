from typing import List, Dict

class Note:
    """
    Класс, представляющий ноту.
    """
    def __init__(self, pitch: str, duration: float, velocity: int = 100):
        """
        Инициализация ноты.

        :param pitch: Нота в формате MIDI (например, "C4", "D#5").
        :param duration: Длительность ноты (в долях такта).
        :param velocity: Сила нажатия клавиши (по умолчанию 100).
        """
        self.pitch = pitch
        self.duration = duration
        self.velocity = velocity

    def __repr__(self) -> str:
        return f"Note(pitch={self.pitch}, duration={self.duration}, velocity={self.velocity})"


class Notes:
    """
    Класс для работы со списком нот.
    """
    def __init__(self, notes: List[Note]):
        """
        Инициализация списка нот.

        :param notes: Список объектов Note.
        """
        self.notes = notes

    @classmethod
    def from_json(cls, json_data: Dict) -> "Notes":
        """
        Создание объекта Notes из JSON-данных.

        :param json_data: JSON-объект с массивом нот.
        :return: Объект Notes.
        """
        notes = [
            Note(pitch=note["pitch"], duration=note["duration"], velocity=note.get("velocity", 100))
            for note in json_data["notesArray"]
        ]
        return cls(notes)
