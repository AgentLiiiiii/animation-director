"""Read-only structural checks. A pass is NOT an animation-quality verdict."""

import argparse
import json
import re
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path


NUMBER = r"\d+(?:\.\d+)?"
STAMP = r"\d{1,3}:\d{2}(?:\.\d+)?"
SPAN = re.compile(
    rf"^[\[【]\s*({STAMP})\s*[-–—~～至]\s*({STAMP})\s*[\]】]\s*(.*)$"
)
TIMELINE = re.compile(rf"时间线(?:[（(]\s*({NUMBER})\s*(?:秒|s)\s*[）)])?", re.I)
LIMITATION = "仅检查结构与时间；弹性、张力、运镜效果、动作因果及文字中的约束归属仍需模型复核。"


def label(line):
    value = re.sub(r"^#{1,6}\s+", "", line.strip()).rstrip("：:").strip()
    if value.startswith("**") and value.endswith("**"):
        value = value[2:-2].strip().rstrip("：:")
    return value


def seconds(stamp):
    minute, second = stamp.split(":")
    if Decimal(second) >= 60:
        raise ValueError("时间码的秒字段必须小于60")
    return Decimal(minute) * 60 + Decimal(second)


def validate(text, expected_duration=None, require_code_block=False):
    errors = []

    def fail(code, message, line=None):
        item = {"code": code, "message": message}
        if line is not None:
            item["line"] = line
        errors.append(item)

    def result(total=None, count=0):
        return {"ok": not errors, "scope": "structure_and_timing_only",
                "duration_seconds": str(total) if total is not None else None,
                "segment_count": count, "errors": errors, "limitation": LIMITATION}

    rows = [(n, line.strip()) for n, line in enumerate(text.lstrip("\ufeff").splitlines(), 1)
            if line.strip()]
    fences = [(i, value) for i, (_, value) in enumerate(rows)
              if value.startswith(("```", "~~~"))]
    if fences:
        if (len(fences) != 2 or fences[0][0] != 0 or fences[-1][0] != len(rows) - 1
                or not re.fullmatch(r"(```|~~~)[\w-]*", fences[0][1])
                or fences[-1][1] != fences[0][1][:3]):
            fail("code_block", "应只有一个完整代码块，块外不得有文字。")
            return result()
        rows = rows[1:-1]
    elif require_code_block:
        fail("code_block", "正式交付必须放在一个代码块中。")

    if expected_duration is not None:
        try:
            expected_duration = Decimal(str(expected_duration))
            if not expected_duration.is_finite() or not 4 <= expected_duration <= 30:
                raise ValueError()
        except (InvalidOperation, ValueError):
            fail("expected_duration", "指定总时长必须是4–30秒之间的有限数值。")
            return result()

    sections = []
    for index, (line_no, line) in enumerate(rows):
        title = label(line)
        match = TIMELINE.fullmatch(title)
        if title in ("画面内容", "全局约束") or match:
            sections.append((index, "时间线" if match else title,
                             Decimal(match[1]) if match and match[1] else None))
        elif title in ("声音设计", "音效设计", "音效时间表"):
            fail("sound_section", "不得保留独立的声音设计或音效栏目。", line_no)
        elif re.match(r"^#{1,6}\s+", line):
            fail("extra_heading", "提示词内出现额外标题。", line_no)
        elif title.startswith("时间线"):
            fail("timeline_heading", "时间线标题格式应为“时间线”或“时间线（14秒）”。", line_no)

    if [part[1] for part in sections] != ["画面内容", "时间线", "全局约束"]:
        fail("sections", "三项必须各出现一次，顺序为画面内容、时间线、全局约束。")
        return result()
    if sections[0][0] != 0:
        fail("preamble", "画面内容之前不得有前言或约束段落。", rows[0][0])

    bodies = {}
    for i, (start, title, _) in enumerate(sections):
        stop = sections[i + 1][0] if i + 1 < len(sections) else len(rows)
        bodies[title] = rows[start + 1:stop]
        if not bodies[title]:
            fail("empty_section", f"{title}不能为空。", rows[start][0])

    for title in ("画面内容", "全局约束"):
        for line_no, line in bodies[title]:
            if SPAN.fullmatch(line):
                fail("misplaced_timecode", "分镜时间码只能放在时间线中。", line_no)

    timeline = bodies["时间线"]
    if timeline and not SPAN.fullmatch(timeline[0][1]):
        fail("timeline_preamble", "时间线标题后应直接进入首个时间码，不插入约束段落。", timeline[0][0])
    segments = []
    for line_no, line in timeline:
        match = SPAN.fullmatch(line)
        if match:
            try:
                start, end = seconds(match[1]), seconds(match[2])
            except ValueError as exc:
                fail("timecode", str(exc), line_no)
                continue
            segments.append({"start": start, "end": end, "line": line_no,
                             "has_body": bool(match[3])})
        elif re.match(r"^[\[【]\s*\d", line):
            fail("timecode", "时间码格式无效，应如[00:00–00:03.3]。", line_no)
        elif segments:
            segments[-1]["has_body"] = True

    if not segments:
        fail("no_segments", "缺少有效的分镜时间段。")
        return result()
    previous = Decimal(0)
    for segment in segments:
        start, end, line_no = segment["start"], segment["end"], segment["line"]
        if start > previous:
            fail("gap", f"时间线存在空档：应从{previous}秒开始，实际从{start}秒开始。", line_no)
        elif start < previous:
            fail("overlap", f"时间线重叠或重置：应从{previous}秒开始，实际从{start}秒开始。", line_no)
        if end <= start:
            fail("nonpositive_span", "每个时间段的结束必须晚于开始。", line_no)
        if not segment["has_body"]:
            fail("empty_segment", "时间段缺少动作或运镜正文。", line_no)
        previous = end
    total = segments[-1]["end"]
    if not 4 <= total <= 30:
        fail("duration_range", "整个单元必须为4–30秒；内部单段可以短于4秒。")
    declared = sections[1][2]
    if declared is not None and declared != total:
        fail("declared_duration", f"标题时长{declared}秒与时间线终点{total}秒不一致。")
    if expected_duration is not None and expected_duration != total:
        fail("requested_duration", f"要求时长{expected_duration}秒与时间线终点{total}秒不一致。")
    return result(total, len(segments))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="-", help="UTF-8提示词文件；-表示标准输入")
    parser.add_argument("--duration", help="用户指定的总时长（秒），用于核对终点")
    parser.add_argument("--require-code-block", action="store_true", help="同时验证正式交付的单代码块包装")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        text = (sys.stdin.buffer.read().decode("utf-8-sig") if args.path == "-"
                else Path(args.path).read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError) as exc:
        print(json.dumps({"ok": False, "errors": [{"code": "input", "message": str(exc)}]}, ensure_ascii=False))
        return 2
    report = validate(text, args.duration, args.require_code_block)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
