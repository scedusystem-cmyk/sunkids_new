"""
Sun Kids æ™ºæ…§æŽ’èª²ç®¡ç†ç³»çµ± (SK-SSS)
Streamlit Web Application - æ•´åˆ Google Sheets

ä¸‰ç¨®æª¢è¦–æ¨¡å¼ï¼šæœˆ/é€±/æ—¥
é›£æ˜“åº¦é¡è‰²ç³»çµ±ï¼šLV1-LV5
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from config import get_spreadsheet
from sheets_handler import load_master_schedule, load_config_courseline, load_config_syllabus

# ============================================
# é é¢è¨­å®š
# ============================================
st.set_page_config(
    page_title="Sun Kids æŽ’èª²ç³»çµ±",
    page_icon="ðŸ“š",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# é›£æ˜“åº¦é¡è‰²å®šç¾©
# ============================================
DIFFICULTY_COLORS = {
    1: "#FFB3BA",  # å«©ç´…ï¼ˆç°¡å–®ï¼‰
    2: "#FFCC99",  # æ·¡æ©˜
    3: "#FFFFB3",  # æ·ºé»ƒ
    4: "#B3FFB3",  # æ·ºç¶ 
    5: "#B3D9FF",  # æ·ºè—ï¼ˆå›°é›£ï¼‰
}

# çµ±ä¸€ä½¿ç”¨é»‘è‰²æ–‡å­—
TEXT_COLOR = "#000000"

# ============================================
# è³‡æ–™è¼‰å…¥
# ============================================
@st.cache_data(ttl=60)
def load_schedule_data():
    """
    å¾ž Google Sheets è¼‰å…¥æŽ’èª²è³‡æ–™
    """
    try:
        # æ¸¬è©¦é€£ç·š
        spreadsheet = get_spreadsheet()
        if spreadsheet is None:
            st.error("âŒ ç„¡æ³•é€£æŽ¥åˆ° Google Sheets - Spreadsheet ç‚º None")
            st.info("è«‹æª¢æŸ¥ï¼š1. Secrets æ˜¯å¦æ­£ç¢ºè¨­å®š 2. Service Account æ˜¯å¦åŠ å…¥å…±ç”¨")
            return pd.DataFrame(), []
        
        st.success(f"âœ… æˆåŠŸé€£æŽ¥åˆ°: {spreadsheet.title}")
        
        # è¼‰å…¥ Master_Schedule
        df_schedule = load_master_schedule()
        
        if df_schedule is None:
            st.error("âŒ load_master_schedule() è¿”å›ž None")
            return pd.DataFrame(), []
        
        if len(df_schedule) == 0:
            st.warning("âš ï¸ Master_Schedule ç„¡è³‡æ–™ï¼Œè«‹å…ˆæ–°å¢žèª²ç¶±è·¯ç·š")
            return pd.DataFrame(), []
        
        original_count = len(df_schedule)
        st.info(f"ðŸ“Š Master_Schedule å…± {original_count} ç­†è³‡æ–™")
        
        # åŽ»é™¤é‡è¤‡è³‡æ–™ï¼ˆæ ¹æ“š Slot_IDï¼‰
        df_schedule = df_schedule.drop_duplicates(subset=['Slot_ID'], keep='first')
        
        if len(df_schedule) < original_count:
            removed = original_count - len(df_schedule)
            st.warning(f"âš ï¸ å·²ç§»é™¤ {removed} ç­†é‡è¤‡è³‡æ–™ï¼ˆSlot_ID é‡è¤‡ï¼‰")
        
        # ç¢ºä¿æ—¥æœŸæ ¼å¼
        df_schedule['Date'] = pd.to_datetime(df_schedule['Date'], errors='coerce')
        df_schedule['Date'] = df_schedule['Date'].dt.strftime('%Y-%m-%d')
        
        # è¼‰å…¥ Config_CourseLine å–å¾—é›£æ˜“åº¦
        df_courseline = load_config_courseline()
        
        if df_courseline is not None and len(df_courseline) > 0:
            # å¾ž Level_ID æå–é›£æ˜“åº¦
            df_schedule['Difficulty'] = df_schedule['Level_ID'].str.extract(r'(\d+)').astype(int)
        else:
            # é è¨­é›£æ˜“åº¦
            df_schedule['Difficulty'] = 3
        
        # è¼‰å…¥ Config_Teacher å–å¾—è€å¸«åå­—
        from sheets_handler import load_config_teacher
        df_teacher = load_config_teacher()
        
        if df_teacher is not None and len(df_teacher) > 0:
            # åˆä½µè€å¸«åå­—
            df_schedule = df_schedule.merge(
                df_teacher[['Teacher_ID', 'Teacher_Name']], 
                on='Teacher_ID', 
                how='left'
            )
            # å¦‚æžœæœ‰ Teacher_Name å°±ç”¨ï¼Œæ²’æœ‰å°±ç”¨ Teacher_ID
            df_schedule['Teacher'] = df_schedule['Teacher_Name'].fillna(df_schedule['Teacher_ID'])
        else:
            # å¦‚æžœæ²’æœ‰è€å¸«è³‡æ–™ï¼Œå°±ç”¨ Teacher_ID
            df_schedule['Teacher'] = df_schedule['Teacher_ID']
        
        # è¼‰å…¥ Config_Syllabus å–å¾—èª²ç¶±åç¨±
        df_syllabus = load_config_syllabus()
        
        if df_syllabus is not None and len(df_syllabus) > 0:
            # å–å¾—å”¯ä¸€çš„èª²ç¶±æ¸…å–®ï¼ˆSyllabusID + SyllabusNameï¼‰
            syllabus_unique = df_syllabus[['SyllabusID', 'SyllabusName']].drop_duplicates()
            # åˆä½µèª²ç¶±åç¨±
            df_schedule = df_schedule.merge(
                syllabus_unique,
                on='SyllabusID',
                how='left'
            )
        
        # æ•´ç†æ¬„ä½åç¨±ï¼ˆåª rename éœ€è¦æ”¹çš„ï¼‰
        if 'Book_Full_Name' in df_schedule.columns:
            df_schedule = df_schedule.rename(columns={'Book_Full_Name': 'Book'})
        
        # ç§»é™¤é‡è¤‡è¨˜éŒ„ï¼ˆæ ¹æ“š Slot_ID åŽ»é‡ï¼‰
        if 'Slot_ID' in df_schedule.columns:
            df_schedule = df_schedule.drop_duplicates(subset=['Slot_ID'], keep='first')
        
        # å–å¾—èª²ç¨‹æ¸…å–®ï¼ˆç”¨æ–¼ç¯©é¸ï¼‰
        classes = df_schedule[['CourseLineID', 'CourseName', 'Teacher', 'Difficulty']].drop_duplicates().to_dict('records')
        
        return df_schedule, classes
    
    except Exception as e:
        st.error(f"âŒ è¼‰å…¥è³‡æ–™å¤±æ•—: {str(e)}")
        st.error(f"éŒ¯èª¤é¡žåž‹: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame(), []

# ============================================
# è¼”åŠ©å‡½æ•¸
# ============================================
def get_month_calendar(year, month):
    """å–å¾—æŒ‡å®šæœˆä»½çš„æ—¥æ›†çŸ©é™£ï¼ˆ6é€±x7å¤©ï¼‰"""
    cal = calendar.monthcalendar(year, month)
    # è£œé½Šåˆ° 6 é€±
    while len(cal) < 6:
        cal.append([0] * 7)
    return cal

# ============================================
# å´é‚Šæ¬„
# ============================================
st.sidebar.title("ðŸ“š Sun Kids æŽ’èª²ç³»çµ±")
st.sidebar.markdown("---")

# ç™»å…¥è³‡è¨Š
st.sidebar.info("ðŸ‘¤ ç™»å…¥èº«åˆ†ï¼šæ•™å‹™é•·")
st.sidebar.markdown("---")

# æª¢è¦–æ¨¡å¼åˆ‡æ›
view_mode = st.sidebar.radio(
    "ðŸ“… æª¢è¦–æ¨¡å¼",
    ["æœˆ", "é€±", "æ—¥"],
    horizontal=True
)

# æ—¥æœŸé¸æ“‡
st.sidebar.subheader("ðŸ—“ï¸ æ—¥æœŸé¸æ“‡")

# åˆå§‹åŒ– session state
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()

# æ—¥æœŸé¸æ“‡å™¨ï¼ˆä½¿ç”¨ on_change å›žèª¿ï¼‰
def on_date_change():
    selected = st.session_state.date_picker
    st.session_state.current_date = datetime.combine(selected, datetime.min.time())

selected_date = st.sidebar.date_input(
    "é¸æ“‡æ—¥æœŸ",
    value=st.session_state.current_date.date(),
    key="date_picker",
    on_change=on_date_change
)

# è¼‰å…¥è³‡æ–™
df_schedule, classes = load_schedule_data()

# ç¯©é¸æ¢ä»¶
st.sidebar.markdown("---")
st.sidebar.subheader("ðŸ” ç¯©é¸æ¢ä»¶")

# èª²ç¨‹ç¯©é¸
class_options = ['å…¨éƒ¨'] + sorted(list(set([c['CourseName'] for c in classes])))
selected_class = st.sidebar.selectbox("èª²ç¨‹", class_options)

# è€å¸«ç¯©é¸
teacher_options = ['å…¨éƒ¨'] + sorted(list(set([c['Teacher'] for c in classes])))
selected_teacher = st.sidebar.selectbox("è¬›å¸«", teacher_options)

# é›£æ˜“åº¦ç¯©é¸
difficulty_options = ['å…¨éƒ¨'] + [f'LV{i}' for i in range(1, 6)]
selected_difficulty = st.sidebar.selectbox("é›£æ˜“åº¦", difficulty_options)

st.sidebar.markdown("---")

# å¿«é€Ÿæ“ä½œæŒ‰éˆ•
st.sidebar.subheader("âš¡ å¿«é€Ÿæ“ä½œ")

# æ–°å¢žèª²ç¶±è·¯ç·šæŒ‰éˆ•
if st.sidebar.button("âž• æ–°å¢žèª²ç¶±è·¯ç·š", use_container_width=True, type="primary"):
    st.session_state.show_create_dialog = True

# åŒæ­¥ç­ç´šè³‡æ–™æŒ‰éˆ•ï¼ˆèˆŠåŠŸèƒ½ï¼Œä¿ç•™ä½†æ”¹ç‚ºæ¬¡è¦ï¼‰
if st.sidebar.button("ðŸ”„ åŒæ­¥æ‰€æœ‰èª²ç¶±è·¯ç·š", use_container_width=True):
    with st.spinner("æ­£åœ¨ç”¢ç”ŸæŽ’ç¨‹..."):
        from schedule_generator import generate_all_schedules
        from sheets_handler import write_master_schedule, clear_cache
        
        # è¼‰å…¥è¨­å®šæª”
        df_courseline = load_config_courseline()
        df_syllabus = load_config_syllabus()
        
        if df_courseline is None or df_syllabus is None:
            st.sidebar.error("âŒ ç„¡æ³•è¼‰å…¥è¨­å®šæª”")
        elif len(df_courseline) == 0:
            st.sidebar.warning("âš ï¸ Config_CourseLine ç„¡è³‡æ–™ï¼Œè«‹å…ˆæ–°å¢žèª²ç¶±è·¯ç·š")
        elif len(df_syllabus) == 0:
            st.sidebar.warning("âš ï¸ Config_Syllabus ç„¡è³‡æ–™")
        else:
            # ç”¢ç”ŸæŽ’ç¨‹
            schedule = generate_all_schedules(df_courseline, df_syllabus, weeks=12)
            
            if len(schedule) == 0:
                st.sidebar.warning("âš ï¸ ç„¡æ³•ç”¢ç”ŸæŽ’ç¨‹ï¼Œè«‹æª¢æŸ¥è¨­å®š")
            else:
                # å¯«å…¥ Google Sheets
                success = write_master_schedule(schedule)
                
                if success:
                    st.sidebar.success(f"âœ… æˆåŠŸç”¢ç”Ÿ {len(schedule)} ç­†èª²ç¨‹è¨˜éŒ„")
                    # æ¸…é™¤å¿«å–ï¼Œé‡æ–°è¼‰å…¥
                    clear_cache()
                    st.rerun()

if st.sidebar.button("ðŸ”„ é‡æ–°è¼‰å…¥è³‡æ–™", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# é¡¯ç¤ºæ–°å¢žèª²ç¶±è·¯ç·šå°è©±æ¡†
if st.session_state.get('show_create_dialog', False):
    from ui_create_courseline import show_create_courseline_dialog
    
    # ä½¿ç”¨å½ˆå‡ºå¼å®¹å™¨
    with st.container():
        st.markdown("---")
        show_create_courseline_dialog()
        st.markdown("---")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("âŒ å–æ¶ˆ", use_container_width=True):
                st.session_state.show_create_dialog = False
                st.rerun()

st.sidebar.markdown("---")

# ============================================
# å¥—ç”¨ç¯©é¸
# ============================================
filtered_df = df_schedule.copy()

if selected_class != 'å…¨éƒ¨':
    filtered_df = filtered_df[filtered_df['CourseName'] == selected_class]

if selected_teacher != 'å…¨éƒ¨':
    filtered_df = filtered_df[filtered_df['Teacher'] == selected_teacher]

if selected_difficulty != 'å…¨éƒ¨':
    difficulty_level = int(selected_difficulty.replace('LV', ''))
    filtered_df = filtered_df[filtered_df['Difficulty'] == difficulty_level]

# ============================================
# ä¸»ç•«é¢
# ============================================

# å¦‚æžœæ²’æœ‰è³‡æ–™ï¼Œé¡¯ç¤ºæç¤ºè¨Šæ¯
if df_schedule.empty:
    st.info("ðŸ“­ ç›®å‰æ²’æœ‰èª²ç¨‹è³‡æ–™ï¼Œè«‹é»žæ“Šå·¦å´ã€Œâž• æ–°å¢žèª²ç¶±è·¯ç·šã€é–‹å§‹æŽ’èª²")
    st.stop()

# æ¨™é¡Œåˆ—
col_title1, col_title2, col_title3 = st.columns([1, 2, 1])

with col_title1:
    if st.button("â—€", key="prev_date"):
        if view_mode == "æœˆ":
            # ä¸Šå€‹æœˆ
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
        elif view_mode == "é€±":
            # ä¸Šé€±
            st.session_state.current_date = st.session_state.current_date - timedelta(days=7)
        else:
            # æ˜¨å¤©
            st.session_state.current_date = st.session_state.current_date - timedelta(days=1)
        st.rerun()

with col_title2:
    current_date = st.session_state.current_date
    if view_mode == "æœˆ":
        st.title(f"ðŸ“… {current_date.year}å¹´{current_date.month}æœˆ")
    elif view_mode == "é€±":
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)
        st.title(f"ðŸ“… {week_start.strftime('%Y/%m/%d')} - {week_end.strftime('%m/%d')}")
    else:
        st.title(f"ðŸ“… {current_date.strftime('%Yå¹´%mæœˆ%dæ—¥')} ({['é€±ä¸€','é€±äºŒ','é€±ä¸‰','é€±å››','é€±äº”','é€±å…­','é€±æ—¥'][current_date.weekday()]})")

with col_title3:
    if st.button("â–¶", key="next_date"):
        if view_mode == "æœˆ":
            # ä¸‹å€‹æœˆ
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
        elif view_mode == "é€±":
            # ä¸‹é€±
            st.session_state.current_date = st.session_state.current_date + timedelta(days=7)
        else:
            # æ˜Žå¤©
            st.session_state.current_date = st.session_state.current_date + timedelta(days=1)
        st.rerun()

st.markdown("---")

# ============================================
# æœˆæª¢è¦–
# ============================================
if view_mode == "æœˆ":
    st.caption("ðŸ’¡ æœˆæ¨¡å¼ï¼šé¡¯ç¤ºä¸»èª²ç¨‹åç¨± + é›£æ˜“åº¦é¡è‰²")
    
    current_date = st.session_state.current_date
    cal = get_month_calendar(current_date.year, current_date.month)
    
    header_cols = st.columns(7)
    weekdays = ['é€±ä¸€', 'é€±äºŒ', 'é€±ä¸‰', 'é€±å››', 'é€±äº”', 'é€±å…­', 'é€±æ—¥']
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
                    
                    # å»ºç«‹æ ¼å­å…§å®¹
                    cards_html = ""
                    if len(day_classes) > 0:
                        for _, row in day_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            classroom = row.get('Classroom', '')
                            cards_html += f"<div style='background-color: {color}; color: {TEXT_COLOR}; padding: 6px; margin-bottom: 6px; border-radius: 4px; font-size: 14px; font-weight: 600;'>{row['Time']} {row['CourseName']} {classroom}</div>"
                    
                    # å®Œæ•´æ ¼å­ HTMLï¼ˆå›ºå®šé«˜åº¦ï¼‰
                    cell_html = f"<div style='height: 180px; border: 1px solid #dee2e6; padding: 8px; overflow-y: auto;'><div style='font-weight: bold; margin-bottom: 8px; font-size: 16px;'>{day}</div>{cards_html}</div>"
                    st.markdown(cell_html, unsafe_allow_html=True)

# ============================================
# é€±æª¢è¦–
# ============================================
elif view_mode == "é€±":
    st.caption("ðŸ’¡ é€±æ¨¡å¼ï¼šé¡¯ç¤ºèª²ç¨‹åç¨± + é›£æ˜“åº¦é¡è‰² + è€å¸«åç¨±")
    
    current_date = st.session_state.current_date
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    # å¾žè³‡æ–™ä¸­å–å¾—æœ‰èª²ç¨‹çš„æ™‚æ®µ
    all_times = filtered_df['Time'].unique()
    time_slots = sorted([t for t in all_times if pd.notna(t)])
    
    if len(time_slots) == 0:
        st.info("ðŸ“­ æœ¬é€±ç„¡èª²ç¨‹")
    else:
        # è¨ˆç®—æ¯å€‹æ™‚æ®µçš„æœ€å¤§èª²ç¨‹æ•¸ï¼ˆç”¨æ–¼çµ±ä¸€é«˜åº¦ï¼‰
        time_slot_max_courses = {}
        for time_slot in time_slots:
            max_count = 0
            for date in week_dates:
                date_str = date.strftime('%Y-%m-%d')
                count = len(filtered_df[
                    (filtered_df['Date'] == date_str) & 
                    (filtered_df['Time'] == time_slot)
                ])
                max_count = max(max_count, count)
            time_slot_max_courses[time_slot] = max(max_count, 1)  # è‡³å°‘ 1
        
        # ä½¿ç”¨è¡¨æ ¼æ¨£å¼
        st.markdown("""
        <style>
        .week-table-cell {
            border: 2px solid #dee2e6;
            padding: 8px;
            background-color: white;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # å»ºç«‹è¡¨é ­
        cols_header = st.columns([1] + [3]*7)
        with cols_header[0]:
            st.markdown("<div class='week-table-cell' style='font-weight: bold; text-align: center; font-size: 16px; min-height: 60px;'>æ™‚é–“</div>", unsafe_allow_html=True)
        for i, date in enumerate(week_dates):
            weekday = ['é€±ä¸€', 'é€±äºŒ', 'é€±ä¸‰', 'é€±å››', 'é€±äº”', 'é€±å…­', 'é€±æ—¥'][date.weekday()]
            with cols_header[i+1]:
                st.markdown(f"<div class='week-table-cell' style='font-weight: bold; text-align: center; font-size: 16px; min-height: 60px;'>{date.month}/{date.day}<br>{weekday}</div>", unsafe_allow_html=True)
        
        # å»ºç«‹æ¯å€‹æ™‚æ®µçš„è¡Œ
        for time_slot in time_slots:
            cols = st.columns([1] + [3]*7)
            
            # è¨ˆç®—è©²æ™‚æ®µçš„çµ±ä¸€é«˜åº¦
            cell_height = 80 + (time_slot_max_courses[time_slot] * 110)
            
            # æ™‚é–“æ¨™ç±¤
            with cols[0]:
                st.markdown(f"<div class='week-table-cell' style='font-weight: bold; text-align: center; font-size: 18px; min-height: {cell_height}px;'>{time_slot}</div>", unsafe_allow_html=True)
            
            # æ¯ä¸€å¤©çš„èª²ç¨‹
            for i, date in enumerate(week_dates):
                date_str = date.strftime('%Y-%m-%d')
                
                slot_classes = filtered_df[
                    (filtered_df['Date'] == date_str) & 
                    (filtered_df['Time'] == time_slot)
                ]
                
                with cols[i+1]:
                    cell_content = f"<div class='week-table-cell' style='min-height: {cell_height}px;'>"
                    if len(slot_classes) > 0:
                        for _, row in slot_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            classroom = row.get('Classroom', '')
                            cell_content += f"<div style='background-color: {color}; color: {TEXT_COLOR}; padding: 10px; border-radius: 4px; margin-bottom: 6px; border-left: 4px solid rgba(0,0,0,0.3);'><div style='font-weight: 600; font-size: 15px;'>{row['CourseName']} {classroom}</div><div style='font-size: 13px; margin-top: 4px;'>{row['Teacher']}</div><div style='font-size: 13px;'>{row['Book']}</div></div>"
                    cell_content += "</div>"
                    st.markdown(cell_content, unsafe_allow_html=True)

# ============================================
# æ—¥æª¢è¦–
# ============================================
else:
    st.caption("ðŸ’¡ æ—¥æ¨¡å¼ï¼šé¡¯ç¤ºå®Œæ•´èª²ç¨‹è³‡è¨Š")
    
    current_date = st.session_state.current_date
    date_str = current_date.strftime('%Y-%m-%d')
    day_classes = filtered_df[filtered_df['Date'] == date_str].sort_values('Time')
    
    if len(day_classes) == 0:
        st.info("ðŸ“­ ä»Šæ—¥ç„¡èª²ç¨‹")
    else:
        for _, row in day_classes.iterrows():
            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
            
            # å®‰å…¨å–å¾—èª²ç¶±åç¨±
            syllabus_name = '-'
            if 'SyllabusName' in row.index and pd.notna(row['SyllabusName']):
                syllabus_name = str(row['SyllabusName'])
            elif 'SyllabusID' in row.index and pd.notna(row['SyllabusID']):
                syllabus_name = str(row['SyllabusID'])
            
            classroom = str(row.get('Classroom', '-'))
            unit = str(row.get('Unit', '-'))
            course_name = str(row['CourseName'])
            time = str(row['Time'])
            difficulty = str(row['Difficulty'])
            teacher = str(row['Teacher'])
            book = str(row.get('Book', '-'))
            
            # èª²ç¨‹å¡ç‰‡ï¼ˆå…¨éƒ¨é å·¦æŽ’åˆ—ï¼‰
            st.markdown(f"""
            <div style='
                background-color: white;
                border-radius: 8px;
                padding: 24px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border-left: 8px solid {color};
            '>
                <div style='font-size: 20px; font-weight: bold; color: #495057; margin-bottom: 8px;'>â° {time}</div>
                <div style='font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #212529;'>{course_name}</div>
                
                <div style='line-height: 2; font-size: 16px;'>
                    <div><span style='color: #6c757d; font-weight: 600;'>ðŸ“ æ•™å®¤ï¼š</span>{classroom}</div>
                    <div><span style='color: #6c757d; font-weight: 600;'>â­ é›£æ˜“åº¦ï¼š</span>LV{difficulty}</div>
                    <div><span style='color: #6c757d; font-weight: 600;'>ðŸ‘¨â€ðŸ« è¬›å¸«ï¼š</span>{teacher}</div>
                    <div><span style='color: #6c757d; font-weight: 600;'>ðŸ“š æ•™æï¼š</span>{book}</div>
                    <div><span style='color: #6c757d; font-weight: 600;'>ðŸ“ å–®å…ƒï¼š</span>{unit}</div>
                    <div><span style='color: #6c757d; font-weight: 600;'>ðŸ“‹ èª²ç¶±ï¼š</span>{syllabus_name}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================
# åº•éƒ¨è³‡è¨Š
# ============================================
st.markdown("---")
st.caption("ðŸ”§ Sun Kids æ™ºæ…§æŽ’èª²ç®¡ç†ç³»çµ± v1.0 | é€£æŽ¥ Google Sheets")
