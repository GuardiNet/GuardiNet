import re, os

def fix_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    # fix E711 in sqlalchemy
    content = re.sub(r"==\s*None", ".is_(None)", content)
    
    # fix F541 in init_db
    if "init_db.py" in filepath:
        content = re.sub(r'f"([^"{}]+)"', r'"\1"', content)
        content = re.sub(r'f"(\s+[^"{}]+)"', r'"\1"', content)
        content = re.sub(r'f"(\s*\n.+)"', r'"\1"', content)
        
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

fix_file("app/routes/main.py")
fix_file("database/init-scripts/init_db.py")
