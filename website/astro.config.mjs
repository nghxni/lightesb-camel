import { defineConfig } from "astro/config";
import sitemap from "@astrojs/sitemap";

export default defineConfig({
  site: "https://lightesb-camel.pages.dev",
  output: "static",
  build: {
    inlineStylesheets: "auto"
  },
  vite: {
    build: {
      assetsInlineLimit: 32768
    }
  },
  integrations: [
    sitemap({
      filter: (page) => !page.includes("/404")
    })
  ]
});
