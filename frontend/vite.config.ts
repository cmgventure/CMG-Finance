import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), tsconfigPaths()],
  build: {
    outDir: "build",
  },
  server: {
    port: 5173,
    host: true,
    strictPort: true,
    origin: "http://0.0.0.0:5173",
  },
});
