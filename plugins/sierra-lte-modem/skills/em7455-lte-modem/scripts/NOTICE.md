# Drittanbieter-Code in diesem Skill

## sierrakeygen.py

- Quelle: https://github.com/bkerler/edl (Datei `edlclient/Tools/sierrakeygen.py`), Stand Februar 2026, unverändert übernommen.
- Autor: Bjoern Kerler, (c) 2019-2024.
- Lizenz: GNU General Public License v3, Volltext in `LICENSE.sierrakeygen.txt`.
- Hinweis des Autors im Dateikopf und in seiner README: Wer den Code in kommerzielle Produkte einbaut,
  stellt damit das Produkt unter GPLv3 und muss es offenlegen; eine kommerzielle Nutzung ohne vorherige
  Zustimmung des Autors ist nicht gestattet. Dieser Skill nutzt den Code nur zur Berechnung der
  AT!OPENLOCK-Antwort für eigene Modems.

Die übrigen Dateien in diesem Ordner (`keygen_wrap.py`, `fcc-unlock.py`, `fcc-unlock.ps1`) sind eigene
Hilfsskripte des Skills. `keygen_wrap.py` lädt aus sierrakeygen.py nur die Klasse `SierraGenerator`;
die Abhängigkeiten pyserial, Exscript und colorama, die das Original für seine Telnet- und
Automatik-Modi braucht, werden dafür nicht benötigt.
