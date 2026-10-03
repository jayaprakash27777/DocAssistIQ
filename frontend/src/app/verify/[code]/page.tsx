import { redirect } from "next/navigation";

export default async function VerifyCodeRedirectPage({
  params,
}: {
  params: Promise<{ code: string }>;
}) {
  const resolvedParams = await params;
  const code = resolvedParams.code;
  redirect(`/verify?code=${encodeURIComponent(code)}`);
}
