# Hospital Report Cleaner

這個專案用來把多種醫院報表整理成乾淨、可分析的 Excel 檔。

## 目標

- 讀取 `raw/` 內的原始報表
- 統一欄位名稱
- 清除空白列、合計列、重複資料
- 標準化日期與文字值
- 輸出到 `output/cleaned_reports.xlsx`
- 同時產生 `cleaned_data`、`standardized_data`、`patient_master`、`unmatched_icd10`、`stage_review` 五張工作表

## 建議流程

1. 把原始報表放進 `raw/`
2. 依需求調整 `mapping/column_mapping.csv`
3. 依需求調整 `mapping/value_mapping.csv`
4. 安裝套件後執行清洗

## 安裝

```powershell
pip install -r requirements.txt
```

## 執行

```powershell
$env:PYTHONPATH="src"
python -m report_cleaner.cli
```

## 目前支援

- `.xlsx`
- `.xls`
- `.csv`

## 目前輸出內容

- `cleaned_data`：保留原始欄位的大聯集清洗版
- `standardized_data`：把不同報表轉成統一欄位，保留每筆事件
- `patient_master`：同一病人跨報表合併後的主檔
- `unmatched_icd10`：目前還無法自動映射癌別的 ICD10 清單
- `stage_review`：目前 TNM 與 final stage 的整理結果
- 會盡量從檔名或報表表頭抓出 `report_period_start` / `report_period_end`

## Final Stage 策略

- 先用報表原始 `期別` 當 `final_stage`
- 若 `final_stage` 空白，才會嘗試查 `mapping/tnm_stage_mapping.csv`
- `mapping/tnm_stage_mapping.csv` 可逐步補上院內常見的 `癌別 + TNM -> stage` 對照

## 備註

- `report_period_start` / `report_period_end` 代表這份報表匯出的涵蓋時間區間，不是病人的診斷或治療日期
- 目前這批資料中的 `癌別說明` 多數實際承載的是 `ICD10` 診斷碼

## 資料夾說明

- `raw/`：原始報表
- `mapping/`：欄位與值對照表
- `output/`：輸出結果
- `src/report_cleaner/`：清洗程式

## 後續擴充方向

- 不同報表格式的專屬解析器
- 科別、病房、醫師名稱對照表
- 多工作表輸出
- 自動產出摘要統計表
