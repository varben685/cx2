import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Descriptions,
  Divider,
  Drawer,
  Empty,
  InputNumber,
  Select,
  Space,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { Eye, Plus, RefreshCw, Send, XCircle } from "lucide-react";
import { useMemo, useState } from "react";

import {
  ApiError,
  cancelPaperTrade,
  closePaperTrade,
  createPaperTrade,
  fetchPaperTradeEvents,
  fetchPaperTrades,
  observePaperTradePrice,
  type PaperTrade,
  type PaperTradeEvent,
  type SetupCandidate,
} from "./api";

const statusColors: Record<PaperTrade["status"], string> = {
  PENDING: "gold",
  OPEN: "blue",
  CLOSED: "green",
  CANCELLED: "default",
};

export function PaperTradingPanel({ setups }: { setups: SetupCandidate[] }) {
  const queryClient = useQueryClient();
  const [setupId, setSetupId] = useState<string>();
  const [accountBalance, setAccountBalance] = useState<number | null>(10_000);
  const [riskPercent, setRiskPercent] = useState<number | null>(1);
  const [selectedTradeId, setSelectedTradeId] = useState<string | null>(null);
  const [marketPrice, setMarketPrice] = useState<number | null>(null);
  const [manualExitPrice, setManualExitPrice] = useState<number | null>(null);

  const tradesQuery = useQuery({
    queryKey: ["paper-trades"],
    queryFn: () => fetchPaperTrades(),
    retry: 1,
    refetchInterval: 5_000,
  });
  const selectedTrade = tradesQuery.data?.items.find(
    (trade) => trade.tradeId === selectedTradeId,
  );
  const eventsQuery = useQuery({
    queryKey: ["paper-trade-events", selectedTradeId],
    queryFn: () => fetchPaperTradeEvents(selectedTradeId ?? ""),
    enabled: selectedTradeId !== null,
    retry: 1,
    refetchInterval: 5_000,
  });

  const refreshTrades = async (trade?: PaperTrade) => {
    await queryClient.invalidateQueries({ queryKey: ["paper-trades"] });
    if (trade) {
      setSelectedTradeId(trade.tradeId);
      await queryClient.invalidateQueries({ queryKey: ["paper-trade-events", trade.tradeId] });
    }
  };
  const showError = (error: Error) => {
    void message.error(error instanceof ApiError ? error.message : "A művelet sikertelen.");
  };
  const createMutation = useMutation({
    mutationFn: createPaperTrade,
    onSuccess: async (trade) => {
      setSetupId(undefined);
      await refreshTrades(trade);
      void message.success("Paper trade létrehozva.");
    },
    onError: showError,
  });
  const priceMutation = useMutation({
    mutationFn: ({ tradeId, price }: { tradeId: string; price: number }) =>
      observePaperTradePrice(tradeId, price),
    onSuccess: async (trade) => {
      setMarketPrice(null);
      await refreshTrades(trade);
    },
    onError: showError,
  });
  const closeMutation = useMutation({
    mutationFn: ({ tradeId, exitPrice }: { tradeId: string; exitPrice: number }) =>
      closePaperTrade(tradeId, exitPrice),
    onSuccess: async (trade) => {
      setManualExitPrice(null);
      await refreshTrades(trade);
    },
    onError: showError,
  });
  const cancelMutation = useMutation({
    mutationFn: cancelPaperTrade,
    onSuccess: refreshTrades,
    onError: showError,
  });

  const acceptedSetups = useMemo(
    () => setups.filter((setup) => setup.accepted),
    [setups],
  );
  const existingSetupIds = new Set(tradesQuery.data?.items.map((trade) => trade.setupId));
  const setupOptions = acceptedSetups
    .filter((setup) => !existingSetupIds.has(setup.setupId))
    .map((setup) => ({
      value: setup.setupId,
      label: `${setup.symbol} · ${setup.direction} · ${setup.score.toFixed(0)}`,
    }));
  const columns = useMemo<ColumnsType<PaperTrade>>(
    () => [
      {
        title: "Symbol",
        dataIndex: "symbol",
        key: "symbol",
        render: (symbol: string, trade) => (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{symbol}</Typography.Text>
            <Typography.Text type="secondary">{trade.direction}</Typography.Text>
          </Space>
        ),
      },
      {
        title: "Status",
        dataIndex: "status",
        key: "status",
        render: (status: PaperTrade["status"]) => <Tag color={statusColors[status]}>{status}</Tag>,
      },
      {
        title: "Plan",
        key: "plan",
        render: (_, trade) => `${trade.entryPrice} / ${trade.stopLoss} / ${trade.takeProfit}`,
      },
      {
        title: "Risk",
        key: "risk",
        render: (_, trade) => `${trade.riskAmount.toFixed(2)} (${trade.riskPercent}%)`,
      },
      {
        title: "Result",
        dataIndex: "realizedR",
        key: "realizedR",
        render: (value: number | null) => (value === null ? "-" : `${value.toFixed(2)} R`),
      },
      {
        title: "Updated",
        dataIndex: "updatedAt",
        key: "updatedAt",
        render: (value: string) => new Date(value).toLocaleString(),
      },
      {
        title: "",
        key: "actions",
        width: 56,
        render: (_, trade) => (
          <Button
            icon={<Eye size={16} />}
            onClick={() => setSelectedTradeId(trade.tradeId)}
            aria-label={`${trade.symbol} paper trade részletek`}
          />
        ),
      },
    ],
    [],
  );

  return (
    <section className="paper-trading-panel" aria-label="Paper trading">
      <div className="paper-heading">
        <div>
          <Typography.Text type="secondary">Simulated execution</Typography.Text>
          <Typography.Title level={2}>Paper trading</Typography.Title>
        </div>
        <Button
          icon={<RefreshCw size={16} />}
          onClick={() => void tradesQuery.refetch()}
          aria-label="Paper trade lista frissítése"
        />
      </div>

      <div className="paper-create-row">
        <label className="field-label paper-setup-select">
          <Typography.Text>Setup</Typography.Text>
          <Select
            showSearch
            value={setupId}
            options={setupOptions}
            onChange={setSetupId}
            placeholder="Elfogadott setup"
            aria-label="Paper trade setup"
          />
        </label>
        <label className="field-label">
          <Typography.Text>Account balance</Typography.Text>
          <InputNumber
            min={1}
            value={accountBalance}
            onChange={setAccountBalance}
            className="numeric-input"
            aria-label="Paper account balance"
          />
        </label>
        <label className="field-label">
          <Typography.Text>Risk %</Typography.Text>
          <InputNumber
            min={0.01}
            max={100}
            step={0.1}
            value={riskPercent}
            onChange={setRiskPercent}
            className="numeric-input"
            aria-label="Paper risk percent"
          />
        </label>
        <Button
          type="primary"
          icon={<Plus size={16} />}
          disabled={!setupId || accountBalance === null || riskPercent === null}
          loading={createMutation.isPending}
          onClick={() => {
            if (setupId && accountBalance !== null && riskPercent !== null) {
              createMutation.mutate({ setupId, accountBalance, riskPercent });
            }
          }}
        >
          Új trade
        </Button>
      </div>

      {tradesQuery.isError ? (
        <Alert
          type="error"
          showIcon
          message="A paper trade lista nem érhető el."
          action={<Button onClick={() => void tradesQuery.refetch()}>Újrapróbálás</Button>}
        />
      ) : null}

      <Table<PaperTrade>
        rowKey="tradeId"
        columns={columns}
        dataSource={tradesQuery.isError ? [] : tradesQuery.data?.items}
        loading={tradesQuery.isLoading}
        pagination={false}
        scroll={{ x: 900 }}
        locale={{
          emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Még nincs paper trade." />,
        }}
      />

      <Drawer
        width="min(560px, 100vw)"
        open={selectedTradeId !== null}
        onClose={() => setSelectedTradeId(null)}
        title="Paper trade részletek"
      >
        {selectedTrade ? (
          <div className="paper-detail">
            <div className="paper-detail-heading">
              <Typography.Title level={3}>{selectedTrade.symbol}</Typography.Title>
              <Tag color={statusColors[selectedTrade.status]}>{selectedTrade.status}</Tag>
            </div>
            <Descriptions column={1} size="small" bordered>
              <Descriptions.Item label="Direction">{selectedTrade.direction}</Descriptions.Item>
              <Descriptions.Item label="Entry">{selectedTrade.entryPrice}</Descriptions.Item>
              <Descriptions.Item label="Stop loss">{selectedTrade.stopLoss}</Descriptions.Item>
              <Descriptions.Item label="Take profit">{selectedTrade.takeProfit}</Descriptions.Item>
              <Descriptions.Item label="Quantity">{selectedTrade.quantity.toFixed(8)}</Descriptions.Item>
              <Descriptions.Item label="Risk">
                {`${selectedTrade.riskAmount.toFixed(2)} (${selectedTrade.riskPercent}%)`}
              </Descriptions.Item>
              <Descriptions.Item label="Result">
                {selectedTrade.realizedR === null ? "-" : `${selectedTrade.realizedR.toFixed(2)} R`}
              </Descriptions.Item>
              <Descriptions.Item label="Risk policy">
                {selectedTrade.riskPolicyVersion}
              </Descriptions.Item>
            </Descriptions>

            {selectedTrade.status === "PENDING" || selectedTrade.status === "OPEN" ? (
              <div className="paper-actions">
                <label className="field-label">
                  <Typography.Text>Market price</Typography.Text>
                  <InputNumber
                    min={0.00000001}
                    value={marketPrice}
                    onChange={setMarketPrice}
                    className="numeric-input"
                    aria-label="Paper market price"
                  />
                </label>
                <Button
                  icon={<Send size={16} />}
                  disabled={marketPrice === null}
                  loading={priceMutation.isPending}
                  onClick={() => {
                    if (marketPrice !== null) {
                      priceMutation.mutate({ tradeId: selectedTrade.tradeId, price: marketPrice });
                    }
                  }}
                >
                  Ár küldése
                </Button>
              </div>
            ) : null}

            {selectedTrade.status === "OPEN" ? (
              <div className="paper-actions">
                <label className="field-label">
                  <Typography.Text>Manual exit price</Typography.Text>
                  <InputNumber
                    min={0.00000001}
                    value={manualExitPrice}
                    onChange={setManualExitPrice}
                    className="numeric-input"
                    aria-label="Paper manual exit price"
                  />
                </label>
                <Button
                  disabled={manualExitPrice === null}
                  loading={closeMutation.isPending}
                  onClick={() => {
                    if (manualExitPrice !== null) {
                      closeMutation.mutate({
                        tradeId: selectedTrade.tradeId,
                        exitPrice: manualExitPrice,
                      });
                    }
                  }}
                >
                  Manuális zárás
                </Button>
              </div>
            ) : null}

            {selectedTrade.status === "PENDING" ? (
              <Button
                danger
                icon={<XCircle size={16} />}
                loading={cancelMutation.isPending}
                onClick={() => cancelMutation.mutate(selectedTrade.tradeId)}
              >
                Visszavonás
              </Button>
            ) : null}

            <Divider orientation="left">Execution log</Divider>
            <ExecutionLog events={eventsQuery.data?.items ?? []} loading={eventsQuery.isLoading} />
          </div>
        ) : null}
      </Drawer>
    </section>
  );
}

function ExecutionLog({ events, loading }: { events: PaperTradeEvent[]; loading: boolean }) {
  return (
    <Table<PaperTradeEvent>
      rowKey="sequence"
      loading={loading}
      size="small"
      pagination={false}
      columns={[
        { title: "#", dataIndex: "sequence", key: "sequence", width: 48 },
        { title: "Event", dataIndex: "eventType", key: "eventType" },
        {
          title: "Time",
          dataIndex: "occurredAt",
          key: "occurredAt",
          render: (value: string) => new Date(value).toLocaleString(),
        },
        {
          title: "Details",
          dataIndex: "details",
          key: "details",
          render: (details: Record<string, unknown>) =>
            Object.entries(details)
              .map(([key, value]) => `${key}: ${String(value)}`)
              .join(" · "),
        },
      ]}
      dataSource={events}
      locale={{ emptyText: "Nincs végrehajtási esemény." }}
      scroll={{ x: 620 }}
    />
  );
}
