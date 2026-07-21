import { resolve } from "node:path";
import { defineConfig } from "vite";

export default defineConfig({
  define: {
    "process.env.NODE_ENV": JSON.stringify("production"),
  },
  build: {
    assetsInlineLimit: Number.POSITIVE_INFINITY,
    cssCodeSplit: false,
    emptyOutDir: true,
    outDir: resolve(import.meta.dirname, "../templates/markdown_assets"),
    lib: {
      entry: resolve(import.meta.dirname, "src/main.js"),
      name: "FrontierMarkdownRenderer",
      formats: ["iife"],
      fileName: () => "markdown-render.js",
      cssFileName: "markdown-render",
    },
    rollupOptions: {
      output: {
        assetFileNames: (asset) => asset.name === "style.css" ? "markdown-render.css" : "[name][extname]",
      },
    },
  },
});
