import { ChatMessage } from "@/src/types/chat";

interface Props {
  message: ChatMessage;
}

export default function MessageBubble({
  message,
}: Props) {
  return (
    <div className="space-y-4">
      <div className="ml-auto max-w-3xl rounded-2xl bg-zinc-800 px-5 py-4 text-sm leading-7 text-white">
        {message.question}
      </div>

      <div className="max-w-4xl rounded-2xl border border-zinc-800 bg-zinc-900 px-5 py-5 text-sm leading-7 text-zinc-200">
        <div className="whitespace-pre-wrap">
          {message.answer}
        </div>

        {message.sources &&
          message.sources.length >
            0 && (
            <div className="mt-5 border-t border-zinc-800 pt-4">
              <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-zinc-500">
                Sources
              </div>

              <div className="space-y-2">
                {message.sources.map(
                  (source) => (
                    <div
                      key={
                        source.document_id
                      }
                      className="rounded-lg bg-zinc-950 px-3 py-2 text-xs text-zinc-400"
                    >
                      {source.original_filename}
                    </div>
                  ),
                )}
              </div>
            </div>
          )}
      </div>
    </div>
  );
}