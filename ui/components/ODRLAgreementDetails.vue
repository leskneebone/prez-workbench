<script lang="ts" setup>
const props = defineProps<{
    term: any;
    dataNode?: any;
    nodesById: Record<string, any>;
}>();

const SCHEMA = "https://schema.org/";
const ODRL = "http://www.w3.org/ns/odrl/2/";
const PREZ_LABEL = "https://prez.dev/label";

function objects(predicate: string, node = props.dataNode): any[] {
    return node?.[predicate] || [];
}

function displayValue(value: any): string {
    if (value?.["@value"] !== undefined) return String(value["@value"]);
    if (value?.["@id"]) {
        const identifier = value["@id"];
        const label = props.nodesById[identifier]?.[PREZ_LABEL]?.[0]?.["@value"];
        if (label) return label;
        if (identifier.startsWith(ODRL)) return identifier.slice(ODRL.length);
        return identifier;
    }
    return "";
}

function values(predicate: string, node = props.dataNode): string[] {
    return [...new Set(objects(predicate, node).map(displayValue).filter(Boolean))];
}

const name = computed(() => values(SCHEMA + "name")[0] || props.term.label?.value || "ODRL Agreement");
const description = computed(() => values(SCHEMA + "description"));
const permissions = computed(() => objects(ODRL + "permission")
    .filter(value => value["@id"])
    .map(value => ({ id: value["@id"], node: props.nodesById[value["@id"]] })));

function permissionName(permission: any): string {
    return values(SCHEMA + "name", permission.node)[0] || "Permission";
}

function permissionFields(permission: any): [string, string[]][] {
    return [
        ["Description", values(SCHEMA + "description", permission.node)],
        ["Action", values(ODRL + "action", permission.node)],
        ["Assigner", values(ODRL + "assigner", permission.node)],
        ["Assignee", values(ODRL + "assignee", permission.node)],
        ["Target", values(ODRL + "target", permission.node)],
    ].filter(([, fieldValues]) => fieldValues.length) as [string, string[]][];
}
</script>

<template>
    <article class="rounded-md border border-border bg-card p-4">
        <header class="mb-3">
            <h3 class="text-lg font-semibold">{{ name }}</h3>
            <div class="mt-1 break-all text-sm text-muted-foreground">{{ term.value }}</div>
            <p v-for="value in description" :key="value" class="mt-3 whitespace-pre-line">{{ value }}</p>
        </header>

        <section v-for="permission in permissions" :key="permission.id" class="mt-4 border-t pt-4">
            <h4 class="font-semibold">{{ permissionName(permission) }}</h4>
            <div class="mt-1 break-all text-sm text-muted-foreground">{{ permission.id }}</div>
            <dl class="mt-3 divide-y border-t">
                <div v-for="([label, fieldValues]) in permissionFields(permission)" :key="label" class="grid gap-1 py-3 md:grid-cols-[12rem_1fr]">
                    <dt class="font-medium">{{ label }}</dt>
                    <dd>
                        <div v-for="value in fieldValues" :key="value" class="whitespace-pre-line break-words">{{ value }}</div>
                    </dd>
                </div>
            </dl>
        </section>
    </article>
</template>
