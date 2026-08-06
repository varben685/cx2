import { useQuery } from "@tanstack/react-query";
import { Alert, Button, ConfigProvider, Layout, Space, Spin, Statistic, Typography } from "antd";
import { Activity, RefreshCw } from "lucide-react";

import { fetchHealth } from "./api";

const { Content, Header } = Layout;

export function App() {
  const healthQuery = useQuery({
    queryKey: ["health"],
    queryFn: fetchHealth,
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
                onClick={() => void healthQuery.refetch()}
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
        </Content>
      </Layout>
    </ConfigProvider>
  );
}
