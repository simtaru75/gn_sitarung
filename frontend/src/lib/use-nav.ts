"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useCallback } from "react";

/** Hook untuk navigasi filter: reset page, mutate params, push. */
export function useNav(basePath: string) {
  const router = useRouter();
  const sp = useSearchParams();
  return useCallback(
    (mutate: (p: URLSearchParams) => void) => {
      const p = new URLSearchParams(sp.toString());
      p.delete("page");
      mutate(p);
      const qs = p.toString();
      router.push(qs ? `${basePath}?${qs}` : basePath, { scroll: false });
    },
    [router, sp, basePath],
  );
}
