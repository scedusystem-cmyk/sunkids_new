"""
Sun Kids 排課系統 - Google Sheets 連線測試
"""

import streamlit as st
from config import get_spreadsheet
from sheets_handler import (
    load_config_syllabus, 
    load_config_teacher, 
    load_config_class,
    load_master_schedule,
    load_lesson_log
)

st.set_page_config(
    page_title="連線測試 - Sun Kids",
    page_icon="🔧",
    layout="wide"
)

st.title("🔧 Google Sheets 連線測試")
st.markdown("---")

# 測試 1: 基本連線
st.subheader("1️⃣ 測試基本連線")
try:
    spreadsheet = get_spreadsheet()
    if spreadsheet:
        st.success(f"✅ 連線成功！")
        st.info(f"📊 檔案名稱: **{spreadsheet.title}**")
        
        worksheets = spreadsheet.worksheets()
        st.info(f"📄 工作表數量: **{len(worksheets)}**")
        
        worksheet_names = [ws.title for ws in worksheets]
        st.write("**工作表清單:**")
        for name in worksheet_names:
            st.write(f"- {name}")
    else:
        st.error("❌ 連線失敗")
except Exception as e:
    st.error(f"❌ 連線錯誤: {str(e)}")

st.markdown("---")

# 測試 2: 讀取各工作表
st.subheader("2️⃣ 測試讀取工作表")

col1, col2 = st.columns(2)

with col1:
    st.write("**Config_Syllabus**")
    try:
        df = load_config_syllabus()
        if df is not None and len(df) > 0:
            st.success(f"✅ 讀取成功 ({len(df)} 筆)")
            st.dataframe(df.head(3), use_container_width=True)
        else:
            st.warning("⚠️ 無資料或工作表不存在")
    except Exception as e:
        st.error(f"❌ 錯誤: {str(e)}")
    
    st.write("**Config_Teacher**")
    try:
        df = load_config_teacher()
        if df is not None and len(df) > 0:
            st.success(f"✅ 讀取成功 ({len(df)} 筆)")
            st.dataframe(df.head(3), use_container_width=True)
        else:
            st.warning("⚠️ 無資料或工作表不存在")
    except Exception as e:
        st.error(f"❌ 錯誤: {str(e)}")
    
    st.write("**Config_Class**")
    try:
        df = load_config_class()
        if df is not None and len(df) > 0:
            st.success(f"✅ 讀取成功 ({len(df)} 筆)")
            st.dataframe(df.head(3), use_container_width=True)
        else:
            st.warning("⚠️ 無資料或工作表不存在")
    except Exception as e:
        st.error(f"❌ 錯誤: {str(e)}")

with col2:
    st.write("**Master_Schedule**")
    try:
        df = load_master_schedule()
        if df is not None and len(df) > 0:
            st.success(f"✅ 讀取成功 ({len(df)} 筆)")
            st.dataframe(df.head(3), use_container_width=True)
        else:
            st.warning("⚠️ 無資料（正常，系統會自動產生）")
    except Exception as e:
        st.error(f"❌ 錯誤: {str(e)}")
    
    st.write("**Lesson_Log**")
    try:
        df = load_lesson_log()
        if df is not None and len(df) > 0:
            st.success(f"✅ 讀取成功 ({len(df)} 筆)")
            st.dataframe(df.head(3), use_container_width=True)
        else:
            st.warning("⚠️ 無資料（正常，講師尚未回填）")
    except Exception as e:
        st.error(f"❌ 錯誤: {str(e)}")

st.markdown("---")

# 測試 3: 權限檢查
st.subheader("3️⃣ 權限檢查")

st.info("""
**確認事項：**
1. Service Account Email 已加入 Google Sheets 共用
2. 權限至少為「編輯者」
3. 5 個工作表都已建立並有表頭
""")

if st.button("🔄 重新整理快取"):
    st.cache_data.clear()
    st.success("✅ 快取已清除，請重新載入頁面")
    st.rerun()

st.markdown("---")
st.caption("🔧 Sun Kids 智慧排課管理系統 - 連線測試工具")
