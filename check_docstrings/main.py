"""Pre-commit hook to check if there is a method longer than length threshold without docstring."""
import argparse
import ast
import sys

METHOD_LENGTH_THRESHOLD = 6  # lines
has_error = False
possible_func_call_api = {}


def check_file(filename):
    global has_error
    with open(filename, "r") as f:
        source = f.read()
    module = ast.parse(source, filename)
    for node in ast.walk(module):
        # checks normal and async functions but skips private functions
        if (
            isinstance(node, ast.AsyncFunctionDef) or isinstance(node, ast.FunctionDef)
        ) and not node.name.startswith("_"):
            # Skip methods that have a docstring
            if ast.get_docstring(node):
                continue
            # Api endpoints should have docstrings
            if is_func_an_endpoint(node):
                print_missing_docstring(filename, node)
                continue
            code_lines = count_code_lines(source, node)
            # Check with pydocstyle for methods over specified length
            if len(code_lines) > METHOD_LENGTH_THRESHOLD:
                # Print log with link to line of code
                print_missing_docstring(filename, node)
                has_error = True
                continue
            #If func is less than threshold Save name and line number
            possible_func_call_api[node.name] = node.lineno
        # Check if function call is an endpoint
        elif isinstance(node, ast.Call):
            print_error_if_func_call_is_an_endpoint(filename, node, possible_func_call_api)
            
    # Returns appropriate exit code for pre-commit
    if has_error:
        sys.exit(1)
    else:
        sys.exit(0)

def count_code_lines(source, node):
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
    return code_lines


def is_func_an_endpoint(node):    
    for decorator in node.decorator_list:
        if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
            if decorator.func.attr in ['route', 'get', 'post', 'put', 'delete', 'patch']:
                return True
    return False
    
def print_error_if_func_call_is_an_endpoint(filename, node: ast.Call, possible_func_call_api):
    if isinstance(node.func, ast.Call) and isinstance(node.func.func, ast.Attribute):
        if node.func.func.attr in ['route', 'get', 'post', 'put', 'delete', 'patch']:
            if isinstance(node.args[0], ast.Attribute):
                function_name = node.args[0].attr
                if function_name in possible_func_call_api:
                    
                    print(f"{filename}:{possible_func_call_api[function_name]} missing docstring.")
                    # print_missing_docstring(filename, node)


            
def print_missing_docstring(filename, node):
    global has_error
    print(f"{filename}:{node.lineno} missing docstring.")
    has_error = True

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--length", type=int, default=6, help="Method length threshold")
    return parser.parse_known_args()


def main():
    global METHOD_LENGTH_THRESHOLD
    args, filenames = parse_arguments()
    METHOD_LENGTH_THRESHOLD = args.length
    for filename in filenames:
        check_file(filename)


if __name__ == "__main__":
    main()
