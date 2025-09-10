Dobrodošli v repozitorij Spletne Strani Pisarne Sonce.

**⚠️ Lastnina in pravice:**
Vse vsebine, koda, dokumentacija in drugi materiali v tem repozitoriju so **last avtorjev/lastnikov repozitorija Sonce**.  
Kopiranje, distribuiranje ali uporaba brez dovoljenja lastnika ni dovoljena.  

© 2025 Sonce. Vse pravice pridržane.

---

Če imate vprašanja glede uporabe ali dovoljenj, nas kontaktirajte.

---

## 🛠️ Development Tools

**⚠️ Pomembno**: Mapa `generator/` vsebuje **razvojna orodja**, ne del spletne strani!

Ta mapa vsebuje orodja za ustvarjanje vsebine za spletno stran:
- **Python GUI generator** - namizna aplikacija
- **HTML web editor** - spletni urejevalnik

Za podrobnosti glejte `generator/README.md`.

---

## 📝 Enostavna navodila za novice (za ne-tehnične):

### Opcija 1: Python GUI Generator
1) Ustvarite ZIP z generatorjem
- Odprite mapo `generator/` in zaženite `run_windows.bat` ali `run_mac_linux.sh`.
- Izpolnite naslov, datum (kliknite Today), po želji dodajte sliko, kliknite "Generate Draft", nato "Create ZIP" in "Copy ZIP to incoming…".

2) Dodajte ZIP v repozitorij
- Kopirajte ZIP v mapo `incoming/` v tem repozitoriju in izvedite commit + push na `main`.

3) Avtomatika uvozi datoteke
- GitHub Actions samodejno premakne vse v `content/news/` in `static/uploads/news/YYYY/MM/`.
- V `content/news/index.json` se seznam objav posodobi.

### Opcija 2: HTML Web Editor
1) Odprite web editor
- Zaženite `generator/run_html_editor.sh` (Mac/Linux) ali `generator/run_html_editor.bat` (Windows)
- Uporabite "Connect Repo Folder" za direktno povezavo z repozitorijem

2) Ustvarite in shranite objavo
- Izpolnite obrazec in kliknite "Save to Repo"
- Datoteke se samodejno shranijo v pravilne mape
