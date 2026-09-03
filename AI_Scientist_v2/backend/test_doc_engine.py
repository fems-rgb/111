import asyncio, sys
sys.path.insert(0, '.')
from app.services.doc_engine import DocumentEngine

async def test():
    engine = DocumentEngine()
    result = await engine.generate_document(
        research_question='基于FAST脉冲星计时阵列的纳赫兹引力波背景探测新方法',
        context='',
        template_id='nh_202619_track1'
    )
    if result['success']:
        with open('test_output.md', 'w', encoding='utf-8') as f:
            f.write(result['document'])
        n_sections = len(result['sections'])
        n_chars = len(result['document'])
        print(f'OK: {n_chars} chars, {n_sections} sections')
    else:
        print(f"FAIL: {result.get('error')}")

asyncio.run(test())
