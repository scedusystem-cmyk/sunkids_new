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

def auto_assign_classroom(df_courseline, weekday, time):
    """
    根據同時段課程數量自動分配教室
    
    Parameters:
    - df_courseline: Config_CourseLine DataFrame
    - weekday: 星期（1-7）
    - time: 時間（HH:MM）
    
    Returns:
    - str: 教室名稱（A教室、B教室...）
    """
    if df_courseline is None or len(df_courseline) == 0:
        return "A教室"
    
    # 檢查同時段已有幾堂課
    same_time_courses = df_courseline[
        (df_courseline['Weekday'] == weekday) & 
        (df_courseline['Time'] == time)
    ]
    
    # 計算已使用的教室數量
    count = len(same_time_courses)
    
    # 分配下一個教室（A, B, C, D...）
    classroom_letter = chr(65 + count)  # 65 = 'A'
    
    return f"{classroom_letter}教室"

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
    
    # 初始化 session state（必須在 form 外部）
    if 'time_slots' not in st.session_state:
        st.session_state.time_slots = [{'weekday': 1, 'time': '19:00'}]
    
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
            # 相容舊欄位名稱
            display_columns = ['Sequence', 'Book_Full_Name']
            if 'Unit' in syllabus_detail.columns:
                display_columns.append('Unit')
            elif 'Chapters' in syllabus_detail.columns:
                display_columns.append('Chapters')
            
            # 建立顯示用的 DataFrame 並強制轉換為字串
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
        
        # 上課時間（支援多時段）
        st.write("**上課時間 ***")
        st.caption("一個課綱路線可設定多個上課時段（例如：週一19:00 + 週三19:00）")
        
        # 顯示所有時段
        time_slots = []
        slots_to_remove = []
        
        for idx in range(len(st.session_state.time_slots)):
            slot = st.session_state.time_slots[idx]
            col1, col2, col3 = st.columns([2, 2, 1])
            
            with col1:
                weekday_val = st.selectbox(
                    f"星期 {idx+1}",
                    options=[
                        ("週一", 1), ("週二", 2), ("週三", 3), ("週四", 4),
                        ("週五", 5), ("週六", 6), ("週日", 7)
                    ],
                    format_func=lambda x: x[0],
                    index=slot['weekday']-1,
                    key=f"weekday_{idx}"
                )[1]
            
            with col2:
                time_val = st.time_input(
                    f"時間 {idx+1}",
                    value=datetime.strptime(slot['time'], "%H:%M").time(),
                    key=f"time_{idx}"
                ).strftime("%H:%M")
            
            with col3:
                if idx > 0:
                    if st.button("🗑️", key=f"remove_{idx}", help="刪除此時段"):
                        slots_to_remove.append(idx)
            
            time_slots.append({'weekday': weekday_val, 'time': time_val})
        
        # 處理刪除
        if slots_to_remove:
            for idx in reversed(slots_to_remove):
                st.session_state.time_slots.pop(idx)
            st.rerun()
        else:
            # 更新 session state
            st.session_state.time_slots = time_slots
        
        # 新增時段按鈕
        if len(st.session_state.time_slots) < 7:
            if st.button("➕ 新增時段", use_container_width=True):
                st.session_state.time_slots.append({'weekday': 1, 'time': '19:00'})
                st.rerun()
        
        st.markdown("---")
        
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
            
            # 產生 CourseLineID（所有時段共用）
            courseline_id = generate_courseline_id(df_courseline)
            
            # 寫入 Config_CourseLine
            with st.spinner("正在建立課綱路線..."):
                all_success = True
                total_schedules = 0
                
                # 為每個時段建立課綱路線
                for idx, slot in enumerate(time_slots):
                    weekday = slot['weekday']
                    time = slot['time']
                    
                    # 自動分配教室
                    classroom = auto_assign_classroom(df_courseline, weekday, time)
                    
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
                        'Start_Sequence': 1,
                        'Status': '進行中',
                        'Note': note
                    }
                    
                    # 寫入 Config_CourseLine
                    success = append_courseline(courseline_data)
                    
                    if success:
                        # 產生排程
                        schedule = generate_schedule(
                            courseline_data, 
                            df_syllabus, 
                            weeks=12
                        )
                        
                        if len(schedule) > 0:
                            # 追加至 Master_Schedule
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
                    st.success(f"✅ 成功建立課綱路線：{courseline_id}")
                    st.info(f"📊 共產生 {total_schedules} 筆課程（{len(time_slots)} 個時段 x 12 週）")
                    
                    # 清除快取
                    clear_cache()
                    
                    # 清除 time_slots session state
                    if 'time_slots' in st.session_state:
                        del st.session_state.time_slots
                    
                    # 重新載入頁面
                    st.rerun()
                else:
                    st.error("❌ 部分時段建立失敗，請檢查錯誤訊息")
