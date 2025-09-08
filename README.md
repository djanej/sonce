Dobrodošli v repozitorij Spletne Strani Pisarne Sonce.

**⚠️ Lastnina in pravice:**
Vse vsebine, koda, dokumentacija in drugi materiali v tem repozitoriju so **last avtorjev/lastnikov repozitorija Sonce**.  
Kopiranje, distribuiranje ali uporaba brez dovoljenja lastnika ni dovoljena.  

© 2025 Sonce. Vse pravice pridržane.

---

Če imate vprašanja glede uporabe ali dovoljenj, nas kontaktirajte.

---

Enostavna navodila za novice (za ne-tehnične):

1) Ustvarite ZIP z generatorjem
- Odprite mapo `generator/` in zaženite `run_windows.bat` ali `run_mac_linux.sh`.
- Izpolnite naslov, datum (kliknite Today), po želji dodajte sliko, kliknite "Generate Draft", nato "Create ZIP" in "Copy ZIP to incoming…".

2) Dodajte ZIP v repozitorij
- Kopirajte ZIP v mapo `incoming/` v tem repozitoriju in izvedite commit + push na `main`.

3) Avtomatika uvozi datoteke
- GitHub Actions samodejno premakne vse v `content/news/` in `static/uploads/news/YYYY/MM/`.
- V `content/news/index.json` se seznam objav posodobi.
