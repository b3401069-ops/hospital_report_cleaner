"""Administrative screening rules from the hospital's 1151028 specification.

These are not clinical guidelines. An order is evidence to review, not proof
of administration, diagnosis, treatment appropriateness or reportability.
"""
from collections import defaultdict
from datetime import date, timedelta
from functools import lru_cache
import re
import csv

from .case_manager_sources import cancer_scope, day, text, TREATMENTS

RADIATION_CODES = {"36011B", "36012B"}
SUPPORTIVE = re.compile(
    r"leucovorin|folinate|denosumab|zoledronic|ibandronic|romosozumab|mesna|"
    r"urokinase|\bTPA\b|pirfenidone|nintedanib|azathioprine", re.I)
DRUG_OVERRIDES = {
    "化學治療": r"tegafur|\bUFUR\b|trifluridine|tipiracil",
    "抗荷爾蒙治療": r"flutamide",
    "標靶治療": r"trametinib|dabrafenib|mobocertinib|alpelisib|sotorasib",
}


def generic_name(name):
    value = re.sub(r"\b(?:HCl|hydrochloride|acetate|sodium|hydrate|trihydrate|"
                   r"monohydrate|mesylate|maleate|phosphate|sulfate)\b", "", name, flags=re.I)
    value = re.sub(r"\d+(?:\.\d+)?\s*(?:mg|mcg|ug|g|ml|iu|units?)\b.*", "", value, flags=re.I)
    value = re.sub(r"\b(?:injection|tablets?|capsules?|inj|tab|cap)\b.*", "", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip(" ,-/()")


def planned_drugs(values, mapping):
    content = " ".join(v for k,v in values.items() if k in {"化學治療","標靶治療","免疫治療","抗荷爾蒙治療","CCRT"})
    found = set()
    with mapping.open(encoding="utf-8-sig",newline="") as handle:
        for rule in csv.DictReader(handle):
            pattern = rule.get("name_pattern","")
            # Only literal generic names are suitable as display labels.
            if pattern and re.fullmatch(r"[A-Za-z][A-Za-z /-]*",pattern) and re.search(r"\b"+re.escape(pattern)+r"\b",content,re.I):
                found.add(pattern.title())
    for pattern, drugs in [
        (r"\bFOLFOX\b", ["Fluorouracil","Oxaliplatin","Leucovorin"]),
        (r"\bCapeOX\b|\bXELOX\b",["Capecitabine","Oxaliplatin"]),
        (r"\bEpiC\b|\bEC\b",["Epirubicin","Cyclophosphamide"]),
        (r"\bLenozole\b",["Letrozole"]), (r"\bTagrisso\b",["Osimertinib"]),
        (r"\bUFUR\b",["Tegafur/Uracil"]),
    ]:
        if re.search(pattern,content,re.I):
            found.update(drugs)
    return sorted(found)


def reclassify(event):
    e = dict(event)
    code, name = e["code"], e["name"]
    e["note"] = ""
    e["generic"] = generic_name(name) if e["drug"] else ""
    if e["drug"]:
        if SUPPORTIVE.search(name):
            e.update(category="未分類藥物", note="支持性／非癌症治療")
        elif code == "OMET3" or (re.search(r"methotrexate.*2\.5\s*mg", name, re.I)
                                 and not re.search(r"inj|注射",name,re.I)):
            e.update(category="未分類藥物", note="口服低劑量Methotrexate，癌症用途待確認")
        else:
            for category, pattern in DRUG_OVERRIDES.items():
                if re.search(pattern, name, re.I):
                    e["category"] = category
                    break
    elif code in {"63010C", "50014C"}:
        e.update(category="未分類醫令", scope="",
                 note="支持性／非癌症治療" if code == "50014C" else "切片不列手術治療")
    elif code in {"67050B", "67051B", "67053B", "70213B", "70214B"}:
        e.update(category="手術", scope="LC")
    elif code in {"79403B", "79410B", "79417B"}:
        e.update(category="手術", scope="PR")
    elif code in RADIATION_CODES:
        e.update(category="放射治療", scope="")
    elif code == "36015B":
        e.update(category="放療計畫", scope="")
    elif code == "50011C":
        e.update(category="化學治療", scope="BL")
    e["location"] = {"O":"門診", "I":"住院", "E":"急診", "門":"門診", "住":"住院", "急":"急診"}.get(e["location"], e["location"])
    return e


def is_class_zero(value):
    return bool(re.match(r"^(?:class\s*)?0(?:\D|$)", text(value), re.I))


def exempt_plan(raw):
    return is_class_zero(raw.get("個案分類")) and any(
        word in text(raw.get("結案原因")) for word in ("轉院", "死亡(未治療)", "死亡（未治療）", "未治療死亡", "拒絕"))


@lru_cache(maxsize=32)
def holiday_calendar(start=2019, end=2027):
    import holidays
    # Public includes substitute and bridge holidays; Saturdays remain excluded
    # even when government calendars designate a make-up workday.
    return dict(holidays.TW(years=range(start, end+1), language="zh_TW", observed=True))


def courses(events, gap):
    groups = []
    for d in sorted({e["date"] for e in events if e["date"]}):
        if not groups or (d-groups[-1][-1]).days > gap:
            groups.append([])
        groups[-1].append(d)
    return groups


def plan_dates(rows, cutoff):
    return sorted({d for r in rows for k,v in r.items()
                   if not k.startswith("_") and "日期" in k
                   and ("填寫" in k or "計畫書" in k or "計劃書" in k
                        or k.startswith(("標靶", "荷爾蒙", "口服", "膀胱灌", "CCRT")))
                   and (d := day(v)) and d <= cutoff})


def new_courses(categories, dates, class_zero):
    results = []
    if class_zero:
        return results
    for kind in TREATMENTS.values():
        if kind == "抗荷爾蒙治療":
            continue
        gap = 30 if kind in {"手術", "肝動脈栓塞（TACE）", "射頻燒灼（RFA）"} else 60
        events = categories[kind]
        if kind == "放射治療":
            events = [e for e in events if e["code"] in RADIATION_CODES]
        for group in courses(events, gap):
            previous = max((d for d in dates if d <= group[0]), default=None)
            if previous and (group[0]-previous).days > 183:
                results.append({"kind":kind,"start":group[0],"end":group[-1],
                    "days":(group[0]-previous).days-183,
                    "text":f"{kind} {group[0]:%Y/%m/%d} 開始（距計畫書 {previous:%Y/%m/%d} 共 {(group[0]-previous).days} 天）"})
    return results


def fraction_count(value):
    values = re.findall(r"(\d+)\s*(?:fx\b|fr\b|fractions?\b|次)", value, re.I)
    values += re.findall(r"Gy\s*[x×*]\s*(\d+)", value, re.I)
    return max((int(v) for v in values if 1 <= int(v) <= 45), default=None)


def radiation_review(categories, plans, dates, cutoff, new):
    irradiation = [e for e in categories["放射治療"] if e["code"] in RADIATION_CODES]
    days = sorted({e["date"] for e in irradiation})
    holidays = holiday_calendar(min([2019]+[d.year for d in days]), max(2027, cutoff.year))
    interruptions = []
    for left, right in zip(days, days[1:]):
        if (right-left).days > 21:
            continue
        between = [left+timedelta(days=n) for n in range(1,(right-left).days)]
        missed = sum(d.weekday()<5 and d not in holidays for d in between)
        holiday_days = sum(d.weekday()<5 and d in holidays for d in between)
        if missed < 5:
            continue
        replan = min((e["date"] for e in categories["放療計畫"]
                      if left < e["date"] <= right+timedelta(days=3)), default=None)
        description = f"{left:%Y/%m/%d}→{right:%Y/%m/%d} 間隔{(right-left).days}天（缺{missed}個工作日，已扣國定假日{holiday_days}天）"
        if replan:
            description += f"；{replan:%Y/%m/%d} 重新放療計畫，疑似 re-plan 暫停"
        else:
            description += "；放療中斷（初篩）"
        interruptions.append({"start":left,"days":missed-4,"text":description,"replan":replan})
    prescriptions = []
    for p in plans:
        for prefixes in [("放射線治療", "放療", "DOSECGY"), ("CCRT",)]:
            fields = {k:v for k,v in p.items() if k.startswith(prefixes)
                      and not (cancer_scope(p.get("_cancer")) == "LI" and k == "放療其他說明")}
            n = fraction_count(" ".join(text(v) for v in fields.values()))
            dated = [day(v) for k,v in fields.items() if "日期" in k and day(v) and day(v)<=cutoff]
            when = max(dated,default=None)
            if when and n:
                prescriptions.append((when,n))
    incomplete, related = False, None
    if prescriptions:
        when, n = max(prescriptions)
        # A chain of entries no more than 60 days apart belongs to one plan.
        anchor = when
        end = cutoff
        for d in (d for d in dates if d > when):
            if (d-anchor).days > 60:
                end = d-timedelta(days=1)
                break
            anchor = d
        start = when-timedelta(days=30)
        included = [d for d in days if start <= d <= end and not any(
            r["kind"]=="放射治療" and r["start"]<=d<=r["end"] for r in new)]
        span = f"計畫書 {when:%Y/%m/%d}～{end:%Y/%m/%d}期間"
        if not included:
            completion = f"計畫{n}次，{span}查無照射紀錄"
        else:
            ratio = len(included)/n
            related = included[-1]
            incomplete = ratio < .8 and (cutoff-related).days > 14
            completion = f"實際{len(included)}次／計畫{n}次（{ratio:.0%}；{span}）" + ("，未完成" if incomplete else "")
    else:
        completion = f"實際{len(days)}次（計畫書無分次數）" if days else "本批無照射紀錄／可用分次計畫"
    concurrent = []
    for group in courses(irradiation,30):
        chemo = {e["date"] for e in categories["化學治療"]
                 if group[0]-timedelta(days=7)<=e["date"]<=group[-1]+timedelta(days=7)}
        if chemo:
            concurrent.append(f"疑似同步：放療{group[0]:%Y/%m/%d}～{group[-1]:%Y/%m/%d}期間化療{len(chemo)}次")
    return completion, incomplete, related, interruptions, "\n".join(concurrent)


def death_review(death, reason, categories, plans):
    if any(w in reason for w in ("死亡(未治療)", "死亡（未治療）", "未治療死亡")):
        return "排除：結案原因為死亡(未治療)"
    if not death:
        return ""
    included, excluded = [], []
    purpose_prefixes = {"化學治療":("化學治療目的", "口服化療目的", "口服化療治療目的"),
                        "放射治療":("放射線治療目的", "放療目的"),
                        "標靶治療":("標靶",), "免疫治療":("免疫",)}
    for kind in TREATMENTS.values():
        if kind == "抗荷爾蒙治療":
            continue
        candidates = [e["date"] for e in categories[kind] if e["date"]<=death
                      and (kind!="放射治療" or e["code"] in RADIATION_CODES)]
        last = max(candidates,default=None)
        if not last or (death-last).days > 30:
            continue
        purposes = [text(v) for p in plans for k,v in p.items() if "目的" in k
                    and k.startswith(purpose_prefixes.get(kind,("__none__",))) and text(v)]
        # Mixed curative/palliative records must not suppress a reportable flag.
        palliative = purposes and all("palliative" in v.lower() for v in purposes)
        description = f"{kind}後30日內死亡（{last:%Y/%m/%d}→{death:%Y/%m/%d}）"
        (excluded if palliative else included).append(description)
    if included:
        return "疑似必要提報："+"；".join(included)+"，請核對"+("（已排除Palliative："+"；".join(excluded)+"）" if excluded else "")
    if excluded:
        return "排除：治療目的為Palliative（"+"；".join(excluded)+"）"
    return "有死亡日期，未落在治療後30日內（請人工核對）"


ACTIONS = {
    "疑似必要提報":"調閱病歷，依認證定義確認是否提報",
    "疑似失聯":"電話追蹤，確認是否轉院或中斷治療",
    "確診逾30天無院內治療":"確認治療計畫、是否外院治療或拒絕治療",
    "放療中斷":"確認中斷原因（副作用、住院、交通等）",
    "放療暫停（重新計畫）":"確認是否為計畫性 re-plan／boost 暫停；若非，確認中斷原因",
    "放療未完成":"確認是否計畫變更、外院續照或中止",
    "需追蹤（新確診）":"安排追蹤並於個管系統登錄",
    "需追蹤（舊案追蹤）":"安排追蹤並於個管系統登錄",
    "計畫書缺漏":"請主治醫師補填計畫書",
    "計畫書有、查無實際治療":"確認是否外院執行、病人拒絕或計畫變更",
    "期別未填":"核對TNM與期別；填獨立病人期別確認檔",
    "期別來源衝突":"請醫師核對不同來源期別，不自動覆蓋",
    "應提MDT未討論":"排入多專科團隊會議",
    "首療等候逾30天":"了解延遲原因，納入品質檢討",
    "術後化療逾8週":"了解延遲原因",
    "計畫書後新療程":"確認是否有新計畫書（復發／階段性治療改變），若無請醫師補填",
    "查無病理惡性報告":"確認是否外院病理或臨床診斷",
    "癌別未填（資格待確認）":"確認是否符合癌症收案資格",
}
RED = {"疑似必要提報","疑似失聯","確診逾30天無院內治療","放療中斷"}
GRAY = {"查無病理惡性報告","癌別未填（資格待確認）"}
