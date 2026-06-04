import type { BarSeriesOption, LineSeriesOption, PieSeriesOption } from 'echarts/charts'
import type { ComposeOption } from 'echarts/core'
import type { GridComponentOption, LegendComponentOption, TooltipComponentOption } from 'echarts/components'

export type OpsChartOption = ComposeOption<
  | BarSeriesOption
  | LineSeriesOption
  | PieSeriesOption
  | GridComponentOption
  | LegendComponentOption
  | TooltipComponentOption
>
