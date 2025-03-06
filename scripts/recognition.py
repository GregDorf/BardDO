import parselmouth
import numpy as np
import json
import os
import classes.storage as storage

file_name = storage.load_file_name()

# Функция для округления длительности к ближайшей музыкальной длительности
def round_to_note_duration(duration, tempo):
    quarter_note_duration = 60 / tempo  # Длительность четверти
    note_durations = [quarter_note_duration * (1 / (2 ** i)) for i in range(8)]  # 1, 0.5, 0.25, ...
    closest_duration = min(note_durations, key=lambda x: abs(x - duration))
    return round(closest_duration / quarter_note_duration, 3)

# Функция для преобразования частоты в музыкальную ноту
def hz_to_note(hz):
    if hz == 0:
        return None  # Пауза для нулевой частоты
    note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
    A4 = 440  # Частота ноты A4
    note_number = round(12 * np.log2(hz / A4)) + 69  # Вычисляем номер ноты в музыкальной шкале
    note_index = note_number % 12
    octave = (note_number // 12) - 1
    return f'{note_names[note_index]}{octave}'

# Функция для ограничения нот в диапазоне 6-струнной гитары
def limit_note_range(hz):
    # Диапазон для 6-струнной гитары (E2 ~ E6)
    guitar_min = 82.41  # E2
    guitar_max = 1318.51  # E6
    
    # Если частота выходит за пределы диапазона, сдвигаем октаву
    while hz < guitar_min:
        hz *= 2  # Поднимаем октаву (увеличиваем частоту в два раза)
    while hz > guitar_max:
        hz /= 2  # Понижаем октаву (уменьшаем частоту в два раза)
        
    return hz

# Функция для усиления контраста звука
def enhance_contrast(intensities, contrast_factor=10):
    # Усиливаем пики и уменьшаем слабые звуки с помощью экспоненциального преобразования
    enhanced_intensities = intensities ** contrast_factor
    # Нормализуем результат для предотвращения значений больше 1.0
    enhanced_intensities = np.clip(enhanced_intensities, 0, 1)
    return enhanced_intensities

# Функция для выравнивания пиков интенсивности сигнала
def normalize_peaks(intensities, target_peak=1.0):
    # Приводим интенсивности к целевому пику
    max_intensity = np.max(intensities)
    if max_intensity > 0:
        return intensities * (target_peak / max_intensity)
    return intensities

# Функция для фильтрации интенсивных всплесков (например, при скрежете)
def filter_intensity_spikes(intensities, threshold=0.1):
    # Фильтруем интенсивности, удаляя резкие скачки
    filtered = []
    for i in range(1, len(intensities)):
        if abs(intensities[i] - intensities[i-1]) < threshold:
            filtered.append(intensities[i])
        else:
            filtered.append(intensities[i-1])  # Если скачок большой, заменяем на предыдущую интенсивность
    return np.array(filtered)

# Функция для создания трапециевидной огибающей
def trapezoidal_envelope(signal, rise_time=0.1, fall_time=0.1, sample_rate=22050):
    """Создает трапециевидную огибающую для сигнала."""
    num_samples = len(signal)
    rise_samples = int(rise_time * sample_rate)
    fall_samples = int(fall_time * sample_rate)
    
    # Создание огибающей в форме трапеции
    envelope = np.zeros(num_samples)
    
    # Восходящий фронт
    envelope[:rise_samples] = np.linspace(0, 1, rise_samples)
    
    # Плато
    envelope[rise_samples:num_samples - fall_samples] = 1
    
    # Нисходящий фронт
    envelope[num_samples - fall_samples:] = np.linspace(1, 0, fall_samples)
    
    return signal * envelope

# Функция для извлечения нот и их длительностей
def get_notes_and_durations(wav_file, tempo, intensity_threshold=0.4, contrast_factor=10, max_freq_diff=1.0, intensity_spike_threshold=0.1, decay_threshold=0.2, min_note_duration=0.1):
    # Загружаем аудиофайл с помощью parselmouth
    snd = parselmouth.Sound(wav_file)

    # Извлечение высоты звука (pitch) и интенсивности
    pitch = snd.to_pitch()
    intensity = snd.to_intensity()

    # Конвертируем высоту звука в массив частот
    times = pitch.xs()
    frequencies = pitch.selected_array['frequency']
    intensities = intensity.values.T.flatten()

    # Применяем усиление контраста и выравнивание пиков
    intensities = enhance_contrast(intensities, contrast_factor)
    intensities = normalize_peaks(intensities)

    # Фильтруем резкие изменения интенсивности (скрежет и дрожание)
    intensities = filter_intensity_spikes(intensities, threshold=intensity_spike_threshold)

    # Получаем аудиосигнал
    signal = snd.values.T.flatten()
    sample_rate = snd.xmax / len(signal)

    # Применяем трапециевидную огибающую к сигналу
    signal = trapezoidal_envelope(signal, rise_time=0.05, fall_time=0.05, sample_rate=sample_rate)

    # Параметры для фильтрации
    min_pitch = 50  # Минимальная частота для ноты (в Гц)
    min_intensity = intensity_threshold  # Минимальная громкость (в дБ) для отбора пиков

    # Обработка данных
    notes_data = []
    last_pitch = None
    last_onset_time = 0
    last_duration = 0
    last_freq = None
    last_intensity = None  # для отслеживания интенсивности предыдущей ноты
    current_note_end_time = 0  # Время завершения текущей основной ноты

    for i, freq in enumerate(frequencies):
        if freq < min_pitch or intensities[i] < min_intensity:
            continue  # Пропускаем шумы и тихие сигналы

        # Ограничиваем частоту в пределах диапазона гитары
        freq = limit_note_range(freq)

        # Преобразование частоты в музыкальную ноту
        pitch_note = hz_to_note(freq)

        # Защита от раздвоения нот
        if last_pitch and abs(freq - last_freq) < max_freq_diff:
            # Приводим частоту к основной частоте, если разница мала
            pitch_note = last_pitch

        # Временные метки
        current_time = times[i]

        # Если интенсивность упала ниже порога и остаётся на этом уровне, нота считается затухающей
        if last_intensity and intensities[i] < decay_threshold and last_intensity > decay_threshold:
            # Затухающая нота, больше не обрабатываем
            continue

        # Если ноты одинаковые и идут очень быстро, увеличиваем длительность
        if pitch_note == last_pitch:
            if (current_time - last_onset_time) < 0.3:
                last_duration += (current_time - last_onset_time)
            else:
                # Если интервал между одинаковыми нотами больше 0.3, добавляем ноту
                notes_data.append({
                    "pitch": last_pitch,
                    "duration": round_to_note_duration(last_duration, tempo),
                    "velocity": 85
                })
                last_duration = 0  # Сброс длительности
        else:
            if last_pitch:
                # Добавляем предыдущую ноту, если её длительность больше минимальной
                if last_duration >= min_note_duration:
                    notes_data.append({
                        "pitch": last_pitch,
                        "duration": round_to_note_duration(last_duration, tempo),
                        "velocity": 85
                    })
            last_pitch = pitch_note
            last_duration = 0

        last_onset_time = current_time
        last_freq = freq  # Сохраняем последнюю частоту для сравнения
        last_intensity = intensities[i]  # Обновляем интенсивность

    # Добавляем последнюю ноту, если её длительность больше минимальной
    if last_pitch and last_duration >= min_note_duration:
        notes_data.append({
            "pitch": last_pitch,
            "duration": round_to_note_duration(last_duration, tempo),
            "velocity": 85
        })

    return notes_data

# Путь к файлам
input_path = f"../input/{file_name}.wav"
output_path = f"../data/{file_name}_input.json"

# Укажите темп (ударов в минуту)
tempo = 120

# Получаем данные о нотах
notes_data = get_notes_and_durations(input_path, tempo)

# Формируем JSON-структуру
output_data = {
    "notesArray": notes_data
}

# Сохраняем в файл
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as json_file:
    json.dump(output_data, json_file, indent=4, ensure_ascii=False)

print(f"Мелодия успешно преобразована в {output_path}")
