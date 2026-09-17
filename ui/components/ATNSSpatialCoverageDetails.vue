<script lang="ts" setup>
const props = withDefaults(defineProps<{
    term: any;
    dataNode?: any;
    nodesById: Record<string, any>;
    heading?: string;
    openByDefault?: boolean;
    showDetailLink?: boolean;
}>(), {
    heading: "Agreement area map",
    openByDefault: false,
    showDetailLink: true,
});

const GEO = "http://www.opengis.net/ont/geosparql#";
const SCHEMA = "https://schema.org/";
const PREZ_LABEL = "https://prez.dev/label";
const expanded = ref(props.openByDefault || false);

function onToggle(event: Event) {
    expanded.value = (event.currentTarget as HTMLDetailsElement).open;
}

function objects(predicate: string, node = props.dataNode): any[] {
    return node?.[predicate] || [];
}

function literalValue(value: any): string | undefined {
    return value?.["@value"] === undefined ? undefined : String(value["@value"]);
}

const title = computed(() =>
    literalValue(objects(SCHEMA + "name")[0])
    || literalValue(objects(PREZ_LABEL)[0])
    || props.term.label?.value
    || props.term.value,
);

const geometries = computed(() => [
    ...objects(GEO + "hasGeometry"),
    ...objects(GEO + "hasBoundingBox"),
]);

const wkts = computed(() => geometries.value.flatMap((geometry: any) => {
    const node = geometry?.["@id"] ? props.nodesById[geometry["@id"]] : undefined;
    return objects(GEO + "asWKT", node).map(literalValue).filter(Boolean) as string[];
}));

const layers = computed(() => [{
    type: "FeatureCollection",
    title: title.value,
    features: wkts.value.map((wkt, index) => ({
        type: "Feature",
        id: `${props.term.value}-${index}`,
        wkt,
        name: title.value,
        data: { iri: props.term.value },
    })),
}]);

const detailUrl = computed(() => `/object?uri=${encodeURIComponent(props.term.value)}`);
</script>

<template>
    <details
        class="mt-6 rounded-md border bg-white"
        :open="openByDefault"
        @toggle="onToggle"
    >
        <summary class="cursor-pointer select-none px-5 py-4 text-xl font-semibold">
            {{ heading }}
        </summary>
        <div class="border-t px-5 py-4">
            <div class="mb-4 flex flex-wrap items-baseline justify-between gap-3">
                <strong>{{ title }}</strong>
                <a v-if="showDetailLink" :href="detailUrl" class="underline">See full details</a>
            </div>
            <div v-if="expanded && wkts.length" class="h-[500px] overflow-hidden rounded-md border">
                <Map :layers="layers" :animation-duration="1000" fit-added-layers-to-extent />
            </div>
            <p v-else-if="expanded" class="text-sm text-muted-foreground">
                Map geometry is not available from this workbench.
            </p>
        </div>
    </details>
</template>
