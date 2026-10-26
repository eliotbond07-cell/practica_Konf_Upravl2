import argparse
import os
import sys

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


REQUIRED_KEYS = (
    "package_name",
    "repo_url",
    "test_mode",
    "repo_file_path",
    "output_image",
    "ascii_tree",
)


class ConfigError(Exception):
    """Генерируется при неверной конфигурации"""


def load_config(path):
    """Загружает файл конфигурации TOML"""
    if not os.path.isfile(path):
        raise ConfigError(
            f"Файл конфигурации не найден: {path}"
        )
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"Битый TOML: {exc}") from exc


def check_keys(cfg):
    """Проверяет наличие всех полей в файле конфигурации"""
    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        raise ConfigError(
            f"Пропущены поля в файле конфигурации: {', '.join(missing)}"
        )


def validate_package_name(value):
    """Проверка package_name (ну пустая строка и нет пробелов)"""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("package_name не должен быть пустой строкой")
    if any(c.isspace() for c in value):
        raise ConfigError("package_name не должен содержать пробелы")
    return value


def validate_repo_url(value):
    """Проверка repo_url (начинается не с http(s) или не ведет к файлу)"""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("repo_url не должен быть пустой строкой")
    if value.startswith(("http://", "https://")):
        return value
    if os.path.exists(value):
        return value
    raise ConfigError(
        "repo_url должен быть http(s) URL или существующим путем к файлу"
    )


def validate_test_mode(value):
    """Проверка test_mode (bool)."""
    if not isinstance(value, bool):
        raise ConfigError("test_mode должен быть true или false")
    return value


def validate_repo_file(value, test_mode):
    """Проверка, если test_mode = true,
        repo_file_path (должен вести к файлу)"""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("repo_file_path не должен быть пустой строкой")
    if test_mode and not os.path.isfile(value):
        raise ConfigError(
            f"Test repo file не найден: {value}"
        )
    return value


def validate_output_image(value):
    """Проверка output_image (.png)"""
    if not isinstance(value, str) or not value.strip():
        raise ConfigError("output_image не должен быть пустой строкой")
    if not value.lower().endswith(".png"):
        raise ConfigError("output_image должен иметь формат .png")
    return value


def validate_ascii_tree(value):
    """Проверка ascii_tree (bool)"""
    if not isinstance(value, bool):
        raise ConfigError("ascii_tree должен быть true или false")
    return value


def validate_config(cfg):
    """Запускает проверку каждого параметра"""
    return {
        "package_name": validate_package_name(cfg["package_name"]),
        "repo_url": validate_repo_url(cfg["repo_url"]),
        "test_mode": validate_test_mode(cfg["test_mode"]),
        "repo_file_path": validate_repo_file(
            cfg["repo_file_path"], validate_test_mode(cfg["test_mode"])),
        "output_image": validate_output_image(cfg["output_image"]),
        "ascii_tree": validate_ascii_tree(cfg["ascii_tree"]),
    }


def print_config(cfg):
    """Печатает параметры конфигурации в формате ключ-значение"""
    print("=== Параметры конфигурации ===")
    for key in REQUIRED_KEYS:
        print(f"{key} = {cfg[key]}")
    print("==============================")


def parse_args(argv):
    """Разбирает параметры командной строки"""
    parser = argparse.ArgumentParser(
        description="Визуализатор графа зависимостей пакетов"
    )
    parser.add_argument(
        "--config",
        required=True,
        help="Путь к файлу конфигурации TOML",
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Точка входа в программу"""
    args = parse_args(argv)
    try:
        raw = load_config(args.config)
        check_keys(raw)
        cfg = validate_config(raw)
    except ConfigError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1
    print_config(cfg)
    return 0


if __name__ == "__main__":
    main()