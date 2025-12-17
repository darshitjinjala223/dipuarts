import streamlit as st
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Scopes required
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate():
    """Authenticate using Service Account from Streamlit Secrets."""
    try:
        # Load from secrets
        service_account_info = st.secrets["gcp_service_account"]
        creds = service_account.Credentials.from_service_account_info(
            service_account_info, scopes=SCOPES)
        return creds
    except Exception as e:
        print(f"Drive Params Error: {e}")
        return None

def get_drive_service():
    """Build the Drive Service."""
    creds = authenticate()
    if creds:
        return build('drive', 'v3', credentials=creds)
    return None

def get_folder_id(service, folder_name, parent_id=None):
    """Find a folder ID by name. Create if not exists."""
    try:
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
            
        results = service.files().list(q=query, fields="files(id, name)").execute()
        items = results.get('files', [])
        
        if not items:
            # Create Folder
            file_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            if parent_id:
                file_metadata['parents'] = [parent_id]
                
            file = service.files().create(body=file_metadata, fields='id').execute()
            return file.get('id')
        else:
            return items[0]['id']
            
    except Exception as e:
        print(f"Folder Error ({folder_name}): {e}")
        return None

def upload_file(file_path, parent_folder_id):
    """Upload or Update a file in the given folder."""
    if not os.path.exists(file_path):
        return False
        
    service = get_drive_service()
    if not service:
        return False
        
    file_name = os.path.basename(file_path)
    
    try:
        # Check if file exists to update it
        query = f"name='{file_name}' and '{parent_folder_id}' in parents and trashed=false"
        results = service.files().list(q=query, fields="files(id)").execute()
        items = results.get('files', [])
        
        media = MediaFileUpload(file_path, resumable=True)
        
        if items:
            # Update
            file_id = items[0]['id']
            service.files().update(fileId=file_id, media_body=media).execute()
            print(f"Updated: {file_name}")
        else:
            # Create
            file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
            print(f"Uploaded: {file_name}")
            
        return True
    except Exception as e:
        print(f"Upload Error ({file_name}): {e}")
        return False

def sync_cloud(file_path, subfolder_name):
    """High Level Sync Function for Cloud."""
    service = get_drive_service()
    if not service:
        return False
        
    # 1. Ensure Root "Auto Biller Data" exists
    root_id = get_folder_id(service, "AutoBiller_Data")
    
    if not root_id:
        return False
        
    # 2. Ensure Subfolder exists
    target_id = get_folder_id(service, subfolder_name, parent_id=root_id)
    
    if not target_id:
        return False
        
    # 3. Upload
    return upload_file(file_path, target_id)
