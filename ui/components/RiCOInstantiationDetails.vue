<script lang="ts" setup>
const props = defineProps<{
    term: any;
    dataNode?: any;
    nodesById: Record<string, any>;
    renderHtml?: boolean;
    renderMarkdown?: boolean;
}>();

const SCHEMA = "https://schema.org/";
const RICO = "https://www.ica.org/standards/RiC/ontology#";
const PREZ_LABEL = "https://prez.dev/label";

function objects(predicate: string, node = props.dataNode): any[] {
    return node?.[predicate] || [];
}

function displayValue(value: any): string {
    if (value?.["@value"] !== undefined) return String(value["@value"]);
    if (value?.["@id"]) {
        const label = objects(PREZ_LABEL, props.nodesById[value["@id"]])[0]?.["@value"];
        return label || value["@id"];
    }
    return "";
}

function values(predicate: string): string[] {
    return [...new Set(objects(predicate).map(displayValue).filter(Boolean))];
}

const name = computed(() =>
    values(SCHEMA + "name")[0] || values(RICO + "name")[0] || props.term.label?.value || "Instantiation",
);

const expressedDates = computed(() => objects(RICO + "isAssociatedWithDate")
    .flatMap(value => value["@id"] ? objects(RICO + "expressedDate", props.nodesById[value["@id"]]) : [])
    .map(displayValue)
    .filter(Boolean));

const fields = computed(() => [
    ["Description", values(SCHEMA + "description")],
    ["Identifier", values(SCHEMA + "identifier").length ? values(SCHEMA + "identifier") : values(RICO + "identifier")],
    ["Instantiation date", expressedDates.value],
    ["Extent", [...new Set([...values(RICO + "instantiationExtent"), ...values(SCHEMA + "materialExtent")])]],
    ["Location", values(SCHEMA + "location")],
    ["Collector", values(RICO + "hasCollector")],
    ["Date created", values(SCHEMA + "dateCreated")],
    ["Date modified", values(SCHEMA + "dateModified")],
].filter(([, fieldValues]) => fieldValues.length));
</script>

<template>
    <article class="rounded-md border border-border bg-card p-4">
        <header class="mb-3">
            <h3 class="text-lg font-semibold">{{ name }}</h3>
            <div class="mt-1 break-all text-sm text-muted-foreground">{{ term.value }}</div>
            <div v-if="term.rdfTypes?.length" class="mt-2 flex flex-wrap gap-3 text-sm">
                <Node v-for="rdfType in term.rdfTypes" :key="rdfType.value" :term="rdfType" />
            </div>
        </header>

        <dl v-if="fields.length" class="divide-y border-t">
            <div v-for="([label, fieldValues]) in fields" :key="label" class="grid gap-1 py-3 md:grid-cols-[12rem_1fr]">
                <dt class="font-medium">{{ label }}</dt>
                <dd>
                    <div v-for="value in fieldValues" :key="value" class="whitespace-pre-line break-words">{{ value }}</div>
                </dd>
            </div>
        </dl>
    </article>
</template>
