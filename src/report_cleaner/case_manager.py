"""Case-level planned/observed views. Alerts are administrative review prompts."""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
import hashlib
import json
import re
from pathlib import Path

import pandas as pd
from dateutil.relativedelta import relativedelta

from .case_manager_sources import (
    Sources, TREATMENTS, cancer_scope, day, deduplicate_events, first, merge_cases, text,
)
from .case_manager_rules import (
    ACTIONS, RED, GRAY, RADIATION_CODES, reclassify, is_class_zero, exempt_plan,
    plan_dates as collect_plan_dates, new_courses, radiation_review, death_review, planned_drugs,
)

PLAN_PREFIXES = {
    "手術": ("手術", "淋巴", "乳房重建"), "放射治療": ("放射線治療", "放療", "電療"),
    "化學治療": ("化學治療", "化療", "口服", "膀胱灌", "NSCLC", "SCLC"), "標靶治療": ("標靶",),
    "免疫治療": ("免疫",), "抗荷爾蒙治療": ("荷爾蒙", "賀爾蒙"),
    "肝動脈栓塞（TACE）": ("動脈栓塞",), "射頻燒灼（RFA）": ("RFA",),
    "CCRT": ("CCRT",), "預定緩和治療": ("預定緩和",),
}


@dataclass(frozen=True)
class ReviewRules:
    # Operational thresholds transcribed from the supplied template, not a
    # clinical guideline or evidence that a treatment was inappropriate.
    prediagnosis_days: int = 90
    first_treatment_days: int = 30
    adjuvant_chemo_days: int = 56
    no_visit_days: int = 90
    followup_months: int = 6


@dataclass
class CaseReport:
    as_of: date
    planned: list[dict] = field(default_factory=list)
    actual: list[dict] = field(default_factory=list)
    tasks: list[dict] = field(default_factory=list)
    events: list[dict] = field(default_factory=list)
    pending: list[dict] = field(default_factory=list)
    audit: list[dict] = field(default_factory=list)
    stages: pd.DataFrame = field(default_factory=pd.DataFrame)


def join(values):
    return "\n".join(dict.fromkeys(text(v) for v in values if text(v)))


def plan_fields(plans, cancer="", cutoff=None):
    fields = {kind: [] for kind in PLAN_PREFIXES}
    for row in sorted(plans, key=lambda r: (r["_period"], r["_source"], r["_row"])):
        for kind, prefixes in PLAN_PREFIXES.items():
            dated = [day(v) for k,v in row.items() if k.startswith(prefixes) and "日期" in k and day(v)]
            if cutoff and dated and min(dated) > cutoff:
                continue
            for key, value in row.items():
                if kind == "放射治療" and key == "放療其他說明" and cancer_scope(cancer or row.get("_cancer")) == "LI":
                    continue
                if (key.startswith(prefixes) or (kind == "放射治療" and key == "DOSECGY")) and value and not re.match(r"^(?:N(?:_|$)|否$|無$|0$)", str(value)):
                    if "日期" in key:
                        value = day(value)
                        if value and (not cutoff or value <= cutoff):
                            fields[kind].append(f"填寫日：{value}")
                    else:
                        fields[kind].append(f"{key}：{value}")
        if cancer_scope(cancer or row.get("_cancer")) == "LI":
            notes = " ".join(text(v) for k,v in row.items() if "說明" in k)
            for kind, pattern in [("肝動脈栓塞（TACE）", r"(?<![A-Za-z])TA(?:CE|E)(?![A-Za-z])"), ("射頻燒灼（RFA）", r"(?<![A-Za-z])RFA(?![A-Za-z])")]:
                if re.search(pattern, notes, re.I):
                    fields[kind].append("是（計畫書說明）")
    return {kind: join(values) for kind, values in fields.items()}


def event_summary(events):
    if not events:
        return ""
    groups = defaultdict(list)
    for e in events:
        key = (e.get("generic") or e["name"]) if e["drug"] else f'{e["name"]}（{e["code"]}）'
        groups[key].append(e)
    result = []
    for name, group in groups.items():
        dates = sorted({e["date"] for e in group if e["date"]})
        span = f"{dates[0]} ～ {dates[-1]}，{len(dates)}日" if dates else "日期缺漏"
        result.append(f"{name}：{span}")
    return "\n".join(result)


def eligible_event(event, record, rules):
    if event["date"] is None:
        return False
    baseline = day(first(record, "最初診斷日期", "初次診斷日期", "收案日期"))
    if baseline is None or event["date"] < baseline - timedelta(days=rules.prediagnosis_days):
        return False
    return not event["scope"] or event["scope"] == cancer_scope(record["_cancer"])


def prepare_stages(cases, root):
    from .cleaner import _apply_stage_mapping, _load_tnm_stage_mapping, _standardize_tnm
    from .patient_stage_review import STAGE_VALUES, apply_confirmations, review_path
    contexts = []
    for case in cases:
        for tnm in case["_tnm_rows"]:
            row = {k:v for k,v in case.items() if not k.startswith("_")}
            row.update({"病歷號":case["_mrn"], "癌別":case["_cancer"],
                "最初診斷日期":text(day(first(case,"最初診斷日期","初次診斷日期","收案日期"))),
                "組合":tnm.get("組合", ""), "期別":tnm.get("期別", ""), "_sources":case["_sources"]})
            contexts.append(row)
    frame = pd.DataFrame(contexts).fillna("")
    stage = _standardize_tnm(frame, "D1.2／個案清單", "", "", "")
    stage["patient_key"] = "MRN:" + stage["medical_record_no"]
    stage["cohort_eligible"] = ["Y" if r["癌別"] and int(r["病歷號"]) >= 1000 else "" for r in contexts]
    stage["source_file"] = [" | ".join(r["_sources"]) for r in contexts]
    stage["raw_stage"] = stage["final_stage"]
    invalid = stage["final_stage"].ne("") & ~stage["final_stage"].str.upper().isin(STAGE_VALUES)
    stage.loc[invalid, "final_stage"] = ""
    stage = _apply_stage_mapping(stage, _load_tnm_stage_mapping(root / "mapping/tnm_stage_mapping.csv"))
    stage.loc[invalid, "final_stage"] = ""
    stage.loc[invalid, "final_stage_source"] = "invalid_reported"
    return apply_confirmations(stage, review_path(root))


def task_key(record, kind, related, context):
    fields = [record["病歷號"], record["個案編號"], kind, text(related), context]
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False).encode("utf-8")).hexdigest()


def add_pathology_pending(report, pathology_rows):
    represented = {r["病歷號"] for r in report.actual + report.pending}
    orphan_sources = defaultdict(list)
    for row in pathology_rows:
        if row["_mrn"] not in represented:
            orphan_sources[row["_mrn"]].append(row["_source"])
    for ident, files in sorted(orphan_sources.items()):
        report.pending.append({"病歷號":ident,"個案編號":"",
            "待確認原因":"有病理紀錄但未連結收案個案，請核對完整病理、癌別及個案編號；未自動判為癌症",
            "來源檔案":join(files)})


def build_report(sources: Sources, root: Path, *, as_of=None, rules=ReviewRules()):
    cases = merge_cases(sources.cases)
    if not cases:
        raise ValueError("收案資料沒有有效個案編號，無法建立個案總表。")
    cutoff = as_of or sources.as_of
    if cutoff is None:
        raise ValueError("無法辨識來源涵蓋日期，請以 --as-of YYYY-MM-DD 明確指定統計截止日。")
    report = CaseReport(cutoff, audit=sources.audit)
    report.stages = prepare_stages(cases, root)
    stage_groups = {(ident,case_id): group for (ident,case_id),group in report.stages.groupby(["medical_record_no","case_id"])}
    events = deduplicate_events([reclassify(e) for e in sources.events])
    report.audit = list(sources.audit) + [{"來源檔案":"合併去重", "類型":"稽核", "有效列數":len(events),
        "說明":f"原始醫令{len(sources.events)}列，去重後{len(events)}列；保留來源檔名與列號"}]
    by_patient, plans, path_reports = defaultdict(list), defaultdict(list), defaultdict(list)
    for event in events:
        by_patient[event["mrn"]].append(event)
    for row in sources.plans:
        plans[row["_mrn"], row["_case"]].append(row)
    for row in sources.pathology:
        path_reports[row["_mrn"]].append(row)
    count = Counter(r["_mrn"] for r in cases)
    serial = Counter()
    case_owners = defaultdict(set)
    for row in cases:
        case_owners[row["_case"]].add(row["_mrn"])

    def add_task(row, kind, description, related=None, days=None, severity=None, context=""):
        severity = severity or ("紅" if kind in RED else "灰" if kind in GRAY else "黃")
        report.tasks.append({"嚴重度": severity, "個管師": row["個管師"], "病歷號": row["病歷號"],
            "個案編號": row["個案編號"], "癌別": row["癌別"], "待辦類型": kind,
            "說明": description, "相關日期": related, "逾期天數": days,
            "建議動作": ACTIONS[kind], "確認結果": "", "確認備註": "",
            "確認鍵": task_key(row, kind, related, context or description)})

    for index, raw in enumerate(cases):
        ident, case_id = raw["_mrn"], raw["_case"]
        if int(ident) < 1000:
            report.pending.append({"病歷號": ident, "個案編號": case_id, "待確認原因": "疑似測試病歷號（小於1000），未納入總表"})
            continue
        cancer = raw["_cancer"]
        if not cancer:
            report.pending.append({"病歷號":ident,"個案編號":case_id,
                "待確認原因":"收案癌別未填，不納入癌別統計；需確認資格",
                "來源檔案":join(raw["_sources"])})
        diagnosis = day(first(raw, "最初診斷日期", "初次診斷日期", "收案日期"))
        case_date = day(raw.get("收案日期"))
        death, closed = day(raw.get("死亡日期")), day(raw.get("結案日期"))
        reported_visit = day(raw.get("最近看診日"))
        last_visit = reported_visit if reported_visit and reported_visit <= cutoff else day(raw.get("最近掛號"))
        if last_visit and last_visit > cutoff:
            last_visit = None
        followup = day(raw.get("最近追蹤日"))
        if followup and followup > cutoff:
            followup = None
        stage_rows = stage_groups[ident,case_id]
        stage_value = join(stage_rows["final_stage"])
        stage_missing = stage_rows["final_stage"].eq("").any()
        stage_display = join("；".join(text(v) for v in [r["clinical_tnm"],r["pathologic_tnm"],
            ("期別："+r["final_stage"]) if r["final_stage"] else "期別待確認"] if text(v)) for r in stage_rows.to_dict("records"))
        has_tnm = stage_rows["clinical_tnm"].ne("").any() or stage_rows["pathologic_tnm"].ne("").any()
        stage_status = ("完整" if has_tnm else "僅期別，無TNM") if stage_value else ("僅TNM，未判期別" if has_tnm else "未填")
        if stage_missing and stage_value:
            stage_status = "部分TNM期別待確認"
        if stage_rows["final_stage_source"].eq("patient_confirmed").any():
            stage_status += "；人工確認期別（個案人工確認）"
        if stage_rows["final_stage_source"].eq("tnm_mapping").any():
            stage_status += "；含規則補值（需核對適用性）"
        invalid_stage = stage_rows.loc[stage_rows["final_stage_source"].eq("invalid_reported"),"raw_stage"]
        if not invalid_stage.empty:
            stage_display += "\n來源期別代碼待核對：" + join(invalid_stage)
        if raw["_stage_conflict"]:
            stage_status = "同期來源期別不一致，待核對"
        serial[ident] += 1
        shared = {"收案日期": case_date, "病患姓名": first(raw, "病患姓名", "姓名"),
            "病歷號": ident, "性別": first(raw, "性別"), "年齡": first(raw, "年齡"),
            "癌別": cancer, "分期": stage_display,
            "期別資料狀態": stage_status, "納入依據": "癌症收案紀錄" if cancer else "癌別未填，資格待確認",
            "最後回診日": last_visit, "主責醫師": first(raw, "主責醫師", "主治醫師"),
            "個管師": first(raw, "收案個管師"), "個案編號": case_id, "診斷日": diagnosis,
            "診斷名稱": first(raw, "簡稱", "癌別說明"), "癌症個案數": count[ident],
            "查詢鍵": f"{ident}#{serial[ident]}"}
        all_plans = plans[ident, case_id]
        case_plans = [p for p in all_plans if not p["_cancer"] or p["_cancer"] == cancer
                      or (cancer_scope(cancer) and cancer_scope(cancer) == cancer_scope(p["_cancer"]))]
        planned_values = plan_fields(case_plans, cancer, cutoff)
        if not case_plans:
            fallback = plan_fields([raw], cancer, cutoff)
            planned_values.update({k:"計畫書已填寫（個管清單，無細項）\n"+v for k,v in fallback.items() if v})
        current_events = [e for e in by_patient[ident] if e["date"] and e["date"] <= cutoff and eligible_event(e, raw, rules)]
        categories = defaultdict(list)
        for event in current_events:
            categories[event["category"]].append(event)
        delivered = [e for e in current_events if e["category"] in TREATMENTS.values()]
        first_tx = min((e["date"] for e in delivered if diagnosis and e["date"] >= diagnosis-timedelta(days=30)), default=None)
        surgery = min((e["date"] for e in categories["手術"]), default=None)
        chemo = min((e["date"] for e in categories["化學治療"] if surgery and 0 <= (e["date"]-surgery).days <= 180), default=None)
        radiation = min((e["date"] for e in categories["放射治療"] if e["code"] in RADIATION_CODES and surgery and 0 <= (e["date"]-surgery).days <= 365), default=None)
        drug_events = [e for e in delivered if e["drug"]]
        latest = max([d for d in [case_date, diagnosis, last_visit, followup, *[e["date"] for e in current_events]] if d and d <= cutoff], default=None)
        shared["最後資料日期"] = latest
        warnings = []
        if not cancer:
            warnings.append("癌症資格待確認；不納入癌別統計")
        if raw["_cancer_conflict"]:
            warnings.append("同個案同期來源有不同癌別，未任選癌別")
        if len(case_plans) != len(all_plans):
            warnings.append("有計畫書癌別與收案不同，未自動併入")
        if count[ident] > 1:
            warnings.append("多癌別：無部位限制醫令僅按病歷號及時間關聯，需核對歸屬")
        if not diagnosis:
            warnings.append("缺診斷／收案日期，未自動連結治療")
        if len(case_owners[case_id]) > 1:
            warnings.append("同個案編號對應不同病歷號，未跨病歷合併")
        if any(e["date"] is None for e in by_patient[ident]):
            warnings.append("有醫令日期缺漏，僅保留明細")
        if any(e.get("note") != "支持性／非癌症治療" for e in categories["未分類藥物"]+categories["未分類醫令"]):
            warnings.append("有未分類醫令／藥物，療程比對可能不完整")
        if stage_missing:
            warnings.append("缺期別，不能當成已確認期別統計")
        if not case_plans and not exempt_plan(raw):
            warnings.append("未取得詳細治療計畫書")
        pathology = path_reports[ident]
        specimen_results = defaultdict(set)
        for row in pathology:
            if row.get("病理編號") and row.get("結果"):
                specimen_results[row["病理編號"]].add(row["結果"])
        malignant = any(r.get("病理編號") and specimen_results[r["病理編號"]] == {"惡性"}
                        and r.get("層級") in {"完整報告", "最終報告"} for r in pathology)
        # A patient-level pathology record does not identify which primary
        # cancer it belongs to; never use it to fill this case's site or stage.
        warnings.append("有病理惡性紀錄，部位需核對" if malignant else "本批未找到病理惡性依據，不代表非癌症")
        if any(len(values)>1 for values in specimen_results.values()):
            warnings.append("同病理編號有不同結果，需核對完整報告")
        if reported_visit and reported_visit > cutoff:
            warnings.append("最近看診／掛號日超過統計截止日，可能為預約，需核對")
        shared["資料提醒"] = join(warnings)
        plan_dates = collect_plan_dates(case_plans + raw["_history"], cutoff)
        planned = dict(shared, **planned_values)
        plan_drug_names = planned_drugs(planned_values,root/"mapping/drug_treatment_mapping.csv")
        planned.update({"藥物種類數": len(plan_drug_names), "藥物摘要": join(plan_drug_names),
            "治療摘要": join(k for k, v in planned_values.items() if v), "計畫書日期": join(plan_dates),
            "計畫資料來源": join(p["_source"] for p in case_plans)})
        alive_open = not death and not closed and not raw.get("結案原因") and bool(cancer)
        old_followup = followup and (not diagnosis or followup >= diagnosis)
        due = (followup + relativedelta(months=rules.followup_months)) if old_followup else (diagnosis + timedelta(days=rules.first_treatment_days) if diagnosis else None)
        followup_status = "免追蹤：已死亡" if death else "免追蹤：已結案" if closed or raw.get("結案原因") else "癌別未填（資格待確認），不判斷" if not cancer else (
            "缺追蹤基準日" if due is None else
            ("需追蹤" if due < cutoff else "未到期") + ("（舊案追蹤）" if old_followup else "（新確診）") + f"：應追蹤日{due}，逾期{max(0,(cutoff-due).days)}天")
        absent = alive_open and last_visit and (cutoff - last_visit).days > rules.no_visit_days
        compare_kinds = [k for k in TREATMENTS.values() if k != "手術" or cancer_scope(cancer) in {"BR","CR","LC","LI","PR","BL"}]
        missing_plan = [k for k in compare_kinds if categories[k] and not planned_values[k]]
        missing_actual = [k for k in compare_kinds if planned_values[k] and not categories[k]]
        differences = [f"實際有{k}，計畫書未填" for k in missing_plan]
        differences += [f"計畫書有{k}，查無實際醫令" for k in missing_actual]
        classification = first(raw, "個案分類")
        class_zero = is_class_zero(classification)
        new = new_courses(categories, plan_dates, class_zero)
        new_text = "；".join(r["text"] for r in new)
        if class_zero:
            comparison = "不比對：首療於他院（Class 0）"
        elif not any(planned_values.values()) and not delivered:
            comparison = "無計畫書及實際治療資料"
        elif not any(planned_values.values()) and delivered:
            comparison = "否：無計畫書，" + "、".join(k for k in compare_kinds if categories[k]) + "有實際治療"
        else:
            comparison = "否："+"；".join(differences) if differences else "是"
        if new:
            description = "計畫書後新療程，需確認是否有新計畫書："+new_text
            comparison = comparison+"；"+description if comparison.startswith("否") else "需確認："+description
        if not exempt_plan(raw):
            if missing_plan:
                planned["資料提醒"] += "\n計畫書缺漏："+"、".join(missing_plan)+"（實際有執行）"
            if not any(planned_values.values()):
                planned["資料提醒"] += "\n無計畫書治療資料"
        mdt_dates = sorted({d for p in raw["_history"]+case_plans
                            if (d := day(p.get("多專科團隊會議日期"))) and d <= cutoff})
        advanced = any(re.match(r"^(?:III|IV|3|4)",text(v),re.I) for v in stage_rows["final_stage"])
        if advanced:
            shared["期別資料狀態"] += "；含第三四期"
            planned["期別資料狀態"] = shared["期別資料狀態"]
        recurrent = any("復發" in text(v) for p in case_plans for k,v in p.items() if k in {"治療分類","治療維護序","個案治療維護序"})
        mdt_needed = (advanced or recurrent) and not mdt_dates
        mdt_reason = "／".join(v for v in ["第三四期" if advanced else "", "復發" if recurrent else ""] if v)
        mdt = f"有（{len(mdt_dates)}次，最近{mdt_dates[-1]:%Y/%m/%d}）" if mdt_dates else (
            f"無（{mdt_reason}，建議提MDT）" if mdt_needed else "無（期別未填）" if stage_missing else "無（本批未見會議紀錄）")
        completion, incomplete, last_rt, interruptions, ccrt = radiation_review(categories,case_plans,plan_dates,cutoff,new)
        necessary = death_review(death if death and death <= cutoff else None, text(raw.get("結案原因")),categories,case_plans)
        actual = dict(shared)
        actual.update({k: event_summary(categories[k]) for k in TREATMENTS.values()})
        if categories["放療計畫"]:
            actual["放射治療"] = join([actual["放射治療"], "放療計畫（不計照射）："+event_summary(categories["放療計畫"])] )
        actual.update({"個案分類": classification, "結案日期/原因": join([closed, raw.get("結案原因")]),
            "死亡日期": death, "必要提報事件": necessary,
            "是否符合計畫書": comparison, "最近追蹤日": followup, "追蹤狀態": followup_status,
            "失聯狀態": f"疑似失聯：{(cutoff-last_visit).days}天未回診" if absent else ("無回診紀錄" if not last_visit else "未觸發逾90天提醒"),
            "藥物種類數": len({e["generic"].casefold() for e in drug_events}),
            "藥物摘要": join(e["generic"] for e in drug_events), "治療摘要": join(k for k in TREATMENTS.values() if categories[k]),
            "首次治療日": first_tx, "首次治療項目": join(e["category"] for e in delivered if e["date"] == first_tx),
            "診斷至首次治療天數": (first_tx - diagnosis).days if first_tx and diagnosis else None,
            "首次手術日": surgery, "術後至化療天數": (chemo-surgery).days if chemo else None,
            "術後至放療天數": (radiation-surgery).days if radiation else None,
            "放療完成度": completion, "放療中斷": join(r["text"] for r in interruptions),
            "MDT討論": mdt, "計畫書後新療程": new_text, "CCRT": ccrt,
            "收案年度": case_date.year if case_date else None, "收案季": f"Q{(case_date.month-1)//3+1}" if case_date else ""})
        report.planned.append(planned)
        report.actual.append(actual)
        task_start = len(report.tasks)
        if exempt_plan(raw):
            continue
        if not cancer and not death and not closed and not raw.get("結案原因"):
            add_task(shared, "癌別未填（資格待確認）", "有個案編號但缺癌別；不能由手術代碼推定癌症", diagnosis)
        if alive_open and stage_missing:
            add_task(shared, "期別未填", "請填獨立病人期別確認檔，非總表；確認結果只套用本個案", diagnosis, context=stage_display)
        if raw["_stage_conflict"]:
            add_task(shared, "期別來源衝突", "同期收案來源記錄不同期別，請核對", diagnosis)
        if alive_open and due and due < cutoff:
            add_task(shared, "需追蹤（舊案追蹤）" if old_followup else "需追蹤（新確診）", followup_status, due, (cutoff-due).days, context=f"追蹤期限:{due}")
        if absent:
            add_task(shared, "疑似失聯", "僅表示院內資料超過90天未回診，需聯繫確認", last_visit, (cutoff-last_visit).days-rules.no_visit_days)
        for kind, values in [("計畫書缺漏",missing_plan), ("計畫書有、查無實際治療",missing_actual if not class_zero else [])]:
            if values:
                add_task(shared,kind,"、".join(values),max(plan_dates,default=diagnosis))
        if not class_zero and alive_open and diagnosis and not delivered and rules.first_treatment_days < (cutoff-diagnosis).days <= 365:
            add_task(shared, "確診逾30天無院內治療", "本批查無已分類治療醫令；可能外院治療或來源不完整", diagnosis, (cutoff-diagnosis).days-rules.first_treatment_days)
        if not class_zero and first_tx and diagnosis and rules.first_treatment_days < (first_tx-diagnosis).days <= 365 and diagnosis.year >= cutoff.year-1:
            add_task(shared, "首療等候逾30天", "依本批最早治療醫令日期計算，請核對真實首療日期", first_tx, (first_tx-diagnosis).days-rules.first_treatment_days)
        if chemo and (chemo-surgery).days > rules.adjuvant_chemo_days and surgery.year >= cutoff.year-1:
            add_task(shared, "術後化療逾8週", "依醫令日期篩檢，未判定是否為輔助治療，請核對療程", chemo, (chemo-surgery).days-rules.adjuvant_chemo_days)
        if necessary.startswith("疑似必要提報"):
            add_task(shared,"疑似必要提報",necessary,death)
        for interruption in interruptions:
            add_task(shared,"放療暫停（重新計畫）" if interruption["replan"] else "放療中斷",
                     interruption["text"],interruption["start"],interruption["days"])
        if incomplete:
            add_task(shared,"放療未完成",completion,last_rt,(cutoff-last_rt).days-14)
        if alive_open and mdt_needed:
            add_task(shared,"應提MDT未討論",mdt,diagnosis)
        if alive_open and not malignant:
            add_task(shared,"查無病理惡性報告","本批未找到病理惡性依據，不代表非癌症",diagnosis)
        for course in new:
            add_task(shared,"計畫書後新療程",course["text"],course["start"],course["days"])
        if (class_zero and (closed or raw.get("結案原因"))) or "轉院" in text(raw.get("結案原因")):
            report.tasks[task_start:] = [t for t in report.tasks[task_start:]
                                         if t["待辦類型"] in {"計畫書缺漏","計畫書後新療程"}]
    known = {r["_mrn"] for r in cases}
    for ident in sorted({r["_mrn"] for r in sources.cases if not r["_case"]}):
        report.pending.append({"病歷號":ident,"個案編號":"","待確認原因":"收案來源缺個案編號，未自動建立或合併癌症個案"})
    for ident in sorted(set(by_patient) - known):
        report.pending.append({"病歷號": ident, "個案編號": "", "待確認原因": "只有醫令／藥物資料，未連結收案個案；未納入總表", "來源檔案": join(e["source"] for e in by_patient[ident])})
    report.events = events
    add_pathology_pending(report, sources.pathology)
    report.tasks.sort(key=lambda r: ({"紅":0,"黃":1,"灰":2}[r["嚴重度"]],r["個管師"], r["待辦類型"], -(r["逾期天數"] or 0), r["病歷號"], r["個案編號"]))
    return report
