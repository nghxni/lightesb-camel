import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const scriptDirectory = path.dirname(fileURLToPath(import.meta.url));
const distDirectory = path.resolve(scriptDirectory, "../dist");
const siteUrl = "https://lightesb-camel.pages.dev";
const failures = [];
const titles = new Map();
const descriptions = new Map();
const canonicals = new Map();

const htmlFiles = [];
function collectHtml(directory) {
  for (const entry of fs.readdirSync(directory, { withFileTypes: true })) {
    const entryPath = path.join(directory, entry.name);
    if (entry.isDirectory()) collectHtml(entryPath);
    if (entry.isFile() && entry.name.endsWith(".html")) htmlFiles.push(entryPath);
  }
}

if (!fs.existsSync(distDirectory)) {
  failures.push("dist/ does not exist; run npm run build first");
} else {
  collectHtml(distDirectory);
}

const pageUrl = (filePath) => {
  const relative = path.relative(distDirectory, filePath).replaceAll(path.sep, "/");
  if (relative === "index.html") return "/";
  if (relative === "404.html") return "/404/";
  if (relative.endsWith("/index.html")) return `/${relative.slice(0, -"index.html".length)}`;
  return `/${relative}`;
};

const titleFrom = (html, filePath) => {
  const match = html.match(/<title>([^<]+)<\/title>/i);
  if (!match?.[1]?.trim()) failures.push(`${pageUrl(filePath)} is missing a non-empty title`);
  return match?.[1]?.trim() || "";
};

const requiredMeta = (html, name, attribute = "name") => {
  const pattern = new RegExp(`<meta\\s+${attribute}=["']${name}["']\\s+content=["']([^"']+)["']`, "i");
  return html.match(pattern)?.[1]?.trim() || "";
};

const canonicalFrom = (html) => html.match(/<link\s+rel=["']canonical["']\s+href=["']([^"']+)["']/i)?.[1]?.trim() || "";

const jsonLdValues = (html) => {
  const values = [];
  for (const match of html.matchAll(/<script[^>]+type=["']application\/ld\+json["'][^>]*>([\s\S]*?)<\/script>/gi)) {
    try {
      values.push(JSON.parse(match[1]));
    } catch {
      failures.push("invalid JSON-LD script");
    }
  }
  return values.flatMap((value) => value["@graph"] || [value]);
};

const htmlByUrl = new Map();
for (const filePath of htmlFiles) {
  const url = pageUrl(filePath);
  const html = fs.readFileSync(filePath, "utf8");
  htmlByUrl.set(url, filePath);
}

for (const filePath of htmlFiles) {
  const url = pageUrl(filePath);
  const html = fs.readFileSync(filePath, "utf8");
  if (path.basename(filePath) === "google19c02e3e4ae1669c.html") continue;

  const title = titleFrom(html, filePath);
  const description = requiredMeta(html, "description");
  const canonical = canonicalFrom(html);
  if (!description) failures.push(`${url} is missing a non-empty description`);
  if (!canonical.startsWith(siteUrl)) failures.push(`${url} has invalid canonical: ${canonical || "missing"}`);
  if (canonical !== new URL(url, siteUrl).toString()) failures.push(`${url} canonical does not match its generated URL`);
  if (title.length < 30 || title.length > 65) failures.push(`${url} title length ${title.length} is outside 30..65`);
  if (description.length < 110 || description.length > 180) failures.push(`${url} description length ${description.length} is outside 110..180`);
  titles.set(title, [...(titles.get(title) || []), url]);
  descriptions.set(description, [...(descriptions.get(description) || []), url]);
  canonicals.set(canonical, [...(canonicals.get(canonical) || []), url]);

  const h1Count = (html.match(/<h1\b/gi) || []).length;
  if (url !== "/404/" && h1Count !== 1) failures.push(`${url} has ${h1Count} h1 elements; expected exactly one`);

  for (const image of html.matchAll(/<img\b[^>]*>/gi)) {
    if (!/\balt=["'][^"']*["']/i.test(image[0])) failures.push(`${url} has an image without alt text`);
    if (!/\bwidth=["'][^"']+["']/i.test(image[0]) || !/\bheight=["'][^"']+["']/i.test(image[0])) {
      failures.push(`${url} has an image without explicit width and height`);
    }
  }

  const types = new Set(jsonLdValues(html).map((value) => value["@type"]));
  if (url === "/") {
    for (const type of ["Organization", "WebSite", "SoftwareApplication"]) {
      if (!types.has(type)) failures.push(`/ is missing JSON-LD type ${type}`);
    }
  }
  if (url.startsWith("/articles/") && url !== "/articles/") {
    for (const type of ["Article", "BreadcrumbList"]) {
      if (!types.has(type)) failures.push(`${url} is missing JSON-LD type ${type}`);
    }
    if (requiredMeta(html, "author") !== "nghxni") failures.push(`${url} is missing author nghxni`);
    const articleSchema = jsonLdValues(html).find((value) => value["@type"] === "Article");
    const visibleHeadline = html.match(/<h1\b[^>]*>([^<]+)<\/h1>/i)?.[1]?.trim();
    if (articleSchema?.headline !== visibleHeadline) failures.push(`${url} Article headline does not match visible h1`);
  }
  if (url === "/404/") {
    if (requiredMeta(html, "robots") !== "noindex") failures.push("/404/ must be noindex");
  }

  for (const match of html.matchAll(/<a\b[^>]*href=["']([^"'#]+)["']/gi)) {
    const href = match[1];
    if (!href.startsWith("/") || href.startsWith("//")) continue;
    const target = href.endsWith("/") ? href : `${href}/`;
    if (!htmlByUrl.has(target) && !htmlByUrl.has(href)) failures.push(`${url} links to missing page ${href}`);
  }

  if (!title) failures.push(`${url} has an empty title`);
}

for (const [kind, values] of [["title", titles], ["description", descriptions], ["canonical", canonicals]]) {
  for (const [value, urls] of values) {
    if (value && urls.length > 1) failures.push(`duplicate ${kind} on ${urls.join(", ")}`);
  }
}

const robotsPath = path.join(distDirectory, "robots.txt");
const robots = fs.existsSync(robotsPath) ? fs.readFileSync(robotsPath, "utf8") : "";
if (!robots.includes(`Sitemap: ${siteUrl}/sitemap-index.xml`)) failures.push("robots.txt does not declare the production sitemap index");

const sitemapIndexPath = path.join(distDirectory, "sitemap-index.xml");
const sitemapPath = path.join(distDirectory, "sitemap-0.xml");
if (!fs.existsSync(sitemapIndexPath) || !fs.existsSync(sitemapPath)) failures.push("generated sitemap index or sitemap-0.xml is missing");
if (fs.existsSync(sitemapPath) && fs.readFileSync(sitemapPath, "utf8").includes("/404")) failures.push("sitemap contains the 404 page");
if (fs.existsSync(sitemapPath)) {
  const sitemapUrlCount = (fs.readFileSync(sitemapPath, "utf8").match(/<url>/g) || []).length;
  const indexablePageCount = htmlFiles.filter((filePath) => !["404.html", "google19c02e3e4ae1669c.html"].includes(path.basename(filePath))).length;
  if (sitemapUrlCount !== indexablePageCount) {
    failures.push(`sitemap contains ${sitemapUrlCount} URLs; expected ${indexablePageCount}`);
  }
}

if (failures.length > 0) {
  console.error("SEO checks failed:");
  for (const failure of failures) console.error(`- ${failure}`);
  process.exit(1);
}

console.log(`SEO checks passed for ${htmlFiles.length} HTML pages.`);
