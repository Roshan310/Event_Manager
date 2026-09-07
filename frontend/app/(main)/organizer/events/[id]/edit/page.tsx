import { EventFormPage } from "@/components/event-form";
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  return <EventFormPage id={(await params).id} />;
}
