# Monitor Licytacji Komorniczych AI

## Automatyczne narzędzie do monitorowania nowych licytacji komorniczych samochodów, wykorzystujące sztuczną inteligencję do wstępnej analizy technicznej.

## Kluczowe funkcjonalności: 
- Scraping danych: pobiera najnowsze ogłoszenia z kategorii "samochody osobowe".
- Analiza AI (Gemini 2.5 Flash): model analizuje opis techniczny oraz zdjęcia licytowanego obiektu, wyciągając najważniejsze ryzyka, wady i potencjał finansowy.
- System powiadomień: wysłanie powiadomienia na Telegram z linkiem do aukcji i analizą.
- Baza "widzianych" ofert: prosty mechanizm zapobiegający dublowaniu powiadomień.

## Technologie: 
- Python 3.10.11
- Google Gemini API
- Telegram Bot API
- Requests

## Planowane usprawnienia:
- [x] Przeniesienie kluczy do zmiennych środowiskowych (.env).
- [ ] Refaktoryzacja kodu (rozbicie kodu na mniejsze funkcje).
- [ ] Implementacja bazy danych zamiast pliku tekstowego.
