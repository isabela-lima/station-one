<script lang="ts">
	import { Plus, X } from 'lucide-svelte';
	import AddForm from './AddForm.svelte';
	import type { Goal } from '$lib';
	import type { Section, FormType, FormPayload } from '$lib/components/dashboard';

	let {
		show = $bindable<boolean>(),
		activeSection,
		selectedType = $bindable<FormType>(),
		goals,
		onSubmit
	}: {
		show: boolean;
		activeSection: Section;
		selectedType: FormType;
		goals: Goal[];
		onSubmit: (payload: FormPayload) => Promise<void>;
	} = $props();

	async function handleSubmit(payload: FormPayload) {
		await onSubmit(payload);
		show = false;
	}

	const formTitle = $derived(
		activeSection === 'operations' ? 'Nova Operação'
		: activeSection === 'missions' ? 'Nova Missão'
		: 'Adicionar à Wishlist'
	);
</script>

{#if show}
	<!-- Backdrop -->
	<div
		class="lg:hidden fixed inset-0 z-40"
		style="background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);"
		onclick={() => (show = false)}
		role="button"
		tabindex="-1"
		aria-label="Fechar"
	></div>

	<!-- Sheet -->
	<div
		class="lg:hidden fixed bottom-0 left-0 right-0 z-50 rounded-t-2xl flex flex-col"
		style="background: #0f0f1c; border-top: 1px solid rgba(6,182,212,0.2); max-height: 85vh;"
	>
		<!-- Handle -->
		<div class="flex justify-center pt-3 pb-1">
			<div class="w-10 h-1 rounded-full" style="background: rgba(6,182,212,0.25)"></div>
		</div>

		<!-- Header -->
		<div class="flex items-center justify-between px-5 pt-2 pb-4">
			<div class="flex items-center gap-2">
				<Plus size={14} class="text-primary/60" />
				<span class="text-xs font-semibold uppercase tracking-widest text-base-content/50">{formTitle}</span>
			</div>
			<button
				onclick={() => (show = false)}
				class="btn btn-ghost btn-sm btn-circle text-base-content/40"
				aria-label="Fechar"
			>
				<X size={16} />
			</button>
		</div>

		<!-- Form -->
		<div class="overflow-y-auto px-5 pb-8">
			<AddForm {activeSection} {goals} bind:selectedType onSubmit={handleSubmit} />
		</div>
	</div>
{/if}
