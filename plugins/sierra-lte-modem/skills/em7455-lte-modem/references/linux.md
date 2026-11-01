# Linux: ModemManager, qmicli, Firmware, FCC-Unlock

Getestet gedanklich gegen Debian 12 / Ubuntu 22.04+ mit ModemManager 1.18+, libqmi 1.30+.
Pakete: `modemmanager libqmi-utils libmbim-utils network-manager`.

## Gerät erkennen

```bash
lsusb | grep -i 1199          # 1199:9079 oder 9071 = Normalbetrieb, 9078 / 9070 = Bootmodus (QDL)
mmcli -L                      # Modem gelistet?
mmcli -m 0                    # Status, power state, unlock, signal
ls /dev/cdc-wdm* /dev/ttyUSB* # cdc-wdm0 = MBIM/QMI, ttyUSB0 DM, ttyUSB1 NMEA, ttyUSB2 AT
```

Im MBIM-Modus bindet der Kernel cdc_mbim an die Netzschnittstelle (wwan0 / wwp0s...) und qcserial an
die seriellen Ports. Fehlt /dev/ttyUSB2, hat die USB-Konfiguration keinen AT-Port
(`AT!USBCOMP` Bitmaske ohne Bit 4). Dann über qmicli arbeiten, siehe unten.

## Low Power Mode erkennen

```bash
mmcli -m 0 | grep -iE 'power|state'
# power state: low  und  state: disabled/failed  =>  AT!PCINFO? auf /dev/ttyUSB2 ansehen
```

AT-Port ohne minicom:

```bash
sudo systemctl stop ModemManager      # sonst belegt MM den Port
sudo stty -F /dev/ttyUSB2 115200 raw -echo
( sleep 1; printf 'AT!ENTERCND="A710"\r'; sleep 1; printf 'AT!PCINFO?\r'; sleep 1 ) > /dev/ttyUSB2 &
timeout 4 cat /dev/ttyUSB2
sudo systemctl start ModemManager
```

Oder bequemer mit `python3 -m serial.tools.miniterm /dev/ttyUSB2 115200` (Paket python3-serial).

## FCC-Unlock pro Boot (wenn die Sperre im Modul bleiben soll)

ModemManager bringt das Skript mit, es ist nur nicht aktiviert:

```bash
sudo ln -s /usr/share/ModemManager/fcc-unlock.available.d/1199:9079 /etc/ModemManager/fcc-unlock.d/1199:9079
sudo systemctl restart ModemManager
```

Für generische Identität (1199:9071) gibt es kein vorgefertigtes Skript; dann einmalig:

```bash
sudo qmicli -d /dev/cdc-wdm0 --device-open-proxy --dms-set-fcc-authentication
```

Das funktioniert auch im MBIM-Modus (QMI über MBIM). Dauerhaft besser: Sperre im NV abschalten,
siehe `at-befehle.md`, dann ist weder Skript noch qmicli nötig.

## Dauerhafter FCC-Unlock unter Linux

`scripts/fcc-unlock.py` aus diesem Skill läuft auch unter Linux (pyserial, Port `/dev/ttyUSB2`).
ModemManager vorher stoppen, sonst ist der AT-Port belegt:

```bash
sudo systemctl stop ModemManager
pip install pyserial
python3 scripts/fcc-unlock.py --port /dev/ttyUSB2 --keygen scripts/sierrakeygen.py --set 0
sudo systemctl start ModemManager
```

## NetworkManager-Verbindung für Telekom

```bash
nmcli connection add type gsm ifname "*" con-name Telekom apn internet.telekom user telekom password tm
nmcli connection modify Telekom ipv6.method auto connection.autoconnect yes
nmcli connection up Telekom
mmcli -m 0 --signal-get
```

PIN auf der SIM: `nmcli connection modify Telekom gsm.pin 1234` oder PIN-Abfrage auf der SIM abschalten.

## USB-Konfiguration ohne AT-Port umstellen

```bash
sudo qmicli -d /dev/cdc-wdm0 --device-open-proxy --dms-swi-get-usb-composition
sudo qmicli -d /dev/cdc-wdm0 --device-open-proxy --dms-swi-set-usb-composition=6   # 6 = DM NMEA AT MBIM
sudo qmicli -d /dev/cdc-wdm0 --device-open-proxy --dms-set-operating-mode=reset
```

Konfiguration 6 ist die, die unter Windows und Linux gleichermaßen läuft. 8 (QMI) nur für reine Linux-Router.

## Bootmodus (1199:9078): Firmware neu flashen

Das ist der einzige Weg aus einem hängenden QDL-Modus und der Grund, warum man Linux für diese Module
braucht. Firmware kommt von source.sierrawireless.com (kostenloses Konto), Paket
`SWI9X30C_02.33.03.00_Generic_002.072_001` mit `.cwe` und `.nvu`.

```bash
sudo systemctl stop ModemManager
sudo apt install libqmi-utils
unzip SWI9X30C_02.33.03.00_Generic_*.zip
# Modul im Normalbetrieb:
sudo qmi-firmware-update --update -d 1199:9079 SWI9X30C_02.33.03.00.cwe SWI9X30C_02.33.03.00_GENERIC_002.072_001.nvu
# Modul hängt im Bootmodus:
sudo qmi-firmware-update --update-qdl -d 1199:9078 SWI9X30C_02.33.03.00.cwe SWI9X30C_02.33.03.00_GENERIC_002.072_001.nvu
```

Springt das Modul alle 10 Sekunden zwischen vorhanden und weg, bricht der Flash ab. Dann zuerst Port,
Kabel und Stromversorgung wechseln (aktiver USB-Hub, USB-2-Port statt USB-3). Das Skript
`autoflash-7455.sh` aus github.com/danielewood/sierra-wireless-modems macht Flash, generische
Identität und MBIM-Konfiguration in einem Durchgang, ist aber nur für USB-Gehäuse gedacht.

## Modul im internen M.2-Slot eines Lenovo-Laptops

Neuere ThinkPads prüfen im BIOS eine Whitelist. Umgehung (am USB-Gehäuse vorher setzen):

```
AT!ENTERCND="A710"
AT!CUSTOM="FASTENUMEN",2    Modul erst nach voller Initialisierung zeigen
AT!PCOFFEN=2                W_DISABLE-Pin ignorieren
AT!USBSPEED=0               USB 2 erzwingen
AT!RESET
```
