// Screenshot-native components inspired by shadcn/ui's semantic composition.
// Every field has been validated by utils/markdown_rich.py before reaching here.
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined && text !== null) node.textContent = String(text);
  return node;
}

function header(config, titleClass, titleTag = "h3") {
  if (!config.title && !config.description && !config.eyebrow) return null;
  const node = element("header", "md-ui-header");
  if (config.eyebrow) node.append(element("div", "md-ui-eyebrow", config.eyebrow));
  if (config.title) node.append(element(titleTag, titleClass, config.title));
  if (config.description) node.append(element("p", "md-ui-description", config.description));
  return node;
}

function statusIcon(status) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", "0 0 24 24");
  svg.setAttribute("fill", "none");
  svg.setAttribute("stroke", "currentColor");
  svg.setAttribute("stroke-width", "1.6");
  svg.setAttribute("stroke-linecap", "round");
  svg.setAttribute("stroke-linejoin", "round");
  svg.setAttribute("aria-hidden", "true");
  const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
  path.setAttribute("d", status === "success"
    ? "M21 12a9 9 0 1 1-4-7.5M8 11l4 4 9-10"
    : status === "warning" || status === "danger"
      ? "M12 3 2 21h20L12 3Zm0 6v5m0 3v.1"
      : "M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0ZM12 11v6m0-10v.1");
  svg.append(path);
  return svg;
}

function itemContent(item) {
  const body = element("div", "md-ui-item-content");
  const top = element("div", "md-ui-item-header");
  top.append(element("strong", "md-ui-item-title", item.title));
  if (item.meta) top.append(element("span", "md-ui-item-meta", item.meta));
  body.append(top);
  if (item.description) body.append(element("p", "md-ui-description", item.description));
  return body;
}

function component(config, pendingCharts, renderers) {
  const type = config.type;
  let node;
  const children = () => config.children.map((child) => component(child, pendingCharts, renderers));
  if (["row", "column", "grid"].includes(type)) {
    node = element("div", `md-ui-${type} md-gap-${config.gap || "md"}`);
    if (type === "grid") node.style.setProperty("--md-ui-columns", String(config.columns));
    node.append(...children());
  } else if (type === "card" || type === "section") {
    node = element(type === "section" ? "section" : "article",
      type === "section" ? "md-ui-section" : `md-ui-card md-card-${config.variant || "outline"}`);
    const top = header(config, "md-ui-card-title");
    if (top) node.append(top);
    const body = element("div", "md-ui-content");
    body.append(...children());
    node.append(body);
    if (config.footer) node.append(element("footer", "md-ui-card-footer", config.footer));
  } else if (type === "heading" || type === "text") {
    node = element(type === "heading" ? "h3" : "p",
      type === "heading" ? "md-ui-heading" : `md-ui-text md-text-${config.variant || "body"}`, config.text);
  } else if (type === "prose") {
    node = element("div", "md-ui-prose");
    // This HTML comes exclusively from the server's HTML-disabled Markdown parser.
    node.innerHTML = config.rendered;
    renderers.renderMath(node, true);
  } else if (type === "badge") {
    node = element("span", `md-ui-badge md-badge-${config.variant || "secondary"} md-status-${config.status}`, config.text);
  } else if (type === "callout" || type === "alert") {
    node = element("aside", `md-ui-alert md-status-${config.status}`);
    node.setAttribute("role", "note");
    node.append(statusIcon(config.status));
    const body = element("div", "md-ui-alert-body");
    if (config.title) body.append(element("strong", "md-ui-alert-title", config.title));
    body.append(element("p", "md-ui-text", config.text));
    node.append(body);
  } else if (type === "link") {
    node = element("div", "md-ui-link");
    node.append(element("strong", null, config.label), element("div", "md-ui-url", config.url));
  } else if (type === "sources") {
    node = element("ol", "md-ui-sources");
    config.items.forEach((source) => {
      const item = element("li");
      item.append(element("strong", "md-ui-source-label", source.label));
      if (source.description) item.append(element("p", "md-ui-description", source.description));
      item.append(element("div", "md-ui-url", source.url));
      node.append(item);
    });
  } else if (type === "code") {
    node = element("pre", "md-ui-code");
    node.append(element("code", null, config.text));
  } else if (type === "mermaid") {
    node = element("div", "mermaid", config.text);
  } else if (type === "steps" || type === "list") {
    node = element(type === "steps" ? "ol" : "ul",
      type === "steps" ? "md-ui-steps" : `md-ui-list md-list-${config.variant || "plain"}`);
    config.items.forEach((item, index) => {
      const row = element("li", "md-ui-item");
      if (type === "steps") row.append(element("span", "md-ui-step-number", index + 1));
      row.append(itemContent(typeof item === "string" ? { title: item } : item));
      node.append(row);
    });
  } else if (type === "facts") {
    node = element("dl", "md-ui-facts");
    node.style.setProperty("--md-fact-columns", String(config.columns));
    config.items.forEach((item) => {
      const row = element("div", "md-ui-fact");
      row.append(element("dt", null, item.label), element("dd", null, item.value));
      node.append(row);
    });
  } else if (type === "separator") {
    node = element("div", "md-ui-separator", config.label);
    node.setAttribute("role", "separator");
  } else if (type === "quote") {
    node = element("blockquote", "md-ui-quote");
    node.append(element("p", null, config.text));
    if (config.attribution) node.append(element("cite", null, config.attribution));
  } else if (type === "progress") {
    node = element("div", "md-ui-progress");
    const top = element("div", "md-ui-item-header");
    top.append(element("strong", null, config.label), element("span", "md-ui-item-meta", `${config.value}%`));
    const track = element("div", "md-ui-progress-track");
    track.setAttribute("role", "progressbar");
    track.setAttribute("aria-label", config.label);
    track.setAttribute("aria-valuemin", "0");
    track.setAttribute("aria-valuemax", "100");
    track.setAttribute("aria-valuenow", String(config.value));
    const fill = element("div", "md-ui-progress-fill");
    fill.style.width = `${config.value}%`;
    track.append(fill);
    node.append(top, track);
    if (config.detail) node.append(element("p", "md-ui-description", config.detail));
  } else if (type === "table") {
    node = element("table", "md-ui-table");
    if (config.caption) node.append(element("caption", null, config.caption));
    if (config.column_widths) {
      node.classList.add("md-table-weighted");
      const group = element("colgroup");
      const total = config.column_widths.reduce((sum, width) => sum + width, 0);
      config.column_widths.forEach((weight) => {
        const col = element("col");
        col.style.width = `${100 * weight / total}%`;
        group.append(col);
      });
      node.append(group);
    }
    const head = element("thead");
    const row = element("tr");
    row.append(...config.columns.map((label) => element("th", null, label)));
    head.append(row);
    const body = element("tbody");
    config.rows.forEach((values) => {
      const item = element("tr");
      item.append(...values.map((value) => element("td", null, value)));
      body.append(item);
    });
    node.append(head, body);
  } else if (["chart", "stats", "timeline"].includes(type)) {
    node = element("div", "md-ui-data");
    if (type === "chart") pendingCharts.push(() => renderers.renderChart(node, config.config));
    else if (type === "stats") renderers.renderStats(node, config.config);
    else renderers.renderTimeline(node, config.config);
  } else {
    throw new Error(`Unsupported UI component: ${type}`);
  }
  return node;
}

export function renderMessageUI(container, config, renderers) {
  container.classList.add("md-ui-document");
  const top = header(config, "md-ui-title", "h2");
  if (top) container.append(top);
  const pendingCharts = [];
  container.append(...config.children.map((child) => component(child, pendingCharts, renderers)));
  // ECharts must see attached nodes with real layout dimensions.
  pendingCharts.forEach((render) => render());
}
