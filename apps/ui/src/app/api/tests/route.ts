import { NextRequest, NextResponse } from 'next/server';
import { z } from 'zod';
import { exec } from 'node:child_process';
import path from 'node:path';

const Body = z.object({ target: z.enum(['rag', 'ai', 'ui', 'all']) });

function runCmd(command: string, cwd?: string, timeoutMs = 120000): Promise<{ code: number; stdout: string; stderr: string; }> {
  return new Promise((resolve) => {
    exec(command, { cwd, windowsHide: true, env: process.env, timeout: timeoutMs }, (error, stdout, stderr) => {
      const code = (error && (error as unknown as { code?: number }).code) ?? 0;
      resolve({ code, stdout: stdout?.toString() ?? '', stderr: stderr?.toString() ?? '' });
    });
  });
}

export async function POST(req: NextRequest) {
  const json = await req.json().catch(() => ({}));
  const parsed = Body.safeParse(json);
  if (!parsed.success) {
    return NextResponse.json({ ok: false, error: 'Invalid body' }, { status: 400 });
  }

  const target = parsed.data.target;

  const base = process.cwd();
  const ragCwd = path.resolve(base, '../rag');
  const aiCwd = path.resolve(base, '../ai');
  const uiCwd = path.resolve(base, '.');

  type Step = { cmd: string; cwd: string };
  const steps: Step[] = [];
  if (target === 'rag') {
    steps.push({ cmd: 'uv run -q pytest -vv', cwd: ragCwd });
  } else if (target === 'ai') {
    steps.push({ cmd: 'uv run -q pytest -vv', cwd: aiCwd });
  } else if (target === 'ui') {
    steps.push({ cmd: 'pnpm test', cwd: uiCwd });
  } else {
    steps.push({ cmd: 'uv run -q pytest -vv', cwd: ragCwd });
    steps.push({ cmd: 'uv run -q pytest -vv', cwd: aiCwd });
    steps.push({ cmd: 'pnpm test', cwd: uiCwd });
  }

  let combined = '';
  let anyFail = false;
  for (const step of steps) {
    combined += `cwd: ${step.cwd}\n> ${step.cmd}\n`;
    let { code, stdout, stderr } = await runCmd(step.cmd, step.cwd, 180000);
    // Fallback if uv is unavailable
    if (code !== 0 && /uv(\s|:|\sis)?(not found|não|recognized)/i.test(stderr || '')) {
      const fallback = 'pytest -vv';
      combined += `uv não disponível, tentando: ${fallback}\n`;
      const res = await runCmd(fallback, step.cwd, 180000);
      code = res.code; stdout = res.stdout; stderr = res.stderr;
    }
    combined += stdout;
    if (stderr) combined += `\n[stderr]\n${stderr}\n`;
    if (code !== 0) anyFail = true;
    combined += `\n(exit code: ${code})\n\n`;
  }

  return NextResponse.json({ ok: !anyFail, output: combined.trim() }, { status: anyFail ? 500 : 201 });
}


