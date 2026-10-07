"""공유본(index.html) 스냅샷 갱신.

사용: python3 tools/build_snapshot.py <ArtifactData out_dir> "YYYY-MM-DD HH:MM"
- out_dir 아래 <collection>/<doc_id>.json 파일을 읽어 index.html의 DATA 블록을 교체
- out_dir에 없는 컬렉션은 기존 값 유지
- 배지의 '기준 시각' 갱신
"""
import json, re, sys, pathlib

root = pathlib.Path(__file__).resolve().parent.parent
html_path = root / "index.html"
src, stamp = pathlib.Path(sys.argv[1]), sys.argv[2]

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

new_line = "  var DATA=" + json.dumps(data, ensure_ascii=False) + ";"
html = html[: m.start()] + new_line + html[m.end():]
html, n = re.subn(r"읽기 전용 공유본 · [0-9-]+ [0-9:]+ 기준", f"읽기 전용 공유본 · {stamp} 기준", html)
if n == 0:
    sys.exit("기준 시각 배지를 찾지 못함")
html_path.write_text(html, encoding="utf-8")
print("updated:", {k: len(v) for k, v in data.items()}, "stamp:", stamp)
