import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const target = loadEnv(mode, process.cwd(), "").ACADEMIA_API_PROXY_TARGET;
  return {
    plugins: [react()],
    server: {
      host: "127.0.0.1",
      port: 5173,
      strictPort: true,
      proxy: target
        ? {
            "/api": {
              target,
              rewrite: (path) => path.replace(/^\/api\/health(?=\?|$)/, "/health"),
            },
          }
        : undefined,
    },
    test: { environment: "jsdom" },
  };
});
