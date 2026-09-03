import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Button,
  ConfigProvider,
  Empty,
  Input,
  Layout,
  Segmented,
  Space,
  Spin,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { Activity, RefreshCw, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { fetchHealth, fetchSetupCandidates, type SetupCandidate } from "./api";

const { Content, Header } = Layout;

type AcceptedFilter = "ALL" | "ACCEPTED" | "REJECTED";

const setupColumns: ColumnsType<SetupCandidate> = [
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
];

export function App() {
  const [symbolFilter, setSymbolFilter] = useState("");
  const [acceptedFilter, setAcceptedFilter] = useState<AcceptedFilter>("ALL");
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
              />
            ) : null}

            <Table<SetupCandidate>
              rowKey="setupId"
              loading={setupsQuery.isLoading}
              columns={setupColumns}
              dataSource={setupsQuery.data?.items ?? []}
              pagination={false}
              scroll={{ x: 920 }}
              locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="Nincs setup" /> }}
            />
          </section>
        </Content>
      </Layout>
    </ConfigProvider>
  );
}
