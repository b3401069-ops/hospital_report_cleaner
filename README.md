# Hospital Report Cleaner

這個專案用來把多種醫院報表整理成乾淨、可分析的 Excel 檔。

## 目標

- 讀取 `raw/` 內的原始報表
- 統一欄位名稱
- 清除空白列、合計列、重複資料
- 標準化日期與文字值
- 輸出到 `output/cleaned_reports.xlsx`
- 同時產生 `cleaned_data`、`standardized_data`、`patient_master`、`patient_list`、`patient_list_zh`、`summary_zh`、`summary_trend_zh`、`unmatched_icd10`、`stage_review` 等工作表

## 建議流程

1. 把原始報表放進 `raw/`
2. 依需求調整 `mapping/column_mapping.csv`
3. 依需求調整 `mapping/value_mapping.csv`
4. 依需求調整 `mapping/drug_treatment_mapping.csv`
5. 依需求調整 `mapping/order_treatment_mapping.csv`
4. 安裝套件後執行清洗

## 安裝

```powershell
pip install -r requirements.txt
```

## 測試

```powershell
python -m pytest
```

## 執行

一般使用者可直接雙擊專案根目錄的批次檔：

- `執行報表清洗.bat`：產生 `output/cleaned_reports.xlsx`
- `匯出待確認mapping.bat`：產生 `output/pending_*_mapping.csv`
- `套用已確認mapping.bat`：將已填好的 pending mapping 追加到正式 `mapping/*.csv`

批次檔會自動切到專案資料夾、檢查 Python 套件，必要時用 `requirements.txt` 安裝缺少的套件。

進階使用者也可以用命令列執行：

```powershell
$env:PYTHONPATH="src"
python -m report_cleaner.cli
```

## 半自動補 Mapping

新增 raw 報表後，若 `unmapped_drug_orders`、`unmapped_treatment_orders` 或 `stage_review` 有需要人工確認的資料，可先匯出待填 CSV：

```powershell
$env:PYTHONPATH="src"
python -m report_cleaner.cli export-mapping-review
```

會產生：

- `output/pending_drug_treatment_mapping.csv`
- `output/pending_order_treatment_mapping.csv`
- `output/pending_tnm_stage_mapping.csv`

人工填好藥物/治療醫令的 `treatment_type`，必要時調整 `name_pattern`、`order_code`、`order_code_prefix`、`cancer_type`、`diagnosis_text`。TNM stage review 則只套用已填 `final_stage` 的列。確認後再套用回 mapping：

```powershell
$env:PYTHONPATH="src"
python -m report_cleaner.cli apply-mapping-review
```

只有已填 `treatment_type` 且有比對規則的藥物/治療列會被追加到 mapping CSV；TNM stage 只有已填 `cancer_type`、`tnm_pattern`、`final_stage` 的列會被追加到 `mapping/tnm_stage_mapping.csv`。空白列不會套用。

## 目前支援

- `.xlsx`
- `.xls`
- `.csv`

## 目前輸出內容

- `cleaned_data`：保留原始欄位的大聯集清洗版
- `standardized_data`：把不同報表轉成統一欄位，保留每筆事件
- `patient_master`：同一病人跨報表合併後的主檔
- `patient_list`：適合後續篩選或串接的病人清單
- `patient_list_zh`：中文欄名版本的病人清單
- `summary_zh`：依癌別、期別、個案分類、性別、年齡區間、治療別統計人數
- `summary_trend_zh`：依診斷月份彙整總人數、癌別與治療別趨勢
- `unmatched_icd10`：目前還無法自動映射癌別的 ICD10 清單
- `stage_review`：目前 TNM 與 final stage 的整理結果
- `unmapped_drug_orders`：尚未歸類的指引藥物醫令，可用來補 `mapping/drug_treatment_mapping.csv`
- `unmapped_treatment_orders`：尚未歸類的一般治療醫令，可用來補 `mapping/order_treatment_mapping.csv`
- 會盡量從檔名或報表表頭抓出 `report_period_start` / `report_period_end`

## 資料安全

- `raw/` 與 `output/` 預設被 `.gitignore` 排除，避免原始報表與清洗後病人資料進入 GitHub
- 若要分享測試資料，請放匿名化、小型範例到 `tests/fixtures/`
- `mapping/` 可以進版控，因為它保存欄位、值、ICD10、TNM 與藥物治療分類規則
- `mapping/*.csv` 使用 UTF-8 with BOM，方便 Windows 檔案總管與 Excel 直接開啟時正確顯示繁體中文

## Final Stage 策略

- 先用報表原始 `期別` 當 `final_stage`
- 若 `final_stage` 空白，才會嘗試查 `mapping/tnm_stage_mapping.csv`
- `mapping/tnm_stage_mapping.csv` 可逐步補上院內常見的 `癌別 + TNM -> stage` 對照

## 品質檢查

- 最新不含病人明細的檢查紀錄放在 `docs/REPORT_QUALITY_REVIEW_ZH.md`
- 優先處理 `unmatched_icd10`、`stage_review`、`unmapped_drug_orders`、`unmapped_treatment_orders`、病人主檔欄位空值率與 summary sheet 是否符合使用情境

## 備註

- `report_period_start` / `report_period_end` 代表這份報表匯出的涵蓋時間區間，不是病人的診斷或治療日期
- 目前這批資料中的 `癌別說明` 多數實際承載的是 `ICD10` 診斷碼

## 資料夾說明

- `raw/`：原始報表
- `mapping/`：欄位與值對照表
- `mapping/drug_treatment_mapping.csv`：指引藥物的化療、標靶、免疫、荷爾蒙分類規則
- `mapping/order_treatment_mapping.csv`：醫令型報表的化療、放療、手術、TACE、RFA 分類規則
- `output/pending_*_mapping.csv`：半自動 mapping review 暫存檔，不進版控
- `output/`：輸出結果
- `src/report_cleaner/`：清洗程式

## GitHub 協作流程

建議把 `main` 當成正式可用版本，所有會影響清洗結果的修改都先走分支與 PR。

### 分支命名

- `main`：正式版本
- `feature/...`：新增功能或欄位
- `fix/...`：修正錯誤或規則
- `review/...`：暫時性試作或 review 用分支

例如：

- `feature/add-treatment-dates`
- `feature/add-icd10-mapping`
- `fix/patient-key-rules`

### 建議流程

1. 先抓最新版本
2. 從 `main` 開新分支
3. 在分支上修改與測試
4. Push 到 GitHub
5. 開 Pull Request
6. 由另一位使用者或 AI review
7. 修正完成後再 merge 回 `main`

### 常用指令

```powershell
git pull
git checkout -b feature/add-treatment-dates
```

修改完成後：

```powershell
git add .
git commit -m "Add separate treatment date fields"
git push -u origin feature/add-treatment-dates
```

### 什麼情況建議開 PR

- 新增或調整輸出欄位
- 修改日期邏輯
- 修改病人主鍵規則
- 新增 ICD10 對照規則
- 修改 TNM / final stage 規則
- 修改摘要統計方式

### 什麼情況可直接改 `main`

- README 或操作文件的小幅修字
- 不影響資料結果的純說明文字調整

### 多電腦或多 AI 使用建議

- 修改前先 `git pull`
- 修改後再 `commit` + `push`
- 另一台電腦或另一個 AI 開始前，先再 `git pull`
- 若由兩個 AI 協作，建議一方負責實作，另一方負責 review，最後由同一邊整合後 merge

## 後續擴充方向

- 不同報表格式的專屬解析器
- 科別、病房、醫師名稱對照表
- 多工作表輸出
- 自動產出摘要統計表
