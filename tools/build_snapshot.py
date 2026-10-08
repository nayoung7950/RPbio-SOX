"""공유본(index.html) 스냅샷 갱신.

사용: python3 tools/build_snapshot.py <ArtifactData out_dir> "YYYY-MM-DD HH:MM"
- out_dir 아래 <collection>/<doc_id>.json 파일을 읽어 index.html의 DATA 블록을 교체
- out_dir에 없는 컬렉션은 기존 값 유지
- 공개 원칙(PUBLIC_FIELDS)에 없는 항목은 제거
- 배지의 '기준 시각' 갱신
"""
import json, re, sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
html_path = root / "index.html"
src, stamp = pathlib.Path(sys.argv[1]), sys.argv[2]

# 공개 저장소 노출 원칙(2026-10-07): 상태·짧은 사유 유형만 게시.
# 거래처명·금액·전표번호·담당자 실명·상세 사유는 원본(Claude 현황판)에만 둔다.
PUBLIC_FIELDS = {
    "pbc": {"cid", "cname", "dept", "due", "no", "period", "req", "reqDate",
            "round", "status", "updated", "checkResult", "checkReason"},
    "samples": {"cid", "cname", "round", "due", "ev", "status", "updated",
                "checkResult", "checkReason"},
}
MASK = {"samples": {"sample": lambda i: f"샘플{i:02d}", "amount": lambda i: "",
                    "date": lambda i: "", "desc": lambda i: "", "note": lambda i: ""}}


def sanitize(col, docs):
    allow = PUBLIC_FIELDS.get(col)
    if allow is None:  # 정의되지 않은 컬렉션(outbox 등)은 게시하지 않음
        return []
    out = []
    for i, d in enumerate(docs, 1):
        clean = {k: v for k, v in d["data"].items() if k in allow}
        for k, fn in MASK.get(col, {}).items():
            clean[k] = fn(i)
        out.append({"id": f"s{i:03d}" if col == "samples" else d["id"], "data": clean})
    return out


html = html_path.read_text(encoding="utf-8")
m = re.search(r"^  var DATA=(.*);$", html, re.M)
if not m:
    sys.exit("DATA 블록을 찾지 못함")
data = json.loads(m.group(1))

for col_dir in sorted(p for p in src.iterdir() if p.is_dir()):
    docs = []
    for f in sorted(col_dir.glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        d = d.get("data", d) if isinstance(d, dict) and set(d) <= {"id", "data", "version"} else d
        docs.append({"id": f.stem, "data": d})
    data[col_dir.name] = docs

data = {k: sanitize(k, v) for k, v in data.items()}

new_line = "  var DATA=" + json.dumps(data, ensure_ascii=False) + ";"
html = html[: m.start()] + new_line + html[m.end():]
html, n = re.subn(r"읽기 전용 공유본 · [0-9-]+ [0-9:]+ 기준", f"읽기 전용 공유본 · {stamp} 기준", html)
if n == 0:
    sys.exit("기준 시각 배지를 찾지 못함")
html_path.write_text(html, encoding="utf-8")
print("updated:", {k: len(v) for k, v in data.items()}, "stamp:", stamp)
