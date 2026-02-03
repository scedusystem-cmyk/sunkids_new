"""
Google Sheets 資料操作模組
負責讀取和寫入 Google Sheets 資料
"""

import pandas as pd
import streamlit as st
from config import get_spreadsheet

@st.cache_data(ttl=60)
def load_config_syllabus():
    """
    讀取 Config_Syllabus 工作表（新格式：包含 SyllabusID 和 SyllabusName）
    返回 DataFrame
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
        
        worksheet = spreadsheet.worksheet("Config_Syllabus")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    
    except Exception as e:
        st.error(f"❌ 讀取 Config_Syllabus 失敗: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_config_courseline():
    """
    讀取 Config_CourseLine 工作表
    返回 DataFrame
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
        
        worksheet = spreadsheet.worksheet("Config_CourseLine")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    
    except Exception as e:
        st.error(f"❌ 讀取 Config_CourseLine 失敗: {str(e)}")
        return None

@st.cache_data(ttl=60)
def load_config_teacher():
    """
    讀取 Config_Teacher 工作表
    返回 DataFrame
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
        
        worksheet = spreadsheet.worksheet("Config_Teacher")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    
    except Exception as e:
        st.error(f"❌ 讀取 Config_Teacher 失敗: {str(e)}")
        return None

@st.cache_data(ttl=30)
def load_master_schedule():
    """
    讀取 Master_Schedule 工作表
    返回 DataFrame
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
        
        worksheet = spreadsheet.worksheet("Master_Schedule")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        # 確保日期格式正確
        if not df.empty and 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        
        return df
    
    except Exception as e:
        st.error(f"❌ 讀取 Master_Schedule 失敗: {str(e)}")
        return None

@st.cache_data(ttl=30)
def load_lesson_log():
    """
    讀取 Lesson_Log 工作表
    返回 DataFrame
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return None
        
        worksheet = spreadsheet.worksheet("Lesson_Log")
        data = worksheet.get_all_records()
        df = pd.DataFrame(data)
        
        return df
    
    except Exception as e:
        st.error(f"❌ 讀取 Lesson_Log 失敗: {str(e)}")
        return None

def write_master_schedule(df):
    """
    寫入 Master_Schedule 工作表
    完全覆寫（含表頭）
    用於「同步所有課綱路線」按鈕
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
        
        worksheet = spreadsheet.worksheet("Master_Schedule")
        
        # 清空工作表
        worksheet.clear()
        
        # 寫入表頭
        headers = df.columns.tolist()
        worksheet.append_row(headers)
        
        # 寫入資料
        for _, row in df.iterrows():
            worksheet.append_row(row.tolist())
        
        st.success("✅ Master_Schedule 更新成功")
        return True
    
    except Exception as e:
        st.error(f"❌ 寫入 Master_Schedule 失敗: {str(e)}")
        return False

def append_master_schedule(df):
    """
    追加課程至 Master_Schedule 工作表
    不清空現有資料，只新增新課程
    用於「新增課綱路線」
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
        
        worksheet = spreadsheet.worksheet("Master_Schedule")
        
        # 取得表頭
        headers = worksheet.row_values(1)
        
        # 確保 DataFrame 欄位順序與 Google Sheets 表頭一致
        df_ordered = df[headers] if all(col in df.columns for col in headers) else df
        
        # 追加資料（不清空）
        for _, row in df_ordered.iterrows():
            worksheet.append_row(row.tolist())
        
        st.success(f"✅ 成功新增 {len(df)} 筆課程")
        return True
    
    except Exception as e:
        st.error(f"❌ 追加 Master_Schedule 失敗: {str(e)}")
        return False

def append_lesson_log(log_data):
    """
    新增一筆講師回填記錄至 Lesson_Log
    log_data: dict，包含所有欄位
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
        
        worksheet = spreadsheet.worksheet("Lesson_Log")
        
        # 取得表頭
        headers = worksheet.row_values(1)
        
        # 依照表頭順序建立資料列
        row_data = [log_data.get(header, "") for header in headers]
        
        # 新增資料
        worksheet.append_row(row_data)
        
        st.success("✅ 講師回填記錄已儲存")
        return True
    
    except Exception as e:
        st.error(f"❌ 新增 Lesson_Log 失敗: {str(e)}")
        return False

def append_courseline(courseline_data):
    """
    新增一筆課綱路線至 Config_CourseLine
    courseline_data: dict，包含所有欄位
    """
    try:
        spreadsheet = get_spreadsheet()
        if not spreadsheet:
            return False
        
        worksheet = spreadsheet.worksheet("Config_CourseLine")
        
        # 取得表頭
        headers = worksheet.row_values(1)
        
        # 依照表頭順序建立資料列
        row_data = [courseline_data.get(header, "") for header in headers]
        
        # 新增資料
        worksheet.append_row(row_data)
        
        st.success("✅ 課綱路線建立成功")
        return True
    
    except Exception as e:
        st.error(f"❌ 新增課綱路線失敗: {str(e)}")
        return False

def clear_cache():
    """
    清除所有快取，強制重新載入資料
    """
    st.cache_data.clear()
