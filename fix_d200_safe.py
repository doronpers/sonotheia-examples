import os


def fix_file(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    changed = False
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check for """ followed by newline, then a single line of text, then newline and """
        if (
            i + 2 < len(lines)
            and line.strip() == '"""'
            and lines[i + 2].strip() == '"""'
            and "\n" not in lines[i + 1].strip()
        ):
            # Construct one-liner
            content = lines[i + 1].strip()
            indent = line[: line.find('"""')]
            new_lines.append(f'{indent}"""{content}"""\n')
            i += 3
            changed = True
        else:
            new_lines.append(line)
            i += 1

    if changed:
        with open(path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        return True
    return False


for root, dirs, files in os.walk("."):
    if ".venv" in dirs:
        dirs.remove(".venv")
    if ".git" in dirs:
        dirs.remove(".git")
    for file in files:
        if file.endswith(".py"):
            if fix_file(os.path.join(root, file)):
                print(f"Fixed {os.path.join(root, file)}")
