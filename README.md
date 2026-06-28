# Hospital Report Cleaner

醫院癌症報表清洗器。把 `raw/` 裡多個 Excel 報表整理成 `output/cleaned_reports.xlsx`，並產生標準化資料、病人清單、中文摘要、mapping 待確認清單與 TNM/stage review。

請先看這份短版操作說明：

[使用說明_給個管師.md](使用說明_給個管師.md)

## 最短使用方法

1. 解壓縮專案資料夾。
2. 第一次使用先按兩下 `install_dependencies.bat`。
3. 把要清洗的 Excel 報表放進 `raw/`。
4. 按兩下 `執行報表清洗.bat`。
5. 到 `output/cleaned_reports.xlsx` 查看結果。
6. 如果想先檢查電腦能不能跑，按兩下 `檢查執行環境.bat`。

## Windows 批次檔

- `install_dependencies.bat`：安裝或更新 Python 套件，完成後執行環境檢查。
- `檢查執行環境.bat`：檢查 Python、套件、資料夾、mapping CSV、`output/` 寫入權限。
- `執行報表清洗.bat`：產生 `output/cleaned_reports.xlsx`。
- `匯出待確認mapping.bat`：產生 `output/pending_*_mapping.csv`，給人工確認新藥物、醫令碼或 TNM stage。
- `套用已確認mapping.bat`：把已確認的 pending mapping 套回 `mapping/*.csv`。

如果電腦顯示找不到 Python，請先安裝 Python 3：
https://www.python.org/downloads/

## 指令用法

工程或測試時也可以用 PowerShell：

```powershell
pip install -r requirements.txt
$env:PYTHONPATH="src"
python -m report_cleaner.cli check-env
python -m report_cleaner.cli
python -m report_cleaner.cli export-mapping-review
python -m report_cleaner.cli apply-mapping-review
```

## 輸出工作表

`output/cleaned_reports.xlsx` 會包含：

- `cleaned_data`
- `standardized_data`
- `patient_master`
- `patient_list`
- `patient_list_zh`
- `summary_zh`
- `summary_trend_zh`
- `unmatched_icd10`
- `stage_review`
- `unmapped_drug_orders`
- `unmapped_treatment_orders`

## Mapping Review 流程

當新報表出現程式還不認識的藥物、治療醫令碼或 TNM/stage 組合時：

1. 按 `匯出待確認mapping.bat`。
2. 打開 `output/pending_drug_treatment_mapping.csv`、`output/pending_order_treatment_mapping.csv`、`output/pending_tnm_stage_mapping.csv`。
3. 由 Codex 或醫療端確認要新增的欄位，例如 `treatment_type`、`order_code`、`name_pattern`、`final_stage`。
4. 確認完成後按 `套用已確認mapping.bat`。
5. 再按 `執行報表清洗.bat` 重新產生報表。

## 資料安全

- `raw/` 和 `output/` 會被 `.gitignore` 排除，不應上傳 GitHub。
- 請不要把真實病人報表、輸出 workbook、截圖或含病歷號的檔案 commit。
- `mapping/*.csv` 可以上傳，內容是欄位、ICD10、TNM、藥物與治療醫令碼規則。
- `mapping/*.csv` 使用 UTF-8 with BOM，方便 Windows Excel 開啟繁體中文。

## 專案結構

- `raw/`：放原始 Excel 報表，不上傳 GitHub。
- `mapping/`：欄位與分類規則，可維護、可上傳。
- `output/`：產生的報表與 pending mapping，不上傳 GitHub。
- `src/report_cleaner/`：清洗程式。
- `tests/`：自動測試。

## 測試

```powershell
$env:PYTHONPATH="src"
python -m pytest
```

目前測試涵蓋欄位對應、ICD10、TNM/stage review、藥物/治療 mapping、CSV 編碼、CLI 匯入與環境檢查。
