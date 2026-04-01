with open("database/init-scripts/init_db.py", "r", encoding="utf-8") as f:
    text = f.read()

text = text.replace("f\"  Password:", "\"  Password:")
text = text.replace("f\"\\n IMPORTANT:", "\"\\n IMPORTANT:")

text = text.replace("f\"  🔑 Password:", "\"  🔑 Password:")
text = text.replace("f\"\\n⚠�  IMPORTANT:", "\"\\n⚠�  IMPORTANT:")

with open("database/init-scripts/init_db.py", "w", encoding="utf-8") as f:
    f.write(text)
