// The backend URL is read when the container starts, not baked into the bundle, so the same
// image works locally, in docker compose and on Azure Container Apps.
export const dynamic = "force-dynamic";

export function GET() {
  const apiUrl = (process.env.API_URL || "http://localhost:8000").replace(/\/+$/, "");
  return Response.json({ apiUrl });
}
