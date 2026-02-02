"""
Sun Kids 智慧排課管理系統 (SK-SSS)
Streamlit Web Application - Phase 1 MVP

使用模擬資料展示基本功能
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import uuid

# ============================================
# 頁面設定
# ============================================
st.set_page_config(
    page_title="Sun Kids 排課系統",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# 模擬資料載入
# ============================================

@st.cache_data
def load_mock_data():
    """載入模擬資料"""
    
    # 教材循環資料
    syllabus_data = {
        'Level_1': [
            {'Sequence': 1, 'Book_Code': 'P21_B1_1-3', 'Chapters': '1+2+3', 'Book_Full_Name': 'P21 Book 1'},
            {'Sequence': 2, 'Book_Code': 'P21_B1_4-6', 'Chapters': '4+5+6', 'Book_Full_Name': 'P21 Book 1'},
            {'Sequence': 3, 'Book_Code': 'P21_B2_7-9', 'Chapters': '7+9', 'Book_Full_Name': 'P21 Book 2'},
            {'Sequence': 4, 'Book_Code': 'TTR_Story1_1-2', 'Chapters': '1+2', 'Book_Full_Name': 'Toy Team Review Story 1'},
            {'Sequence': 5, 'Book_Code': 'TTR_Story1_2-3', 'Chapters': '2+3', 'Book_Full_Name': 'Toy Team Review Story 1'},
            {'Sequence': 6, 'Book_Code': 'P21_B3_Review', 'Chapters': 'Review', 'Book_Full_Name': 'P21 Book 3 Review'},
        ],
        'Level_2': [
            {'Sequence': 1, 'Book_Code': 'TTT_A1', 'Chapters': '-', 'Book_Full_Name': 'The Thinking Train A1'},
            {'Sequence': 2, 'Book_Code': 'TTT_A2', 'Chapters': '-', 'Book_Full_Name': 'The Thinking Train A2'},
            {'Sequence': 3, 'Book_Code': 'TTT_A3', 'Chapters': '-', 'Book_Full_Name': 'The Thinking Train A3'},
            {'Sequence': 4, 'Book_Code': 'TTT_B1', 'Chapters': '-', 'Book_Full_Name': 'The Thinking Train B1'},
        ]
    }
    
    # 班級資料
    classes = [
        {'Class_ID': 'C001', 'Class_Name': '快樂A班', 'Level_ID': 'Level_1', 'Weekday': 0, 'Time': '19:00', 'Classroom': 'A教室', 'Teacher_ID': 'T001', 'Teacher_Name': '王小明'},
        {'Class_ID': 'C002', 'Class_Name': '活力B班', 'Level_ID': 'Level_2', 'Weekday': 1, 'Time': '19:00', 'Classroom': 'B教室', 'Teacher_ID': 'T002', 'Teacher_Name': '李美華'},
        {'Class_ID': 'C003', 'Class_Name': '精英C班', 'Level_ID': 'Level_1', 'Weekday': 4, 'Time': '20:00', 'Classroom': 'A教室', 'Teacher_ID': 'T001', 'Teacher_Name': '王小明'},
    ]
    
    # 產生排課表（未來4週）
    start_date = datetime.now()
    holidays = []
    
    all_schedules = []
    for cls in classes:
        syllabus = syllabus_data[cls['Level_ID']]
        dates = generate_dates(start_date, cls['Weekday'], weeks=4, holidays=holidays)
        
        for idx, date in enumerate(dates):
            current_book = syllabus[idx % len(syllabus)]
            
            all_schedules.append({
                'Slot_ID': str(uuid.uuid4()),
                'Date': date.strftime('%Y-%m-%d'),
                'Weekday': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][date.weekday()],
                'Time': cls['Time'],
                'Classroom': cls['Classroom'],
                'Class_ID': cls['Class_ID'],
                'Class_Name': cls['Class_Name'],
                'Teacher_ID': cls['Teacher_ID'],
                'Teacher_Name': cls['Teacher_Name'],
                'Level_ID': cls['Level_ID'],
                'Book_Code': current_book['Book_Code'],
                'Book_Name': current_book['Book_Full_Name'],
                'Chapters': current_book['Chapters'],
                'Status': '正常' if date >= datetime.now() else '已完成',
                'Note': ''
            })
    
    return pd.DataFrame(all_schedules), classes, syllabus_data

def generate_dates(start_date, weekday, weeks=4, holidays=None):
    """產生日期列表"""
    if holidays is None:
        holidays = []
    
    dates = []
    current_date = start_date
    
    days_ahead = weekday - current_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    current_date += timedelta(days=days_ahead)
    
    for _ in range(weeks):
        dates.append(current_date)
        current_date += timedelta(weeks=1)
    
    return dates

# ============================================
# 側邊欄 - 篩選器
# ============================================

st.sidebar.title("📚 Sun Kids 排課系統")
st.sidebar.markdown("---")

# 登入資訊（模擬）
st.sidebar.info("👤 登入身分：教務長")
st.sidebar.markdown("---")

# 篩選選項
st.sidebar.subheader("🔍 篩選條件")

df_schedule, classes, syllabus_data = load_mock_data()

# 日期範圍篩選
date_range = st.sidebar.date_input(
    "日期範圍",
    value=(datetime.now(), datetime.now() + timedelta(weeks=4)),
    key="date_range"
)

# 班級篩選
class_options = ['全部'] + [c['Class_Name'] for c in classes]
selected_class = st.sidebar.selectbox("班級", class_options)

# 老師篩選
teacher_options = ['全部'] + list(df_schedule['Teacher_Name'].unique())
selected_teacher = st.sidebar.selectbox("講師", teacher_options)

# 狀態篩選
status_options = ['全部', '正常', '已完成', '停課']
selected_status = st.sidebar.selectbox("狀態", status_options)

st.sidebar.markdown("---")

# 快速操作按鈕
st.sidebar.subheader("⚡ 快速操作")
if st.sidebar.button("➕ 新增班級", use_container_width=True):
    st.sidebar.info("功能開發中...")
if st.sidebar.button("🚫 標記停課日", use_container_width=True):
    st.sidebar.info("功能開發中...")
if st.sidebar.button("📋 新增補課", use_container_width=True):
    st.sidebar.info("功能開發中...")

# ============================================
# 主畫面
# ============================================

st.title("📅 排課總覽")

# 資訊卡片
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("📚 總課程數", len(df_schedule))
with col2:
    normal_count = len(df_schedule[df_schedule['Status'] == '正常'])
    st.metric("✅ 正常課程", normal_count)
with col3:
    completed_count = len(df_schedule[df_schedule['Status'] == '已完成'])
    st.metric("📝 已完成", completed_count)
with col4:
    class_count = len(classes)
    st.metric("🏫 活躍班級", class_count)

st.markdown("---")

# 套用篩選
filtered_df = df_schedule.copy()

# 日期篩選
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = filtered_df[
        (pd.to_datetime(filtered_df['Date']).dt.date >= start_date) &
        (pd.to_datetime(filtered_df['Date']).dt.date <= end_date)
    ]

# 班級篩選
if selected_class != '全部':
    filtered_df = filtered_df[filtered_df['Class_Name'] == selected_class]

# 老師篩選
if selected_teacher != '全部':
    filtered_df = filtered_df[filtered_df['Teacher_Name'] == selected_teacher]

# 狀態篩選
if selected_status != '全部':
    filtered_df = filtered_df[filtered_df['Status'] == selected_status]

# 排序
filtered_df = filtered_df.sort_values(['Date', 'Time'])

# ============================================
# 顯示模式切換
# ============================================

tab1, tab2 = st.tabs(["📋 列表檢視", "📊 統計分析"])

with tab1:
    st.subheader("課程列表")
    
    # 顯示篩選後的資料
    if len(filtered_df) == 0:
        st.warning("沒有符合條件的課程")
    else:
        # 自訂顯示欄位
        display_df = filtered_df[[
            'Date', 'Weekday', 'Time', 'Class_Name', 
            'Teacher_Name', 'Classroom', 'Book_Name', 
            'Chapters', 'Status', 'Note'
        ]].copy()
        
        # 重新命名欄位
        display_df.columns = [
            '日期', '星期', '時間', '班級', 
            '講師', '教室', '教材', 
            '章節', '狀態', '備註'
        ]
        
        # 狀態顏色標記
        def color_status(val):
            if val == '正常':
                return 'background-color: #d4edda; color: #155724'
            elif val == '已完成':
                return 'background-color: #fff3cd; color: #856404'
            elif val == '停課':
                return 'background-color: #f8d7da; color: #721c24'
            return ''
        
        styled_df = display_df.style.applymap(
            color_status, 
            subset=['狀態']
        )
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=500
        )
        
        st.caption(f"📊 顯示 {len(filtered_df)} 筆課程")

with tab2:
    st.subheader("統計分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 各班級課程數")
        class_stats = filtered_df.groupby('Class_Name').size().reset_index(name='課程數')
        st.dataframe(class_stats, use_container_width=True, hide_index=True)
    
    with col2:
        st.markdown("#### 👨‍🏫 各講師課程數")
        teacher_stats = filtered_df.groupby('Teacher_Name').size().reset_index(name='課程數')
        st.dataframe(teacher_stats, use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.markdown("#### 📚 教材使用統計")
        book_stats = filtered_df.groupby('Book_Name').size().reset_index(name='使用次數')
        st.dataframe(book_stats, use_container_width=True, hide_index=True)
    
    with col4:
        st.markdown("#### 🏫 教室使用統計")
        classroom_stats = filtered_df.groupby('Classroom').size().reset_index(name='使用次數')
        st.dataframe(classroom_stats, use_container_width=True, hide_index=True)

# ============================================
# 底部資訊
# ============================================

st.markdown("---")
st.caption("🔧 Sun Kids 智慧排課管理系統 v1.0 (MVP) | Phase 1: 基本顯示功能")
st.caption("💡 提示：目前使用模擬資料，Phase 2 將連接 Google Sheets")
