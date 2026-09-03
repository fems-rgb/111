import pathlib
p = pathlib.Path(r'D:\AI_Scientist\AI_Scientist\frontend\src\api\modules\chat.ts')
c = p.read_text(encoding='utf-8')
old = 'client.get(/multimodal/upload/status/)'
new = 'client.get(`/multimodal/upload/status/${uploadId}`)'
if old in c:
    c = c.replace(old, new)
    p.write_text(c, encoding='utf-8')
    print('Fixed: getStatus template literal')
else:
    print('Pattern not found, checking current content...')
    for i, line in enumerate(c.splitlines(), 1):
        if 'getStatus' in line or 'status' in line.lower():
            print(f'  L{i}: {line.strip()}')
