import { getSiteIdentity } from "@/lib/geonode";
import LoadingState from "@/components/LoadingState";

export default async function Loading() {
  let siteName = "SITARUNG";
  try {
    const site = await getSiteIdentity();
    if (site.siteName && site.siteName !== "DST") siteName = site.siteName;
  } catch { /* fallback */ }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-cap-bg">
      <LoadingState
        label={`Memuat ${siteName}...`}
        labelClassName="text-xs font-semibold tracking-[0.2em] uppercase text-cap-muted animate-pulse"
      />
    </div>
  );
}
