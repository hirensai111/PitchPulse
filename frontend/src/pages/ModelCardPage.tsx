import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { useModelCard } from "@/api/queries";
import { Skeleton } from "@/components/ui/skeleton";

export function ModelCardPage() {
  const { data, isLoading, error } = useModelCard();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50">
        <div className="max-w-3xl mx-auto px-4 py-8 space-y-4">
          <Skeleton className="h-8 w-48" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-rose-600">Failed to load model card.</div>
      </div>
    );
  }

  const content = data?.content ?? "";
  const isPlaceholder = content.includes("coming soon") || content.includes("coming soon");

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-3xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-slate-900 mb-6">
          About This Model
        </h1>

        {isPlaceholder ? (
          <div className="bg-white rounded-lg border border-slate-200 p-8 text-center">
            <p className="text-slate-600 mb-4">
              The model card is being finalized. Check back soon, or see the
              GitHub repo for the latest version.
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-slate-200 p-8">
            <article className="prose prose-slate max-w-none">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>
                {content}
              </ReactMarkdown>
            </article>
          </div>
        )}

        <div className="mt-6 text-center">
          <a
            href="#"
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            View raw model card on GitHub →
          </a>
        </div>
      </div>
    </div>
  );
}
