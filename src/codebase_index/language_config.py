from tree_sitter import Language

Language.build_library(
  # Store the library in the `build` directory
  'build/my-languages.so',

  # Include one or more languages
  [
    'vendor/tree-sitter-go',
    'vendor/tree-sitter-javascript',
    'vendor/tree-sitter-python',
    'vendor/tree-sitter-rust',
    'vendor/tree-sitter-zig',
    'vendor/tree-sitter-cpp',
    'vendor/tree-sitter-c',
    'vendor/tree-sitter-typescript',
  ]
)

GO_LANGUAGE = Language('build/my-languages.so', 'go')
JS_LANGUAGE = Language('build/my-languages.so', 'javascript')
PYTHON_LANGUAGE = Language('build/my-languages.so', 'python')
RUST_LANGUAGE = Language('build/my-languages.so', 'rust')
ZIG_LANGUAGE = Language('build/my-languages.so', 'zig')
CPP_LANGUAGE = Language('build/my-languages.so', 'cpp')
C_LANGUAGE = Language('build/my-languages.so', 'c')
TYPESCRIPT_LANGUAGE = Language('build/my-languages.so', 'typescript')
TSX_LANGUAGE = Language('build/my-languages.so', 'tsx')
JSX_LANGUAGE = TSX_LANGUAGE

LANGUAGE_CONFIG = {
    'go': GO_LANGUAGE,
    'js': JS_LANGUAGE,
    'py': PYTHON_LANGUAGE,
    'rs': RUST_LANGUAGE,
    'zig': ZIG_LANGUAGE,
    'cpp': CPP_LANGUAGE,
    'c': C_LANGUAGE,
    'ts': TYPESCRIPT_LANGUAGE,
    'js': JS_LANGUAGE,
    'tsx': TSX_LANGUAGE,
    'jsx': JSX_LANGUAGE,
}
