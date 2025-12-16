import base64

# קריאת הקובץ והמרה ל-Base64
with open("service_account.json", "rb") as f:
    encoded_string = base64.b64encode(f.read()).decode("utf-8")

print("--- העתק את השורה למטה (הכל בשורה אחת) ---")
print(encoded_string)
print("--- סוף ---")