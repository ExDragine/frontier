import type {
  ChartBlock,
  StatsBlock,
  TimelineBlock,
  UIBlock,
  UIFrame,
  UIImage,
  UIMap,
  UIProse,
} from "./message-schema";

// Only the server can add these fields after validation and bounded media loading.
type LoadedMedia = {
  media_data?: string;
  media_width?: number;
  media_height?: number;
  media_error?: string;
  source_url?: string;
  capture_note?: string;
};

type Trusted<T> = T extends UIProse
  ? T & { rendered: string }
  : T extends UIImage | UIMap | UIFrame
    ? T & LoadedMedia
    : T extends { children: unknown[] }
      ? Omit<T, "children"> & { children: MessageNode[] }
      : T;

export type MessageNode = Trusted<UIBlock["children"][number]>;
export type MessageDocument = Omit<UIBlock, "children"> & {
  children: MessageNode[];
};
export type MediaNode = Extract<
  MessageNode,
  { type: "image" | "map" | "iframe" }
>;
export type DataNode = Extract<
  MessageNode,
  { type: "chart" | "stats" | "timeline" }
>;

export type Renderers = {
  renderChart: (
    container: HTMLElement,
    config: ChartBlock,
  ) => void | (() => void);
  renderStats: (container: HTMLElement, config: StatsBlock) => void;
  renderTimeline: (container: HTMLElement, config: TimelineBlock) => void;
  onError: (error: unknown) => void;
};
