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
- Usługa `fitatu.add_custom_item` do szybkiego dodawania posiłków z poziomu automatyzacji i dashboardów

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
