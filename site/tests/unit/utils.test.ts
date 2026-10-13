import { describe, expect, it } from "vitest";
import { cn, formatNumber } from "../../src/lib/utils";

describe("site utilities", () => {
  it("merges conflicting Tailwind classes deterministically", () => {
    expect(cn("px-2 text-sm", false && "px-4", "px-6")).toBe("text-sm px-6");
  });

  it("formats verification numbers for the product surface", () => {
    expect(formatNumber(527)).toBe("527");
    expect(formatNumber(1000000)).toBe("1,000,000");
  });
});
