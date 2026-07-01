import { describe, expect, it } from "vitest";
import { isLoginPath } from "./isLoginPath";

describe("isLoginPath", () => {
  it("returns true only for /login", () => {
    expect(isLoginPath("/login")).toBe(true);
    expect(isLoginPath("/")).toBe(false);
    expect(isLoginPath("/projects")).toBe(false);
    expect(isLoginPath("/login/extra")).toBe(false);
  });
});
