# 🌲 Nástroj pro odhad retenční schopnosti území (metoda SCS-CN)

Tento softwarový nástroj v jazyce Python byl vyvinut jako praktický výstup bakalářské práce. Slouží k automatizovanému výpočtu potenciální retence krajiny a odhadu povrchového odtoku na základě integrace otevřených prostorových dat.

[Image of a software data flow diagram]

## 🎯 Cíle projektu
* **Integrace heterogenních dat:** Spojení informací o hydrologických skupinách půd (BPEJ) a využití území (CORINE Land Cover).
* **Simulace scénářů:** Možnost testování odezvy krajiny na různou intenzitu srážek (např. 20 mm vs. 100 mm).
* **Analýza odtoku:** Identifikace kritických lokalit s nízkou retenční schopností v rámci zájmového území.

## 🚀 Instalace a prerekvizity

### 1. Hardwarové nároky
Vzhledem k práci s rozsáhlými soubory CORINE Land Cover (cca 8.5 GB) je doporučeno minimálně 8 GB RAM.

### 2. Softwarové závislosti
Nainstalujte potřebné knihovny pomocí přiloženého souboru `requirements.txt`:
```bash
pip install -r requirements.txt