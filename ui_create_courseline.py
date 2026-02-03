"""
新增課綱路線 UI 模組
提供對話框介面讓教務長建立課綱路線
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
    產生新的 CourseLineID
    格式：C001, C002, C003...
    """
    if existing_courselines is None or len(existing_courselines) == 0:
        return "C001"
    
    # 取得現有最大編號
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

def show_create_courseline_dialog():
    """
    顯示新增課綱路線對話框
    """
    st.subheader("➕ 新增課綱路線")
    
    # 載入基礎資料
    df_syllabus = load_config_syllabus()
    df_teacher = load_config_teacher()
    df_courseline = load_config_courseline()
    
    if df_syllabus is None or len(df_syllabus) == 0:
        st.error("❌ 請先在 Config_Syllabus 建立課綱")
        return
    
    if df_teacher is None or len(df_teacher) == 0:
        st.error("❌ 請先在 Config_Teacher 建立講師資料")
        return
    
    # 取得課綱選項
    syllabus_options = df_syllabus[['SyllabusID', 'SyllabusName', 'Level_ID']].drop_duplicates()
    syllabus_dict = {}
    for _, row in syllabus_options.iterrows():
        key = f"{row['SyllabusID']} - {row['SyllabusName']} ({row['Level_ID']})"
        syllabus_dict[key] = row['SyllabusID']
    
    # 取得老師選項
    teacher_options = {}
    for _, row in df_teacher.iterrows():
        key = f"{row['Teacher_ID']} - {row['Teacher_Name']}"
        teacher_options[key] = row['Teacher_ID']
    
    # 表單
    with st.form("create_courseline_form"):
        # 課程名稱
        course_name = st.text_input(
            "課程名稱 *",
            placeholder="例如：快樂A班",
            help="家長看到的課程名稱"
        )
        
        # 選擇課綱
        selected_syllabus_key = st.selectbox(
            "選擇課綱 *",
            options=list(syllabus_dict.keys()),
            help="決定使用哪個教材循環"
        )
        syllabus_id = syllabus_dict[selected_syllabus_key]
        
        # 顯示該課綱的教材列表
        with st.expander("📚 查看課綱內容"):
            syllabus_detail = df_syllabus[df_syllabus['SyllabusID'] == syllabus_id]
            st.dataframe(
                syllabus_detail[['Sequence', 'Book_Full_Name', 'Chapters']],
                use_container_width=True,
                hide_index=True
            )
        
        # 上課時間
        col1, col2 = st.columns(2)
        with col1:
            weekday = st.selectbox(
                "上課星期 *",
                options=[
                    ("週一", 1), ("週二", 2), ("週三", 3), ("週四", 4),
                    ("週五", 5), ("週六", 6), ("週日", 7)
                ],
                format_func=lambda x: x[0]
            )[1]
        
        with col2:
            time = st.time_input(
                "上課時間 *",
                value=datetime.strptime("19:00", "%H:%M").time(),
                help="開始時間（24小時制）"
            ).strftime("%H:%M")
        
        # 教室
        classroom = st.text_input(
            "教室 *",
            placeholder="例如：A教室",
            value="A教室"
        )
        
        # 選擇老師
        selected_teacher_key = st.selectbox(
            "選擇老師 *",
            options=list(teacher_options.keys())
        )
        teacher_id = teacher_options[selected_teacher_key]
        
        # 開課日期
        start_date = st.date_input(
            "開課日期 *",
            value=datetime.now().date(),
            help="第一次上課的日期"
        )
        
        # 起始教材
        syllabus_sequences = df_syllabus[df_syllabus['SyllabusID'] == syllabus_id].sort_values('Sequence')
        sequence_options = {}
        for _, row in syllabus_sequences.iterrows():
            key = f"{row['Sequence']} - {row['Book_Full_Name']}"
            sequence_options[key] = row['Sequence']
        
        selected_sequence_key = st.selectbox(
            "起始教材 *",
            options=list(sequence_options.keys()),
            help="從哪個教材開始上課"
        )
        start_sequence = sequence_options[selected_sequence_key]
        
        # 備註
        note = st.text_area(
            "備註",
            placeholder="選填",
            height=80
        )
        
        # 提交按鈕
        col_submit1, col_submit2, col_submit3 = st.columns([1, 1, 1])
        with col_submit2:
            submitted = st.form_submit_button(
                "✅ 建立課綱路線",
                use_container_width=True,
                type="primary"
            )
        
        if submitted:
            # 驗證
            if not course_name:
                st.error("❌ 請輸入課程名稱")
                return
            
            # 產生 CourseLineID
            courseline_id = generate_courseline_id(df_courseline)
            
            # 建立課綱路線資料
            courseline_data = {
                'CourseLineID': courseline_id,
                'CourseName': course_name,
                'SyllabusID': syllabus_id,
                'Weekday': weekday,
                'Time': time,
                'Classroom': classroom,
                'Teacher_ID': teacher_id,
                'Start_Date': start_date.strftime('%Y-%m-%d'),
                'Start_Sequence': start_sequence,
                'Status': '進行中',
                'Note': note
            }
            
            # 寫入 Config_CourseLine
            with st.spinner("正在建立課綱路線..."):
                success = append_courseline(courseline_data)
                
                if success:
                    # 產生排程
                    st.info("正在產生未來課程...")
                    schedule = generate_schedule(
                        courseline_data, 
                        df_syllabus, 
                        weeks=12
                    )
                    
                    if len(schedule) > 0:
                        # 寫入 Master_Schedule
                        write_success = write_master_schedule(schedule)
                        
                        if write_success:
                            st.success(f"✅ 成功建立課綱路線：{courseline_id}")
                            st.success(f"✅ 已產生 {len(schedule)} 筆未來課程")
                            
                            # 清除快取
                            clear_cache()
                            
                            # 重新載入頁面
                            st.rerun()
                    else:
                        st.error("❌ 無法產生課程，請檢查設定")
