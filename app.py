"""
Sun Kids 智慧排課管理系統 (SK-SSS)
Streamlit Web Application - Phase 1 完整版

三種檢視模式：月/週/日
難易度顏色系統：LV1-LV5
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar

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
# 模擬資料
# ============================================
@st.cache_data
def load_mock_data():
    """載入模擬資料"""
    
    # 班級資料（集中在晚上 19:00-22:00，同時段會有多個課程）
    classes = [
        # 週一 19:00 - 3 個課程
        {'Class_ID': 'C001', 'Class_Name': '快樂A班', 'World_Line': 1, 'Difficulty': 3, 'Weekday': 0, 'Time': '19:00', 'Teacher': '王小明'},
        {'Class_ID': 'C002', 'Class_Name': '快樂A班', 'World_Line': 2, 'Difficulty': 5, 'Weekday': 0, 'Time': '19:00', 'Teacher': '李美華'},
        {'Class_ID': 'C003', 'Class_Name': '活力B班', 'World_Line': 1, 'Difficulty': 1, 'Weekday': 0, 'Time': '19:00', 'Teacher': '張大偉'},
        
        # 週一 20:00 - 3 個課程
        {'Class_ID': 'C004', 'Class_Name': '精英C班', 'World_Line': 1, 'Difficulty': 2, 'Weekday': 0, 'Time': '20:00', 'Teacher': '王小明'},
        {'Class_ID': 'C005', 'Class_Name': '進階D班', 'World_Line': 1, 'Difficulty': 4, 'Weekday': 0, 'Time': '20:00', 'Teacher': '李美華'},
        {'Class_ID': 'C006', 'Class_Name': '進階D班', 'World_Line': 2, 'Difficulty': 4, 'Weekday': 0, 'Time': '20:00', 'Teacher': '張大偉'},
        
        # 週一 21:00 - 2 個課程
        {'Class_ID': 'C007', 'Class_Name': '基礎E班', 'World_Line': 1, 'Difficulty': 1, 'Weekday': 0, 'Time': '21:00', 'Teacher': '王小明'},
        {'Class_ID': 'C008', 'Class_Name': '衝刺F班', 'World_Line': 1, 'Difficulty': 5, 'Weekday': 0, 'Time': '21:00', 'Teacher': '李美華'},
        
        # 週二 19:00 - 3 個課程
        {'Class_ID': 'C009', 'Class_Name': '快樂A班', 'World_Line': 3, 'Difficulty': 3, 'Weekday': 1, 'Time': '19:00', 'Teacher': '王小明'},
        {'Class_ID': 'C010', 'Class_Name': '活力B班', 'World_Line': 2, 'Difficulty': 1, 'Weekday': 1, 'Time': '19:00', 'Teacher': '李美華'},
        {'Class_ID': 'C011', 'Class_Name': '精英C班', 'World_Line': 2, 'Difficulty': 2, 'Weekday': 1, 'Time': '19:00', 'Teacher': '張大偉'},
        
        # 週二 20:00 - 3 個課程
        {'Class_ID': 'C012', 'Class_Name': '進階D班', 'World_Line': 3, 'Difficulty': 4, 'Weekday': 1, 'Time': '20:00', 'Teacher': '王小明'},
        {'Class_ID': 'C013', 'Class_Name': '基礎E班', 'World_Line': 2, 'Difficulty': 1, 'Weekday': 1, 'Time': '20:00', 'Teacher': '李美華'},
        {'Class_ID': 'C014', 'Class_Name': '衝刺F班', 'World_Line': 2, 'Difficulty': 5, 'Weekday': 1, 'Time': '20:00', 'Teacher': '張大偉'},
        
        # 週三到週五類似配置（省略，會自動產生）
        {'Class_ID': 'C015', 'Class_Name': '快樂A班', 'World_Line': 1, 'Difficulty': 3, 'Weekday': 2, 'Time': '19:00', 'Teacher': '王小明'},
        {'Class_ID': 'C016', 'Class_Name': '活力B班', 'World_Line': 1, 'Difficulty': 1, 'Weekday': 2, 'Time': '19:00', 'Teacher': '李美華'},
        {'Class_ID': 'C017', 'Class_Name': '精英C班', 'World_Line': 1, 'Difficulty': 2, 'Weekday': 3, 'Time': '20:00', 'Teacher': '張大偉'},
        {'Class_ID': 'C018', 'Class_Name': '進階D班', 'World_Line': 1, 'Difficulty': 4, 'Weekday': 4, 'Time': '21:00', 'Teacher': '王小明'},
    ]
    
    # 教材資料
    books = {
        'C001': ['P21 Book 1', 'P21 Book 2', 'Review 1'],
        'C002': ['P21 Book 1', 'P21 Book 2', 'Review 1'],
        'C003': ['TTT A1', 'TTT A2', 'TTT A3'],
        'C004': ['Disney 1', 'Disney 2', 'Story 1'],
        'C005': ['TTT C1', 'TTT C2', 'TTT D1'],
        'C006': ['TTT C1', 'TTT C2', 'TTT D1'],
        'C007': ['Basic 1', 'Basic 2'],
        'C008': ['Advanced 1', 'Advanced 2'],
        'C009': ['P21 Book 1', 'P21 Book 2'],
        'C010': ['TTT A1', 'TTT A2'],
        'C011': ['Disney 1', 'Disney 2'],
        'C012': ['TTT C1', 'TTT C2'],
        'C013': ['Basic 1', 'Basic 2'],
        'C014': ['Advanced 1', 'Advanced 2'],
        'C015': ['P21 Book 1', 'P21 Book 2'],
        'C016': ['TTT A1', 'TTT A2'],
        'C017': ['Disney 1', 'Disney 2'],
        'C018': ['TTT C1', 'TTT C2'],
    }
    
    # 產生未來 4 週的課程
    start_date = datetime(2026, 2, 3)
    all_schedules = []
    
    for cls in classes:
        days_ahead = cls['Weekday'] - start_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        first_date = start_date + timedelta(days=days_ahead)
        
        for week in range(4):
            date = first_date + timedelta(weeks=week)
            book_index = week % len(books[cls['Class_ID']])
            
            all_schedules.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Weekday': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][date.weekday()],
                'Time': cls['Time'],
                'Class_ID': cls['Class_ID'],
                'Class_Name': cls['Class_Name'],
                'World_Line': cls['World_Line'],
                'Teacher': cls['Teacher'],
                'Difficulty': cls['Difficulty'],
                'Book': books[cls['Class_ID']][book_index],
                'Status': '正常',
            })
    
    return pd.DataFrame(all_schedules), classes

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
    st.session_state.current_date = datetime(2026, 2, 3)

selected_date = st.sidebar.date_input(
    "選擇日期",
    value=st.session_state.current_date,
    key="date_picker"
)

# 同步日期選擇器的變更
if selected_date != st.session_state.current_date.date():
    st.session_state.current_date = datetime.combine(selected_date, datetime.min.time())

# 載入資料
df_schedule, classes = load_mock_data()

# 篩選條件
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 篩選條件")

# 班級篩選
class_options = ['全部'] + sorted(list(set([f"{c['Class_Name']} (世界線{c['World_Line']})" for c in classes])))
selected_class = st.sidebar.selectbox("班級", class_options)

# 老師篩選
teacher_options = ['全部'] + sorted(list(set([c['Teacher'] for c in classes])))
selected_teacher = st.sidebar.selectbox("講師", teacher_options)

# 難易度篩選
difficulty_options = ['全部'] + [f'LV{i}' for i in range(1, 6)]
selected_difficulty = st.sidebar.selectbox("難易度", difficulty_options)

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
# 套用篩選
# ============================================
filtered_df = df_schedule.copy()

if selected_class != '全部':
    class_name = selected_class.split(' (世界線')[0]
    world_line = int(selected_class.split('世界線')[1].rstrip(')'))
    filtered_df = filtered_df[
        (filtered_df['Class_Name'] == class_name) & 
        (filtered_df['World_Line'] == world_line)
    ]

if selected_teacher != '全部':
    filtered_df = filtered_df[filtered_df['Teacher'] == selected_teacher]

if selected_difficulty != '全部':
    difficulty_level = int(selected_difficulty.replace('LV', ''))
    filtered_df = filtered_df[filtered_df['Difficulty'] == difficulty_level]

# ============================================
# 主畫面
# ============================================

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
                    st.markdown("<div style='height: 120px; background-color: #f8f9fa; border: 1px solid #dee2e6;'></div>", unsafe_allow_html=True)
                else:
                    date_str = f"{current_date.year}-{current_date.month:02d}-{day:02d}"
                    day_classes = filtered_df[filtered_df['Date'] == date_str]
                    
                    content = f"<div style='min-height: 120px; border: 1px solid #dee2e6; padding: 8px;'>"
                    content += f"<div style='font-weight: bold; margin-bottom: 8px;'>{day}</div>"
                    
                    if len(day_classes) > 0:
                        for _, row in day_classes.iterrows():
                            color = DIFFICULTY_COLORS[row['Difficulty']]
                            content += f"""
                            <div style='
                                background-color: {color};
                                color: {TEXT_COLOR};
                                padding: 6px;
                                margin-bottom: 6px;
                                border-radius: 4px;
                                font-size: 15px;
                                font-weight: 600;
                                cursor: pointer;
                            '>
                                {row['Class_Name']}
                            </div>
                            """
                    
                    content += "</div>"
                    st.markdown(content, unsafe_allow_html=True)

# ============================================
# 週檢視
# ============================================
elif view_mode == "週":
    st.caption("💡 週模式：顯示課程名稱 + 難易度顏色 + 世界線 + 老師名稱")
    
    current_date = st.session_state.current_date
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    # 時間軸設定（19:00 - 22:00）
    time_slots = [f"{h:02d}:00" for h in range(19, 23)]
    
    # 找出有課程的時段（整週都沒課的時段會被隱藏）
    active_time_slots = []
    for time_slot in time_slots:
        has_class = False
        for date in week_dates:
            date_str = date.strftime('%Y-%m-%d')
            slot_classes = filtered_df[
                (filtered_df['Date'] == date_str) & 
                (filtered_df['Time'].str.startswith(time_slot.split(':')[0]))
            ]
            if len(slot_classes) > 0:
                has_class = True
                break
        if has_class:
            active_time_slots.append(time_slot)
    
    st.markdown("""
    <style>
    .week-grid {
        display: grid;
        grid-template-columns: 100px repeat(7, 1fr);
        gap: 1px;
        background-color: #dee2e6;
        border: 1px solid #dee2e6;
    }
    .time-label {
        background-color: #f8f9fa;
        padding: 12px;
        text-align: center;
        font-size: 18px;
        font-weight: 600;
        color: #000000;
    }
    .day-header {
        background-color: #ffffff;
        padding: 16px;
        text-align: center;
        font-weight: bold;
        font-size: 16px;
        border-bottom: 2px solid #dee2e6;
    }
    .time-slot {
        background-color: #ffffff;
        min-height: 80px;
        padding: 6px;
        position: relative;
    }
    .class-card {
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 6px;
        font-size: 15px;
        cursor: pointer;
        border-left: 4px solid rgba(0,0,0,0.3);
        font-weight: 600;
    }
    .class-card:hover {
        opacity: 0.8;
    }
    .class-info {
        font-size: 13px;
        font-weight: 500;
        margin-top: 4px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    header_html = "<div class='week-grid'>"
    header_html += "<div class='time-label'>時間</div>"
    for date in week_dates:
        weekday = ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][date.weekday()]
        header_html += f"<div class='day-header'>{date.month}/{date.day}<br>{weekday}</div>"
    
    # 只顯示有課程的時段
    for time_slot in active_time_slots:
        header_html += f"<div class='time-label'>{time_slot}</div>"
        
        for date in week_dates:
            date_str = date.strftime('%Y-%m-%d')
            
            slot_classes = filtered_df[
                (filtered_df['Date'] == date_str) & 
                (filtered_df['Time'].str.startswith(time_slot.split(':')[0]))
            ]
            
            header_html += "<div class='time-slot'>"
            
            if len(slot_classes) > 0:
                for _, row in slot_classes.iterrows():
                    color = DIFFICULTY_COLORS[row['Difficulty']]
                    header_html += f"""
                    <div class='class-card' style='background-color: {color}; color: {TEXT_COLOR};'>
                        <div>{row['Class_Name']}</div>
                        <div class='class-info'>世界線{row['World_Line']} | {row['Teacher']}</div>
                        <div class='class-info'>{row['Book']}</div>
                    </div>
                    """
            
            header_html += "</div>"
    
    header_html += "</div>"
    st.markdown(header_html, unsafe_allow_html=True)

# ============================================
# 日檢視
# ============================================
else:
    st.caption("💡 日模式：顯示完整課程資訊 + 每日課程內容")
    
    current_date = st.session_state.current_date
    date_str = current_date.strftime('%Y-%m-%d')
    day_classes = filtered_df[filtered_df['Date'] == date_str].sort_values('Time')
    
    if len(day_classes) == 0:
        st.info("📭 今日無課程")
    else:
        time_slots = [f"{h:02d}:00" for h in range(8, 22)]
        
        st.markdown("""
        <style>
        .day-timeline {
            position: relative;
            padding-left: 100px;
        }
        .time-marker {
            position: absolute;
            left: 0;
            width: 80px;
            text-align: right;
            padding-right: 15px;
            font-size: 12px;
            color: #6c757d;
        }
        .timeline-slot {
            border-left: 2px solid #dee2e6;
            min-height: 80px;
            padding-left: 20px;
            margin-bottom: 0;
        }
        .day-class-card {
            background-color: white;
            border-radius: 8px;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            border-left: 6px solid;
        }
        </style>
        """, unsafe_allow_html=True)
        
        timeline_html = "<div class='day-timeline'>"
        
        for time_slot in time_slots:
            timeline_html += f"<div class='time-marker' style='top: 0;'>{time_slot}</div>"
            timeline_html += "<div class='timeline-slot'>"
            
            slot_classes = day_classes[day_classes['Time'].str.startswith(time_slot.split(':')[0])]
            
            if len(slot_classes) > 0:
                for _, row in slot_classes.iterrows():
                    color = DIFFICULTY_COLORS[row['Difficulty']]
                    timeline_html += f"""
                    <div class='day-class-card' style='border-left-color: {color};'>
                        <div style='display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px;'>
                            <div>
                                <div style='font-size: 20px; font-weight: bold; margin-bottom: 4px;'>{row['Class_Name']}</div>
                                <div style='color: #6c757d; font-size: 14px;'>世界線 {row['World_Line']} | 難易度 LV{row['Difficulty']}</div>
                            </div>
                            <div style='text-align: right;'>
                                <div style='font-size: 18px; font-weight: bold;'>{row['Time']}</div>
                            </div>
                        </div>
                        <div style='display: grid; grid-template-columns: 1fr 1fr; gap: 12px; padding: 12px; background-color: #f8f9fa; border-radius: 4px;'>
                            <div>
                                <div style='font-size: 12px; color: #6c757d; margin-bottom: 4px;'>👨‍🏫 講師</div>
                                <div style='font-weight: bold;'>{row['Teacher']}</div>
                            </div>
                            <div>
                                <div style='font-size: 12px; color: #6c757d; margin-bottom: 4px;'>📚 教材</div>
                                <div style='font-weight: bold;'>{row['Book']}</div>
                            </div>
                        </div>
                        <div style='margin-top: 12px; padding: 8px; background-color: {color}; border-radius: 4px;'>
                            <div style='font-size: 12px; color: #495057;'>📝 今日課程內容：Unit 3 - Colors and Shapes</div>
                        </div>
                    </div>
                    """
            
            timeline_html += "</div>"
        
        timeline_html += "</div>"
        st.markdown(timeline_html, unsafe_allow_html=True)

# ============================================
# 底部資訊
# ============================================
st.markdown("---")
st.caption("🔧 Sun Kids 智慧排課管理系統 v1.0 | 使用模擬資料")
