#!/usr/bin/env python3
"""Independently verify PSPV/PTDV Data Summary values; see README.md."""
import argparse
import csv
import io
import json
import math
from pathlib import Path
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import warnings

import numpy as np
import pandas as pd
from scipy import stats

METRICS = ["mean", "sd", "sem", "95CI mean", "median", "MAD", "IQR", "Q1", "Q3", "95CI median"]
COMPONENTS = {"PSPV": "PlotsOfData", "PTDV": "PlotsTwist"}
NUMBER = r"[+-]?(?:(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?|nan|inf(?:inity)?)"
INTERVAL = re.compile(r"^\s*(" + NUMBER + r")\s+-\s+(" + NUMBER + r")\s*$", re.I)


def prepare_matrix(text, module, tidy):
    # Match the panel's data selection, but calculate every metric independently.
    data = pd.read_csv(io.StringIO(text), index_col=0 if module == "PTDV" else None)
    if tidy:
        data = data.pivot_table(index=tidy["x"], columns=[tidy["idc"], tidy["ids"]],
                                values=tidy["y"], aggfunc="mean", sort=True,
                                dropna=True, observed=False)
        data.columns = ["_".join(map(str, col)).replace(" ", "_") for col in data.columns]
    if module == "PSPV":
        data = data.select_dtypes(include=["number"])
        key = "Condition"
    else:
        data = data.T
        key = str(data.columns.name)
        if not all(pd.api.types.is_numeric_dtype(dtype) for dtype in data.dtypes):
            raise ValueError("PTDV 样本列包含非数值类型；不能悄悄强制转数值或删除这些观测。")
    if not len(data.columns):
        raise ValueError("没有可检验的统计对象。检查数值列和 tidy 配置。")
    if key in ["n"] + METRICS:
        raise ValueError("PTDV 索引名称与统计字段重名，无法无歧义地比较。")
    return data, key


def independent_rows(matrix, key):
    rows = []
    for position, label in enumerate(matrix.columns):
        values = matrix.iloc[:, position].dropna().to_numpy(dtype=float)
        if np.isinf(values).any():
            raise ValueError("检测到无穷值：请核查输入，脚本不会将其当作缺失值删除。")
        n = len(values)
        mean = float(np.mean(values)) if n else math.nan
        median = float(np.median(values)) if n else math.nan
        sd = float(np.std(values, ddof=1)) if n >= 2 else math.nan
        sem = sd / math.sqrt(n) if n else math.nan
        # pandas .mad() means mean absolute deviation, NOT median_abs_deviation.
        mad = float(np.mean(np.abs(values - mean))) if n else math.nan
        q1, q3 = (pd.Series(values).quantile([0.25, 0.75], interpolation="linear").tolist()
                  if n else (math.nan, math.nan))
        # Positional confidence argument works with both old and new SciPy.
        # Retain SciPy's NaN result for zero scale and insufficient degrees of freedom.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            mean_ci = stats.t.interval(0.95, n - 1, loc=mean, scale=sem)
            median_ci = stats.t.interval(0.95, n - 1, loc=median, scale=sem)
        rows.append({key: label, "n": n, "mean": mean, "sd": sd, "sem": sem,
                     "95CI mean": tuple(map(float, mean_ci)), "median": median,
                     "MAD": mad, "IQR": float(q3 - q1), "Q1": float(q1),
                     "Q3": float(q3), "95CI median": tuple(map(float, median_ci))})
    return rows


def displayed_rows(rows, key, digits):
    result = []
    for row in rows:
        shown = {}
        for name, value in row.items():
            if name == key or name == "n":
                shown[name] = value
            elif name.startswith("95CI"):
                shown[name] = "{} - {}".format(*(round(np.float64(v), digits) for v in value))
            else:
                # Iterating the panel's pandas Series yields Python scalars;
                # interval endpoints above come from NumPy arrays instead.
                shown[name] = round(float(value), digits)
        result.append(shown)
    return result


def validate_columns(columns):
    if not columns or len(columns) != len(set(columns)):
        raise ValueError("界面表格的列名为空或重复。")


def load_observed(path, module):
    if path.suffix.lower() == ".csv":
        text = path.read_text(encoding="utf-8-sig")
        columns = next(csv.reader(io.StringIO(text)), [])
        validate_columns(columns)
        table = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
        return columns, table.to_dict("records")
    if path.suffix.lower() != ".json":
        raise ValueError("--observed 仅支持面板导出的 CSV 或 JSON。")
    return unpack_table(json.loads(path.read_text(encoding="utf-8-sig")), module)


def unpack_table(payload, module):
    component = "[" + COMPONENTS[module] + "/DataSummary]show_data"
    if isinstance(payload, dict) and "response" in payload:
        payload = payload["response"][component]
    if isinstance(payload, list):
        if not payload or not isinstance(payload[0], dict):
            raise ValueError("JSON 应为非空 records 列表。")
        columns, rows = list(payload[0]), payload
    elif isinstance(payload, dict) and "columns" in payload and "data" in payload:
        columns = [c["id"] if isinstance(c, dict) else c for c in payload["columns"]]
        rows = payload["data"]
    else:
        raise ValueError("无法识别界面 JSON：支持 Dash response、{columns,data} 或 records。")
    validate_columns(columns)
    if not isinstance(rows, list) or not all(isinstance(row, dict) for row in rows):
        raise ValueError("界面 data 必须是 records 列表。")
    # A record may also contain unselected metrics: only visible columns count.
    return columns, rows


def fetch_panel(base_url, module, text, tidy, digits, timeout):
    parsed = urllib.parse.urlsplit(base_url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError("--base-url 必须是 HTTP/HTTPS 平台地址。")
    group = COMPONENTS[module]
    component = "[" + group + "/DataSummary]show_data"
    outputs = [{"id": component, "property": prop} for prop in ("columns", "data")]
    payload = {
        "output": ".." + component + ".columns..." + component + ".data..",
        "outputs": outputs,
        "inputs": [
            {"id": "[" + group + "/DataSummary]check_show", "property": "value", "value": METRICS},
            {"id": "[" + group + "/DataSummary]digits", "property": "value", "value": str(digits)},
        ],
        "state": [
            {"id": "[" + group + "]data_input", "property": "data", "value": text},
            {"id": "[" + group + "]data_tiny", "property": "data", "value": tidy},
        ],
        "changedPropIds": ["[" + group + "/DataSummary]check_show.value"],
    }
    request = urllib.request.Request(base_url.rstrip("/") + "/_dash-update-component",
                                     data=json.dumps(payload).encode("utf-8"),
                                     headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return unpack_table(json.load(response), module)


def as_number(value):
    if value is None or value == "":
        return math.nan
    if isinstance(value, bool):
        raise ValueError("布尔值不是统计数字")
    return float(value)


def close(expected, actual, rtol, atol):
    expected, actual = as_number(expected), as_number(actual)
    if math.isnan(expected) or math.isnan(actual):
        return math.isnan(expected) and math.isnan(actual)
    return math.isclose(expected, actual, rel_tol=rtol, abs_tol=atol)


def interval_values(value):
    if value is None or value == "":
        return (math.nan, math.nan)
    match = INTERVAL.fullmatch(str(value))
    if not match:
        raise ValueError("置信区间应为 '下限 - 上限'，支持负数和科学计数法")
    return tuple(map(float, match.groups()))


def compare(expected, columns, actual, key, allow_partial, rtol, atol):
    validate_columns(columns)
    required = [key, "n"] + METRICS
    missing = [name for name in required if name not in columns]
    unknown = [name for name in columns if name not in required]
    if unknown or key not in columns or "n" not in columns:
        raise ValueError("界面列不匹配：缺少标识列/n 或存在未知列 {}".format(unknown))
    if missing and not allow_partial:
        raise ValueError("未覆盖所有指标 {}；请在面板勾选全部指标再导出，或用 --allow-partial。".format(missing))
    metrics = [name for name in METRICS if name in columns]
    if not metrics:
        raise ValueError("界面表格没有任何统计指标，不能宣称通过。")
    differences, count, checked = [], 0, 0

    def mismatch(row, column, wanted, observed, reason="value mismatch"):
        nonlocal count
        count += 1
        if len(differences) < 100:
            differences.append({"row": row, "column": column, "expected": wanted,
                                "actual": observed, "reason": reason})

    if len(expected) != len(actual):
        mismatch(None, "row_count", len(expected), len(actual))
    for index, (wanted, observed) in enumerate(zip(expected, actual), 1):
        # Keep row order and duplicate identifiers; never silently overwrite a group.
        for name in [key, "n"] + metrics:
            checked += 1
            target, value = wanted[name], observed.get(name)
            try:
                if name not in observed:
                    equal = False
                elif name == key:
                    if isinstance(target, (int, float, np.number)) and not isinstance(target, bool):
                        equal = close(target, value, 0, 0)
                    else:
                        equal = str(target) == str(value)
                elif name == "n":
                    equal = close(target, value, 0, 0)
                elif name.startswith("95CI"):
                    equal = all(close(a, b, rtol, atol)
                                for a, b in zip(interval_values(target), interval_values(value)))
                else:
                    equal = close(target, value, rtol, atol)
                if not equal:
                    mismatch(index, name, target, value)
            except (TypeError, ValueError, OverflowError) as error:
                mismatch(index, name, target, value, str(error))
    return {"passed": count == 0, "coverage": "partial" if missing else "all",
            "metrics_checked": metrics, "metrics_missing": missing, "cells_checked": checked,
            "difference_count": count, "differences": differences,
            "differences_truncated": count > len(differences)}


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return str(value)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module", required=True, choices=COMPONENTS)
    parser.add_argument("--input", required=True, type=Path, help="Data upload 导出的原始 CSV")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--observed", type=Path, help="汇总面板导出 CSV，或界面回调 JSON")
    source.add_argument("--base-url", help="直接调用平台 Dash 汇总回调，例如 http://127.0.0.1:8050")
    parser.add_argument("--digits", type=int, default=2, help="与界面 Digits 一致；默认 2")
    for name in ("x", "y", "ids", "idc"):
        parser.add_argument("--tidy-" + name, help="tidy 数据对应的列名")
    parser.add_argument("--allow-partial", action="store_true", help="仅核对导出中实际显示的指标")
    parser.add_argument("--rtol", type=float, default=1e-9)
    parser.add_argument("--atol", type=float, default=1e-10)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--report", type=Path, help="JSON 报告路径；默认 tests/results/statistics_<module>.json")
    args = parser.parse_args()
    report_path = args.report or Path(__file__).parent / "results" / ("statistics_" + args.module.lower() + ".json")
    protected = [args.input] + ([args.observed] if args.observed else [])
    if any(report_path.resolve() == path.resolve() for path in protected):
        parser.error("报告路径不能覆盖输入或界面导出文件。")
    report = {"module": args.module, "input": str(args.input), "digits": args.digits,
              "observed_source": str(args.observed) if args.observed else args.base_url,
              "versions": {"pandas": pd.__version__, "numpy": np.__version__,
                           "scipy": __import__("scipy").__version__}}
    try:
        if not 0 <= args.digits <= 15:
            raise ValueError("--digits 必须在 0..15 之间。")
        if any(not math.isfinite(v) or v < 0 for v in (args.atol, args.rtol)):
            raise ValueError("容差必须是有限的非负数。")
        if not math.isfinite(args.timeout) or args.timeout <= 0:
            raise ValueError("--timeout 必须为有限正数。")
        tidy = {name: getattr(args, "tidy_" + name) for name in ("x", "y", "ids", "idc")}
        if any(tidy.values()) and not all(tidy.values()):
            raise ValueError("tidy 数据必须同时提供 --tidy-x/y/ids/idc。")
        tidy = tidy if all(tidy.values()) else None
        report.update({"tidy": tidy, "rtol": args.rtol, "atol": args.atol})
        text = args.input.read_text(encoding="utf-8-sig")
        matrix, key = prepare_matrix(text, args.module, tidy)
        raw = independent_rows(matrix, key)
        expected = displayed_rows(raw, key, args.digits)
        columns, actual = (load_observed(args.observed, args.module) if args.observed else
                           fetch_panel(args.base_url, args.module, text, tidy, args.digits, args.timeout))
        report.update(compare(expected, columns, actual, key, args.allow_partial, args.rtol, args.atol))
        report.update({"reference_unrounded": raw, "reference_displayed": expected,
                       "observed_columns": columns, "observed_rows": actual})
        exit_code = 0 if report["passed"] else 1
        print("{} {}: {} rows, {} cells, {} differences; coverage={}".format(
            "PASS" if report["passed"] else "FAIL", args.module, len(expected),
            report["cells_checked"], report["difference_count"], report["coverage"]))
        for difference in report["differences"][:10]:
            print("  row {row}, {column}: expected={expected!r}, actual={actual!r}".format(**difference))
    except (ValueError, TypeError, KeyError, OSError, urllib.error.URLError) as error:
        report.update({"passed": False, "error": str(error)})
        print("ERROR: " + str(error), file=sys.stderr)
        exit_code = 2
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(json_safe(report), ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    print("Report: " + str(report_path))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
