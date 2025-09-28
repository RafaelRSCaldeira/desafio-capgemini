type MessageProps = {
  message: string;
  type: 'system' | 'user';
};

export default function Message({ message, type }: MessageProps) {
  return (
    <>
      <div
        className={`${
          type === 'user'
            ? 'bg-primary_blue w-1/2'
            : 'bg-secondary_gray w-full'
        } break-words text-white text-2xl p-4 rounded-md`}
      >
        <p>{message}</p>
      </div>
    </>
  );
}
