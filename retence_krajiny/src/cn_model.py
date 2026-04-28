"""
Implementace hydrologického modelu Curve Number (SCS-CN).

Tento modul slouží k výpočtu čísel odtokových křivek (CN) pro zájmové území.
Hodnoty CN jsou stanovovány na základě prostorového průniku dvou vrstev:
1. Využití území (na základě klasifikace CORINE Land Cover)
2. Hydrologické vlastnosti půdy (odvozené z kódů BPEJ)

Výstupem je přiřazení CN hodnoty (0-100) každému polygonu v území.
"""
from typing import Dict, Tuple

# Klasifikace hydrologických skupin půd (HSP) podle propustnosti a infiltrační kapacity.
# Rozdělení odpovídá standardní metodice SCS (A = nejvyšší infiltrace, D = nejnižší).
SOIL_HYDROLOGIC_GROUPS: Dict[str, str] = {
    "A": "Vysoká infiltrace - písky, hlinité písky nebo štěrky; hluboké, dobře odvodněné půdy",
    "B": "Střední infiltrace - středně hluboké a středně dobře odvodněné půdy se středně jemnou texturou",
    "C": "Nízká infiltrace - půdy s jemnou texturou (jílovitohlinité), pomalá infiltrace",
    "D": "Velmi nízká infiltrace - těžké jílovité půdy, vysoká hladina podzemní vody nebo mělké půdy na nepropustném podloží",
}

# Klíčová převodní tabulka pro metodu SCS-CN. 
# Přiřazuje bezrozměrnou hodnotu odtokové křivky (CN) na základě kombinace typu krajiny (CORINE kód) a hydrologické skupiny půdy (A-D).
# Hodnoty vycházejí z tabulkových norem pro výpočet povrchového odtoku.
CN_LOOKUP: Dict[Tuple[int, str], int] = {
    # Lesy a zalesněné plochy (CORINE 311, 312, 313) - vykazují nejvyšší retenční schopnost
    (311, 'A'): 30, (311, 'B'): 55, (311, 'C'): 70, (311, 'D'): 77,
    (312, 'A'): 30, (312, 'B'): 55, (312, 'C'): 70, (312, 'D'): 77,
    (313, 'A'): 30, (313, 'B'): 55, (313, 'C'): 70, (313, 'D'): 77,

    # Louky a pastviny (CORINE 231) a městská zeleň (CORINE 141)
    (231, 'A'): 39, (231, 'B'): 61, (231, 'C'): 74, (231, 'D'): 80,
    (141, 'A'): 39, (141, 'B'): 61, (141, 'C'): 74, (141, 'D'): 80,

    # Orná půda (CORINE 211) - vyšší odtok kvůli orbě a absenci trvalého pokryvu
    (211, 'A'): 67, (211, 'B'): 78, (211, 'C'): 85, (211, 'D'): 89,

    # Pestré zemědělské oblasti a přirozená vegetace (CORINE 242, 243)
    (242, 'A'): 59, (242, 'B'): 74, (242, 'C'): 82, (242, 'D'): 86,
    (243, 'A'): 51, (243, 'B'): 68, (243, 'C'): 79, (243, 'D'): 84,

    # Křoviny a stromy v přechodu (CORINE 324)
    (324, 'A'): 35, (324, 'B'): 56, (324, 'C'): 70, (324, 'D'): 77,

    # Zástavba a antropogenní plochy (CORINE 111, 112) - vysoký podíl zpevněných, nepropustných ploch
    (111, 'A'): 90, (111, 'B'): 92, (111, 'C'): 94, (111, 'D'): 98,
    (112, 'A'): 77, (112, 'B'): 85, (112, 'C'): 90, (112, 'D'): 92,
    
    # Průmyslové a obchodní areály (CORINE 121)
    (121, 'A'): 81, (121, 'B'): 88, (121, 'C'): 91, (121, 'D'): 93,
    
    # Zcela nepropustné plochy (Silnice, železnice 122 a Letiště 124) - extrémně vysoký odtok blížící se 100 %
    (122, 'A'): 98, (122, 'B'): 98, (122, 'C'): 98, (122, 'D'): 98,
    (124, 'A'): 98, (124, 'B'): 98, (124, 'C'): 98, (124, 'D'): 98,
    
    # Skládky, staveniště a těžba nerostných surovin (CORINE 131, 132, 133) - udusaná/obnažená půda
    (131, 'A'): 77, (131, 'B'): 86, (131, 'C'): 91, (131, 'D'): 94,
    (132, 'A'): 77, (132, 'B'): 86, (132, 'C'): 91, (132, 'D'): 94,
    (133, 'A'): 77, (133, 'B'): 86, (133, 'C'): 91, (133, 'D'): 94,
    
    # Mokřady a vodní plochy (CORINE 411, 512) - saturované plochy, kde je retence nulová (srážka rovnou odtéká)
    (411, 'A'): 98,  (411, 'B'): 98,  (411, 'C'): 98,  (411, 'D'): 98,
    (512, 'A'): 100, (512, 'B'): 100, (512, 'C'): 100, (512, 'D'): 100,
}

def compute_cn(land_cover_code: int, soil_group: str) -> int:
    """
    Funkce pro vyhledání hodnoty CN z převodní tabulky.

    Args:
        land_cover_code: Celočíselný kód využití území z databáze CORINE.
        soil_group: Hydrologická skupina půdy ('A', 'B', 'C', nebo 'D').

    Returns:
        Hodnota CN (0-100) pro výpočet odtoku.
    """
    sg = soil_group.upper()
    key = (land_cover_code, sg)
    try:
        return CN_LOOKUP[key]
    except KeyError:
        # Bezpečnostní pojistka, pokud by prostorový průnik vygeneroval kód CORINE, který není v modelu definován.
        available_land_covers = sorted({k[0] for k in CN_LOOKUP.keys()})
        available_soil_groups = sorted({k[1] for k in CN_LOOKUP.keys()})
        raise ValueError(
            f"Pro kombinaci (CORINE={land_cover_code!r}, HSP={soil_group!r}) nebyla nalezena hodnota CN. "
            f"Dostupné kódy krajiny: {available_land_covers}. "
        )

# Zjednodušený model rozdělení HPJ (používáno primárně pro testovací účely)
BPEJ_HPJ_TO_SOIL_GROUP = {
    1: "A", 2: "A", 3: "A",       # Lehké a písčité půdy
    4: "B", 5: "B", 6: "B",       # Hlinité půdy
    7: "C", 8: "C", 9: "C",       # Jílovité půdy
    10: "D", 11: "D", 12: "D",    # Těžké a podmáčené půdy
}

# Detailní a metodicky přesné mapování Hlavních půdních jednotek (HPJ 01-78) do hydrologických skupin půd (HSP A-D).
# Toto rozdělení plně respektuje oficiální českou metodiku ochrany zemědělské půdy před vodní erozí (Janeček a kol.).
HPJ_TO_HSP = {
    # Skupina A (vysoká infiltrace: písky, štěrky, litozemě)
    **{hpj: "A" for hpj in [17, 18, 20, 21, 22, 23, 29, 31, 39, 41, 56]},

    # Skupina B (střední infiltrace: hnědozemě, černozemě, typické kvalitní zemědělské půdy)
    **{hpj: "B" for hpj in [1, 2, 3, 4, 5, 6, 9, 10, 11, 14, 15, 16, 24, 25, 26, 27, 28, 30, 32, 33, 34, 35, 36, 37, 38, 40, 43, 44, 55, 57, 58, 60, 61]},

    # Skupina C (nízká infiltrace: jílovitohlinité půdy, méně propustné pseudogleje)
    **{hpj: "C" for hpj in [7, 8, 12, 13, 19, 42, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 59, 62, 63]},

    # Skupina D (velmi nízká infiltrace: těžké jíly, gleje, silně zamokřené rašeliny)
    **{hpj: "D" for hpj in [64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78]}
}

def bpej_to_soil_group(bpej_code: int) -> str:
    """
    Algoritmus pro extrakci hydrologické skupiny z pětimístného kódu BPEJ.
    Kód BPEJ je strukturován tak, že 2. a 3. číslice udávají Hlavní půdní jednotku (HPJ), 
    která je klíčová pro určení infiltračních vlastností půdy.

    Args:
        bpej_code: Pětimístný kód BPEJ získávaný z GIS vrstvy SPÚ (např. 21501).

    Returns:
        Hydrologická skupina půdy (HSP) jako znak 'A', 'B', 'C', nebo 'D'.
    """
    bpej_string = str(bpej_code)

    # Ošetření nekonzistencí ve zdrojových GIS datech.
    # Pokud je kód načten jako integer, počáteční nuly (např. u kódu 01501) jsou smazány.
    # Tento blok zajistí doplnění úvodní nuly pro správnou extrakci pozic.
    if len(bpej_string) != 5:
        bpej_string = bpej_string.zfill(5)
        if len(bpej_string) != 5:
            raise ValueError(f"Datová anomálie: Kód BPEJ {bpej_code} nemá platný formát (očekáváno 5 číslic).")

    # Extrakce Hlavní půdní jednotky (HPJ) z pozice 2 a 3 (indexy 1 a 2 v textovém řetězci)
    hpj = int(bpej_string[1:3])

    # Vyhledání příslušné hydrologické skupiny v metodické tabulce
    if hpj not in HPJ_TO_HSP:
        raise ValueError(f"Pro BPEJ kód {bpej_code} byla identifikována neznámá Hlavní půdní jednotka (HPJ: {hpj}).")

    return HPJ_TO_HSP[hpj]