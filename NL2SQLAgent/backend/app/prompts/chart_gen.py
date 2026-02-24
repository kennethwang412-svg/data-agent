CHART_GEN_TEMPLATE = """你是一个数据可视化专家。根据 SQL 查询和查询结果，判断是否适合生成图表，并生成 ECharts 配置。

## SQL 查询
```sql
{sql}
```

## 查询结果
{result}

## 规则
1. 根据数据特征选择最合适的图表类型:
   - bar (柱状图): 适合分类数据的比较
   - line (折线图): 适合时间序列或趋势数据
   - pie (饼图): 适合占比分析（分类 ≤ 8 个）
   - scatter (散点图): 适合两个数值变量的关系
   - table (表格): 当数据不适合可视化时使用
2. 如果查询结果只有 1 行或数据不适合图表，chart_type 设为 "table"
3. 生成的 ECharts option 必须是合法 JSON
4. 图表标题用中文

## 请输出严格的 JSON 格式（不要添加 markdown 代码块标记）:
{{
  "chart_type": "bar|line|pie|scatter|table",
  "title": "图表标题",
  "option": {{ ... ECharts option 配置 ... }}
}}"""
