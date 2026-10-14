import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

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
    "https://github.com/sachncs/morel/tree/master/docs",
  );
});

test("desktop page has no axe WCAG A/AA violations", async ({ page }) => {
  await page.goto("./");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  expect(results.violations).toEqual([]);
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
      maxDiffPixelRatio: 0.02,
    });
  });

  test("mobile composition and navigation affordance stay stable", async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await page.emulateMedia({ reducedMotion: "reduce" });
    await page.goto("./");
    await expect(page).toHaveScreenshot("mobile-home.png", {
      animations: "disabled",
      caret: "hide",
      maxDiffPixelRatio: 0.02,
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
