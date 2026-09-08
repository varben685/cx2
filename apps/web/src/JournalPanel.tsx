import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  Button,
  Checkbox,
  Descriptions,
  Drawer,
  Empty,
  Input,
  Modal,
  Rate,
  Select,
  Space,
  Table,
  Tag,
  Timeline,
  Tooltip,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { BookPlus, Eye, Pencil, RefreshCw } from "lucide-react";
import { useMemo, useState } from "react";

import {
  ApiError,
  createJournalEntry,
  fetchJournal,
  fetchJournalEntry,
  fetchJournalRevisions,
  fetchSetupCandidates,
  updateJournalEntry,
  type JournalContent,
  type JournalEntry,
  type JournalExecutionStatus,
} from "./api";

const { TextArea } = Input;

type JournalDraft = JournalContent & {
  setupId: string;
  outcomeId: string;
};

const emptyDraft: JournalDraft = {
  setupId: "",
  outcomeId: "",
  executionStatus: "NOT_RECORDED",
  userNote: null,
  screenshotReference: null,
  manualRating: null,
  manualOverride: false,
  overrideReason: null,
  tags: [],
};

function statusColor(status: JournalExecutionStatus): string {
  if (status === "TAKEN") return "green";
  if (status === "SKIPPED") return "orange";
  return "default";
}

function formatR(value: number | null): string {
  return value === null ? "-" : `${value.toFixed(3)}R`;
}

function entryToDraft(entry: JournalEntry): JournalDraft {
  return {
    setupId: entry.setupId,
    outcomeId: entry.outcomeId ?? "",
    executionStatus: entry.executionStatus,
    userNote: entry.userNote,
    screenshotReference: entry.screenshotReference,
    manualRating: entry.manualRating,
    manualOverride: entry.manualOverride,
    overrideReason: entry.overrideReason,
    tags: entry.tags,
  };
}

function journalColumns(onOpen: (journalId: string) => void): ColumnsType<JournalEntry> {
  return [
    {
      title: "Market",
      key: "market",
      render: (_, entry) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{entry.symbol}</Typography.Text>
          <Typography.Text type="secondary">{`${entry.exchange} / ${entry.timeframe}`}</Typography.Text>
        </Space>
      ),
    },
    {
      title: "Decision",
      dataIndex: "executionStatus",
      key: "executionStatus",
      width: 130,
      render: (value: JournalExecutionStatus) => <Tag color={statusColor(value)}>{value}</Tag>,
    },
    {
      title: "Outcome",
      key: "outcome",
      width: 126,
      render: (_, entry) => entry.outcomeLabel ?? "-",
    },
    {
      title: "Net R",
      key: "realizedR",
      width: 100,
      render: (_, entry) => formatR(entry.realizedR),
    },
    {
      title: "Rating",
      dataIndex: "manualRating",
      key: "manualRating",
      width: 88,
      render: (value: number | null) => value ?? "-",
    },
    {
      title: "Note",
      dataIndex: "userNote",
      key: "userNote",
      ellipsis: true,
      render: (value: string | null) => value ?? "-",
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
      render: (_, entry) => (
        <Tooltip title="Journal megnyitása">
          <Button
            icon={<Eye size={16} />}
            aria-label="Journal megnyitása"
            onClick={(event) => {
              event.stopPropagation();
              onOpen(entry.journalId);
            }}
          />
        </Tooltip>
      ),
    },
  ];
}

export function JournalPanel() {
  const queryClient = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [editingEntry, setEditingEntry] = useState<JournalEntry | null>(null);
  const [isEditorOpen, setEditorOpen] = useState(false);
  const [draft, setDraft] = useState<JournalDraft>(emptyDraft);
  const journalsQuery = useQuery({
    queryKey: ["journal"],
    queryFn: () => fetchJournal(100),
    retry: 1,
  });
  const setupsQuery = useQuery({
    queryKey: ["journal-setups"],
    queryFn: () => fetchSetupCandidates({ limit: 100 }),
    retry: 1,
  });
  const detailQuery = useQuery({
    queryKey: ["journal", selectedId],
    queryFn: () => fetchJournalEntry(selectedId ?? ""),
    enabled: selectedId !== null,
    retry: 1,
  });
  const revisionsQuery = useQuery({
    queryKey: ["journal-revisions", selectedId],
    queryFn: () => fetchJournalRevisions(selectedId ?? ""),
    enabled: selectedId !== null,
    retry: 1,
  });
  const existingSetupIds = useMemo(
    () => new Set(journalsQuery.data?.items.map((entry) => entry.setupId) ?? []),
    [journalsQuery.data],
  );
  const availableSetups = setupsQuery.data?.items.filter(
    (setup) => !existingSetupIds.has(setup.setupId),
  ) ?? [];

  async function refreshJournal(entry: JournalEntry) {
    setSelectedId(entry.journalId);
    setEditorOpen(false);
    setEditingEntry(null);
    await queryClient.invalidateQueries({ queryKey: ["journal"] });
    await queryClient.invalidateQueries({ queryKey: ["journal-revisions", entry.journalId] });
    await queryClient.invalidateQueries({ queryKey: ["analytics"] });
  }

  const createMutation = useMutation({
    mutationFn: createJournalEntry,
    onSuccess: refreshJournal,
  });
  const updateMutation = useMutation({
    mutationFn: updateJournalEntry,
    onSuccess: refreshJournal,
  });
  const columns = useMemo(() => journalColumns(setSelectedId), []);

  function openCreate() {
    createMutation.reset();
    updateMutation.reset();
    setEditingEntry(null);
    setDraft({ ...emptyDraft, setupId: availableSetups[0]?.setupId ?? "" });
    setEditorOpen(true);
  }

  function openEdit(entry: JournalEntry) {
    createMutation.reset();
    updateMutation.reset();
    setEditingEntry(entry);
    setDraft(entryToDraft(entry));
    setEditorOpen(true);
  }

  function submit() {
    const content: JournalContent = {
      executionStatus: draft.executionStatus,
      userNote: draft.userNote,
      screenshotReference: draft.screenshotReference,
      manualRating: draft.manualRating,
      manualOverride: draft.manualOverride,
      overrideReason: draft.manualOverride ? draft.overrideReason : null,
      tags: draft.tags,
    };
    if (editingEntry) {
      updateMutation.mutate({
        ...content,
        journalId: editingEntry.journalId,
        expectedRevision: editingEntry.revision,
      });
      return;
    }
    createMutation.mutate({
      ...content,
      setupId: draft.setupId,
      ...(draft.outcomeId.trim() ? { outcomeId: draft.outcomeId.trim() } : {}),
    });
  }

  const mutationError = createMutation.error ?? updateMutation.error;
  const editorError = mutationError instanceof ApiError
    ? mutationError.message
    : mutationError
      ? "A journal mentése sikertelen."
      : null;
  const detail = detailQuery.data ?? null;

  return (
    <section className="journal-panel" aria-label="Trading journal">
      <div className="setups-heading">
        <div>
          <Typography.Text type="secondary">Trading journal</Typography.Text>
          <Typography.Title level={2}>Döntési napló</Typography.Title>
        </div>
        <Space>
          <Tooltip title="Journal frissítése">
            <Button
              icon={<RefreshCw size={16} />}
              aria-label="Journal frissítése"
              onClick={() => void journalsQuery.refetch()}
            />
          </Tooltip>
          <Button
            type="primary"
            icon={<BookPlus size={16} />}
            disabled={availableSetups.length === 0}
            onClick={openCreate}
          >
            Új bejegyzés
          </Button>
        </Space>
      </div>

      {journalsQuery.isError ? (
        <Alert
          type="error"
          showIcon
          message="A journal nem tölthető be."
          action={<Button onClick={() => void journalsQuery.refetch()}>Újrapróbálás</Button>}
        />
      ) : null}
      {setupsQuery.isError ? (
        <Alert
          type="warning"
          showIcon
          message="Az új bejegyzéshez szükséges setupok nem tölthetők be."
          action={<Button onClick={() => void setupsQuery.refetch()}>Setupok frissítése</Button>}
        />
      ) : null}
      <Table<JournalEntry>
        rowKey="journalId"
        size="small"
        loading={journalsQuery.isLoading}
        columns={columns}
        dataSource={journalsQuery.isError ? [] : (journalsQuery.data?.items ?? [])}
        pagination={false}
        scroll={{ x: 940 }}
        onRow={(entry) => ({ onClick: () => setSelectedId(entry.journalId) })}
        locale={{
          emptyText: (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="Még nincs journal bejegyzés."
            />
          ),
        }}
      />

      <JournalEditor
        open={isEditorOpen}
        editing={editingEntry !== null}
        draft={draft}
        setDraft={setDraft}
        setups={availableSetups.map((setup) => ({
          value: setup.setupId,
          label: `${setup.symbol} / ${setup.timeframe} / ${setup.direction}`,
        }))}
        error={editorError}
        submitting={createMutation.isPending || updateMutation.isPending}
        onCancel={() => setEditorOpen(false)}
        onSubmit={submit}
      />

      <Drawer
        width="min(560px, 100vw)"
        open={selectedId !== null}
        onClose={() => setSelectedId(null)}
        title="Journal részletek"
        extra={
          detail ? (
            <Button icon={<Pencil size={16} />} onClick={() => openEdit(detail)}>
              Szerkesztés
            </Button>
          ) : null
        }
      >
        {detailQuery.isError ? (
          <Alert type="error" showIcon message="A bejegyzés nem tölthető be." />
        ) : detail ? (
          <JournalDetails entry={detail} revisions={revisionsQuery.data?.items ?? []} />
        ) : (
          <Empty description="Nincs adat." />
        )}
      </Drawer>
    </section>
  );
}

type JournalEditorProps = {
  open: boolean;
  editing: boolean;
  draft: JournalDraft;
  setDraft: (draft: JournalDraft) => void;
  setups: { value: string; label: string }[];
  error: string | null;
  submitting: boolean;
  onCancel: () => void;
  onSubmit: () => void;
};

function JournalEditor({
  open,
  editing,
  draft,
  setDraft,
  setups,
  error,
  submitting,
  onCancel,
  onSubmit,
}: JournalEditorProps) {
  return (
    <Modal
      width={720}
      open={open}
      title={editing ? "Journal szerkesztése" : "Új journal bejegyzés"}
      onCancel={onCancel}
      okText="Mentés"
      cancelText="Mégse"
      confirmLoading={submitting}
      okButtonProps={{ disabled: draft.setupId === "" }}
      onOk={onSubmit}
    >
      <div className="journal-form">
        {error ? <Alert type="error" showIcon message={error} /> : null}
        <label className="field-label">
          <Typography.Text strong>Setup</Typography.Text>
          <Select
            disabled={editing}
            value={draft.setupId || undefined}
            options={setups}
            placeholder="Válassz setupot"
            onChange={(setupId) => setDraft({ ...draft, setupId })}
          />
        </label>
        {!editing ? (
          <label className="field-label">
            <Typography.Text strong>Outcome ID (opcionális)</Typography.Text>
            <Input
              value={draft.outcomeId}
              placeholder="Üresen a legfrissebb kapcsolódó outcome"
              onChange={(event) => setDraft({ ...draft, outcomeId: event.target.value })}
            />
          </label>
        ) : null}
        <div className="journal-fields-grid">
          <label className="field-label">
            <Typography.Text strong>Döntés</Typography.Text>
            <Select
              value={draft.executionStatus}
              options={[
                { value: "NOT_RECORDED", label: "Nincs rögzítve" },
                { value: "TAKEN", label: "Megkötöttem" },
                { value: "SKIPPED", label: "Kihagytam" },
              ]}
              onChange={(executionStatus) => setDraft({ ...draft, executionStatus })}
            />
          </label>
          <label className="field-label">
            <Typography.Text strong>Manuális értékelés</Typography.Text>
            <Rate
              value={draft.manualRating ?? 0}
              onChange={(manualRating) =>
                setDraft({ ...draft, manualRating: manualRating || null })
              }
            />
          </label>
        </div>
        <label className="field-label">
          <Typography.Text strong>Megjegyzés</Typography.Text>
          <TextArea
            rows={5}
            value={draft.userNote ?? ""}
            maxLength={5000}
            onChange={(event) => setDraft({ ...draft, userNote: event.target.value || null })}
          />
        </label>
        <label className="field-label">
          <Typography.Text strong>Címkék</Typography.Text>
          <Select
            mode="tags"
            value={draft.tags}
            maxCount={10}
            tokenSeparators={[","]}
            placeholder="például: A+, türelem, London"
            onChange={(tags) => setDraft({ ...draft, tags })}
          />
        </label>
        <label className="field-label">
          <Typography.Text strong>Screenshot URL vagy fájlhivatkozás</Typography.Text>
          <Input
            value={draft.screenshotReference ?? ""}
            onChange={(event) =>
              setDraft({ ...draft, screenshotReference: event.target.value || null })
            }
          />
        </label>
        <Checkbox
          checked={draft.manualOverride}
          onChange={(event) =>
            setDraft({
              ...draft,
              manualOverride: event.target.checked,
              overrideReason: event.target.checked ? draft.overrideReason : null,
            })
          }
        >
          Manuálisan felülbíráltam a rendszer javaslatát
        </Checkbox>
        {draft.manualOverride ? (
          <label className="field-label">
            <Typography.Text strong>Felülbírálás indoka</Typography.Text>
            <TextArea
              rows={3}
              value={draft.overrideReason ?? ""}
              maxLength={1000}
              onChange={(event) =>
                setDraft({ ...draft, overrideReason: event.target.value || null })
              }
            />
          </label>
        ) : null}
      </div>
    </Modal>
  );
}

function JournalDetails({ entry, revisions }: { entry: JournalEntry; revisions: JournalEntry[] }) {
  return (
    <div className="journal-detail">
      <div className="setup-detail-title">
        <div>
          <Typography.Title level={3}>{entry.symbol}</Typography.Title>
          <Typography.Text type="secondary">{`${entry.exchange} / ${entry.timeframe} / ${entry.session}`}</Typography.Text>
        </div>
        <Tag color={statusColor(entry.executionStatus)}>{entry.executionStatus}</Tag>
      </div>
      <Descriptions column={1} size="small" bordered>
        <Descriptions.Item label="Direction">{entry.direction}</Descriptions.Item>
        <Descriptions.Item label="Signal time">
          {new Date(entry.signalTime).toLocaleString()}
        </Descriptions.Item>
        <Descriptions.Item label="Outcome">{entry.outcomeLabel ?? "-"}</Descriptions.Item>
        <Descriptions.Item label="Net R">{formatR(entry.realizedR)}</Descriptions.Item>
        <Descriptions.Item label="MFE / MAE">
          {`${formatR(entry.mfeR)} / ${formatR(entry.maeR)}`}
        </Descriptions.Item>
        <Descriptions.Item label="Rating">{entry.manualRating ?? "-"} / 5</Descriptions.Item>
        <Descriptions.Item label="Manual override">
          {entry.manualOverride ? "Igen" : "Nem"}
        </Descriptions.Item>
        <Descriptions.Item label="Override reason">{entry.overrideReason ?? "-"}</Descriptions.Item>
        <Descriptions.Item label="Screenshot">
          {entry.screenshotReference ?? "-"}
        </Descriptions.Item>
        <Descriptions.Item label="Revision">{entry.revision}</Descriptions.Item>
      </Descriptions>
      <div>
        <Typography.Text strong>Megjegyzés</Typography.Text>
        <Typography.Paragraph className="journal-note">
          {entry.userNote ?? "Nincs megjegyzés."}
        </Typography.Paragraph>
      </div>
      <Space wrap>
        {entry.tags.map((tag) => <Tag key={tag}>{tag}</Tag>)}
      </Space>
      <div>
        <Typography.Title level={4}>Előzmények</Typography.Title>
        <Timeline
          items={revisions.map((revision) => ({
            children: `v${revision.revision} · ${new Date(revision.updatedAt).toLocaleString()} · ${revision.executionStatus}`,
          }))}
        />
      </div>
    </div>
  );
}
