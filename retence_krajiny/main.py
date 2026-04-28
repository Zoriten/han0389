"""
Hlavní řídící modul nástroje pro modelování retence krajiny.

Tento skript integruje všechny dělající moduly (vstup dat, preprocessing, hydrologický výpočet a vizualizaci).
Poskytuje interaktivní rozhraní pro uživatele, které umožňuje:
1. Definici srážkového úhrnu pro modelování odtokových situací.
2. Automatizované generování prostorové masky na základě GPS souřadnic.
3. Řízení celého výpočetního řetězce (pipeline) od surových GIS dat po výsledné reporty.
"""
import os
import sys

# --- KRITICK� OPRAVA: Izolace PROJ prost�ed� (�e�en� kolize s PostGIS) ---
# Tato sekce mus� b�t na �pln�m za��tku p�ed importem geopandas/pyproj
conda_env = r'C:\Users\Alttr\miniconda3\envs\pgis2'

# Nastaven� PATH pro prioritizaci Conda knihoven
os.environ['PATH'] = os.path.join(conda_env, 'Library', 'bin') + os.path.pathsep + os.environ['PATH']

# Nastaven� PROJ a GDAL cest
proj_path = os.path.join(conda_env, 'Library', 'share', 'proj')
gdal_path = os.path.join(conda_env, 'Library', 'share', 'gdal')

os.environ['PROJ_LIB'] = proj_path
os.environ['PROJ_DATA'] = proj_path
os.environ['GDAL_DATA'] = gdal_path

# Vynucen� cesty v r�mci knihovny pyproj
try:
    import pyproj
    pyproj.datadir.set_data_dir(proj_path)
except Exception:
    pass

from pathlib import Path
root_path = Path(__file__).resolve().parent
sys.path.append(str(root_path))

from config import load_default_config
from src.utils import check_environment, check_input_files, create_mask_from_point, write_log
from src.preprocessing import preprocess_data
from src.retention import calculate_retention
from src.visualization import create_graphs_and_statistics

def get_input(cfg):
    """
    Interaktivní konzolové rozhraní pro sběr uživatelských parametrů.
    Zajišťuje validaci vstupů a nastavení konfigurace pro aktuální běh výpočtu.
    """
    print("\n" + "="*55)
    print("  NASTAVENÍ PARAMETRŮ VÝPOČTU")
    print("="*55)
    
    # --- 1. Definice srážkového úhrnu ---
    rainfall_input = input(f" Zadej srážkový úhrn v mm [výchozí {cfg.rainfall_mm} mm - stiskni Enter]: ").strip()
    if rainfall_input:
        try:
            cfg.rainfall_mm = float(rainfall_input.replace(',', '.'))
        except ValueError:
            print(f" Neplatný formát čísla! Byla zachována výchozí hodnota: {cfg.rainfall_mm} mm")

    # --- 2. Definice zájmového území (Spatial Extent) ---
    lat, lon, radius = None, None, None
    wants_mask = input("\n Chceš vygenerovat nové území pomocí GPS? (ano/ne) [výchozí 'ne' - stiskni Enter]: ").strip()
    
    if wants_mask.lower() in ['ano', 'a', 'yes', 'y']:
        print("\n Vložte souřadnice ve formátu dekadických stupňů (např. z Mapy.cz).")
        coords = input("Vstup (např. 49.8682N, 18.3326E) [stiskni Enter pro zrušení]: ").strip()
        
        if coords:
            try:
                # Normalizace textového vstupu: odstranění doprovodných znaků a sjednocení oddělovačů
                clean_input = coords.upper().replace('N', ' ').replace('E', ' ').replace('S', ' ').replace('W', ' ').replace('°', ' ').replace(',', ' ')
                parts = clean_input.split()
                
                if len(parts) >= 2:
                    lat = float(parts[0])
                    lon = float(parts[1])
                    
                    # Definice poloměru kruhové výseče pro ořez dat
                    radius_input = input(" Zadej poloměr území v km (max 10) [výchozí 2.5 - stiskni Enter]: ").strip()
                    radius = float(radius_input.replace(',', '.')) if radius_input else 2.5
                    
                    # Implementace bezpečnostního limitu pro ochranu operační paměti při zpracování BPEJ
                    if radius > 10.0:
                        print(" Z bezpečnostních důvodů (velikost dat) byl poloměr omezen na 10 km.")
                        radius = 10.0
                        
                    create_mask_from_point(cfg, lat, lon, radius)
                else:
                    print(" Chybný formát souřadnic. Výpočet byl ukončen.")
                    sys.exit(1)
            except Exception as e:
                print(f"\nChyba při zpracování souřadnic: {e}")
                print(" Zadejte platné geografické údaje v rámci území ČR.")
                sys.exit(1)
        else:
            print("Nebyl zadán žádný vstup. Pokračuji s existující prostorovou maskou.")

    # --- 3. Personalizace výstupů ---
    print("\n" + "-"*55)
    custom_name = input(" Název výstupních souborů [výchozí 'retence_vysledek' - stiskni Enter]: ").strip()
    cfg.nazev_souboru = custom_name if custom_name else "retence_vysledek"

    default_title = f"Průměrný povrchový odtok při srážce {cfg.rainfall_mm} mm"
    custom_title = input(" Nadpis do grafu [stiskni Enter pro automaticky generovaný nadpis]: ").strip()
    cfg.nadpis_grafu = custom_title if custom_title else default_title

    # Dokumentace parametrů výpočtu do logovacího souboru
    write_log(cfg, lat, lon, radius)


def main():
    """
    Hlavní exekuční smyčka programu.
    Řídí sekvenční volání jednotlivých funkčních modulů a zajišťuje ošetření chyb.
    """
    print("=======================================================")
    print(" VÝPOČET RETENCE KRAJINY A POVRCHOVÉHO ODTOKU ")
    print("=======================================================\n")
    
    # Iniciace konfigurace a validace systémových cest
    cfg = load_default_config()
    check_environment(cfg)
    
    # Sběr dat od uživatele
    get_input(cfg)
    
    print(f"\n INICIALIZACE VÝPOČTU: {cfg.nazev_souboru}")
    print(f" Zvolený úhrn srážek: {cfg.rainfall_mm} mm\n")

    # Validace přítomnosti nezbytných GIS podkladů v složišti data/raw
    required_files = ["ft_pudniJednotka.shp", "CLC18_CZ.shp", "maska.gpkg"]
    if not check_input_files(cfg, required_files):
        sys.exit(1)
        
    print("-" * 55 + "\n")

    try:
        # FÁZE 1: Geoprocessing (Načtení, reprojekce a prostorový průnik datových sad)
        print(" KROK 1: Prostorové zpracování a filtrace dat (Preprocessing)")
        preprocess_data(cfg)
        
        # FÁZE 2: Hydrologický model (Aplikace matematického aparátu SCS-CN)
        print("\n KROK 2: Aplikace hydrologického modelu a výpočet odtokové bilance")
        calculate_retention(cfg)
        
        # FÁZE 3: Postprocessing (Statistická sumarizace a vizuální interpretace)
        print("\n KROK 3: Generování statistických přehledů, grafů a exportů")
        create_graphs_and_statistics(cfg)
        
        # Závěrečný informační výstup
        print("\n" + "="*55)
        print(" PROCES BYL ÚSPĚŠNĚ DOKONČEN!")
        print(f" Prostorová data (GPKG): {cfg.nazev_souboru}.gpkg")
        print(f" Vizualizace (PNG):      {cfg.nazev_souboru}.png")
        print(f" Datový report (XLSX):    {cfg.nazev_souboru}.xlsx")
        print(f" Provozní deník:          vypocet.log")
        print(f" Cesta k výsledkům:       {cfg.data_results_dir}")
        print("="*55)

    except Exception as e:
        # Zachycení neočekávaných chyb v průběhu výpočetní pipeline
        print(f"\nDošlo k selhání výpočetního modulu: {e}")

if __name__ == "__main__":
    main()
