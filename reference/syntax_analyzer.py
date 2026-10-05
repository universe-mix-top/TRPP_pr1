from typing import List, Tuple

class SyntaxAnalyzer:
    def __init__(self, lexemes: List[Tuple[int, int]], keywords, delimiters, numbers, identifiers, hide_log):
        self.lexemes = lexemes
        self.keywords = keywords
        self.delimiters = delimiters
        self.numbers = numbers
        self.identifiers = identifiers

        self.pos = 0
        self.LEX: Tuple[int, int] = (0, 0)  # текущая лексема (таблица, индекс)
        self.hide_log = hide_log            # при необходимости скрывает основные логи
        self._gl()                          # прочитать первую лексему

    """Вспомогательные методы"""

    def _gl(self):
        """
        Считать следующую лексему
        :return: None
        """
        if self.pos < len(self.lexemes):
            self.LEX = self.lexemes[self.pos]
            self.pos += 1
        else:
            self.LEX = (0, 0)  # симулируем eof как (0, 0)

    def _lex_str(self) -> str:
        """
        Определеляем тип текущей лексемы для сообщений
        :return: текущая лексема
        """
        tab, idx = self.LEX
        if tab == 1:
            name = self.keywords[idx - 1] if 1 <= idx <= len(self.keywords) else f"kw{idx}"
            return f"КЛЮЧЕВОЕ_СЛОВО('{name}')"
        
        elif tab == 2:
            name = self.delimiters[idx - 1] if 1 <= idx <= len(self.delimiters) else f"del{idx}"
            return f"РАЗДЕЛИТЕЛЬ('{name if name != '\n' else r'\n'}')"
        
        elif tab == 3:
            return f"ЧИСЛО(#{idx})"
        
        elif tab == 4:
            return f"ИДЕНТИФИКАТОР(#{idx})"
        
        else:
            return "EOF"

    def err_proc(self, msg: str):
        """
        Обработка ошибки
        :param msg:
        :return: None
        """
        loc = f"позиция {self.pos}"
        lex = self._lex_str()
        print(f"СИНТАКСИЧЕСКАЯ ОШИБКА ({loc}): {msg}. Текущая лексема: {lex}")
        raise SystemExit(1)

    """Основные методы"""

    def parse(self):
        """
        Разбор программы (используется как точка входа)
        :return: None
        """
        self.PR()
        # После разбора программы ожидаем конец лексем (или симулированный eof)
        if self.LEX != (0, 0):  # если остались еще лексемы (к примеру, лишние ';'), сообщаем об этом
            print("ВНИМАНИЕ: после разбора остались лексемы.")
        print("Синтаксический анализ пройден успешно.")

    def PR(self):
        """
        Программа: {/ (<описание> | <оператор>) ( : | переход строки) /} end
        :return:  None
        """
        if self.EQ("dim"):
            self.DESCR()
        else:
            self.OPER()

        # Дополнительные операторы и описания через ':' или новые строки
        while self.EQ(":") or self.EQ("\n"):
            self._gl()
            if self.EQ(":") or self.EQ("\n"): self._gl()  # если стоит : и переход строки

            # Ждем конец
            if self.EQ("end"):
                break
            if self.EQ("dim"):
                self.DESCR()
            else:
                self.OPER()

        if not self.EQ("end"):
            self.err_proc("Ожидалось ключевое слово 'end'")
        self._gl()
    
    
    """Проверка лексем"""

    def NUM(self) -> bool:
        """
        Является ли текущая лексема числом
        :return:
        """
        return self.LEX[0] == 3 and self.LEX[1] <= len(self.numbers)

    def ID(self) -> bool:
        """
        Является ли текущая лексема идентификатором
        :return: bool
        """
        return self.LEX[0] == 4 and self.LEX[1] <= len(self.identifiers)

    def EQ(self, token: str) -> bool:
        """
        Проверка, соответствует ли текущая лексема терминалу token; для ключевых слов и разделителей
        :param token:
        :return: bool
        """
        tab, idx = self.LEX
        if tab == 1:
            # Ключевое слово
            if 1 <= idx <= len(self.keywords):
                return self.keywords[idx - 1] == token
            return False
        
        elif tab == 2:
            # Разделитель
            if 1 <= idx <= len(self.delimiters):
                return self.delimiters[idx - 1] == token
            return False
        else:
            return False
    
    
    """Проверка соответствия синтаксису"""

    # DESCR ::= dim ID1 ("integer" | "real" | "boolean")
    def DESCR(self):
        if not self.EQ("dim"):
            self.err_proc("Ожидалось ключевое слово 'dim'")
        self._gl()

        self.ID1()

        if not (self.EQ("integer") or self.EQ("real") or self.EQ("boolean")):
            self.err_proc("Ожидался тип (integer | real | boolean)")
        self._gl()

    # Первый идентификатор
    def ID1(self):
        if not self.ID():
            self.err_proc("Ожидался идентификатор в описании переменных")

        self._gl()

        # Дополнительные идентификаторы через запятую
        while self.EQ(","):
            self._gl()
            if not self.ID():
                self.err_proc("Ожидался идентификатор после ','")
            self._gl()

    # Операторы
    def OPER(self):
        
        # Составной: «[» <оператор> { ( : | перевод строки) <оператор> } «]»
        if self.EQ("["):
            self._gl()
            self.OPER()
            while self.EQ(":") or self.EQ("\n"):
                self._gl()
                self.OPER()
            if not self.EQ("]"):
                self.err_proc("Ожидалась ']' для завершения составного оператора")
            self._gl()
            return

        # Присваивание: <идентификатор> as <выражение>
        elif self.ID():
            self._gl()
            if not self.EQ("as"):
                self.err_proc("Ожидался оператор присваивания 'as'")
            self._gl()
            self.COMPARE()
            return

        # Условный: if <выражение> then <оператор> [ else <оператор>]
        elif self.EQ("if"):
            self._gl()
            self.COMPARE()
            if not self.EQ("then"):
                self.err_proc("Ожидалось 'then' после условного оператора if")
            self._gl()
            self.OPER()
            if self.EQ("else"):
                self._gl()
                self.OPER()
            return

        # Фиксированный цикл: for <присваивания> to <выражение> do <оператор>
        elif self.EQ("for"):
            self._gl()
            # ожидаем идентификатор
            if not self.ID():
                self.err_proc("Ожидался идентификатор в for")
            self._gl()
            if not self.EQ("as"):
                self.err_proc("Ожидался оператор присваивания 'as'")
            self._gl()
            self.COMPARE()
            if not self.EQ("to"):
                self.err_proc("Ожидалось 'to' в for")
            self._gl()
            self.COMPARE()
            if not self.EQ("do"):
                self.err_proc("Ожидалось 'do' в for")
            self._gl()
            if self.EQ("\n"):  # если после do есть переход строки
                self._gl()
            self.OPER()
            return

        # Условный цикл: while <выражение> do <оператор>
        elif self.EQ("while"):
            self._gl()
            self.COMPARE()
            if not self.EQ("do"):
                self.err_proc("Ожидалось 'do' после условия в while")
            self._gl()
            if self.EQ("\n"):  # если после do есть переход строки
                self._gl()
            self.OPER()
            return

        # Ввод: read «(»<идентификатор> {, <идентификатор> } «)»
        elif self.EQ("read"):
            self._gl()
            if not self.EQ("("):
                self.err_proc("Ожидалась '(' после ключевого слова 'read'")
            self._gl()
            if not self.ID():
                self.err_proc("Ожидался идентификатор в read")
            self._gl()
            while self.EQ(","):
                self._gl()
                if not self.ID():
                    self.err_proc("Ожидался идентификатор после ',' в read")
                self._gl()
            if not self.EQ(")"):
                self.err_proc("Ожидался ')' в конце read")
            self._gl()
            return

        # Вывод: write «(»<выражение> {, <выражение> } «)»
        elif self.EQ("write"):
            self._gl()
            if not self.EQ("("):
                self.err_proc("Ожидался '(' после 'write'")
            self._gl()
            self.COMPARE()
            while self.EQ(","):
                self._gl()
                self.COMPARE()
            if not self.EQ(")"):
                self.err_proc("Ожидался ')' в конце write")
            self._gl()
            return

        else:
            self.err_proc("Неправильный оператор")

    # Разбор выражений в порядке выполнения
    # COMPARE -> ADD { (NE | EQ | LT | LE | GT | GE) ADD }      имеет низший приоритет
    # ADD -> MULT { (+ | - | or) MULT }                         третий по значимости
    # MULT -> FACT { (* | / | and) FACT }                       второй по значимости
    # FACT -> ID | NUM | true | false | not FACT | (COMPARE)    имеет высший приоритет
    
    def COMPARE(self):
        self.ADD()
        # Операторы сравнения являются разделителями в таблице: NE, EQ, LT, LE, GT, GE
        while self.EQ("NE") or self.EQ("EQ") or self.EQ("LT") or self.EQ("LE") or self.EQ("GT") or self.EQ("GE"):
            self._gl()
            self.ADD()

    def ADD(self):
        self.MULT()
        while self.EQ("plus") or self.EQ("min") or self.EQ("or"):
            self._gl()
            self.MULT()

    def MULT(self):
        self.FACT()
        while self.EQ("mult") or self.EQ("div") or self.EQ("and") or self.EQ("*") or self.EQ("/"):
            self._gl()
            self.FACT()

    def FACT(self):
        # Идентификатор
        if self.ID():
            self._gl()
            return
        
        # Число
        if self.NUM():
            self._gl()
            return
        
        # true/false
        if self.EQ("true") or self.EQ("false"):
            self._gl()
            return
        
        # Отрицание (унарное)
        if self.EQ("~"):
            self._gl()
            self.FACT()
            return
        
        # Выражения в скобках
        if self.EQ("("):
            self._gl()
            self.COMPARE()  # для выражений в скобках снова запускаем рекурсию
            if not self.EQ(")"):
                self.err_proc("Ожидалась ')' в выражении")
            self._gl()
            return
        self.err_proc("Ожидался операнд (ID, NUM, true/false, ~, '(') в FACT")
