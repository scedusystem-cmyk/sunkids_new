"""
排課生成邏輯模組
根據 Config_Class 和 Config_Syllabus 自動產生 Master_Schedule
"""

import pandas as pd
from datetime import datetime, timedelta
import uuid

def generate_schedule(courseline_config, syllabus_config, weeks=12):
    """
    單一該時段的排課函式（保留以供相容性使用）
    若只有單一時段，此函式邏輯與 generate_interleaved_schedule 結果相同
    """
    return generate_interleaved_schedule([courseline_config], syllabus_config, weeks)

def generate_interleaved_schedule(courseline_configs, syllabus_config, weeks=12):
    """
    [新功能] 針對同一個 CourseLineID 的多個時段進行「交錯排課」
    
    Parameters:
    - courseline_configs: List[dict]，包含該課綱路線的所有時段設定 (Mon, Wed...)
    - syllabus_config: Config_Syllabus 的所有教材
    - weeks: 產生幾週的課程
    
    Returns:
    - DataFrame: 依日期排序並共用進度的排程資料
    """
    if not courseline_configs:
        return pd.DataFrame()

    # 取得基礎共用資訊（假設同一個 ID 的課程，課綱、老師、開始序列都是一樣的）
    base_config = courseline_configs[0]
    courseline_id = base_config['CourseLineID']
    course_name = base_config['CourseName']
    syllabus_id = base_config['SyllabusID']
    start_sequence = int(base_config.get('Start_Sequence', 1))
    
    # 取得課綱教材
    syllabus_data = syllabus_config[syllabus_config['SyllabusID'] == syllabus_id].sort_values('Sequence')
    
    if len(syllabus_data) == 0:
        return pd.DataFrame()
        
    level_id = syllabus_data.iloc[0]['Level_ID']
    total_books = len(syllabus_data)
    
    # 步驟 1: 收集所有可能的上課日期與時段資訊
    all_slots_pool = []
    
    for config in courseline_configs:
        weekday = int(config['Weekday']) # 1-7
        time = config['Time']
        classroom = config['Classroom']
        teacher_id = config['Teacher_ID']
        start_date = pd.to_datetime(config['Start_Date'])
        
        # 計算該時段的第一次上課日期
        target_weekday = weekday - 1  # 0-6
        days_ahead = target_weekday - start_date.weekday()
        if days_ahead < 0:
            days_ahead += 7
        first_class_date = start_date + timedelta(days=days_ahead)
        
        # 產生該時段未來 N 週的日期
        for week in range(weeks):
            class_date = first_class_date + timedelta(weeks=week)
            all_slots_pool.append({
                'Date': class_date,
                'Time': time,
                'Weekday_Num': class_date.weekday(), # 0-6 for sorting
                'Weekday_Str': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][class_date.weekday()],
                'Classroom': classroom,
                'Teacher_ID': teacher_id
            })
            
    # 步驟 2: 將所有日期依「日期 + 時間」排序
    # 這就是共用進度的關鍵：先排好順序，再填內容
    df_pool = pd.DataFrame(all_slots_pool)
    if df_pool.empty:
        return pd.DataFrame()
        
    df_pool = df_pool.sort_values(by=['Date', 'Time'])
    
    # 步驟 3: 依序填入課綱進度
    schedule = []
    lesson_index = start_sequence - 1
    
    for _, slot_info in df_pool.iterrows():
        # 取得教材
        book_index = lesson_index % total_books
        book_info = syllabus_data.iloc[book_index]
        
        unit_value = book_info.get('Unit', book_info.get('Chapters', ''))
        
        slot = {
            'Slot_ID': str(uuid.uuid4()),
            'CourseLineID': courseline_id,
            'CourseName': course_name,
            'SyllabusID': syllabus_id,
            'SyllabusName': book_info.get('SyllabusName', ''),
            'Date': slot_info['Date'].strftime('%Y-%m-%d'),
            'Weekday': slot_info['Weekday_Str'],
            'Time': slot_info['Time'],
            'Classroom': slot_info['Classroom'],
            'Teacher_ID': slot_info['Teacher_ID'],
            'Level_ID': level_id,
            'Book_Code': book_info.get('Book_Code', ''),
            'Book_Full_Name': book_info['Book_Full_Name'],
            'Unit': unit_value,
            'Status': '正常',
            'Note': '',
            'Created_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Updated_At': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        schedule.append(slot)
        lesson_index += 1
        
    return pd.DataFrame(schedule)

def generate_all_schedules(df_courseline, df_syllabus, weeks=12):
    """
    為所有進行中的課綱路線產生排程
    [修改] 支援將相同 CourseLineID 的多個時段合併處理
    """
    all_schedules = []
    
    # 只處理「進行中」的課綱路線
    active_courselines = df_courseline[df_courseline['Status'] == '進行中']
    
    # [關鍵修改] 依照 CourseLineID 分組，這樣才能把週一和週三視為同一組課程
    if not active_courselines.empty:
        grouped = active_courselines.groupby('CourseLineID')
        
        for courseline_id, group in grouped:
            # 將該 ID 的所有時段設定轉為 list[dict]
            courseline_configs = group.to_dict('records')
            
            # 使用新的交錯排課函式
            schedule = generate_interleaved_schedule(courseline_configs, df_syllabus, weeks)
            
            if len(schedule) > 0:
                all_schedules.append(schedule)
    
    if len(all_schedules) == 0:
        return pd.DataFrame()
    
    # 合併所有排程
    final_schedule = pd.concat(all_schedules, ignore_index=True)
    
    # 依日期和時間排序
    final_schedule['Date_Sort'] = pd.to_datetime(final_schedule['Date'])
    final_schedule = final_schedule.sort_values(['Date_Sort', 'Time']).drop('Date_Sort', axis=1)
    
    return final_schedule
