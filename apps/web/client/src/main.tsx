import React from "react";
import ReactDOM from "react-dom/client";
import { MutationCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { LanguageProvider } from "./i18n";
import { ErrorProvider, reportError } from "./components/ErrorDialog";
import "./index.css";

const queryClient = new QueryClient({
  // 更新系の失敗は、呼び出し側が「inline」で自分の場所に表示する場合を除き、共通のエラーダイアログに出す
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      if (!mutation.meta?.inline) reportError(error);
    },
  }),
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <LanguageProvider>
        <ErrorProvider>
          <BrowserRouter>
            <App />
          </BrowserRouter>
        </ErrorProvider>
      </LanguageProvider>
    </QueryClientProvider>
  </React.StrictMode>
);
