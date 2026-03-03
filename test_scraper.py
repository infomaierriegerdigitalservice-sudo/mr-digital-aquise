import sys
import logging
sys.path.append(r"c:\Users\Nicklas Rieger\OneDrive\Desktop\Antigravity\Automatisierung\mr-digital-akquise-v2")
from researcher import _scrape_gelbeseiten, _scrape_branchenbuch

logging.basicConfig(level=logging.DEBUG)

print("Testing Gelbe Seiten...")
gs = _scrape_gelbeseiten("Maler", "")
print("Gelbe Seiten Results:")
for r in gs:
    print(r)

print("\nTesting Branchenbuch...")
bb = _scrape_branchenbuch("Maler", "")
print("Branchenbuch Results:")
for r in bb:
    print(r)
