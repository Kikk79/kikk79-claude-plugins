# kikk79-plugins

Ein Claude-Code-Plugin-Marketplace. Hinzufügen und installieren:

```
claude plugin marketplace add Kikk79/kikk79-claude-plugins
claude plugin install sierra-lte-modem@kikk79-plugins
```

In einer laufenden Sitzung geht dasselbe mit `/plugin marketplace add Kikk79/kikk79-claude-plugins`
und `/plugin install sierra-lte-modem@kikk79-plugins`.

## Plugins

### sierra-lte-modem

Skill `em7455-lte-modem`: Einrichtung, Diagnose und dauerhafte FCC-Entsperrung eines Sierra Wireless
EM7455 (auch MC7455, EM7430) im USB-Gehäuse oder M.2-Slot, so dass dasselbe Modul ohne Umschalten
unter Windows 11 und Linux läuft. Mit Telekom-APN, aber auf andere Anbieter übertragbar.

Inhalt:

- Diagnose in fünf Stufen: USB-Identität (Bootmodus 1199:9078 erkennen), Treiber, SIM, Funkstatus
  (`AT!PCINFO?`-Voter lesen), Datenweg.
- `references/windows.md`: PnP, `netsh mbn`, APN-Profil, AT-Port aus PowerShell.
- `references/linux.md`: ModemManager, qmicli, NetworkManager, Firmware-Flash im QDL-Modus.
- `references/at-befehle.md`: alle AT-Befehle mit erwarteten Antworten.
- `scripts/`: Freischaltsequenz für Windows (PowerShell) und beide Systeme (Python), plus
  `sierrakeygen.py` von B. Kerler (GPLv3, siehe `scripts/NOTICE.md`).

Der Skill ist auf Deutsch geschrieben.

## Lizenz

GPL-3.0. Der enthaltene Challenge-Response-Generator `sierrakeygen.py` stammt aus
[bkerler/edl](https://github.com/bkerler/edl) und steht unter GPLv3 mit dem Hinweis des Autors, dass
eine kommerzielle Nutzung seine vorherige Zustimmung braucht. Alles Übrige in diesem Repository steht
ebenfalls unter GPL-3.0, siehe `LICENSE`.
