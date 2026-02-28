import memory
import json

def test():
    convs = memory.list_conversations(status="active", project=None, limit=10)
    print(f"Active, no project filter: {len(convs)}")
    for c in convs:
        print(f" - {c['id']}: {c['name']} (Project: {c['project']})")

    convs2 = memory.list_conversations(status="active", project="outback", limit=10)
    print(f"Active, project='outback': {len(convs2)}")

if __name__ == "__main__":
    test()
