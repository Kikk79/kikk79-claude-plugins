"""Berechnet die AT!OPENLOCK-Antwort fuer Sierra-Module mit dem Keygen aus bkerler/edl.

Laedt nur die Klasse SierraGenerator aus sierrakeygen.py und stubbt die Module
(pyserial, Exscript, colorama), die das Skript nur fuer seine Telnet-/Auto-Modi braucht.

Aufruf:  python -I keygen_wrap.py <pfad/sierrakeygen.py> [<challenge>] [<generation>]
Ausgabe: SELFTEST OK|FAIL ...   und bei Challenge:   RESPONSE <16 Hex>
"""
import importlib.util
import sys
import types

for name in ["serial", "serial.tools", "serial.tools.list_ports",
             "Exscript", "Exscript.protocols", "Exscript.protocols.telnetlib", "colorama"]:
    sys.modules[name] = types.ModuleType(name)
sys.modules["Exscript.protocols.telnetlib"].Telnet = object
_names = ["RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE", "BLACK", "RESET",
          "RESET_ALL", "BRIGHT", "DIM", "NORMAL", "LIGHTBLUE_EX", "LIGHTRED_EX", "LIGHTGREEN_EX",
          "LIGHTYELLOW_EX", "LIGHTMAGENTA_EX", "LIGHTCYAN_EX", "LIGHTWHITE_EX"]
for attr in ("Fore", "Back", "Style"):
    setattr(sys.modules["colorama"], attr, types.SimpleNamespace(**{k: "" for k in _names}))
sys.modules["colorama"].init = lambda *a, **k: None

spec = importlib.util.spec_from_file_location("sierrakeygen", sys.argv[1])
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

generation = sys.argv[3] if len(sys.argv) > 3 else "MDM9x30"
g = mod.SierraGenerator()
# Testvektor aus der Selbsttest-Tabelle des Skripts (MDM9x30 = EM7455)
test = g.run("MDM9x30", "BE96CBBEE0829BCA", 0)
print("SELFTEST", "OK" if test == "1E02CE6A98B7DD2A" else "FAIL " + str(test))
if len(sys.argv) > 2:
    print("RESPONSE", g.run(generation, sys.argv[2], 0))
