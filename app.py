"""
Sun Kids 智慧排課管理系統 (SK-SSS)
Streamlit Web Application - 整合 Google Sheets

三種檢視模式：月/週/日
難易度顏色系統：LV1-LV5
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from config import get_spreadsheet
from sheets_handler import load_master_schedule, load_config_courseline, load_config_syllabus

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
# 難易度顏色定義
# ============================================
DIFFICULTY_COLORS = {
    1: "#FFB3BA",  # 嫩紅（簡單）
    2: "#FFCC99",  # 淡橘
    3: "#FFFFB3",  # 淺黃
    4: "#B3FFB3",  # 淺綠
    5: "#B3D9FF",  # 淺藍（困難）
}

# 統一使用黑色文字
TEXT_COLOR = "#000000"

# ============================================
# 資料載入
# ============================================
@st.cache_data(ttl=60)
def load_schedule_data():
    """
    從 Google Sheets 載入排課資料
    """
    try:
        # 測試連線
        spreadsheet = get_spreadsheet()
        if spreadsheet is None:
            st.error("❌ 無法連接到 Google Sheets - Spreadsheet 為 None")
            st.info("請檢查：1. Secrets 是否正確設定 2. Service Account 是否加入共用")
            return pd.DataFrame(), []
        
        st.success(f"✅ 成功連接到: {spreadsheet.title}")
        
        # 載入 Master_Schedule
        df_schedule = load_master_schedule()
        
        if df_schedule is None:
            st.error("❌ load_master_schedule() 返回 None")
            return pd.DataFrame(), []
        
        if len(df_schedule) == 0:
            st.warning("⚠️ Master_Schedule 無資料，請先新增課綱路線")
            return pd.DataFrame(), []
        
        st.info(f"📊 Master_Schedule 共 {len(df_schedule)} 筆資料")
        
        # 確保日期格式
        df_schedule['Date'] = pd.to_datetime(df_schedule['Date'], errors='coerce')
        df_schedule['Date'] = df_schedule['Date'].dt.strftime('%Y-%m-%d')
        
        # 載入 Config_CourseLine 取得難易度
        df_courseline = load_config_courseline()
        
        if df_courseline is not None and len(df_courseline) > 0:
            # 從 Level_ID 提取難易度
            df_schedule['Difficulty'] = df_schedule['Level_ID'].str.extract(r'(\d+)').astype(int)
        else:
            # 預設難易度
            df_schedule['Difficulty'] = 3
        
        # 載入 Config_Teacher 取得老師名字
        from sheets_handler import load_config_teacher
        df_teacher = load_config_teacher()
        
        if df_teacher is not None and len(df_teacher) > 0:
            # 合併老師名字
            df_schedule = df_schedule.merge(
                df_teacher[['Teacher_ID', 'Teacher_Name']], 
                on='Teacher_ID', 
                how='left'
            )
            # 如果有 Teacher_Name 就用，沒有就用 Teacher_ID
            df_schedule['Teacher'] = df_schedule['Teacher_Name'].fillna(df_schedule['Teacher_ID'])
        else:
            # 如果沒有老師資料，就用 Teacher_ID
            df_schedule['Teacher'] = df_schedule['Teacher_ID']
        
        # 整理欄位名稱（只 rename 需要改的）
        if 'Book_Full_Name' in df_schedule.columns:
            df_schedule = df_schedule.rename(columns={'Book_Full_Name': 'Book'})
        
        # 取得課程清單（用於篩選）
        classes = df_schedule[['CourseLineID', 'CourseName', 'Teacher', 'Difficulty']].drop_duplicates().to_dict('records')
        
        return df_schedule, classes
    
    except Exception as e:
        st.error(f"❌ 載入資料失敗: {str(e)}")
        st.error(f"錯誤類型: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame(), []

# ============================================
# 輔助函數
# ============================================
def get_month_calendar(year, month):
    """取得指定月份的日曆矩陣（6週x7天）"""
    cal = calendar.monthcalendar(year, month)
    # 補齊到 6 週
    while len(cal) < 6:
        cal.append([0] * 7)
    return cal

# ============================================
# 側邊欄
# ============================================
st.sidebar.title("📚 Sun Kids 排課系統")
st.sidebar.markdown("---")

# 登入資訊
st.sidebar.info("👤 登入身分：教務長")
st.sidebar.markdown("---")

# 檢視模式切換
view_mode = st.sidebar.radio(
    "📅 檢視模式",
    ["月", "週", "日"],
    horizontal=True
)

# 日期選擇
st.sidebar.subheader("🗓️ 日期選擇")

# 初始化 session state
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()

# 日期選擇器（使用 on_change 回調）
def on_date_change():
    selected = st.session_state.date_picker
    st.session_state.current_date = datetime.combine(selected, datetime.min.time())

selected_date = st.sidebar.date_input(
    "選擇日期",
    value=st.session_state.current_date.date(),
    key="date_picker",
    on_change=on_date_change
)

# 載入資料
df_schedule, classes = load_schedule_data()

# 篩選條件
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 篩選條件")

# 課程篩選
class_options = ['全部'] + sorted(list(set([c['CourseName'] for c in classes])))
selected_class = st.sidebar.selectbox("課程", class_options)

# 老師篩選
teacher_options = ['全部'] + sorted(list(set([c['Teacher'] for c in classes])))
selected_teacher = st.sidebar.selectbox("講師", teacher_options)

# 難易度篩選
difficulty_options = ['全部'] + [f'LV{i}' for i in range(1, 6)]
selected_difficulty = st.sidebar.selectbox("難易度", difficulty_options)

st.sidebar.markdown("---")

# 快速操作按鈕
st.sidebar.subheader("⚡ 快速操作")

# 新增課綱路線按鈕
if st.sidebar.button("➕ 新增課綱路線", use_container_width=True, type="primary"):
    st.session_state.show_create_dialog = True

# 同步班級資料按鈕（舊功能，保留但改為次要）
if st.sidebar.button("🔄 同步所有課綱路線", use_container_width=True):
    with st.spinner("正在產生排程..."):
        from schedule_generator import generate_all_schedules
        from sheets_handler import write_master_schedule, clear_cache
        
        # 載入設定檔
        df_courseline = load_config_courseline()
        df_syllabus = load_config_syllabus()
        
        if df_courseline is None or df_syllabus is None:
            st.sidebar.error("❌ 無法載入設定檔")
        elif len(df_courseline) == 0:
            st.sidebar.warning("⚠️ Config_CourseLine 無資料，請先新增課綱路線")
        elif len(df_syllabus) == 0:
            st.sidebar.warning("⚠️ Config_Syllabus 無資料")
        else:
            # 產生排程
            schedule = generate_all_schedules(df_courseline, df_syllabus, weeks=12)
            
            if len(schedule) == 0:
                st.sidebar.warning("⚠️ 無法產生排程，請檢查設定")
            else:
                # 寫入 Google Sheets
                success = write_master_schedule(schedule)
                
                if success:
                    st.sidebar.success(f"✅ 成功產生 {len(schedule)} 筆課程記錄")
                    # 清除快取，重新載入
                    clear_cache()
                    st.rerun()

if st.sidebar.button("🔄 重新載入資料", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# 顯示新增課綱路線對話框
if st.session_state.get('show_create_dialog', False):
    from ui_create_courseline import show_create_courseline_dialog
    
    # 使用彈出式容器
    with st.container():
        st.markdown("---")
        show_create_courseline_dialog()
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("❌ 取消", use_container_width=True):
                st.session_state.show_create_dialog = False
                st.rerun()

st.sidebar.markdown("---")

# ============================================
# 套用篩選
# ============================================
filtered_df = df_schedule.copy()

if selected_class != '全部':
    filtered_df = filtered_df[filtered_df['CourseName'] == selected_class]

if selected_teacher != '全部':
    filtered_df = filtered_df[filtered_df['Teacher'] == selected_teacher]

if selected_difficulty != '全部':
    difficulty_level = int(selected_difficulty.replace('LV', ''))
    filtered_df = filtered_df[filtered_df['Difficulty'] == difficulty_level]

# ============================================
# 主畫面
# ============================================

# 如果沒有資料，顯示提示訊息
if df_schedule.empty:
    st.info("📭 目前沒有課程資料，請點擊左側「➕ 新增課綱路線」開始排課")
    st.stop()

# 標題列
col_title1, col_title2, col_title3 = st.columns([1, 2, 1])

with col_title1:
    if st.button("◀", key="prev_date"):
        if view_mode == "月":
            # 上個月
            if st.session_state.current_date.month == 1:
                st.session_state.current_date = st.session_state.current_date.replace(
                    year=st.session_state.current_date.year - 1, 
                    month=12, 
                    day=1
                )
            else:
                st.session_state.current_date = st.session_state.current_date.replace(
                    month=st.session_state.current_date.month - 1, 
                    day=1
                )
        elif view_mode == "週":
            # 上週
            st.session_state.current_date = st.session_state.current_date - timedelta(days=7)
        else:
            # 昨天
            st.session_state.current_date = st.session_state.current_date - timedelta(days=1)
        st.rerun()

with col_title2:
    current_date = st.session_state.current_date
    if view_mode == "月":
        st.title(f"📅 {current_date.year}年{current_date.month}月")
    elif view_mode == "週":
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)
        st.title(f"📅 {week_start.strftime('%Y/%m/%d')} - {week_end.strftime('%m/%d')}")
    else:
        st.title(f"📅 {current_date.strftime('%Y年%m月%d日')} ({['週一','週二','週三','週四','週五','週六','週日'][current_date.weekday()]})")

with col_title3:
    if st.button("▶", key="next_date"):
        if view_mode == "月":
            # 下個月
            if st.session_state.current_date.month == 12:
                st.session_state.current_date = st.session_state.current_date.replace(
                    year=st.session_state.current_date.year + 1, 
                    month=1, 
                    day=1
                )
            else:
                st.session_state.current_date = st.session_state.current_date.replace(
                    month=st.session_state.current_date.month + 1, 
                    day=1
                )
        elif view_mode == "週":
            # 下週
            st.session_state.current_date = st.session_state.current_date + timedelta(days=7)
        else:
            # 明天
            st.session_state.current_date = st.session_state.current_date + timedelta(days=1)
        st.rerun()

st.markdown("---")

# ============================================
# 月檢視
# ============================================
if view_mode == "月":
    st.caption("💡 月模式：顯示主課程名稱 + 難易度顏色")
    
    current_date = st.session_state.current_date
    cal = get_month_calendar(current_date.year, current_date.month)
    
    header_cols = st.columns(7)
    weekdays = ['週一', '週二', '週三', '週四', '週五', '週六', '週日']
    for i, col in enumerate(header_cols):
        col.markdown(f"<div style='text-align: center; font-weight: bold; padding: 10px;'>{weekdays[i]}</div>", unsafe_allow_html=True)
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height: 180px; background-color: #f8f9fa; border: 1px solid #dee2e6;'></div>", unsafe_allow_html=True)
                else:
                    date_str = f"{current_date.year}-{current_date.month:02d}-{day:02d}"
                    day_classes = filtered_df[filtered_df['Date'] == date_str]
                    
                    # 建立格子內容
                    cards_html = ""
                    if len(day_classes) > 0:
                        for _, row in day_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            cards_html += f"<div style='background-color: {color}; color: {TEXT_COLOR}; padding: 6px; margin-bottom: 6px; border-radius: 4px; font-size: 14px; font-weight: 600;'>{row['Time']} {row['CourseName']}</div>"
                    
                    # 完整格子 HTML（固定高度）
                    cell_html = f"<div style='height: 180px; border: 1px solid #dee2e6; padding: 8px; overflow-y: auto;'><div style='font-weight: bold; margin-bottom: 8px; font-size: 16px;'>{day}</div>{cards_html}</div>"
                    st.markdown(cell_html, unsafe_allow_html=True)

# ============================================
# 週檢視
# ============================================
elif view_mode == "週":
    st.caption("💡 週模式：顯示課程名稱 + 難易度顏色 + 老師名稱")
    
    current_date = st.session_state.current_date
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    # 從資料中取得有課程的時段
    all_times = filtered_df['Time'].unique()
    time_slots = sorted([t for t in all_times if pd.notna(t)])
    
    if len(time_slots) == 0:
        st.info("📭 本週無課程")
    else:
        # 使用表格樣式
        st.markdown("""
        <style>
        .week-table-cell {
            border: 2px solid #dee2e6;
            padding: 8px;
            min-height: 100px;
            background-color: white;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # 建立表頭
        cols_header = st.columns([1] + [3]*7)
        with cols_header[0]:
            st.markdown("<div class='week-table-cell' style='font-weight: bold; text-align: center; font-size: 16px;'>時間</div>", unsafe_allow_html=True)
        for i, date in enumerate(week_dates):
            weekday = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][date.weekday()]
            with cols_header[i+1]:
                st.markdown(f"<div class='week-table-cell' style='font-weight: bold; text-align: center; font-size: 16px;'>{date.month}/{date.day}<br>{weekday}</div>", unsafe_allow_html=True)
        
        # 建立每個時段的行
        for time_slot in time_slots:
            cols = st.columns([1] + [3]*7)
            
            # 時間標籤
            with cols[0]:
                st.markdown(f"<div class='week-table-cell' style='font-weight: bold; text-align: center; font-size: 18px;'>{time_slot}</div>", unsafe_allow_html=True)
            
            # 每一天的課程
            for i, date in enumerate(week_dates):
                date_str = date.strftime('%Y-%m-%d')
                
                slot_classes = filtered_df[
                    (filtered_df['Date'] == date_str) & 
                    (filtered_df['Time'] == time_slot)
                ]
                
                with cols[i+1]:
                    cell_content = "<div class='week-table-cell'>"
                    if len(slot_classes) > 0:
                        for _, row in slot_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            cell_content += f"<div style='background-color: {color}; color: {TEXT_COLOR}; padding: 10px; border-radius: 4px; margin-bottom: 6px; border-left: 4px solid rgba(0,0,0,0.3);'><div style='font-weight: 600; font-size: 15px;'>{row['CourseName']}</div><div style='font-size: 13px; margin-top: 4px;'>{row['Teacher']}</div><div style='font-size: 13px;'>{row['Book']}</div></div>"
                    cell_content += "</div>"
                    st.markdown(cell_content, unsafe_allow_html=True)

# ============================================
# 日檢視
# ============================================
else:
    st.caption("💡 日模式：顯示完整課程資訊")
    
    current_date = st.session_state.current_date
    date_str = current_date.strftime('%Y-%m-%d')
    day_classes = filtered_df[filtered_df['Date'] == date_str].sort_values('Time')
    
    if len(day_classes) == 0:
        st.info("📭 今日無課程")
    else:
        for _, row in day_classes.iterrows():
            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
            
            # 課程卡片
            st.markdown(f"""
            <div style='
                background-color: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 8px solid {color};
            '>
                <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 16px;'>
                    <div>
                        <div style='font-size: 24px; font-weight: bold; margin-bottom: 6px;'>{row['CourseName']}</div>
                        <div style='color: #6c757d; font-size: 16px;'>難易度 LV{row['Difficulty']}</div>
                    </div>
                    <div style='text-align: right;'>
                        <div style='font-size: 22px; font-weight: bold;'>{row['Time']}</div>
                    </div>
                </div>
                <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 16px; padding: 16px; background-color: #f8f9fa; border-radius: 4px;'>
                    <div>
                        <div style='font-size: 14px; color: #6c757d; margin-bottom: 6px;'>👨‍🏫 講師</div>
                        <div style='font-weight: bold; font-size: 16px;'>{row['Teacher']}</div>
                    </div>
                    <div>
                        <div style='font-size: 14px; color: #6c757d; margin-bottom: 6px;'>📚 教材</div>
                        <div style='font-weight: bold; font-size: 16px;'>{row['Book']}</div>
                    </div>
                </div>
                <div style='margin-top: 16px; padding: 12px; background-color: {color}; border-radius: 4px;'>
                    <div style='font-size: 14px; color: #000000;'>📝 章節：{row.get('Chapters', '-')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# 底部資訊
# ============================================
st.markdown("---")
st.caption("🔧 Sun Kids 智慧排課管理系統 v1.0 | 連接 Google Sheets")
