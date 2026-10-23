// Playwright CT のブラウザ側の入口。アプリと同じ CSS を読み込み、
// React Query のプロバイダで全部品を包む（API 呼び出しはテスト側で page.route により差し替える）。
import "../src/index.css";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeMount } from "@playwright/experimental-ct-react/hooks";

beforeMount(async ({ App }) => {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return (
    <QueryClientProvider client={client}>
      <App />
    </QueryClientProvider>
  );
});
