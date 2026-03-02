import Map, { NavigationControl } from 'react-map-gl/maplibre';
import DeckGL from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { HeatmapLayer } from '@deck.gl/aggregation-layers';
import 'maplibre-gl/dist/maplibre-gl.css';
import { CitySummary } from './types';

const INITIAL_VIEW_STATE = {
  longitude: -98.5795,
  latitude: 39.8283,
  zoom: 3,
  pitch: 50,
  bearing: 0
};

interface MapComponentProps {
  data: CitySummary[];
  onCitySelect: (city: CitySummary) => void;
}

export default function MapComponent({ data, onCitySelect }: MapComponentProps) {
  const layers = [
    new HeatmapLayer({
      id: 'heatmap-layer',
      data,
      getPosition: (d: any) => [d.lon, d.lat],
      getWeight: (d: any) => d.weight,
      radiusPixels: 50,
      aggregation: 'SUM',
      colorRange: [
        [0, 0, 0, 0],
        [65, 182, 196],
        [127, 205, 187],
        [199, 233, 180],
        [237, 248, 177],
        [255, 255, 204],
        [255, 237, 160],
        [254, 217, 118],
        [254, 178, 76],
        [253, 141, 60],
        [252, 78, 42],
        [227, 26, 28],
        [177, 0, 38]
      ]
    }),
    new ScatterplotLayer({
      id: 'scatter-layer',
      data,
      getPosition: (d: any) => [d.lon, d.lat],
      getFillColor: [255, 50, 50, 200],
      getRadius: 20000,
      pickable: true,
      onClick: ({object}: any) => {
        if (object) {
          onCitySelect(object as CitySummary);
        }
      }
    })
  ] as any; // Type assertion since deck.gl types can be complex with react-map-gl

  return (
    <div className="absolute inset-0 w-full h-full">
      <DeckGL
        layers={layers}
        initialViewState={INITIAL_VIEW_STATE}
        controller={true}
        getTooltip={({object}: any) => object ? `${object.location}\nActivity: ${object.weight.toFixed(2)}` : null}
      >
        <Map
          mapStyle="https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json"
        >
          <NavigationControl position="top-right" />
        </Map>
      </DeckGL>
    </div>
  );
}
