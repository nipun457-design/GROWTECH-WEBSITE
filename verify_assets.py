import os
import re
from app import app

client = app.test_client()

routes = ['/', '/company', '/products', '/news', '/contact']
missing_assets = []
found_assets = set()

img_regex = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)

for r in routes:
    res = client.get(r)
    html = res.data.decode('utf-8')
    matches = img_regex.findall(html)
    for src in matches:
        if src.startswith('/static/'):
            local_path = os.path.join(*src.strip('/').split('/'))
            if os.path.exists(local_path):
                found_assets.add(src)
            else:
                missing_assets.append((r, src))

print('Total unique verified images across rendered pages:', len(found_assets))
for a in sorted(found_assets):
    print('  [EXISTS]', a)

if missing_assets:
    print('ERROR: Missing image assets:', missing_assets)
else:
    print('SUCCESS: Every single image referenced in all 5 pages exists on disk!')
