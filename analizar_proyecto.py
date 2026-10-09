#!/usr/bin/env python3
"""
analizar_proyecto.py
Analiza un proyecto y genera UN archivo Markdown (analisis_proyecto.md)
que puedes subir a Claude para pedir mejoras de interfaz, código y flujo de trabajo.

Uso:
    python analizar_proyecto.py                      # analiza la carpeta actual
    python analizar_proyecto.py /ruta/al/proyecto
    python analizar_proyecto.py . --full             # incluye más código fuente
    python analizar_proyecto.py . --budget 300000    # más caracteres de código

No necesita instalar nada (solo librería estándar de Python 3.8+).
"""
import argparse
import ast
import json
import re
from collections import Counter
from pathlib import Path

IGNORE_DIRS = {
    ".git", ".svn", ".hg", "node_modules", "venv", ".venv", "env", "__pycache__",
    ".idea", ".vscode", "dist", "build", ".next", ".nuxt", ".cache", "target",
    "coverage", ".pytest_cache", ".mypy_cache", ".gradle", "Pods", ".dart_tool",
    "vendor", "bin", "obj", ".terraform", "site-packages",
}
IGNORE_FILES = {".env", ".env.local", ".env.production", "id_rsa", "id_ed25519",
                "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock",
                "composer.lock", "Pipfile.lock", ".DS_Store"}
BINARY_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".svg", ".pdf", ".zip",
              ".tar", ".gz", ".exe", ".dll", ".so", ".pyc", ".woff", ".woff2", ".ttf",
              ".eot", ".mp3", ".mp4", ".mov", ".db", ".sqlite", ".sqlite3", ".bin",
              ".jar", ".class", ".lock", ".map", ".min.js", ".min.css"}

LANGS = {
    ".py": "Python", ".js": "JavaScript", ".jsx": "JavaScript (React)", ".ts": "TypeScript",
    ".tsx": "TypeScript (React)", ".vue": "Vue", ".svelte": "Svelte", ".html": "HTML",
    ".css": "CSS", ".scss": "SCSS", ".sass": "Sass", ".less": "Less", ".java": "Java",
    ".kt": "Kotlin", ".swift": "Swift", ".dart": "Dart", ".go": "Go", ".rs": "Rust",
    ".rb": "Ruby", ".php": "PHP", ".cs": "C#", ".cpp": "C++", ".c": "C", ".h": "C/C++ header",
    ".sh": "Shell", ".sql": "SQL", ".md": "Markdown", ".json": "JSON", ".yml": "YAML",
    ".yaml": "YAML", ".toml": "TOML", ".xml": "XML", ".ui": "Qt UI", ".kv": "Kivy",
}
UI_EXT = {".html", ".css", ".scss", ".sass", ".less", ".jsx", ".tsx", ".vue", ".svelte",
          ".ui", ".kv", ".xml", ".dart", ".swift"}
KEY_FILES = ["README.md", "readme.md", "README.rst", "package.json", "requirements.txt",
             "pyproject.toml", "setup.py", "Pipfile", "composer.json", "pubspec.yaml",
             "Cargo.toml", "go.mod", "pom.xml", "build.gradle", "Dockerfile",
             "docker-compose.yml", "docker-compose.yaml", "Makefile", "tsconfig.json",
             "vite.config.js", "vite.config.ts", "next.config.js", "tailwind.config.js",
             "tailwind.config.ts", "webpack.config.js", ".eslintrc.json", "manage.py"]
ENTRY_NAMES = {"main.py", "app.py", "run.py", "server.py", "manage.py", "wsgi.py", "asgi.py",
               "index.js", "server.js", "app.js", "main.js", "index.ts", "main.ts",
               "index.html", "App.jsx", "App.tsx", "App.vue", "main.dart", "main.go"}

TECH_HINTS = {
    "react": "React", "next": "Next.js", "vue": "Vue", "nuxt": "Nuxt", "svelte": "Svelte",
    "@angular/core": "Angular", "tailwindcss": "Tailwind CSS", "bootstrap": "Bootstrap",
    "@mui/material": "Material UI", "antd": "Ant Design", "chakra-ui": "Chakra UI",
    "shadcn": "shadcn/ui", "styled-components": "styled-components", "redux": "Redux",
    "zustand": "Zustand", "express": "Express", "fastify": "Fastify", "electron": "Electron",
    "vite": "Vite", "webpack": "Webpack", "typescript": "TypeScript", "jest": "Jest",
    "vitest": "Vitest", "cypress": "Cypress", "playwright": "Playwright",
    "django": "Django", "flask": "Flask", "fastapi": "FastAPI", "streamlit": "Streamlit",
    "gradio": "Gradio", "tkinter": "Tkinter", "customtkinter": "CustomTkinter",
    "pyqt5": "PyQt5", "pyqt6": "PyQt6", "pyside6": "PySide6", "kivy": "Kivy",
    "pandas": "Pandas", "numpy": "NumPy", "sqlalchemy": "SQLAlchemy", "pytest": "Pytest",
    "torch": "PyTorch", "tensorflow": "TensorFlow", "requests": "Requests",
    "laravel": "Laravel", "flutter": "Flutter", "anthropic": "Anthropic SDK",
    "openai": "OpenAI SDK", "prisma": "Prisma", "mongoose": "Mongoose",
}
SECRET_PATTERNS = [
    (re.compile(r"(?i)(api[_-]?key|secret|token|passw(or)?d|authorization)(\s*[:=]\s*)(['\"]?)[^\s'\"#,]{6,}"),
     r"\1\3\4***REDACTADO***"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"), "***REDACTADO***"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "***REDACTADO***"),
    (re.compile(r"ghp_[A-Za-z0-9]{30,}"), "***REDACTADO***"),
]


def redact(text: str) -> str:
    for pat, repl in SECRET_PATTERNS:
        text = pat.sub(repl, text)
    return text


def read_text(path: Path, limit=None):
    try:
        data = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return data[:limit] if limit else data


def scan(root: Path):
    files = []
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        if any(part in IGNORE_DIRS for part in rel.parts[:-1]):
            continue
        if p.name in IGNORE_FILES or p.suffix.lower() in BINARY_EXT:
            continue
        try:
            size = p.stat().st_size
        except OSError:
            continue
        if size > 1_500_000:
            continue
        files.append(p)
    return files


def tree(root: Path, max_depth=3, max_items=25):
    lines = [f"{root.name}/"]

    def walk(d: Path, prefix: str, depth: int):
        if depth > max_depth:
            return
        try:
            items = sorted(d.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
        except OSError:
            return
        items = [i for i in items if i.name not in IGNORE_DIRS and i.name not in IGNORE_FILES]
        for idx, it in enumerate(items[:max_items]):
            last = idx == len(items[:max_items]) - 1 and len(items) <= max_items
            lines.append(f"{prefix}{'└── ' if last else '├── '}{it.name}{'/' if it.is_dir() else ''}")
            if it.is_dir():
                walk(it, prefix + ("    " if last else "│   "), depth + 1)
        if len(items) > max_items:
            lines.append(f"{prefix}└── ... (+{len(items) - max_items} más)")

    walk(root, "", 1)
    return "\n".join(lines)


def analyze_python(path: Path):
    src = read_text(path)
    info = {"classes": [], "functions": [], "imports": set(), "routes": []}
    try:
        tree_ = ast.parse(src)
    except SyntaxError:
        return info
    for node in ast.walk(tree_):
        if isinstance(node, ast.ClassDef):
            info["classes"].append(node.name)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info["functions"].append(node.name)
            for dec in node.decorator_list:
                d = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                if re.search(r"\.(route|get|post|put|delete|patch)\(", d):
                    info["routes"].append(d)
        elif isinstance(node, ast.Import):
            info["imports"].update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            info["imports"].add(node.module.split(".")[0])
    return info


def detect_tech(root: Path, files, py_imports):
    found = set()
    blobs = []
    for name in ("package.json", "requirements.txt", "pyproject.toml", "Pipfile",
                 "composer.json", "pubspec.yaml", "Cargo.toml", "go.mod"):
        for p in root.rglob(name):
            if not any(part in IGNORE_DIRS for part in p.relative_to(root).parts):
                blobs.append(read_text(p).lower())
    blob = "\n".join(blobs)
    for key, label in TECH_HINTS.items():
        if re.search(rf"(?<![\w-]){re.escape(key)}(?![\w-])", blob):
            found.add(label)
    for imp in py_imports:
        if imp.lower() in TECH_HINTS:
            found.add(TECH_HINTS[imp.lower()])
    names = {f.name for f in files}
    if "Dockerfile" in names:
        found.add("Docker")
    if any(".github" in f.parts for f in files):
        found.add("GitHub Actions")
    return sorted(found)


def find_todos(files, root, limit=40):
    out = []
    pat = re.compile(r"(TODO|FIXME|HACK|XXX)[:\s](.*)")
    for f in files:
        if f.suffix.lower() not in LANGS:
            continue
        for i, line in enumerate(read_text(f, 200_000).splitlines(), 1):
            m = pat.search(line)
            if m:
                out.append(f"- `{f.relative_to(root)}:{i}` {m.group(1)}: {m.group(2).strip()[:100]}")
                if len(out) >= limit:
                    return out
    return out


def ui_signals(files, root):
    """Heurísticas rápidas sobre la interfaz."""
    s = {"html": 0, "css": 0, "components": 0, "inline_styles": 0, "media_queries": 0,
         "aria": 0, "alt_missing": 0, "css_vars": 0, "dark_mode": 0, "big_css": []}
    for f in files:
        ext = f.suffix.lower()
        if ext not in UI_EXT:
            continue
        txt = read_text(f, 400_000)
        if ext == ".html":
            s["html"] += 1
            s["inline_styles"] += len(re.findall(r'style\s*=\s*"', txt))
            s["aria"] += len(re.findall(r"aria-|role=", txt))
            s["alt_missing"] += len(re.findall(r"<img(?![^>]*\balt=)[^>]*>", txt, re.I))
        if ext in {".css", ".scss", ".sass", ".less"}:
            s["css"] += 1
            s["media_queries"] += txt.count("@media")
            s["css_vars"] += len(re.findall(r"--[\w-]+\s*:", txt))
            s["dark_mode"] += txt.count("prefers-color-scheme") + txt.count(".dark")
            if len(txt.splitlines()) > 500:
                s["big_css"].append(str(f.relative_to(root)))
        if ext in {".jsx", ".tsx", ".vue", ".svelte"}:
            s["components"] += 1
            s["aria"] += len(re.findall(r"aria-|role=", txt))
    return s


def main():
    ap = argparse.ArgumentParser(description="Analiza un proyecto y genera un informe para Claude.")
    ap.add_argument("ruta", nargs="?", default=".", help="Carpeta del proyecto")
    ap.add_argument("-o", "--output", default="analisis_proyecto.md")
    ap.add_argument("--budget", type=int, default=120_000,
                    help="Máx. de caracteres de código a incluir (def. 120000)")
    ap.add_argument("--full", action="store_true", help="Incluir más archivos fuente")
    args = ap.parse_args()

    root = Path(args.ruta).resolve()
    if not root.is_dir():
        raise SystemExit(f"No existe la carpeta: {root}")

    print(f"Analizando {root} ...")
    files = scan(root)

    # --- Estadísticas ---
    lang_files, lang_lines = Counter(), Counter()
    sizes = []
    for f in files:
        lang = LANGS.get(f.suffix.lower())
        if not lang:
            continue
        n = read_text(f).count("\n") + 1
        lang_files[lang] += 1
        lang_lines[lang] += n
        sizes.append((n, f))
    sizes.sort(reverse=True, key=lambda x: x[0])
    total_lines = sum(lang_lines.values())

    # --- Python ---
    py_imports, py_classes, py_funcs, py_routes = set(), 0, 0, []
    for f in files:
        if f.suffix == ".py":
            info = analyze_python(f)
            py_imports |= info["imports"]
            py_classes += len(info["classes"])
            py_funcs += len(info["functions"])
            py_routes += [(str(f.relative_to(root)), r) for r in info["routes"]]

    tech = detect_tech(root, files, py_imports)
    entries = [str(f.relative_to(root)) for f in files if f.name in ENTRY_NAMES]
    tests = [f for f in files if re.search(r"(test_|_test\.|\.test\.|\.spec\.)", f.name)]
    ui = ui_signals(files, root)
    todos = find_todos(files, root)

    # --- Informe ---
    md = []
    md.append(f"# Análisis del proyecto: {root.name}\n")
    md.append("> **Instrucciones para Claude:** Este informe describe mi proyecto. "
              "Analízalo y: (1) resume qué hace y su arquitectura, (2) detecta problemas de "
              "interfaz/UX, accesibilidad, rendimiento y calidad de código, (3) propón mejoras "
              "priorizadas (alto/medio/bajo impacto) y (4) entrégame el código mejorado, "
              "archivo por archivo, listo para copiar.\n")

    md.append("## 1. Resumen\n")
    md.append(f"- Archivos analizados: **{len(files)}**")
    md.append(f"- Líneas de código/texto: **{total_lines:,}**")
    md.append(f"- Tecnologías detectadas: {', '.join(tech) or 'no detectadas'}")
    md.append(f"- Puntos de entrada probables: {', '.join(f'`{e}`' for e in entries[:10]) or 'no detectados'}")
    md.append(f"- Archivos de test: **{len(tests)}**")
    if py_classes or py_funcs:
        md.append(f"- Python: {py_classes} clases, {py_funcs} funciones")
    md.append("\n## 2. Lenguajes\n")
    md.append("| Lenguaje | Archivos | Líneas |\n|---|---:|---:|")
    for lang, n in lang_lines.most_common(12):
        md.append(f"| {lang} | {lang_files[lang]} | {n:,} |")

    md.append("\n## 3. Estructura\n")
    md.append("```\n" + tree(root) + "\n```")

    md.append("\n## 4. Archivos más grandes (candidatos a refactor)\n")
    for n, f in sizes[:10]:
        md.append(f"- `{f.relative_to(root)}` — {n} líneas")

    md.append("\n## 5. Señales de interfaz (UI/UX)\n")
    md.append(f"- Páginas HTML: {ui['html']} | Hojas CSS: {ui['css']} | Componentes (React/Vue/Svelte): {ui['components']}")
    md.append(f"- Estilos inline en HTML: {ui['inline_styles']}")
    md.append(f"- Media queries (responsive): {ui['media_queries']}")
    md.append(f"- Variables CSS: {ui['css_vars']} | Soporte modo oscuro: {'sí' if ui['dark_mode'] else 'no detectado'}")
    md.append(f"- Atributos de accesibilidad (aria/role): {ui['aria']} | `<img>` sin alt: {ui['alt_missing']}")
    if ui["big_css"]:
        md.append(f"- CSS muy grandes: {', '.join(f'`{c}`' for c in ui['big_css'][:5])}")

    if py_routes:
        md.append("\n## 6. Rutas / endpoints (Python)\n")
        for path, r in py_routes[:30]:
            md.append(f"- `{r}` en `{path}`")

    if todos:
        md.append("\n## 7. TODO / FIXME pendientes\n")
        md.extend(todos)

    # --- Código fuente (con presupuesto) ---
    md.append("\n## 8. Código fuente relevante\n")
    budget = args.budget * (2 if args.full else 1)
    per_file = 12_000 if args.full else 6_000
    included = set()

    def add(f: Path):
        nonlocal budget
        if f in included or budget <= 0:
            return
        txt = redact(read_text(f, per_file))
        if not txt.strip():
            return
        ext = f.suffix.lstrip(".") or "text"
        truncated = len(read_text(f)) > per_file
        md.append(f"\n### `{f.relative_to(root)}`\n```{ext}\n{txt}\n```"
                  + ("\n*(truncado)*" if truncated else ""))
        budget -= len(txt)
        included.add(f)

    names = {f.name: f for f in files if f.parent == root}
    for k in KEY_FILES:                       # 1) configuración y README
        if k in names:
            add(names[k])
    for f in files:                           # 2) puntos de entrada
        if f.name in ENTRY_NAMES:
            add(f)
    ui_files = sorted([f for f in files if f.suffix.lower() in UI_EXT],
                      key=lambda f: -f.stat().st_size)
    for f in ui_files[:15 if not args.full else 40]:   # 3) archivos de interfaz
        add(f)
    if args.full:                             # 4) resto del código
        for _, f in sizes:
            if f.suffix.lower() in {".py", ".js", ".jsx", ".ts", ".tsx", ".vue", ".go", ".java", ".php"}:
                add(f)

    out = Path(args.output)
    out.write_text("\n".join(md), encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"\nListo: {out.resolve()}  ({kb:.0f} KB)")
    print("Sube ese archivo a Claude y escribe, por ejemplo:")
    print('  "Analiza este informe y mejora la interfaz y el flujo de trabajo del proyecto."')


if __name__ == "__main__":
    main()
