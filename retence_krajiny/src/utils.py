"""
Pomocný modul (Utilities) pro správu prostředí a prostorové operace.

Tento skript obsahuje podpůrné funkce pro běh hlavního hydrologického modelu.
Zajišťuje validaci adresářové struktury, kontrolu existence nezbytných vstupních dat,
generování prostorových masek (výřezů) na základě uživatelských souřadnic a logování 
metadat o výpočtu pro zajištění reprodukovatelnosti výsledků.
"""
import sys
from pathlib import Path
import os
import datetime

# Fix for PROJ database context issue
# Set PROJ_DATA and PROJ_LIB to the correct path
# Try conda environment first
conda_proj_path = os.path.join(os.path.dirname(sys.executable), '..', 'Library', 'share', 'proj')
conda_proj_path = os.path.abspath(conda_proj_path)
conda_gdal_path = os.path.join(os.path.dirname(sys.executable), '..', 'Library', 'share', 'gdal')
conda_gdal_path = os.path.abspath(conda_gdal_path)

if os.path.exists(conda_proj_path):
    os.environ['PROJ_DATA'] = conda_proj_path
    os.environ['PROJ_LIB'] = conda_proj_path
    os.environ['GDAL_DATA'] = conda_gdal_path
else:
    # Fallback to PostgreSQL path
    proj_data_path = r"C:\Program Files\PostgreSQL\18\share\contrib\postgis-3.6\proj"
    if os.path.exists(proj_data_path):
        os.environ['PROJ_DATA'] = proj_data_path
        os.environ['PROJ_LIB'] = proj_data_path

import geopandas as gpd
from shapely.geometry import Point

def check_environment(cfg):
    """
    Validace a inicializace pracovního prostředí.
    Zajišťuje, že všechny potřebné složky pro čtení a zápis dat existují.
    Pokud ne, automaticky je vytvoří.
    """
    cfg.data_raw_dir.mkdir(parents=True, exist_ok=True)
    cfg.data_processed_dir.mkdir(parents=True, exist_ok=True)
    cfg.data_results_dir.mkdir(parents=True, exist_ok=True)
    print(" Kontrola adresářů: V pořádku.")

def check_input_files(cfg, required_files):
    """
    Validace dostupnosti primárních prostorových dat před spuštěním výpočtu.
    Chrání hlavní skript před pádem v důsledku chybějících vstupů (např. chybějící BPEJ nebo CORINE).
    
    Args:
        cfg: Konfigurační objekt obsahující cesty.
        required_files: Seznam názvů souborů, které musí být přítomny ve složce data/raw.
    """
    missing = [s for s in required_files if not (cfg.data_raw_dir / s).exists()]
    if missing:
        print("\n KRITICKÁ CHYBA: Ve složce 'data/raw' chybí tyto soubory:")
        for ch in missing: 
            print(f"   - {ch}")
        return False
    print(" Kontrola dat: Všechny potřebné zdrojové soubory byly nalezeny.")
    return True

def create_mask_from_point(cfg, lat, lon, radius_km):
    """
    Geoprocessing: Vytvoření kruhové ořezové masky pro zájmové území.
    Funkce přijme GPS souřadnice, provede prostorovou transformaci a vygeneruje polygon (buffer).
    Tato maska je v dalších krocích použita k ořezu velkoobjemových národních datových sad.
    """
    print("\n Generuji novou masku území...")
    
    # Bezpečnostní validace: Geografický bounding box (hraniční obdélník) České republiky.
    # Zabraňuje spuštění výpočtu pro souřadnice, kde chybí národní data (např. BPEJ).
    if not (48.0 < lat < 52.0 and 12.0 < lon < 19.0):
        raise ValueError(f" Zadané souřadnice ({lat}, {lon}) leží zcela mimo území ČR!")
        
    # Inicializace bodové geometrie v globálním referenčním systému WGS84 (EPSG:4326)
    point = Point(lon, lat)
    gdf_point = gpd.GeoDataFrame({'id': [1]}, geometry=[point], crs="EPSG:4326")
    
    # Transformace (reprojekce) do lokálního rovinného systému S-JTSK (EPSG:5514).
    # Toto je nezbytný krok, protože operace typu 'buffer' vyžadují metrický souřadnicový systém,
    # nikoliv úhlové stupně z WGS84.
    gdf_sjtsk = gdf_point.to_crs(epsg=cfg.crs_epsg)
    radius_m = radius_km * 1000
    
    # Tvorba bufferu (kružnice) s exaktním poloměrem v metrech
    gdf_mask = gdf_sjtsk.copy()
    gdf_mask.geometry = gdf_sjtsk.geometry.buffer(radius_m)

    # Export výsledné prostorové masky do formátu GeoPackage pro navazující analytické kroky
    mask_path = cfg.data_raw_dir / "maska.gpkg"
    gdf_mask.to_file(mask_path, driver="GPKG")
    print(f" Nová maska (kružnice o poloměru max {radius_km} km) uložena.")

def write_log(cfg, lat=None, lon=None, radius=None):
    """
    Logování metadat o průběhu výpočtu pro zajištění transparentnosti a reprodukovatelnosti.
    Každý běh modelu zaznamená přesné parametry (srážka, souřadnice, názvy) společně s časovou stopou.
    """
    log_path = cfg.data_results_dir / "vypocet.log"
    time_stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"--- ZÁZNAM O VÝPOČTU [{time_stamp}] ---\n")
        f.write(f"Srážkový úhrn: {cfg.rainfall_mm} mm\n")
        f.write(f"Výstupní soubor: {getattr(cfg, 'nazev_souboru', 'default')}\n")
        
        # Zápis prostorových specifikací (zda byla generována nová maska, nebo použita existující)
        if lat and lon:
            f.write(f"Nové území (střed): {lat}, {lon} (Poloměr: {radius} km)\n")
        else:
            f.write("Použita původní/manuální maska území.\n")
            
        f.write("-" * 40 + "\n\n")
    print(f" Parametry výpočtu byly zaznamenány do: {log_path}")