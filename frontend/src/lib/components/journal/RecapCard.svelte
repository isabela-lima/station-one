<script lang="ts">
	import { CheckCircle2, Flame, Wallet } from 'lucide-svelte';
	import type { Recap } from '$lib/models/types';

	let { recap, title = 'Resumo do dia' }: { recap: Recap; title?: string } = $props();

	const empty = $derived(
		recap.tasks_done.length === 0 &&
			recap.habits_done.length === 0 &&
			recap.spent === 0 &&
			recap.income === 0
	);

	function brl(v: number) {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v);
	}
</script>

<section class="recap" aria-label={title}>
	<h3 class="font-display text-base">{title}</h3>
	{#if empty}
		<p class="muted">
			Nada registrado ainda. Conclua tarefas, marque protocolos ou lance gastos e eles aparecem
			aqui.
		</p>
	{:else}
		<ul class="lines">
			{#if recap.tasks_done.length > 0}
				<li>
					<CheckCircle2 size={17} style="color: var(--c-ops)" />
					<div class="min-w-0">
						<strong
							>{recap.tasks_done.length}
							{recap.tasks_done.length === 1 ? 'tarefa concluída' : 'tarefas concluídas'}</strong
						>
						<span class="detail"
							>{recap.tasks_done.slice(0, 3).join(' · ')}{recap.tasks_done.length > 3
								? ' …'
								: ''}</span
						>
					</div>
				</li>
			{/if}
			{#if recap.habits_done.length > 0}
				<li>
					<Flame size={17} style="color: var(--c-protocols)" />
					<div class="min-w-0">
						<strong
							>{recap.habits_done.length}
							{recap.habits_done.length === 1 ? 'protocolo' : 'protocolos'}</strong
						>
						<span class="detail"
							>{recap.habits_done.map((h) => `${h.emoji} ${h.name}`).join(' · ')}</span
						>
					</div>
				</li>
			{/if}
			{#if recap.spent > 0 || recap.income > 0}
				<li>
					<Wallet size={17} style="color: var(--c-finance)" />
					<div class="min-w-0">
						<strong>
							{#if recap.spent > 0}{brl(recap.spent)} gastos{/if}{#if recap.spent > 0 && recap.income > 0}
								·
							{/if}{#if recap.income > 0}{brl(recap.income)} recebidos{/if}
						</strong>
						{#if recap.top_categories.length > 0}
							<span class="detail">{recap.top_categories.map((c) => c.category).join(' · ')}</span>
						{/if}
					</div>
				</li>
			{/if}
		</ul>
	{/if}
</section>

<style>
	.recap {
		display: flex;
		flex-direction: column;
		gap: 12px;
	}
	.muted {
		margin: 0;
		font-size: 14px;
		line-height: 1.5;
		color: color-mix(in oklab, var(--color-base-content) 62%, transparent);
	}
	.lines {
		display: flex;
		flex-direction: column;
		gap: 12px;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.lines li {
		display: flex;
		gap: 10px;
		align-items: flex-start;
		font-size: 14px;
	}
	.lines li > :global(svg) {
		flex-shrink: 0;
		margin-top: 2px;
	}
	.lines strong {
		display: block;
		font-weight: 600;
	}
	.detail {
		display: block;
		margin-top: 2px;
		color: color-mix(in oklab, var(--color-base-content) 62%, transparent);
		overflow-wrap: anywhere;
	}
</style>
