import argparse
from pathlib import Path

from lexical_analyzer import LexicalAnalyzer
from syntax_analyzer import SyntaxAnalyzer
from semantic_analyzer import SemanticAnalyzer


def run_file_test(filepath: Path, hide_log):
    print()
    print("-" * 50)
    print(f"\nТестирование: {filepath.name}")

    with open(filepath, 'r', encoding='utf-8') as f:
        source_code = f.read()

    # Лексический анализ
    lexer = LexicalAnalyzer(source_code, hide_log)
    lexemes = lexer.scanner()
    if lexer.state == lexer.State.ER:   
        print("Ошибка на этапе лексического анализа.")
        return False

    # Синтаксический анализ
    try:
        parser = SyntaxAnalyzer(lexemes, lexer.keywords, lexer.delimiters,
                                lexer.numbers, lexer.identifiers, hide_log)
        parser.parse()
    except SystemExit:
        print("Ошибка на этапе синтаксического анализа.")
        return False

    # Семантический анализ
    sa = SemanticAnalyzer(lexemes, lexer.keywords, lexer.delimiters,
                          lexer.numbers, lexer.identifiers, hide_log)
    if not sa.analyze_used_vars():
        sa.report()
        print("Ошибка на этапе семантического анализа.")
        return False

    print("Код полностью корректен.")
    return True


def run_all_tests(test_dir: Path = Path("test_inputs"), hide_log=True):
    test_dir = test_dir.resolve()
    if not test_dir.exists():
        print(f"Директория {test_dir} не найдена.")
        return

    success_count = 0
    total_count = 0

    for file_path in sorted(test_dir.glob("*.txt")):
        total_count += 1
        success = run_file_test(file_path, hide_log)
        if success:
            success_count += 1

    print("\n" + "="*60)
    print(f"Успешно: {success_count}/{total_count}")
    if success_count != total_count:
        print("Некоторые тесты завершились с ошибками.")
    else:
        print("Все тесты пройдены!")

def main():
    parser = argparse.ArgumentParser(
        description="Тестирование анализаторов языка программирования"
    )
    parser.add_argument(
        "--tests-dir",
        type=str,
        default="test_inputs",
        help="Путь к директории с тестовыми файлами (по умолчанию: test_inputs)"
    )
    parser.add_argument(
        "--logs",
        action="store_true",
        default=False,
        help="Включить подробные логи анализаторов"
    )
    parser.add_argument(
        "--file",
        type=str,
        default=None,
        help="Запустить тест для конкретного файла"
    )

    args = parser.parse_args()

    if args.file:
        file_path = Path(args.file).resolve()
        run_file_test(file_path, hide_log=not args.logs)
    else:
        run_all_tests(test_dir=Path(args.tests_dir), hide_log=not args.logs)


if __name__ == "__main__":
    main()