#!/usr/bin/env python3
"""Compare conversion cells independently (Python 3.8+).

Default mode extracts only eight core functions via AST; it does not test the UI.
External mode reads <input-stem>_convert.{csv,xls,xlsx,json} without converting.
Optional packages: openpyxl for XLSX; xlrd to read XLS; xlwt to export XLS.
"""
import argparse
import ast
import csv
import importlib
import json
import math
from pathlib import Path
import sys
import tempfile

FORMATS = ("csv", "xls", "xlsx", "json")
ROOT = Path(__file__).resolve().parents[1]
MISSING = object()


def read_table(path):
    """Independent readers: never call the platform's import functions here."""
    ext = path.suffix.lower()[1:]
    if ext == "csv":
        with path.open(encoding="utf-8-sig", newline="") as stream:
            data = list(csv.reader(stream))
    elif ext == "json":
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream)
    elif ext == "xls":
        xlrd = importlib.import_module("xlrd")
        book = xlrd.open_workbook(str(path))
        try:
            sheet = book.sheet_by_index(0)
            data = [sheet.row_values(i) for i in range(sheet.nrows)]
        finally:
            book.release_resources()
    elif ext == "xlsx":
        openpyxl = importlib.import_module("openpyxl")
        book = openpyxl.load_workbook(str(path), data_only=False)
        try:
            data = [list(row) for row in book.active.iter_rows(values_only=True)]
        finally:
            book.close()
    else:
        raise ValueError("Unsupported input extension: " + path.suffix)
    if not isinstance(data, list) or any(not isinstance(row, list) for row in data):
        raise ValueError("Expected a JSON two-dimensional array / table")
    if any(not isinstance(v, (str, int, float, bool, type(None)))
           for row in data for v in row):
        raise ValueError("Cells must be scalar text, numbers, booleans or null")
    return data


def load_core():
    """Compile definitions from production, without executing its module imports."""
    source = ROOT / "pages/DataFormatConvert/DataFormatConvert.py"
    tree = ast.parse(source.read_text(encoding="utf-8"), filename=str(source))
    names = {"convert_" + direction + "_" + fmt
             for direction in ("import", "export") for fmt in FORMATS}
    nodes = [node for node in tree.body
             if isinstance(node, ast.FunctionDef) and node.name in names]
    if len(nodes) != 8 or {node.name for node in nodes} != names:
        raise ValueError("Production source must contain exactly eight core functions")
    if any(node.decorator_list for node in nodes):
        raise ValueError("Unexpected decorators on production core functions")
    namespace = {"csv": csv, "json": json}
    module = ast.Module(body=nodes, type_ignores=[])
    exec(compile(module, str(source), "exec"), namespace)
    return namespace


def prepare_dependencies(namespace, source_format, target_format):
    required = set()
    if source_format == "xls":
        required.add("xlrd")
    if target_format == "xls":
        required.add("xlwt")
    if "xlsx" in (source_format, target_format):
        required.add("openpyxl")
    for name in sorted(required):
        namespace[name] = importlib.import_module(name)


def shape(table):
    return {"rows": len(table), "columns": max(map(len, table), default=0),
            "row_lengths": [len(row) for row in table]}


def describe(value):
    if value is MISSING:
        return {"type": "missing"}
    if isinstance(value, float) and not math.isfinite(value):
        return {"type": "float", "value": repr(value)}
    return {"type": type(value).__name__, "value": value}


def expected_cell(value, fmt):
    # CSV has no numeric type: compare the exact textual spelling of each number.
    # Null stays null so a CSV empty field cannot silently pass for null.
    if fmt == "csv" and value is not MISSING and value is not None:
        if not (isinstance(value, float) and not math.isfinite(value)):
            return str(value)
    return value


def equal(left, right):
    if left is MISSING or right is MISSING:
        return left is right
    numeric = (int, float)
    if (isinstance(left, numeric) and not isinstance(left, bool)
            and isinstance(right, numeric) and not isinstance(right, bool)):
        return left == right  # Exact numeric equality; NaN remains unequal.
    return type(left) is type(right) and left == right


def compare(original, actual, fmt, limit):
    differences = []
    count = 0
    for r in range(max(len(original), len(actual))):
        before = original[r] if r < len(original) else []
        after = actual[r] if r < len(actual) else []
        for c in range(max(len(before), len(after))):
            raw = before[c] if c < len(before) else MISSING
            expected = expected_cell(raw, fmt)
            received = after[c] if c < len(after) else MISSING
            if not equal(expected, received):
                count += 1
                if len(differences) < limit:
                    differences.append({"row": r + 1, "column": c + 1,
                                        "original": describe(raw),
                                        "expected": describe(expected),
                                        "actual": describe(received)})
    same_shape = shape(original) == shape(actual)
    return {"status": "pass" if same_shape and count == 0 else "fail",
            "expected_shape": shape(original), "actual_shape": shape(actual),
            "shape_equal": same_shape, "difference_count": count,
            "differences": differences, "differences_truncated": count > limit}


def add_edge_cases(table):
    width = max(6, max(map(len, table), default=0))
    rows = [list(row) for row in table]
    edge = [None, "", " ", "NA", "N/A", "尾部空格  "]
    rows.append(edge + [""] * (width - len(edge)))
    rows.extend([[""] * width, [None] * width, []])
    return rows


def nonnegative(text):
    number = int(text)
    if number < 0:
        raise argparse.ArgumentTypeError("must be nonnegative")
    return number


def arguments():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=ROOT / "tests/fixtures/conversion_input.json")
    parser.add_argument("--output-dir", type=Path,
                        help="Save converted files and report.json (default: temporary directory)")
    parser.add_argument("--converted-dir", type=Path,
                        help="Read existing <input-stem>_convert.ext files; do not convert")
    parser.add_argument("--edge-cases", action="store_true",
                        help="Append null/whitespace/NA/trailing empty rows in local mode")
    parser.add_argument("--diff-limit", type=nonnegative, default=100,
                        help="Maximum saved cell differences per format; count always includes all")
    args = parser.parse_args()
    if args.edge_cases and args.converted_dir:
        parser.error("--edge-cases changes input; use its generated edge_input.json on the platform, "
                     "then --input edge_input.json --converted-dir DIR")
    return args


def run(args):
    output_dir = (args.output_dir or Path(tempfile.mkdtemp(prefix="conversion-validation-")))
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    source = args.input.resolve()
    mode = "external_files" if args.converted_dir else "production_core_ast"
    print("Mode: " + mode + " (core functions/files only; UI is not tested)")
    report = {"mode": mode, "input": str(source), "formats": {},
              "comparison": "1-based positions; CSV literal text; exact numeric equality; "
                            "no null/empty/NA normalization", "exit_code": 2}
    try:
        original = read_table(source)
        if args.edge_cases:
            original = add_edge_cases(original)
            source = output_dir / "edge_input.json"
            if source.resolve() == args.input.resolve():
                raise ValueError("Edge output would overwrite input; choose another output directory")
            source.write_text(json.dumps(original, ensure_ascii=False, indent=2), encoding="utf-8")
            report["effective_input"] = str(source)
        report["input_shape"] = shape(original)
        core = None if args.converted_dir else load_core()
        for fmt in FORMATS:
            directory = args.converted_dir.resolve() if args.converted_dir else output_dir
            target = directory / (source.stem + "_convert." + fmt)
            try:
                if target.resolve() == source:
                    raise ValueError("Conversion output would overwrite input")
                if core is not None:
                    prepare_dependencies(core, source.suffix.lower()[1:], fmt)
                    imported = core["convert_import_" + source.suffix.lower()[1:]](str(source))
                    core["convert_export_" + fmt](str(target), imported)
                result = compare(original, read_table(target), fmt, args.diff_limit)
            except Exception as exc:
                result = {"status": "error", "error": type(exc).__name__ + ": " + str(exc),
                          "expected_shape": shape(original), "actual_shape": None,
                          "difference_count": None, "differences": []}
            result["path"] = str(target)
            report["formats"][fmt] = result
            detail = result.get("error", "{} cell differences; shape_equal={}".format(
                result["difference_count"], result.get("shape_equal")))
            print("{}: {} — {}".format(fmt, result["status"].upper(), detail))
            for diff in result["differences"][:3]:
                print("  r{row} c{column}: {expected} -> {actual}".format(**diff))
        statuses = [item["status"] for item in report["formats"].values()]
        report["exit_code"] = 2 if "error" in statuses else (1 if "fail" in statuses else 0)
    except Exception as exc:
        report["error"] = type(exc).__name__ + ": " + str(exc)
        print("Input/execution ERROR: " + report["error"], file=sys.stderr)
    report_path = output_dir / "report.json"
    if report_path.resolve() == args.input.resolve():
        raise ValueError("Report would overwrite input; choose another output directory")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False),
                           encoding="utf-8")
    print("Report: " + str(report_path))
    return report["exit_code"]


def main():
    args = arguments()
    try:
        return run(args)
    except Exception as exc:
        print("Execution ERROR: {}: {}".format(type(exc).__name__, exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
