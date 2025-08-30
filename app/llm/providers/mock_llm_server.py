from fastapi import FastAPI
import json

app = FastAPI()

@app.post("/v1/chat/completions")
async def mock_completion():
    return {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "dag": {
                            "nodes": [{"id": "stub-dev", "role": "Dev", "name": "Stub Task"}],
                            "edges": []
                        },
                        "budgets": {"Dev": 100},
                        "dod": ["Stub task is completed."]
                    })
                }
            }
        ]
    }