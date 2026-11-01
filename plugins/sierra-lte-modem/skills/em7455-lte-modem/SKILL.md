---
name: em7455-lte-modem
description: Einrichtung, Diagnose und Entsperrung eines Sierra Wireless EM7455 (auch MC7455, EM7430) LTE-Modems im USB-Gehäuse oder M.2-Slot unter Windows 11 und Linux, mit Telekom-SIM oder anderem Anbieter. Nutze diesen Skill immer, wenn ein 4G/LTE/WWAN/Mobilfunk-Modem von Sierra Wireless eingerichtet werden soll, keine Verbindung bekommt, 0 % Signal zeigt, "Software-Funkstatus Aus" meldet, im Low Power Mode hängt (BIOS:1, FCC-Auth), als USB-ID 1199:9078 im Bootmodus feststeckt, nur unter einem Betriebssystem läuft, zu langsam ist oder mehr Leistung bringen soll (Band wechseln, Bandsperre, Carrier-Aggregation, Durchsatz messen, Antennen), oder wenn nach APN, MBIM vs. QMI, AT-Befehlen (AT!PCINFO, AT!USBCOMP, AT!OPENLOCK, AT!BAND), ModemManager, qmicli, netsh mbn oder Lenovo-Whitelist gefragt wird, auch ohne dass der Nutzer das Wort "Skill" oder die Modellnummer nennt.
---

# Sierra EM7455 LTE-Modem unter Windows und Linux

Dieser Skill fasst eine erprobte Einrichtung zusammen: EM7455 mit Lenovo-Identität in einem
USB-M.2-Gehäuse, Telekom-SIM, Ziel: dasselbe Modul läuft ohne Umschalten unter Windows 11 und Linux.
Die Reihenfolge unten ist die Reihenfolge, in der Probleme tatsächlich auftreten. Arbeite sie von
oben nach unten ab und springe nicht voraus, weil jede Stufe die nächste voraussetzt.

## Zielzustand

| Eigenschaft | Sollwert | Warum |
|---|---|---|
| USB-Konfiguration | MBIM (`AT!USBCOMP` Bitmaske `1009` oder `100D`) | MBIM ist USB-Standard: Windows 11 bindet den eingebauten Treiber, Linux cdc_mbim + ModemManager. QMI läuft nur unter Linux. |
| Firmware | SWI9X30C_02.33.03.00 mit GENERIC-Carrier-PRI | Letzte Version, Telekom braucht keine eigene Carrier-PRI. |
| FCC-Auth | `AT!PCFCCAUTH?` alle drei Werte 0 | Sonst wartet das Modul bei jedem Start auf einen Host-Handshake, den nur Lenovos Windows-Treiber oder ein ModemManager-Skript liefern. |
| APN Telekom | `internet.telekom`, Benutzer `telekom`, Passwort `tm`, IPv4v6 | Windows legt den Kontext meist selbst an, Linux nicht. |

## Diagnose in fünf Stufen

Jede Stufe hat ein eindeutiges Symptom. Prüfe das Symptom, bevor du etwas änderst.

### Stufe 1: Wie meldet sich das Modul am USB?

- **1199:9079** (Lenovo-Identität) oder **1199:9071** (generisch): Normalbetrieb, weiter mit Stufe 2.
- **1199:9078** oder **1199:9070**: Bootloader (QDL). Das Modul zeigt dann nur eine herstellerspezifische
  Schnittstelle und Windows meldet Fehlercode 28. Oft springt es alle 10 Sekunden zwischen
  "vorhanden" und "weg". Erst anderen USB-Port oder aktiven Hub probieren, denn die Module ziehen beim
  Start über 1 A. Bleibt es im Bootmodus: Firmware unter Linux neu flashen, siehe `references/linux.md`,
  Abschnitt "Bootmodus".
- Windows: `Get-PnpDevice -PresentOnly | Where-Object InstanceId -like 'USB\VID_1199*'`
- Linux: `lsusb | grep 1199`

### Stufe 2: Hat das Betriebssystem einen Treiber gebunden?

- Windows: Schnittstelle MI_0C (Klasse 02/0E) muss den Treiber `netwmbclass.inf` / Dienst `cxwmbclass`
  haben. Dann existiert eine Mobilfunk-Schnittstelle in `netsh mbn show interfaces`. DM-Port (MI_00) und
  AT-Port (MI_03) bekommen Sierra-Treiber über Windows Update, der AT-Port erscheint als "WWAN Modem (COMx)".
- Linux: `mmcli -L` zeigt das Modem, `/dev/cdc-wdm0` und `/dev/ttyUSB0..2` existieren.
- Fehlt der MBIM-Treiber, prüfe `AT!USBCOMP?` über den AT-Port. Steht dort QMI statt MBIM, setze
  `AT!USBCOMP=1,1,0000100D` und `AT!RESET`.

### Stufe 3: Ist die SIM lesbar?

- Windows: `netsh mbn show readyinfo interface="Mobilfunk"` muss "Bereit" zeigen und den Heimanbieter nennen.
- AT: `AT+CPIN?` muss `READY` liefern.
- PIN-Abfrage auf der SIM besser abschalten (am Handy), dann gibt es auf keinem System Nachfragen.

### Stufe 4: Ist der Funk an? Hier hängt es fast immer.

Symptom: Windows meldet "Hardware-Funkstatus Ein, Client fordert Ein, Aktueller Software-Funkstatus Aus",
Signal 0 %, kein Anbietername. Linux: ModemManager-Status `disabled` oder `locked`, `mmcli -m 0`
zeigt `power state: low`.

Ursache lesen, nicht raten:

```
AT!ENTERCND="A710"
AT!PCINFO?
```

Die Zeile `LPM voters` nennt den Grund:

| Voter | Bedeutung | Abhilfe |
|---|---|---|
| `BIOS:1` | FCC-Auth-Sperre der OEM-Firmware (Lenovo, Dell, HP) | Dauerhaft: `references/at-befehle.md`, Abschnitt "FCC-Auth abschalten". Pro Boot: Lenovo-Treiber (Windows) oder ModemManager fcc-unlock (Linux). |
| `W_DISABLE:1` | Flugmodus-Pin des Slots aktiv | `AT!PCOFFEN=2` + `AT!RESET`, oder Flugmodus im Host aus. |
| `Temp:1` / `Volt:1` | Hardware | Kühlung, Stromversorgung, anderes Gehäuse. |
| `User:1` | Per Software abgeschaltet | `AT+CFUN=1` oder Funk im Betriebssystem einschalten. |
| `IMSWITCH:1` | Firmware-Image-Wechsel läuft | Warten, dann `AT!IMPREF?` prüfen. |

Wichtig: Die PRI-Kennung (`AT!PRIID`) auf "Generic-Laptop" zu setzen ändert nur ein Etikett und
löscht die FCC-Sperre nicht. Das haben wir ausprobiert. Die Sperre sitzt als NV-Wert und wird nur über
den Engineering-Modus (`AT!OPENLOCK` mit berechneter Antwort) und `AT!PCFCCAUTH=0` entfernt.
Das Skript `scripts/fcc-unlock.ps1` (Windows) bzw. `scripts/fcc-unlock.py` (beide Systeme) macht das
komplett. Der dafür nötige Keygen `scripts/sierrakeygen.py` liegt bei (bkerler/edl, GPLv3, siehe
`scripts/NOTICE.md`). Da es fremder Code ist, lass den Nutzer den Aufruf selbst starten oder
bestätigen; in Claude Code geht das mit dem `!`-Präfix vor dem Befehl.

### Stufe 5: Verbindung und Datenweg

- Windows verbindet nach dem Funk-Einschalten meist von selbst über den vorhandenen Kontext.
  Prüfen: `netsh mbn show connection interface="Mobilfunk"` (Registrierung "Startseite", APN),
  `Get-NetIPAddress -InterfaceIndex <ifIndex der Mobilfunk-Schnittstelle>`, dann
  `ping -S <IPv4 der Schnittstelle> 1.1.1.1`, weil die Standardroute sonst über WLAN geht.
- Linux: `nmcli connection add type gsm ifname "*" con-name Telekom apn internet.telekom user telekom password tm`
  und `nmcli connection up Telekom`.
- Telekom-APN bei alten Verträgen: `internet.t-mobile` mit `t-mobile` / `tm`.

## Was dieser Skill nicht tut

- Keine Firmware auf Windows flashen. Sierra liefert dafür nur noch Pakete über OEMs; Linux mit
  `qmi-firmware-update` ist der zuverlässige Weg, siehe `references/linux.md`.
- Keine Band-Sperren setzen, solange die Grundeinrichtung nicht steht. Danach lohnt es sich fast
  immer: `references/leistung.md` beschreibt die Band-Messung, die Sperre und die Durchsatzmessung.
  Beim erprobten Modul brachte der Wechsel von Band 8 auf Band 3 + 20 das Fünffache.

## Referenzen

- `references/windows.md`: Windows-11-Befehle für PnP, netsh mbn, AT-Port per PowerShell, Aufräumen verwaister Adapter.
- `references/linux.md`: ModemManager, qmicli, NetworkManager, Firmware-Flash im QDL-Modus, FCC-Unlock pro Boot.
- `references/at-befehle.md`: Alle genutzten AT-Befehle mit erwarteten Antworten, FCC-Auth abschalten und wieder einschalten, Identität zurücksetzen.
- `references/leistung.md`: Wenn es läuft, aber langsam ist. Bänder einzeln testen, auf das beste Band
  mit Carrier-Aggregation festlegen, Durchsatz an die Mobilfunk-Schnittstelle gebunden messen, Antennen.
- `scripts/fcc-unlock.ps1`, `scripts/fcc-unlock.py`, `scripts/keygen_wrap.py`: Freischaltsequenz.
- `scripts/sierrakeygen.py`: Challenge-Response-Generator von B. Kerler, GPLv3 (`scripts/NOTICE.md`,
  `scripts/LICENSE.sierrakeygen.txt`). Aufruf immer mit `--keygen` auf diese Datei.

Beispielaufruf unter Windows (Port anpassen, siehe `references/windows.md`):

```
powershell -ExecutionPolicy Bypass -File <skill>\scripts\fcc-unlock.ps1 -Port COM7 -Keygen <skill>\scripts\sierrakeygen.py
```

Unter Linux:

```
sudo systemctl stop ModemManager
python3 <skill>/scripts/fcc-unlock.py --port /dev/ttyUSB2 --keygen <skill>/scripts/sierrakeygen.py --set 0
sudo systemctl start ModemManager
```

## Erprobter Ablauf vom 1. November 2026

ThinkPad E16 Gen 2, EM7455 Lenovo-Identität im USB-Gehäuse, Telekom-SIM. Das Modul hing zuerst im
Bootmodus (9078) und kam nach Umstecken von selbst in den Normalmodus. Windows band den MBIM-Treiber,
Windows Update lieferte DM- und AT-Port-Treiber (COM7). SIM und APN waren sofort da, der Funk blieb
aus: `BIOS:1`. Nach `AT!OPENLOCK` (Antwort vom Keygen, Generation MDM9x30) und `AT!PCFCCAUTH=0` plus
`AT!RESET` war das Modul innerhalb von 30 Sekunden auf Telekom LTE Band 20 eingebucht, Windows
verband sich selbst, Ping über die Mobilfunk-Schnittstelle lief.
