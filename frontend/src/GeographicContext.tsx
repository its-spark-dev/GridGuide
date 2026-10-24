import { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { getMap } from './api';
import type { MapData } from './api';

type Asset = MapData['assets'][number];
type TileStatus = 'loading' | 'ready' | 'unavailable' | 'off';

function VerifiedMap({ data }: { data: MapData }) {
  const host = useRef<HTMLDivElement>(null);
  const mapRef = useRef<L.Map | null>(null);
  const markers = useRef(new Map<string, L.Marker>());
  const overview = useRef<L.LatLngBounds | null>(null);
  const [selected, setSelected] = useState(data.location_alias);
  const [streets, setStreets] = useState(true);
  const [tileAttempt, setTileAttempt] = useState(0);
  const [tileStatus, setTileStatus] = useState<TileStatus>('loading');
  const selectedAsset = data.assets.find(asset => asset.alias === selected)!;

  useEffect(() => {
    if (!host.current) return;
    const map = L.map(host.current, { scrollWheelZoom: false, minZoom: 9, maxZoom: 14, zoomAnimation: false, fadeAnimation: false });
    mapRef.current = map;
    map.attributionControl.addAttribution('AEP challenge GIS · generalized');
    const bounds = L.latLngBounds([]);
    data.primary_lines.paths.forEach(path => {
      const points: L.LatLngTuple[] = path.map(point => [point.latitude, point.longitude]);
      points.forEach(point => bounds.extend(point));
      L.polyline(points, { color: '#025a95', weight: 2, opacity: .55, dashArray: '5 5', interactive: false }).addTo(map);
    });
    const groups = new Map<string, Asset[]>();
    data.assets.forEach(asset => {
      if (!asset.position) return;
      const key = `${asset.position.latitude},${asset.position.longitude}`;
      groups.set(key, [...(groups.get(key) ?? []), asset]);
    });
    groups.forEach(assets => {
      const point = assets[0].position!;
      const latlng: L.LatLngTuple = [point.latitude, point.longitude];
      const half = data.precision_degrees / 2;
      const area: L.LatLngBoundsExpression = [[point.latitude - half, point.longitude - half], [point.latitude + half, point.longitude + half]];
      bounds.extend(area);
      L.rectangle(area, { color: '#025a95', weight: 1, fillOpacity: .08, dashArray: '3 4', interactive: false }).addTo(map);
      const containsCustomer = assets.some(asset => asset.kind === 'customer');
      const label = assets.length === 2 && containsCustomer && assets.some(asset => asset.kind === 'transformer')
        ? 'Customer + serving transformer'
        : assets.length === 1 && assets[0].kind === 'fuse' ? 'Upstream fuse' : assets.map(asset => asset.label).join(' + ');
      const symbol = assets.map(asset => ({ customer: 'C', transformer: 'T', fuse: 'F', circuit_terminal: '' })[asset.kind]).join(' + ');
      const icon = L.divIcon({ className: 'verified-map-marker', html: `<span class="${containsCustomer ? 'customer-marker' : 'equipment-marker'}">${symbol}</span>`, iconSize: [52, 44], iconAnchor: [26, 22] });
      const popup = document.createElement('div');
      const title = document.createElement('strong'); title.textContent = label;
      const description = document.createElement('p'); description.textContent = assets.length > 1 ? 'Share this generalized area; exact positions are hidden.' : 'Source-verified equipment in this generalized area; exact position hidden.';
      popup.append(title, description);
      const marker = L.marker(latlng, { icon, title: `${label} — approximate area`, alt: label, keyboard: true }).addTo(map).bindPopup(popup);
      marker.on('click', () => setSelected(assets[0].alias));
      assets.forEach(asset => markers.current.set(asset.alias, marker));
    });
    if (bounds.isValid()) { map.fitBounds(bounds, { padding: [30, 30], maxZoom: 12 }); overview.current = bounds; }
    const resize = new ResizeObserver(() => map.invalidateSize());
    resize.observe(host.current);
    return () => { resize.disconnect(); markers.current.clear(); map.remove(); mapRef.current = null; };
  }, [data]);

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
      setTileStatus('unavailable');
      // Queue removal outside Leaflet's tile event stack. Vector GIS stays intact.
      queueMicrotask(() => { if (!disposed && map.hasLayer(tiles)) map.removeLayer(tiles); });
    };
    const timeout = window.setTimeout(fail, 8000);
    tiles.on('tileerror', fail);
    tiles.on('load', () => { if (!disposed && !failed) { clearTimeout(timeout); setTileStatus('ready'); } });
    tiles.addTo(map);
    return () => { disposed = true; clearTimeout(timeout); tiles.off(); if (map.hasLayer(tiles)) map.removeLayer(tiles); };
  }, [streets, tileAttempt, data]);

  const select = (asset: Asset) => {
    setSelected(asset.alias);
    mapRef.current?.closePopup();
    const marker = markers.current.get(asset.alias);
    if (marker && mapRef.current) { mapRef.current.setView(marker.getLatLng(), 13); marker.openPopup(); }
  };
  return <>
    <div className="geography-toolbar"><span>{data.region_label}</span><div>
      <label><input type="checkbox" checked={streets} onChange={event => setStreets(event.target.checked)} /> Street map</label>
      <button type="button" onClick={() => { mapRef.current?.closePopup(); if (overview.current) mapRef.current?.fitBounds(overview.current, { padding: [30, 30], maxZoom: 12 }); }}>View full grid context</button>
    </div></div>
    <div className="geography-layout">
      <div><div className="geographic-map" ref={host} role="region" aria-label="Verified geographic context for Demo location A" aria-describedby="map-precision" data-testid="geographic-map" />
        <p className="map-service-status" role="status">{tileStatus === 'unavailable' ? 'Street basemap unavailable. Verified GIS areas and line context remain visible.' : tileStatus === 'off' ? 'Offline view: verified GIS areas and line context; no street tiles requested.' : tileStatus === 'loading' ? 'Loading optional street basemap. Verified GIS context is already available.' : 'Street basemap: OpenStreetMap. Equipment and line context: AEP challenge GIS.'}
          {tileStatus === 'unavailable' && <button type="button" onClick={() => setTileAttempt(attempt => attempt + 1)}>Retry basemap</button>}</p>
      </div>
      <div className="map-location-list"><h3>Selected location & upstream assets</h3>
        <ul>{data.assets.map(asset => <li key={asset.alias}><button type="button" aria-pressed={selected === asset.alias} onClick={() => select(asset)}>
          <strong>{asset.label}</strong><span>{asset.position ? 'Verified geometry · approximate area' : 'Geometry unavailable · schematic only'}</span>
        </button></li>)}</ul>
        <p className="map-selection" role="status">{selectedAsset.label}{selectedAsset.position ? ' selected. Exact position is hidden.' : ': no map position supplied. See the dependency schematic below.'}</p>
        <a href="#topology-title">See the verified dependency path ↓</a>
      </div>
    </div>
    <ul className="map-legend" aria-label="Map legend"><li><b>C + T</b> Customer + transformer</li><li><b>F</b> Upstream fuse</li><li><span className="line-key" /> Generalized primary lines</li><li><span className="area-key" /> Approximate area</li></ul>
    <p id="map-precision" className="map-disclosure">Approximate areas only; exact positions are hidden. Do not use this map for routing or distance measurement.</p>
    <p className="map-disclosure">{data.disclosures[3]}</p>
    <details className="map-provenance"><summary>Map details & limitations</summary>
      {data.disclosures.slice(0, 3).map(disclosure => <p key={disclosure}>{disclosure}</p>)}<p>{data.primary_lines.note}</p>
      <p>Source layers: Customer_Clip, Transformer_Clip, Fuse_Bank_Clip, Primary_ExportFeatures. Point identities use the verified customer record and typed upstream IDs.</p>
      <p>{data.primary_lines.status === 'available' ? `${data.primary_lines.source_segment_count} source primary segments match the verified circuit; ${data.primary_lines.paths.length} generalized parts remain visible and ${data.primary_lines.omitted_collapsed_parts} parts collapse below the privacy grid.` : 'No primary lines are displayed.'}</p>
    </details>
  </>;
}

export function GeographicContext({ locationAlias }: { locationAlias: string }) {
  const [data, setData] = useState<MapData | null>(null);
  const [error, setError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    setData(null); setError(false);
    getMap(locationAlias, controller.signal).then(result => {
      if (controller.signal.aborted) return;
      if (result.location_alias !== locationAlias) throw new Error('Map location mismatch');
      setData(result);
    }).catch(() => { if (!controller.signal.aborted) setError(true); });
    return () => controller.abort();
  }, [locationAlias, attempt]);
  return <section className="geography-panel" aria-labelledby="geography-title">
    <div className="section-heading"><div><span className="eyebrow">YOUR GRID CONTEXT</span><h2 id="geography-title">Your location on the map</h2></div><span className="small-badge">Verified GIS · approximate areas</span></div>
    <p className="muted">Explore the geography behind your outage outlook. The dependency schematic below explains how the assets connect.</p>
    {data ? <VerifiedMap data={data} /> : <div className="map-load-state" role="status">{error ? <><p>Geographic context is unavailable. Your outage outlook and dependency schematic remain available.</p><button type="button" onClick={() => setAttempt(value => value + 1)}>Retry map</button></> : 'Loading verified geographic context…'}</div>}
  </section>;
}
