import requests

# We will test the resolve API for an ignored issue
# Pick an ACKNOWLEDGED or NEW issue ID from the previous run
issue_id = "3a9e9df5-0e49-4961-ace4-f533e5ff67c5"

res = requests.post(
    f"http://localhost:8000/api/v1/issues/{issue_id}/resolve",
    json={"status": "IGNORED", "resolution": "Ignored by operator", "user_typing": "test ignore"}
)
print(res.status_code)
print(res.text)
