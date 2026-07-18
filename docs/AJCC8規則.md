# AJCC8 TNM 規則與限制

本專案的 `mapping/tnm_stage_mapping.csv` 只保存能由目前癌別與 TNM 欄位判定的 broad stage（0–4）。規則用於報表整理，不取代醫師或癌症登記人員判讀。

## 2026-07-18 新增規則

本輪先從院內報表找出「同癌別、同 TNM、已有期別」的組合，再保留至少 3 筆一致證據者，最後以 NCI 所列 AJCC 第 8 版 stage grouping 核對。

- 結腸直腸癌：`T3 N1 M0` 歸 broad stage 3；`M1` 歸 broad stage 4。
- 非小細胞肺癌：`M1/M1a/M1c` 歸 broad stage 4；`T1mi N0 M0` 歸 broad stage 1。
- 肝癌：`M1` 歸 broad stage 4。本專案不把 `Nx` 當成 `N0`。
- 口腔癌：`T2 N0 M0` 歸 broad stage 2。
- 膀胱癌：`Ta N0 M0` 歸 broad stage 0。

參考來源：

- [NCI Colon Cancer Treatment (AJCC 8)](https://www.cancer.gov/types/colorectal/hp/colon-treatment-pdq)
- [NCI Non-Small Cell Lung Cancer Treatment (AJCC 8)](https://www.cancer.gov/types/lung/hp/non-small-cell-lung-treatment-pdq)
- [NCI Primary Liver Cancer Treatment (AJCC 8)](https://www.cancer.gov/types/liver/hp/adult-liver-treatment-pdq)
- [NCI Lip and Oral Cavity Cancer Treatment (AJCC 8)](https://www.cancer.gov/types/head-and-neck/hp/adult/lip-mouth-treatment-pdq)
- [NCI Bladder Cancer Treatment (AJCC 8)](https://www.cancer.gov/types/bladder/hp/bladder-treatment-pdq)

## 不自動判定

- 乳癌：AJCC8 prognostic stage 還會使用 Grade、HER2、ER、PR，不能只靠 TNM。
- 攝護腺癌：stage grouping 可能需要 PSA 與 Grade Group。
- TNM 含 `X`、只有 `TNM` 字樣、癌別不明或同一組合出現衝突期別。
- 肝癌 `Nx` 的早期期別：缺少淋巴結狀態時不自動假設為 `N0`。

這些組合會保留在 `TNM期別待確認`，由醫療端確認後再加入 mapping。
