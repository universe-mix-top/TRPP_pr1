from typing import List, Tuple, Optional


class LexicalAnalyzer:
    class State:
        """
        S       состояние ожидания нового токена (начальное состояние)
        I       состояние обработки буквы
        N2      двоичное число
        N8      восьмеричное число
        N10     десятичное число
        N16     шестнадцатеричное число
        B       суффикс двоичного числа
        O       суффикс восьмеричного числа
        D       суффикс десятеричного числа
        H       суффикс шестнадцатеричного числа
        FRAC    начало дробной части действительного числа (после точки)
        SIGN    знак из порядка (возможный после 'E'/'e')
        DE      разделители
        C       комментарии
        K       завершение
        ER      ошибка
        """
        S = "S"  # состояние ожидания нового токена (начальное состояние)
        I = "I"  # состояние обработки буквы
        N2 = "N2"  # двоичное число
        N8 = "N8"  # восьмеричное число
        N10 = "N10"  # десятичное число
        N16 = "N16"  # шестнадцатеричное число
        B = "B"  # суффикс двоичного числа
        O = "O"  # суффикс восьмеричного числа
        D = "D"  # суффикс десятеричного числа
        H = "H"  # суффикс шестнадцатеричного числа
        FRAC = "FRAC"  # начало дробной части действительного числа (после точки)
        SIGN = "SIGN"  # знак из порядка (возможный после 'E'/'e')
        DE = "DE"  # разделители
        C = "C"  # комментарии
        K = "K"  # завершение
        ER = "ER"  # ошибка

    def __init__(self, text: str, hide_log):
        self.text = text  # входной текст
        self.pos = 0  # текущая позиция во входном тексте
        self.current_char = ''  # текущий обрабатываемый символ
        self.state = self.State.S  # текущее состояние (сейчас начальное)
        self.token_buffer = ""  # буфер для накопления символов токена
        self.lexemes: List[
            Tuple[int, int]] = []  # список распознанных лексем в виде (номер_таблицы, положение_в_таблице)
        self.current_table_index = 0  # временное хранилище индекса последней добавленной лексемы в таблице
        self.line_number = 1  # номер текущей строки
        self.token_start_line = 1  # номер строки, на которой начинается токен
        self.hide_log = hide_log  # при необходимости скрывает основные логи

        """Таблицы лексем"""

        # Ключевые слова
        self.keywords = [
            "dim", "end",
            "if", "then", "else",
            "for", "to", "do", "while",
            "read", "write", "as",
            "true", "false"
        ]

        # Разделители
        self.delimiters = [
            ";", ":", ",", ".",
            "(", ")", "[", "]",
            "integer", "real", "boolean",
            "NE", "EQ", "LT", "LE", "GT", "GE",
            "plus", "min", "or",
            "mult", "div", "and",
            "~", "\n"
        ]

        # Числа
        self.numbers = []

        # Идентификаторы
        self.identifiers = []

    """Вспомогательные методы"""

    def _gc(self) -> bool:
        """
        Считывает следующий символ из входного текста.
        Возвращает True если файл закончился
        :return: bool
        """
        if self.pos < len(self.text):
            self.current_char = self.text[self.pos]
            self.pos += 1
            if self.current_char == '\n':  # перенос строки в файле
                self.line_number += 1
            return False

        self.current_char = ''
        return True  # достигнут конец текста - возвращаем True

    def _nill(self):
        """
        Очистка буфера токена
        :return: None
        """
        self.token_buffer = ""

    def _add(self):
        """
        Добавление символа в буфер токена
        :return: None
        """
        self.token_buffer += self.current_char

    def _is_letter(self) -> bool:
        """
        Проверка, является ли текущий символ буквой
        :return: bool
        """
        return self.current_char.isalpha() or self.current_char == "_"

    def _is_digit(self) -> bool:
        """
        Проверка, является ли текущий символ цифрой
        :return: bool
        """
        return self.current_char.isdigit()

    def _is_hex_char(self) -> bool:
        """
        Проверка, является ли текущий символ цифрой шестнадцатеричного числа
        :return: bool
        """
        return self._is_digit() or self.current_char.upper() in "ABCDEF"

    def _is_whitespace(self) -> bool:
        """
        Проверка, является ли текущий символ пустым пространством
        :return:  bool
        """
        return self.current_char in ' \t\r'  # пробел, табуляция, перенос строки или возврат каретки

    def _look(self, table: List[str]) -> int:
        """
        Ищет токен в таблице и возвращает его позицию + 1, если найден; иначе 0
        Применяется для таблицы ключевых слов и разделителей
        :param table:
        :return: int
        """
        try:
            return table.index(self.token_buffer) + 1
        except ValueError:
            return 0

    def _put(self, table: list) -> int:
        """
        Добавляет токен в указанную таблицу (если его там ещё нет) и возвращает его позицию.
        Применяется для таблиц чисел и идентификаторов, формируемых динамически
        :param table:
        :return: int
        """
        if self.token_buffer in table:
            return table.index(self.token_buffer) + 1  # если токен уже в таблице, возвращаем его позицию

        table.append(self.token_buffer)  # добавляем токен
        return len(table)

    def _emit(self, table_type: int, index: int):
        """
        Формирует лексему в виде пары (номер_таблицы, позиция_в_таблице) и добавляет её в список распознанных лексем
        :param table_type:
        :param index:
        :return: None
        """
        self.lexemes.append((table_type, index))
        if not self.hide_log:
            if self.token_buffer == "\n":
                print(
                    f"- Лексема: {r"\n":20s} => ({table_type},{index}). \tСтрока: {self.token_start_line} \tНомер: {len(self.lexemes)}")
                return
            print(
                f"- Лексема: {self.token_buffer:20s} => ({table_type},{index}). \tСтрока: {self.token_start_line} \tНомер: {len(self.lexemes)}")

    def _convert_to_int(self, base: int):
        """
        Преобразует токен, представляющий целое число с суффиксом (B, O, D, H), в десятичную форму
        :param base:
        :return: None
        """
        try:
            num_str = self.token_buffer[:-1]  # убираем суффикс (B, O, D, H)
            self.token_buffer = str(int(num_str, base))
        except Exception:
            self._error(f"Некорректное число в системе счисления {base}")

    def _convert_to_float(self):
        """
        Преобразует токен, представляющий действительное число в строковое представление с плавающей точкой
        :return: None
        """
        try:
            self.token_buffer = str(float(self.token_buffer))
        except Exception:
            self._error("Некорректное действительное число")

    def _error(self, message: str):
        """
        Фиксирует лексическую ошибку, выводит сообщение с указанием строки и переводит анализатор в состояние ошибки
        :param message:
        :return: None
        """
        print(f"ЛЕКСИЧЕСКАЯ ОШИБКА (строка {self.line_number}): {message}")
        self.state = self.State.ER

    """Обработка состояний"""

    # Начальное состояние
    def _handle_start(self, eof: bool) -> bool:
        while self._is_whitespace() and not eof:  # пропускаем пробелы
            eof = self._gc()
        if eof:
            self.state = self.State.K  # в конце файла устанавливаем конечное состояние 
            return True

        self.token_start_line = self.line_number  # сохраняем строку начала токена

        if self.current_char == '{':  # распознаем комментарии
            self._nill()
            self._gc()  # пропустить '{'
            self.state = self.State.C
            return False  # не возвращаться в S сразу

        if self._is_letter():
            self._nill()
            self._add()
            self._gc()
            self.state = self.State.I

        elif self.current_char in '01':
            self._nill()
            self._add()
            self._gc()
            self.state = self.State.N2

        elif self.current_char in '234567':
            self._nill()
            self._add()
            self._gc()
            self.state = self.State.N8

        elif self.current_char in '89':
            self._nill()
            self._add()
            self._gc()
            self.state = self.State.N10

        elif self.current_char == '.':  # дробное число
            self._nill()
            self._add()
            self._gc()
            self.state = self.State.FRAC

        else:
            self._nill()
            self._add()
            self.state = self.State.DE

        return False

    def _handle_comment(self, eof: bool):
        """
        Обработка комментариев
        :param eof:
        :return: None
        """
        # [ОШИБКА 1 — Интерфейсная/вывод]
        # Чтение символов комментария выполняется напрямую из self.text,
        # минуя метод _gc(). Из-за этого self.line_number НЕ инкрементируется
        # при встрече '\n' внутри многострочного комментария.
        # Последующие ошибки будут содержать неверный номер строки.
        while not eof and self.current_char != '}':
            self.pos += 1
            if self.pos < len(self.text):
                self.current_char = self.text[self.pos]
                eof = False
            else:
                self.current_char = ''
                eof = True
        if eof:
            self._error("Комментарий не закрыт '}'")
        else:
            # Прочитали '}' — выходим из комментария
            self.pos += 1
            if self.pos < len(self.text):
                self.current_char = self.text[self.pos]
            else:
                self.current_char = ''
            self.state = self.State.S

    def _handle_identifier(self, eof: bool):
        """
        Обработка идентификатора
        :param eof:
        :return: None
        """
        # Собираем токен
        while (self._is_letter() or self._is_digit()) and not eof:
            self._add()
            eof = self._gc()

        kw_index = self._look(self.keywords)  # ищем токен в таблице ключевых слов
        if kw_index:
            # Если найден, формируем лексему из таблицы ключевых слов
            self._emit(1, kw_index)
            self.state = self.State.S
            return

        # Разделителями также считаются, например, операции сравнения - проверяем их
        delim_index = self._look(self.delimiters)
        if delim_index:
            self._emit(2, delim_index)
            self.state = self.State.S
            return

        elif self.token_buffer[-1] in "Hh" and len(self.token_buffer) != 1:
            self._handle_hex(eof)
            return
        else:
            # Иначе формируем лексему в таблице идентификаторов
            self.current_table_index = self._put(self.identifiers)
            self._emit(4, self.current_table_index)

        self.state = self.State.S  # ожидаем новый токен

    # Окончательная обработка числа
    def _finalize_number(self):
        """
        Окончательная обработка числа
        :return: None
        """
        # Формируем лексему в таблице чисел
        self.current_table_index = self._put(self.numbers)
        self._emit(3, self.current_table_index)

        self.state = self.State.S

    def _handle_binary(self, eof: bool):
        """
        Обработка двоичных чисел
        :param eof:
        :return: None
        """
        while self.current_char in '01' and not eof:
            self._add()
            eof = self._gc()

        # После двоичных цифр возможны:
        if self.current_char in '234567':
            self._add()
            self._gc()
            self.state = self.State.N8

        elif self.current_char in '89':
            self._add()
            self._gc()
            self.state = self.State.N10

        elif self.current_char in 'Bb':
            self._add()
            self._gc()
            self.state = self.State.B

        elif self.current_char in 'Oo':
            self._add()
            self._gc()
            self.state = self.State.O

        elif self.current_char in 'Dd':
            self._add()
            self._gc()
            self.state = self.State.D

        elif self.current_char == '.':
            self._add()
            self._gc()
            self.state = self.State.FRAC

        elif self.current_char in 'Ee':
            self._add()
            self._gc()
            self.state = self.State.SIGN

        elif self._is_hex_char():  # Шестнадцатеричные символы A-F
            self._add()
            self._gc()
            self.state = self.State.N16

        elif self.current_char in 'Hh':
            self._add()
            self._gc()
            self.state = self.State.H

        elif self._is_letter():
            # Любая другая буква — ошибка
            self._error(f"Недопустимый символ после двоичного числа: {self.token_buffer + self.current_char}")
        else:
            self._finalize_number()

    # Обработка восьмеричных чисел
    def _handle_octal(self, eof: bool):
        """
        Обработка восьмеричных чисел
        :param eof:
        :return: None
        """
        while self.current_char in '01234567' and not eof:
            self._add()
            eof = self._gc()

        if self.current_char in '89':
            self._add()
            self._gc()
            self.state = self.State.N10

        elif self.current_char in 'Oo':
            self._add()
            self._gc()
            self.state = self.State.O

        elif self.current_char in 'Dd':
            self._add()
            self._gc()
            self.state = self.State.D

        elif self.current_char == '.':
            self._add()
            self._gc()
            self.state = self.State.FRAC

        elif self.current_char in 'Ee':
            self._add()
            self._gc()
            self.state = self.State.SIGN

        elif self._is_hex_char():  # Шестнадцатеричные символы A-F
            self._add()
            self._gc()
            self.state = self.State.N16

        elif self.current_char in 'Hh':
            self._add()
            self._gc()
            self.state = self.State.H

        elif self._is_letter():
            self._error(f"Недопустимый символ после восьмеричного числа: {self.token_buffer + self.current_char}")
        else:
            self._finalize_number()

    def _handle_decimal(self, eof: bool):
        """
        Обработка десятичных чисел
        :param eof:
        :return: None
        """
        while self._is_digit() and not eof:
            self._add()
            eof = self._gc()

        if self.current_char in 'Dd':
            self._add()
            self._gc()
            self.state = self.State.D

        elif self.current_char == '.':
            self._add()
            self._gc()
            self.state = self.State.FRAC

        elif self.current_char in 'Ee':
            self._add()
            self._gc()
            self.state = self.State.SIGN

        elif self._is_hex_char():  # Шестнадцатеричные символы A-F
            self._add()
            self._gc()
            self.state = self.State.N16

        elif self.current_char in 'Hh':
            self._add()
            self._gc()
            self.state = self.State.H

        elif self._is_letter():
            self._error(f"Недопустимый символ после десятичного числа: {self.token_buffer + self.current_char}")
        else:
            self._finalize_number()

    def _handle_hex(self, eof: bool):
        """
        Обработка шестнадцатеричных чисел
        :param eof:
        :return: None
        """
        while self._is_hex_char() and not eof:
            self._add()
            eof = self._gc()

        if self.current_char in 'Hh':
            self._add()
            self._gc()
            self.state = self.State.H
        elif self._is_letter():
            self._error(f"Недопустимый символ в шестнадцатеричном числе: {self.token_buffer + self.current_char}")
        elif self.token_buffer[0].isalpha():
            self._error(f"Шестнадцатеричное число не может начинаться с буквы: {self.token_buffer + self.current_char}")
        else:
            self._error("Шестнадцатеричное число должно заканчиваться на H/h")

    def _handle_hex_prefix(self):
        """
        Обработка префикса шестнадцатеричных чисел
        :return: None
        """
        if self._is_letter():
            self._error(f"Недопустимый символ перед 'H': {self.token_buffer + self.current_char}")
        else:
            self._convert_to_int(16)
            self._finalize_number()

    # Обработка дробных чисел
    def _handle_float(self, eof: bool):
        """
        Обработка дробных чисел
        :param eof:
        :return: None
        """
        if not self._is_digit():
            self._error("Ожидалась цифра после точки")
            return

        self._add()
        eof = self._gc()
        while self._is_digit() and not eof:
            self._add()
            eof = self._gc()

        if self.current_char in 'Ee':
            self._add()
            self._gc()
            self.state = self.State.SIGN
        elif self._is_letter():
            self._error(f"Недопустимый символ в дробной части: {self.token_buffer + self.current_char}")
        else:
            self._convert_to_float()
            self._finalize_number()

    # Обработка экспоненты (E/e)
    def _handle_exponent(self, eof: bool):
        """
        Обработка экспоненты (E/e)
        :param eof:
        :return: None
        """
        if self.current_char in '+-':
            self._add()
            eof = self._gc()

        if not self._is_digit():
            self._error("Ожидалась цифра после E[+-]")
            return

        while self._is_digit() and not eof:
            self._add()
            eof = self._gc()

        if self._is_letter() and self.current_char not in 'Hh':
            self._error(f"Недопустимый символ после экспоненты: {self.token_buffer + self.current_char}")
        elif self.current_char in 'Hh':
            self._error("E/e не используется в шестнадцатеричных числах")
        else:
            self._convert_to_float()
            self._finalize_number()

    # Обработка разделителей
    def _handle_delimiter(self, eof: bool):
        """
        Обработка разделителей
        :param eof:
        :return: None
        """
        delim_index = self._look(self.delimiters)

        if delim_index:
            self._emit(2, delim_index)
            self._gc()
            self.state = self.State.S
        else:
            self._error(f"Неизвестный символ: '{self.token_buffer}'")

    """Основной цикл"""

    def scanner(self) -> List[Tuple[int, int]]:
        eof = self._gc()  # инициализируем end of file

        # Обрабатываем текст до конечного состояния или ошибки
        while self.state not in (self.State.K, self.State.ER):
            if self.state == self.State.S:
                if self._handle_start(eof):
                    continue

            elif self.state == self.State.C:
                self._handle_comment(eof)

            elif self.state == self.State.I:
                self._handle_identifier(eof)

            elif self.state == self.State.N2:
                self._handle_binary(eof)

            elif self.state == self.State.N8:
                self._handle_octal(eof)

            elif self.state == self.State.N10:
                self._handle_decimal(eof)

            elif self.state == self.State.N16:
                self._handle_hex(eof)

            elif self.state == self.State.B:
                if self._is_letter():
                    self._error(f"Недопустимый символ после 'B': {self.token_buffer + self.current_char}")
                else:
                    self._convert_to_int(2)
                    self._finalize_number()

            elif self.state == self.State.O:
                if self._is_letter():
                    self._error(f"Недопустимый символ после 'O': {self.token_buffer + self.current_char}")
                else:
                    self._convert_to_int(8)
                    self._finalize_number()

            elif self.state == self.State.D:
                if self._is_letter():
                    self._error(f"Недопустимый символ после 'D': {self.token_buffer + self.current_char}")
                else:
                    self.token_buffer = self.token_buffer[:-1]  # обрезаем D
                    self._finalize_number()  # уже десятичное

            elif self.state == self.State.H:
                self._handle_hex_prefix()

            elif self.state == self.State.FRAC:
                self._handle_float(eof)

            elif self.state == self.State.SIGN:
                self._handle_exponent(eof)

            elif self.state == self.State.DE:
                self._handle_delimiter(eof)

            else:
                self._error("Неизвестное состояние")

        return self.lexemes
