import { describe, expect, it, jest, afterEach } from "@jest/globals";

import { fetchApi } from "../lib/api";

describe("fetchApi", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    jest.restoreAllMocks();
  });

  it("handles 204 No Content responses without parsing JSON", async () => {
    const json = jest.fn<() => Promise<unknown>>();
    const fetchMock = jest.fn<typeof fetch>().mockResolvedValueOnce({
      ok: true,
      status: 204,
      json,
    } as unknown as Response);
    globalThis.fetch = fetchMock;

    await expect(fetchApi("/assistants/assistant-id", { method: "DELETE" })).resolves.toBeUndefined();
    expect(json).not.toHaveBeenCalled();
  });
});
