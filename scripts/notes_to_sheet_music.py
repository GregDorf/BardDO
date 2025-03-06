import abjad
from classes.notes import Notes, Note
import classes.storage as storage

file_name = storage.load_file_name()

def notes_to_sheet_music(notes: Notes, output_path: str) -> None:
    """
    Генерация профессионально оформленного нотного листа в формате PDF.

    :param notes: Объект Notes, содержащий список нот.
    :param output_path: Путь для сохранения PDF-файла.
    """
    # Создаём систему нот
    staff = abjad.Staff()
    score = abjad.Score([staff])

    # Конвертируем каждую ноту в формат Abjad
    for note in notes.notes:
        abjad_note = note_to_abjad(note)
        staff.append(abjad_note)

    # Сохраняем результат в PDF
    abjad.persist.as_pdf(score, output_path)
    print(f"Нотный лист успешно сохранён: {output_path}")


def adjust_octave(pitch: str, octave: int) -> int:
    """
    Ограничиваем диапазон октав для каждой ноты, в зависимости от ноты и её диапазона.
    """
    valid_octaves = {"C": [3, 6], "C#": [3, 6], "D": [3, 6], "D#": [3, 6], "E": [2, 6],
                     "F": [2, 5], "F#": [2, 5], "G": [2, 5], "G#": [2, 5], "A": [2, 5], "A#": [2, 5], "B": [2, 5]}

    min_octave, max_octave = valid_octaves.get(pitch, [None, None])

    if min_octave is not None and max_octave is not None:
        # Если текущая октава меньше минимальной, устанавливаем минимальную
        if octave < min_octave:
            return min_octave
        # Если текущая октава больше максимальной, устанавливаем максимальную
        elif octave > max_octave:
            return max_octave
        # Если октава в пределах диапазона, оставляем её без изменений
        else:
            return octave
    else:
        return octave


def note_to_abjad(note: Note) -> abjad.Note:
    """
    Преобразует объект Note в ноту Abjad.

    :param note: Нота из класса Note.
    :return: Нота Abjad.
    """
    pitch = note.pitch.lower().replace("#", "s")  # Пример: C# -> cs
    
    # Получаем октаву из ноты
    if note.pitch[-1].isdigit():
        octave = int(note.pitch[-1])  # Если октава указана явно (например, g2)
        pitch = pitch[:-1]  # Убираем цифру из названия ноты
    else:
        octave = 4  # Если октава не указана явно, устанавливаем 4 по умолчанию

    # Ограничиваем диапазон по октаве
    octave = adjust_octave(pitch, octave)

    # Теперь создаем строку с нотой и октавой, например: f4, c5, g3
    abjad_pitch = "";
    if (octave>3 and octave<5):
        abjad_pitch = f"{pitch}{octave}"
    elif (octave < 3):
        abjad_pitch = f"{pitch}{octave+1}"
    elif (octave >= 5):
        abjad_pitch = f"{pitch}{octave-1}"

    # Преобразуем длительность ноты в формат Abjad
    duration = note_duration_to_abjad(note.duration)

    # Убираем апострофы и запятые, если они были добавлены автоматически
    abjad_note = abjad.Note(abjad_pitch, duration)
    return abjad_note


def note_duration_to_abjad(duration: float) -> abjad.Duration:
    """
    Преобразование длительности в формат Abjad.

    :param duration: Длительность в долях такта (например, 0.25 для четвертной).
    :return: Длительность в формате Abjad.
    """
    base_durations = {1.0: (1, 1), 0.5: (1, 2), 0.25: (1, 4), 0.125: (1, 8)}
    numerator, denominator = base_durations.get(duration, (1, 1))
    return abjad.Duration(numerator, denominator)


if __name__ == "__main__":
    input_path = f"../data/{file_name}_input.json"  # Путь к JSON-файлу
    output_path = f"../output/{file_name}_NOTES.pdf"  # Путь для сохранения 

    from json_to_notes import load_json

    # Загружаем JSON и преобразуем в Notes
    notes = load_json(input_path)

    # Генерируем нотный лист
    notes_to_sheet_music(notes, output_path)
