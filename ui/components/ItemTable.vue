<script lang="ts" setup>
const props = defineProps<{
    term: any;
    renderHtml?: boolean;
    renderMarkdown?: boolean;
}>();
const term = props.term;
const apiEndpoint = useGetPrezAPIEndpoint();
const { getPageUrl } = usePageInfo();
const responseNodes = ref<any[]>([]);

onMounted(async () => {
    const response = await fetch(apiEndpoint + getPageUrl(), {
        headers: { Accept: "application/anot+ld+json" },
    });
    if (response.ok) responseNodes.value = await response.json();
});

const responseNodesById = computed(() => {
    const merged: Record<string, any> = {};
    for (const node of responseNodes.value) {
        const id = node["@id"];
        if (!id) continue;
        const target = merged[id] ||= { "@id": id };
        for (const [predicate, values] of Object.entries(node)) {
            if (predicate === "@id") continue;
            target[predicate] = [...(target[predicate] || []), ...(values as any[])];
        }
    }
    return merged;
});

const hiddenPredicates = new Set([
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#type",
    "https://schema.org/hasPart",
    "https://schema.org/name",
    "https://olis.dev/isAliasFor",
    "http://www.w3.org/2004/02/skos/core#prefLabel",
    "http://purl.org/dc/terms/title",
    "http://www.w3.org/2000/01/rdf-schema#label",
    "https://linked.data.gov.au/def/atns/model/deleted",
]);

const descriptionPredicates = new Set([
    "http://www.w3.org/2004/02/skos/core#definition",
    "http://purl.org/dc/terms/description",
    "https://schema.org/description",
]);

const instantiationPredicates = new Set([
    "https://www.ica.org/standards/RiC/ontology#hasOrHadInstantiation",
    "https://www.ica.org/standards/RiC/ontology#hasOrHadAnalogueInstantiation",
    "https://www.ica.org/standards/RiC/ontology#hasOrHadDigitalInstantiation",
    "https://www.ica.org/standards/RiC/ontology#hasOrHadDerivedInstantiation",
]);

const referencePredicate = "http://purl.org/dc/terms/references";

const atnsDatasetIri = "https://data.idnau.org/pid/resource/d23405b4-fc04-47e2-9e7a-9c5735ae3780";
const dctermsSource = "http://purl.org/dc/terms/source";
const hiddenAtnsSourceNote = "ATNS_XML_05Apr22 export; public, non-deleted records with usable display labels.";

const filteredProperties = computed(() => {
    if (!term?.properties) return [];
    return Object.entries(term.properties)
        .filter(([key]) => !hiddenPredicates.has(key) && !instantiationPredicates.has(key) && key !== referencePredicate)
        .map(([key, value]: [string, any]) => {
            if (term.value !== atnsDatasetIri || key !== dctermsSource) return value;
            return {
                ...value,
                objects: value.objects.filter((object: any) => object.value !== hiddenAtnsSourceNote),
            };
        })
        .filter((value) => value.objects.length)
        .sort((a, b) => {
            if (descriptionPredicates.has(a.predicate.value)) return -1;
            if (descriptionPredicates.has(b.predicate.value)) return 1;
            return (a.predicate.label?.value || a.predicate.value)
                .localeCompare(b.predicate.label?.value || b.predicate.value);
        });
});

const instantiations = computed(() => {
    if (!term?.properties) return [];
    const unique = new Map<string, any>();
    for (const [predicate, property] of Object.entries(term.properties)) {
        if (!instantiationPredicates.has(predicate)) continue;
        for (const object of property.objects) unique.set(object.value, object);
    }
    return [...unique.values()];
});

const references = computed(() => {
    if (!term?.properties) return [];
    const unique = new Map<string, any>();
    for (const object of term.properties[referencePredicate]?.objects || []) unique.set(object.value, object);
    return [...unique.values()];
});
</script>

<template>
    <Table v-if="term?.properties && filteredProperties.length" class="item-table">
        <TableBody role="rowgroup">
            <ItemTableRow
                v-for="(fieldProp, index) in filteredProperties"
                :key="fieldProp.predicate.value"
                :index="index"
                :term="term"
                :objects="fieldProp.objects"
                :predicate="fieldProp.predicate"
                :renderHtml="props.renderHtml"
                :renderMarkdown="props.renderMarkdown"
            />
        </TableBody>
    </Table>

    <section v-if="instantiations.length" class="mt-8" aria-labelledby="rico-instantiations-heading">
        <h2 id="rico-instantiations-heading" class="mb-3 text-xl font-semibold">
            {{ instantiations.length === 1 ? "Instantiation" : "Instantiations" }}
        </h2>
        <div class="flex flex-col gap-4">
            <RiCOInstantiationDetails
                v-for="instantiation in instantiations"
                :key="instantiation.value"
                :term="instantiation"
                :data-node="responseNodesById[instantiation.value]"
                :nodes-by-id="responseNodesById"
                :render-html="props.renderHtml"
                :render-markdown="props.renderMarkdown"
            />
        </div>
    </section>

    <section v-if="references.length" class="mt-8" aria-labelledby="atns-references-heading">
        <h2 id="atns-references-heading" class="mb-3 text-xl font-semibold">
            {{ references.length === 1 ? "Reference" : "References" }}
        </h2>
        <div class="flex flex-col gap-4">
            <ATNSReferenceDetails
                v-for="reference in references"
                :key="reference.value"
                :term="reference"
                :data-node="responseNodesById[reference.value]"
                :nodes-by-id="responseNodesById"
            />
        </div>
    </section>
</template>
