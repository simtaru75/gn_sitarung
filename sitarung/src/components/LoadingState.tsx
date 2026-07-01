import type { CSSProperties } from "react";

export const DEFAULT_LOADING_SPINNER = "https://www.svgrepo.com/show/491270/loading-spinner.svg";

export default function LoadingState({
  label,
  className = "",
  spinnerClassName = "h-16 w-16",
  labelClassName = "text-xs font-semibold tracking-[0.2em] uppercase animate-pulse",
  labelStyle,
}: {
  label: string;
  className?: string;
  spinnerClassName?: string;
  labelClassName?: string;
  labelStyle?: CSSProperties;
}) {
  return (
    <div className={`flex flex-col items-center justify-center gap-5 text-center ${className}`.trim()}>
      <img
        src={DEFAULT_LOADING_SPINNER}
        alt="Loading"
        className={`animate-spin object-contain ${spinnerClassName}`.trim()}
      />
      <p className={labelClassName} style={labelStyle}>{label}</p>
    </div>
  );
}