# GitHub 與本機版本比較

比較對象：

- GitHub: `b3401069-ops/hospital_report_cleaner`，`main`，最新 commit `bf49cf5`
- 本機: `C:\Users\Ming\Documents\Codex\hospital_report_cleaner`
- raw 資料來源: 本機 `raw/` 內 12 份報表

這份筆記只記錄彙總與程式差異，不放病人明細。

## 結論

本機版本比 GitHub `main` 更接近目前報表需求。GitHub `main` 的 2026-06-22 修改看似新增很多欄位 mapping 與發佈包，但破壞了專屬解析器讀中文原始欄位的流程，導致 TNM、治療計畫與新醫令報表被大量讀成空白或去重成單筆。

## 同一批 raw 的輸出差異

| 指標 | GitHub main | 本機版本 |
| --- | ---: | ---: |
| processed files | 12 | 12 |
| cleaned rows | 5861 | 5861 |
| standardized rows | 1388 | 4091 |
| patient master rows | 846 | 971 |
| unmatched ICD10 rows | 14 | 12 |
| stage review rows | 0 | 76 |

## 治療旗標差異

| 治療欄位 | GitHub standardized | 本機 standardized |
| --- | ---: | ---: |
| chemotherapy | 390 | 2625 |
| targeted_therapy | 0 | 15 |
| immunotherapy | 0 | 0 |
| hormone_therapy | 0 | 32 |
| radiation_therapy | 0 | 47 |
| surgery | 0 | 540 |
| tace | 0 | 210 |
| rfa | 0 | 9 |

GitHub `patient_master` 的所有治療旗標皆為 0；本機版本可彙整到病人層級。

## 主要原因

1. GitHub `mapping/column_mapping.csv` 被擴成大量欄位轉換，且仍把 `病歷編號` 對成 `patient_id`。
2. `run_cleaning()` 會先套用欄位 rename，再進入 `_standardize_tnm()`、`_standardize_treatment_plan()` 等專屬解析器。
3. 這些專屬解析器仍以中文原始欄名讀資料，例如 `個案編號`、`癌別說明`、`組合`、`期別`。
4. 欄位先被 rename 後，專屬解析器找不到原始欄名，導致 D1.1/D1.2/D1.4 幾乎全部變空白，去重後各剩 1 筆。
5. GitHub `main` 沒有 `_standardize_order_detail()`，所以新增的醫令、藥物、手術、放射或 TAE/TACE/RFA 類報表沒有被轉成結構化治療欄位。

## 本機版本新增且應保留的方向

- `_standardize_order_detail()`：處理有 `醫令代碼`、`醫令名稱` 的新報表。
- `_classify_order_treatment()`：用報表名稱、醫令代碼、醫令名稱分類 chemotherapy、radiation、surgery、tace、rfa。
- D1.2 已能從 `癌別說明` 抽 ICD10，從 `簡稱` 或癌別說明補診斷文字，並保留 `主責醫師`。
- `病歷號`、`病歷編號`、`病歷號碼` 都回到 `medical_record_no`。
- 有 smoke tests 守住上述欄位。

## GitHub main 中不建議直接沿用的部分

- 大量 global `column_mapping.csv`。它會和專屬解析器互相打架。
- `dist_package/` 與 `HospitalReportCleaner.zip` 放在 repo 根目錄。這些是發佈產物，會和原始碼重複，建議改用 GitHub release 或重新產生。
- `main.py` 與 dist package 的平行入口。若要保留桌面雙擊執行，應讓它薄薄包一層 `report_cleaner.cli`，避免多份邏輯。

## 建議救援策略

1. 以本機版本為恢復基底，不要直接用 GitHub `main` 覆蓋。
2. 從 GitHub 只挑文件中有用的操作說明，避開 2026-06-22 的欄位 mapping 和發佈包改動。
3. 接 GitHub 前先重建有效 `.git`，確認 `raw/`、`output/`、`_compare/`、`*.zip` 不進版控。
4. 下一步優先改善本機的醫令分類：
   - 化療藥物代碼 37038B-37041B 已能被抓到 chemotherapy。
   - 手術報表已能抓 surgery，但還沒有輸出「術式名稱」的專用欄位。
   - RT 檔名中的醫令碼 `33075BR`、`33144BR` 目前分類為 TACE/TAE 類，需由使用者確認這些碼是否應歸類為栓塞治療，而不是放射治療。
   - 標靶、免疫、荷爾蒙藥物若來自醫令明細，仍需補代碼或藥名分類規則。
