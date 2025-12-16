import base64

# קריאת הקובץ והמרה ל-Base64 בשורה אחת ארוכה
with open("service_account.json", "rb") as f:
    # ההמרה הזו מבטיחה שורה אחת רציפה בלי שבירות
    encoded_string = base64.b64encode(f.read()).decode("utf-8")

# כתיבה לקובץ נקי וחדש
with open("copy_this.txt", "w") as f:
    f.write(f'GCP_JSON_BASE64 = "{encoded_string}"')

print("DONE! Open 'copy_this.txt' and copy everything inside.")