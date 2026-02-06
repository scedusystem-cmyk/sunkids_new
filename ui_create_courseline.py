"""
Add Course Line UI Module
Provides dialog interface for academic director to create course lines
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from sheets_handler import (
    load_config_syllabus, 
    load_config_teacher, 
    load_config_courseline,
    append_courseline,
    write_master_schedule,
    clear_cache
)
from schedule_generator import generate_schedule

def generate_courseline_id(existing_courselines):
    """
    Generate new CourseLineID
    Format: C001, C002, C003...
    """
    if existing_courselines is None or len(existing_courselines) == 0:
        return "C001"
    
    # Get existing maximum number
    existing_ids = existing_courselines['CourseLineID'].tolist()
    numbers = []
    for cid in existing_ids:
        try:
            num = int(cid.replace('C', ''))
            numbers.append(num)
        except:
            continue
    
    if len(numbers) == 0:
        return "C001"
    
    next_num = max(numbers) + 1
    return f"C{next_num:03d}"

def auto_assign_classroom(df_courseline, weekday, time):
    """
    Automatically assign classroom based on concurrent courses
    
    Parameters:
    - df_courseline: Config_CourseLine DataFrame
    - weekday: Weekday (1-7)
    - time: Time (HH:MM)
    
    Returns:
    - str: Classroom name (A, B, C...)
    """
    if df_courseline is None or len(df_courseline) == 0:
        return "A"
    
    # Check how many courses at the same time
    same_time_courses = df_courseline[
        (df_courseline['Weekday'] == weekday) & 
        (df_courseline['Time'] == time)
    ]
    
    # Calculate number of used classrooms
    count = len(same_time_courses)
    
    # Assign next classroom (A, B, C, D...)
    classroom_letter = chr(65 + count)  # 65 = 'A'
    
    return classroom_letter

def show_create_courseline_dialog():
    """
    Display add course line dialog
    """
    st.subheader("Add Course Line")
    
    # Load base data
    df_syllabus = load_config_syllabus()
    df_teacher = load_config_teacher()
    df_courseline = load_config_courseline()
    
    if df_syllabus is None or len(df_syllabus) == 0:
        st.error("Please create syllabus in Config_Syllabus first")
        return
    
    if df_teacher is None or len(df_teacher) == 0:
        st.error("Please create teacher data in Config_Teacher first")
        return
    
    # Get syllabus options
    syllabus_options = df_syllabus[['SyllabusID', 'SyllabusName', 'Level_ID']].drop_duplicates()
    syllabus_dict = {}
    for _, row in syllabus_options.iterrows():
        key = f"{row['SyllabusID']} - {row['SyllabusName']} ({row['Level_ID']})"
        syllabus_dict[key] = row['SyllabusID']
    
    # Get teacher options
    teacher_options = {}
    for _, row in df_teacher.iterrows():
        key = f"{row['Teacher_ID']} - {row['Teacher_Name']}"
        teacher_options[key] = row['Teacher_ID']
    
    # Initialize session state (outside form)
    if 'time_slots' not in st.session_state:
        st.session_state.time_slots = [{'weekday': 1, 'time': '19:00'}]
    
    # Form
    with st.form("create_courseline_form"):
        # Course name
        course_name = st.text_input(
            "Course Name *",
            placeholder="e.g., Happy Class A"
        )
        
        # Select syllabus
        selected_syllabus_key = st.selectbox(
            "Select Syllabus *",
            options=list(syllabus_dict.keys())
        )
        syllabus_id = syllabus_dict[selected_syllabus_key]
        
        # Display syllabus content
        with st.expander("View Syllabus Content"):
            syllabus_detail = df_syllabus[df_syllabus['SyllabusID'] == syllabus_id]
            display_columns = ['Sequence', 'Book_Full_Name']
            if 'Unit' in syllabus_detail.columns:
                display_columns.append('Unit')
            elif 'Chapters' in syllabus_detail.columns:
                display_columns.append('Chapters')
            
            # Build display DataFrame with string conversion
            display_df = syllabus_detail[display_columns].copy()
            if 'Unit' in display_df.columns:
                display_df['Unit'] = display_df['Unit'].astype(str)
            if 'Chapters' in display_df.columns:
                display_df['Chapters'] = display_df['Chapters'].astype(str)
            
            st.dataframe(
                display_df,
                width='stretch',
                hide_index=True
            )
        
        st.markdown("---")
        
        # Schedule times (multiple slots)
        st.write("**Schedule Times *")
        
        # Hour options (0-23)
        hour_options = [f"{h:02d}:00" for h in range(24)]
        
        # Display all time slots
        time_slots = []
        for idx in range(len(st.session_state.time_slots)):
            slot = st.session_state.time_slots[idx]
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                weekday_val = st.selectbox(
                    f"Weekday {idx+1}",
                    options=[
                        ("Mon", 1), ("Tue", 2), ("Wed", 3), ("Thu", 4),
                        ("Fri", 5), ("Sat", 6), ("Sun", 7)
                    ],
                    format_func=lambda x: x[0],
                    index=slot['weekday']-1,
                    key=f"weekday_{idx}"
                )[1]
            
            with col2:
                time_val = st.selectbox(
                    f"Time {idx+1}",
                    options=hour_options,
                    index=hour_options.index(slot['time']) if slot['time'] in hour_options else 19,
                    key=f"time_{idx}"
                )
            
            with col3:
                if idx > 0:
                    if st.form_submit_button("🗑️", key=f"remove_{idx}"):
                        st.session_state.time_slots.pop(idx)
                        st.rerun()
            
            time_slots.append({'weekday': weekday_val, 'time': time_val})
        
        # Update session state
        st.session_state.time_slots = time_slots
        
        # Add time slot button (outside form, use form_submit_button)
        if len(st.session_state.time_slots) < 7:
            col_add1, col_add2, col_add3 = st.columns([1, 1, 1])
            with col_add2:
                if st.form_submit_button("Add Time Slot", use_container_width=True):
                    st.session_state.time_slots.append({'weekday': 1, 'time': '19:00'})
                    st.rerun()
        
        st.markdown("---")
        
        # Select teacher
        selected_teacher_key = st.selectbox(
            "Select Teacher *",
            options=list(teacher_options.keys())
        )
        teacher_id = teacher_options[selected_teacher_key]
        
        # Start date
        start_date = st.date_input(
            "Start Date *",
            value=datetime.now().date()
        )
        
        # Number of weeks
        weeks = st.selectbox(
            "Generate Schedule for (weeks) *",
            options=list(range(1, 53)),
            index=11  # Default 12 weeks
        )
        
        # Note
        note = st.text_area(
            "Note",
            placeholder="Optional",
            height=80
        )
        
        # Submit button
        col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
        with col_submit2:
            submitted = st.form_submit_button(
                "Create Course Line",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # Validation
            if not course_name:
                st.error("Please enter course name")
                return
            
            # Generate CourseLineID (shared by all time slots)
            courseline_id = generate_courseline_id(df_courseline)
            
            # Write to Config_CourseLine
            with st.spinner("Creating course line..."):
                all_success = True
                total_schedules = 0
                
                # Create course line for each time slot
                for idx, slot in enumerate(time_slots):
                    weekday = slot['weekday']
                    time = slot['time']
                    
                    # Auto-assign classroom
                    classroom = auto_assign_classroom(df_courseline, weekday, time)
                    
                    # Build course line data
                    courseline_data = {
                        'CourseLineID': courseline_id,
                        'CourseName': course_name,
                        'SyllabusID': syllabus_id,
                        'Weekday': weekday,
                        'Time': time,
                        'Classroom': classroom,
                        'Teacher_ID': teacher_id,
                        'Start_Date': start_date.strftime('%Y-%m-%d'),
                        'Start_Sequence': 1,
                        'Status': 'Active',
                        'Note': note
                    }
                    
                    # Write to Config_CourseLine
                    success = append_courseline(courseline_data)
                    
                    if success:
                        # Generate schedule
                        schedule = generate_schedule(
                            courseline_data, 
                            df_syllabus, 
                            weeks=weeks
                        )
                        
                        if len(schedule) > 0:
                            # Append to Master_Schedule
                            from sheets_handler import append_master_schedule
                            write_success = append_master_schedule(schedule)
                            
                            if write_success:
                                total_schedules += len(schedule)
                            else:
                                all_success = False
                        else:
                            all_success = False
                    else:
                        all_success = False
                
                if all_success:
                    st.success(f"Successfully created course line: {courseline_id}")
                    st.info(f"Generated {total_schedules} course records ({len(time_slots)} slots x {weeks} weeks)")
                    
                    # Clear cache
                    clear_cache()
                    
                    # Clear time_slots session state
                    if 'time_slots' in st.session_state:
                        del st.session_state.time_slots
                    
                    # Reload page
                    st.rerun()
                else:
                    st.error("Some time slots failed to create")
