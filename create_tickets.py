import requests
import json

url = "http://127.0.0.1:5000/ticket"
headers = {
    'content-type': "application/json",
}

start = 2
end = 100
while start <= end:
    ticketdata = {
        "id": start,
        "title": f"Ticket created with ID/number:{start}",
        "description": f"desc: {start}",
        "status": "new",
        "agent": f"plac{start}",
        "customer": "default",
        "agent_notes": f"test notes{start}"
    }
    payload = json.dumps(ticketdata, indent=4)
    try:
        response = requests.request("POST", url, data=payload, headers=headers)
    except Exception as err:
        pprint(err)
    start+=1
