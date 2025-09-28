import { ChatMessage } from "@/type/message";
import { marked } from "marked";
import DOMPurify from "isomorphic-dompurify";

export default function Message({ message, role }: ChatMessage) {
  // Converter markdown em HTML
  const rawHtml = marked(message, { breaks: true, gfm: true }) as string;
  const safeHtml = DOMPurify.sanitize(rawHtml);

  return (
    <div
      className={`${
        role === "user" ? "bg-primary_blue w-1/2 self-end" : "w-full"
      } break-words text-white text-lg p-4 rounded-md h-fit`}
    >
      {/* Renderizar como HTML, mas ainda funciona se for só texto normal */}
      <div dangerouslySetInnerHTML={{ __html: safeHtml }} />
    </div>
  );
}
