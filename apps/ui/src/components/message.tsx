import { ChatMessage } from "@/type/message";

export default function Message({ message, role }: ChatMessage) {
  return (
    <>
      <div
        className={`${
          role === 'user'
            ? 'bg-primary_blue w-1/2 self-end'
            : 'w-full'
        } break-words text-white text-lg p-4 rounded-md h-fit`}
      >
        <p>{message}</p>
      </div>
    </>
  );
}
