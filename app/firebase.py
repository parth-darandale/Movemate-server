import firebase_admin
from firebase_admin import credentials, firestore, auth
from pathlib import Path
import os
import json


firebase_creds = os.getenv("FIREBASE_CREDS")
if firebase_creds:
    cred_dict = json.loads(firebase_creds)
    cred = credentials.Certificate(cred_dict)
    firebase_admin.initialize_app(cred)
else:
    firebase_admin.initialize_app()

db = firestore.client()


def verify_token(id_token: str):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        print("Token verification failed:", str(e))
        return None
