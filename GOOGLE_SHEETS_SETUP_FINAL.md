# Google Sheets 結構更新指南 - 最終版

## 總覽

**重要：大部分工作表由系統自動產生，你只需要設定基礎資料！**

### 需要手動填寫（基礎資料）
1. ✅ Config_Syllabus - 課綱定義
2. ✅ Config_Teacher - 講師資料

### 只填表頭，系統自動產生
3. ⬜ Config_CourseLine - 課綱路線（在 UI 對話框建立）
4. ⬜ Master_Schedule - 排課總表（系統自動產生）
5. ⬜ Lesson_Log - 回填記錄（講師回填）

**操作方式：**
- 在 Google Sheets 填好課綱和老師
- 其他都在 Streamlit UI 操作
- 點「新增課綱路線」按鈕 → 填對話框 → 系統自動產生

---

## 工作表 1：Config_Syllabus（課綱定義表）

### 操作步驟
1. 如果已有 Config_Syllabus，清空所有資料
2. 如果沒有，新建工作表命名為 `Config_Syllabus`

### 表頭（第1行）
```
SyllabusID	SyllabusName	Level_ID	Sequence	Book_Code	Chapters	Book_Full_Name
```

### 範例資料（第2行開始，用 Tab 分隔）
```
SYL001	幼兒英語啟蒙	Level_1	1	P21_B1_1-3	1+2+3	P21 Book 1
SYL001	幼兒英語啟蒙	Level_1	2	P21_B1_4-6	4+5+6	P21 Book 1
SYL001	幼兒英語啟蒙	Level_1	3	P21_B2_7-9	7+9	P21 Book 2
SYL001	幼兒英語啟蒙	Level_1	4	TTR_Story1_1-2	1+2	Toy Team Review Story 1
SYL001	幼兒英語啟蒙	Level_1	5	P21_B3_Review	Review	P21 Book 3 Review
SYL002	兒童進階閱讀	Level_2	1	TTT_A1	-	The Thinking Train A1
SYL002	兒童進階閱讀	Level_2	2	TTT_A2	-	The Thinking Train A2
SYL002	兒童進階閱讀	Level_2	3	TTT_A3	-	The Thinking Train A3
SYL002	兒童進階閱讀	Level_2	4	TTT_B1	-	The Thinking Train B1
SYL002	兒童進階閱讀	Level_2	5	TTT_Review	Review	The Thinking Train Review
```

---

## 工作表 2：Config_Teacher（講師資料）- 保持不變

### 操作步驟
如果已有資料，保持不變。如果沒有，新建並填入。

### 表頭（第1行）
```
Teacher_ID	Teacher_Name	Qualified_Levels	Status	Note
```

### 範例資料（第2行開始）
```
T001	王小明	Level_1,Level_2,Level_3	在職	資深講師
T002	李美華	Level_1,Level_2	在職	
T003	張大偉	Level_3,Level_4,Level_5	在職	外籍講師
T004	陳雅婷	Level_1	在職	新進講師
```

---

## 工作表 3：Config_CourseLine（課綱路線設定表）- 新建

### 操作步驟
1. 刪除舊的 `Config_Class`（如果有）
2. 新建工作表命名為 `Config_CourseLine`

### 表頭（第1行）
```
CourseLineID	CourseName	SyllabusID	Weekday	Time	Classroom	Teacher_ID	Start_Date	Start_Sequence	Status	Note
```

### 資料
```
（第2行開始留空，等系統自動產生）
```

**重要：**
- CourseLineID 由系統自動產生（C001, C002...）
- 教務長在 UI 建立課綱路線時，系統會自動寫入這個工作表
- 不需要手動填入任何資料

**Weekday 對照表（參考用）：**
- 1 = 週一
- 2 = 週二
- 3 = 週三
- 4 = 週四
- 5 = 週五
- 6 = 週六
- 7 = 週日

---

## 工作表 4：Master_Schedule（排課總表）- 修改

### 操作步驟
1. 清空所有資料
2. 只填入表頭，內容留空（系統自動產生）

### 表頭（第1行）
```
Slot_ID	CourseLineID	CourseName	SyllabusID	Date	Weekday	Time	Classroom	Teacher_ID	Level_ID	Book_Code	Book_Full_Name	Chapters	Status	Note	Created_At	Updated_At
```

### 資料
```
（第2行開始留空，等系統產生）
```

---

## 工作表 5：Lesson_Log（講師回填記錄）- 保持不變

### 操作步驟
如果已有，保持不變。如果沒有，新建並只填表頭。

### 表頭（第1行）
```
Log_ID	Slot_ID	Teacher_ID	Actual_Book_Code	Attendance	Handover_Note	Completed_At
```

### 資料
```
（第2行開始留空，等講師回填）
```

---

## 完成檢查清單

建立完成後，確認以下事項：

**手動設定：**
- [ ] Config_Syllabus 有 2 個以上的課綱（SYL001, SYL002...）
- [ ] 每個課綱至少有 3-5 筆教材
- [ ] Config_Teacher 有至少 2 位老師

**系統產生（保持空白）：**
- [ ] Config_CourseLine 只有表頭，無資料 ✓
- [ ] Master_Schedule 只有表頭，無資料 ✓
- [ ] Lesson_Log 只有表頭，無資料 ✓

**權限設定：**
- [ ] Service Account Email 已加入共用（編輯者權限）
- [ ] automation-credential@premium-ember-474807-n7.iam.gserviceaccount.com

**工作表確認：**
- [ ] 沒有 Config_Class 工作表（已刪除）
- [ ] 有 Config_CourseLine 工作表（新建）

完成後，前往 Streamlit App 點選「➕ 新增課綱路線」開始排課。

---

## 快速複製貼上格式

### Config_Syllabus（複製下方整段貼到 Google Sheets）
```
SyllabusID	SyllabusName	Level_ID	Sequence	Book_Code	Chapters	Book_Full_Name
SYL001	幼兒英語啟蒙	Level_1	1	P21_B1_1-3	1+2+3	P21 Book 1
SYL001	幼兒英語啟蒙	Level_1	2	P21_B1_4-6	4+5+6	P21 Book 1
SYL001	幼兒英語啟蒙	Level_1	3	P21_B2_7-9	7+9	P21 Book 2
SYL001	幼兒英語啟蒙	Level_1	4	TTR_Story1_1-2	1+2	Toy Team Review Story 1
SYL001	幼兒英語啟蒙	Level_1	5	P21_B3_Review	Review	P21 Book 3 Review
SYL002	兒童進階閱讀	Level_2	1	TTT_A1	-	The Thinking Train A1
SYL002	兒童進階閱讀	Level_2	2	TTT_A2	-	The Thinking Train A2
SYL002	兒童進階閱讀	Level_2	3	TTT_A3	-	The Thinking Train A3
SYL002	兒童進階閱讀	Level_2	4	TTT_B1	-	The Thinking Train B1
SYL002	兒童進階閱讀	Level_2	5	TTT_Review	Review	The Thinking Train Review
```

### Config_CourseLine（只複製表頭）
```
CourseLineID	CourseName	SyllabusID	Weekday	Time	Classroom	Teacher_ID	Start_Date	Start_Sequence	Status	Note
```
**注意：只填表頭，不要填資料。系統會自動產生。**

### Master_Schedule（只複製表頭）
```
Slot_ID	CourseLineID	CourseName	SyllabusID	Date	Weekday	Time	Classroom	Teacher_ID	Level_ID	Book_Code	Book_Full_Name	Chapters	Status	Note	Created_At	Updated_At
```

---

完成後，回到 Streamlit App 點選「同步班級資料」按鈕。
