# Report Quality Review

這份筆記只記錄彙總品質指標，不放病人姓名、病歷號或其他病人明細。

## 目前基準

最近一次使用 `raw/` 內 38 份報表產生 `output/cleaned_reports.xlsx`：

- Processed files: 38
- Standardized rows: 25377
- Patient master rows: 2964
- Patient list rows: 2964
- Unmatched ICD10 rows: 13
- Stage review rows: 76
- Unmapped drug order rows: 0
- Unmapped treatment order rows: 0

## 資料安全

- `.gitignore` 已排除 `raw/*` 與 `output/*`，避免原始報表與輸出 workbook 進版控。
- 目前資料夾尚未初始化為 git repository；接 GitHub 前需先 `git init`，並確認沒有真實資料被 `git add`。

## 這輪已處理

- `unmatched_icd10` 會保留既有或手工 mapping 補出的 `diagnosis_text`。
- 這讓 ICD10 review sheet 不只列 code，也能顯示已知診斷文字，方便人工判斷是否要補 `cancer_type`。
- 新增 `11401-11505` 系列報表支援：
  - `醫令代碼` / `醫令名稱` 類報表可透過 `mapping/order_treatment_mapping.csv` 歸入化療、放療、手術、TACE、RFA。
  - `醫令碼` / `名稱` 的指引藥物報表可歸入化療、標靶、免疫、荷爾蒙。
  - 收案清單與各癌計畫書填寫日期可讀取化療、電療、荷爾蒙、標靶、手術日期欄位。
- `unmatched_icd10` 目前只列 C 開頭癌症 ICD10，避免 Z51、M06、L40 等行政或非癌症診斷淹沒 review sheet。
- 新增 `unmapped_drug_orders` 與 `unmapped_treatment_orders` review sheets；程式遇到未知藥物或未知治療醫令時，只列出待確認項目，不會自動寫入 mapping CSV。

## 下一批優先品質點

1. 補 `mapping/icd10_mapping.csv` 中仍缺診斷文字或癌別的 ICD10。
   目前仍需 review 的 C-code 以 `unmatched_icd10` sheet 為準。

2. 擴充 `mapping/tnm_stage_mapping.csv`。
   `stage_review` 仍有 TNM 組合沒有最終期別；建議由醫療端確認常見癌別與 TNM 對照後再補表，不在程式內硬寫。

3. 檢查 summary 使用情境。
   `summary_zh` 與 `summary_trend_zh` 目前以 `patient_master` 為基礎，因此偏向病人層級統計；若要看治療事件量，應另外新增事件層級 summary，避免混淆。

4. 補匿名 fixture。
   現在 smoke test 會讀本機 `raw/`，可再加入小型匿名 Excel/CSV fixture，讓 GitHub CI 在沒有真實資料時也能跑核心測試。

5. 精緻化藥物分類。
   目前指引藥物用 `mapping/drug_treatment_mapping.csv` 分成化療、標靶、免疫、荷爾蒙；後續新增藥物時，優先補這份 CSV。

6. 精緻化醫令/術式分類。
   目前醫令型治療用 `mapping/order_treatment_mapping.csv` 分成化療、放療、手術、TACE、RFA；後續新增術式或醫令碼時，優先補這份 CSV。

7. 檢查未分類 review sheets。
   每次新增 raw 報表後，先看 `unmapped_drug_orders` 和 `unmapped_treatment_orders` 是否有資料；若有，人工確認分類後再補 mapping CSV。

8. 使用半自動 mapping 工具。
   可用 `python -m report_cleaner.cli export-mapping-review` 產生 `output/pending_drug_treatment_mapping.csv` 與 `output/pending_order_treatment_mapping.csv`，人工填好 `treatment_type` 後，再用 `python -m report_cleaner.cli apply-mapping-review` 追加到正式 mapping CSV。

## 2026-06-26 品質檢查補充

- `mapping/icd10_mapping.csv` 已將明確的非核心主診斷 C-code 補到既有癌別群組。
- `C77`、`C78`、`C79` 這類續發性或轉移性 ICD10 code 不直接推回主癌別，仍保留在 `unmatched_icd10` 供人工確認。
- `unmatched_icd10.notes` 會用 `secondary_or_metastatic_code_needs_primary_site_review` 標示這類需確認原發部位的 code。
- `stage_review` 新增 `primary_tnm` 與 `review_reason`，方便優先處理缺少 final stage 或 TNM 含 `X` 的資料。
- 程式不會自行硬算 TNM stage；只有 `mapping/tnm_stage_mapping.csv` 有人工確認過的對照時，才會補上 `final_stage_source = tnm_mapping`。
