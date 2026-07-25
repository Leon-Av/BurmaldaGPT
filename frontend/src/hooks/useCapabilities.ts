/** Хук возможностей сервера (vision + имя модели). */
import { useEffect, useState } from "react";

import { fetchCapabilities } from "@/api/meta";
import type { Capabilities } from "@/types";

const DEFAULT: Capabilities = {
  vision_enabled: true,
  max_images_per_message: 5,
  model: "",
};

export function useCapabilities(enabled: boolean): Capabilities {
  const [caps, setCaps] = useState<Capabilities>(DEFAULT);

  useEffect(() => {
    if (!enabled) return;
    let alive = true;
    fetchCapabilities()
      .then((c) => {
        if (alive) setCaps(c);
      })
      .catch(() => {
        /* оставляем дефолт */
      });
    return () => {
      alive = false;
    };
  }, [enabled]);

  return caps;
}
