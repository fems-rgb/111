import asyncio, sys, traceback
sys.path.insert(0, r'D:\AI_Scientist\AI_Scientist\backend')

print('=== get_user_projects test ===')
from app.database.session import AsyncSessionLocal

async def test():
    async with AsyncSessionLocal() as db:
        try:
            from app.services.project_service import get_user_projects
            result = await get_user_projects(db, user_id=1, workspace='personal')
            print(f'OK: {len(result)} projects')
            for p in result:
                print(f'  id={p.id} title={p.title} status={p.status}')
        except Exception:
            traceback.print_exc()

asyncio.run(test())
