import { useMemo } from "react";

export default function useMapBounds(points = []) {
  return useMemo(() => {
    if (!points.length) return null;

    const lats = points.map(p => p[0]); // Lat = index 0
    const lngs = points.map(p => p[1]); // Lng = index 1

    return [
      [Math.min(...lats), Math.min(...lngs)], // Southwest
      [Math.max(...lats), Math.max(...lngs)]  // Northeast
    ];
  }, [points]);
}
