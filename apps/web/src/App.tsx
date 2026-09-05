import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  ConfigProvider,
  Descriptions,
  Divider,
  Drawer,
  Empty,
  Input,
  Layout,
  Progress,
  Segmented,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { Activity, Eye, RefreshCw, Search } from "lucide-react";
import { useMemo, useState } from "react";

import {
  fetchHealth,
  fetchSetupCandidate,
  fetchSetupCandidates,
  type SetupCandidate,
  type SetupScoreComponent,
} from "./api";

const { Content, Header } = Layout;

type AcceptedFilter = "ALL" | "ACCEPTED" | "REJECTED";

function getSetupEmptyDescription(hasFilters: boolean): string {
  if (hasFilters) {
    return "Nincs találat a jelenlegi szűrőkkel.";
  }

  return "Még nincs beérkezett setup candidate.";
}

const componentColumns: ColumnsType<SetupScoreComponent> = [
  {
    title: "Component",
    dataIndex: "name",
    key: "name",
  },
  {
    title: "Score",
    dataIndex: "score",
    key: "score",
    render: (score: number, component) => `${score.toFixed(1)} / ${component.maxScore.toFixed(1)}`,
  },
  {
    title: "Reason",
    dataIndex: "reason",
    key: "reason",
  },
];

function createSetupColumns(onOpenDetails: (setupId: string) => void): ColumnsType<SetupCandidate> {
  return [
    {
      title: "Symbol",
      dataIndex: "symbol",
      key: "symbol",
      render: (symbol: string, record) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{symbol}</Typography.Text>
          <Typography.Text type="secondary">{`${record.exchange} / ${record.timeframe}`}</Typography.Text>
        </Space>
      ),
    },
    {
      title: "Direction",
      dataIndex: "direction",
      key: "direction",
      render: (direction: SetupCandidate["direction"]) => (
        <Tag color={direction === "LONG" ? "green" : "red"}>{direction}</Tag>
      ),
    },
    {
      title: "Bias",
      dataIndex: "htfBias",
      key: "htfBias",
      render: (bias: SetupCandidate["htfBias"]) => {
        const color = bias === "BULLISH" ? "cyan" : bias === "BEARISH" ? "orange" : "default";
        return <Tag color={color}>{bias}</Tag>;
      },
    },
    {
      title: "Score",
      dataIndex: "score",
      key: "score",
      sorter: (a, b) => a.score - b.score,
      render: (score: number, record) => (
        <Space size={8}>
          <Typography.Text strong>{score.toFixed(1)}</Typography.Text>
          <Tag color={record.accepted ? "blue" : "volcano"}>
            {record.accepted ? "ACCEPTED" : "REJECTED"}
          </Tag>
        </Space>
      ),
    },
    {
      title: "Reasons",
      dataIndex: "rejectionReasons",
      key: "rejectionReasons",
      render: (rejectionReasons: string[], record) => (
        <Typography.Text type={rejectionReasons.length > 0 ? "danger" : "secondary"}>
          {rejectionReasons.length > 0
            ? rejectionReasons.join(", ")
            : record.positiveReasons.slice(0, 2).join(", ")}
        </Typography.Text>
      ),
    },
    {
      title: "Received",
      dataIndex: "receivedAt",
      key: "receivedAt",
      render: (receivedAt: string) => new Date(receivedAt).toLocaleString(),
    },
    {
      title: "",
      key: "actions",
      width: 56,
      render: (_, record) => (
        <Button
          icon={<Eye size={16} />}
          onClick={(event) => {
            event.stopPropagation();
            onOpenDetails(record.setupId);
          }}
          aria-label="Setup részletek"
        />
      ),
    },
  ];
}

export function App() {
  const [symbolFilter, setSymbolFilter] = useState("");
  const [acceptedFilter, setAcceptedFilter] = useState<AcceptedFilter>("ALL");
  const [selectedSetupId, setSelectedSetupId] = useState<string | null>(null);
  const normalizedSymbolFilter = symbolFilter.trim().toUpperCase();
  const hasSetupFilters = normalizedSymbolFilter !== "" || acceptedFilter !== "ALL";
  const acceptedQueryValue = useMemo(() => {
    if (acceptedFilter === "ACCEPTED") {
      return true;
    }

    if (acceptedFilter === "REJECTED") {
      return false;
    }

    return undefined;
  }, [acceptedFilter]);

  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
    retry: 1,
  });

  const setupsQuery = useQuery({
    queryKey: ["setups", symbolFilter, acceptedQueryValue],
    queryFn: () =>
      fetchSetupCandidates({
        limit: 50,
        symbol: symbolFilter,
        accepted: acceptedQueryValue,
      }),
    retry: 1,
  });

  const selectedSetupQuery = useQuery({
    queryKey: ["setup", selectedSetupId],
    queryFn: () => fetchSetupCandidate(selectedSetupId ?? ""),
    enabled: selectedSetupId !== null,
    retry: 1,
  });

  const setupColumns = useMemo(
    () => createSetupColumns(setSelectedSetupId),
    [],
  );
  const setupItems = setupsQuery.data?.items ?? [];
  const setupCount = setupsQuery.data?.count ?? setupItems.length;
  const setupEmptyDescription = getSetupEmptyDescription(hasSetupFilters);
  const setupStatusColor = setupsQuery.isError
    ? "red"
    : setupsQuery.isFetching
      ? "processing"
      : setupCount > 0
        ? "green"
        : "default";
  const setupStatusLabel = setupsQuery.isError
    ? "API hiba"
    : setupsQuery.isLoading
      ? "Betöltés"
      : setupsQuery.isFetching
        ? "Frissítés"
        : `${setupCount} setup`;

  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: "#1677ff",
          borderRadius: 6,
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif",
        },
      }}
    >
      <Layout className="app-shell">
        <Header className="app-header">
          <Space size={12}>
            <Activity size={22} aria-hidden="true" />
            <Typography.Title level={1}>SMC AI Trading Assistant</Typography.Title>
          </Space>
        </Header>
        <Content className="app-content">
          <section className="status-panel" aria-label="Backend status">
            <div className="status-heading">
              <div>
                <Typography.Text type="secondary">System status</Typography.Text>
                <Typography.Title level={2}>Backend kapcsolat</Typography.Title>
              </div>
              <Button
                icon={<RefreshCw size={16} />}
                onClick={() => {
                  void healthQuery.refetch();
                  void setupsQuery.refetch();
                }}
                aria-label="Frissítés"
              />
            </div>

            {healthQuery.isLoading ? <Spin aria-label="Állapot lekérése" /> : null}

            {healthQuery.isError ? (
              <Alert
                type="error"
                showIcon
                message="A backend jelenleg nem érhető el."
                description="Ellenőrizd, hogy az API fut-e a konfigurált porton."
              />
            ) : null}

            {healthQuery.data ? (
              <div className="status-grid">
                <Statistic title="Állapot" value={healthQuery.data.status} />
                <Statistic title="Service" value={healthQuery.data.service} />
                <Statistic title="Version" value={healthQuery.data.version} />
                <Statistic
                  title="Timestamp"
                  value={new Date(healthQuery.data.timestamp).toLocaleString()}
                />
              </div>
            ) : null}
          </section>

          <section className="setups-panel" aria-label="Setup candidates">
            <div className="setups-heading">
              <div>
                <Typography.Text type="secondary">Setup candidates</Typography.Text>
                <Typography.Title level={2}>Pontozott setupok</Typography.Title>
              </div>
              <div className="setups-actions">
                <Input
                  allowClear
                  className="symbol-filter"
                  prefix={<Search size={16} aria-hidden="true" />}
                  placeholder="Symbol"
                  value={symbolFilter}
                  onChange={(event) => setSymbolFilter(event.target.value)}
                  aria-label="Symbol szűrő"
                />
                <Segmented<AcceptedFilter>
                  value={acceptedFilter}
                  options={[
                    { label: "All", value: "ALL" },
                    { label: "Accepted", value: "ACCEPTED" },
                    { label: "Rejected", value: "REJECTED" },
                  ]}
                  onChange={setAcceptedFilter}
                />
              </div>
            </div>

            {setupsQuery.isError ? (
              <Alert
                type="error"
                showIcon
                message="A setup lista nem érhető el."
                description="Ellenőrizd a backend kapcsolatot és a setup API útvonalat."
                action={
                  <Button
                    size="small"
                    icon={<RefreshCw size={14} />}
                    onClick={() => void setupsQuery.refetch()}
                  >
                    Újrapróbálás
                  </Button>
                }
              />
            ) : null}

            <div className="setup-state-bar">
              <Space size={8} wrap>
                <Tag color={setupStatusColor}>{setupStatusLabel}</Tag>
                {hasSetupFilters ? <Tag>Szűrve</Tag> : null}
              </Space>
              {setupsQuery.data ? (
                <Typography.Text type="secondary">
                  {`Megjelenítve: ${setupItems.length} / ${setupCount}`}
                </Typography.Text>
              ) : null}
            </div>

            <Table<SetupCandidate>
              rowKey="setupId"
              loading={setupsQuery.isLoading}
              columns={setupColumns}
              dataSource={setupsQuery.isError ? [] : setupItems}
              pagination={false}
              scroll={{ x: 920 }}
              onRow={(record) => ({
                onClick: () => setSelectedSetupId(record.setupId),
              })}
              locale={{
                emptyText: (
                  <Empty
                    image={Empty.PRESENTED_IMAGE_SIMPLE}
                    description={
                      setupsQuery.isError ? "A setupok nem tölthetők be." : setupEmptyDescription
                    }
                  />
                ),
              }}
            />
          </section>
        </Content>
        <Drawer
          width={560}
          open={selectedSetupId !== null}
          onClose={() => setSelectedSetupId(null)}
          title="Setup részletek"
        >
          {selectedSetupQuery.isLoading ? <Spin aria-label="Setup részletek lekérése" /> : null}

          {selectedSetupQuery.isError ? (
            <Alert
              type="error"
              showIcon
              message="A setup részletei nem érhetők el."
              description="Ellenőrizd, hogy a kiválasztott setup még létezik-e."
            />
          ) : null}

          {selectedSetupQuery.data ? <SetupDetails setup={selectedSetupQuery.data} /> : null}
        </Drawer>
      </Layout>
    </ConfigProvider>
  );
}

function SetupDetails({ setup }: { setup: SetupCandidate }) {
  return (
    <div className="setup-detail">
      <div className="setup-detail-title">
        <div>
          <Typography.Title level={3}>{setup.symbol}</Typography.Title>
          <Typography.Text type="secondary">{setup.setupId}</Typography.Text>
        </div>
        <Space size={8}>
          <Tag color={setup.direction === "LONG" ? "green" : "red"}>{setup.direction}</Tag>
          <Tag color={setup.accepted ? "blue" : "volcano"}>
            {setup.accepted ? "ACCEPTED" : "REJECTED"}
          </Tag>
        </Space>
      </div>

      <div className="setup-detail-score">
        <Progress percent={setup.score} strokeColor={setup.accepted ? "#1677ff" : "#cf1322"} />
      </div>

      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="Exchange">{setup.exchange}</Descriptions.Item>
        <Descriptions.Item label="Timeframe">{setup.timeframe}</Descriptions.Item>
        <Descriptions.Item label="HTF bias">{setup.htfBias}</Descriptions.Item>
        <Descriptions.Item label="Strategy">{setup.strategyVersion}</Descriptions.Item>
        <Descriptions.Item label="Scoring config">{setup.scoringConfigVersion}</Descriptions.Item>
        <Descriptions.Item label="Bar close">
          {new Date(setup.barCloseTime).toLocaleString()}
        </Descriptions.Item>
        <Descriptions.Item label="Received">
          {new Date(setup.receivedAt).toLocaleString()}
        </Descriptions.Item>
      </Descriptions>

      <Divider orientation="left">Components</Divider>
      <Table<SetupScoreComponent>
        rowKey="name"
        columns={componentColumns}
        dataSource={setup.components}
        pagination={false}
        size="small"
      />

      <Divider orientation="left">Reasons</Divider>
      <div className="setup-reason-grid">
        <ReasonList title="Positive" reasons={setup.positiveReasons} />
        <ReasonList title="Negative" reasons={setup.negativeReasons} />
        <ReasonList title="Reject" reasons={setup.rejectionReasons} />
      </div>
    </div>
  );
}

function ReasonList({ title, reasons }: { title: string; reasons: string[] }) {
  return (
    <div className="setup-reason-list">
      <Typography.Text strong>{title}</Typography.Text>
      {reasons.length > 0 ? (
        <ul>
          {reasons.map((reason) => (
            <li key={reason}>
              <Typography.Text>{reason}</Typography.Text>
            </li>
          ))}
        </ul>
      ) : (
        <Typography.Text type="secondary">-</Typography.Text>
      )}
    </div>
  );
}
