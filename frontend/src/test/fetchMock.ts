import { vi } from "vitest";

export interface MockResult {
  status?: number;
  body: unknown;
}

export type Router = (url: string, init?: RequestInit) => MockResult;

/** Install a fetch mock that routes requests by URL to canned JSON responses. */
export function mockFetch(router: Router): void {
  global.fetch = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const { status = 200, body } = router(url, init);
    return new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { "Content-Type": "application/json" },
    });
  }) as unknown as typeof fetch;
}
