"""
Fix the double-blank-line issue caused by CRLF expansion during text mode reads.
The file has \r\n\r\n everywhere instead of \r\n.
Strategy: read as binary, replace all \r\n\r\n -> \r\n ONLY where no blank line was originally intended.
Better strategy: read as binary, replace \r\n\r\n with \r\n globally (since the original had NO double blank lines),
then verify line count.
"""

with open('dashboard_web.py', 'rb') as f:
    raw = f.read()

print(f"Before: {len(raw)} bytes, {raw.count(b'\\r\\n')} CRLF sequences")

# Remove the doubled CRLF: every \r\n became \r\n\r\n
# So replace \r\n\r\n -> \r\n, BUT careful about intentional blank lines.
# Original file had some blank lines too (as \r\n\r\n originally).
# After doubling, intentional blank lines become \r\n\r\n\r\n\r\n.
# So: \r\n\r\n\r\n\r\n -> \r\n\r\n (intentional blank lines)
#     \r\n\r\n -> \r\n (doubled single newlines)

# First, protect intentional blank lines (triple or more \r\n sequences)
# by replacing them with a placeholder
# Actually simpler: since every line got doubled, 3+ \r\n means originally 1+ blank lines
# The pattern is: all \r\n -> \r\n\r\n, all blank lines -> \r\n\r\n\r\n\r\n

# So the inverse is:
# Replace \r\n\r\n with a single \r\n
# This will turn quadruple sequences into double (preserving blank lines)

fixed = raw.replace(b'\r\n\r\n', b'\r\n')

print(f"After: {len(fixed)} bytes, {fixed.count(b'\\r\\n')} CRLF sequences")
print(f"First 300 bytes: {repr(fixed[:300])}")

# Verify the syntax
import subprocess, tempfile, os
with open('_test_fixed.py', 'wb') as f:
    f.write(fixed)
    
result = subprocess.run(
    [r'.venv\Scripts\python.exe', '-m', 'py_compile', '_test_fixed.py'],
    capture_output=True, text=True, encoding='utf-8', errors='replace'
)

os.remove('_test_fixed.py')

if result.returncode == 0:
    print("Syntax OK! Saving...")
    with open('dashboard_web.py', 'wb') as f:
        f.write(fixed)
    print("Saved!")
else:
    print(f"Syntax error: {result.stderr[:400]}")
    # Show the lines around the error
    lines = fixed.split(b'\r\n')
    print(f"Total lines: {len(lines)}")
