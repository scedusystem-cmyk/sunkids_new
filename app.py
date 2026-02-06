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
        # Test connection
        spreadsheet = get_spreadsheet()
        if spreadsheet is None:
            st.error("❌ Unable to connect to Google Sheets - Spreadsheet is None")
            st.info("Please check: 1. Secrets configuration 2. Service Account permissions")
            return pd.DataFrame(), []
        
        st.success(f"✅ Successfully connected to: {spreadsheet.title}")
        
        # Load Master_Schedule
        df_schedule = load_master_schedule()
        
        if df_schedule is None:
            st.error("❌ load_master_schedule() returned None")
            return pd.DataFrame(), []
        
        if len(df_schedule) == 0:
            st.warning("⚠️ Master_Schedule has no data, please add course lines first")
            return pd.DataFrame(), []
        
        original_count = len(df_schedule)
        st.info(f"📊 Master_Schedule total {original_count} records")
        
        # Remove duplicates (based on Slot_ID)
        df_schedule = df_schedule.drop_duplicates(subset=['Slot_ID'], keep='first')
        
        if len(df_schedule) < original_count:
            removed = original_count - len(df_schedule)
            st.warning(f"⚠️ Removed {removed} duplicate records (Slot_ID duplicates)")
        
        # Ensure date format
        df_schedule['Date'] = pd.to_datetime(df_schedule['Date'], errors='coerce')
        df_schedule['Date'] = df_schedule['Date'].dt.strftime('%Y-%m-%d')
        
        # Load Config_CourseLine to get difficulty
        df_courseline = load_config_courseline()
        
        if df_courseline is not None and len(df_courseline) > 0:
            # Extract difficulty from Level_ID
            df_schedule['Difficulty'] = df_schedule['Level_ID'].str.extract(r'(\d+)').astype(int)
        else:
            # Default difficulty
            df_schedule['Difficulty'] = 3
        
        # Load Config_Teacher to get teacher names
        from sheets_handler import load_config_teacher
        df_teacher = load_config_teacher()
        
        if df_teacher is not None and len(df_teacher) > 0:
            # Merge teacher names
            df_schedule = df_schedule.merge(
                df_teacher[['Teacher_ID', 'Teacher_Name']], 
                on='Teacher_ID', 
                how='left'
            )
            # Use Teacher_Name if available, otherwise use Teacher_ID
            df_schedule['Teacher'] = df_schedule['Teacher_Name'].fillna(df_schedule['Teacher_ID'])
        else:
            # If no teacher data, use Teacher_ID
            df_schedule['Teacher'] = df_schedule['Teacher_ID']
        
        # Load Config_Syllabus to get syllabus names
        df_syllabus = load_config_syllabus()
        
        if df_syllabus is not None and len(df_syllabus) > 0:
            # Get unique syllabus list (SyllabusID + SyllabusName)
            syllabus_unique = df_syllabus[['SyllabusID', 'SyllabusName']].drop_duplicates()
            # Merge syllabus names
            df_schedule = df_schedule.merge(
                syllabus_unique,
                on='SyllabusID',
                how='left'
            )
        
        # Organize column names (only rename what needs to be changed)
        if 'Book_Full_Name' in df_schedule.columns:
            df_schedule = df_schedule.rename(columns={'Book_Full_Name': 'Book'})
        
        if 'Chapters' in df_schedule.columns:
            df_schedule = df_schedule.rename(columns={'Chapters': 'Unit'})
        
        # Remove duplicate records (deduplicate by Slot_ID)
        if 'Slot_ID' in df_schedule.columns:
            df_schedule = df_schedule.drop_duplicates(subset=['Slot_ID'], keep='first')
        
        # Get course list (for filtering)
        classes = df_schedule[['CourseLineID', 'CourseName', 'Teacher', 'Difficulty']].drop_duplicates().to_dict('records')
        
        return df_schedule, classes
    
    except Exception as e:
        st.error(f"❌ Failed to load data: {str(e)}")
        st.error(f"Error type: {type(e).__name__}")
        import traceback
        st.code(traceback.format_exc())
        return pd.DataFrame(), []

# ============================================
# Helper Functions
# ============================================
def get_month_calendar(year, month):
    """Get calendar matrix for specified month (6 weeks x 7 days)"""
    cal = calendar.monthcalendar(year, month)
    # Pad to 6 weeks
    while len(cal) < 6:
        cal.append([0] * 7)
    return cal

# ============================================
# Sidebar
# ============================================
st.sidebar.title("📚 Sun Kids Scheduling System")
st.sidebar.markdown("---")

# Login info
st.sidebar.info("👤 Login: Academic Director")
st.sidebar.markdown("---")

# View mode switch
view_mode = st.sidebar.radio(
    "📅 View Mode",
    ["Month", "Week", "Day"],
    horizontal=True
)

# Date selection
st.sidebar.subheader("🗓️ Date Selection")

# Initialize session state
if 'current_date' not in st.session_state:
    st.session_state.current_date = datetime.now()

# Date picker (with on_change callback)
def on_date_change():
    selected = st.session_state.date_picker
    st.session_state.current_date = datetime.combine(selected, datetime.min.time())

selected_date = st.sidebar.date_input(
    "Select Date",
    value=st.session_state.current_date.date(),
    key="date_picker",
    on_change=on_date_change
)

# Load data
df_schedule, classes = load_schedule_data()

# Filter conditions
st.sidebar.markdown("---")
st.sidebar.subheader("🔍 Filter Conditions")

# Course filter
class_options = ['All'] + sorted(list(set([c['CourseName'] for c in classes])))
selected_class = st.sidebar.selectbox("Course", class_options)

# Teacher filter
teacher_options = ['All'] + sorted(list(set([c['Teacher'] for c in classes])))
selected_teacher = st.sidebar.selectbox("Teacher", teacher_options)

# Difficulty filter
difficulty_options = ['All'] + [f'LV{i}' for i in range(1, 6)]
selected_difficulty = st.sidebar.selectbox("Difficulty", difficulty_options)

st.sidebar.markdown("---")

# Quick operations
st.sidebar.subheader("⚡ Quick Operations")

# Add course line button
if st.sidebar.button("➕ Add Course Line", use_container_width=True, type="primary"):
    st.session_state.show_create_dialog = True

# Sync class data button (legacy feature, keep but make secondary)
if st.sidebar.button("🔄 Sync All Course Lines", use_container_width=True):
    with st.spinner("Generating schedule..."):
        from schedule_generator import generate_all_schedules
        from sheets_handler import write_master_schedule, clear_cache
        
        # Load config files
        df_courseline = load_config_courseline()
        df_syllabus = load_config_syllabus()
        
        if df_courseline is None or df_syllabus is None:
            st.sidebar.error("❌ Unable to load config files")
        elif len(df_courseline) == 0:
            st.sidebar.warning("⚠️ Config_CourseLine has no data, please add course lines first")
        elif len(df_syllabus) == 0:
            st.sidebar.warning("⚠️ Config_Syllabus has no data")
        else:
            # Generate schedule
            schedule = generate_all_schedules(df_courseline, df_syllabus, weeks=12)
            
            if len(schedule) == 0:
                st.sidebar.warning("⚠️ Unable to generate schedule, please check settings")
            else:
                # Write to Google Sheets
                success = write_master_schedule(schedule)
                
                if success:
                    st.sidebar.success(f"✅ Successfully generated {len(schedule)} course records")
                    # Clear cache and reload
                    clear_cache()
                    st.rerun()

if st.sidebar.button("🔄 Reload Data", use_container_width=True):
    st.cache_data.clear()
    st.rerun()

# Display create course line dialog
if st.session_state.get('show_create_dialog', False):
    from ui_create_courseline import show_create_courseline_dialog
    
    # Use popup container
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

# If no data, show prompt
if df_schedule.empty:
    st.info("🔭 Currently no course data, please click '➕ Add Course Line' on the left to start scheduling")
    st.stop()

# Title row
col_title1, col_title2, col_title3 = st.columns([1, 2, 1])

with col_title1:
    if st.button("◀", key="prev_date"):
        if view_mode == "Month":
            # Previous month
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
        elif view_mode == "Week":
            # Previous week
            st.session_state.current_date = st.session_state.current_date - timedelta(days=7)
        else:
            # Yesterday
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
            # Next month
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
        elif view_mode == "Week":
            # Next week
            st.session_state.current_date = st.session_state.current_date + timedelta(days=7)
        else:
            # Tomorrow
            st.session_state.current_date = st.session_state.current_date + timedelta(days=1)
        st.rerun()

st.markdown("---")

# ============================================
# Month View
# ============================================
if view_mode == "Month":
    st.caption("💡 Month mode: Display with difficulty colors")
    
    current_date = st.session_state.current_date
    cal = get_month_calendar(current_date.year, current_date.month)
    
    header_cols = st.columns(7)
    weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    for i, col in enumerate(header_cols):
        col.markdown(f"<div style='text-align: center; font-weight: bold; padding: 10px;'>{weekdays[i]}</div>", unsafe_allow_html=True)
    
    # Collect all courses in current month for selection
    month_courses = []
    
    for week in cal:
        cols = st.columns(7)
        for i, day in enumerate(week):
            with cols[i]:
                if day == 0:
                    st.markdown("<div style='height: 180px; background-color: #f8f9fa; border: 1px solid #dee2e6;'></div>", unsafe_allow_html=True)
                else:
                    date_str = f"{current_date.year}-{current_date.month:02d}-{day:02d}"
                    day_classes = filtered_df[filtered_df['Date'] == date_str]
                    
                    # Build cell HTML with colors
                    cards_html = ""
                    if len(day_classes) > 0:
                        for idx, row in day_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            classroom = row.get('Classroom', '')
                            cards_html += f"<div style='background-color: {color}; color: {TEXT_COLOR}; padding: 6px; margin-bottom: 6px; border-radius: 4px; font-size: 14px; font-weight: 600;'>{row['Time']} {row['CourseName']} {classroom}</div>"
                            # Add to selection list
                            month_courses.append((f"{date_str} {row['Time']} - {row['CourseName']} {classroom}", row.to_dict()))
                    
                    # Complete cell HTML
                    cell_html = f"<div style='height: 180px; border: 1px solid #dee2e6; padding: 8px; overflow-y: auto;'><div style='font-weight: bold; margin-bottom: 8px; font-size: 16px;'>{day}</div>{cards_html}</div>"
                    st.markdown(cell_html, unsafe_allow_html=True)
    
    # Course selection below calendar
    if len(month_courses) > 0:
        st.markdown("---")
        st.subheader("📋 View Course Details")
        course_options = ['Select a course...'] + [c[0] for c in month_courses]
        
        selected_idx = st.selectbox(
            "Choose course:",
            range(len(course_options)),
            format_func=lambda x: course_options[x],
            key="month_course_selector"
        )
        
        if selected_idx > 0:
            selected_course = month_courses[selected_idx - 1][1]
            
            # Display course details
            color = DIFFICULTY_COLORS.get(selected_course.get('Difficulty', 3), "#CCCCCC")
            
            # Safely get syllabus name
            syllabus_name = '-'
            if 'SyllabusName' in selected_course and pd.notna(selected_course.get('SyllabusName')):
                syllabus_name = str(selected_course['SyllabusName'])
            elif 'SyllabusID' in selected_course and pd.notna(selected_course.get('SyllabusID')):
                syllabus_name = str(selected_course['SyllabusID'])
            
            classroom = str(selected_course.get('Classroom', '-'))
            unit = str(selected_course.get('Unit', '-'))
            course_name = str(selected_course.get('CourseName', '-'))
            time = str(selected_course.get('Time', '-'))
            difficulty = str(selected_course.get('Difficulty', '-'))
            teacher = str(selected_course.get('Teacher', '-'))
            book = str(selected_course.get('Book', '-'))
            date = str(selected_course.get('Date', '-'))
            weekday = str(selected_course.get('Weekday', '-'))
            
            # Course detail card
            card_html = f"""
<div style='background-color: white; border-radius: 8px; padding: 24px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 8px solid {color};'>
    <div style='font-size: 20px; font-weight: bold; color: #495057; margin-bottom: 8px;'>{date} ({weekday}) {time}</div>
    <div style='font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #212529;'>{course_name}</div>
    <div style='line-height: 2; font-size: 16px;'>
        <div><span style='color: #6c757d; font-weight: 600;'>Classroom:</span> {classroom}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Difficulty:</span> LV{difficulty}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Teacher:</span> {teacher}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Book:</span> {book}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Unit:</span> {unit}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Syllabus:</span> {syllabus_name}</div>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

# ============================================
# Week View
# ============================================
elif view_mode == "Week":
    st.caption("💡 Week mode: Display with difficulty colors")
    
    current_date = st.session_state.current_date
    week_start = current_date - timedelta(days=current_date.weekday())
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    
    # Get time slots
    all_times = filtered_df['Time'].unique()
    time_slots = sorted([t for t in all_times if pd.notna(t)])
    
    # Collect all courses in current week for selection
    week_courses = []
    
    if len(time_slots) == 0:
        st.info("📭 No courses this week")
    else:
        # Table header
        cols_header = st.columns([1] + [3]*7)
        with cols_header[0]:
            st.markdown("<div style='font-weight: bold; text-align: center; font-size: 16px; padding: 10px;'>Time</div>", unsafe_allow_html=True)
        for i, date in enumerate(week_dates):
            weekday = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][date.weekday()]
            with cols_header[i+1]:
                st.markdown(f"<div style='font-weight: bold; text-align: center; font-size: 16px; padding: 10px;'>{date.month}/{date.day}<br>{weekday}</div>", unsafe_allow_html=True)
        
        # Rows for each time slot
        for time_slot in time_slots:
            cols = st.columns([1] + [3]*7)
            
            # Time label
            with cols[0]:
                st.markdown(f"<div style='font-weight: bold; text-align: center; font-size: 18px; padding: 10px; min-height: 100px; border: 1px solid #dee2e6;'>{time_slot}</div>", unsafe_allow_html=True)
            
            # Courses for each day
            for i, date in enumerate(week_dates):
                date_str = date.strftime('%Y-%m-%d')
                
                slot_classes = filtered_df[
                    (filtered_df['Date'] == date_str) & 
                    (filtered_df['Time'] == time_slot)
                ]
                
                with cols[i+1]:
                    cell_content = f"<div style='min-height: 100px; padding: 8px; border: 1px solid #dee2e6;'>"
                    if len(slot_classes) > 0:
                        for idx, row in slot_classes.iterrows():
                            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
                            classroom = row.get('Classroom', '')
                            cell_content += f"<div style='background-color: {color}; color: {TEXT_COLOR}; padding: 10px; border-radius: 4px; margin-bottom: 6px; border-left: 4px solid rgba(0,0,0,0.3);'><div style='font-weight: 600; font-size: 15px;'>{row['CourseName']} {classroom}</div><div style='font-size: 13px; margin-top: 4px;'>{row['Teacher']}</div><div style='font-size: 13px;'>{row['Book']}</div></div>"
                            # Add to selection list
                            week_courses.append((f"{date_str} {time_slot} - {row['CourseName']} {classroom}", row.to_dict()))
                    cell_content += "</div>"
                    st.markdown(cell_content, unsafe_allow_html=True)
        
        # Course selection below table
        if len(week_courses) > 0:
            st.markdown("---")
            st.subheader("📋 View Course Details")
            course_options = ['Select a course...'] + [c[0] for c in week_courses]
            
            selected_idx = st.selectbox(
                "Choose course:",
                range(len(course_options)),
                format_func=lambda x: course_options[x],
                key="week_course_selector"
            )
            
            if selected_idx > 0:
                selected_course = week_courses[selected_idx - 1][1]
                
                # Display course details
                color = DIFFICULTY_COLORS.get(selected_course.get('Difficulty', 3), "#CCCCCC")
                
                # Safely get syllabus name
                syllabus_name = '-'
                if 'SyllabusName' in selected_course and pd.notna(selected_course.get('SyllabusName')):
                    syllabus_name = str(selected_course['SyllabusName'])
                elif 'SyllabusID' in selected_course and pd.notna(selected_course.get('SyllabusID')):
                    syllabus_name = str(selected_course['SyllabusID'])
                
                classroom = str(selected_course.get('Classroom', '-'))
                unit = str(selected_course.get('Unit', '-'))
                course_name = str(selected_course.get('CourseName', '-'))
                time = str(selected_course.get('Time', '-'))
                difficulty = str(selected_course.get('Difficulty', '-'))
                teacher = str(selected_course.get('Teacher', '-'))
                book = str(selected_course.get('Book', '-'))
                date = str(selected_course.get('Date', '-'))
                weekday = str(selected_course.get('Weekday', '-'))
                
                # Course detail card
                card_html = f"""
<div style='background-color: white; border-radius: 8px; padding: 24px; margin-top: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 8px solid {color};'>
    <div style='font-size: 20px; font-weight: bold; color: #495057; margin-bottom: 8px;'>{date} ({weekday}) {time}</div>
    <div style='font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #212529;'>{course_name}</div>
    <div style='line-height: 2; font-size: 16px;'>
        <div><span style='color: #6c757d; font-weight: 600;'>Classroom:</span> {classroom}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Difficulty:</span> LV{difficulty}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Teacher:</span> {teacher}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Book:</span> {book}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Unit:</span> {unit}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Syllabus:</span> {syllabus_name}</div>
    </div>
</div>
"""
                st.markdown(card_html, unsafe_allow_html=True)

# Day View
# ============================================
else:
    st.caption("💡 Day mode: Display complete course information")
    
    current_date = st.session_state.current_date
    date_str = current_date.strftime('%Y-%m-%d')
    day_classes = filtered_df[filtered_df['Date'] == date_str].sort_values('Time')
    
    if len(day_classes) == 0:
        st.info("📭 No courses today")
    else:
        for _, row in day_classes.iterrows():
            color = DIFFICULTY_COLORS.get(row['Difficulty'], "#CCCCCC")
            
            # Safely get syllabus name
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
            
            # Course card (simplified, no emojis)
            card_html = f"""
<div style='background-color: white; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 8px solid {color};'>
    <div style='font-size: 20px; font-weight: bold; color: #495057; margin-bottom: 8px;'>Time: {time}</div>
    <div style='font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #212529;'>{course_name}</div>
    <div style='line-height: 2; font-size: 16px;'>
        <div><span style='color: #6c757d; font-weight: 600;'>Classroom:</span> {classroom}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Difficulty:</span> LV{difficulty}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Teacher:</span> {teacher}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Book:</span> {book}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Unit:</span> {unit}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Syllabus:</span> {syllabus_name}</div>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)

# ============================================
# Course Detail Popup (for Month/Week View)
# ============================================
if st.session_state.get('show_course_detail', False):
    course = st.session_state.get('selected_course', {})
    
    if course:
        color = DIFFICULTY_COLORS.get(course.get('Difficulty', 3), "#CCCCCC")
        
        # Safely get syllabus name
        syllabus_name = '-'
        if 'SyllabusName' in course and pd.notna(course.get('SyllabusName')):
            syllabus_name = str(course['SyllabusName'])
        elif 'SyllabusID' in course and pd.notna(course.get('SyllabusID')):
            syllabus_name = str(course['SyllabusID'])
        
        classroom = str(course.get('Classroom', '-'))
        unit = str(course.get('Unit', '-'))
        course_name = str(course.get('CourseName', '-'))
        time = str(course.get('Time', '-'))
        difficulty = str(course.get('Difficulty', '-'))
        teacher = str(course.get('Teacher', '-'))
        book = str(course.get('Book', '-'))
        date = str(course.get('Date', '-'))
        weekday = str(course.get('Weekday', '-'))
        
        # Modal dialog
        with st.container():
            st.markdown("---")
            
            # Close button
            col1, col2, col3 = st.columns([4, 1, 1])
            with col2:
                if st.button("✕ Close", use_container_width=True):
                    st.session_state.show_course_detail = False
                    st.rerun()
            
            # Course detail card
            card_html = f"""
<div style='background-color: white; border-radius: 8px; padding: 24px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-left: 8px solid {color};'>
    <div style='font-size: 20px; font-weight: bold; color: #495057; margin-bottom: 8px;'>{date} ({weekday}) {time}</div>
    <div style='font-size: 28px; font-weight: bold; margin-bottom: 20px; color: #212529;'>{course_name}</div>
    <div style='line-height: 2; font-size: 16px;'>
        <div><span style='color: #6c757d; font-weight: 600;'>Classroom:</span> {classroom}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Difficulty:</span> LV{difficulty}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Teacher:</span> {teacher}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Book:</span> {book}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Unit:</span> {unit}</div>
        <div><span style='color: #6c757d; font-weight: 600;'>Syllabus:</span> {syllabus_name}</div>
    </div>
</div>
"""
            st.markdown(card_html, unsafe_allow_html=True)
            
            st.markdown("---")

# ============================================
# Footer Information
# ============================================
st.markdown("---")
st.caption("🔧 Sun Kids Smart Scheduling System v1.0 | Connected to Google Sheets")

# ============================================
# Footer Information
# ============================================
st.markdown("---")
st.caption("🔧 Sun Kids Smart Scheduling System v1.0 | Connected to Google Sheets")
