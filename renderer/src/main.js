import { BarChart, LineChart, PieChart } from "echarts/charts";
import { AriaComponent, GridComponent, LegendComponent } from "echarts/components";
import { init, use } from "echarts/core";
import { SVGRenderer } from "echarts/renderers";
import renderMathInElement from "katex/contrib/auto-render";
import mermaid from "mermaid";
import Prism from "prismjs";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-css";
import "prismjs/components/prism-java";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-json";
import "prismjs/components/prism-python";
import "prismjs/components/prism-sql";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-yaml";
import "./vendor.css";

use([BarChart, LineChart, PieChart, GridComponent, LegendComponent, AriaComponent, SVGRenderer]);

const CHART_COLORS = ["#2563eb", "#0f9f6e", "#f59e0b", "#ef4444", "#8b5cf6", "#0891b2", "#db2777", "#64748b"];
const renderState = { state: "pending", errors: [] };
window.__FRONTIER_RENDER__ = renderState;

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function recordError(kind, error) {
  const message = error instanceof Error ? error.message : String(error);
  renderState.errors.push({ kind, message });
  console.warn(`${kind} rendering failed:`, error);
}

function addTitle(container, config) {
  if (!config.title) return;
  const title = element("div", "md-rich-title", config.title);
  if (config.unit) title.append(element("span", "md-rich-unit", `单位：${config.unit}`));
  container.append(title);
}

function axisLabel(labels) {
  const longest = Math.max(0, ...labels.map((label) => String(label).length));
  return {
    interval: labels.length > 24 ? Math.ceil(labels.length / 12) - 1 : 0,
    rotate: labels.length > 12 || longest > 8 ? 30 : 0,
    hideOverlap: true,
  };
}

function chartOption(config) {
  const common = {
    animation: false,
    aria: {
      enabled: true,
      label: { description: config.title || "数据图表" },
    },
    color: CHART_COLORS,
    textStyle: { fontFamily: "Noto Sans CJK SC, Microsoft YaHei, sans-serif" },
    toolbox: { show: false },
    tooltip: { show: false },
  };

  if (config.type === "pie") {
    return {
      ...common,
      legend: config.show_legend ? { type: "plain", bottom: 0 } : { show: false },
      series: [{
        type: "pie",
        radius: ["34%", "68%"],
        center: ["50%", "46%"],
        data: config.data,
        label: { formatter: "{b}: {d}%", overflow: "truncate" },
        avoidLabelOverlap: true,
        silent: true,
      }],
    };
  }

  return {
    ...common,
    grid: {
      left: 64,
      right: 28,
      top: 28,
      bottom: config.show_legend ? 82 : 58,
      containLabel: true,
    },
    legend: config.show_legend ? { bottom: 0 } : { show: false },
    xAxis: {
      type: "category",
      data: config.labels,
      axisLabel: axisLabel(config.labels),
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: "value",
      name: config.unit || "",
      scale: config.type === "line",
      splitLine: { lineStyle: { color: "#e4eaf2" } },
    },
    series: config.series.map((series) => ({
      name: series.name,
      type: config.type,
      data: series.values,
      barMaxWidth: config.type === "bar" ? 48 : undefined,
      showSymbol: config.type === "line" && config.labels.length <= 30,
      symbolSize: 7,
      smooth: false,
      silent: true,
    })),
  };
}

function renderChartFallback(container, config) {
  const table = element("table", "md-chart-fallback");
  const head = element("thead");
  const headRow = element("tr");
  const body = element("tbody");

  if (config.type === "pie") {
    headRow.append(element("th", null, "项目"), element("th", null, `数值${config.unit ? `（${config.unit}）` : ""}`));
    config.data.forEach((item) => {
      const row = element("tr");
      row.append(element("td", null, item.name), element("td", null, item.value));
      body.append(row);
    });
  } else {
    headRow.append(element("th", null, "项目"), ...config.series.map((series) => element("th", null, series.name)));
    config.labels.forEach((label, index) => {
      const row = element("tr");
      row.append(element("td", null, label), ...config.series.map((series) => element("td", null, series.values[index])));
      body.append(row);
    });
  }

  head.append(headRow);
  table.append(head, body);
  container.append(table);
}

function renderChart(container, config) {
  addTitle(container, config);
  const chartRoot = element("div", "md-chart-canvas");
  chartRoot.setAttribute("role", "img");
  chartRoot.setAttribute("aria-label", config.title || "数据图表");
  container.append(chartRoot);

  try {
    const chart = init(chartRoot, null, { renderer: "svg" });
    chart.setOption(chartOption(config), { notMerge: true, lazyUpdate: false });
    chart.resize();
    container.dataset.chartRendered = "true";
  } catch (error) {
    chartRoot.remove();
    renderChartFallback(container, config);
    container.dataset.chartRendered = "fallback";
    recordError("chart", error);
  }
}

function renderStats(container, config) {
  addTitle(container, config);
  const grid = element("div", "md-stats-grid");
  grid.style.setProperty("--md-stats-columns", String(config.columns));
  config.items.forEach((item) => {
    const card = element("section", `md-stat-card md-status-${item.status}`);
    card.append(element("div", "md-stat-label", item.label));
    const value = element("div", "md-stat-value", item.value);
    if (item.unit) value.append(element("span", "md-stat-unit", item.unit));
    card.append(value);
    if (item.detail) card.append(element("div", "md-stat-detail", item.detail));
    grid.append(card);
  });
  container.append(grid);
}

function renderTimeline(container, config) {
  addTitle(container, config);
  const timeline = element("div", "md-timeline");
  config.items.forEach((item) => {
    const row = element("section", `md-timeline-item md-status-${item.status}`);
    row.append(element("span", "md-timeline-marker"));
    const body = element("div", "md-timeline-body");
    body.append(element("div", "md-timeline-time", item.time));
    body.append(element("div", "md-timeline-title", item.title));
    if (item.content) body.append(element("div", "md-timeline-content", item.content));
    row.append(body);
    timeline.append(row);
  });
  container.append(timeline);
}

function renderRichBlocks() {
  document.querySelectorAll(".md-rich-block").forEach((container) => {
    try {
      const kind = container.dataset.richKind;
      const config = JSON.parse(container.dataset.richConfig);
      if (kind === "chart") renderChart(container, config);
      else if (kind === "stats") renderStats(container, config);
      else if (kind === "timeline") renderTimeline(container, config);
      else throw new Error(`Unsupported rich block: ${kind}`);
      container.dataset.richRendered = "true";
    } catch (error) {
      container.replaceChildren(element("div", "md-rich-error", "增强内容渲染失败，已保留其余内容。"));
      container.dataset.richRendered = "fallback";
      recordError("rich", error);
    }
  });
}

function renderMath() {
  renderMathInElement(document.body, {
    delimiters: [
      { left: "$$", right: "$$", display: true },
      { left: "$", right: "$", display: false },
      { left: "\\(", right: "\\)", display: false },
      { left: "\\[", right: "\\]", display: true },
    ],
    throwOnError: false,
    strict: false,
    trust: false,
    ignoredClasses: ["mermaid", "md-rich-block"],
    macros: {
      "\\RR": "\\mathbb{R}",
      "\\NN": "\\mathbb{N}",
      "\\ZZ": "\\mathbb{Z}",
      "\\QQ": "\\mathbb{Q}",
      "\\CC": "\\mathbb{C}",
    },
  });
}

async function renderMermaid() {
  mermaid.initialize({
    startOnLoad: false,
    securityLevel: "strict",
    htmlLabels: false,
    theme: "default",
  });

  for (const node of document.querySelectorAll(".mermaid")) {
    const source = node.textContent;
    try {
      await mermaid.run({ nodes: [node], suppressErrors: false });
      node.dataset.mermaidRendered = "true";
    } catch (error) {
      const fallback = element("pre", "md-mermaid-fallback");
      fallback.append(element("code", "language-mermaid", source));
      node.replaceWith(fallback);
      recordError("mermaid", error);
    }
  }
}

function nextFrame() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

async function renderDocument() {
  try {
    if (document.fonts?.ready) await document.fonts.ready;
    await Promise.allSettled([
      ["math", renderMath],
      ["rich", renderRichBlocks],
      ["mermaid", renderMermaid],
      ["highlight", () => Prism.highlightAll()],
    ].map(async ([kind, render]) => {
      try {
        await render();
      } catch (error) {
        recordError(kind, error);
      }
    }));
    await nextFrame();
    await nextFrame();
  } finally {
    renderState.state = "ready";
    document.documentElement.dataset.frontierReady = "true";
  }
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => void renderDocument(), { once: true });
} else {
  void renderDocument();
}
