"""
Modul pro akvizici a správu prostorových dat.
Tento skript validuje lokální data a pokouší se o automatické stažení 
indexových map (Klad listů). Pokud server poskytovatele neodpovídá (Chyba 404), 
modul poskytne uživateli alternativní metodický postup.
"""
import sys
import requests
import zipfile
from pathlib import Path

cesta_korenu = Path(__file__).resolve().parent.parent
sys.path.append(str(cesta_korenu))
from config import load_default_config

def ensure_dmr_index_data(cfg):
    """
    Pokusí se stáhnout klad listů. Pokud selže, navede uživatele.
    """
    # Aktuální URL pro Klad listů 1:5000 (S-JTSK)
    url = "https://geoportal.cuzk.cz/SDIFree/SM5/Klad_SM5_JTSK.zip"
    cil = cfg.data_raw_dir / "klad_listu_sm5.zip"

    print(f" Pokus o automatickou aktualizaci indexů z: {url}")
    
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            with open(cil, 'wb') as f:
                f.write(r.content)
            print(" Klad listů byl úspěšně aktualizován.")
        else:
            print(f" Server poskytovatele (ČÚZK) vrátil chybu {r.status_code}.")
            print(" METODICKÁ POZNÁMKA: Vzhledem k dynamickým změnám na státních geoportálech")
            print("   je doporučeno v případě výpadku stáhnout soubor manuálně.")
    except Exception as e:
        print(f" Spojení se serverem selhalo: {e}")

def vypis_zaverecny_status(cfg):
    print("\n" + "="*50)
    print(" FINÁLNÍ REVIZE DATOVÉHO SKLADU")
    print("="*50)
    
    soubory = {
        "BPEJ (Půda)": "ft_pudniJednotka.shp",
        "CORINE (Krajina)": "CLC18_CZ.shp",
        "Maska (Území)": "maska.gpkg"
    }
    
    vse_ok = True
    for label, file in soubory.items():
        exists = (cfg.data_raw_dir / file).exists()
        status = " PŘÍTOMNO" if exists else " CHYBÍ"
        if not exists: vse_ok = False
        print(f"{label:18}: {status}")
    
    print("="*50)
    if vse_ok:
        print(" SYSTÉM JE PŘIPRAVEN KE SPUŠTĚNÍ (python main.py)")
    else:
        print(" Před spuštěním main.py doplňte chybějící data do data/raw/")

if __name__ == "__main__":
    cfg = load_default_config()
    ensure_dmr_index_data(cfg)
    vypis_zaverecny_status(cfg)