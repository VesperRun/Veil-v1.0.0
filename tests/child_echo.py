import os
import sys
from pathlib import Path

name = sys.argv[1]
out = Path(sys.argv[2]) if len(sys.argv) > 2 else None
value = os.environ.get(name, "")
if out:
    out.write_text(value, encoding="utf-8")
else:
    sys.stdout.write(value)
