import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Empty,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { RefreshCw } from "lucide-react";

import {
  fetchPerformanceReport,
  type AnalyticsBreakdown,
  type ComponentBreakdown,
  type EquityPoint,
} from "./api";

function formatR(value: number | null): string {
  return value === null ? "-" : `${value.toFixed(3)}R`;
}

function formatPercent(value: number | null): string {
  return value === null ? "-" : `${(value * 100).toFixed(1)}%`;
}

const breakdownColumns: ColumnsType<AnalyticsBreakdown> = [
  {
    title: "Csoport",
    dataIndex: "label",
    key: "label",
    render: (label: string) => <Typography.Text strong>{label}</Typography.Text>,
  },
  {
    title: "Trade",
    dataIndex: ["statistics", "closedTrades"],
    key: "trades",
    width: 78,
  },
  {
    title: "Win rate",
    key: "winRate",
    width: 108,
    render: (_, group) => formatPercent(group.statistics.netWinRate),
  },
  {
    title: "Expectancy",
    key: "expectancy",
    width: 112,
    render: (_, group) => formatR(group.statistics.netExpectancyR),
  },
  {
    title: "Net R",
    key: "netR",
    width: 100,
    render: (_, group) => formatR(group.statistics.totalNetR),
  },
  {
    title: "Profit factor",
    key: "profitFactor",
    width: 116,
    render: (_, group) => group.statistics.netProfitFactor?.toFixed(3) ?? "-",
  },
];

function componentGroups(groups: ComponentBreakdown[]): AnalyticsBreakdown[] {
  return groups.map((group) => ({
    key: `${group.component}:${group.state}`,
    label: `${group.component} / ${group.state}`,
    statistics: group.statistics,
  }));
}

function BreakdownTable({ groups }: { groups: AnalyticsBreakdown[] }) {
  return (
    <Table<AnalyticsBreakdown>
      rowKey="key"
      size="small"
      columns={breakdownColumns}
      dataSource={groups}
      pagination={false}
      scroll={{ x: 650 }}
      locale={{
        emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nincs bontási adat." />,
      }}
    />
  );
}

function EquityCurve({ points }: { points: EquityPoint[] }) {
  if (points.length === 0) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nincs lezárt trade." />;
  }

  const width = 800;
  const height = 250;
  const padding = { top: 18, right: 18, bottom: 34, left: 52 };
  const values = [0, ...points.map((point) => point.cumulativeNetR)];
  const rawMin = Math.min(...values);
  const rawMax = Math.max(...values);
  const rawRange = rawMax - rawMin;
  const rangePadding = rawRange === 0 ? 1 : rawRange * 0.12;
  const min = rawMin - rangePadding;
  const max = rawMax + rangePadding;
  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;
  const x = (index: number) => padding.left + (index / (values.length - 1)) * plotWidth;
  const y = (value: number) => padding.top + ((max - value) / (max - min)) * plotHeight;
  const polyline = values.map((value, index) => `${x(index)},${y(value)}`).join(" ");
  const gridValues = Array.from({ length: 5 }, (_, index) => min + ((max - min) * index) / 4);

  return (
    <div className="equity-chart">
      <svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Kumulált nettó R equity görbe">
        {gridValues.map((value) => (
          <g key={value}>
            <line
              x1={padding.left}
              x2={width - padding.right}
              y1={y(value)}
              y2={y(value)}
              className="equity-grid-line"
            />
            <text x={padding.left - 8} y={y(value) + 4} textAnchor="end">
              {`${value.toFixed(1)}R`}
            </text>
          </g>
        ))}
        <line
          x1={padding.left}
          x2={width - padding.right}
          y1={y(0)}
          y2={y(0)}
          className="equity-zero-line"
        />
        <polyline points={polyline} className="equity-line" />
        {values.map((value, index) => (
          <circle key={index} cx={x(index)} cy={y(value)} r={index === values.length - 1 ? 5 : 3}>
            <title>
              {index === 0
                ? "Kezdőpont: 0R"
                : `#${index} ${points[index - 1].eventId}: ${value.toFixed(3)}R`}
            </title>
          </circle>
        ))}
        <text x={padding.left} y={height - 8}>0</text>
        <text x={width - padding.right} y={height - 8} textAnchor="end">
          {`#${points.length}`}
        </text>
      </svg>
    </div>
  );
}

export function AnalyticsReportPanel({ runId }: { runId: string }) {
  const reportQuery = useQuery({
    queryKey: ["analytics", runId],
    queryFn: () => fetchPerformanceReport(runId),
    retry: 1,
  });
  const report = reportQuery.data;

  return (
    <div className="analytics-workspace">
      <div className="analytics-heading">
        <div>
          <Typography.Text type="secondary">Run analytics</Typography.Text>
          <Typography.Title level={3}>Teljesítményelemzés</Typography.Title>
        </div>
        <Tooltip title="Elemzés frissítése">
          <Button
            icon={<RefreshCw size={16} />}
            aria-label="Elemzés frissítése"
            onClick={() => void reportQuery.refetch()}
          />
        </Tooltip>
      </div>

      {reportQuery.isLoading ? <Spin aria-label="Elemzés betöltése" /> : null}
      {reportQuery.isError ? (
        <Alert
          type="error"
          showIcon
          message="Az elemzés nem tölthető be."
          action={<Button onClick={() => void reportQuery.refetch()}>Elemzés újrapróbálása</Button>}
        />
      ) : null}

      {report ? (
        <>
          <div className="analytics-metrics-grid">
            <Statistic title="Átlagos nyerő" value={formatR(report.risk.averageWinR)} />
            <Statistic title="Átlagos vesztes" value={formatR(report.risk.averageLossR)} />
            <Statistic title="Maximum drawdown" value={formatR(report.risk.maximumDrawdownR)} />
            <Statistic title="Leghosszabb nyerő sorozat" value={report.risk.longestWinningStreak} />
            <Statistic title="Leghosszabb vesztes sorozat" value={report.risk.longestLosingStreak} />
            <Statistic title="Javaslatkövetés" value={formatPercent(report.decisions.agreementRate)} />
          </div>

          <div className="analytics-block">
            <Typography.Title level={4}>Equity curve</Typography.Title>
            <EquityCurve points={report.equityCurve} />
          </div>

          <div className="analytics-block decision-summary">
            <div>
              <Typography.Title level={4}>Döntési összevetés</Typography.Title>
              <Typography.Text type="secondary">
                {`Pontozás: ${report.scoringConfigVersion}`}
              </Typography.Text>
            </div>
            {report.decisions.journaledSetups > 0 ? (
              <Space wrap>
                <Tag color="green">{`Megkötve: ${report.decisions.taken} · ${formatR(report.decisions.takenStatistics.totalNetR)}`}</Tag>
                <Tag color="orange">{`Kihagyva: ${report.decisions.skipped} · ${formatR(report.decisions.skippedStatistics.totalNetR)}`}</Tag>
                <Tag>{`Követett: ${report.decisions.followedRecommendation}`}</Tag>
                <Tag>{`Felülbírált: ${report.decisions.overrodeRecommendation}`}</Tag>
              </Space>
            ) : (
              <Typography.Text type="secondary">
                Ehhez a futáshoz még nincs journal döntés.
              </Typography.Text>
            )}
          </div>

          <div className="analytics-block">
            <Typography.Title level={4}>Bontások</Typography.Title>
            <Tabs
              items={[
                { key: "session", label: "Session", children: <BreakdownTable groups={report.bySession} /> },
                { key: "score", label: "Score", children: <BreakdownTable groups={report.byScoreBucket} /> },
                { key: "direction", label: "Direction", children: <BreakdownTable groups={report.byDirection} /> },
                { key: "component", label: "Komponens", children: <BreakdownTable groups={componentGroups(report.bySetupComponent)} /> },
                { key: "instrument", label: "Instrumentum", children: <BreakdownTable groups={report.byInstrument} /> },
                { key: "strategy", label: "Stratégia", children: <BreakdownTable groups={report.byStrategyVersion} /> },
              ]}
            />
          </div>
        </>
      ) : null}
    </div>
  );
}
