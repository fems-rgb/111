import asyncio
import httpx

async def main():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwidXNlcm5hbWUiOiJhZG1pbiIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc4NzMzMTM5NCwiaWF0IjoxNzg3MjQ0OTk0LCJ0eXBlIjoiYWNjZXNzIn0.MiCuA6ag2Chckb-x8k_HO4xewkii72EyCsPsOGmIZt8"
    
    # 先用 TestClient 直接调用，绕过网络层，能看到完整异常
    from app.main import app
    from fastapi.testclient import TestClient
    
    client = TestClient(app)
    resp = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})
    print(f"Status: {resp.status_code}")
    print(f"Response: {resp.text[:2000]}")

asyncio.run(main())
