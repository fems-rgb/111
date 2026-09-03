import asyncio
from app.main import app

# 列出所有已注册的路由
print('=== REGISTERED ROUTES ===')
for route in app.routes:
    if hasattr(route, 'path') and hasattr(route, 'methods'):
        print(f'  {route.methods} {route.path}')
    elif hasattr(route, 'path'):
        print(f'  MOUNT {route.path}')
