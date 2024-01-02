"""Pre-commit hook to check if there is a method longer than length threshold without docstring."""
import ast
import sys

METHOD_LENGTH_THRESHOLD = 6  # lines

has_error = False


def check_file(filename):
    global has_error
    with open(filename, "r") as f:
        source = f.read()
    module = ast.parse(source, filename)
    for node in ast.walk(module):
        if isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.FunctionDef):
            # Skip methods that have a docstring
            if ast.get_docstring(node):
                continue
            func_source = ast.get_source_segment(source, node)
            lines = func_source.split("\n")
            # Save end of method definition part to skip
            method_def_end = next(
                (i for i, line in enumerate(lines) if line.strip().endswith(":")),
                len(lines),
            )
            code_lines = []
            for line in lines[method_def_end + 1 :]:
                stripped = line.strip()
                # Skip docstring part and comments
                if stripped and not stripped.startswith("#"):
                    code_lines.append(line)
            # Check with pydocstyle for methods over specified length
            if len(code_lines) > METHOD_LENGTH_THRESHOLD:
                # Print log with link to line of code
                print(f"{filename}:{node.lineno} missing docstring.")
                has_error = True
    # Returns appropriate exit code for pre-commit
    if has_error:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    for filename in sys.argv[1:]:
        check_file(filename)
