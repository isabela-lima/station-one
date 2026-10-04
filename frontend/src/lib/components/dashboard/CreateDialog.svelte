<script lang="ts">
	import { X } from 'lucide-svelte';
	import AddForm from './AddForm.svelte';
	import type { Goal } from '$lib';
	import { SECTIONS, type CreatableSection, type FormType, type FormPayload } from './types';

	let {
		open = $bindable<boolean>(),
		kind = $bindable<CreatableSection>(),
		selectedType = $bindable<FormType>(),
		goals,
		onSubmit
	}: {
		open: boolean;
		kind: CreatableSection;
		selectedType: FormType;
		goals: Goal[];
		onSubmit: (payload: FormPayload) => Promise<void>;
	} = $props();

	const KINDS = SECTIONS.filter((s) => s.id !== 'today') as unknown as {
		id: CreatableSection;
		label: string;
		color: string;
	}[];

	const TITLES: Record<CreatableSection, string> = {
		operations: 'Nova operação',
		missions: 'Nova missão',
		protocols: 'Novo protocolo',
		finance: 'Nova transação',
		wishlist: 'Adicionar à wishlist'
	};

	const DEFAULT_TYPE: Record<CreatableSection, FormType> = {
		operations: 'task',
		missions: 'goal',
		protocols: 'habit',
		finance: 'transaction',
		wishlist: 'wishlist'
	};

	let dialog = $state<HTMLDialogElement | null>(null);

	// Sincroniza o <dialog> nativo com a prop `open`
	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) dialog.showModal();
		else if (!open && dialog.open) dialog.close();
	});

	function pick(k: CreatableSection) {
		kind = k;
		selectedType = DEFAULT_TYPE[k];
	}

	async function handleSubmit(payload: FormPayload) {
		await onSubmit(payload);
		open = false;
	}
</script>

<dialog
	bind:this={dialog}
	class="create-dialog"
	aria-labelledby="create-title"
	onclose={() => (open = false)}
	onclick={(e) => {
		// clique no backdrop fecha
		if (e.target === dialog) open = false;
	}}
>
	<div class="panel">
		<div class="flex items-center justify-between gap-3">
			<h2 id="create-title" class="font-display text-xl">{TITLES[kind]}</h2>
			<button type="button" class="close-btn" aria-label="Fechar" onclick={() => (open = false)}>
				<X size={18} />
			</button>
		</div>

		<div class="kinds" role="radiogroup" aria-label="O que criar">
			{#each KINDS as k (k.id)}
				<button
					type="button"
					role="radio"
					aria-checked={kind === k.id}
					class="kind sec-{k.color}"
					class:active={kind === k.id}
					onclick={() => pick(k.id)}
				>
					{k.label}
				</button>
			{/each}
		</div>

		{#key kind}
			<AddForm activeSection={kind} {goals} bind:selectedType onSubmit={handleSubmit} />
		{/key}
	</div>
</dialog>

<style>
	.create-dialog {
		margin: auto;
		padding: 0;
		border: none;
		background: transparent;
		color: inherit;
		width: min(520px, calc(100vw - 32px));
		max-height: calc(100vh - 48px);
	}
	.create-dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(3px);
	}

	.panel {
		display: flex;
		flex-direction: column;
		gap: 18px;
		padding: 24px;
		border-radius: var(--tile-radius);
		background: var(--color-base-200);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
	}

	/* No celular vira uma folha presa embaixo */
	@media (max-width: 640px) {
		.create-dialog {
			margin: auto 0 0;
			width: 100vw;
			max-width: 100vw;
			max-height: 88vh;
		}
		.panel {
			border-radius: var(--tile-radius) var(--tile-radius) 0 0;
			padding-bottom: 32px;
		}
	}

	.close-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border-radius: 999px;
		color: color-mix(in oklab, var(--color-base-content) 65%, transparent);
		cursor: pointer;
	}
	.close-btn:hover {
		background: var(--color-base-300);
		color: var(--color-base-content);
	}

	.kinds {
		display: flex;
		flex-wrap: wrap;
		gap: 6px;
	}
	.kind {
		min-height: 36px;
		padding: 0 12px;
		border-radius: var(--radius-selector);
		background: var(--sec-soft);
		color: var(--sec-ink);
		font: 600 13px/1 var(--font-body);
		cursor: pointer;
	}
	.kind.active {
		background: var(--sec);
		color: var(--color-base-100);
	}
	.kind:focus-visible,
	.close-btn:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
