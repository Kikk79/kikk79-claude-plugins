# Leistung: Band-Messung, Bandsperre, Durchsatz, Antennen

Erst wenn Stufe 1 bis 5 aus SKILL.md stehen (Modul online, registriert, Datenweg läuft). Ein Modul, das
sich auf dem falschen Band einbucht, liefert einen Bruchteil dessen, was der Standort hergibt. Beispiel
vom 1. November 2026 (Telekom, Innenraum, USB-Gehäuse mit Stummelantennen):

| | Band 8 (automatisch gewählt) | Band 3 + 20 (gesperrt) |
|---|---|---|
| Bandbreite | 10 MHz | 20 MHz + 10 MHz Zweitträger |
| RSRP / SINR | -97 dBm / 4 dB | -82 dBm / 14,6 dB |
| Download, ein Strom | 13 Mbit/s | 67 Mbit/s |
| Download, vier Ströme | | 57 Mbit/s, CA aktiv |
| Upload | 10 Mbit/s | 25 Mbit/s |

## 1. Ausgangslage lesen

```
AT!ENTERCND="A710"
AT!GSTATUS?      LTE band, LTE bw, CA state, RSRP, RSRQ, SINR
AT!LTEINFO?      Serving-Zelle, Intra- und Inter-Frequenz-Nachbarn (nur die, die das Netz melden)
AT!LTECA?        welche Band-Kombinationen das Modul für Carrier-Aggregation kann
AT!BAND?         aktive Bandauswahl (00 = alle)
AT!SELRAT?       06 = nur LTE, sinnvoll, 3G ist in Deutschland abgeschaltet
```

Lesehilfe: RSRP über -90 dBm ist gut, unter -100 schwach. SINR über 10 dB gut, unter 3 dB
störungsbegrenzt. "CA state: INACTIVE" mit "Scell band" bedeutet: Zweitträger konfiguriert, die
Basisstation schaltet ihn erst unter Last zu. Ein niedriges Band (B8, B20) mit 10 MHz ist fast immer die
Reichweiten-, nicht die Kapazitätszelle.

Die Inter-Frequenz-Liste in `AT!LTEINFO?` ist oft leer. Das heißt nicht, dass es keine anderen Bänder
gibt, sondern nur, dass das Netz keine Messung angeordnet hat. Darum die Bänder einzeln testen.

## 2. Band-Messung durch zeitweise Sperren

Bänder in Deutschland: Telekom B3 (1800, Kapazität), B20 (800), B8 (900), B1 (2100), B7 (2600);
Vodafone B1, B3, B7, B8, B20; o2 B1, B3, B7, B8, B20, B28. Masken aus `AT!BAND=?`: B1 = 1, B3 = 4,
B7 = 40, B8 = 80, B20 = 80000, B28 = 8000000 (hex, addieren für Kombinationen).

Je Band: Sperre setzen, 25 Sekunden warten, Zustand lesen.

```
AT!BAND=10,"B3",0,0000000000000004
AT!BAND=10
   ... 25 s ...
AT!GSTATUS?
AT!LTEINFO?
```

Dasselbe für B1 (`...0001`), B7 (`...0040`), B20 (`...80000`), danach alle Kapazitätsbänder zusammen
(`...0045` = B1+B3+B7). Am Ende `AT!BAND=00`. Während der Messung reißt die Verbindung je Band kurz ab.
Als PowerShell-Schleife über den AT-Port (Funktion Q aus `windows.md`):

```powershell
foreach ($t in @(@('B3','0000000000000004'),@('B1','0000000000000001'),@('B7','0000000000000040'),@('B20','0000000000080000'))) {
  Q ('AT!BAND=10,"' + $t[0] + '",0,' + $t[1]) | Out-Null; Q 'AT!BAND=10' | Out-Null
  Start-Sleep -Seconds 25; "=== $($t[0])"; Q 'AT!GSTATUS?' 2500; Q 'AT!LTEINFO?' 2500
}
Q 'AT!BAND=00'
```

Bewerten: `EMM state: Deregistered` oder leeres Band = nicht empfangbar. In `AT!LTEINFO?` die Spalte
MNC prüfen: 262 01 Telekom, 262 02 Vodafone, 262 03 o2. Ein Band, das nur ein fremdes Netz zeigt, nützt
nichts. Gewinner ist das Band mit größter Bandbreite bei RSRP über etwa -95 und SINR über 5.

## 3. Bandsperre dauerhaft setzen

Gewinnerband plus das Band, mit dem es laut `AT!LTECA?` aggregieren darf (bei Telekom B3 + B20):

```
AT!BAND=10,"B3B20",0,0000000000080004
AT!BAND=10
AT!BAND?          -> 10, B3B20
```

Die Einstellung liegt im Modul, gilt also unter Windows und Linux gleich und überlebt Neustarts.
Ohne das Rückfallband (B8) verliert das Modul an einem Ort ohne B3 den Dienst. Dann aufheben:

```
AT!BAND=00
```

Für mobile Nutzung besser B3 + B20 + B8 (`...0080084`), dann bleibt ein Rückfall. Das Modul kann
dann aber wieder im Leerlauf auf B8 kampieren.

## 4. Durchsatz messen

Immer an die Mobilfunk-Schnittstelle binden, sonst misst man das WLAN.

Windows:

```powershell
$ix  = (Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceDescription -like '*EM7455*' }).ifIndex
$src = (Get-NetIPAddress -InterfaceIndex $ix -AddressFamily IPv4).IPAddress
curl.exe -s --interface $src -o NUL -w "%{speed_download} B/s`n" "https://speed.cloudflare.com/__down?bytes=50000000"
# vier Stroeme parallel:
1..4 | ForEach-Object { Start-Job { param($s) curl.exe -s --interface $s -o NUL -w "%{size_download} %{time_total}" "https://speed.cloudflare.com/__down?bytes=40000000" } -ArgumentList $src } | Wait-Job | Receive-Job
```

Linux:

```bash
curl -s --interface wwan0 -o /dev/null -w "%{speed_download} B/s\n" "https://speed.cloudflare.com/__down?bytes=50000000"
```

Einzelstrom deutlich unter Mehrstrom-Summe: Netzseitige Begrenzung pro Fluss oder überlastete Zelle,
nicht das Modem. Beide niedrig bei gutem SINR: Vertragsdrossel. Beide niedrig bei SINR unter 3: Funk.
Während der Messung `AT!GSTATUS?` lesen, dann sieht man, ob CA auf ACTIVE geht und wie weit der SINR
unter Last fällt.

## 5. Antennen

Fällt der SINR unter Last auf unter 3 dB bei gutem RSRP, stören Nachbarzellen. Das ist der Normalfall
mit den Stummelantennen eines USB-Gehäuses. Reihenfolge nach Nutzen:

1. Beide Antennen anschließen (MAIN und AUX). Ohne AUX kein MIMO und keine CA. Prüfen: in
   `AT!GSTATUS?` müssen "RxM" und "RxD" ähnliche Werte zeigen.
2. Zwei Rundstrahler 698 bis 2700 MHz mit SMA, am Fenster, etwa 20 cm Abstand, eine senkrecht,
   eine waagrecht.
3. Richtantenne (LPDA oder Panel, 9 bis 11 dBi) zur Basisstation bei festem Standort. Die Richtung
   liefert `AT!LTEINFO?` nicht; Zellstandorte über cellmapper.net anhand der Cell ID aus `AT!GSTATUS?`.
4. SMA gegen RP-SMA prüfen, die Gehäuse mischen das gern.

Was nichts bringt: USB 3 statt USB 2 (das Modul ist mit 300 Mbit/s weit unter USB 2), Windows-TCP-
Tuning (Autotuning "normal" reicht), `AT!USBSPEED`.
