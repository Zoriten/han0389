"""
Modul pro předzpracování prostorových dat (Geoprocessing).

Tento skript zajišťuje načtení, transformaci a prostorové spojení vstupních vektorových dat.
Provádí ořez národních datových sad (BPEJ a CORINE Land Cover) na základě vymezeného
zájmového území (masky) a sjednocuje jejich souřadnicové referenční systémy (CRS) do EPSG:5514.
Závěrečným krokem je prostorový průnik (intersection), který vytvoří homogenní vrstvu
kombinující pedologické a krajinné charakteristiky pro následný hydrologický model.
"""
import sys
from pathlib import Path
import geopandas as gpd

# Dynamické nastavení absolutních cest pro zajištění přenositelnosti kódu
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

def preprocess_data(cfg):
    
    # Definice cest ke zdrojovým datovým sadám. 
    # Využívají se optimalizované národní sady (např. oříznutá CZ verze CORINE) pro snížení výpočetní náročnosti.
    bpej_path = cfg.data_raw_dir / "ft_pudniJednotka.shp"
    corine_path = cfg.data_raw_dir / "CLC18_CZ.shp"
    mask_path = cfg.data_raw_dir / "maska.gpkg"
    output_path = cfg.data_processed_dir / "bpej_corine_prunik.gpkg"
    
    print("--- 1. Načítám masku ---")
    # Načtení polygonu definujícího zájmové území a validace jeho souřadnicového systému
    mask = gpd.read_file(mask_path)
    if mask.crs != f"EPSG:{cfg.crs_epsg}":
        mask = mask.to_crs(epsg=cfg.crs_epsg)

    print("\n--- 2. Načítám a ořezávám BPEJ data ---")
    # Optimalizované načítání: Parametr 'mask' zajistí, že se z velkoobjemové databáze
    # načtou do paměti pouze polygony protínající zájmové území.
    # Ošetření nekonzistencí CRS v otevřených datech SPÚ (často publikováno v EPSG:3857).
    mask_epsg3857 = mask.to_crs(epsg=3857)
    bpej = gpd.read_file(bpej_path, mask=mask_epsg3857)
    
    # Fallback mechanismus: Pokud jsou zdrojová data v nativním S-JTSK (EPSG:5514)
    if bpej.empty:
         bpej = gpd.read_file(bpej_path, mask=mask)
         
    # Reprojekce do cílového referenčního systému modelu
    bpej = bpej.to_crs(epsg=cfg.crs_epsg)
    print(f" BPEJ načteno! Dostupné sloupce: {bpej.columns.tolist()}")

    print("\n--- 3. Načítám a ořezávám CORINE (CZ verze) ---")
    # Načtení databáze krajinného pokryvu oříznuté maskou zájmového území
    corine = gpd.read_file(corine_path, mask=mask)
    
    # Sjednocení souřadnicového systému pro zajištění topologické přesnosti při průniku
    if corine.crs != f"EPSG:{cfg.crs_epsg}":
        corine = corine.to_crs(epsg=cfg.crs_epsg)
        
    # Standardizace názvosloví atributů (řešení rozdílů mezi evropskou a českou verzí CLC)
    if 'CODE_18' in corine.columns:
        corine = corine.rename(columns={'CODE_18': 'Code_18'})
        
    if 'Code_18' not in corine.columns:
        print(f" Varování: Nenašel jsem sloupec Code_18 v CORINE! Dostupné sloupce jsou: {corine.columns.tolist()}")

    print("\n--- 4. Provádím prostorový průnik ---")
    # Topologická operace intersection (průnik). Výsledkem jsou nové polygony nesoucí 
    # informace z obou podkladových vrstev (jak BPEJ, tak CORINE).
    intersection = gpd.overlay(bpej, corine, how='intersection')
    
    # Validace výsledku operace: Kontrola, zda v zájmovém území existují vstupní data
    if intersection.empty:
        raise ValueError(" Průnik je prázdný! Pro tuto oblast chybí zdrojová data, nebo je území mimo rozsah datových sad.")
    
    # Dynamická identifikace klíčového atributu s kódem BPEJ. 
    # Slouží jako ochrana proti změnám ve struktuře atributových tabulek od poskytovatelů dat.
    possible_columns = ['Kod_B5', 'Kod_BPEJ_t', 'BPEJ', 'bpej', 'KOD', 'kod']
    bpej_column = next((col for col in possible_columns if col in intersection.columns), None)
    
    if bpej_column is None:
        raise ValueError(f" Nenašel jsem sloupec BPEJ! Sloupce v datech jsou: {intersection.columns.tolist()}")
        
    # Filtrace redundantních atributů pro optimalizaci velikosti výstupního souboru
    intersection = intersection[[bpej_column, 'Code_18', 'geometry']]
    intersection = intersection.rename(columns={bpej_column: 'BPEJ_KOD'})
    
    print("\n--- 5. Ukládám výsledek ---")
    # Export do moderního formátu GeoPackage
    cfg.data_processed_dir.mkdir(parents=True, exist_ok=True)
    intersection.to_file(output_path, driver="GPKG")
    print(f" HOTOVO! Zpracovaná mapa uložena do: {output_path}")

if __name__ == "__main__":
    # Testovací volání modulu s výchozí konfigurací
    from config import load_default_config
    cfg = load_default_config()
    preprocess_data(cfg)