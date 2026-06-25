import requests
import os
import time
import random
from google import genai
from google.genai import types
import base64

base_path = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_path, "seen.txt")

time.sleep(random.randint(1, 600))

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) Firefox/121.0'
]
headers = {'User-Agent': random.choice(user_agents)}

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)


def analyze_car(data_for_ai, images=None):
    contents = []

    if images:
        contents.extend(images)

    prompt = f"""
    {data_for_ai}
    Jesteś profesjonalnym analitykiem rynku samochodowego. Twoim zadaniem jest dostarczenie suchej, technicznej oceny na podstawie powyższych danych i zdjęć

    WYTYCZNE MERYTORYCZNE:
    1. ZAKAZ używania żartów, metafor, sarkazmu i potocznego języka (np. "złom", "handlarz").
    2. Skup się wyłącznie na faktach technicznych i liczbach.
    3. Jeśli w danych BRAK konkretnych wad (typu: uszkodzony silnik, brak kluczyków), w sekcji 🚩 napisz wyłącznie: "Brak krytycznych uwag w opisie".
    4. PRZEBIEG: Jeśli jest podany i wynosi >300 000 km, wspomnij o tym jako o ryzyku (o ile w ogóle w tym konkretnym modelu jest to ryzykiem). Jeśli go nie ma - całkowicie pomin ten temat (nie pisz, że go brakuje).
    5. Jeśli nie ma zdjęć to nie uwzględniaj tego w żanym wypadku w analizie. Nie pisz wtedy w ogóle nawet "UWAGI NA PODSTAWIE ZDJĘĆ".

    STRUKTURA (Utrzymaj tę formę):
    💰FINANSE
    - Rynkowa: [średnia cena modelu/rocznika] PLN
    - Wywołanie: [cena] PLN (Różnica: [X]%)

    ⚙️GŁÓWNE RYZYKA TECHNICZNE MODELU
    - [konkretna usterka silnika/skrzyni, np. koło dwumasowe]
    - [konkretna usterka modelu, np. korozja progów]

    🚩UWAGI DO EGZEMPLARZA
    [Tu wpisz konkret z opisu LUB "Brak krytycznych uwag w opisie"]

    UWAGI NA PODSTAWIE ZDJĘĆ
    [Co widać na zdjęciach o czym warto wspomnieć. JEŚLI nie ma zdjęć nie pisz nic]

    NA CO ZWRÓCIĆ UWAGĘ PODCZAS KUPNA
    - [przykladowa rzecz którą warto sprawdzić]

    ⚖️OCENA POTENCJAŁU: X/10
    """

    contents.append(prompt)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents
    )
    return response.text


def send_telegram(message):
    api_url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "disable_web_page_preview": True
    }

    requests.post(api_url, data=payload)
    time.sleep(0.5)


def get_auction_details(auction_id):
    try:
        api_url = f"https://licytacje.komornik.pl/services/item-back/rest/item/{auction_id}"

        r = requests.get(api_url, headers=headers, timeout=10)
        data = r.json()

        obj = data.get("object", {})

        title = obj.get("name", "Licytacja")
        start = obj.get("startAuction", "brak")

        if start != "brak":
            from datetime import datetime
            start = datetime.fromisoformat(start.replace("Z", "")).strftime("%d.%m.%Y %H:%M")

        price = obj.get("openingValue", "brak danych")
        estimation = obj.get("estimate", "brak danych")
        description = obj.get("description", "brak danych")
        engineCapacity = obj.get("additionalParams", {}).get("ENGINECAPACITY", {}).get("value", "brak danych")
        mileage = obj.get("additionalParams", {}).get("MILEAGE", {}).get("value", "brak danych")
        gearbox = obj.get("additionalParams", {}).get("GEARBOX", {}).get("value", "brak danych")

        images = []

        if obj.get("attachments"):
            for attachment in obj.get("attachments"):
                raw_base64 = attachment.get("fileContent")

                if raw_base64:
                    img = types.Part.from_bytes(
                        data=base64.b64decode(raw_base64),
                        mime_type="image/jpeg",
                    )

                    images.append(img)

        return {
            "title": title,
            "price": price,
            "start": start,
            "estimation": estimation,
            "description": description,
            "engineCapacity": engineCapacity,
            "mileage": mileage,
            "gearbox": gearbox,
            "images": images
        }

        # return title, price, estimation, start

    except Exception as e:
        print("API error:", e)
        # return "Licytacja", "brak", "brak", "brak"
        return {
            "title": "Licytacja",
            "price": "brak danych",
            "start": "brak danych",
            "estimation": "brak danych",
            "description": "brak danych",
            "engineCapacity": "brak danych",
            "milleage": "brak danych",
            "gearbox": "brak danych"
        }


# START
search_url = "https://licytacje.komornik.pl/services/item-back/rest/item/search"

payload = {
    "limit": 10,
    "orderBy": "DESC",
    "orderByField": "dateCreated",
    "termFilters": [
        {"field": "subCategory", "value": ["CARS"]},
        {"field": "mainCategory", "value": ["MOVABLE"]},
        {"field": "joinable", "value": ["true"]}
    ]
}

r = requests.post(search_url, json=payload, headers=headers)
data = r.json()

ids = []

for item in data["items"]:
    ids.append(str(item["id"]))

# Wczytywanie bazy
if os.path.exists(db_path):
    with open(db_path, "r") as f:
        seen = f.read().splitlines()
else:
    seen = []

new_seen = set(seen)

for auction_id in ids:
    if auction_id not in new_seen:
        full_link = f"https://licytacje.komornik.pl/licytacje/{auction_id}/"
        data = get_auction_details(auction_id)
        # title, price, estimation, start = get_auction_details(auction_id)

        title = data.get("title")
        price = data.get("price")
        start = data.get("start")
        estimation = data.get("estimation")

        description = data.get("description")
        engineCapacity = data.get("engineCapacity")
        mileage = data.get("mileage")
        gearbox = data.get("gearbox")
        images = data.get("images")

        data_for_ai = f"""
        TYTUL: {title}
        PRZEBIEG: {mileage} km
        SILNIK: {engineCapacity}
        CENA WYWOŁAWCZA: {price} PLN
        WARTOŚĆ OSZACOWANA: {estimation} PLN
        TERMIN LICYTACJI: {start} PLN
        OPIS TECHNICZNY: {description}
        """

        try:
            ai_analysis = analyze_car(data_for_ai, images)
        except Exception as e:
            ai_analysis = "BŁĄD. Prawdopodobnie wyczerpanie tokenów"

        message = (
            f"🚨Nowa licytacja!\n\n"
            f"🚗{title}\n\n"
            f"💰Cena wywoławcza: {price}\n"
            f"📊Cena oszacowania: {estimation}\n"
            f"📅Początek licytacji: {start}\n\n"
            f"🔗{full_link}\n\n"
            f"Analiza: {ai_analysis}"
        )
        send_telegram(message)

        new_seen.add(auction_id)

# Zapisywanie wszystkich aktualnych ID
with open(db_path, "w") as f:
    for aid in new_seen:
        f.write(aid + "\n")