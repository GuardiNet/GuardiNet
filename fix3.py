with open("app/routes/main.py", "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace("            | (Announcement.class_id.is_(None))", "            (Announcement.class_id.is_(None))")
with open("app/routes/main.py", "w", encoding="utf-8") as f:
    f.write(text)
