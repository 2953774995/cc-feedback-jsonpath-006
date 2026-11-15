#!/usr/bin/env python3
"""多路径批量抽取验收探针。

契约：
  from jsonpath_ng.batch import extract
  res = extract(data, {"books": "$.store.books[*].title", "ghost": "$.store.videos[*]"})
  res.values   匹配到的值，按输入顺序
  res.missing  未匹配到任何结果的路径名
  res.errors   {路径名: 错误信息}，解析失败的路径不抛异常
  res.ok       errors 与 missing 都为空时为 True
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

FAILED = 0
PASSED = 0


def check(code, desc, fn):
    global FAILED, PASSED
    try:
        fn()
        print(f"[PASS] {code} {desc}")
        PASSED += 1
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] {code} {desc}")
        print(f"        {type(exc).__name__}: {exc}")
        FAILED += 1


DATA = {
    "store": {
        "books": [
            {"title": "A", "price": 8.95},
            {"title": "B", "price": 12.99},
        ],
        "bicycle": {"color": "red"},
    }
}


def main():
    try:
        from jsonpath_ng.batch import extract  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] P0 导入 jsonpath_ng.batch 失败：{type(exc).__name__}: {exc}")
        print("-" * 60)
        print("探针汇总：0/7 通过")
        return 1

    def p1():
        r = extract(DATA, {"titles": "$.store.books[*].title"})
        assert r.values["titles"] == ["A", "B"], r.values
        assert "titles" not in r.missing
        assert r.errors == {}

    def p2():
        r = extract(DATA, {"titles": "$.store.books[*].title", "videos": "$.store.videos[*]"})
        assert r.missing == ["videos"], r.missing
        assert r.ok is False

    def p3():
        r = extract(DATA, {"broken": "$.store.books[", "titles": "$.store.books[*].title"})
        assert "broken" in r.errors, r.errors
        assert r.values["titles"] == ["A", "B"], "解析失败不应影响其它路径"
        assert r.ok is False

    def p4():
        r = extract(DATA, {"titles": "$.store.books[*].title"})
        assert r.ok is True, (r.errors, r.missing)

    def p5():
        r = extract(DATA, {"prices": "$.store.books[*].price"})
        assert r.values["prices"] == [8.95, 12.99], r.values

    def p6():
        r = extract(DATA, {"colors": "$.store.bicycle.color"})
        assert r.values["colors"] == ["red"], r.values

    def p7():
        try:
            extract(["not", "a", "dict"], {"any": "$.x"})
        except (TypeError, ValueError):
            return
        raise AssertionError("非字典输入未报错")

    check("P1", "单路径正常抽取", p1)
    check("P2", "无匹配路径进 missing", p2)
    check("P3", "非法路径进 errors 且不影响其它路径", p3)
    check("P4", "全部命中时 ok 为 True", p4)
    check("P5", "数值结果按顺序返回", p5)
    check("P6", "标量命中仍以列表返回", p6)
    check("P7", "非字典输入报错", p7)

    print("-" * 60)
    print(f"探针汇总：{PASSED}/{PASSED + FAILED} 通过")
    return 0 if FAILED == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
