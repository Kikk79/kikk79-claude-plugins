# AT-Befehle der EM7455 mit erwarteten Antworten

AT-Port: Windows "WWAN Modem (COMx)", Linux /dev/ttyUSB2. 115200 Baud. Befehle in Großbuchstaben.
`AT!ENTERCND="A710"` schaltet die erweiterten Befehle frei und ist nach jedem Reset neu nötig.

## Identität und Firmware

```
ATI
  Model: EM7455
  Revision: SWI9X30C_02.33.03.00 r8209 CARMD-EV-FRMWR2 2019/08/28
  IMEI, FSN (Seriennummer beginnt mit LF)

AT!USBVID?       1199
AT!USBPID?       APP : 9079   BOOT: 9078       (Lenovo-Identität; generisch 9071 / 9070)
AT!USBPRODUCT?   Sierra Wireless EM7455 Qualcomm Snapdragon X7 LTE-A

AT!PRIID?
  PRI Part Number: 9905228 / Revision: 001.004 / Customer: Lenovo-Tablet     (Lenovo-OEM-PRI)
  Carrier PRI: 9999999_9904609_SWI9X30C_02.33.03.00_00_GENERIC_002.072_000

AT!IMPREF?       preferred/current carrier name GENERIC, config GENERIC_002.072_000
AT!IMAGE?        FW-Slots 1..4 und PRI-Images, aktiver Slot
```

## USB-Konfiguration

```
AT!USBCOMP?
  Config Index: 1  Config Type: 1 (Generic)  Interface bitmask: 00001009 (diag,modem,mbim)

AT!USBCOMP=1,1,0000100D     diag, nmea, modem, mbim  (Standard für Windows + Linux)
AT!USBCOMP=1,1,00000D0B     ... mit QMI statt MBIM (nur Linux)
AT!RESET
```

Bitmaske: 1 = DM/diag, 2 = NMEA (0x04 in der Maske), 8 = AT/modem, 0x100 = QMI/RMNET, 0x1000 = MBIM.

## Energiezustand und Sperre

```
AT!PCINFO?
  State: Low Power Mode
  LPM voters - Temp:0, Volt:0, User:0, W_DISABLE:0, IMSWITCH:0, BIOS:1, LWM2M:0, OMADM:0, FOTA:0
  LPM persistence - None

AT+CFUN?         +CFUN: 0  (LPM)  /  +CFUN: 1 (online)
AT+CFUN=1        bei BIOS:1 -> +CME ERROR: operation not supported   (Sperre, kein Fehler des Hosts)

AT!PCFCCAUTH?
  NV Setting: 1 / FCC Auth Enabled: 1 / FCC Lock State: 1     gesperrt
  NV Setting: 0 / FCC Auth Enabled: 0 / FCC Lock State: 0     frei (nach Reset)

AT!PCOFFEN?      0 = W_DISABLE-Pin wird beachtet, 2 = ignorieren
AT!PCTEMP?       Temperatur und Temp-Zustand
```

## FCC-Auth abschalten (dauerhaft)

`AT!PCFCCAUTH=0` wird mit ERROR abgelehnt, solange der Engineering-Modus nicht offen ist. Der
Engineering-Modus öffnet sich per Challenge-Response; das Passwort A710 reicht dafür nicht.

```
AT!ENTERCND="A710"
AT!OPENLOCK?                 -> 16 Hex-Zeichen, bei jeder Abfrage neu
   Antwort berechnen: python -I scripts/keygen_wrap.py scripts/sierrakeygen.py <Challenge> MDM9x30
   (oder das Original: python sierrakeygen.py -l <Challenge> -d MDM9x30, braucht pyserial, Exscript, colorama)
AT!OPENLOCK="<Antwort>"      -> OK   (ERROR = falsche Antwort oder falsche Generation, kein Schaden)
AT!PCFCCAUTH=0               -> OK
AT!PCFCCAUTH?                -> NV Setting: 0, die anderen beiden noch 1 (werden erst beim Boot gelesen)
AT!RESET
   nach 30 s:
AT!ENTERCND="A710"
AT!PCFCCAUTH?                -> 0 / 0 / 0
AT!PCINFO?                   -> State: Online, BIOS:0
AT+COPS?                     -> +COPS: 0,0,"Telekom.de",7     (7 = LTE)
```

Generationen für den Keygen: EM7455/MC7455/EM7430 = MDM9x30, EM7565/EM7511 = MDM9x50,
EM7355/MC7355/EM7305 = MDM9x15. `AT!OPENMEP?` und `AT!OPENCND?` sind andere Sperren, nicht nötig.

Wieder einschalten: gleiche Sequenz mit `AT!PCFCCAUTH=1`.

Belegt durch den Sierra-Forum-Thread "EM7455, Deactivate Low-Power-Mode" (Beitrag 22, Nov 2021)
und durch unseren eigenen Durchlauf am 1. November 2026 mit Firmware 02.33.03.00.

## Netz und Signal

```
AT!GSTATUS?
  Mode: ONLINE / System mode: LTE / PS state: Attached / LTE band: B20 / EMM state: Registered
  RSRP (dBm): -89 / RSRQ: -10.9 / SINR: 7.6

AT+COPS?         +COPS: 0,0,"Telekom.de",7
AT+CPIN?         +CPIN: READY
AT!LTEINFO?      Nachbarzellen
AT!SELRAT?       00 Automatisch, 06 nur LTE
AT!BAND?         00 All bands
```

## Identität ändern (nur wenn nötig)

Lenovo-Identität behalten ist unter Windows praktisch, weil Windows Update dafür die Sierra-Port-
Treiber liefert. Generische Identität (aus dem Repo danielewood/sierra-wireless-modems):

```
AT!USBVID=1199
AT!USBPID=9071,9070
AT!USBPRODUCT="EM7455"
AT!PRIID="9904609","002.026","Generic-Laptop"
AT!RESET
```

Zurück zu Lenovo:

```
AT!USBPID=9079,9078
AT!USBPRODUCT="Sierra Wireless EM7455 Qualcomm Snapdragon X7 LTE-A"
AT!PRIID="9905228","001.004","Lenovo-Tablet"
AT!RESET
```

Hinweis aus der Praxis: `AT!PRIID` allein hebt die FCC-Sperre nicht auf. Es ist nur ein Etikett.

## Werkszustand

```
AT!RMARESET=1    Lenovo/Sierra-Werkseinstellungen (setzt auch PCFCCAUTH zurück!)
AT!NVRESTORE=0   Dell-Variante
AT!BOOTHOLD      in den Bootmodus (QDL) für Firmware-Flash
```
