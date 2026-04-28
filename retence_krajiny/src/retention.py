"""
Hlavní výpočetní modul hydrologického modelu (SCS-CN metoda).

Tento skript aplikuje rovnice metody Soil Conservation Service - Curve Number (SCS-CN)
na předzpracovaná prostorová data. Pro každý polygon v zájmovém území:
1. Přiřadí hodnotu odtokové křivky (CN).
2. Vypočítá potenciální maximální retenci (S).
3. Vypočítá počáteční ztrátu (Ia).
4. Stanoví výsledný přímý povrchový odtok (Q) pro zadaný srážkový úhrn.
"""
import sys
from pathlib import Path
import geopandas as gpd
import numpy as np

# Zajištění přístupu ke kořenovému adresáři projektu a konfiguraci
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from config import load_default_config
from src.cn_model import bpej_to_soil_group, compute_cn

def calculate_retention(cfg):
    
    # Definice vstupních a výstupních cest
    # Vstupem je vrstva prostorového průniku (BPEJ x CORINE) z předchozího kroku (preprocessing.py)
    input_path = cfg.data_processed_dir / "bpej_corine_prunik.gpkg"
    
    # Dynamické nastavení názvu výstupního souboru podle volby uživatele
    gpkg_name = getattr(cfg, 'nazev_souboru', 'retence_vysledek') + ".gpkg"
    output_path = cfg.data_results_dir / gpkg_name
    
    print("--- 1. Načítám zpracovaná data ---")
    gdf = gpd.read_file(input_path)
    print(f"Načteno {len(gdf)} polygonů k analýze.")

    def calculate_cn_for_row(row):
        """
        Pomocná iterační funkce pro extrakci parametrů z každého polygonu.
        Z atributové tabulky načte kód BPEJ a CORINE, převede BPEJ na hydrologickou 
        skupinu půdy (HSP) a následně dotazem do CN_LOOKUP tabulky získá hodnotu CN.
        """
        try:
            bpej_code = int(row['BPEJ_KOD'])
            hsp = bpej_to_soil_group(bpej_code)
            corine_code = int(row['Code_18'])
            return compute_cn(corine_code, hsp)
        except Exception as e:
            # Hodnota -1 značí datovou anomálii nebo chybějící klasifikaci ve zdrojových datech
            return -1

    print("\n--- 2. Počítám Curve Number (CN) a maximální retenci (S) ---")
    # Aplikace funkce na každý polygon (řádek GeoDataFrame)
    gdf['CN'] = gdf.apply(calculate_cn_for_row, axis=1)
    
    # Matematický model: Výpočet potenciální maximální retence území (S) v milimetrech.
    # Metodika SCS-CN využívá pro převod z palců na milimetry konstantu 254.
    # Podmínka np.where zajišťuje, že se výpočet provede pouze pro platné CN hodnoty (>0).
    gdf['S_mm'] = np.where(gdf['CN'] > 0, (25400 / gdf['CN']) - 254, 0)
    
    print(f"\n--- 3. Počítám přímý odtok (Q) pro srážku {cfg.rainfall_mm} mm ---")
    P = cfg.rainfall_mm
    
    # Matematický model: Výpočet počáteční ztráty (Ia).
    # Podle standardní metodiky představuje počáteční ztráta (intercepce, povrchové deprese,
    # počáteční vsak) přibližně 20 % potenciální maximální retence.
    gdf['Ia_mm'] = 0.2 * gdf['S_mm']
    
    # Matematický model: Výpočet přímého povrchového odtoku (Q).
    # Použita je funkce np.where pro implementaci hydrologické podmínky:
    # Odtok vzniká POUZE tehdy, pokud je srážka (P) větší než počáteční ztráta (Ia).
    # V opačném případě (srážka se celá vsákne nebo zachytí) je odtok roven 0.
    gdf['Q_mm'] = np.where(P > gdf['Ia_mm'], 
                           ((P - gdf['Ia_mm'])**2) / (P + 0.8 * gdf['S_mm']), 
                           0)
    
    # Zaokrouhlení výsledných hodnot na 1 desetinné místo pro přehlednost a realistickou přesnost
    gdf['S_mm'] = gdf['S_mm'].round(1)
    gdf['Ia_mm'] = gdf['Ia_mm'].round(1)
    gdf['Q_mm'] = gdf['Q_mm'].round(1)

    print("\nUkázka finálních výsledků (v mm):")
    # Zobrazení prvních 7 záznamů pro rychlou vizuální validaci modelu v terminálu
    print(gdf[['BPEJ_KOD', 'Code_18', 'CN', 'S_mm', 'Q_mm']].head(7))

    print("\n--- 4. Ukládám kompletní mapu ---")
    # Export vypočtených hodnot zpět do prostorového formátu GeoPackage.
    # Tento soubor slouží jako primární vstup pro QGIS (tvorba map) a statistický modul.
    gdf.to_file(output_path, driver="GPKG")
    print(f" HOTOVO! Mapa s retencí a odtokem je uložena.")

if __name__ == "__main__":
    vypocet_retence()