import asyncio
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    async with sse_client("http://localhost:8000/sse") as streams:
        async with ClientSession(streams[0], streams[1]) as session:
            await session.initialize()
            
            print("Queueing P2-D1...")
            res1 = await session.call_tool("queue_task", {"task_id": "P2-D1", "spec_path": "docs/specs/P2-D1_dmx_engine.md"})
            print(res1)
            
            print("Queueing P2-D2...")
            res2 = await session.call_tool("queue_task", {"task_id": "P2-D2", "spec_path": "docs/specs/P2-D2_artnet_output.md"})
            print(res2)

            print("Queueing P2-D3...")
            res3 = await session.call_tool("queue_task", {"task_id": "P2-D3", "spec_path": "docs/specs/P2-D3_dmx_fx.md"})
            print(res3)

            print("Worker Alpha requesting work...")
            work = await session.call_tool("request_work", {"worker_name": "WorkerAlpha"})
            print("Received work:", work)

if __name__ == "__main__":
    asyncio.run(main())
