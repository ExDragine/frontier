import {
  Component,
  useLayoutEffect,
  useRef,
  type CSSProperties,
  type ReactNode,
} from "react";
import { flushSync } from "react-dom";
import { createRoot, type Root } from "react-dom/client";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";
import type { UIItem, UITable } from "./message-schema";
import type {
  DataNode,
  MediaNode,
  MessageDocument,
  MessageNode,
  Renderers,
} from "./message-types";

type HeaderFields = Pick<MessageDocument, "title" | "description" | "eyebrow">;

function Header({
  config,
  document = false,
}: {
  config: HeaderFields;
  document?: boolean;
}) {
  if (!config.title && !config.description && !config.eyebrow) return null;
  return (
    <header className="md-ui-header">
      {config.eyebrow && <div className="md-ui-eyebrow">{config.eyebrow}</div>}
      {config.title &&
        (document ? (
          <h2 className="md-ui-title">{config.title}</h2>
        ) : (
          <h3 className="md-ui-card-title">{config.title}</h3>
        ))}
      {config.description && (
        <p className="md-ui-description">{config.description}</p>
      )}
    </header>
  );
}

function StatusIcon({ status }: { status: string }) {
  const path =
    status === "success"
      ? "M21 12a9 9 0 1 1-4-7.5M8 11l4 4 9-10"
      : status === "warning" || status === "danger"
        ? "M12 3 2 21h20L12 3Zm0 6v5m0 3v.1"
        : "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM12 11v6m0-10v.1";
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  );
}

function ItemContent({ item }: { item: UIItem }) {
  return (
    <div className="md-ui-item-content">
      <div className="md-ui-item-header">
        <strong className="md-ui-item-title">{item.title}</strong>
        {item.meta && <span className="md-ui-item-meta">{item.meta}</span>}
      </div>
      {item.description && (
        <p className="md-ui-description">{item.description}</p>
      )}
    </div>
  );
}

function Children({
  nodes,
  renderers,
}: {
  nodes: MessageNode[];
  renderers: Renderers;
}) {
  return nodes.map((config, index) => (
    <MessageComponent key={index} config={config} renderers={renderers} />
  ));
}

function Media({ config }: { config: MediaNode }) {
  const title = "title" in config ? config.title : undefined;
  const url =
    config.source_url ||
    ("url" in config ? config.url : "https://www.openstreetmap.org/");
  return (
    <figure className={`md-ui-media md-media-${config.type}`}>
      {title && <h3 className="md-ui-card-title">{title}</h3>}
      {config.media_data ? (
        config.type === "iframe" ? (
          <iframe
            className="md-ui-frame"
            sandbox=""
            title={config.title}
            referrerPolicy="no-referrer"
            style={{
              aspectRatio: `${config.media_width} / ${config.media_height}`,
            }}
            // The frame receives only the server's PNG data URL, never the remote page.
            srcDoc={
              '<!doctype html><html><head><meta http-equiv="Content-Security-Policy" content="default-src &apos;none&apos;; img-src data:; style-src &apos;unsafe-inline&apos;"><style>html,body{margin:0;background:#fff}img{display:block;width:100%;height:auto}</style></head><body><img alt="" src="' +
              config.media_data +
              '"></body></html>'
            }
          />
        ) : (
          <img
            className={cn(
              "md-ui-picture",
              config.type === "image"
                ? `md-fit-${config.fit || "contain"} md-aspect-${config.aspect || "original"}`
                : "md-fit-contain md-aspect-original",
            )}
            src={config.media_data}
            alt={config.type === "image" ? config.alt : title || "地图"}
            width={config.media_width}
            height={config.media_height}
          />
        )
      ) : (
        <Alert variant="muted" className="md-media-fallback">
          <AlertDescription>
            {config.media_error || "素材未能加载，请查看原链接。"}
          </AlertDescription>
        </Alert>
      )}
      {config.caption && (
        <figcaption className="md-ui-description">{config.caption}</figcaption>
      )}
      {config.capture_note && (
        <div className="md-ui-description">{config.capture_note}</div>
      )}
      {config.type === "map" && (
        <div className="md-ui-url">
          WGS84 · {config.latitude}, {config.longitude} · © OpenStreetMap
          contributors
        </div>
      )}
      <div className="md-ui-url">{url}</div>
    </figure>
  );
}

function MessageTable({ config }: { config: UITable }) {
  const weights = config.column_widths;
  const total = weights?.reduce((sum, weight) => sum + weight, 0) || 1;
  return (
    <Table className={cn("md-ui-table", weights && "md-table-weighted")}>
      {config.caption && <TableCaption>{config.caption}</TableCaption>}
      {weights && (
        <colgroup>
          {weights.map((weight, index) => (
            <col key={index} style={{ width: `${(100 * weight) / total}%` }} />
          ))}
        </colgroup>
      )}
      <TableHeader>
        <TableRow>
          {config.columns.map((label, index) => (
            <TableHead key={index} scope="col">
              {label}
            </TableHead>
          ))}
        </TableRow>
      </TableHeader>
      <TableBody>
        {config.rows.map((values, index) => (
          <TableRow key={index}>
            {values.map((value, column) => (
              <TableCell key={column}>{value}</TableCell>
            ))}
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}

function DataBlock({
  config,
  renderers,
}: {
  config: DataNode;
  renderers: Renderers;
}) {
  const node = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const container = node.current!;
    let dispose: void | (() => void);
    // The React commit has attached the container, so ECharts sees its real width.
    if (config.type === "chart")
      dispose = renderers.renderChart(container, config.config);
    else if (config.type === "stats")
      renderers.renderStats(container, config.config);
    else renderers.renderTimeline(container, config.config);
    return () => {
      dispose?.();
      container.replaceChildren();
    };
  }, [config, renderers]);
  return <div className="md-ui-data" ref={node} />;
}

function MessageComponent({
  config,
  renderers,
}: {
  config: MessageNode;
  renderers: Renderers;
}): ReactNode {
  switch (config.type) {
    case "row":
    case "column":
    case "grid":
      return (
        <div
          className={`md-ui-${config.type} md-gap-${config.gap || "md"}`}
          style={
            config.type === "grid"
              ? ({ "--md-ui-columns": config.columns || 2 } as CSSProperties)
              : undefined
          }
        >
          <Children nodes={config.children} renderers={renderers} />
        </div>
      );
    case "card":
      return (
        <Card
          surface={config.variant || "outline"}
          tone={config.color || "neutral"}
          className={`md-ui-card md-card-${config.variant || "outline"} md-color-${config.color || "neutral"}`}
        >
          {(config.title || config.description || config.eyebrow) && (
            <CardHeader className="md-ui-header">
              {config.eyebrow && (
                <div className="md-ui-eyebrow">{config.eyebrow}</div>
              )}
              {config.title && (
                <CardTitle className="md-ui-card-title">
                  {config.title}
                </CardTitle>
              )}
              {config.description && (
                <CardDescription className="md-ui-description">
                  {config.description}
                </CardDescription>
              )}
            </CardHeader>
          )}
          <CardContent className="md-ui-content">
            <Children nodes={config.children} renderers={renderers} />
          </CardContent>
          {config.footer && (
            <CardFooter className="md-ui-card-footer">
              {config.footer}
            </CardFooter>
          )}
        </Card>
      );
    case "section":
      return (
        <section className="md-ui-section">
          <Header config={config} />
          <div className="md-ui-content">
            <Children nodes={config.children} renderers={renderers} />
          </div>
        </section>
      );
    case "heading":
      return <h3 className="md-ui-heading">{config.text}</h3>;
    case "text":
      return (
        <p className={`md-ui-text md-text-${config.variant || "body"}`}>
          {config.text}
        </p>
      );
    case "prose":
      // Only the HTML-disabled server Markdown parser can supply `rendered`.
      return (
        <div
          className="md-ui-prose"
          dangerouslySetInnerHTML={{ __html: config.rendered }}
        />
      );
    case "badge":
      return (
        <Badge
          variant={
            config.variant === "solid"
              ? "default"
              : config.variant || "secondary"
          }
          tone={config.status || "neutral"}
          className={`md-ui-badge md-status-${config.status || "neutral"}`}
        >
          {config.text}
        </Badge>
      );
    case "callout":
    case "alert":
      return (
        <Alert
          variant={config.status || "neutral"}
          role="note"
          className={`md-ui-alert md-status-${config.status || "neutral"}`}
        >
          <StatusIcon status={config.status || "neutral"} />
          <div className="md-ui-alert-body">
            {config.title && (
              <AlertTitle className="md-ui-alert-title">
                {config.title}
              </AlertTitle>
            )}
            <AlertDescription className="md-ui-text">
              {config.text}
            </AlertDescription>
          </div>
        </Alert>
      );
    case "link":
      return (
        <div className="md-ui-link">
          <strong>{config.label}</strong>
          <div className="md-ui-url">{config.url}</div>
        </div>
      );
    case "sources":
      return (
        <ol className="md-ui-sources">
          {config.items.map((source, index) => (
            <li key={index}>
              <strong className="md-ui-source-label">{source.label}</strong>
              {source.description && (
                <p className="md-ui-description">{source.description}</p>
              )}
              <div className="md-ui-url">{source.url}</div>
            </li>
          ))}
        </ol>
      );
    case "image":
    case "map":
    case "iframe":
      return <Media config={config} />;
    case "code":
      return (
        <pre className="md-ui-code">
          <code>{config.text}</code>
        </pre>
      );
    case "mermaid":
      return <div className="mermaid">{config.text}</div>;
    case "steps":
    case "list": {
      const Tag = config.type === "steps" ? "ol" : "ul";
      return (
        <Tag
          className={
            config.type === "steps"
              ? "md-ui-steps"
              : `md-ui-list md-list-${config.variant || "plain"}`
          }
        >
          {config.items.map((item, index) => (
            <li key={index} className="md-ui-item">
              {config.type === "steps" && (
                <span className="md-ui-step-number">{index + 1}</span>
              )}
              <ItemContent
                item={typeof item === "string" ? { title: item } : item}
              />
            </li>
          ))}
        </Tag>
      );
    }
    case "facts":
      return (
        <dl
          className="md-ui-facts"
          style={{ "--md-fact-columns": config.columns || 1 } as CSSProperties}
        >
          {config.items.map((item, index) => (
            <div className="md-ui-fact" key={index}>
              <dt>{item.label}</dt>
              <dd>{item.value}</dd>
            </div>
          ))}
        </dl>
      );
    case "separator":
      return (
        <div className="md-ui-separator">
          <Separator className="min-w-0 flex-1" decorative={!!config.label} />
          {config.label && (
            <>
              <span>{config.label}</span>
              <Separator className="min-w-0 flex-1" />
            </>
          )}
        </div>
      );
    case "quote":
      return (
        <blockquote className="md-ui-quote">
          <p>{config.text}</p>
          {config.attribution && <cite>{config.attribution}</cite>}
        </blockquote>
      );
    case "progress":
      return (
        <div className="md-ui-progress">
          <div className="md-ui-item-header">
            <strong>{config.label}</strong>
            <span className="md-ui-item-meta">{config.value}%</span>
          </div>
          <Progress value={config.value} aria-label={config.label} />
          {config.detail && (
            <p className="md-ui-description">{config.detail}</p>
          )}
        </div>
      );
    case "table":
      return <MessageTable config={config} />;
    case "chart":
    case "stats":
    case "timeline":
      return <DataBlock config={config} renderers={renderers} />;
    default:
      throw new Error("Unsupported UI component");
  }
}

class MessageBoundary extends Component<
  { children: ReactNode; onError: Renderers["onError"] },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch(error: unknown) {
    this.props.onError(error);
  }
  render() {
    return this.state.failed ? (
      <div className="md-rich-error">增强内容渲染失败，已保留其余内容。</div>
    ) : (
      this.props.children
    );
  }
}

const roots = new WeakMap<HTMLElement, { root: Root; revision: number }>();

export function renderMessageUI(
  container: HTMLElement,
  config: MessageDocument,
  renderers: Renderers,
) {
  container.classList.add("md-ui-document");
  container.dataset.messageEngine = "react";
  let mounted = roots.get(container);
  if (!mounted) {
    mounted = {
      root: createRoot(container, { onCaughtError: () => {} }),
      revision: 0,
    };
    roots.set(container, mounted);
  }
  const { root } = mounted;
  // A screenshot needs one complete commit before math, Mermaid and highlighting.
  flushSync(() =>
    root.render(
      <MessageBoundary key={++mounted.revision} onError={renderers.onError}>
        <Header config={config} document />
        <Children nodes={config.children} renderers={renderers} />
      </MessageBoundary>,
    ),
  );
}
