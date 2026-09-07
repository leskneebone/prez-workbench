<script lang="ts" setup>
const props = defineProps<{
    term: any;
    dataNode?: any;
    nodesById: Record<string, any>;
}>();

const SCHEMA = "https://schema.org/";
const ATNS = "https://linked.data.gov.au/def/atns/model/";
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

const name = computed(() => values(SCHEMA + "name")[0] || props.term.label?.value || "Reference");
const urls = computed(() => values(SCHEMA + "url"));
const fields = computed(() => [
    ["Author", values(SCHEMA + "author")],
    ["Contributor", values(SCHEMA + "contributor")],
    ["Date published", values(SCHEMA + "datePublished")],
    ["Reference type", values(ATNS + "referenceType")],
    ["ATNS reference ID", values(ATNS + "sourceReferenceId")],
    ["Conditions of access", values(SCHEMA + "conditionsOfAccess")],
].filter(([, fieldValues]) => fieldValues.length));
</script>

<template>
    <article class="rounded-md border border-border bg-card p-4">
        <header class="mb-3">
            <h3 class="text-lg font-semibold">{{ name }}</h3>
            <div class="mt-1 break-all text-sm text-muted-foreground">{{ term.value }}</div>
        </header>

        <dl v-if="fields.length" class="divide-y border-t">
            <div v-for="([label, fieldValues]) in fields" :key="label" class="grid gap-1 py-3 md:grid-cols-[12rem_1fr]">
                <dt class="font-medium">{{ label }}</dt>
                <dd>
                    <div v-for="value in fieldValues" :key="value" class="whitespace-pre-line break-words">{{ value }}</div>
                </dd>
            </div>
            <div v-if="urls.length" class="grid gap-1 py-3 md:grid-cols-[12rem_1fr]">
                <dt class="font-medium">URL</dt>
                <dd>
                    <div v-for="url in urls" :key="url" class="break-all">
                        <a :href="url" class="underline" target="_blank" rel="noopener noreferrer">{{ url }}</a>
                    </div>
                </dd>
            </div>
        </dl>
    </article>
</template>
