import requests
import os

# Download Tailwind CSS
url = "https://cdn.tailwindcss.com"
response = requests.get(url)

if response.status_code == 200:
    # Create css directory if it doesn't exist
    os.makedirs('akuna_calc/static/css', exist_ok=True)
    
    # Save Tailwind CSS
    with open('akuna_calc/static/css/tailwind.css', 'w', encoding='utf-8') as f:
        f.write(response.text)
    
    print("✅ Tailwind CSS descargado exitosamente")
else:
    print("❌ Error descargando Tailwind CSS")