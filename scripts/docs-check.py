#!/usr/bin/env python3
"""Проверка доков troy-docs: свежесть страниц system/*.md, битые относительные
ссылки, несуществующие пути/символы кода в бэктик-фрагментах.

Запуск: python3 scripts/docs-check.py [-v]   (из любой директории — корень
доков вычисляется от расположения этого файла).

Только stdlib. Exit 0 — битых ссылок и путей/символов нет (stale — не влияет
на exit code, это просто информация). Exit 1 — есть хотя бы одна битая ссылка
или несуществующий путь/символ.
"""

import os
import re
import subprocess
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_ROOT = os.path.dirname(SCRIPT_DIR)          # troy-docs/
TROY_ROOT = os.path.dirname(DOCS_ROOT)            # /Users/fost/Projects/troy
SYSTEM_DIR = os.path.join(DOCS_ROOT, "system")

REPO_KEY = {
    "troy-backend": "backend",
    "troy-flutter": "flutter",
    "troy-admin": "admin",
}

SKIP_DIRS = {".git", ".obsidian", "node_modules"}


# ---------------------------------------------------------------- helpers --

def iter_md_files(root):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            if fn.endswith(".md"):
                yield os.path.join(dirpath, fn)


def strip_inline_code(line):
    """Убирает `инлайн-код`, чтобы ссылки/пути внутри него не проверялись."""
    return re.sub(r"`[^`]*`", "", line)


def parse_frontmatter(text):
    """Мини-парсер YAML-подобного frontmatter (только то, что нам нужно:
    скалярные ключи и один уровень списков через '- ')."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    body = text[3:end]
    lines = body.split("\n")
    data = {}
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        if line[0] in (" ", "\t"):
            i += 1
            continue
        if ":" not in line:
            i += 1
            continue
        key, _, rest = line.partition(":")
        key = key.strip()
        rest = rest.split("#", 1)[0].strip()
        if rest == "":
            items = []
            j = i + 1
            while j < len(lines) and lines[j].strip().startswith("-"):
                item = lines[j].strip()[1:].strip()
                item = item.split("#", 1)[0].strip()
                if item:
                    items.append(item)
                j += 1
            data[key] = items
            i = j
        else:
            data[key] = rest
            i += 1
    return data


# --------------------------------------------------------- (a) свежесть --

def count_commits_since(repo_dir_name, sha, rel_paths, verbose):
    repo_path = os.path.join(TROY_ROOT, repo_dir_name)
    rev_range = f"{sha}..HEAD"
    cmd = ["git", "-C", repo_path, "rev-list", "--count", rev_range, "--"] + rel_paths
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, check=True)
        count = int(out.stdout.strip() or "0")
    except Exception as e:  # noqa: BLE001 — репо/sha могли протухнуть, это не должно валить exit code
        return None, str(e)

    log_text = None
    if verbose:
        log_cmd = ["git", "-C", repo_path, "log", "--oneline", rev_range, "--"] + rel_paths
        try:
            log_out = subprocess.run(log_cmd, capture_output=True, text=True, check=True)
            log_text = log_out.stdout.strip()
        except Exception as e:  # noqa: BLE001
            log_text = f"(git log error: {e})"
    return count, log_text


def check_freshness(verbose):
    if not os.path.isdir(SYSTEM_DIR):
        return
    for fn in sorted(os.listdir(SYSTEM_DIR)):
        if not fn.endswith(".md") or fn in ("README.md", "_template.md"):
            continue
        fpath = os.path.join(SYSTEM_DIR, fn)
        with open(fpath, encoding="utf-8") as f:
            text = f.read()
        fm = parse_frontmatter(text)
        if not fm:
            print(f"{fn}  (нет frontmatter)")
            continue
        verified = fm.get("verified", "?")
        paths = fm.get("paths", [])

        by_repo = {}
        for p in paths:
            prefix = p.split("/", 1)[0]
            if prefix not in REPO_KEY:
                continue
            rest = p[len(prefix) + 1:] if "/" in p else ""
            by_repo.setdefault(prefix, []).append(rest)

        segments = []
        log_lines = []
        for prefix, rel_paths in by_repo.items():
            repo_key = REPO_KEY[prefix]
            sha = fm.get(repo_key)
            if not sha:
                segments.append(f"{repo_key} (нет sha)")
                continue
            count, log_or_err = count_commits_since(prefix, sha, rel_paths, verbose)
            if count is None:
                segments.append(f"{repo_key} error({log_or_err})")
            else:
                segments.append(f"{repo_key} +{count}")
                if verbose and log_or_err:
                    log_lines.append(f"  [{repo_key}]\n" + "\n".join(
                        f"    {l}" for l in log_or_err.splitlines()
                    ))

        line = f"{fn}  verified {verified}  " + "  ".join(segments) if segments else f"{fn}  verified {verified}  (нет путей)"
        print(line)
        for l in log_lines:
            print(l)


# ------------------------------------------------------- (b) битые ссылки --

LINK_RE = re.compile(r"\]\(([^)\s]+\.md(?:#[^)\s]+)?|[^)\s]+/)\)")


def check_links():
    issues = []
    for fpath in iter_md_files(DOCS_ROOT):
        with open(fpath, encoding="utf-8") as f:
            lines = f.readlines()
        in_fence = False
        for lineno, raw_line in enumerate(lines, start=1):
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            line = strip_inline_code(raw_line)
            for m in LINK_RE.finditer(line):
                target = m.group(1)
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                anchor = ""
                path_part = target
                if "#" in path_part:
                    path_part, anchor = path_part.split("#", 1)
                if not path_part:
                    continue
                base_dir = os.path.dirname(fpath)
                resolved = os.path.normpath(os.path.join(base_dir, path_part))
                if target.endswith("/"):
                    ok = os.path.isdir(resolved)
                else:
                    ok = os.path.isfile(resolved)
                if not ok:
                    rel = os.path.relpath(fpath, DOCS_ROOT)
                    issues.append(f"{rel}:{lineno} → битая ссылка `{target}` (нет {os.path.relpath(resolved, DOCS_ROOT)})")
    return issues


# ------------------------------------------------- (c) пути/символы кода --

CODE_REF_RE = re.compile(r"`((?:troy-backend|troy-flutter|troy-admin)/[^`]*)`")


def check_code_refs():
    issues = []
    if not os.path.isdir(SYSTEM_DIR):
        return issues
    for fn in sorted(os.listdir(SYSTEM_DIR)):
        if not fn.endswith(".md"):
            continue
        fpath = os.path.join(SYSTEM_DIR, fn)
        with open(fpath, encoding="utf-8") as f:
            lines = f.readlines()
        for lineno, raw_line in enumerate(lines, start=1):
            for m in CODE_REF_RE.finditer(raw_line):
                frag = m.group(1)
                if ":" in frag:
                    path_part, _, symbol = frag.rpartition(":")
                else:
                    path_part, symbol = frag, None

                fs_path = os.path.join(TROY_ROOT, path_part)
                path_ok = os.path.isdir(fs_path) if path_part.endswith("/") else os.path.isfile(fs_path)
                if not path_ok:
                    issues.append(f"system/{fn}:{lineno} → путь не найден `{path_part}`")
                    continue

                if symbol is not None and not symbol.isdigit():
                    try:
                        with open(fs_path, encoding="utf-8") as cf:
                            content = cf.read()
                    except Exception as e:  # noqa: BLE001
                        issues.append(f"system/{fn}:{lineno} → не смог прочитать `{path_part}` ({e})")
                        continue
                    if symbol not in content:
                        issues.append(f"system/{fn}:{lineno} → символ `{symbol}` не найден в `{path_part}`")
    return issues


# -------------------------------------------------------------------- main --

def main():
    verbose = "-v" in sys.argv[1:]

    print("== свежесть (info, не влияет на exit code) ==")
    check_freshness(verbose)

    print("\n== битые ссылки ==")
    link_issues = check_links()
    if not link_issues:
        print("(нет)")
    else:
        for issue in link_issues:
            print(issue)

    print("\n== несуществующие пути/символы кода ==")
    code_issues = check_code_refs()
    if not code_issues:
        print("(нет)")
    else:
        for issue in code_issues:
            print(issue)

    if link_issues or code_issues:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
