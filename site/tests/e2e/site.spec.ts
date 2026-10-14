import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

// Hosted Chromium can differ from the checked-in Linux baseline at the raster
// level (especially across CPU/renderer images). Keep hosted visual tolerance
// wider, while semantic brand checks below still reject palette regressions.
const visualDiffPixelRatio =
  process.env.CI || process.env.BASE_URL?.includes("/morel/") ? 0.15 : 0.02;

test.describe("morel site mobile navigation", () => {
  test.use({ viewport: { width: 390, height: 844 } });

  test.beforeEach(async ({ page }) => {
    await page.goto("./");
  });

  test("opens, traps focus, closes with Escape, and restores focus", async ({ page }) => {
    await page.getByRole("button", { name: "Open menu" }).click();

    const dialog = page.getByRole("dialog", { name: "Site navigation" });
    await expect(dialog).toBeVisible();
    await expect(page.getByRole("button", { name: "Close menu" })).toBeFocused();

    const lastLink = dialog.getByRole("link", { name: "Get started" });
    await lastLink.focus();
    await page.keyboard.press("Tab");
    await expect(
      dialog.getByRole("button", { name: /Switch to .* mode|Toggle theme/ }),
    ).toBeFocused();

    await page.keyboard.press("Escape");
    await expect(dialog).toBeHidden();
    await expect(page.getByRole("button", { name: "Open menu" })).toBeFocused();
  });

  test("anchor navigation closes the sheet and reaches the section", async ({ page }) => {
    await page.getByRole("button", { name: "Open menu" }).click();
    await page
      .getByRole("dialog", { name: "Site navigation" })
      .getByRole("link", { name: "Features" })
      .click();

    await expect(page.getByRole("dialog", { name: "Site navigation" })).toBeHidden();
    await expect(page.locator("#features")).toBeInViewport();
  });
});

test.describe("morel site interaction contracts", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("./");
  });

  test("theme choice persists across reloads", async ({ page }) => {
    const mobileMenu = page.getByRole("button", { name: "Open menu" });
    if (await mobileMenu.isVisible()) await mobileMenu.click();

    const toggle = page.locator(
      'button[aria-label="Toggle theme"], button[aria-label="Switch to light mode"]',
    ).first();
    await toggle.click();
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    await expect(page.getByRole("button", { name: "Switch to dark mode" }).first()).toBeVisible();

    await page.reload();
    if (await mobileMenu.isVisible()) await mobileMenu.click();
    await expect(page.locator("html")).not.toHaveClass(/dark/);
    await expect(page.getByRole("button", { name: "Switch to dark mode" }).first()).toBeVisible();
  });

  test("code copy action gives visible confirmation", async ({ page, context }) => {
    await context.grantPermissions(["clipboard-read", "clipboard-write"]);
    await page.getByRole("button", { name: "Copy code" }).click();
    await expect(page.getByRole("button", { name: "Copy code" })).toContainText("Copied");
  });

  test("reduced-motion preference disables smooth scrolling", async ({ page }) => {
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.reload();
    await expect(page.locator("html")).toHaveCSS("scroll-behavior", "auto");
  });
});

test("primary links expose the canonical repository and docs targets", async ({ page }) => {
  await page.goto("./");
  await expect(page.getByRole("link", { name: "View on GitHub" }).first()).toHaveAttribute(
    "href",
    "https://github.com/sachncs/morel",
  );
  await expect(page.getByRole("link", { name: "Docs", exact: true }).first()).toHaveAttribute(
    "href",
    "https://sachncs.github.io/morel/docs/",
  );
});

test("Astro docs render as task-oriented pages inside the site build", async ({ page }) => {
  await page.goto("/morel/docs/");
  await expect(page).toHaveTitle("Documentation · morel");
  await expect(page.getByRole("heading", { name: "Documentation", level: 1 })).toBeVisible();
  await expect(page.locator(".morel-hero")).toHaveCount(0);
  await expect(page.getByRole("link", { name: "License" })).toHaveAttribute(
    "href",
    "/morel/docs/project/license/",
  );

  const hrefs = await page.locator("a[href]").evaluateAll((links) =>
    links.map((link) => link.getAttribute("href")).filter((href): href is string => Boolean(href)),
  );
  expect(hrefs.some((href) => href.endsWith(".md"))).toBe(false);
});

test("every generated docs route renders in the shared shell", async ({ page }) => {
  await page.goto("/morel/docs/");
  const routes = await page.locator('a[href^="/morel/docs/"]').evaluateAll((links) =>
    [...new Set(links.map((link) => link.getAttribute("href")).filter((href): href is string => Boolean(href)))],
  );
  expect(routes.length).toBeGreaterThan(30);
  for (const route of routes) {
    const response = await page.goto(route);
    expect(response?.status(), route).toBe(200);
    await expect(page.locator(".docs-header")).toBeVisible();
    await expect(page.locator("article h1")).toBeVisible();
  }
  await page.goto("/morel/docs/concepts/architecture/");
  await expect(page.locator(".docs-architecture-diagram")).toBeVisible();
  await expect(page.locator("article pre")).toHaveCount(0);
  await page.goto("/morel/docs/concepts/method/");
  await expect(page.getByText("plain English", { exact: false }).first()).toBeVisible();
  const removedReview = await page.goto("/morel/docs/reference/site-ux-review/");
  expect(removedReview?.status()).toBe(404);
});

test("hero pipeline stages support pointer and keyboard interaction", async ({ page }) => {
  await page.goto("./");
  const completion = page.getByRole("button", { name: "Highlight completion stage" });
  await completion.focus();
  await expect(completion).toHaveAttribute("tabindex", "0");
  await completion.press("Enter");
  await expect(completion).toHaveAttribute("opacity", "1");
});

test("desktop page has no axe WCAG A/AA violations", async ({ page }) => {
  await page.goto("./");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations).toEqual([]);
});

test("deployed brand contract keeps the teal graph identity", async ({ page }) => {
  await page.goto("./");
  const gradient = await page.locator("h1 .gradient-text").evaluate((element) =>
    getComputedStyle(element).backgroundImage,
  );
  expect(gradient).toContain("rgb(12, 143, 125)");
  await expect(page.locator('svg[aria-hidden="true"]').first()).toBeVisible();
});

test.describe("visual contracts", () => {
  test("desktop composition and branding stay stable", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 1000 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("./");
    await expect(page).toHaveScreenshot("desktop-home.png", {
      animations: "disabled",
      caret: "hide",
      // Keep visual regressions strict enough to catch palette and hierarchy
      // changes; platform-specific baselines handle renderer differences.
      maxDiffPixelRatio: visualDiffPixelRatio,
    });
  });

  test("mobile composition and navigation affordance stay stable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("./");
    await expect(page).toHaveScreenshot("mobile-home.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: visualDiffPixelRatio,
    });
  });
});

for (const viewport of [
  { width: 360, height: 800 },
  { width: 768, height: 900 },
  { width: 1024, height: 900 },
  { width: 1440, height: 1000 },
]) {
  test(`responsive layout stays usable at ${viewport.width}px`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("./");

    await expect(page.locator("h1")).toBeVisible();
    await expect(page.getByRole("link", { name: "View on GitHub" }).first()).toBeVisible();
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    expect(overflow, `horizontal overflow at ${viewport.width}px`).toBeLessThanOrEqual(1);

    const menu = page.getByRole("button", { name: "Open menu" });
    if (viewport.width < 768) {
      await expect(menu).toBeVisible();
      await expect(page.locator("header nav").first()).toBeHidden();
    } else {
      await expect(menu).toBeHidden();
      await expect(page.locator("header nav").first()).toBeVisible();
    }
  });
}

test("all rendered links resolve or target an existing local section", async ({ page, request }) => {
  await page.goto("./");
  const hrefs = await page.locator("a[href]").evaluateAll((links) =>
    [...new Set(links.map((link) => link.getAttribute("href")))].filter(
      (href): href is string => Boolean(href),
    ),
  );

  for (const href of hrefs) {
    if (href.startsWith("#")) {
      await expect(page.locator(href)).toHaveCount(1);
      continue;
    }
    if (!href.startsWith("http")) continue;

    const url = new URL(href);
    url.hash = "";
    // The Pages docs route is published by the deployment job after this
    // pre-deploy product-site suite completes; the deploy job probes it live.
    if (url.hostname === "sachncs.github.io" && url.pathname.startsWith("/morel/docs")) {
      continue;
    }
    const response = await request.get(url.toString(), {
      failOnStatusCode: false,
      timeout: 10_000,
    });
    // GitHub may return rate-limit or transient edge errors to unauthenticated
    // CI probes; local 4xx errors still fail hard so broken links are caught.
    if (url.hostname === "github.com" && (response.status() === 429 || response.status() >= 500)) {
      continue;
    }
    expect(response.status(), `${url} returned ${response.status()}`).toBeLessThan(400);
  }
});
