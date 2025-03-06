import sys
import os
from mido import Message, MidiFile, MidiTrack, MetaMessage
import classes.storage as storage

file_name = storage.load_file_name()

# Добавляем путь к папке scripts для импорта классов
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "scripts")))

from classes.notes import Notes, Note


def notes_to_midi(notes: Notes, output_path: str) -> None:
    """
    Преобразование объекта Notes в MIDI-файл.

    :param notes: Объект Notes, содержащий список нот.
    :param output_path: Путь для сохранения MIDI-файла.
    """
    midi = MidiFile()  # Создаем MIDI-файл
    track = MidiTrack()  # Создаем трек
    midi.tracks.append(track)  # Добавляем трек в MIDI-файл

    # Выбираем темп
    tempo_microseconds_per_beat = 60000000 // 120
    track.append(MetaMessage('set_tempo', tempo=tempo_microseconds_per_beat))

    # Переводим каждую ноту в MIDI-сообщение
    for note in notes.notes:
        # Преобразуем тон ноты в MIDI-число
        midi_note = note_to_midi_number(note.pitch)
        # Добавляем MIDI-сообщения: нота зажата и отпущена
        track.append(Message('note_on', note=midi_note, velocity=note.velocity, time=0))
        track.append(Message('note_off', note=midi_note, velocity=note.velocity, time=int(note.duration * 480)))

    # Сохраняем MIDI-файл
    midi.save(output_path)


def note_to_midi_number(note: str) -> int:
    """
    Преобразование тона ноты в MIDI-номер.

    :param note: Тон ноты (например, "C4").
    :return: MIDI-номер.
    """
    # Таблица для преобразования нот
    note_base = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
    octave = int(note[-1])  # Извлекаем октаву
    pitch = note[:-1]  # Извлекаем тон (без октавы)

    # Рассчитываем MIDI-номер
    midi_number = 12 * (octave + 1) + note_base[pitch]

    return midi_number


if __name__ == "__main__":
    input_path = f"../data/{file_name}_input.json"  # Путь к JSON-файлу
    output_path = f"../output/{file_name}_MIDI.mid"  # Путь для сохранения MIDI-файла

    # Загружаем JSON и преобразуем в Notes
    from json_to_notes import load_json
    notes = load_json(input_path)

    # Генерируем MIDI-файл
    notes_to_midi(notes, output_path)
    print(f"MIDI-файл успешно создан: {output_path}")
