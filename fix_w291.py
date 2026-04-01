with open("app/routes/main.py", "r", encoding="utf-8") as f:
    text = f.read()
text = text.replace(" (Announcement.class_id.in_(class_ids)) \n", " (Announcement.class_id.in_(class_ids))\n")
with open("app/routes/main.py", "w", encoding="utf-8") as f:
    f.write(text)
