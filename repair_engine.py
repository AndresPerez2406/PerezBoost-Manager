import os
import sys
import re

def repair_file(filepath):
    print(f"Repairing {filepath}...")
    
    with open(filepath, 'rb') as f:
        data = f.read()

    # 1. De-double newlines
    # If the file had \r\n\r\n everywhere, replace it.
    # But be careful about intentional blank lines (which would be \r\n\r\n\r\n\r\n)
    # Strategy: Replace \r\n\r\n -> \r\n
    # This turns 4x into 2x, which is correct for intentional blank lines.
    doubled_newlines = data.count(b'\r\n\r\n')
    if doubled_newlines > 100: # Safe threshold to assume corruption
        print(f"Detected {doubled_newlines} doubled newlines. Normalizing...")
        data = data.replace(b'\r\n\r\n', b'\r\n')
    
    # 2. Fix Mojibake surgically
    # We decode as UTF-8 (replace errors to avoid crash)
    text = data.decode('utf-8', errors='replace')
    
    lines = text.split('\n')
    fixed_lines = []
    mojibake_fixed = 0
    
    for line in lines:
        if '\u00c3' in line: # 'Ã'
            try:
                # Try to fix the whole line
                fixed_line = line.encode('latin-1').decode('utf-8')
                fixed_lines.append(fixed_line)
                mojibake_fixed += 1
            except (UnicodeEncodeError, UnicodeDecodeError):
                # If fails, keep as is or try surgical fix for known patterns
                # For now, let's keep the line if single-line fix fails
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    print(f"Fixed {mojibake_fixed} lines with mojibake.")
    
    # 3. Final normalization
    result_text = '\n'.join(fixed_lines)
    
    # Ensure CRLF line endings (standard for this project)
    result_text = result_text.replace('\r\n', '\n').replace('\n', '\r\n')
    
    return result_text.encode('utf-8')

if __name__ == "__main__":
    target = r'd:\Perez Boost Manager\Dev_PerezBoost_Pro\dashboard_web.py'
    repaired_data = repair_file(target)
    
    with open(target, 'wb') as f:
        f.write(repaired_data)
    
    print("Repair complete.")
