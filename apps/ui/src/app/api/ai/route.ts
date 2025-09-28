import { NextResponse, NextRequest } from 'next/server';
import { z } from 'zod';

const Body = z.object({ message: z.string().min(1) });

export async function POST(req: NextRequest) {
  const json = await req.json();
  const parsed = Body.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ error: 'Invalid body' }, { status: 400 });
  }
  return NextResponse.json(
    { ok: true, message: "teste" },
    { status: 201 }
  );
}
