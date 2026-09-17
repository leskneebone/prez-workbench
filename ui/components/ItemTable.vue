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
const relationPredicate = "http://purl.org/dc/terms/relation";
const spatialCoveragePredicate = "https://schema.org/spatialCoverage";
const schemaDescriptionPredicate = "https://schema.org/description";
const bodyTextPredicate = "https://schema.org/text";
const atnsEntityClass = "https://linked.data.gov.au/def/atns/model/Entity";
const geoFeatureClass = "http://www.opengis.net/ont/geosparql#Feature";

const atnsDatasetIri = "https://data.idnau.org/pid/resource/d23405b4-fc04-47e2-9e7a-9c5735ae3780";
const dctermsSource = "http://purl.org/dc/terms/source";
const hiddenAtnsSourceNote = "ATNS_XML_05Apr22 export; public, non-deleted records with usable display labels.";

const filteredProperties = computed(() => {
    if (!term?.properties) return [];
    return Object.entries(term.properties)
        .filter(([key]) => !hiddenPredicates.has(key) && !instantiationPredicates.has(key) && key !== referencePredicate && key !== relationPredicate && key !== spatialCoveragePredicate)
        .filter(([key]) => key !== bodyTextPredicate && key !== schemaDescriptionPredicate)
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

const schemaDescriptions = computed(() => term?.properties?.[schemaDescriptionPredicate]?.objects || []);
const bodyTexts = computed(() => term?.properties?.[bodyTextPredicate]?.objects || []);
const isAtnsEntity = computed(() => term?.rdfTypes?.some((type: any) => type.value === atnsEntityClass));
const isGeoFeature = computed(() => term?.rdfTypes?.some((type: any) => type.value === geoFeatureClass));
const spatialCoverages = computed(() => isAtnsEntity.value
    ? term?.properties?.[spatialCoveragePredicate]?.objects || []
    : []);

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

const relatedAgreements = computed(() => {
    if (!term?.properties) return [];
    const unique = new Map<string, any>();
    for (const object of term.properties[relationPredicate]?.objects || []) unique.set(object.value, object);
    return [...unique.values()];
});
</script>

<template>
    <section v-if="schemaDescriptions.length" aria-labelledby="schema-description-heading">
        <h2 id="schema-description-heading" class="mb-3 text-xl font-semibold">Description</h2>
        <div class="rounded-md border bg-white p-5">
            <p
                v-for="description in schemaDescriptions"
                :key="description.value"
                class="whitespace-pre-wrap break-words leading-relaxed [overflow-wrap:anywhere]"
            >{{ description.value }}</p>
        </div>
    </section>

    <details v-if="bodyTexts.length" class="mt-6 rounded-md border bg-white">
        <summary class="cursor-pointer select-none px-5 py-4 text-xl font-semibold">Body text</summary>
        <div class="border-t px-5 py-4">
            <p
                v-for="bodyText in bodyTexts"
                :key="bodyText.value"
                class="whitespace-pre-wrap break-words leading-relaxed [overflow-wrap:anywhere]"
            >{{ bodyText.value }}</p>
        </div>
    </details>

    <ATNSSpatialCoverageDetails
        v-for="feature in spatialCoverages"
        :key="feature.value"
        :term="feature"
        :data-node="responseNodesById[feature.value]"
        :nodes-by-id="responseNodesById"
    />

    <ATNSSpatialCoverageDetails
        v-if="isGeoFeature"
        :term="term"
        :data-node="responseNodesById[term.value]"
        :nodes-by-id="responseNodesById"
        heading="Map"
        open-by-default
        :show-detail-link="false"
    />

    <Table v-if="filteredProperties.length" class="item-table mt-6">
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

    <section v-if="relatedAgreements.length" class="mt-8" aria-labelledby="odrl-agreements-heading">
        <h2 id="odrl-agreements-heading" class="mb-3 text-xl font-semibold">ODRL Agreement enrichment</h2>
        <div class="flex flex-col gap-4">
            <ODRLAgreementDetails
                v-for="agreement in relatedAgreements"
                :key="agreement.value"
                :term="agreement"
                :data-node="responseNodesById[agreement.value]"
                :nodes-by-id="responseNodesById"
            />
        </div>
    </section>
</template>
