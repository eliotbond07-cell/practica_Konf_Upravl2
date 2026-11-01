import argparse
import io
import os
import sys
import tarfile
import urllib.error
import urllib.request
from collections import deque

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

APKINDEX_NAME = "APKINDEX.tar.gz"
APKINDEX_MEMBER = "APKINDEX"
HTTP_TIMEOUT = 30
TWO = 2


class ConfigError(Exception):
    """Генерируется при неверной конфигурации"""


class FetchError(Exception):
    """Генерируется при ошибке загрузки репозитория"""


class PackageNotFoundError(Exception):
    """Генерируется, если пакет отсутствует в индексе"""


class TestRepoError(Exception):
    """Ошибка чтения тестового репозитория"""


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


def build_index_url(repo_url):
    """Склеивает URL репозитория и имя индекса"""
    if repo_url.startswith(("http://", "https://")):
        return repo_url.rstrip("/") + "/" + APKINDEX_NAME
    return os.path.join(repo_url, APKINDEX_NAME)


def download_index(repo_url):
    """Скачивает APKINDEX.tar.gz и возвращает bytes"""
    url = build_index_url(repo_url)
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        raise FetchError(
            f"Не удалось скачать {url}: {exc}"
        ) from exc


def read_index_archive(archive_bytes):
    """Открывает tar.gz-байты и возвращает содержимое APKINDEX"""
    try:
        with tarfile.open(fileobj=io.BytesIO(archive_bytes),
                          mode="r:gz") as tar:
            member = tar.getmember(APKINDEX_MEMBER)
            handle = tar.extractfile(member)
            if handle is None:
                raise FetchError("APKINDEX не найден в архиве")
            return handle.read().decode("utf-8", errors="replace")
    except (tarfile.TarError, KeyError) as exc:
        raise FetchError(f"Битый APKINDEX.tar.gz: {exc}") from exc


def parse_index_text(text):
    """Парсит APKINDEX-текст в dict {имя: запись}.
    Запись — dict с ключами 'P', 'V', 'D'"""
    packages = {}
    record = {}
    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r")
        if not line:
            finish_record(packages, record)
            record = {}
            continue
        if len(line) < TWO or line[1] != ":":
            continue
        key, value = line[0], line[2:]
        record[key] = value
    finish_record(packages, record)
    return packages


def finish_record(packages, record):
    """Сохраняет запись в packages, если в ней есть имя"""
    name = record.get("P")
    if name:
        packages[name] = record


def load_apkindex(repo_url):
    """Скачивает и парсит APKINDEX репозитория"""
    archive = download_index(repo_url)
    text = read_index_archive(archive)
    return parse_index_text(text)


def normalize_dep(dep):
    """Убирает версию или ограничение, возвращает чистое имя или None"""
    if not dep or dep.startswith("!"):
        return None
    for sep in ("=", "<", ">", "~"):
        idx = dep.find(sep)
        if idx != -1:
            dep = dep[:idx]
    dep = dep.strip()
    return dep or None


def split_dependencies(raw_deps):
    """Разбивает строку D: на список нормализованных имен"""
    if not raw_deps:
        return []
    result = []
    for part in raw_deps.split():
        name = normalize_dep(part)
        if name:
            result.append(name)
    return result


def parse_test_repo_line(line, line_no):
    """Парсит одну строку тестового файла, получается (имя, [deps])"""
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None
    if ":" not in stripped:
        raise TestRepoError(
            f"Строка {line_no}: ожидается формат 'ИМЯ: deps'"
        )
    name, raw_deps = stripped.split(":", 1)
    name = name.strip()
    if not name:
        raise TestRepoError(
            f"Строка {line_no}: пустое имя пакета"
        )
    if not name.isalpha() or not name.isupper():
        raise TestRepoError(
            f"Строка {line_no}: имя '{name}' должно быть A-Z"
        )
    deps = [d for d in raw_deps.split() if d]
    for dep in deps:
        if not dep.isalpha() or not dep.isupper():
            raise TestRepoError(
                f"Строка {line_no}: зависимость '{dep}' "
                f"должна быть A-Z"
            )
    return name, deps


def load_test_graph(path):
    """Читает тестовый файл и возвращает dict {имя: [deps]}"""
    graph = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, start=1):
                parsed = parse_test_repo_line(line, line_no)
                if parsed is None:
                    continue
                name, deps = parsed
                graph[name] = deps
    except OSError as exc:
        raise TestRepoError(f"Не удалось прочитать {path}: {exc}")
    if not graph:
        raise TestRepoError(f"Тестовый репозиторий пуст: {path}")
    return graph


def build_bfs_order(graph, start):
    """BFS от start. Возвращает (order, missing).
    Обрабатывает циклы: каждый узел попадает в order один раз

    order — список пакетов в порядке обхода
    missing — пакеты, встреченные как зависимости, но отсутствующие
              в графе как ключи
    """
    if start not in graph:
        raise PackageNotFoundError(
            f"Пакет '{start}' отсутствует в графе"
        )
    order = []
    missing = set()
    visited = {start}
    queue = deque([start])
    while queue:
        current = queue.popleft()
        order.append(current)
        for dep in graph.get(current, []):
            if dep not in graph:
                missing.add(dep)
                continue
            if dep in visited:
                continue
            visited.add(dep)
            queue.append(dep)
    return order, missing


def collect_subgraph(graph, order):
    """Возвращает подграф только из узлов order (deps внутри order)"""
    allowed = set(order)
    return {
        node: [d for d in graph.get(node, []) if d in allowed]
        for node in order
    }


def find_cycles(graph):
    """Итеративный DFS, возвращает список найденных циклов.
    Каждый цикл — список узлов без замыкания (A -> B -> A
    представлен как [A, B])
    """
    cycles = []
    seen_cycles = set()
    color = {}
    for start in graph:
        if color.get(start):
            continue
        stack = [(start, iter(graph.get(start, [])))]
        path = [start]
        color[start] = 1
        while stack:
            node, it = stack[-1]
            advanced = False
            for dep in it:
                if dep not in graph:
                    continue
                state = color.get(dep, 0)
                if state == 0:
                    color[dep] = 1
                    stack.append((dep, iter(graph.get(dep, []))))
                    path.append(dep)
                    advanced = True
                    break
                if state == 1:
                    record_cycle(path, dep, cycles, seen_cycles)
            if not advanced:
                color[node] = 2
                stack.pop()
                path.pop()
    return cycles


def record_cycle(path, dep, cycles, seen):
    """Регистрирует цикл, если он ещё не встречался"""
    try:
        idx = path.index(dep)
    except ValueError:
        return
    cycle = tuple(path[idx:])
    key = canonical_cycle(cycle)
    if key in seen:
        return
    seen.add(key)
    cycles.append(list(cycle))


def canonical_cycle(cycle):
    """Приводит цикл к лексико-графическрму минимуму"""
    n = len(cycle)
    rotations = [cycle[i:] + cycle[:i] for i in range(n)]
    return min(rotations)


def get_direct_deps(index, package_name):
    """Возвращает список прямых зависимостей пакета"""
    record = index.get(package_name)
    if record is None:
        raise PackageNotFoundError(
            f"Пакет '{package_name}' не найден в APKINDEX"
        )
    return split_dependencies(record.get("D", ""))


def print_direct_deps(package_name, deps):
    """Печатает прямые зависимости пакета"""
    print(f"Прямые зависимости пакета '{package_name}':")
    if not deps:
        print("  (нет)")
        return
    for dep in deps:
        print(f"  - {dep}")


def print_bfs_result(package_name, order, missing, cycles):
    """Печатает порядок обхода BFS и наличие циклических зависимостей"""
    print()
    print(f"Порядок обхода BFS от '{package_name}':")
    for i, node in enumerate(order, start=1):
        print(f"  {i:>3}. {node}")
    print()
    print(f"Всего узлов в графе: {len(order)}")
    if missing:
        print("Отсутствуют в индексе (только упомянуты):")
        for m in sorted(missing):
            print(f"  - {m}")
    if cycles:
        print(f"Найдено циклических зависимостей: {len(cycles)}")
        for c in cycles:
            print("  - " + " -> ".join(c) + " -> " + c[0])
    else:
        print("Циклических зависимостей не найдено.")


def load_source_graph(cfg):
    """Возвращает dict {имя: [deps]} из тестового файла или APKINDEX"""
    if cfg["test_mode"]:
        return load_test_graph(cfg["repo_file_path"])
    index = load_apkindex(cfg["repo_url"])
    graph = {
        name: split_dependencies(rec.get("D", ""))
        for name, rec in index.items()
    }
    return graph


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


def run(cfg):
    """Запуск извлечения графа зависимостей"""
    print_config(cfg)
    graph = load_source_graph(cfg)
    print(f"[INFO] Всего пакетов в источнике: {len(graph)}")
    package = cfg["package_name"]
    order, missing = build_bfs_order(graph, package)
    subgraph = collect_subgraph(graph, order)
    cycles = find_cycles(subgraph)
    print_bfs_result(package, order, missing, cycles)
    return 0


def main(argv=None):
    """Точка входа в программу"""
    args = parse_args(argv)
    try:
        raw = load_config(args.config)
        check_keys(raw)
        cfg = validate_config(raw)
        return run(cfg)
    except (ConfigError, FetchError, PackageNotFoundError,
            TestRepoError) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    main()