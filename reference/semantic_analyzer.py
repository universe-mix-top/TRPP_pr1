class SemanticAnalyzer:
    def __init__(self, lexemes, keywords, delimiters, numbers, identifiers, hide_log):
        self.lexemes = lexemes
        self.keywords = keywords
        self.delimiters = delimiters
        self.numbers = numbers
        self.identifiers = identifiers

        self.declared = set()       # объявленные переменные
        self.used = []              # все упоминания переменных
        self.errors = []            # ошибки
        self.line_number = 1        # номер текущей строки
        self.hide_log = hide_log    # при необходимости скрывает основные логи

    # Семантическая проверка: каждая переменная должна быть объявлена в секции var
    def analyze_used_vars(self):
        declaration_mode = False    # режим объявления переменных
        use_mode = False            # режим использования переменных в теле программы

        # Перебираем все лексемы
        i = 0
        while i < len(self.lexemes):    
            tab, idx = self.lexemes[i]
            i += 1  # Номер cледующей лексемы

            if tab == 1:  # ключевое слово
                kw = self.keywords[idx - 1]
                if kw == "dim":
                    declaration_mode = True  # отмечаем, что лексема в dim-секции

            elif tab == 2:  # разделитель
                de = self.delimiters[idx - 1]
                if de in [":", "\n"]:  # если добрались до ":" или сделали переход строки, то мы теперь в теле программы
                    use_mode = True
                    declaration_mode = False
                    if de == "\n":
                        self.line_number += 1

            elif tab == 4:  # идентификатор
                if declaration_mode:
                    if idx in self.declared:  # ошибка при повторном объявлении
                        self.errors.append((idx, self.line_number, ))
                    self.declared.add((idx, self.line_number, "repeat declared"))  # в dim-секции - это объявление
                    
                elif use_mode:  # в теле - использование
                    self.used.append(idx)
                    if idx in self.declared: continue  # если идентификатор уже объявлен
                    if idx in map(lambda x: x[0], self.errors): continue  # если идентификатор уже в списке ошибок
                    self.errors.append((idx, self.line_number, "not declared"))

        return len(self.errors) == 0

    def report(self):
        if not self.errors:
            print("Семантический анализ пройден.")
            return

        print("\nСЕМАНТИЧЕСКИЕ ОШИБКИ:")
        for var, line, err_type in self.errors:
            if err_type == "not declared":
                print(f"  Переменная ID({self.identifiers[var - 1]}) используется, но не объявлена. Строка: {line}")
            elif err_type == "repeat declared":
                print(f"  Переменная ID({self.identifiers[var - 1]}) объявлена повторно. Строка: {line}")
