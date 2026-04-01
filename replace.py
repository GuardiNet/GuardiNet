with open("app/routes/main.py", "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("(Announcement.class_id .is_(None)) |\n            (Announcement.class_id.in_(class_ids)) |\n            (Announcement.author_id == current_user.user_id)", "| (Announcement.class_id .is_(None))\n            | (Announcement.class_id.in_(class_ids)) \n            | (Announcement.author_id == current_user.user_id)")
content = content.replace("class_id .is_(None)", "class_id.is_(None)")

with open("app/routes/main.py", "w", encoding="utf-8") as f:
    f.write(content)
