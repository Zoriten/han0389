"""
Modul pro vizualizaci, statistické vyhodnocení a export výsledků.

Tento skript zpracovává finální výstup z hydrologického modelu (výpočet odtoku).
Zajišťuje:
1. Kategorizaci a mapování numerických kódů land coveru na textové štítky pro lepší čitelnost.
2. Agregaci prostorových dat a výpočet plošných statistik zájmového území.
3. Export výsledků do strukturovaných formátů (Excel/CSV) pro další analýzu v tabulkových procesorech.
4. Tvorbu prezentační grafiky (sloupcových grafů) ve vysokém rozlišení pro přímé použití v textu práce.
"""
import sys
from pathlib import Path
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd

# Zajištění přístupu ke kořenovému adresáři projektu a konfiguraci
root_path = Path(__file__).resolve().parent.parent
sys.path.append(str(root_path))

from config import load_default_config

def create_graphs_and_statistics(cfg):
    
    # Definice vstupních a výstupních cest
    gpkg_name = getattr(cfg, 'nazev_souboru', 'retence_vysledek') + ".gpkg"
    input_path = cfg.data_results_dir / gpkg_name
    
    print("--- 1. Načítám data pro vizualizaci ---")
    gdf = gpd.read_file(input_path)
    
    # Přepočet rozlohy. V S-JTSK je jednotkou 1 m^2.
    # Dělením konstantou 10000 získáme standardní zemědělskou míru - hektary (ha).
    gdf['Plocha_ha'] = gdf.geometry.area / 10000
    
    # Klasifikační slovník pro překlad kódů CORINE na uživatelsky přívětivé názvy (třídy land coveru)
    corine_names = {
        "111": "Zástavba",
        "112": "Nesouvislá zástavba",
        "121": "Průmyslové zóny",
        "122": "Silnice a železnice",
        "124": "Letiště",
        "131": "Těžba nerostných surovin",
        "132": "Skládky",
        "133": "Staveniště",
        "141": "Městská zeleň",
        "211": "Orná půda",
        "231": "Louky a pastviny",
        "242": "Pestré zemědělství",
        "243": "Zemědělská + příroda",
        "311": "Lesy",
        "312": "Jehličnatý les",
        "313": "Smíšený les",
        "324": "Křoviny",
        "411": "Rašeliniště",
        "512": "Vodní plochy"
    }
    
    # Mapování kódů na text. Pojistka: pokud kód v CORINE neexistuje ve slovníku,
    # ponechá se alespoň jeho číselná hodnota ve formátu string.
    gdf['Vyuziti_text'] = gdf['Code_18'].map(corine_names).fillna(gdf['Code_18'].astype(str))
    
    print("\n--- 2. Počítám celkové statistiky ---")
    # Základní plošné vyhodnocení zájmového území
    total_area = gdf['Plocha_ha'].sum()
    
    # Rozčlenění území na plochy, které dokáží aktuální srážku plně retrahovat (Q=0), 
    # a plochy generující přímý odtok (Q>0).
    area_without_runoff = gdf[gdf['Q_mm'] == 0]['Plocha_ha'].sum()
    area_with_runoff = total_area - area_without_runoff
    
    print(f"Celková rozloha analyzovaného území: {total_area:.2f} ha")
    print(f"Plocha se 100% vsakem (Q = 0 mm):    {area_without_runoff:.2f} ha ({(area_without_runoff/total_area)*100:.1f} %)")
    print(f"Plocha s povrchovým odtokem (Q > 0): {area_with_runoff:.2f} ha ({(area_with_runoff/total_area)*100:.1f} %)")

    print("\n--- 3. Tabulka: Průměrný odtok podle využití krajiny ---")
    # Agregace a seskupení dat podle typu krajinného pokryvu pro stanovení průměrného chování
    # jednotlivých krajinných složek v rámci zkoumaného polygonu.
    statistika = gdf.groupby('Vyuziti_text').agg(
        Prumerny_odtok_mm=('Q_mm', 'mean'),
        Celkova_plocha_ha=('Plocha_ha', 'sum')
    ).reset_index()
    
    # Seřazení výsledků sestupně (od největších zdrojů odtoku po nejméně rizikové oblasti)
    statistika = statistika.sort_values(by='Prumerny_odtok_mm', ascending=False).round(2)
    print(statistika.to_string(index=False))
    
    print("\n--- 4. Export výsledků do Excelu ---")
    excel_name = getattr(cfg, 'nazev_souboru', 'retence_vysledek') + ".xlsx"
    excel_path = cfg.data_results_dir / excel_name
    
    try:
        # Konstrukce vícestránkového Excel sešitu pro komplexní reportování výsledků
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            
            # List 1: Základní hydrologická bilance území
            summary_data = {
                'Parametr': [
                    'Srážkový úhrn (mm)', 'Celková rozloha (ha)', 'Plocha bez odtoku (ha)',
                    'Plocha s odtokem (ha)', 'Podíl plochy bez odtoku (%)', 'Podíl plochy s odtokem (%)'
                ],
                'Hodnota': [
                    cfg.rainfall_mm, round(total_area, 2), round(area_without_runoff, 2),
                    round(area_with_runoff, 2), round((area_without_runoff/total_area)*100, 2),
                    round((area_with_runoff/total_area)*100, 2)
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Celkove_shrnuti', index=False)
            
            # List 2: Agregované výsledky dle tříd krajinného pokryvu
            statistika.to_excel(writer, sheet_name='Statistiky_krajiny', index=False)
            
            # List 3: Detailní datový rámec (raw data) pro případné ověření jednotlivých výpočtů polygonů
            raw_data = gdf[['BPEJ_KOD', 'Code_18', 'Vyuziti_text', 'CN', 'S_mm', 'Q_mm', 'Plocha_ha']].copy()
            raw_data['Plocha_ha'] = raw_data['Plocha_ha'].round(2)
            raw_data.to_excel(writer, sheet_name='Podrobna_data', index=False)
            
        print(f" Excel tabulka byla úspěšně uložena do: {excel_path}")
        
    except ModuleNotFoundError:
        # Krizový režim (fallback) pro případ chybějících knihoven
        print(" Chybí knihovna 'openpyxl' pro export do Excelu.")
        print("Zatím ukládám alespoň jako jednoduché CSV...")
        csv_path = cfg.data_results_dir / (getattr(cfg, 'nazev_souboru', 'retence_vysledek') + ".csv")
        statistika.to_csv(csv_path, index=False, sep=';', encoding='utf-8-sig')
        print(f" Data uložena jako CSV do: {csv_path}")

    print("\n--- 5. Vykresluji a ukládám graf ---")
    # Inicializace grafického plátna
    plt.figure(figsize=(10, 6))
    
    # Dynamická definice barevné škály: 
    # Hodnoty s průměrným odtokem > 2 mm jsou zvýrazněny varovnou barvou (červená),
    # nízký odtok (< 2 mm) standardní chladnou barvou (modrá).
    colors = ['#e74c3c' if x > 2 else '#3498db' for x in statistika['Prumerny_odtok_mm']]
    
    plt.bar(statistika['Vyuziti_text'], statistika['Prumerny_odtok_mm'], color=colors)
    title = getattr(cfg, 'nadpis_grafu', f"Průměrný povrchový odtok při srážce {cfg.rainfall_mm} mm")
    plt.title(title, fontsize=15, pad=15)
    plt.ylabel("Odtok (mm)", fontsize=12)
    plt.xlabel("Typ využití krajiny (CORINE)", fontsize=12)
    plt.xticks(rotation=30, ha='right', fontsize=11)
    
    # Přidání datových štítků přímo k jednotlivým sloupcům pro okamžitou čitelnost
    for i, hodnota in enumerate(statistika['Prumerny_odtok_mm']):
        plt.text(i, hodnota + 0.1, f"{hodnota} mm", ha='center', fontsize=10)

    # Kosmetické úpravy grafu (zajištění nerušivé mřížky a optimalizace rozložení)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()
    
    # Export grafiky v prezentační kvalitě (300 DPI - vhodné pro tisk)
    jmeno_png = getattr(cfg, 'nazev_souboru', 'graf_prumerny_odtok') + ".png"
    chart_path = cfg.data_results_dir / jmeno_png
    plt.savefig(chart_path, dpi=300)
    print(f" Graf ve vysokém rozlišení byl uložen do: {chart_path}")

if __name__ == "__main__":
    vypocet_retence()