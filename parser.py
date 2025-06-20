import os, json, argparse
from pathlib import Path
 
from tree_sitter import Language, Parser
import tree_sitter_python as tspython
import tree_sitter_c_sharp as ts_csharp

from ai import CodeDescriber


DESCRIBER = CodeDescriber(device=-1)

def init_parsers():
    
    LANGUAGES = {
        ".py": Language(tspython.language()),
        ".cs": Language(ts_csharp.language()),
    }
    
    parsers = {}
    for ext, lang in LANGUAGES.items():
        p = Parser(lang)
        parsers[ext] = p
    return parsers


def extract_definitions(source_code, parser):
    """
    Находит все `function_definition`, `class_definition` и т.п.
    Возвращает список кортежей (name, signature, code_snippet, line).
    """
    tree = parser.parse(bytes(source_code, "utf8"))
    root = tree.root_node
    results = []

    # шаблоны узлов в разных грамматиках могут отличаться
    NODE_TYPES = ("function_definition", "method_definition", "class_definition",
                  "function_declaration", "method_declaration")

    def walk(node):
        if node.type in NODE_TYPES:
            # грубый парсинг имени и сигнатуры
            header = source_code[node.start_byte:node.start_byte+200].split("{")[0]
            name = node.child_by_field_name("name")
            name_str = source_code[name.start_byte:name.end_byte] if name else "<anon>"
            signature = header.strip().replace("\n", " ")
            snippet = source_code[node.start_byte:node.end_byte]
            line = node.start_point[0] + 1
            results.append((name_str, signature, snippet, line))
        for c in node.children:
            walk(c)
    walk(root)
    return results


def parser_repo(repo_path, out_md):
    parsers = init_parsers()
    report = []

    for root, _, files in os.walk(repo_path):
        for fn in files:
            ext = Path(fn).suffix
            
            if ext not in parsers:
                continue
            
            full = os.path.join(root, fn)
            with open(full, encoding="utf8", errors="ignore") as f:
                src = f.read()
                
            defs = extract_definitions(src, parsers[ext])
            for name, sig, snippet, line in defs:
                try:
                    desc_json =  DESCRIBER.describe(snippet)
                    
                except Exception as e:
                    print(f"LLM error on {full}:{line}: {e}")
                    continue
                
                try:
                    report.append({
                        "name": name,
                        "signature": sig,
                        "location": f"{full}:{line}",
                        "description": desc_json
                    })
                except json.JSONDecodeError:
                    print(f"LLM error (invalid JSON) on {full}:{line}: {desc_json}")

    with open(out_md, "w", encoding="utf8") as md:
        md.write("# Автосгенерированный отчёт по API\n\n")
        
        for item in report:
            md.write(f"## {item['name']}\n")
            md.write(f"- **Сигнатура**: `{item['signature']}`\n")
            md.write(f"- **Где**: `{item['location']}`\n")
            md.write(f"- **Что делает**: {item['description']}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Генерация описания классов/функций/методов из репозитория")
    
    parser.add_argument("repo_path", help="Путь к корню репозитория")
    
    parser.add_argument(
        "-o", "--output", default="api_report.md",
        help="Имя выходного Markdown-файла")
    
    args = parser.parse_args()
    
    parser_repo(args.repo_path, args.output)
