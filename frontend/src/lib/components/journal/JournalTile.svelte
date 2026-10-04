<script lang="ts">
	import { onMount } from 'svelte';
	import { ArrowRight } from 'lucide-svelte';
	import { journalToday, loadJournalToday, deleteEntry, setCheckin } from '$lib/journal.svelte';
	import CheckinPicker from './CheckinPicker.svelte';
	import EntryComposer from './EntryComposer.svelte';
	import EntryList from './EntryList.svelte';

	let { onOpen }: { onOpen: () => void } = $props();

	onMount(() => {
		loadJournalToday();
	});
</script>

<div class="flex flex-col gap-4">
	<div class="flex items-center justify-between gap-3">
		<h2 class="font-display text-xl">Diário de bordo</h2>
		<button type="button" class="more" onclick={onOpen}>Abrir <ArrowRight size={15} /></button>
	</div>

	{#if journalToday.day}
		<div class="checkins">
			<CheckinPicker kind="mood" compact value={journalToday.day.mood} onPick={(v) => setCheckin('mood', v)} />
			<CheckinPicker kind="energy" compact value={journalToday.day.energy} onPick={(v) => setCheckin('energy', v)} />
		</div>
	{/if}

	<EntryComposer disabled={!journalToday.day} />

	{#if journalToday.loading}
		<div class="skeleton-pulse h-16"></div>
	{:else if journalToday.failed}
		<p class="muted">Não foi possível carregar o diário.</p>
	{:else if journalToday.day && journalToday.day.entries.length > 0}
		<EntryList entries={journalToday.day.entries} onDelete={deleteEntry} limit={4} />
		{#if journalToday.day.entries.length > 4}
			<button type="button" class="more" onclick={onOpen}>+{journalToday.day.entries.length - 4} entradas hoje</button>
		{/if}
	{/if}
</div>

<style>
	.checkins {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
		gap: 16px;
	}
	.muted {
		margin: 0;
		font-size: 14px;
		color: color-mix(in oklab, var(--color-base-content) 62%, transparent);
	}
	.more {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		align-self: flex-start;
		min-height: 36px;
		font: 700 14px/1 var(--font-body);
		color: var(--sec-ink);
		cursor: pointer;
	}
	.more:hover {
		text-decoration: underline;
		text-underline-offset: 3px;
	}
	.more:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
