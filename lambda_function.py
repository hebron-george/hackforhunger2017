from __future__ import print_function # Python 2/3 compatibility
import boto3
from botocore.exceptions import ClientError
import json, hashlib, requests, traceback
'''tempEvent =  {
    "messages":[{
        "_id": "55c8c1498590aa1900b9b9b1",
        "text": "Hi! hopeless",
        "role": "appUser",
        "authorId": "d7f6e6d6c3a637261bd9656f",
        "name": "Steve",
        "received": 1444348338.704,
        "metadata": {},
        "actions": [],
        "source": {
            "type": "messenger"
        }
    }]
}'''

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_session_status(session_id):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-1", endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('Session')
    try:
        response = table.get_item(
           Key={
                'SessionID': session_id
                }
        )
        if 'Item' in response.keys():
            return response['Item']['CurrentStatus']
        else:
            return None
    except ClientError as e:
        print(e.response['Error']['Message'])
        return False
    except Exception as e:
        print(e)
        return False

def get_session(session_id):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-1", endpoint_url="https://dynamodb.us-east-1.amazonaws.com")

    table = dynamodb.Table('Session')
    response = table.get_item(
       Key={
            'SessionID': session_id
            }
    )
    if 'Item' in response.keys():
        return response
    else:
        return None

def update_session(session_id, response_from_user):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-1", endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    table = dynamodb.Table('Session')
    try:

        response = table.update_item(
        Key={
            'SessionID': session_id
        },
        UpdateExpression="set SessionData = :d, CurrentStatus = :c",
        ExpressionAttributeValues={
            ':d': json.dumps(response_from_user),
            ':c': "updated"
        },
        ReturnValues="UPDATED_NEW"
        )
        return "response"
    except ClientError as e:
        print (e.response['Error']['Message'])
        return False
    except Exception as e:
        print(e)
        return False

def update_raw_response(session_id, raw_response):
    print("Inside update_raw_response: {} | {}".format(session_id, raw_response))
    dynamodb = boto3.resource('dynamodb', region_name="us-east-1", endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    table = dynamodb.Table('Session')

    session_to_update = get_session(session_id)
    print("Session to update: {}".format(session_to_update))
    sessionData = session_to_update['Item']['SessionData']
    s = json.loads(sessionData)
    print("Session we're looking to update: {}".format(s))
    s['raw_response'] = raw_response

    response = table.update_item(
    Key={
        'SessionID': session_id
    },
    UpdateExpression="set SessionData = :d",
    ExpressionAttributeValues={
        ':d': json.dumps(s)
    },
    ReturnValues="UPDATED_NEW"
    )

    print("update_raw_response successful: {}".format(session_to_update))
    
        
def create_session(session_id, response_from_user):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-1", endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    table = dynamodb.Table('Session')
    try:
        response = table.put_item(
            Item={
            'SessionID' : session_id,
            'CurrentStatus': "New",
            'SessionData': json.dumps(response_from_user)
            }
        )
    except ClientError as e:
        print (e.response['Error']['Message'])
        return False
    except Exception as e:
        print(e)
        return False

def serial(event):
    # TODO implement
    timestamp = event['messages'][0]['received']
    respondent_id = event['messages'][0]['authorId']
    device_type = event['messages'][0]['source']['type']
    raw_response = event['messages'][0]['text']

    response_payload = {
        "timestamp": timestamp,
        "respondent":
        {
            "respondent_id": respondent_id, 
            "device_type": device_type
        },
        "raw_response": raw_response
    }

    return response_payload

def close_session(session_id):
    dynamodb = boto3.resource('dynamodb', region_name="us-east-1", endpoint_url="https://dynamodb.us-east-1.amazonaws.com")
    table = dynamodb.Table('Session')
    try:
        response = table.delete_item(
                Key={
                    'SessionID':session_id
                }
            )
        return response
    except ClientError as e:
        if e.response['Error']['Code'] == "ConditionalCheckFailedException":
            print(e.response['Error']['Message'])
        else:
            raise  

def send_msg_backend(message):
    try:
        print("line {} data {}".format(145, str(json.dumps(message))))
        handle_message_api = "http://h4h-api.48yn9m8g4b.us-east-1.elasticbeanstalk.com/api/handlemessage/"
        r = requests.post(handle_message_api, json=message)
        print("Status code from backend: {}\n r.reason: {}\n Response: {}".format(r.status_code, r.reason, r.json()))
        return r.json()
    except Exception as e:
        print(e)
        return False

def send_msg_nlp(message):
    try:
        print ("message passed to nlp {}".format(message))
        nlp_url = 'https://0qbp2vi3r5.execute-api.us-east-1.amazonaws.com/Stage/nlp/'
        r = requests.post(nlp_url, json=message)
        if r.status_code == 200:
            return r.json()
        else:
            print(r.status_code)
            return message
    except Exception as e:
        print(e)
        return False

def process_msg(be_msg, serialized_msg):
    serialized_msg['question'] = {}
    serialized_msg['respondent'] = {}


    print("Before processing message back-end: {}".format(be_msg))

    if "question_id" in be_msg['question'].keys():
        serialized_msg['question']['question_id'] = be_msg['question']['question_id']
        
    if "metrics" in be_msg['question'].keys():
        serialized_msg['question']['metrics'] = be_msg['question']['metrics']

    if 'question' in be_msg.keys():
        serialized_msg['question']['question_text'] = be_msg['question']['question_text']

    if 'respondent' in be_msg.keys():
        serialized_msg['respondent']['language']= be_msg['respondent']['language']
        serialized_msg['respondent']['location']= be_msg['respondent']['location']
        serialized_msg['respondent']['location_type']= be_msg['respondent']['location_type']
    
    print("After processing message: {}".format(serialized_msg))
    return serialized_msg
               
def lambda_handler(event, context):
    json_ser = serial(event)
   
    try:
        respondent_hash = hashlib.sha256(json_ser['respondent']['respondent_id']).hexdigest()
        #check status of session
        session_status = get_session_status(respondent_hash)

        # if session is non existant
        if session_status is None:
            print("Creating a brand new session!")
            #generate session obj and create it
            json_ser['SessionID'] = respondent_hash
            create_session(respondent_hash, json_ser)
           
            #send session obj to BE
            r = send_msg_backend(json_ser)

            json_ser = process_msg(r, json_ser)
            update_session(respondent_hash, json_ser)
            print(json_ser['question'])

            #TODO: Send question to the user
            return json_ser['question']['question_text']
            
        # if sessions is existant
        else:
            print("Found an existing session.")
            # TODO: Call backend with response & question id to get metrics types
            update_raw_response(respondent_hash, json_ser['raw_response'])
            session = get_session(respondent_hash)
            print("Existing session: {}".format(session))
            try:
                if "TERMINATE" in session['on_next']:
                    close_session(respondent_hash)
            except KeyError:
                print("Existing session found for respondent: {}".format(respondent_hash))

                #call nlp to add values
                r_nlp = send_msg_nlp(json.loads(session['Item']['SessionData']))
                print("response from nlp api: {}".format(json.dumps(r_nlp)))

                #send msg to backend

                r_be = send_msg_backend(r_nlp)
                print('response from back end: {}'.format(json.dumps(r_be)))

                #update json
                json_ser =process_msg(r_be, session)
                print('normalized responses to be put in sessiondb: {}'.format(json_ser))

                #update session status
                update_session(respondent_hash, json_ser)
                print('message to be sent to user: {}'.format(json_ser['question']))
                return json_ser['question']
                
            # TODO: Once we have type, pass it off to NLP to get Type, Value, Confidence

            #update_session_status(respondent_hash, json_ser)

            # TODO: Get next question fromb back end 
            # TODO: Which end point gives us next question?
            #x = get_session_status(respondent_hash)

            # TODO: Push to output SQS queue

            #return r

    except AttributeError as e:
        print("Exception: {} Stacktrace: {}".format(e, traceback.print_exc()))
        return False
    except Exception as e:
        print(e)
        return False