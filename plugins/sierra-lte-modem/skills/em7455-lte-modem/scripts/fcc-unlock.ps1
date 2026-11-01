# Schaltet die FCC-Authentifizierung (LPM-Voter "BIOS") einer Sierra EM7455 dauerhaft ab (oder an).
# Ablauf: Keygen-Selbsttest -> AT!OPENLOCK? -> Antwort berechnen -> AT!OPENLOCK="..."
#         -> AT!PCFCCAUTH=<Set> -> AT!RESET -> Zustand pruefen.
# Braucht: python 3 im PATH. sierrakeygen.py (bkerler/edl, GPLv3, siehe NOTICE.md) liegt im selben
# Ordner und wird ohne -Keygen automatisch benutzt.
# Beispiel: powershell -ExecutionPolicy Bypass -File fcc-unlock.ps1 -Port COM7
param(
    [string]$Port = 'COM7',
    [string]$Keygen = (Join-Path $PSScriptRoot 'sierrakeygen.py'),
    [ValidateSet('0', '1')][string]$Set = '0',
    [string]$Generation = 'MDM9x30'
)
$ErrorActionPreference = 'Stop'
$wrap = Join-Path $PSScriptRoot 'keygen_wrap.py'

$st = & python -I $wrap $Keygen 2>&1
"Selbsttest: $st"
if ($st -notmatch 'SELFTEST OK') { throw 'Keygen-Selbsttest fehlgeschlagen' }

function Open-At {
    $s = New-Object System.IO.Ports.SerialPort $Port, 115200, 'None', 8, 'One'
    $s.ReadTimeout = 3000; $s.WriteTimeout = 3000; $s.DtrEnable = $true; $s.RtsEnable = $true
    $s.Open(); return $s
}
function Q($s, $cmd, $wait = 1500) {
    $s.DiscardInBuffer(); $s.Write("$cmd`r"); Start-Sleep -Milliseconds $wait
    $out = ''
    try { while ($s.BytesToRead -gt 0) { $out += $s.ReadExisting(); Start-Sleep -Milliseconds 200 } } catch {}
    return $out
}

$sp = Open-At
Q $sp 'ATE0' | Out-Null
Q $sp 'AT!ENTERCND="A710"' | Out-Null
$ch = (Q $sp 'AT!OPENLOCK?') -replace '\s', '' -replace 'OK$', ''
"Challenge: $ch"
if ($ch -notmatch '^[0-9A-F]{16}$') { $sp.Close(); throw "Unerwartete Challenge '$ch' - ist $Port der AT-Port?" }

$resp = ((& python -I $wrap $Keygen $ch $Generation 2>&1) | Select-String 'RESPONSE').Line -replace 'RESPONSE\s*', ''
"Response:  $resp"
$r = Q $sp ("AT!OPENLOCK=`"$resp`"")
"OPENLOCK   -> $($r.Trim())"
if ($r -notmatch 'OK') { $sp.Close(); throw 'OPENLOCK abgelehnt (falsche Generation?)' }

"PCFCCAUTH=$Set -> " + (Q $sp "AT!PCFCCAUTH=$Set").Trim()
"PCFCCAUTH?  -> " + (Q $sp 'AT!PCFCCAUTH?').Trim()
Q $sp 'AT!RESET' 800 | Out-Null
"AT!RESET gesendet, warte auf Neustart..."
$sp.Close()

Start-Sleep -Seconds 25
$ok = $false
for ($i = 0; $i -lt 20 -and -not $ok; $i++) {
    $present = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
        Where-Object { $_.InstanceId -like 'USB\VID_1199&PID_90*&MI_03*' -and $_.Status -eq 'OK' }
    if ($present) {
        try { $sp = Open-At; if ((Q $sp 'AT' 800) -match 'OK') { $ok = $true } else { $sp.Close() } } catch {}
    }
    if (-not $ok) { Start-Sleep -Seconds 5 }
}
if (-not $ok) { throw 'AT-Port nach Reset nicht erreichbar, Zustand von Hand pruefen' }

"--- Zustand nach Reset:"
Q $sp 'ATE0' | Out-Null
Q $sp 'AT!ENTERCND="A710"' | Out-Null
"PCFCCAUTH? -> " + (Q $sp 'AT!PCFCCAUTH?').Trim()
"PCINFO?    -> " + (Q $sp 'AT!PCINFO?').Trim()
"CFUN?      -> " + (Q $sp 'AT+CFUN?').Trim()
Start-Sleep -Seconds 15
"GSTATUS    -> " + (Q $sp 'AT!GSTATUS?' 2500).Trim()
"COPS       -> " + (Q $sp 'AT+COPS?' 2000).Trim()
$sp.Close()

"--- Windows:"
netsh mbn show radio interface="Mobilfunk"
netsh mbn show connection interface="Mobilfunk"
