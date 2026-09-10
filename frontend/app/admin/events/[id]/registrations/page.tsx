import { Roster } from "@/components/management";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <Roster id={(await params).id} />;
}
