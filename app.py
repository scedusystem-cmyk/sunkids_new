"""
Sun Kids Smart Scheduling System (SK-SSS)
Streamlit Web Application - Google Sheets Integration

Three View Modes: Month/Week/Day
Difficulty Color System: LV1-LV5
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import calendar
from config import get_spreadsheet
from sheets_handler import load_master_schedule, load_config_courseline, load_config_syllabus

# ============================================
# Page Configuration
# ============================================
st.set_page_config(
    page_title="Sun Kids Scheduling System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# Difficulty Color Definition
# ============================================
DIFFICULTY_COLORS = {
    1: "#FFB3BA",  # Light red (Easy)
    2: "#FFCC99",  # Light orange
    3: "#FFFFB3",  # Light yellow
    4: "#B3FFB3",  # Light green
    5: "#B3D9FF",  # Light blue (Hard)
}

# Use black text uniformly
TEXT_COLOR = "#000000"

# ============================================
# Data Loading
# ============================================
@st.cache_data(ttl=60)
def load_schedule_data():
    """
    Load schedule data from Google Sheets
    """
    try:
        spreadsheet = get_spreadsheet()
        if spreadsheet is None:
            st.error("❌ Unable to connect to Google Sheets")
            return pd.DataFrame(), []
        
        st.success(f"✅ Connected to: {spreadsheet.title}")
        df_schedule = load_master_schedule()
        
        if df_schedule is None or len(df_schedule) == 0:
            st.warning("⚠️ No schedule data")
            return pd.DataFrame(), []
        
        # Remove duplicates
        df_schedule = df_schedule.drop_duplicates(subset=['Slot_ID'], keep='first')
        
        # Format date
        df_schedule['Date'] = pd.to_datetime(df_schedule['Date'], errors='coerce')
        df_schedule['Date'] = df_schedule['Date'].dt.strftime('%Y-%m-%d')
        
        # Load difficulty
        df_courseline = load_config_courseline()
        if df_courseline is not None and len(df_courseline) > 0:
            df_schedule['Difficulty'] = df_schedule['Level_ID'].str.extract(r'(\d+)').astype(int)
        else:
            df_schedule['Difficulty'] = 3
        
        # Load teacher names
        from sheets_handler import load_config_teacher
        df_teacher = load_config_teacher()
        if df_teacher is not None and len(df_teacher) > 0:
            df_schedule = df_schedule.merge(
                df_teacher[['Teacher_ID', 'Teacher_Name']], 
                on='Teacher_ID', 
                how='left'
            )
            df_schedule['Teacher'] = df_schedule['Teacher_Name'].fillna(df_schedule['Teacher_ID'])
        else:
            df_schedule['Teacher'] = df_schedule['Teacher_ID']
        
        # Load syllabus names
        df_syllabus = load_config_syllabus()
        if df_syllabus is not None and len(df_syllabus) > 0:
            syllabus_unique = df_syllabus[['SyllabusID', 'SyllabusName']].drop_duplicates()
            df_schedule = df_schedule.merge(syllabus_unique, on='SyllabusID', how='left')
        
        # Rename columns
        if 'Book_Full_Name' in df_schedule.columns:
            df_schedule = df_schedule.rename(columns={'Book_Full_Name': 'Book'})
        if 'Chapters' in df_schedule.columns:
            df_schedule = df_schedule.rename(columns={'Chapters': 'Unit'})
        
        # Get course list
        classes = df_schedule[['CourseLineID', 'CourseName', 'Teacher', 'Difficulty']].drop_duplicates().to_dict('records')
        
        return df_schedule, classes
    
    except Exception as e:
        st.error(f"❌ Failed to load data: {str(e)}")
        return pd.DataFrame(), []

def get_month_calendar(year, month):
    """Get calendar matrix for specified month"""
    cal = calendar.monthcalendar(year, month)
    while len(cal) < 6:
        cal.append([0] * 7)
    return cal

# ============================================
# Sidebar
# ============================================
st.sidebar.title("📚 Sun Kids Scheduling System")
st.sidebar.markdown("---")
st.sidebar.info("👤 Login: Academic Director")
st.sidebar.markdown("---")

view_mode = st.sidebar.radio("📅 View Mode", ["Month", "Week", "Day"], horizontal=True)

st.sidebar.subheader("🗓️ Date Selection")

if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()

def on_date_change():
    selected = st.session_state.date_picker
    st.session_state.current_date = datetime.combine(selected, datetime.min.time())

selected_date = st.sidebar.date_input(
    "Select Date",
    value=st.session_state.current_date.date(),
    key="date_picker",
    on_change=on_date_change
)

df_schedule, classes = load_schedule_data()

st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Conditions")

class_options = ['All'] + sorted(list(set([c['CourseName'] for c in classes])))
selected_class = st.sidebar.selectbox("Course", class_options)

teacher_options = ['All'] + sorted(list(set([c['Teacher'] for c in classes])))
selected_teacher = st.sidebar.selectbox("Teacher", teacher_options)

difficulty_options = ['All'] + [f'LV{i}' for i in range(1, 6)]
selected_difficulty = st.sidebar.selectbox("Difficulty", difficulty_options)

st.sidebar.markdown("---")
st.sidebar.subheader("⚡ Quick Operations")

if st.sidebar.button("➕ Add Course Line", use_container_width=True, type="primary"):
    st.session_state.show_create_dialog = True

if st.sidebar.button("🔄 Sync All Course Lines", use_container_width=True):
    with st.spinner("Generating schedule..."):
        from schedule_generator import generate_all_schedules
        from sheets_handler import write_master_schedule, clear_cache
        
        df_courseline = load_config_courseline()
        df_syllabus = load_config_syllabus()
        
        if df_courseline is None or df_syllabus is None:
            st.sidebar.error("❌ Unable to load config files")
        elif len(df_courseline) == 0:
            st.sidebar.warning("⚠️ No course lines")
        elif len(df_syllabus) == 0:
            st.sidebar.warning("⚠️ No syllabus data")
        else:
            schedule = generate_all_schedules(df_courseline, df_syllabus, weeks=12)
            if len(schedule) == 0:
                st.sidebar.warning("⚠️ Unable to generate schedule")
            else:
                success = write_master_schedule(schedule)
                if success:
                    st.sidebar.success(f"✅ Generated {len(schedule)} records")
                    clear_cache()
                    st.rerun()

if st.sidebar.button("🔄 Reload Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

if st.session_state.get('show_create_dialog', False):
    from ui_create_courseline import show_create_courseline_dialog
    with st.container():
        st.markdown("---")
        show_create_courseline_dialog()
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_create_dialog = False
                st.rerun()

st.sidebar.markdown("---")

# ============================================
# Apply Filters
# ============================================
filtered_df = df_schedule.copy()

if selected_class != 'All':
    filtered_df = filtered_df[filtered_df['CourseName'] == selected_class]

if selected_teacher != 'All':
    filtered_df = filtered_df[filtered_df['Teacher'] == selected_teacher]

if selected_difficulty != 'All':
    difficulty_level = int(selected_difficulty.replace('LV', ''))
    filtered_df = filtered_df[filtered_df['Difficulty'] == difficulty_level]

# ============================================
# Main Display
# ============================================
if df_schedule.empty:
    st.info("🔭 No course data available")
    st.stop()

# Title row
col_title1, col_title2, col_title3 = st.columns([1, 2, 1])

with col_title1:
    if st.button("◀", key="prev_date"):
        if view_mode == "Month":
            if st.session_state.current_date.month == 1:
                st.session_state.current_date = st.session_state.current_date.replace(
                    year=st.session_state.current_date.year - 1, month=12, day=1)
            else:
                st.session_state.current_date = st.session_state.current_date.replace(
                    month=st.session_state.current_date.month - 1, day=1)
        elif view_mode == "Week":
            st.session_state.current_date = st.session_state.current_date - timedelta(days=7)
        else:
            st.session_state.current_date = st.session_state.current_date - timedelta(days=1)
        st.rerun()

with col_title2:
    current_date = st.session_state.current_date
    if view_mode == "Month":
        st.title(f"📅 {current_date.year}-{current_date.month:02d}")
    elif view_mode == "Week":
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6)
        st.title(f"📅 {week_start.strftime('%Y/%m/%d')} - {week_end.strftime('%m/%d')}")
    else:
        weekday_names = ['Mon','Tue','Wed','Thu','Fri','Sat','Sun']
        st.title(f"📅 {current_date.strftime('%Y-%m-%d')} ({weekday_names[current_date.weekday()]})")

with col_title3:
    if st.button("▶", key="next_date"):
        if view_mode == "Month":
            if st.session_state.current_date.month == 12:
                st.session_state.current_date = st.session_state.current_date.replace(
                    year=st.session_state.current_date.year + 1, month=1, day=1)
            else:
                st.session_state.current_date = st.session_state.current_date.replace(
                    month=st.session_state.current_date.month + 1, day=1)
        elif view_mode == "Week":
            st.session_state.current_date = st.session_state.current_date + timedelta(days=7)
        else:
            st.session_state.current_date = st.session_state.current_date + timedelta(days=1)
        st.rerun()

st.markdown("---")

# ============================================
# Month View
# ============================================
if view_mode == "Month":
    st.caption("💡 Month mode: Click course card to view details")
    
    current_date = st.session_state.current_date
    cal = get_month_calendar(current_date.year, current_date.month)
    
    header_cols = st.columns(7)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
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
                    
                    # Cell with border
                    st.markdown(f"<div style='border: 1px solid #dee2e6; padding: 8px; min-height: 180px;'><div style='font-weight: bold; font-size: 16px; margin-bottom: 8px;'>{day}</div></div>", unsafe_allow_html=True)
                    
                    # Display courses with popover
                    if len(day_classes) > 0:
                        for idx, row in day_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            classroom = row.get('Classroom', '')
                            course_text = f"{row['Time']} {row['CourseName']} {classroom}"
                            
                            with st.popover(course_text, use_container_width=True):
                                # Course details in popover
                                syllabus_name = str(row.get('SyllabusName', row.get('SyllabusID', '-')))
                                st.markdown(f"**Date:** {row.get('Date', '-')} ({row.get('Weekday', '-')})")
                                st.markdown(f"**Time:** {row.get('Time', '-')}")
                                st.markdown(f"**Classroom:** {row.get('Classroom', '-')}")
                                st.markdown(f"**Difficulty:** LV{row.get('Difficulty', '-')}")
                                st.markdown(f"**Teacher:** {row.get('Teacher', '-')}")
                                st.markdown(f"**Book:** {row.get('Book', '-')}")
                                st.markdown(f"**Unit:** {row.get('Unit', '-')}")
                                st.markdown(f"**Syllabus:** {syllabus_name}")
                            
                            # Style the popover button
                            st.markdown(f"""
                            <style>
                            button[data-testid="baseButton-secondary"] {{
                                background-color: {color} !important;
                                color: {TEXT_COLOR} !important;
                                border: none !important;
                                padding: 6px !important;
                                font-weight: 600 !important;
                                font-size: 13px !important;
                            }}
                            </style>
                            """, unsafe_allow_html=True)

# ============================================
# Week View
# ============================================
elif view_mode == "Week":
    st.caption("💡 Week mode: Click course card to view details")
    
    current_date = st.session_state.current_date
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    all_times = filtered_df['Time'].unique()
    time_slots = sorted([t for t in all_times if pd.notna(t)])
    
    if len(time_slots) == 0:
        st.info("📭 No courses this week")
    else:
        # Table header
        cols_header = st.columns([1] + [3]*7)
        with cols_header[0]:
            st.markdown("<div style='font-weight: bold; text-align: center; padding: 10px;'>Time</div>", unsafe_allow_html=True)
        for i, date in enumerate(week_dates):
            weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]
            with cols_header[i+1]:
                st.markdown(f"<div style='font-weight: bold; text-align: center; padding: 10px;'>{date.month}/{date.day}<br>{weekday}</div>", unsafe_allow_html=True)
        
        # Rows for each time slot
        for time_slot in time_slots:
            cols = st.columns([1] + [3]*7)
            
            with cols[0]:
                st.markdown(f"<div style='font-weight: bold; text-align: center; padding: 10px; min-height: 100px; border: 1px solid #dee2e6;'>{time_slot}</div>", unsafe_allow_html=True)
            
            for i, date in enumerate(week_dates):
                date_str = date.strftime('%Y-%m-%d')
                slot_classes = filtered_df[
                    (filtered_df['Date'] == date_str) & 
                    (filtered_df['Time'] == time_slot)
                ]
                
                with cols[i+1]:
                    st.markdown("<div style='border: 1px solid #dee2e6; padding: 8px; min-height: 100px;'></div>", unsafe_allow_html=True)
                    
                    if len(slot_classes) > 0:
                        for idx, row in slot_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            classroom = row.get('Classroom', '')
                            course_text = f"{row['CourseName']} {classroom}"
                            
                            with st.popover(course_text, use_container_width=True):
                                syllabus_name = str(row.get('SyllabusName', row.get('SyllabusID', '-')))
                                st.markdown(f"**Date:** {row.get('Date', '-')} ({row.get('Weekday', '-')})")
                                st.markdown(f"**Time:** {row.get('Time', '-')}")
                                st.markdown(f"**Classroom:** {row.get('Classroom', '-')}")
                                st.markdown(f"**Difficulty:** LV{row.get('Difficulty', '-')}")
                                st.markdown(f"**Teacher:** {row.get('Teacher', '-')}")
                                st.markdown(f"**Book:** {row.get('Book', '-')}")
                                st.markdown(f"**Unit:** {row.get('Unit', '-')}")
                                st.markdown(f"**Syllabus:** {syllabus_name}")
                            
                            st.markdown(f"""
                            <style>
                            button[data-testid="baseButton-secondary"] {{
                                background-color: {color} !important;
                                color: {TEXT_COLOR} !important;
                                border: none !important;
                                border-left: 4px solid rgba(0,0,0,0.3) !important;
                                padding: 8px !important;
                                font-weight: 600 !important;
                                font-size: 13px !important;
                            }}
                            </style>
                            """, unsafe_allow_html=True)

# ============================================
# Day View
# ============================================
else:
    st.caption("💡 Day mode: Complete course information")
    
    current_date = st.session_state.current_date
    date_str = current_date.strftime('%Y-%m-%d')
    day_classes = filtered_df[filtered_df['Date'] == date_str].sort_values('Time')
    
    if len(day_classes) == 0:
        st.info("📭 No courses today")
    else:
        for _, row in day_classes.iterrows():
            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
            syllabus_name = str(row.get('SyllabusName', row.get('SyllabusID', '-')))
            
            card_html = f"""
<div style='background-color: white; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 8px solid {color};'>
    <div style='font-size: 20px; font-weight: bold; color: #495057; margin-bottom: 8px;'>Time: {row['Time']}</div>
    <div style='font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #212529;'>{row['CourseName']}</div>
    <div style='line-height: 2; font-size: 16px;'>
        <div><span style='color: #6c757d; font-weight: 600;'>Classroom:</span> {row.get('Classroom', '-')}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Difficulty:</span> LV{row['Difficulty']}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Teacher:</span> {row['Teacher']}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Book:</span> {row.get('Book', '-')}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Unit:</span> {row.get('Unit', '-')}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Syllabus:</span> {syllabus_name}</div>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

st.markdown("---")
st.caption("🔧 Sun Kids Smart Scheduling System v1.0 | Connected to Google Sheets")
