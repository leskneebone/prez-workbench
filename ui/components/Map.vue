<script lang="ts" setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import OlMap from "ol/Map";
import View from "ol/View";
import TileLayer from "ol/layer/Tile";
import VectorLayer from "ol/layer/Vector";
import OSM from "ol/source/OSM";
import VectorSource from "ol/source/Vector";
import WKT from "ol/format/WKT";
import { Fill, Stroke, Style } from "ol/style";
import { createEmpty, extend, isEmpty } from "ol/extent";
import "ol/ol.css";

const props = withDefaults(defineProps<{
    layers?: any[];
    projection?: string;
    animationDuration?: number;
    fitAddedLayersToExtent?: boolean;
}>(), {
    layers: () => [],
    projection: "EPSG:4326",
    animationDuration: 0,
    fitAddedLayersToExtent: false,
});

const target = ref<HTMLElement | null>(null);
let map: OlMap | undefined;
let renderedLayers: VectorLayer<VectorSource>[] = [];

function removeRenderedLayers() {
    if (!map) return;
    for (const layer of renderedLayers) map.removeLayer(layer);
    renderedLayers = [];
}

function renderLayers() {
    if (!map) return;
    removeRenderedLayers();
    const combinedExtent = createEmpty();
    const parser = new WKT();

    for (const layer of props.layers) {
        const features = (layer.features || []).flatMap((feature: any) => {
            if (!feature.wkt) return [];
            try {
                const parsed = parser.readFeature(feature.wkt, {
                    dataProjection: props.projection,
                    featureProjection: props.projection,
                });
                parsed.setId(feature.id);
                parsed.setProperties({ name: feature.name, data: feature.data });
                return [parsed];
            } catch (error) {
                console.warn("Unable to render WKT feature", feature.id, error);
                return [];
            }
        });
        if (!features.length) continue;

        const source = new VectorSource({ features });
        const vectorLayer = new VectorLayer({
            source,
            style: new Style({
                stroke: new Stroke({ color: layer.strokeColor || "#155e75", width: 2 }),
                fill: new Fill({ color: layer.fillColor || "rgba(14, 116, 144, 0.25)" }),
            }),
        });
        map.addLayer(vectorLayer);
        renderedLayers.push(vectorLayer);
        extend(combinedExtent, source.getExtent());
    }

    if (props.fitAddedLayersToExtent && !isEmpty(combinedExtent)) {
        map.getView().fit(combinedExtent, {
            padding: [32, 32, 32, 32],
            duration: props.animationDuration,
            maxZoom: 16,
        });
    }
}

onMounted(async () => {
    await nextTick();
    if (!target.value) return;
    map = new OlMap({
        target: target.value,
        layers: [new TileLayer({ source: new OSM() })],
        view: new View({
            projection: props.projection,
            center: [133.7751, -25.2744],
            zoom: 3,
        }),
    });
    renderLayers();
    requestAnimationFrame(() => map?.updateSize());
});

watch(() => props.layers, renderLayers, { deep: true });

onBeforeUnmount(() => {
    removeRenderedLayers();
    map?.setTarget(undefined);
    map = undefined;
});
</script>

<template>
    <div ref="target" class="h-full min-h-[400px] w-full" aria-label="Map"></div>
</template>
