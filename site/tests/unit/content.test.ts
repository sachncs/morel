import { describe, expect, it } from "vitest";
import { SITE, VERIFICATION } from "../../src/lib/content";

describe("published site content", () => {
  it("keeps verification metadata concrete and current", () => {
    expect(VERIFICATION.tests).toBeGreaterThan(0);
    expect(VERIFICATION.coverage).toBeGreaterThanOrEqual(70);
    expect(VERIFICATION.lastVerified).toMatch(/^20\d\d-\d\d-\d\d$/);
  });

  it("uses canonical repository and documentation targets", () => {
    expect(SITE.repo).toBe("https://github.com/sachncs/morel");
    expect(SITE.docs).toBe("https://sachncs.github.io/morel/docs/");
    expect(SITE.url).toMatch(/sachncs\.github\.io\/morel\/$/);
  });
});
