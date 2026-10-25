import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { Candidate } from './useRestorationPlan';

const format = (value: number) => new Intl.NumberFormat('en-US', { maximumFractionDigits: 3 }).format(value);
type TileStatus = 'loading' | 'ready' | 'unavailable' | 'off';

export function CandidateImpactMap({ candidate, streets, onStreetsChange }: { candidate: Candidate; streets: boolean; onStreetsChange: (enabled: boolean) => void }) {
  const host = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const [attempt, setAttempt] = useState(0);
  const [tileStatus, setTileStatus] = useState<TileStatus>('loading');
  const hasGeometry = candidate.position !== null || candidate.customer_cells.length > 0;
  useEffect(() => {
    if (!host.current) return;
    const map = L.map(host.current, { scrollWheelZoom: false, minZoom: 7, maxZoom: 14, zoomAnimation: false, fadeAnimation: false });
    mapRef.current = map;
    map.attributionControl.addAttribution('AEP challenge GIS · generalized areas');
    const bounds = L.latLngBounds([]);
    candidate.customer_cells.forEach(cell => {
      const { latitude, longitude, precision_degrees } = cell.position;
      const half = precision_degrees / 2;
      const area: L.LatLngBoundsExpression = [[latitude - half, longitude - half], [latitude + half, longitude + half]];
      bounds.extend(area);
      L.rectangle(area, { color: '#025a95', weight: 2, fillOpacity: .13, interactive: false }).addTo(map);
      L.marker([latitude, longitude], { keyboard: false, interactive: false,
        icon: L.divIcon({ className: 'decision-cell-count', html: `<span>${cell.premises}</span>`, iconSize: [34, 30], iconAnchor: [17, 40] }),
      }).addTo(map);
    });
    if (candidate.position) {
      const point: L.LatLngTuple = [candidate.position.latitude, candidate.position.longitude];
      bounds.extend(point);
      const label = document.createElement('div');
      label.textContent = `${candidate.label}: generalized equipment area. Exact position hidden.`;
      L.circleMarker(point, { color: '#af2218', fillColor: '#fff', fillOpacity: 1, weight: 3, radius: 8 })
        .addTo(map).bindPopup(label);
    }
    if (bounds.isValid()) map.fitBounds(bounds, { padding: [44, 44], maxZoom: 14 });
    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(host.current);
    return () => { observer.disconnect(); map.remove(); mapRef.current = null; };
  }, [candidate]);

  // Same optional OSM behavior as the customer map: tile failure never removes
  // the public generalized geometry, changes a result or changes a selection.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;
    if (!streets) { setTileStatus('off'); return; }
    setTileStatus('loading');
    let disposed = false;
    let failed = false;
    const tiles = L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 14, keepBuffer: 1,
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    });
    const fail = () => {
      if (disposed || failed) return;
      failed = true;
      clearTimeout(timeout);
      setTileStatus('unavailable');
      queueMicrotask(() => { if (!disposed && map.hasLayer(tiles)) map.removeLayer(tiles); });
    };
    const timeout = window.setTimeout(fail, 8000);
    tiles.on('tileerror', fail);
    tiles.on('load', () => { if (!disposed && !failed) { clearTimeout(timeout); setTileStatus('ready'); } });
    tiles.addTo(map);
    return () => { disposed = true; clearTimeout(timeout); tiles.off(); if (map.hasLayer(tiles)) map.removeLayer(tiles); };
  }, [candidate, streets, attempt]);

  return <div className="decision-map-wrap">
    {hasGeometry && <div className="decision-map-toolbar"><span>Generalized AEP source areas</span><label><input type="checkbox" checked={streets} onChange={event => onStreetsChange(event.target.checked)} /> Street map</label></div>}
    {hasGeometry ? <div className="decision-map" ref={host} tabIndex={0} role="region" aria-label={`Approximate dependent premise areas for ${candidate.label}`} aria-describedby="decision-map-note" data-testid="decision-map" /> : <p role="status">Generalized geometry is unavailable for this candidate.</p>}
    {hasGeometry && <p className="decision-tile-status" role="status">{tileStatus === 'ready' ? 'Street context: OpenStreetMap · dependency areas: AEP sources.' : tileStatus === 'off' ? 'Street map off. Source dependency areas remain visible.' : tileStatus === 'loading' ? 'Loading optional streets. Source dependency areas are ready.' : 'Street map unavailable. Source dependency areas remain visible.'}{tileStatus === 'unavailable' && <button type="button" onClick={() => setAttempt(value => value + 1)}>Retry street map</button>}</p>}
    <div className="decision-map-caption"><span><i className="decision-legend-cell" /> Dependent customer area</span><span><i className="decision-legend-asset" /> Selected equipment area</span></div>
    <p id="decision-map-note" className="decision-fine">0.01° generalized cells; counts come from verified source dependencies. Cells are not outage boundaries. Exact positions hidden; streets do not verify electrical connections. This view works without street tiles.</p>
    <details className="decision-map-accessible"><summary>Read the map as a list</summary>
      <ul>{candidate.customer_cells.map((cell, index) => <li key={index}>Approximate area {index + 1}: {format(cell.premises)} dependent premises.</li>)}</ul>
      {!candidate.customer_cells.length && <p>No validated premise areas are available for this candidate.</p>}
    </details>
  </div>;
}

