import { getSiteIdentity } from "@/lib/geonode";

export default async function Loading() {
  let siteName = "DST FOLUR";
  try {
    const site = await getSiteIdentity();
    if (site.siteName) siteName = site.siteName;
  } catch { /* fallback */ }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-cap-bg">
      <div className="flex flex-col items-center gap-5">
        <div className="animate-spin">
          <img
            src="/images/folur-kakao.svg"
            alt="Loading"
            className="w-12 h-12 object-contain"
          />
        </div>
        <p className="text-xs font-semibold tracking-[0.2em] uppercase text-cap-muted animate-pulse">
          Memuat {siteName}...
        </p>
      </div>
    </div>
  );
}
