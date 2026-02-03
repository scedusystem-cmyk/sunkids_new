"""
排課生成邏輯模組
根據 Config_Class 和 Config_Syllabus 自動產生 Master_Schedule
"""

import pandas as pd
from datetime import datetime, timedelta
import uuid

def generate_schedule(courseline_config, syllabus_config, weeks=12):
    """
    根據課綱路線設定產生未來 N 週的課程排程
    
    Parameters:
    - courseline_config: Config_CourseLine 的單一路線資料 (dict)
    - syllabus_config: Config_Syllabus 的所有教材 (DataFrame)
    - weeks: 產生幾週的課程 (預設 12 週 = 3 個月)
    
    Returns:
    - DataFrame: 排程資料
    """
    schedule = []
    
    # 取得課綱路線基本資訊
    courseline_id = courseline_config['CourseLineID']
    course_name = courseline_config['CourseName']
    syllabus_id = courseline_config['SyllabusID']
    weekday = int(courseline_config['Weekday'])  # 0=週一, 6=週日
    time = courseline_config['Time']
    classroom = courseline_config['Classroom']
    teacher_id = courseline_config['Teacher_ID']
    start_date = pd.to_datetime(courseline_config['Start_Date'])
    start_sequence = int(courseline_config['Start_Sequence'])
    
    # 取得該課綱的教材循環
    syllabus_data = syllabus_config[syllabus_config['SyllabusID'] == syllabus_id].sort_values('Sequence')
    
    if len(syllabus_data) == 0:
        return pd.DataFrame()
    
    # 取得 Level_ID（從第一筆教材記錄）
    level_id = syllabus_data.iloc[0]['Level_ID']
    
    total_books = len(syllabus_data)
    
    # 計算第一次上課日期（從 start_date 開始，找到第一個符合 weekday 的日期）
    days_ahead = weekday - start_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    first_class_date = start_date + timedelta(days=days_ahead)
    
    # 產生未來 N 週的課程
    lesson_index = start_sequence - 1  # Sequence 從 1 開始，陣列從 0 開始
    
    for week in range(weeks):
        class_date = first_class_date + timedelta(weeks=week)
        
        # 取得該堂課的教材
        book_index = lesson_index % total_books
        book_info = syllabus_data.iloc[book_index]
        
        # 建立課程記錄
        slot = {
            'Slot_ID': str(uuid.uuid4()),
            'CourseLineID': courseline_id,
            'CourseName': course_name,
            'SyllabusID': syllabus_id,
            'Date': class_date.strftime('%Y-%m-%d'),
            'Weekday': ['週一', '週二', '週三', '週四', '週五', '週六', '週日'][class_date.weekday()],
            'Time': time,
            'Classroom': classroom,
            'Teacher_ID': teacher_id,
            'Level_ID': level_id,
            'Book_Code': book_info['Book_Code'],
            'Book_Full_Name': book_info['Book_Full_Name'],
            'Chapters': book_info['Chapters'],
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
    
    Parameters:
    - df_courseline: Config_CourseLine DataFrame
    - df_syllabus: Config_Syllabus DataFrame
    - weeks: 產生幾週的課程
    
    Returns:
    - DataFrame: 所有課綱路線的完整排程
    """
    all_schedules = []
    
    # 只處理「進行中」的課綱路線
    active_courselines = df_courseline[df_courseline['Status'] == '進行中']
    
    for _, courseline_row in active_courselines.iterrows():
        courseline_config = courseline_row.to_dict()
        
        # 產生該課綱路線的排程
        schedule = generate_schedule(courseline_config, df_syllabus, weeks)
        
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
