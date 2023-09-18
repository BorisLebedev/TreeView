""" Модуль содержит различные функции, используемые в других модулях """

import re
import time
from datetime import datetime

from PyQt5.QtGui import QFont
from PyQt5.QtGui import QFontMetrics
from pandas import isnull

from STC.config.config import CONFIG


def pixel_size_excel(text):
    """ Возвращает длину текста в пикселях.
        Используется при создании маршрутных карт """
    font = QFont("Times", 12)
    return QFontMetrics(font).width(text)


def text_slicer(text: str, max_len: int) -> list[str]:
    """ Нарезка строки на несколько по длине """
    word_exception = CONFIG.data['excel_document']['word_exception'].split(',')
    if pixel_size_excel(text) > max_len:
        word_list = text.split(' ')
        new_text_list = []
        text_line = ''
        previous_word = ''
        for word in word_list:
            if word in word_exception:
                previous_word = word
            else:
                if previous_word:
                    word = f'{previous_word} {word}'
                if pixel_size_excel(f'{text_line}{word} ') < max_len:
                    text_line = f'{text_line}{word} '
                else:
                    if text_line:
                        new_text_list.append(text_line.rstrip())
                    text_line = f'{word} '
                previous_word = ''
        new_text_list.append(text_line.rstrip())
        return new_text_list
    return [text]


def benchmark(func):
    """ Декоратор для замера времени выполнения """

    def wrapper(*args, **kwargs):
        start = time.time()
        return_value = func(*args, **kwargs)
        end = time.time()
        print(f'Время выполнения: {round(end - start, 3)} секунд.')
        return return_value
    return wrapper


def date_format(date: datetime) -> str:
    """ Возвращает строку с датой """
    if date and date != datetime.min:
        date = date.strftime('%d.%m.%Y %H:%M')
        return date
    return ''


def is_complex(deno: str) -> bool:
    """ Является ли документ составным исходя из
        децимального номера в таблице регистрации
        технологических документов """
    deno = deno.replace(' ', '')
    if re.fullmatch('Всоставе' + r'\w{4}.\d{5}.\d{5}', deno):
        return True
    return False


def product_quantity(str_num: str) -> int | float:
    """ Представление количества в иерархической таблице """
    try:
        return int(str_num)
    except ValueError:
        try:
            return float(str_num.replace(",", "."))
        except ValueError:
            return 0


def sort_un(list_of_items: list) -> list:
    """ Возвращает сортированный список уникальных значений """
    return sorted(list(set(list_of_items)))


def null_cleaner(value):
    """ Изменяет null на None """
    if isnull(value):
        return None
    return value


def none_to_unknown_str(value: None | str) -> str:
    """ Возвращает текст если значение None """
    if value is None:
        return 'Неизвестно'
    return value


def add_missing_keys(dictionary: dict, keys: list[str]) -> dict:
    """ Добавляет отсутствующие ключи в словарь """
    for key in keys:
        if key not in dictionary:
            dictionary[key] = None
    return dictionary


def join_deno(code_org: str, code_class: str, num: str, ver: str = '') -> str | None:
    """ Функция сборки децимального номера """
    if len(code_class) == 6:
        deno = '.'.join([code_org, code_class, num])
        if ver != '':
            deno = f'{deno}-{ver}'
    elif len(code_class) == 5:
        deno = f'{code_org}.{code_class}-{num}'
    else:
        return None
    return deno


def deno_to_components(deno: str) -> tuple[str, str, str, str]:
    """ Функция разделения децимального номера на составляющие """
    # 0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21
    # А  Б  В  Г  .  1  2  3  4  5  6  .  1  2  3  -  1  2  3  .  1  2
    # А  Б  В  Г  .  1  2  3  4  5  -  1  2
    if re.fullmatch(r'\w{4}[.]\d{5}-\d{2}', deno):
        code_org = deno[0:4]
        code_class = deno[5:10]
        num = deno[11:]
        ver = ''
    elif re.fullmatch(r'\w{4}[.]\d{6}[.]\d{3}', deno):
        code_org = deno[0:4]
        code_class = deno[5:11]
        num = deno[12:]
        ver = ''
    elif re.fullmatch(r'\w{4}[.]\d{6}[.]\d{3}-\d{2,3}', deno):
        code_org = deno[0:4]
        code_class = deno[5:11]
        num = deno[12:15]
        ver = deno[16:]
    elif re.fullmatch(r'\w{4}[.]\d{6}[.]\d{3}-\d{2,3}[.]\d{2}', deno):
        code_org = deno[0:4]
        code_class = deno[5:11]
        num = deno[12:15]
        ver = deno[16:]
    else:
        code_org = None
        code_class = None
        num = None
        ver = None
    return code_org, code_class, num, ver


def upd_attrs(obj, **attrs):
    """ Изменяет аттрибут класса если такой
        аттрибут у класса имеется """
    for attr, value in attrs.items():
        if hasattr(obj, attr) and value is not None:
            setattr(obj, attr, value)
