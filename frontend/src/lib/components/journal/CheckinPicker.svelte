<script lang="ts">
	import { Angry, Frown, Meh, Smile, Laugh } from 'lucide-svelte';

	let {
		kind,
		value,
		onPick,
		compact = false
	}: {
		kind: 'mood' | 'energy';
		value: number | null;
		onPick: (v: number) => void;
		compact?: boolean;
	} = $props();

	const MOOD = [
		{ v: 1, label: 'Péssimo', Icon: Angry },
		{ v: 2, label: 'Ruim', Icon: Frown },
		{ v: 3, label: 'Ok', Icon: Meh },
		{ v: 4, label: 'Bom', Icon: Smile },
		{ v: 5, label: 'Ótimo', Icon: Laugh }
	];
	const ENERGY_LABELS = ['Esgotada', 'Baixa', 'Média', 'Boa', 'Alta'];

	const title = $derived(kind === 'mood' ? 'Humor' : 'Energia');
	const current = $derived(
		value == null ? 'sem registro' : kind === 'mood' ? MOOD[value - 1].label : ENERGY_LABELS[value - 1]
	);
</script>

<fieldset class="picker" class:compact>
	<legend class="legend">
		<span>{title}</span>
		<span class="current">{current}</span>
	</legend>
	<div class="options">
		{#if kind === 'mood'}
			{#each MOOD as m (m.v)}
				<button
					type="button"
					class="opt"
					class:on={value === m.v}
					aria-pressed={value === m.v}
					aria-label="Humor: {m.label}"
					title={m.label}
					onclick={() => onPick(m.v)}
				>
					<m.Icon size={compact ? 20 : 22} />
				</button>
			{/each}
		{:else}
			{#each ENERGY_LABELS as label, i (label)}
				<button
					type="button"
					class="opt energy"
					class:on={value != null && i < value}
					class:picked={value === i + 1}
					aria-pressed={value === i + 1}
					aria-label="Energia: {label}"
					title={label}
					onclick={() => onPick(i + 1)}
				>
					<span class="seg" style="height: {8 + i * 4}px"></span>
				</button>
			{/each}
		{/if}
	</div>
</fieldset>

<style>
	.picker {
		display: flex;
		flex-direction: column;
		gap: 8px;
		min-width: 0;
		border: 0;
		padding: 0;
		margin: 0;
	}
	.legend {
		display: flex;
		width: 100%;
		justify-content: space-between;
		gap: 8px;
		padding: 0;
		margin-bottom: 8px;
		font-size: 13px;
		font-weight: 600;
	}
	.current {
		font-weight: 500;
		color: color-mix(in oklab, var(--color-base-content) 60%, transparent);
	}
	.options {
		display: flex;
		gap: 6px;
	}
	.opt {
		display: flex;
		flex: 1;
		align-items: center;
		justify-content: center;
		min-width: 40px;
		height: 44px;
		border-radius: var(--radius-field);
		background: var(--color-base-100);
		color: color-mix(in oklab, var(--color-base-content) 55%, transparent);
		cursor: pointer;
		transition: background 0.15s ease, color 0.15s ease, transform 0.1s ease;
	}
	.compact .opt {
		height: 40px;
	}
	.opt:hover {
		color: var(--color-base-content);
	}
	.opt:active {
		transform: scale(0.94);
	}
	.opt.on:not(.energy) {
		background: var(--c-journal);
		color: var(--color-base-100);
	}

	.energy {
		align-items: flex-end;
		padding-bottom: 10px;
	}
	.seg {
		width: 10px;
		border-radius: 3px;
		background: var(--color-base-300);
		transition: background 0.15s ease;
	}
	.energy.on .seg {
		background: var(--c-journal);
	}
	.energy.picked {
		outline: 2px solid var(--c-journal);
		outline-offset: -2px;
	}

	.opt:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
