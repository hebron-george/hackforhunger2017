import json

event =  {
    "trigger": "message:appUser",
    "app": {
        "_id": "5698edbf2a43bd081be982f1"
    },
    "messages":[{
        "_id": "55c8c1498590aa1900b9b9b1",
        "text": "Hi! Do you have time to chat?",
        "role": "appUser",
        "authorId": "c7f6e6d6c3a637261bd9656f",
        "name": "Steve",
        "received": 1444348338.704,
        "metadata": {},
        "actions": [],
        "source": {
            "type": "messenger"
        }
    }],
    "appUser": {
        "_id": "c7f6e6d6c3a637261bd9656f",
        "userId": "bob@example.com",
        "properties": {},
        "signedUpAt": "2015-10-06T03:38:02.346Z",
        "clients": [
          {
            "active": True,
            "appVersion": "1.0",
            "id": "5A7F8343-DF41-46A8-96EC-8583FCB422FB",
            "lastSeen": "2016-03-09T19:09:01.431Z",
            "platform": "ios",
            "pushNotificationToken": "<...>",
            "info": {
              "appName": "ShellApp",
              "devicePlatform": "x86_64",
              "os": "iPhone OS",
              "osVersion": "9.2"
            }
          }
        ]
    }
}

def lambda_handler(event, context):
    # TODO implement
    timestamp = event['messages'][0]['received']
    respondent_id = event['messages'][0]['authorId']
    device_type = event['appUser']['clients'][0]['info']
    raw_response = event['messages'][0]['text']

    response_payload = {
        "timestamp": timestamp,
        "session_id": "",
        "respondent": 
        {
            "respondent_id": respondent_id,
            "location": "",
            "location_type": "",
            "language": "",
            "device_type": device_type
        },
        "raw_response": raw_response,
        "question":
        {
            "question_id": "",
            "question_text": "",
            "metrics": []
        }
    }

    print json.dumps(response_payload, indent=4)

'''
response_payload = {
  "timestamp": <unix timestamp>, # good
  "session_id": <session id>,
  "respondent": {
    "respondent_id": <id string>, # good
    "location": <location string>, 
    "location_type": <location type>,
    "language": <language if known>,
    "device_type": <device type if known> # good
  },
  "raw_response": <response string (optional)>, # good
  "question": {
    "question_id": <question id>,
    "question_text": <question text>,
    "metrics": [
      {"metric_id": <metric id>, "type": <metric type>, "score": <metric score>},
      {"metric_id": <metric id>, "type": <metric type>, "score": <metric score>},
      ...
      {"metric_id": <metric id>, "type": <metric type>, "score": <metric score>}
    ]
  }
}

'''


lambda_handler(event, None)
