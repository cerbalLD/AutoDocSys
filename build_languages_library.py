import os
from tree_sitter import Language

def build_languages_library(path='build/languages.so'):
    
    if os.path.exists(path):
        print(f"Library {path} already exists. Skipping build.")
        return
    
    print(f"Building languages library at {path}...")
    
    Language.build_library(
        path,
        [
            'vendor/tree-sitter-python',
            'vendor/tree-sitter-c-sharp',
        ]
    )
    
    print(f"Library built successfully at {path}.")

if __name__ == '__main__':
    build_languages_library()