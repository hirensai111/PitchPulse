import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AppNav } from "@/components/AppNav";
import { PredictPage } from "@/pages/PredictPage";
import { TrackRecordPage } from "@/pages/TrackRecordPage";
import { ModelCardPage } from "@/pages/ModelCardPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppNav />
        <Routes>
          <Route path="/" element={<PredictPage />} />
          <Route path="/track-record" element={<TrackRecordPage />} />
          <Route path="/about" element={<ModelCardPage />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
