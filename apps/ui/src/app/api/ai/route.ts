import { NextResponse, NextRequest } from 'next/server';
import { z } from 'zod';

const Body = z.object({ message: z.string().min(1) });

export async function POST(req: NextRequest) {
  const json = await req.json();
  const parsed = Body.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid body' }, { status: 400 });
  }
  const response = await fetch(process.env.AI_API || "", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        message: parsed.data.message,
      }),
    });

    const externalData = await response.json();
  return NextResponse.json(
    { ok: true, message: externalData },
    { status: 201 }
  );
}
