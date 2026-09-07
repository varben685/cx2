import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Descriptions,
  Drawer,
  Empty,
  Input,
  InputNumber,
  Modal,
  Space,
  Statistic,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { Eye, Play, Plus, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";

import {
  ApiError,
  createBacktest,
  fetchBacktests,
  fetchOutcomes,
  type BacktestConfig,
  type BacktestRequest,
  type BacktestRun,
  type OutcomeRecord,
} from "./api";
import { createExampleBacktest } from "./backtestExample";

const { TextArea } = Input;

type BacktestDraft = {
  runId: string;
  setupsJson: string;
  candlesCsv: string;
  config: BacktestConfig;
};

function draftFromExample(): BacktestDraft {
  const example = createExampleBacktest();
  return {
    runId: example.runId,
    setupsJson: JSON.stringify(example.setups, null, 2),
    candlesCsv: example.candlesCsv,
    config: example.config,
  };
}

function formatR(value: number | null): string {
  return value === null ? "-" : `${value.toFixed(3)}R`;
}

function formatPercent(value: number | null): string {
  return value === null ? "-" : `${(value * 100).toFixed(1)}%`;
}

function resultColor(label: string): string {
  if (label === "WIN") return "green";
  if (label === "LOSS") return "red";
  if (label === "TIMEOUT") return "orange";
  if (label === "NOT_TRIGGERED") return "default";
  return "blue";
}

function createRunColumns(onSelect: (runId: string) => void): ColumnsType<BacktestRun> {
  return [
    {
      title: "Market",
      key: "market",
      render: (_, run) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{run.symbol}</Typography.Text>
          <Typography.Text type="secondary">{`${run.exchange} / ${run.timeframe}`}</Typography.Text>
        </Space>
      ),
    },
    {
      title: "Trades",
      dataIndex: ["statistics", "closedTrades"],
      key: "trades",
      width: 92,
    },
    {
      title: "Win rate",
      key: "winRate",
      width: 110,
      render: (_, run) => formatPercent(run.statistics.netWinRate),
    },
    {
      title: "Expectancy",
      key: "expectancy",
      width: 120,
      render: (_, run) => formatR(run.statistics.netExpectancyR),
    },
    {
      title: "Completed",
      dataIndex: "completedAt",
      key: "completedAt",
      render: (value: string) => new Date(value).toLocaleString(),
    },
    {
      title: "",
      key: "actions",
      width: 56,
      render: (_, run) => (
        <Tooltip title="Futás megnyitása">
          <Button
            icon={<Eye size={16} />}
            aria-label="Futás megnyitása"
            onClick={(event) => {
              event.stopPropagation();
              onSelect(run.runId);
            }}
          />
        </Tooltip>
      ),
    },
  ];
}

function createOutcomeColumns(
  onSelect: (outcomeId: string) => void,
): ColumnsType<OutcomeRecord> {
  return [
    {
      title: "Event",
      dataIndex: "eventId",
      key: "eventId",
      ellipsis: true,
      render: (value: string, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{record.symbol}</Typography.Text>
          <Typography.Text type="secondary" ellipsis>
            {value}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: "Direction",
      dataIndex: "direction",
      key: "direction",
      width: 104,
      render: (value: OutcomeRecord["direction"]) => (
        <Tag color={value === "LONG" ? "green" : "red"}>{value}</Tag>
      ),
    },
    {
      title: "Outcome",
      key: "outcome",
      width: 132,
      render: (_, record) => (
        <Tag color={resultColor(record.outcome.label)}>{record.outcome.label}</Tag>
      ),
    },
    {
      title: "Net R",
      key: "netR",
      width: 96,
      sorter: (a, b) => (a.outcome.netRealizedR ?? 0) - (b.outcome.netRealizedR ?? 0),
      render: (_, record) => formatR(record.outcome.netRealizedR),
    },
    {
      title: "MFE / MAE",
      key: "excursion",
      width: 148,
      render: (_, record) =>
        record.outcome.excursion
          ? `${formatR(record.outcome.excursion.mfeR)} / ${formatR(record.outcome.excursion.maeR)}`
          : "-",
    },
    {
      title: "Bars",
      key: "bars",
      width: 76,
      render: (_, record) => record.outcome.barsHeld ?? "-",
    },
    {
      title: "",
      key: "actions",
      width: 56,
      render: (_, record) => (
        <Tooltip title="Outcome részletek">
          <Button
            icon={<Eye size={16} />}
            aria-label="Outcome részletek"
            onClick={(event) => {
              event.stopPropagation();
              onSelect(record.outcomeId);
            }}
          />
        </Tooltip>
      ),
    },
  ];
}

export function BacktestsPanel() {
  const queryClient = useQueryClient();
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);
  const [selectedOutcomeId, setSelectedOutcomeId] = useState<string | null>(null);
  const [isCreateOpen, setCreateOpen] = useState(false);
  const [draft, setDraft] = useState<BacktestDraft>(draftFromExample);
  const [draftError, setDraftError] = useState<string | null>(null);

  const runsQuery = useQuery({
    queryKey: ["backtests"],
    queryFn: () => fetchBacktests(50),
    retry: 1,
  });
  const activeRunId = selectedRunId ?? runsQuery.data?.items[0]?.runId ?? null;
  const activeRun = runsQuery.data?.items.find((run) => run.runId === activeRunId) ?? null;
  const outcomesQuery = useQuery({
    queryKey: ["outcomes", activeRunId],
    queryFn: () => fetchOutcomes(activeRunId ?? ""),
    enabled: activeRunId !== null,
    retry: 1,
  });
  const selectedOutcome =
    outcomesQuery.data?.items.find((item) => item.outcomeId === selectedOutcomeId) ?? null;

  const createMutation = useMutation({
    mutationFn: createBacktest,
    onSuccess: async (run) => {
      setSelectedRunId(run.runId);
      setCreateOpen(false);
      setDraftError(null);
      await queryClient.invalidateQueries({ queryKey: ["backtests"] });
      await queryClient.invalidateQueries({ queryKey: ["outcomes", run.runId] });
    },
  });

  const runColumns = useMemo(() => createRunColumns(setSelectedRunId), []);
  const outcomeColumns = useMemo(() => createOutcomeColumns(setSelectedOutcomeId), []);

  function openCreateModal() {
    setDraft(draftFromExample());
    setDraftError(null);
    createMutation.reset();
    setCreateOpen(true);
  }

  function submitBacktest() {
    setDraftError(null);
    let parsed: unknown;
    try {
      parsed = JSON.parse(draft.setupsJson) as unknown;
    } catch {
      setDraftError("A setup JSON nem értelmezhető.");
      return;
    }
    const setups = Array.isArray(parsed) ? parsed : [parsed];
    const payload: BacktestRequest = {
      runId: draft.runId.trim(),
      setups,
      candlesCsv: draft.candlesCsv,
      config: draft.config,
    };
    createMutation.mutate(payload);
  }

  return (
    <section className="backtests-panel" aria-label="Backtest futások">
      <div className="setups-heading">
        <div>
          <Typography.Text type="secondary">Backtesting</Typography.Text>
          <Typography.Title level={2}>Backtest futások</Typography.Title>
        </div>
        <Space>
          <Tooltip title="Futások frissítése">
            <Button
              icon={<RefreshCw size={16} />}
              aria-label="Futások frissítése"
              onClick={() => void runsQuery.refetch()}
            />
          </Tooltip>
          <Button type="primary" icon={<Plus size={16} />} onClick={openCreateModal}>
            Új backtest
          </Button>
        </Space>
      </div>

      {runsQuery.isError ? (
        <Alert
          type="error"
          showIcon
          message="A backtest futások nem tölthetők be."
          action={<Button onClick={() => void runsQuery.refetch()}>Újrapróbálás</Button>}
        />
      ) : null}

      <Table<BacktestRun>
        rowKey="runId"
        size="small"
        loading={runsQuery.isLoading}
        columns={runColumns}
        dataSource={runsQuery.isError ? [] : (runsQuery.data?.items ?? [])}
        pagination={false}
        scroll={{ x: 760 }}
        rowClassName={(run) => (run.runId === activeRunId ? "selected-row" : "")}
        onRow={(run) => ({ onClick: () => setSelectedRunId(run.runId) })}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description={runsQuery.isError ? "A futások nem érhetők el." : "Még nincs backtest futás."}
            />
          ),
        }}
      />

      {activeRun ? (
        <>
          <div className="run-heading">
            <div>
              <Space size={8} wrap>
                <Typography.Title level={3}>{activeRun.symbol}</Typography.Title>
                <Tag color="green">{activeRun.status}</Tag>
                <Tag>{activeRun.timeframe}</Tag>
              </Space>
              <Typography.Text type="secondary" copyable>
                {activeRun.runId}
              </Typography.Text>
            </div>
            <Typography.Text type="secondary">
              {new Date(activeRun.completedAt).toLocaleString()}
            </Typography.Text>
          </div>
          <div className="metrics-grid">
            <Statistic title="Closed trades" value={activeRun.statistics.closedTrades} />
            <Statistic title="Win rate" value={formatPercent(activeRun.statistics.netWinRate)} />
            <Statistic title="Expectancy" value={formatR(activeRun.statistics.netExpectancyR)} />
            <Statistic title="Total net R" value={formatR(activeRun.statistics.totalNetR)} />
            <Statistic
              title="Profit factor"
              value={activeRun.statistics.netProfitFactor?.toFixed(3) ?? "-"}
            />
          </div>

          {outcomesQuery.isError ? (
            <Alert
              type="error"
              showIcon
              message="Az outcome eredmények nem tölthetők be."
              action={<Button onClick={() => void outcomesQuery.refetch()}>Újrapróbálás</Button>}
            />
          ) : null}
          <Table<OutcomeRecord>
            rowKey="outcomeId"
            size="small"
            loading={outcomesQuery.isLoading}
            columns={outcomeColumns}
            dataSource={outcomesQuery.isError ? [] : (outcomesQuery.data?.items ?? [])}
            pagination={false}
            scroll={{ x: 860 }}
            onRow={(record) => ({ onClick: () => setSelectedOutcomeId(record.outcomeId) })}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nincs outcome." /> }}
          />
        </>
      ) : null}

      <BacktestModal
        open={isCreateOpen}
        draft={draft}
        setDraft={setDraft}
        error={
          draftError ??
          (createMutation.error instanceof ApiError
            ? createMutation.error.message
            : createMutation.isError
              ? "A backtest futtatása sikertelen."
              : null)
        }
        submitting={createMutation.isPending}
        onCancel={() => setCreateOpen(false)}
        onSubmit={submitBacktest}
      />

      <Drawer
        width={560}
        open={selectedOutcomeId !== null}
        onClose={() => setSelectedOutcomeId(null)}
        title="Outcome részletek"
      >
        {selectedOutcome ? <OutcomeDetails record={selectedOutcome} /> : <Empty description="Nincs adat." />}
      </Drawer>
    </section>
  );
}

type BacktestModalProps = {
  open: boolean;
  draft: BacktestDraft;
  setDraft: (draft: BacktestDraft) => void;
  error: string | null;
  submitting: boolean;
  onCancel: () => void;
  onSubmit: () => void;
};

function BacktestModal({
  open,
  draft,
  setDraft,
  error,
  submitting,
  onCancel,
  onSubmit,
}: BacktestModalProps) {
  function updateConfig(key: keyof BacktestConfig, value: number | null) {
    if (value !== null) {
      setDraft({ ...draft, config: { ...draft.config, [key]: value } });
    }
  }

  return (
    <Modal
      width={880}
      open={open}
      title="Új backtest"
      onCancel={onCancel}
      footer={[
        <Button key="cancel" onClick={onCancel}>Mégse</Button>,
        <Button key="submit" type="primary" icon={<Play size={16} />} loading={submitting} onClick={onSubmit}>
          Futtatás
        </Button>,
      ]}
    >
      <div className="backtest-form">
        {error ? <Alert type="error" showIcon message={error} /> : null}
        <label className="field-label">
          <Typography.Text strong>Run ID</Typography.Text>
          <Space.Compact>
            <Input
              value={draft.runId}
              onChange={(event) => setDraft({ ...draft, runId: event.target.value })}
            />
            <Tooltip title="Új azonosító">
              <Button
                icon={<RefreshCw size={14} />}
                aria-label="Új futásazonosító"
                onClick={() => setDraft({ ...draft, runId: crypto.randomUUID() })}
              />
            </Tooltip>
          </Space.Compact>
        </label>
        <div className="config-grid">
          <NumericField label="Max holding bars" min={1} value={draft.config.maxHoldingBars} onChange={(v) => updateConfig("maxHoldingBars", v)} />
          <NumericField label="Entry timeout bars" min={1} value={draft.config.entryTimeoutBars} onChange={(v) => updateConfig("entryTimeoutBars", v)} />
          <NumericField label="Commission bps / side" value={draft.config.commissionBpsPerSide} onChange={(v) => updateConfig("commissionBpsPerSide", v)} />
          <NumericField label="Slippage bps / side" value={draft.config.slippageBpsPerSide} onChange={(v) => updateConfig("slippageBpsPerSide", v)} />
        </div>
        <label className="field-label">
          <Typography.Text strong>Setup JSON</Typography.Text>
          <TextArea
            rows={12}
            value={draft.setupsJson}
            onChange={(event) => setDraft({ ...draft, setupsJson: event.target.value })}
            spellCheck={false}
            aria-label="Setup JSON"
          />
        </label>
        <label className="field-label">
          <Typography.Text strong>OHLCV CSV</Typography.Text>
          <TextArea
            rows={7}
            value={draft.candlesCsv}
            onChange={(event) => setDraft({ ...draft, candlesCsv: event.target.value })}
            spellCheck={false}
            aria-label="OHLCV CSV"
          />
        </label>
      </div>
    </Modal>
  );
}

function NumericField({
  label,
  min = 0,
  value,
  onChange,
}: {
  label: string;
  min?: number;
  value: number;
  onChange: (value: number | null) => void;
}) {
  return (
    <label className="field-label">
      <Typography.Text strong>{label}</Typography.Text>
      <InputNumber min={min} value={value} onChange={onChange} controls className="numeric-input" />
    </label>
  );
}

function OutcomeDetails({ record }: { record: OutcomeRecord }) {
  const { outcome } = record;
  return (
    <div className="outcome-detail">
      <div className="setup-detail-title">
        <div>
          <Typography.Title level={3}>{record.symbol}</Typography.Title>
          <Typography.Text type="secondary">{record.eventId}</Typography.Text>
        </div>
        <Space>
          <Tag color={record.direction === "LONG" ? "green" : "red"}>{record.direction}</Tag>
          <Tag color={resultColor(outcome.label)}>{outcome.label}</Tag>
        </Space>
      </div>
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="Entry">{record.entryPrice}</Descriptions.Item>
        <Descriptions.Item label="Stop loss">{record.stopLoss}</Descriptions.Item>
        <Descriptions.Item label="Take profit">{record.takeProfit}</Descriptions.Item>
        <Descriptions.Item label="Exit reason">{outcome.exitReason}</Descriptions.Item>
        <Descriptions.Item label="Exit price">{outcome.exitPrice ?? "-"}</Descriptions.Item>
        <Descriptions.Item label="Gross / net R">
          {`${formatR(outcome.realizedR)} / ${formatR(outcome.netRealizedR)}`}
        </Descriptions.Item>
        <Descriptions.Item label="Entry / held bars">
          {`${outcome.barsToEntry ?? "-"} / ${outcome.barsHeld ?? "-"}`}
        </Descriptions.Item>
        <Descriptions.Item label="Entry time">
          {outcome.entryTime ? new Date(outcome.entryTime).toLocaleString() : "-"}
        </Descriptions.Item>
        <Descriptions.Item label="Exit time">
          {outcome.exitTime ? new Date(outcome.exitTime).toLocaleString() : "-"}
        </Descriptions.Item>
        <Descriptions.Item label="Cost R">{formatR(outcome.costs?.costR ?? null)}</Descriptions.Item>
        <Descriptions.Item label="MFE / MAE">
          {outcome.excursion
            ? `${formatR(outcome.excursion.mfeR)} / ${formatR(outcome.excursion.maeR)}`
            : "-"}
        </Descriptions.Item>
        <Descriptions.Item label="Engine">{record.engineVersion}</Descriptions.Item>
        <Descriptions.Item label="Market data hash">
          <Typography.Text copyable ellipsis>{record.marketDataSha256}</Typography.Text>
        </Descriptions.Item>
      </Descriptions>
    </div>
  );
}
