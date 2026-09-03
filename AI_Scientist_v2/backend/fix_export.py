import pathlib
from urllib.parse import quote

fp = pathlib.Path(r'D:\AI_Scientist\AI_Scientist\backend\app\api\v1\export.py')
lines = fp.read_text('utf-8').splitlines(True)
out = []
for line in lines:
    # Add import after safe_json_parse import
    if 'from app.utils.safe_json import safe_json_parse' in line and 'urllib.parse' not in ''.join(lines):
        out.append('from urllib.parse import quote\n')
        out.append(line)
    # Fix MD header
    elif 'Content-Disposition' in line and "XH-202619_" in line and ".md" in line:
        indent = line[:len(line) - len(line.lstrip())]
        cn_name = 'XH-202619_\u6280\u672f\u65b9\u6848.md'
        out.append(indent + 'headers={"Content-Disposition": "attachment; filename=\\"XH-202619_report.md\\"; filename*=UTF-8\'\'" + quote("' + cn_name + '")}\n')
    # Fix PDF header
    elif 'Content-Disposition' in line and "XH-202619_" in line and ".pdf" in line:
        indent = line[:len(line) - len(line.lstrip())]
        cn_name = 'XH-202619_\u6280\u672f\u65b9\u6848.pdf'
        out.append(indent + 'headers={"Content-Disposition": "attachment; filename=\\"XH-202619_report.pdf\\"; filename*=UTF-8\'\'" + quote("' + cn_name + '")}\n')
    else:
        out.append(line)

fp.write_text(''.join(out), 'utf-8')
print('PATCHED OK')
