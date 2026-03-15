import { useState, useEffect } from 'react';
import Map, { Source, Layer, useControl } from 'react-map-gl/maplibre';
import type { FillLayer, SymbolLayer } from 'react-map-gl/maplibre';
import { MapboxOverlay } from '@deck.gl/mapbox';
import type { MapboxOverlayProps } from '@deck.gl/mapbox';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import * as topojson from 'topojson-client';
import 'maplibre-gl/dist/maplibre-gl.css';
import { CitySummary } from './types';

// Interleaved overlay — lives inside MapLibre's WebGL context, zero sync drift
function DeckGLOverlay(props: MapboxOverlayProps) {
  const overlay = useControl<MapboxOverlay>(() => new MapboxOverlay({ interleaved: true, ...props }));
  overlay.setProps(props);
  return null;
}

// ISO 3166-1 numeric codes for the three host nations
// Colour: pale version of each country's flag dominant colour
const COUNTRY_LAYERS: Array<{ id: number; color: string; opacity: number }> = [
  { id: 840, color: '#002868', opacity: 0.22 }, // 🇺🇸 USA  — Old Glory blue
  { id: 124, color: '#FF0000', opacity: 0.14 }, // 🍁 Canada — maple red
  { id: 484, color: '#006847', opacity: 0.20 }, // 🇲🇽 Mexico — eagle green
];

// Bold country labels with 2026 World Cup game counts
const COUNTRY_LABELS_GEOJSON = {
  type: 'FeatureCollection' as const,
  features: [
    {
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [-101.5, 39.5] },
      properties: { label: 'UNITED STATES', sub: '78 World Cup Matches' },
    },
    {
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [-96.8, 60.5] },
      properties: { label: 'CANADA', sub: '13 World Cup Matches' },
    },
    {
      type: 'Feature' as const,
      geometry: { type: 'Point' as const, coordinates: [-102.5, 24.0] },
      properties: { label: 'MEXICO', sub: '13 World Cup Matches' },
    },
  ],
};

const INITIAL_VIEW_STATE = {
  longitude: -100,
  latitude: 48,
  zoom: 2.6,
  pitch: 0,
  bearing: 0,
  minZoom: 2.2,
  maxZoom: 10,
};

// Bounding box that covers US + Canada + Mexico only
const NORTH_AMERICA_BOUNDS: [[number, number], [number, number]] = [
  [-175, 12],  // SW: west Alaska, southern Mexico
  [-50,  84],  // NE: eastern Canada
];

// RGBA colors per sentiment — vivid, saturated
const SENTIMENT_COLORS: Record<string, [number, number, number, number]> = {
  positive: [34,  255, 128, 240],   // electric green
  negative: [255,  50, 100, 240],   // hot pink/red
  mixed:    [255, 165,   0, 240],   // vivid orange
  neutral:  [0,   220, 255, 220],   // electric cyan
};

const SENTIMENT_EMOJI: Record<string, string> = {
  positive: '⚽', negative: '🟥', mixed: '🌀', neutral: '🎤',
};

interface MapComponentProps {
  data: CitySummary[];
  onCitySelect: (city: CitySummary) => void;
  mapStyle?: string;
}

export default function MapComponent({ data, onCitySelect, mapStyle }: MapComponentProps) {
  const [countriesGeoJson, setCountriesGeoJson] = useState<any>(null);

  useEffect(() => {
    fetch('https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/countries-110m.json')
      .then(r => r.json())
      .then(topology => {
        const geojson = topojson.feature(topology, topology.objects.countries);
        setCountriesGeoJson(geojson);
      })
      .catch(() => { /* silently ignore if CDN is unreachable */ });
  }, []);

  const layers = [
    new HeatmapLayer({
      id: 'heatmap-layer',
      data,
      getPosition: (d: any) => [d.lon, d.lat],
      getWeight: (d: any) => d.weight,
      radiusPixels: 80,
      aggregation: 'SUM',
      intensity: 1.4,
      threshold: 0.05,
      colorRange: [
        [0,    0,   0,   0],     // transparent (zero energy)
        [0,   104,  71, 160],    // 🇲🇽 Mexico green
        [0,   130,  80, 185],    // Mexico green (brighter)
        [40,   80, 155, 200],    // transition
        [60,   59, 110, 210],    // 🇺🇸 USA blue (Old Glory)
        [100,  90, 200, 215],    // blue-violet bridge
        [210, 215, 255, 225],    // near-white (blue tint)
        [255, 255, 255, 235],    // ⬜ White — shared by all three flags
        [206,  17,  38, 240],    // 🇲🇽 Mexico/🇺🇸 USA red
        [178,  34,  52, 245],    // 🇺🇸 USA flag red (Stars & Stripes)
        [255,   0,   0, 250],    // 🍁 Canada red (vivid)
        [255,  30,  30, 255],    // peak — hot Canada red
      ],
    }),
    // Wide outer glow halo — fixed pixel size so it never grows/shrinks with zoom
    new ScatterplotLayer({
      id: 'scatter-glow',
      data,
      getPosition: (d: any) => [d.lon, d.lat],
      getFillColor: (d: any) => {
        const c = SENTIMENT_COLORS[d.sentiment] ?? SENTIMENT_COLORS.neutral;
        return [c[0], c[1], c[2], 70];
      },
      getRadius: (d: any) => 26 + d.weight * 3,
      radiusUnits: 'pixels',
      stroked: false,
      pickable: false,
    }),
    // Inner mid-glow ring — fixed pixel size
    new ScatterplotLayer({
      id: 'scatter-midglow',
      data,
      getPosition: (d: any) => [d.lon, d.lat],
      getFillColor: (d: any) => {
        const c = SENTIMENT_COLORS[d.sentiment] ?? SENTIMENT_COLORS.neutral;
        return [c[0], c[1], c[2], 140];
      },
      getRadius: (d: any) => 14 + d.weight * 1.5,
      radiusUnits: 'pixels',
      stroked: false,
      pickable: false,
    }),
    // Main bright clickable dot — fixed pixel size
    new ScatterplotLayer({
      id: 'scatter-layer',
      data,
      getPosition: (d: any) => [d.lon, d.lat],
      getFillColor: (d: any) => SENTIMENT_COLORS[d.sentiment] ?? SENTIMENT_COLORS.neutral,
      getLineColor: (d: any) => {
        const c = SENTIMENT_COLORS[d.sentiment] ?? SENTIMENT_COLORS.neutral;
        return [c[0], c[1], c[2], 255];
      },
      lineWidthMinPixels: 1.5,
      stroked: true,
      getRadius: 7,
      radiusUnits: 'pixels',
      pickable: true,
      onClick: ({ object }: any) => {
        if (object) onCitySelect(object as CitySummary);
      },
    }),
  ] as any;

  return (
    <div className="absolute inset-0 w-full h-full">
      <Map
        initialViewState={INITIAL_VIEW_STATE}
        mapStyle={mapStyle ?? 'https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json'}
        maxBounds={NORTH_AMERICA_BOUNDS}
        style={{ width: '100%', height: '100%' }}
      >
        {/* Deck.gl layers rendered inside MapLibre's WebGL context — no sync drift */}
        <DeckGLOverlay
          layers={layers}
          getTooltip={({ object }: any) =>
            object
              ? {
                  html: `
                    <div style="
                      background: rgba(2,6,23,0.96);
                      border: 1px solid rgba(255,255,255,0.15);
                      padding: 8px 12px;
                      border-radius: 10px;
                      font-family: system-ui, sans-serif;
                      min-width: 160px;
                    ">
                      <div style="font-weight:600;color:#f1f5f9;font-size:13px;margin-bottom:3px;">
                        ${SENTIMENT_EMOJI[object.sentiment] ?? '📍'} ${object.location}
                      </div>
                      <div style="color:#94a3b8;font-size:11px;">
                        Fan Energy ${object.weight.toFixed(2)} &nbsp;·&nbsp; ${object.sentiment}
                      </div>
                    </div>`,
                  style: { background: 'none', boxShadow: 'none', padding: '0' },
                }
              : null
          }
        />

        {/* Country flag-colour fills */}
        {countriesGeoJson && (
          <Source id="countries" type="geojson" data={countriesGeoJson}>
            {COUNTRY_LAYERS.map(({ id, color, opacity }) => {
              const layerStyle: FillLayer = {
                id: `country-${id}`,
                type: 'fill',
                filter: ['==', ['id'], id],
                paint: { 'fill-color': color, 'fill-opacity': opacity },
              };
              return <Layer key={id} {...layerStyle} />;
            })}
          </Source>
        )}

        {/* Country name + game count labels */}
        <Source id="country-labels" type="geojson" data={COUNTRY_LABELS_GEOJSON}>
          <Layer
            {...({
              id: 'country-label-name',
              type: 'symbol',
              layout: {
                'text-field': ['get', 'label'],
                'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
                'text-size': 13,
                'text-anchor': 'bottom',
                'text-offset': [0, -0.15],
                'text-letter-spacing': 0.12,
                'text-allow-overlap': true,
                'text-ignore-placement': true,
              },
              paint: {
                'text-color': '#ffffff',
                'text-opacity': 0.85,
                'text-halo-color': '#000000',
                'text-halo-width': 1.5,
              },
            } as SymbolLayer)}
          />
          <Layer
            {...({
              id: 'country-label-sub',
              type: 'symbol',
              layout: {
                'text-field': ['get', 'sub'],
                'text-font': ['Open Sans Bold', 'Arial Unicode MS Bold'],
                'text-size': 10,
                'text-anchor': 'top',
                'text-offset': [0, 0.15],
                'text-letter-spacing': 0.06,
                'text-allow-overlap': true,
                'text-ignore-placement': true,
              },
              paint: {
                'text-color': '#f0c040',
                'text-opacity': 0.9,
                'text-halo-color': '#000000',
                'text-halo-width': 1.5,
              },
            } as SymbolLayer)}
          />
        </Source>

        {/* +/- NavigationControl removed — use scroll/pinch to zoom */}
      </Map>
    </div>
  );
}
