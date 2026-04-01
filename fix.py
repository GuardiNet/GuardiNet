import re, os
def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    content = re.sub(r"==\s*None", "is None", content)
    content = re.sub(r"f(['\"])([^'{}]*)\1", r"\1\2\1", content)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

fix_file("app/routes/main.py")
fix_file("database/init-scripts/init_db.py")
