import os
import subprocess
import telebot
from telebot import types
import scripts.classes.storage as storage

bot = telebot.TeleBot('')

user_files = {}

# Папка для сохранения файлов
input_folder = os.path.join(os.getcwd(), 'input')

# Убедимся, что папка существует
if not os.path.exists(input_folder):
    os.makedirs(input_folder)

def exec_script(script_path):
    """
    Выполнение Python-скрипта через subprocess.
    Возвращает True, если выполнение прошло успешно, иначе False.
    """
    try:
        script_dir, script_name = os.path.split(script_path)
        command = f'cd "{script_dir}" && python "{script_name}"'

        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"Скрипт {script_name} успешно выполнен.")
            return True
        else:
            print(f"Ошибка выполнения {script_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"Ошибка выполнения скрипта {script_path}: {e}")
        return False

def send_result_file(chat_id, result_file_path, file_caption):
    """
    Отправка файла результата пользователю.
    """
    try:
        with open(result_file_path, 'rb') as file:
            bot.send_document(chat_id, file, caption=file_caption)
    except Exception as e:
        print(f"Ошибка при отправке файла: {e}")
        bot.send_message(chat_id, f"❌ Ошибка при отправке файла: {e}")

def show_main_menu(chat_id):
    """
    Главное меню с кнопками "Начать", "FAQ", "Поддержка".
    """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🚀 Начать!', callback_data='go')
    btn2 = types.InlineKeyboardButton('FAQ ⁉️', callback_data='info')
    btn3 = types.InlineKeyboardButton('✍️ Поддержка', callback_data='help')
    markup.row(btn1)
    markup.row(btn2, btn3)

    file = open('photo.jpg', 'rb')  # Изображение для приветственного сообщения
    bot.send_photo(
        chat_id,
        file,
        caption='🎵 Привет, я твой музыкальный помощник!\n\n'
                'Готов помочь с:\n'
                '- Преобразованием в MIDI\n'
                '- Созданием нот\n'
                '- Построением табулатур.\n\n'
                '🚀 Нажмите "Начать", чтобы загрузить файл.',
        parse_mode='html',
        reply_markup=markup
    )

def show_info(chat_id):
    """
    Меню FAQ.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='main_menu'))
    bot.send_message(chat_id, 'ℹ️ FAQ: Нажмите кнопку начать, скиньте файл и выберите что вам нужно.', reply_markup=markup)

def show_help(chat_id):
    """
    Меню поддержки.
    """
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='main_menu'))
    bot.send_message(chat_id, '✍️ Напишите нам: @Gr0G0R', reply_markup=markup)

def show_go(chat_id):
    """
    Меню выбора действия с загруженным файлом.
    """
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton('🔄 Преобразовать в MIDI', callback_data='midi')
    btn2 = types.InlineKeyboardButton('🎼 Создать ноты', callback_data='nots')
    btn3 = types.InlineKeyboardButton('🎸 Построить табулатуры', callback_data='tabulatures')
    btn4 = types.InlineKeyboardButton('⬅️ Назад', callback_data='main_menu')
    markup.add(btn1, btn2, btn3, btn4)

    bot.send_message(
        chat_id,
        '🎶 Файл загружен! Выберите действие:',
        parse_mode='html',
        reply_markup=markup
    )

def process_action(action, chat_id):
    """
    Обработка действий (MIDI, ноты, табулатуры).
    """
    scripts = {
        'midi': 'scripts/notes_to_midi.py',
        'nots': 'scripts/notes_to_sheet_music.py',
        'tabulatures': 'scripts/notes_to_tabs.py'
    }

    if chat_id not in user_files:
        bot.send_message(chat_id, "❌ Сначала загрузите файл.")
        return

    file_info = user_files[chat_id]
    file_name = file_info['file_name']
    storage.save_file_name(file_name)

    recognition_script = os.path.join(os.getcwd(), 'scripts', 'recognition.py')
    if not os.path.exists(recognition_script):
        bot.send_message(chat_id, "❌ Скрипт распознавания не найден.")
        return

    # Шаг 1: Запуск скрипта распознавания
    bot.send_message(chat_id, "🔄 Запуск распознавания...")
    if not exec_script(recognition_script):
        bot.send_message(chat_id, "❌ Ошибка распознавания файла.")
        return

    # Шаг 2: Запуск выбранного действия
    if action in scripts:
        action_script = os.path.join(os.getcwd(), scripts[action])
        bot.send_message(chat_id, f"🔄 Выполнение действия: {action}...")
        if not exec_script(action_script):
            bot.send_message(chat_id, f"❌ Ошибка выполнения действия: {action}.")
            return

        file_name = storage.load_file_name()

        result_files = {
            'midi': f'output/{file_name}_MIDI.mid',
            'nots': f'output/{file_name}_NOTES.pdf',
            'tabulatures': f'output/{file_name}_TABS.pdf'
        }

        result_file_path = os.path.join(os.getcwd(), result_files[action])
        send_result_file(chat_id, result_file_path, f"Вот ваш результат: {action}!")
    else:
        bot.send_message(chat_id, "❌ Неверное действие.")

def convert_to_wav(file_path):
    """
    Конвертация файла в формат WAV с помощью ffmpeg.
    Заменяет исходный файл на WAV.
    """
    try:
        # Формируем путь для выходного WAV
        output_file = os.path.splitext(file_path)[0] + '.wav'

        # Конвертация в формат WAV
        command = f'ffmpeg -y -i "{file_path}" -vn -acodec pcm_s16le -ar 44100 -ac 2 "{output_file}"'
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode != 0:
            print(f"Ошибка при конвертации: {result.stderr}")
            return None

        print(f"Файл успешно преобразован в WAV: {output_file}")

        # Удаляем исходный файл
        os.remove(file_path)
        print(f"Удалён исходный файл: {file_path}")

        return output_file
    except Exception as e:
        print(f"Ошибка при конвертации файла {file_path}: {e}")
        return None


@bot.callback_query_handler(func=lambda callback: True)
def handle_callback(callback):
    chat_id = callback.message.chat.id
    bot.delete_message(chat_id, callback.message.message_id)

    if callback.data == 'go':
        bot.send_message(chat_id, "🎶 Загрузите аудиофайл или голосовое сообщение.")
    elif callback.data == 'info':
        show_info(chat_id)
    elif callback.data == 'help':
        show_help(chat_id)
    elif callback.data == 'main_menu':
        show_main_menu(chat_id)
    elif callback.data in ['midi', 'nots', 'tabulatures']:
        process_action(callback.data, chat_id)

@bot.message_handler(commands=['start', 'menu'])
def start(message):
    show_main_menu(message.chat.id)

@bot.message_handler(content_types=['audio', 'document', 'voice'])
def handle_file(message):
    chat_id = message.chat.id
    file_id = None
    file_name = None

    # Обработка загруженного файла
    if message.content_type == 'document':
        file_name = message.document.file_name
        file_id = message.document.file_id
    elif message.content_type == 'audio':
        file_name = message.audio.file_name or f"{message.audio.file_id}.mp3"
        file_id = message.audio.file_id
    elif message.content_type == 'voice':
        file_name = f"{message.voice.file_id}.ogg"
        file_id = message.voice.file_id

    if file_id and file_name:
        file_info = bot.get_file(file_id)
        file_path = os.path.join(input_folder, file_name)

        # Скачиваем файл
        downloaded_file = bot.download_file(file_info.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Если файл MP3 или OGG, конвертируем в WAV
        if file_name.endswith(('.mp3', '.ogg')):
            converted_file = convert_to_wav(file_path)
            if converted_file:
                user_files[chat_id] = {'file_id': file_id, 'file_name': os.path.basename(converted_file)}
                bot.reply_to(message, f"Файл {file_name} преобразован в WAV. Выберите действие!")
                show_go(chat_id)
            else:
                bot.reply_to(message, "❌ Ошибка при конвертации файла.")
        elif file_name.endswith('.wav'):
            user_files[chat_id] = {'file_id': file_id, 'file_name': file_name}
            bot.reply_to(message, f"Файл {file_name} получен. Выберите действие!")
            show_go(chat_id)
        else:
            bot.reply_to(message, "❌ Неподдерживаемый формат файла. Пожалуйста, загрузите MP3, WAV или OGG.")
    else:
        bot.reply_to(message, "❌ Не удалось обработать файл. Попробуйте ещё раз.")

bot.polling(none_stop=True)
