import os
import re


def fix_d200(content):
    # Regex to match multi-line docstrings that should be one-liners
    pattern = r'"""\n\s*([^\n]+)\n\s*"""'
    replacement = r'"""\1"""'
    return re.sub(pattern, replacement, content)


for root, dirs, files in os.walk("."):
    if ".venv" in dirs:
        dirs.remove(".venv")
    if ".git" in dirs:
        dirs.remove(".git")

    for file in files:
        if file.endswith(".py") and file != "fix_d200.py":
            path = os.path.join(root, file)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

                new_content = fix_d200(content)

                if new_content != content:
                    print(f"Fixing {path}")
                    with open(path, "w", encoding="utf-8") as f:
                        f.write(new_content)
            except UnicodeDecodeError:
                print(f"Skipping binary/non-utf8 file: {path}")
            except Exception as e:
                print(f"Error processing {path}: {e}")
