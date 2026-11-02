<script lang="ts" setup>
const props = defineProps<{
    term: any;
    dataNode?: any;
    nodesById: Record<string, any>;
    showDescription?: boolean;
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
const rules = computed(() => [
    ["permission", "Permission"],
    ["prohibition", "Prohibition"],
    ["obligation", "Obligation"],
].flatMap(([predicate, kind]) => objects(ODRL + predicate)
    .filter(value => value["@id"])
    .map(value => ({
        id: value["@id"],
        kind,
        node: props.nodesById[value["@id"]],
    }))));

function ruleName(rule: any): string {
    return values(SCHEMA + "name", rule.node)[0] || rule.kind;
}

function ruleFields(rule: any): [string, string[]][] {
    return [
        ["Description", values(SCHEMA + "description", rule.node)],
        ["Action", values(ODRL + "action", rule.node)],
        ["Assigner", values(ODRL + "assigner", rule.node)],
        ["Assignee", values(ODRL + "assignee", rule.node)],
    ].filter(([, fieldValues]) => fieldValues.length) as [string, string[]][];
}

function targets(rule: any): any[] {
    return objects(ODRL + "target", rule.node)
        .filter(value => value["@id"])
        .map(value => ({
            id: value["@id"],
            node: props.nodesById[value["@id"]],
        }));
}

function targetName(target: any): string {
    return values(SCHEMA + "name", target.node)[0]
        || displayValue({ "@id": target.id })
        || "Target";
}

function targetDescriptions(target: any): string[] {
    return values(SCHEMA + "description", target.node);
}
</script>

<template>
    <article class="rounded-md border border-border bg-card p-4">
        <header class="mb-3">
            <h3 class="text-lg font-semibold">{{ name }}</h3>
            <div class="mt-1 break-all text-sm text-muted-foreground">{{ term.value }}</div>
            <template v-if="props.showDescription !== false">
                <p v-for="value in description" :key="value" class="mt-3 whitespace-pre-line">{{ value }}</p>
            </template>
        </header>

        <section v-for="rule in rules" :key="rule.id" class="mt-4 border-t pt-4">
            <div class="text-sm font-medium uppercase tracking-wide text-muted-foreground">{{ rule.kind }}</div>
            <h4 class="mt-1 font-semibold">{{ ruleName(rule) }}</h4>
            <div class="mt-1 break-all text-sm text-muted-foreground">{{ rule.id }}</div>
            <dl class="mt-3 divide-y border-t">
                <div v-for="([label, fieldValues]) in ruleFields(rule)" :key="label" class="grid gap-1 py-3 md:grid-cols-[12rem_1fr]">
                    <dt class="font-medium">{{ label }}</dt>
                    <dd>
                        <div v-for="value in fieldValues" :key="value" class="whitespace-pre-line break-words">{{ value }}</div>
                    </dd>
                </div>
            </dl>

            <div v-if="targets(rule).length" class="mt-4">
                <h5 class="font-medium">{{ targets(rule).length === 1 ? "Target" : "Targets" }}</h5>
                <div class="mt-2 grid gap-3">
                    <article v-for="target in targets(rule)" :key="target.id" class="rounded-md border bg-muted/20 p-4">
                        <h6 class="font-semibold">{{ targetName(target) }}</h6>
                        <div class="mt-1 break-all text-sm text-muted-foreground">{{ target.id }}</div>
                        <p
                            v-for="value in targetDescriptions(target)"
                            :key="value"
                            class="mt-3 whitespace-pre-line break-words"
                        >{{ value }}</p>
                    </article>
                </div>
            </div>
        </section>
    </article>
</template>
