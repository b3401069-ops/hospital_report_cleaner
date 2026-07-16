# Hospital Report Cleaner

醫院癌症報表清洗器。把 `raw/` 裡多個 Excel 報表整理成 `output/cleaned_reports.xlsx`，並產生標準化資料、病人清單、中文摘要、mapping 待確認清單與 TNM/stage review。

請先看這份短版操作說明：

[使用說明.md](使用說明.md)

## 最短使用方法

1. 解壓縮專案資料夾。
2. 第一次使用先按兩下 `安裝套件.bat`。
3. 把要清洗的 Excel 報表放進 `raw/`。
4. 按兩下 `清洗報表.bat`。
5. 到 `output/cleaned_reports.xlsx` 查看結果。
6. 打開後先看第一個分頁 `使用說明`，日常總表是第二個分頁 `病人總表`。
7. 如果想先檢查電腦能不能跑，按兩下 `檢查環境.bat`。

## Windows 批次檔

- `安裝套件.bat`：安裝或更新 Python 套件，完成後執行環境檢查。
- `檢查環境.bat`：檢查 Python、套件、資料夾、mapping CSV、`output/` 寫入權限。
- `清洗報表.bat`：產生 `output/cleaned_reports.xlsx`。
- `匯出待確認.bat`：產生 `output/pending_*_mapping.csv`，給人工確認新藥物、醫令碼或 TNM stage。
- `套用確認.bat`：把已確認的 pending mapping 套回 `mapping/*.csv`。

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

- `使用說明`：第一頁，說明總表位置、各分頁用途與本次品質計數。
- `病人總表`：日常主要查閱表，常用欄位在前方，含治療摘要。
- `統計摘要`：依癌別、期別、性別、年齡與治療彙總。
- `月趨勢`：依診斷月份整理個案與治療趨勢。
- `ICD10待確認`、`TNM期別待確認`、`藥物待確認`、`治療醫令待確認`：需要人工檢視的資料。
- `cleaned_data`、`standardized_data`、`patient_master`、`patient_list`、`stage_review`：工程與稽核底稿，預設隱藏，資料仍完整保留。

`病人總表` 的治療欄顯示「有」，代表來源資料中找到該治療紀錄；空白只代表目前來源沒有找到，不等於確認未接受治療。

## Mapping Review 流程

當新報表出現程式還不認識的藥物、治療醫令碼或 TNM/stage 組合時：

1. 按 `匯出待確認.bat`。
2. 打開 `output/pending_drug_treatment_mapping.csv`、`output/pending_order_treatment_mapping.csv`、`output/pending_tnm_stage_mapping.csv`。
3. 由 Codex 或醫療端確認要新增的欄位，例如 `treatment_type`、`order_code`、`name_pattern`、`final_stage`。
4. 確認完成後按 `套用確認.bat`。
5. 再按 `清洗報表.bat` 重新產生報表。

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
