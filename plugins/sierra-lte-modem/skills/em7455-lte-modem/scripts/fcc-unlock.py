#!/usr/bin/env python3
"""FCC-Auth-Sperre einer Sierra EM7455 dauerhaft aus- oder einschalten (Windows und Linux).

Ablauf: AT!OPENLOCK? -> Antwort per keygen_wrap.py -> AT!OPENLOCK="..." -> AT!PCFCCAUTH=<0|1>
        -> AT!RESET -> nach dem Neustart AT!PCFCCAUTH? und AT!PCINFO? anzeigen.

Voraussetzungen: pyserial (pip install pyserial). sierrakeygen.py (bkerler/edl, GPLv3, siehe NOTICE.md)
liegt im selben Ordner und wird ohne --keygen automatisch benutzt. Unter Linux vorher
`systemctl stop ModemManager`.

Beispiele:
  python fcc-unlock.py --port COM7 --set 0
  python3 fcc-unlock.py --port /dev/ttyUSB2 --set 0
"""
import argparse
import os
import re
import subprocess
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial fehlt: pip install pyserial")

HERE = os.path.dirname(os.path.abspath(__file__))


def q(port, cmd, wait=1.5):
    port.reset_input_buffer()
    port.write((cmd + "\r").encode())
    time.sleep(wait)
    out = b""
    while port.in_waiting:
        out += port.read(port.in_waiting)
        time.sleep(0.2)
    return out.decode(errors="replace").strip()


def open_port(name):
    p = serial.Serial(name, 115200, timeout=3, dsrdtr=False, rtscts=False)
    p.dtr = True
    p.rts = True
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", required=True, help="COM7 oder /dev/ttyUSB2")
    ap.add_argument("--keygen", default=os.path.join(HERE, "sierrakeygen.py"),
                    help="Pfad zu sierrakeygen.py (Standard: beiliegende Kopie)")
    ap.add_argument("--set", choices=["0", "1"], default="0", help="0 = Sperre aus, 1 = Sperre an")
    ap.add_argument("--generation", default="MDM9x30", help="MDM9x30 (EM7455), MDM9x50 (EM7565)")
    a = ap.parse_args()

    wrap = os.path.join(HERE, "keygen_wrap.py")
    st = subprocess.run([sys.executable, "-I", wrap, a.keygen], capture_output=True, text=True).stdout
    print("Selbsttest:", st.strip())
    if "SELFTEST OK" not in st:
        sys.exit("Keygen-Selbsttest fehlgeschlagen")

    p = open_port(a.port)
    q(p, "ATE0")
    q(p, 'AT!ENTERCND="A710"')
    ch = re.sub(r"\s|OK$", "", q(p, "AT!OPENLOCK?"))
    print("Challenge:", ch)
    if not re.fullmatch(r"[0-9A-F]{16}", ch):
        sys.exit("Unerwartete Challenge, ist das der AT-Port?")

    out = subprocess.run([sys.executable, "-I", wrap, a.keygen, ch, a.generation],
                         capture_output=True, text=True).stdout
    resp = re.search(r"RESPONSE\s+([0-9A-F]{16})", out).group(1)
    print("Response: ", resp)
    r = q(p, f'AT!OPENLOCK="{resp}"')
    print("OPENLOCK ->", r)
    if "OK" not in r:
        sys.exit("OPENLOCK abgelehnt (falsche Generation?)")

    print(f"PCFCCAUTH={a.set} ->", q(p, f"AT!PCFCCAUTH={a.set}"))
    print("PCFCCAUTH? ->", q(p, "AT!PCFCCAUTH?"))
    q(p, "AT!RESET", 0.8)
    p.close()
    print("AT!RESET gesendet, warte auf Neustart ...")

    time.sleep(25)
    p = None
    for _ in range(20):
        try:
            p = open_port(a.port)
            if "OK" in q(p, "AT", 0.8):
                break
            p.close()
        except (serial.SerialException, OSError):
            pass
        p = None
        time.sleep(5)
    if p is None:
        sys.exit("AT-Port nach Reset nicht erreichbar, Zustand von Hand pruefen")

    q(p, "ATE0")
    q(p, 'AT!ENTERCND="A710"')
    print("--- nach Reset")
    print("PCFCCAUTH? ->", q(p, "AT!PCFCCAUTH?"))
    print("PCINFO?    ->", q(p, "AT!PCINFO?"))
    print("CFUN?      ->", q(p, "AT+CFUN?"))
    time.sleep(15)
    print("GSTATUS    ->", q(p, "AT!GSTATUS?", 2.5))
    print("COPS       ->", q(p, "AT+COPS?", 2))
    p.close()


if __name__ == "__main__":
    main()
