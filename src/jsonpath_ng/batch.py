"""多路径批量抽取。

一次求值多条 JSONPath 表达式，结果按路径分类返回：
匹配值、未命中、解析/求值错误，互不影响。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping

from .exceptions import JSONPathError
from .parser import parse

__all__ = ["extract", "BatchResult"]


@dataclass
class BatchResult:
    """批量抽取结果。

    values:  路径名 -> 匹配到的值列表（按文档内出现顺序；标量命中也是长度 1 的列表）
    missing: 一个都没匹配到的路径名列表（按输入顺序）
    errors:  路径名 -> 错误信息字符串（解析或求值失败）
    ok:      errors 与 missing 都为空时为 True
    """

    values: Dict[str, List[Any]] = field(default_factory=dict)
    missing: List[str] = field(default_factory=list)
    errors: Dict[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not self.errors and not self.missing


def extract(data: Any, paths: Mapping[str, str]) -> BatchResult:
    """对 ``data`` 批量求值 ``paths``（路径名 -> JSONPath 表达式）。

    单条路径解析或求值失败不会中断整批，只记入 ``errors``。
    """
    if not isinstance(data, dict):
        raise TypeError(
            f"extract() 的第一个参数必须是 dict，收到 {type(data).__name__}"
        )
    if not isinstance(paths, Mapping):
        raise TypeError(
            f"extract() 的 paths 参数必须是映射（路径名 -> 表达式），收到 {type(paths).__name__}"
        )

    result = BatchResult()
    for name, expr in paths.items():
        try:
            parsed = parse(expr)
        except JSONPathError as exc:
            result.errors[name] = str(exc) or repr(exc)
            continue
        try:
            matches = [match.value for match in parsed.find(data)]
        except JSONPathError as exc:
            result.errors[name] = str(exc) or repr(exc)
            continue
        result.values[name] = matches
        if not matches:
            result.missing.append(name)
    return result
