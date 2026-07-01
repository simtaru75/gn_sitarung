import { readFile } from "node:fs/promises";
import path from "node:path";

export type StaticSection = "rtrw" | "lainnya";

type StaticPageConfig = {
  slug: string;
  fileName: string;
  label: string;
};

const STATIC_PAGES: Record<StaticSection, StaticPageConfig[]> = {
  rtrw: [
    { slug: "index", fileName: "index.html", label: "Tujuan, Kebijakan dan Strategi" },
    { slug: "tujuan", fileName: "tujuan.html", label: "Tujuan, Kebijakan dan Strategi" },
    { slug: "struktur", fileName: "struktur.html", label: "Rencana Struktur Ruang" },
    { slug: "pola", fileName: "pola.html", label: "Rencana Pola Ruang" },
    { slug: "strategis", fileName: "strategis.html", label: "Rencana Kawasan Strategis" },
    { slug: "pemanfaatan", fileName: "pemanfaatan.html", label: "Arahan Pemanfaatan Ruang" },
    { slug: "pengendalian", fileName: "pengendalian.html", label: "Arahan Pengendalian Pemanfaatan Ruang" },
    { slug: "jukniskkpr", fileName: "jukniskkpr.html", label: "Petunjuk Teknis KKPR" },
  ],
  lainnya: [
    { slug: "index", fileName: "index.html", label: "About Us" },
    { slug: "aboutus", fileName: "aboutus.html", label: "About Us" },
    { slug: "faq", fileName: "faq.html", label: "FAQ" },
    { slug: "pengaduan", fileName: "pengaduan.html", label: "Pengaduan" },
  ],
};

const STATIC_SOURCE_DIRS: Record<StaticSection, string> = {
  rtrw: "rtrw",
  lainnya: "informasi-publik",
};

const APP_STATIC_ROOT = path.resolve(process.cwd(), "src", "legacy-static");

export type StaticPageData = {
  section: StaticSection;
  slug: string;
  title: string;
  heading: string;
  subheading: string;
  summary: string;
  html: string;
  siblings: Array<{ slug: string; label: string; href: string }>;
};

export function getStaticPageEntries(section: StaticSection) {
  return STATIC_PAGES[section];
}

export async function getStaticPage(section: StaticSection, slug: string): Promise<StaticPageData | null> {
  const config = STATIC_PAGES[section].find((item) => item.slug === slug);
  if (!config) return null;

  const filePath = path.join(APP_STATIC_ROOT, STATIC_SOURCE_DIRS[section], config.fileName);
  const html = await readFile(filePath, "utf8");
  const content = extractPageContent(html);

  return {
    section,
    slug,
    title: content.title || config.label,
    heading: content.heading || config.label,
    subheading: content.subheading,
    summary: content.summary,
    html: rewriteStaticHtml(content.html, section),
    siblings: STATIC_PAGES[section]
      .filter((item) => item.slug !== "index")
      .map((item) => ({ slug: item.slug, label: item.label, href: section === "lainnya" && item.slug === "pengaduan" ? "/pengaduan" : `/${section}/${item.slug}` })),
  };
}

function extractPageContent(source: string) {
  const title = decodeHtml(stripTags(source.match(/<title>([\s\S]*?)<\/title>/i)?.[1] ?? ""));
  const firstCustomIndex = source.search(/<div class=" bd-customhtml-\d+ bd-tagstyles">/i);
  const headerSlice = firstCustomIndex > 0 ? source.slice(0, firstCustomIndex) : source;
  const h1Texts = Array.from(headerSlice.matchAll(/<h1[^>]*>([\s\S]*?)<\/h1>/gi))
    .map((match) => cleanText(match[1]))
    .filter(Boolean);
  const pTexts = Array.from(headerSlice.matchAll(/<p[^>]*>([\s\S]*?)<\/p>/gi))
    .map((match) => cleanText(match[1]))
    .filter(Boolean);

  const mainContent = extractSectionContent(source, "content");
  const blocks = (mainContent ? [mainContent] : extractCustomHtmlBlocks(source))
    .map(stripEmbeddedMaps)
    .filter(Boolean);

  const html = blocks.join("\n\n");
  const summary = cleanText(blocks[0]?.match(/<p[^>]*>([\s\S]*?)<\/p>/i)?.[1] ?? "");

  return {
    title,
    heading: h1Texts.at(-2) ?? title,
    subheading: h1Texts.at(-1) ?? title,
    summary,
    html,
  };
}

function rewriteStaticHtml(html: string, section: StaticSection) {
  return html
    .replace(/src=["']assets\//gi, 'src="/adm/PUBLIK/assets/')
    .replace(/href=["']\.\.\/rtrw\/index\.html["']/gi, 'href="/rtrw"')
    .replace(/href=["']\.\.\/rtrw\/([a-z0-9_-]+)\.html["']/gi, (_full, slug) => `href="/rtrw/${slug.toLowerCase()}"`)
    .replace(/href=["']\.\.\/lainnya\/index\.html["']/gi, 'href="/lainnya"')
    .replace(/href=["']\.\.\/lainnya\/pengaduan\.html["']/gi, 'href="/pengaduan"')
    .replace(/href=["']\.\.\/lainnya\/([a-z0-9_-]+)\.html["']/gi, (_full, slug) => `href="/lainnya/${slug.toLowerCase()}"`)
    .replace(/href=["']pengaduan\.html["']/gi, 'href="/pengaduan"')
    .replace(/href=["'](aboutus|faq|pengaduan)\.html["']/gi, (_full, slug) => `href="/lainnya/${slug.toLowerCase()}"`)
    .replace(/href=["'](tujuan|struktur|pola|strategis|pemanfaatan|pengendalian|jukniskkpr)\.html["']/gi, (_full, slug) => `href="/rtrw/${slug.toLowerCase()}"`)
    .replace(/href=["']index\.html["']/gi, `href="/${section}"`);
}

function stripEmbeddedMaps(html: string) {
  return html
    .replace(/<iframe[^>]+google\.com\/maps\/embed[^>]*><\/iframe>/gi, "")
    .trim();
}

function cleanText(value: string) {
  return decodeHtml(stripTags(value))
    .replace(/\s+/g, " ")
    .trim();
}

function stripTags(value: string) {
  return value
    .replace(/<br\s*\/?>/gi, " ")
    .replace(/<\/p>/gi, " ")
    .replace(/<[^>]+>/g, " ");
}

function decodeHtml(value: string) {
  return value
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">");
}

function extractCustomHtmlBlocks(source: string) {
  const blocks: string[] = [];
  const customMarker = '<div class=" bd-customhtml-';
  const contentMarker = '<div class="bd-container-inner bd-content-element">';
  let searchFrom = 0;

  while (true) {
    const customIndex = source.indexOf(customMarker, searchFrom);
    if (customIndex === -1) break;
    const contentIndex = source.indexOf(contentMarker, customIndex);
    if (contentIndex === -1) break;

    const contentStart = contentIndex + contentMarker.length;
    const contentEnd = findMatchingDivEnd(source, contentStart);
    if (contentEnd === -1) break;

    blocks.push(source.slice(contentStart, contentEnd).trim());
    searchFrom = contentEnd;
  }

  return blocks;
}

function findMatchingDivEnd(source: string, fromIndex: number) {
  let depth = 1;
  let cursor = fromIndex;

  while (cursor < source.length) {
    const nextOpen = source.indexOf("<div", cursor);
    const nextClose = source.indexOf("</div>", cursor);
    if (nextClose === -1) return -1;

    if (nextOpen !== -1 && nextOpen < nextClose) {
      depth += 1;
      cursor = nextOpen + 4;
      continue;
    }

    depth -= 1;
    if (depth === 0) return nextClose;
    cursor = nextClose + 6;
  }

  return -1;
}

function extractSectionContent(source: string, sectionId: string) {
  const sectionStart = source.search(new RegExp(`<section[^>]*id=["']${sectionId}["'][^>]*>`, "i"));
  if (sectionStart === -1) return "";

  const openEnd = source.indexOf(">", sectionStart);
  if (openEnd === -1) return "";

  const sectionEnd = findMatchingTagEnd(source, openEnd + 1, "section");
  if (sectionEnd === -1) return "";

  return source.slice(openEnd + 1, sectionEnd).trim();
}

function findMatchingTagEnd(source: string, fromIndex: number, tagName: string) {
  const openTag = `<${tagName}`;
  const closeTag = `</${tagName}>`;
  let depth = 1;
  let cursor = fromIndex;

  while (cursor < source.length) {
    const nextOpen = source.indexOf(openTag, cursor);
    const nextClose = source.indexOf(closeTag, cursor);
    if (nextClose === -1) return -1;

    if (nextOpen !== -1 && nextOpen < nextClose) {
      depth += 1;
      cursor = nextOpen + openTag.length;
      continue;
    }

    depth -= 1;
    if (depth === 0) return nextClose;
    cursor = nextClose + closeTag.length;
  }

  return -1;
}