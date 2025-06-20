import os
import sys
from tree_sitter import Language, Parser
from llama_index import Document, LLMPredictor, PromptHelper, ServiceContext, VectorStoreIndex
from llama_index.node_parser import SimpleNodeParser
from build_languages_library import build_languages_library
from ai import My_Service_Context

def setting_languages(path):
    build_languages_library(path)
    
    PY_LANGUAGE = Language(path, 'python')
    JS_LANGUAGE = Language(path, 'javascript')
    
    return {
        '.py': PY_LANGUAGE,
        '.js': JS_LANGUAGE,
        '.jsx': JS_LANGUAGE,
        '.ts': JS_LANGUAGE,
    }


class CodeExtractor:
    def __init__(self, parser_map):
        self.parsers = {}
        for ext, lang in parser_map.items():
            p = Parser()
            p.set_language(lang)
            self.parsers[ext] = p

    def extract_blocks(self, repo_path):
        blocks = []
        for root, dirs, files in os.walk(repo_path):
            for fname in files:
                ext = os.path.splitext(fname)[1]
                
                if ext not in self.parsers:
                    continue
                
                path = os.path.join(root, fname)
                code = open(path, 'r', encoding='utf-8', errors='ignore').read()
                
                parser = self.parsers[ext]
                tree = parser.parse(bytes(code, 'utf8'))
                root_node = tree.root_node
                
                for node in root_node.walk():
                    if node.type in ('function_definition', 'function_declaration', 'class_definition', 'method_definition'):
                        start_byte = node.start_byte
                        end_byte = node.end_byte
                        block_text = code[start_byte:end_byte]
                        
                        if node.type == 'function_definition':
                            name_node = node.child_by_field_name('name')
                            name = code[name_node.start_byte:name_node.end_byte] if name_node else '<anon>'
                        elif node.type == 'class_definition':
                            name_node = node.child_by_field_name('name')
                            name = code[name_node.start_byte:name_node.end_byte] if name_node else '<anon>'
                        else:
                            name = node.type
                            
                        blocks.append({
                            'file': path,
                            'type': node.type,
                            'name': name,
                            'code': block_text
                        })
        return blocks


def build_index(blocks):
    documents = []
    for b in blocks:
        metadata = {
            'file': b['file'],
            'name': b['name'],
            'type': b['type']
        }
        doc = Document(text=b['code'], metadata=metadata)
        documents.append(doc)

    node_parser = SimpleNodeParser.from_defaults()
    nodes = node_parser.get_nodes_from_documents(documents)

    service_context = My_Service_Context('distilbert-base-uncased')
    index = VectorStoreIndex(nodes, service_context=service_context)
    return index


def CreateRAG(repo_path):
    if not os.path.exists(repo_path):
        print(f"Репозиторий не найден: {repo_path}")
        sys.exit(1)
    path = 'build/my-languages.so'
    parser_map = setting_languages(path)
    extractor = CodeExtractor(parser_map)
    print(f"Сканируем репозиторий: {repo_path}")
    blocks = extractor.extract_blocks(repo_path)
    print(f"Найдено фрагментов кода: {len(blocks)}")

    print("Строим индекс RAG...")
    index = build_index(blocks)
    query_engine = index.as_query_engine()
    return query_engine

if __name__ == '__main__':
    query_engine = CreateRAG(sys.argv[1] if len(sys.argv) > 1 else '.')
    print("Индекс RAG успешно создан.")
    print(query_engine.query(input()))
