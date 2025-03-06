import json
import abjad
from classes.notes import Notes, Note
import classes.storage as storage

file_name = storage.load_file_name()

def note_duration_to_lilypond(duration):
    """
    Преобразует длительность в формат LilyPond.
    """
    durations = {
        1.0: "1",      # Целая нота
        0.5: "2",      # Половинка
        0.25: "4",     # Четверть
        0.125: "8",    # Восьмая
        0.0625: "16",  # Шестнадцатая
        0.03125: "32", # Тридцать вторая
        0.015625: "64",# Шестьдесят четвертая
    }
    return durations.get(duration, "4")  # по умолчанию четвертная

def pitch_to_lilypond(pitch):
    """
    Преобразует питч в формат LilyPond.
    """
    # Разделяем ноту и октаву
    note, octave = pitch[:-1], int(pitch[-1])

    # Преобразуем ноты: заменяем '#' на 'is' для повышения
    if note[-1] == '#':
        lilypond_note = note[:-1].lower() + "s"  # 'F#' -> 'fis'
    elif note.lower() == 'b':
        lilypond_note = 'b'  # 'B' не меняем
    else:
        lilypond_note = note.lower()

    # Обработка октавы
    lilypond_octave = "'" * (octave - 3) if octave >= 2 else "," * (3 - octave)

    return lilypond_note + lilypond_octave

def select_fret_and_string(pitches, simultaneous_play=False):
    """
    Возвращает соответствующие струны и лады для заданных питчей.
    :param pitches: Список питчей (например, ["E4", "G3", "B3"]).
    :param simultaneous_play: Флаг, который указывает, играются ли ноты одновременно.
    :return: Список кортежей (струна, лад) для каждого питча.
    """
    # Стандартное строение гитары (открытые струны)
    guitar_tuning = ["E2", "A2", "D3", "G3", "B3", "E4"]  # от самой низкой (6-я струна) к самой высокой (1-я струна)
    string_pitches = [abjad.NamedPitch(p) for p in guitar_tuning]

    selected_strings_and_frets = []
    used_strings = set()  # Множество для отслеживания использованных струн

    # Для каждого питча
    for pitch in pitches:
        target_pitch = abjad.NamedPitch(pitch)
        best_string, min_fret = None, None

        # Для каждой струны гитары (с самой низкой до самой высокой)
        for i, string_pitch in enumerate(string_pitches):
            # Расстояние между целевой нотой и открытым звуком струны
            fret = int(target_pitch.midi_number) - int(string_pitch.midi_number)

            # Если лад возможен (больше или равен 0) и струна ещё не использована
            if fret >= 0 and (best_string is None or fret < min_fret):
                # Если играются одновременно, ищем разные струны для каждой ноты
                if simultaneous_play:
                    if i + 1 not in used_strings:  # Проверяем, не использована ли эта струна
                        best_string, min_fret = i + 1, fret
                        used_strings.add(i + 1)  # Отметим струну как использованную
                        break
                else:
                    best_string, min_fret = i + 1, fret
                    used_strings.add(i + 1)  # Добавляем струну в использованные
                    break

        # Добавляем в итоговый список выбранную струну и лад
        selected_strings_and_frets.append((best_string, min_fret))

    return selected_strings_and_frets

def generate_lilypond_tab_code(notes):
    """
    Генерация кода табулатуры для LilyPond.
    """
    header = r"""
    \version "2.24.2"
    \paper { #(set-paper-size "a4") }
    \score { <<
    \new TabStaff {
    """
    footer = r"""
        }
        >>
        \layout { }
    }
    """
    notes_lilypond = " ".join(
        [f"<{pitch_to_lilypond(note.pitch)}>{note_duration_to_lilypond(note.duration)}\n"
         for note in notes.notes]  # Доступ к списку нот через notes.notes
    )
    return header + notes_lilypond + footer

def notes_to_tabs(notes, output_path):
    """
    Генерация табулатуры в формате PDF.
    """
    lilypond_code = generate_lilypond_tab_code(notes)
    ly_file_path = output_path.replace(".pdf", ".ly")
    with open(ly_file_path, 'w') as file:
        file.write(lilypond_code)
    lilypond_file = abjad.LilyPondFile(items=[lilypond_code])
    abjad.persist.as_pdf(lilypond_file, output_path)
    print(f"PDF файл сохранён: {output_path}")

def load_json(input_path):
    """
    Загружает данные из JSON файла.
    :param input_path: Путь к файлу.
    :return: Объект с нотами.
    """
    with open(input_path, 'r') as file:
        data = json.load(file)
    notes_array = [Note(note["pitch"], note["duration"], note["velocity"]) for note in data["notesArray"]]
    return Notes(notes_array)

if __name__ == "__main__":
    input_path = f"../data/{file_name}_input.json"  # Путь к JSON-файлу
    output_path = f"../output/{file_name}_TABS.pdf"  # Путь для сохранения

    notes = load_json(input_path)
    notes_to_tabs(notes, output_path)
