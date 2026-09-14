import asyncio
import sys

sys.path.append(r"c:\Users\User\Downloads\DocAssistIQ\backend")

from app.services.llm_service import llm_service

class MockClient:
    async def post(self, url, json):
        class Resp:
            def json(self):
                return {"response": "```json\n{\n  \"test\": \"success\"\n}\n```"}
            def raise_for_status(self):
                pass
        return Resp()

async def test():
    llm_service.client = MockClient()
    try:
        resp = await llm_service.generate_json("test", "test")
        print("Success JSON Extracted:", resp)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test())
