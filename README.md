# Nástroj pro odhad retenční schopnosti území (metoda SCS-CN)

Uživatel si musí v souborech config.py a spouštěcích skriptech upravit cesty k interpretu Pythonu a datům podle svého lokálního nastavení.

Tento softwarový nástroj v jazyce Python byl vyvinut jako praktický výstup bakalářské práce. Slouží k automatizovanému výpočtu potenciální retence krajiny a odhadu povrchového odtoku na základě integrace dat o využití území (CORINE Land Cover) a pedologických vlastností (BPEJ).

## Struktura projektu
Projekt je rozdělen do logických modulů pro zajištění přehlednosti a znovupoužitelnosti kódu:

* `main.py` – Hlavní řídící skript zajišťující chod celého výpočetního řetězce.
* `config.py` – Centrální konfigurace cest, souřadnicových systémů (S-JTSK) a parametrů simulace.
* `src/preprocessing.py` – Modul pro čištění, reprojekci a prostorový průnik (overlay) vstupních dat.
* `src/retention.py` – Implementace matematického aparátu metody SCS-CN (výpočet S, Ia a Q).
* `src/visualization.py` – Generování statistických přehledů, exportů do Excelu a vizualizačních grafů.
* `utils.py` – Pomocné funkce pro logování výpočtů a tvorbu prostorových masek.

## Instalace a spuštění

1.  **Prerekvizity:** Doporučujeme použít distribuci Conda (prostředí je definováno v `run_script.bat`).
2.  **Instalace knihoven:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Konfigurace:** Před spuštěním upravte cesty k datům v souboru `config.py`.
4.  **Spuštění:** Spusťte `main.py` nebo využijte připravený `run_script.bat` (pro Windows).

## Důležité upozornění k datům
Vzhledem k **vysoké datové náročnosti** a licenčním omezením nejsou v tomto repozitáři zahrnuty plné verze vstupních rastrových a vektorových dat (národní sady BPEJ a CORINE dosahují velikosti přes 3 GB).

* Repozitář obsahuje veškerou **logiku výpočtu**.
* Pro otestování funkčnosti je nutné do složky `data/raw` vložit odpovídající `.shp` nebo `.gpkg` soubory specifikované v dokumentaci.
* V případě potřeby poskytnutí testovacích dat mě prosím kontaktujte.

## Použité technologie
* **Jazyk:** Python 3.x
* **Klíčové knihovny:** GeoPandas, Rasterio, NumPy, Matplotlib, Pandas
