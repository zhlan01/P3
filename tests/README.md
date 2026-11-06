# Platform Data Validation

This directory contains two standalone scripts that do not modify the application code. All path arguments are relative to the current working directory.

- `validate_conversion.py`: Calls the existing conversion core functions or reads outputs already downloaded from the platform. It compares CSV, XLS, XLSX, and JSON cell by cell in row and column order.
- `validate_statistics.py`: Uses pandas, NumPy, and SciPy to independently recompute PSPV / PTDV summary metrics. It compares the results with a CSV exported from the panel, a saved callback JSON response, or a live Dash summary callback result. The independent calculations do not import the platform's statistics functions.

## Installation

Create an isolated environment in the project root so the platform runtime environment is not changed:

```bash
cd /Users/zyl/code/DataProcessing_20250723
python3 -m venv tests/.venv
source tests/.venv/bin/activate
python -m pip install -r tests/requirements.txt
```

The scripts use Python 3.8+ syntax. pip selects dependencies according to the Python version. The independent statistics calculations are compatible with newer pandas versions and do not rely on the removed `DataFrame.mad()`. The platform itself still uses older APIs; the scripts do not fix compatibility errors in the platform.

## 1. Format Conversion Validation

Run the included test that converts the same data table into all four output formats:

```bash
python tests/validate_conversion.py --output-dir tests/results/conversion
```

Test a custom table:

```bash
python tests/validate_conversion.py --input /path/to/original.xlsx \
  --output-dir tests/results/my_conversion
```

The default input is `fixtures/conversion_input.json`. It contains Chinese text, decimals, negative numbers, empty strings, numeric text, long-integer text, `NA`, quoted commas, and embedded newlines. Input supports `.csv/.xls/.xlsx/.json`; JSON must be a two-dimensional array. Header cells are also compared.

Local mode parses and executes the eight existing import/export functions from `pages/DataFormatConvert/DataFormatConvert.py`. It does not copy the conversion implementation, import the entire Dash application, or start a server. It validates the conversion core; it does not prove that the upload, routing, or download UI has been tested.

To validate files actually downloaded from the platform, upload the original table on the format conversion page and export all four formats into the same directory:

```text
/path/to/downloads/
  original_convert.csv
  original_convert.xls
  original_convert.xlsx
  original_convert.json
```

```bash
python tests/validate_conversion.py --input /path/to/original.xlsx \
  --converted-dir /path/to/downloads --output-dir tests/results/downloaded_conversion
```

File names must be `<input basename without extension>_convert.<format>`. This mode does not convert again; all four outputs must be present.

Comparison rules:

- No numeric tolerance is used; numeric values must be exactly equal. An Excel-read `2.0` and an input numeric value of `2` are treated as the same number.
- CSV has no cell types, so original numeric values are converted to text with `str()` and compared character by character. Original text such as `00123` is preserved and is not converted to a number.
- `None`, empty strings, `NA`, numbers, and numeric text are strictly distinguished. Nulls are not unified and values are not forced to numeric just to make the result pass.
- Row and column order are preserved, and the shape is compared. Fonts, styles, multiple worksheets, and formula results are not validated. XLS reads the first sheet; XLSX reads the active sheet.

**Conversion does not perform numeric calculations, and it is not guaranteed to be lossless across formats.** Excel may read an empty string back as an empty cell, CSV cannot represent typed nulls, and floating-point numbers and large integers are limited by the representation capabilities of each format. The default sample contains an empty string, so XLSX currently reports `"" → None` as a real difference. This is a detected difference and should not be hidden by widening the tolerance. Production XLSX import also changes the text `NA` to `None`; an original XLSX input can detect this as well.

Therefore, the **expected result for the default sample is CSV/XLS/JSON pass, XLSX fail, and the script exits with code 1**. This is not a script error; it is a known loss in format conversion. Adding `--edge-cases` detects more null, blank, and trailing-empty-row differences. If the goal is "all four formats must be completely identical," the current implementation cannot pass these cases; use this as a test gate rather than loosening the comparison rules.

Append edge cases:

```bash
python tests/validate_conversion.py --edge-cases --diff-limit 20 \
  --output-dir tests/results/conversion_edges
```

This mode also generates `edge_input.json`, which contains nulls, blanks, and trailing blank rows; it is expected to reveal more format loss. `report.json` stores the shape, total number of differences, and the first N differences for each format, with positions starting at 1. The default output directory is a temporary directory; specifying `--output-dir` explicitly is recommended.

## 2. Statistics Validation

### Preparing Real UI Data

1. On the PSPV or PTDV Data upload page, export the uploaded data table and save it as `input.csv`.
2. Go to Data Summary in the same module, select all metrics, and record the Digits and tidy settings. Change a selection or the number of digits once to ensure the table has been recalculated with the currently uploaded data.
3. Export the summary table and save it as `summary.csv`. Both pages may use `Data.csv` as the default download name, so rename the files separately.

```bash
python tests/validate_statistics.py --module PSPV \
  --input /path/to/input.csv --observed /path/to/summary.csv --digits 2 \
  --report tests/results/pspv_real.json

python tests/validate_statistics.py --module PTDV \
  --input /path/to/time_input.csv --observed /path/to/time_summary.csv --digits 2 \
  --report tests/results/ptdv_real.json
```

You can also request the Dash callback that produces the UI table directly from a locally running platform:

```bash
python tests/validate_statistics.py --module PSPV \
  --input /path/to/input.csv --base-url http://127.0.0.1:8050 --digits 8
```

Live mode sends the contents of the input CSV to the specified platform and requests all metrics. It obtains the table values returned by the summary callback; it does not read an existing browser session or validate browser rendering. The platform must be directly reachable and compatible with the Dash callback IDs in the current project. If there is a login layer, use a CSV exported from the browser or a saved `/_dash-update-component` JSON response instead. JSON supports the entire Dash response, `{columns,data}`, or a list of records; when `columns` is present, only the columns actually displayed are checked.

By default, all 10 metrics and `n` must be covered. To check only the currently selected columns, add `--allow-partial`; the report will be explicitly marked `coverage=partial` and cannot be considered a full validation pass.

### tidy Data

All four parameters must be provided together and must match the actual selections in the UI:

```bash
python tests/validate_statistics.py --module PTDV \
  --input Example/Data_tidy_example_time_multi.csv --observed /path/to/summary.csv \
  --tidy-x Time --tidy-y Value --tidy-ids Sample --tidy-idc id --digits 2
```

The PSPV example configuration is `--tidy-x Level --tidy-y Concentration --tidy-ids frame --tidy-idc conditions`.

Data preparation follows the current panel behavior:

- PSPV: wide data is summarized by numeric columns. For tidy data, pivot first by x and "condition × sample"; duplicate records for the same combination are averaged first, then each pivoted numeric column is summarized.
- PTDV: the first CSV column is used as the index, and data is summarized across all sample columns at each time point. After the tidy pivot, different conditions and samples at the same time point participate in the statistics together rather than being summarized separately by condition.
- Missing values are removed per statistical object; they are not filled with zero and no normalization is performed. If PTDV contains non-numeric sample columns or infinite values, an input error is reported directly rather than silently dropping them.

### Metrics and Tolerance

| Metric | Independent calculation definition |
| --- | --- |
| n | Number of non-missing observations; exact comparison |
| mean | Arithmetic mean |
| sd | Sample standard deviation, `ddof=1` |
| sem | `sd / sqrt(n)` |
| 95CI mean | `mean ± t(0.975,n−1) × sem` |
| median | Median |
| MAD | `mean(abs(x − mean))`, i.e. mean absolute deviation, **not median absolute deviation** |
| Q1 / Q3 | 25% / 75% quantiles, linear interpolation |
| IQR | Q3 − Q1 |
| 95CI median | Per the current platform implementation: `median ± t(0.975,n−1) × sem` |

`95CI median` validates the current formula used by the platform; this is not equivalent to proving that the interval is the standard method for a median confidence interval. When n is insufficient or the variance is zero, SciPy's NaN interval behavior is retained.

Independent results are first rounded to the UI Digits and then compared numerically, with default `rtol=1e-9` and `atol=1e-10`. Confidence intervals compare the two endpoints separately and support negative numbers and scientific notation. Group/time identifiers and n do not use floating-point tolerance. Values already rounded to two decimal places in the UI cannot be directly compared with unrounded values using a tiny floating-point tolerance; for actual audits, increasing Digits, for example to 8, is recommended.

The JSON report retains unrounded results, UI-precision results, observed data, coverage, dependency versions, the total number of differences, and the first 100 differences. Floating-point NaN/Infinity values are represented as text in the report to ensure it is standard JSON. Row order and duplicate identifiers are preserved; duplicate groups are not overwritten by dictionary keys.

### Included Baseline Samples

```bash
python tests/validate_statistics.py --module PSPV \
  --input tests/fixtures/pspv_input.csv --observed tests/fixtures/pspv_summary.csv
python tests/validate_statistics.py --module PTDV \
  --input tests/fixtures/ptdv_input.csv --observed tests/fixtures/ptdv_summary.csv
```

These CSV files are fixed baselines for the known sequence `[1,2,4,missing]` and cover all metrics. Passing them only means the scripts can match known results; **it does not mean the user's current UI has been validated**. For real data, use the exported files or live callback mode described above.

## Exit Codes

Both scripts use the following exit codes: `0` = all requested comparisons pass; `1` = data differences found; `2` = input, dependency, interface, or execution error. In conversion validation, execution errors take precedence over differences. `tests/results/` is ignored by version control and can be used to store reports and output files.
