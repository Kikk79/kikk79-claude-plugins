# Windows 11: Befehle und Abläufe

Alle Befehle in PowerShell 7 oder Windows PowerShell, ohne Zusatzsoftware. Der deutsche
Schnittstellenname ist "Mobilfunk", auf englischen Systemen "Cellular".

## Gerät finden und Zustand lesen

```powershell
# Alle Sierra-Geräte, auch die nicht mehr vorhandenen (Vorgeschichte sichtbar)
Get-PnpDevice | Where-Object { $_.InstanceId -like 'USB\VID_1199*' } |
  Select-Object Status, Present, Class, FriendlyName, InstanceId

# Fehlercode und Treiber eines Geräts
Get-PnpDeviceProperty -InstanceId '<InstanceId>' -KeyName 'DEVPKEY_Device_ProblemCode',
  'DEVPKEY_Device_DriverInfPath','DEVPKEY_Device_DriverProvider','DEVPKEY_Device_Service',
  'DEVPKEY_Device_CompatibleIds'
```

Lesehilfe für die Compatible IDs:

- `USB\COMPOSITE` am Elterngerät: Normalbetrieb, Windows lädt usbccgp und zerlegt in MI_00 (DM),
  MI_03 (AT, Klasse FF/00), MI_0C (MBIM, Klasse 02/0E).
- Nur `USB\Class_FF&SubClass_FF&Prot_FF` ohne COMPOSITE: eine einzige Schnittstelle, das Modul ist
  im Bootmodus (PID 9078). Kein Treiber kann hier helfen.

## Mobilfunkdienst und Schnittstelle

```powershell
Get-Service WwanSvc                       # startet automatisch, sobald MBIM-Gerät da ist
netsh mbn show interfaces                 # Modell, Firmware, Anbieter, Signal
netsh mbn show readyinfo  interface="Mobilfunk"   # SIM-Zustand, ICCID, Rufnummer
netsh mbn show radio      interface="Mobilfunk"   # Hardware/Software-Funkstatus
netsh mbn show homeprovider interface="Mobilfunk"
netsh mbn show provisionedcontexts interface="Mobilfunk"   # hinterlegte APNs
netsh mbn show connection interface="Mobilfunk"
netsh mbn show signal     interface="Mobilfunk"
```

"Aktueller Software-Funkstatus: Aus" bei "Client hat Ein angefordert" ist nicht Windows, sondern das
Modul selbst (Low Power Mode). Dann AT-Port befragen, nicht an Windows-Einstellungen drehen.

## APN anlegen, falls Windows ihn nicht selbst hat

Einstellungen, Netzwerk und Internet, Mobilfunk, Mobilfunkanbietereinstellungen, APN hinzufügen.
Oder per Befehl:

```powershell
netsh mbn add profile interface="Mobilfunk" name="C:\pfad\telekom.xml"
```

Profil-XML (Telekom):

```xml
<?xml version="1.0"?>
<MBNProfileExt xmlns="http://www.microsoft.com/networking/WWAN/profile/v4">
  <Name>Telekom</Name>
  <IsDefault>true</IsDefault>
  <ProfileCreationType>UserProvisioned</ProfileCreationType>
  <SubscriberID>IMSI_AUS_READYINFO</SubscriberID>
  <SimIccID>ICCID_AUS_READYINFO</SimIccID>
  <ConnectionMode>auto</ConnectionMode>
  <Context>
    <AccessString>internet.telekom</AccessString>
    <UserLogonCred><UserName>telekom</UserName><Password>tm</Password></UserLogonCred>
    <Compression>NONE</Compression>
    <AuthProtocol>NONE</AuthProtocol>
    <IPType>IPv4v6</IPType>
  </Context>
</MBNProfileExt>
```

SubscriberID (IMSI) und ICCID aus `netsh mbn show readyinfo` übernehmen.

## AT-Port aus PowerShell ansprechen

Windows Update installiert für MI_03 den Sierra-Treiber "WWAN Modem". Die COM-Nummer steht in der
Registry, nicht im Anzeigenamen:

```powershell
$at = Get-PnpDevice -PresentOnly | Where-Object { $_.InstanceId -like 'USB\VID_1199&PID_9079&MI_03*' }
(Get-ItemProperty "HKLM:\SYSTEM\CurrentControlSet\Enum\$($at.InstanceId)\Device Parameters").PortName
```

Befehle senden, ohne PuTTY:

```powershell
$sp = New-Object System.IO.Ports.SerialPort 'COM7',115200,'None',8,'One'
$sp.ReadTimeout = 3000; $sp.DtrEnable = $true; $sp.RtsEnable = $true; $sp.Open()
function Q($cmd, $wait = 1500) {
  $sp.DiscardInBuffer(); $sp.Write("$cmd`r"); Start-Sleep -Milliseconds $wait
  $out = ''; while ($sp.BytesToRead -gt 0) { $out += $sp.ReadExisting(); Start-Sleep -Milliseconds 200 }
  "> $cmd"; $out.Trim()
}
Q 'ATE0'; Q 'AT!ENTERCND="A710"'; Q 'AT!PCINFO?'; Q 'AT!GSTATUS?' 2500
$sp.Close()
```

`AT!ENTERCND` in Großbuchstaben schreiben, klein geschrieben antwortet das Modul mit ERROR.
Der MBIM-Treiber und der AT-Port stören sich nicht, beide können gleichzeitig offen sein.

## Nach AT!RESET

Das Modul verschwindet für 20 bis 40 Sekunden vom USB. Nicht sofort den COM-Port öffnen, sondern erst
warten, bis MI_03 wieder mit Status OK vorhanden ist, und dann mit einem nackten `AT` testen.

## Datenweg prüfen

Windows zieht die Standardroute über WLAN vor, solange es verbunden ist. Darum beim Test die
Quelladresse erzwingen:

```powershell
$ix = (Get-NetAdapter | Where-Object { $_.Status -eq 'Up' -and $_.InterfaceDescription -like '*EM7455*' }).ifIndex
$src = (Get-NetIPAddress -InterfaceIndex $ix -AddressFamily IPv4).IPAddress
ping -n 3 -S $src 1.1.1.1
```

Telekom vergibt private IPv4 (10.x, CGNAT) und öffentliche IPv6 (2a01:599:...). Beides ist normal.

## Verwaiste Adapter aufräumen

Jeder Boot-Zyklus im QDL-Modus hinterlässt einen Eintrag "Mobilfunk N". Sie stören nicht. Entfernen:
Geräte-Manager, Ansicht, "Ausgeblendete Geräte anzeigen", Netzwerkadapter, die halbtransparenten
EM7455-Einträge deinstallieren. Oder:

```powershell
Get-PnpDevice | Where-Object { $_.FriendlyName -like '*EM7455*' -and -not $_.Present } |
  ForEach-Object { pnputil /remove-device $_.InstanceId }
```

## Alternative ohne NV-Änderung: Lenovo-Treiberpaket

Wer die FCC-Sperre im Modul lassen will, installiert Lenovos "Sierra Wireless EM7455 Software for
Windows 11" (nz3wn11w.exe, Version 7.77.5094.0103, Lenovo-Support-ID DS500385). Es ersetzt den
Microsoft-MBIM-Treiber durch Sierras Treiber, der den FCC-Handshake bei jedem Start macht. Nachteil:
Linux braucht dann zusätzlich das ModemManager-Skript, und das Paket ist offiziell nur für ältere
ThinkPads gelistet.
