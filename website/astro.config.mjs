import { defineConfig } from "astro/config";

export default defineConfig({
  output: "static",
  build: {
    inlineStylesheets: "auto"
  },
  vite: {
    build: {
      assetsInlineLimit: 32768
    }
  }
});
