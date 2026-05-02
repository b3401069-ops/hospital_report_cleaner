# 多人共用流程說明

這份文件說明如何讓多位同事在不同電腦上共同提供報表，但仍由單一流程穩定產出同一份整理結果。

## 核心原則

- 多人可以提供原始報表
- 少數人維護對照表
- 固定由一台主機產出結果
- 不直接多人同時修改輸出 Excel

## 建議角色

### 1. 報表提供者

負責：

- 從 HIS 匯出報表
- 把報表放進 `raw/`
- 檔名盡量加上日期區間

不負責：

- 修改 `mapping/`
- 修改 `output/`

### 2. 規則維護者

負責：

- 維護 `mapping/icd10_mapping.csv`
- 維護 `mapping/tnm_stage_mapping.csv`
- 檢查 `unmatched_icd10`
- 檢查 `stage_review`

### 3. 主機執行者

負責：

- 固定執行整理程式
- 確認輸出結果成功更新
- 將已處理原始檔移到封存區

## 建議資料夾權限

### `raw/`

- 多人可寫入
- 多人可讀取

### `mapping/`

- 一般使用者唯讀
- 規則維護者可編輯

### `output/`

- 多人可讀取
- 建議不要手動修改

### `archive/`

- 主機執行者可整理
- 一般使用者可讀取

## 建議檔名規則

同一報表若因資料量太大分多個時間區段下載，建議在檔名加入期間：

- `D1.2_202601_202604.xls`
- `D1.2_202605_202608.xls`
- `住院人次人日_202601.xls`
- `住院人次人日_202602.xls`

即使不改檔名，程式也會嘗試從報表表頭抓期間；但檔名有區間會更穩。

## 日常操作流程

1. 使用者從 HIS 匯出報表
2. 使用者將報表放到 `raw/`
3. 主機執行者執行：

```powershell
$env:PYTHONPATH="src"
python -m report_cleaner.cli
```

4. 檢查 `output/cleaned_reports.xlsx` 或自動另存的新版本
5. 規則維護者查看：

- `unmatched_icd10`
- `stage_review`
- `patient_list`

6. 若需要，更新 `mapping/`
7. 重新執行一次
8. 將已處理原始報表移到 `archive/`

## 建議輸出用途

### `patient_list`

用於：

- 病人主名單
- 管理表
- 提供同事查閱

### `patient_master`

用於：

- 保留完整病人整合欄位
- 後續擴充分析

### `standardized_data`

用於：

- 保留每一筆事件
- 化療、住院、收案、計畫書等事件分析

### `unmatched_icd10`

用於：

- 追蹤尚未完成分類的 ICD10

### `stage_review`

用於：

- 檢查 TNM 與 final stage
- 維護 `tnm_stage_mapping.csv`

## 常見注意事項

### 1. 同一批檔案被重複放進 `raw/`

程式已有去重，但仍建議處理後移到 `archive/`。

### 2. 輸出 Excel 被打開

如果 `cleaned_reports.xlsx` 正開著，程式會自動另存成：

- `cleaned_reports_1.xlsx`
- `cleaned_reports_2.xlsx`

### 3. 不同人改了不同版本 mapping

建議指定固定維護者，不要多人同時修改 `mapping/`。

### 4. 某些診斷碼沒有癌別

先看 `unmatched_icd10`，確認後補進 `mapping/icd10_mapping.csv`。

## 最推薦的實務模式

- 多人提供原始報表
- 一人或一台主機固定產出
- 少數人維護對照規則
- 不把 `output` 當資料輸入來源

這樣最穩，也最容易追蹤錯誤來源。
