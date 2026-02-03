"""
Google Sheets 連線設定模組
負責初始化 gspread 客戶端
"""

import gspread
from google.oauth2.service_account import Credentials
import streamlit as st

# Google Sheets 設定
SPREADSHEET_ID = "1gRZN5Xxlot5VINlDzYabBcuFoXrdgrb5ocENvtTFc8M"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

def get_gspread_client():
    """
    建立並返回 gspread 客戶端
    使用 Streamlit secrets 中的 Service Account 金鑰
    """
    try:
        # 從 Streamlit secrets 讀取金鑰
        creds_dict = {
            "type": st.secrets["gcp_service_account"]["type"],
            "project_id": st.secrets["gcp_service_account"]["project_id"],
            "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
            "private_key": st.secrets["gcp_service_account"]["private_key"],
            "client_email": st.secrets["gcp_service_account"]["client_email"],
            "client_id": st.secrets["gcp_service_account"]["client_id"],
            "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
            "token_uri": st.secrets["gcp_service_account"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
        }
        
        # 建立憑證
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        
        # 授權並返回客戶端
        client = gspread.authorize(creds)
        return client
    
    except Exception as e:
        st.error(f"❌ Google Sheets 連線失敗: {str(e)}")
        return None

def get_spreadsheet():
    """
    取得指定的 Google Spreadsheet 物件
    """
    client = get_gspread_client()
    if client:
        try:
            spreadsheet = client.open_by_key(SPREADSHEET_ID)
            return spreadsheet
        except Exception as e:
            st.error(f"❌ 無法開啟 Spreadsheet: {str(e)}")
            return None
    return None
