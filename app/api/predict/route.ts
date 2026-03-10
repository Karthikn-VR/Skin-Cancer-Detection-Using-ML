import { NextResponse } from "next/server";

export const runtime = "nodejs";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(req: Request) {
  try {
    const form = await req.formData();
    const file = form.get("file");

    if (!(file instanceof File)) {
      return NextResponse.json(
        { error: "Missing file field `file`." },
        { status: 400 }
      );
    }

    const fwd = new FormData();
    fwd.set("file", file, file.name);

    const res = await fetch(`${BACKEND_URL}/predict`, {
      method: "POST",
      body: fwd,
    });

    const text = await res.text();
    let json: any = null;
    try {
      json = JSON.parse(text);
    } catch {
      json = { error: text };
    }

    if (json && typeof json === "object" && "cam_pred_index" in json && json.cam_pred_index === 8) {
      json.prediction = "Unknown";
    }

    return NextResponse.json(json, { status: res.status });
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : "Unknown error";
    return NextResponse.json({ error: msg }, { status: 500 });
  }
}
