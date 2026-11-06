# 平台数据验证

本目录有两个可单独执行的脚本，不修改业务代码。所有路径参数均相对于当前工作目录。

- `validate_conversion.py`：调用现有格式转换核心函数，或者读取平台已经下载的输出；对 CSV、XLS、XLSX、JSON 按行列逐单元格精确比较。
- `validate_statistics.py`：使用 pandas、NumPy、SciPy 独立重算 PSPV / PTDV 汇总指标；与面板导出 CSV、保存的回调 JSON，或者实时 Dash 汇总回调结果比较。独立计算不导入平台统计函数。

## 安装

在项目根目录创建独立环境，避免改变平台运行环境：

```bash
cd /Users/zyl/code/DataProcessing_20250723
python3 -m venv tests/.venv
source tests/.venv/bin/activate
python -m pip install -r tests/requirements.txt
```

脚本使用 Python 3.8+ 语法，依赖包由 pip 按 Python 版本选择。独立统计计算兼容新版 pandas，不依赖已经移除的 `DataFrame.mad()`。平台本身仍使用旧版 API，脚本不会替平台修正兼容性错误。

## 1. 格式转换验证

运行随附的同一张数据表到四种输出格式的测试：

```bash
python tests/validate_conversion.py --output-dir tests/results/conversion
```

测试自定义表格：

```bash
python tests/validate_conversion.py --input /path/to/original.xlsx \
  --output-dir tests/results/my_conversion
```

默认输入为 `fixtures/conversion_input.json`，包含中文、小数、负数、空字符串、数字文本、长整数文本、`NA`、逗号引号和单元格内换行。输入支持 `.csv/.xls/.xlsx/.json`，JSON 必须为二维数组；表头也属于待比较单元格。

本地模式从 `pages/DataFormatConvert/DataFormatConvert.py` 解析并执行八个现有 import/export 函数；不复制转换实现、不导入整个 Dash 应用，也不启动服务器。它验证转换核心，不能证明上传、路由或下载界面已通过测试。

验证平台实际下载文件时，在格式转换页面上传原始表，分别导出四种格式，将它们放到同一个目录：

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

文件名必须为 `<输入文件名去扩展名>_convert.<格式>`。该模式不重新转换，全部四种输出都必须存在。

比较规则：

- 不使用数值误差容限，数值必须精确相等；Excel 读取出的 `2.0` 与输入数值 `2` 视为同一数值。
- CSV 没有单元格类型，因此将原数值按 `str()` 转成文本后逐字比较；`00123` 这样的原始文本保留原样，不转成数字。
- `None`、空字符串、`NA`、数值与数字文本严格区分；不会为了让结果通过而统一空值或强制转数值。
- 保留行列顺序，比较形状；不验证字体、样式、多工作表或公式计算结果。XLS 读取首表，XLSX 读取活动表。

**转换不做数值运算，并不保证跨格式完全无损。**Excel 可能把空字符串读回为空单元格，CSV 不能表达类型化的 null，浮点数和大整数也受格式表示能力限制。默认样例包含空字符串，因此 XLSX 当前会如实报出 `"" → None`。这代表检出了差异，不应改大容差掩盖。生产 XLSX 导入还会把文字 `NA` 改成 `None`，用 XLSX 原始输入也可以检出。

因此，默认样例的**预期结果是 CSV/XLS/JSON 通过、XLSX 失败，脚本退出码为 1**；这不是脚本异常，而是格式转换的已知损失。加入 `--edge-cases` 后会检出更多 null/空白/尾空行差异。若目标是“四种格式都必须完全一致”，当前实现无法通过这些用例；应将它作为测试门禁，而不是放宽比较规则。

追加边界情况：

```bash
python tests/validate_conversion.py --edge-cases --diff-limit 20 \
  --output-dir tests/results/conversion_edges
```

此模式还生成 `edge_input.json`，包含 null、空白及尾空行；预期会揭示更多格式损失。`report.json` 保存各格式的形状、差异总数和前 N 个差异，位置从 1 开始。默认输出目录为临时目录；建议显式指定 `--output-dir`。

## 2. 统计量验证

### 准备真实界面数据

1. 在 PSPV 或 PTDV 的 Data upload 页面导出上传数据表，另存为 `input.csv`。
2. 进入同一模块的 Data Summary，勾选全部统计量，记录 Digits 和 tidy 配置；改变一次勾选或位数，确保表格已使用当前上传数据重新计算。
3. 导出汇总表，另存为 `summary.csv`。两个页面默认下载名都可能是 `Data.csv`，应分别重命名。

```bash
python tests/validate_statistics.py --module PSPV \
  --input /path/to/input.csv --observed /path/to/summary.csv --digits 2 \
  --report tests/results/pspv_real.json

python tests/validate_statistics.py --module PTDV \
  --input /path/to/time_input.csv --observed /path/to/time_summary.csv --digits 2 \
  --report tests/results/ptdv_real.json
```

也可以对本地已启动的平台直接请求产生界面表格的 Dash 回调：

```bash
python tests/validate_statistics.py --module PSPV \
  --input /path/to/input.csv --base-url http://127.0.0.1:8050 --digits 8
```

实时模式将输入 CSV 内容发送到指定平台，请求全部指标。它取得的是汇总回调返回的表格值，不读取现有浏览器 session，也不验证浏览器渲染。平台需要可直接访问且兼容当前项目的 Dash 回调 ID。若有登录层，可改用浏览器导出的 CSV 或保存的 `/_dash-update-component` JSON 响应。JSON 支持整个 Dash response、`{columns,data}` 或 records 列表；有 `columns` 时只核对实际显示列。

默认必须覆盖全部 10 项指标和 `n`。只核对当前勾选列时加入 `--allow-partial`，报告会明确标为 `coverage=partial`，不能视为全量验证通过。

### tidy 数据

四个参数必须一起提供，填写界面中的真实选择：

```bash
python tests/validate_statistics.py --module PTDV \
  --input Example/Data_tidy_example_time_multi.csv --observed /path/to/summary.csv \
  --tidy-x Time --tidy-y Value --tidy-ids Sample --tidy-idc id --digits 2
```

PSPV 示例配置为 `--tidy-x Level --tidy-y Concentration --tidy-ids frame --tidy-idc conditions`。

数据准备遵循当前面板行为：

- PSPV：wide 按数值列汇总。tidy 先按 x 和“条件 × 样本”透视，同一组合重复记录先求均值，再按透视后的每个数值列汇总。
- PTDV：CSV 首列作为索引，按每个时间点跨全部样本列汇总。tidy 透视后，同一时间点的不同条件和样本一起参与统计，不分别按条件汇总。
- 缺失值逐统计对象删除，不补零，不做归一化。PTDV 混入非数值样本列或出现无穷值时直接报告输入错误，不偷偷删除它们。

### 指标和容差

| 指标 | 独立计算定义 |
| --- | --- |
| n | 非缺失观测数，精确比较 |
| mean | 算术平均数 |
| sd | 样本标准差，`ddof=1` |
| sem | `sd / sqrt(n)` |
| 95CI mean | `mean ± t(0.975,n−1) × sem` |
| median | 中位数 |
| MAD | `mean(abs(x − mean))`，即平均绝对偏差，**不是中位数绝对偏差** |
| Q1 / Q3 | 25% / 75% 分位数，线性插值 |
| IQR | Q3 − Q1 |
| 95CI median | 按当前平台实现：`median ± t(0.975,n−1) × sem` |

`95CI median` 验证的是平台当前公式；这不等同于证明该区间是标准的中位数置信区间方法。n 不足、零方差时保留 SciPy 的 NaN 区间行为。

独立结果先按界面 Digits 舍入，再数值比较，默认 `rtol=1e-9`、`atol=1e-10`；置信区间分别比较两个端点，支持负数和科学计数法。分组/时间标识和 n 不使用浮点容差。界面已舍入到两位的小数不能直接与未舍入值按微小浮点容差比较；建议实际审计时将 Digits 提高，例如 8。

JSON 报告保留未舍入结果、界面精度结果、观测数据、覆盖情况、依赖版本、差异总数及前 100 项差异。浮点 NaN/Infinity 在报告中表示为文本，确保报告为标准 JSON。行序及重复标识保留，不会按字典键覆盖重复组。

### 随附基准样例

```bash
python tests/validate_statistics.py --module PSPV \
  --input tests/fixtures/pspv_input.csv --observed tests/fixtures/pspv_summary.csv
python tests/validate_statistics.py --module PTDV \
  --input tests/fixtures/ptdv_input.csv --observed tests/fixtures/ptdv_summary.csv
```

这些 CSV 是已知数列 `[1,2,4,缺失]` 的固定基准，覆盖全部指标。通过它们只说明脚本能匹配已知结果，**不表示用户当前界面已被验证**；真实数据应使用上面的导出文件或实时回调模式。

## 退出码

两个脚本均使用：`0` = 全部已请求比较通过；`1` = 发现数据差异；`2` = 输入、依赖、接口或执行错误。格式验证中执行错误优先于差异。`tests/results/` 已忽略版本控制，可保存报告和输出文件。
