import asyncio
import logging
logging.disable(logging.CRITICAL)

from app.database.session import AsyncSessionLocal
from app.database import models
from sqlalchemy import select

async def check():
    async with AsyncSessionLocal() as db:
        print('=== Projects ===')
        result = await db.execute(select(models.Project))
        for p in result.scalars().all():
            print(f'  id={p.id}, title={p.title}, status={p.status}, complexity={p.complexity}, progress={p.progress}')
            print(f'    config={p.config}')
            print(f'    created={p.created_at}, updated={p.updated_at}')

        print()
        print('=== PipelineRuns ===')
        result = await db.execute(select(models.PipelineRun))
        runs = result.scalars().all()
        if not runs:
            print('  (empty)')
        for r in runs:
            cols = {c.name: getattr(r, c.name, None) for c in r.__table__.columns}
            print(f'  {cols}')

        print()
        print('=== Pipelines (templates) ===')
        result = await db.execute(select(models.Pipeline))
        pipes = result.scalars().all()
        if not pipes:
            print('  (empty)')
        for pipe in pipes:
            cols = {c.name: getattr(pipe, c.name, None) for c in pipe.__table__.columns}
            print(f'  {cols}')

        print()
        print('=== AgentTasks ===')
        result = await db.execute(select(models.AgentTask))
        tasks = result.scalars().all()
        if not tasks:
            print('  (empty)')
        for t in tasks:
            cols = {c.name: getattr(t, c.name, None) for c in t.__table__.columns}
            print(f'  {cols}')

asyncio.run(check())
