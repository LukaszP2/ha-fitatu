# Fitatu – Home Assistant Custom Component

[![GitHub Release](https://img.shields.io/github/v/release/LukaszP2/ha-fitatu?style=flat-square)](https://github.com/LukaszP2/ha-fitatu/releases)
[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg?style=flat-square)](https://hacs.xyz)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)

[![Otwórz repozytorium w HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LukaszP2&repository=ha-fitatu&category=integration)
[![Dodaj integrację do Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fitatu)

*(🇬🇧 English description below)*

---

## 🇵🇱 Opis

Integracja Home Assistant z aplikacją Fitatu (licznik kalorii i dziennik diety). Pozwala na bieżące monitorowanie spożycia kalorii, makroskładników, wagi ciała oraz szybkie dodawanie posiłków za pomocą usług Home Assistant.

### Główne funkcje
- Bieżące spożycie kalorii oraz cel dzienny (kcal, bilans)
- Szczegółowe śledzenie makroskładników: białko, tłuszcze, węglowodany
- Monitorowanie wagi ciała i postępów
- Wybór monitorowanych kategorii w opcjach integracji (odżywianie, aktywność, pomiary ciała, nawodnienie)
- Zestaw usług do zarządzania dziennikiem diety, aktywnością, wodą i pomiarami

### Dostępne usługi / akcje (Services)
Integracja udostępnia zestaw usług dla administratorów Home Assistant:
- **Posiłki i produkty:**
  - `fitatu.add_custom_item` – dodaje własny posiłek z kaloriami i makroskładnikami
  - `fitatu.add_product` – dodaje produkt z katalogu Fitatu (na podstawie `product_id` i `measure_id`)
  - `fitatu.add_product_unit` – dodaje produkt z katalogu podając jednostkę i ilość
  - `fitatu.add_recipe` – dodaje przepis z bazy Fitatu
  - `fitatu.update_item` – edytuje istniejący wpis posiłku
  - `fitatu.remove_item` – usuwa wpis posiłku
  - `fitatu.move_item` – przenosi wpis do innego posiłku lub dnia
  - `fitatu.copy_meal` – kopiuje cały posiłek do innego posiłku lub dnia
  - `fitatu.replace_item` – zastępuje wpis posiłku wpisem własnym
- **Woda i nawodnienie:**
  - `fitatu.set_water` – ustawia dzienną ilość wypitej wody (w ml)
  - `fitatu.set_water_glass_size` – konfiguruje domyślną pojemność szklanki wody
- **Pomiary ciała i notatki:**
  - `fitatu.set_measurements` – zapisuje pomiary ciała (waga, tkanka tłuszczowa, obwody)
  - `fitatu.delete_measurements` – usuwa pomiary ciała z wybranego dnia
  - `fitatu.set_note` – zapisuje lub czyści notatkę dzienną
- **Aktywność fizyczna:**
  - `fitatu.add_activity` – dodaje aktywność z katalogu (czas trwania i spalone kcal)
  - `fitatu.remove_activity` – usuwa zarejestrowaną aktywność

### Instalacja przez HACS (Niestandardowe repozytorium)

### 🚀 Szybka instalacja (1 kliknięcie przez My Home Assistant)

[![Otwórz repozytorium w HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=LukaszP2&repository=ha-fitatu&category=integration)

Po zainstalowaniu i ponownym uruchomieniu Home Assistant, kliknij poniższy przycisk, aby skonfigurować integrację:

[![Dodaj integrację do Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=fitatu)

#### Instalacja ręczna:
1. Upewnij się, że masz zainstalowany **HACS** w Home Assistant.
2. W HACS przejdź do: **Integracje** -> menu w prawym górnym rogu (trzy kropki) -> **Niestandardowe repozytoria** (*Custom repositories*).
3. W polu **Repozytorium** wklej adres:
   ```text
   https://github.com/LukaszP2/ha-fitatu
   ```
4. W polu **Kategoria** wybierz: **Integracja** (*Integration*).
5. Kliknij **Dodaj**, a następnie wyszukaj **Fitatu** i kliknij **Pobierz**.
6. Uruchom ponownie Home Assistant.

### Konfiguracja

1. W Home Assistant przejdź do: **Ustawienia** -> **Urządzenia oraz usługi** -> **Dodaj integrację**.
2. Wyszukaj **Fitatu**.
3. Zaloguj się swoimi danymi konta.

---

## 🇬🇧 Description

Home Assistant integration for Fitatu (calorie counter and diet diary). Tracks calories, macronutrients, body weight, and provides services to log food directly from Home Assistant.

### Available Services
- **Food & Meals:** `fitatu.add_custom_item`, `fitatu.add_product`, `fitatu.add_product_unit`, `fitatu.add_recipe`, `fitatu.update_item`, `fitatu.remove_item`, `fitatu.move_item`, `fitatu.copy_meal`, `fitatu.replace_item`
- **Hydration:** `fitatu.set_water`, `fitatu.set_water_glass_size`
- **Body Measurements & Notes:** `fitatu.set_measurements`, `fitatu.delete_measurements`, `fitatu.set_note`
- **Activities:** `fitatu.add_activity`, `fitatu.remove_activity`

### Installation via HACS (Custom Repository)

1. Open **HACS** in Home Assistant.
2. Navigate to **Integrations** -> top right menu (three dots) -> **Custom repositories**.
3. Enter repository URL:
   ```text
   https://github.com/LukaszP2/ha-fitatu
   ```
4. Category: **Integration**.
5. Click **Add**, find **Fitatu**, and install.
6. Restart Home Assistant.

---

## Licencja / License

Projekt objęty licencją [MIT](LICENSE).
