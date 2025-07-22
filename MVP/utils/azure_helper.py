from azure.storage.blob import BlobServiceClient
import streamlit as st
import os
from datetime import datetime

class AzureHelper:
    def __init__(self):
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        self.connected = False
        
        if connection_string:
            try:
                self.client = BlobServiceClient.from_connection_string(connection_string)
                self.connected = True
            except:
                self.connected = False
    
    def upload_csv(self, df, filename):
        if not self.connected:
            return False, "Azure 연결 안됨"
        
        try:
            csv_string = df.to_csv(index=False, encoding='utf-8-sig')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            blob_name = f"uploads/{timestamp}_{filename}"
            
            blob_client = self.client.get_blob_client(
                container="billing-data", 
                blob=blob_name
            )
            blob_client.upload_blob(csv_string, overwrite=True)
            return True, blob_name
        except Exception as e:
            return False, str(e)