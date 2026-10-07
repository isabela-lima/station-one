<script lang="ts">
	import type { Item } from '$lib';
	import { Check, Trash2, Star, CalendarDays } from 'lucide-svelte';
	import { dueInfo } from '$lib/dates';

	let {
		item,
		onToggle,
		onDelete,
		onTogglePriority,
		missionTitle = null,
		onOpenMission,
		onSetDue,
		pending = false,
		index = 0
	}: {
		item: Item;
		onToggle: (id: string) => void;
		onDelete: (id: string) => void;
		onTogglePriority?: (id: string) => void;
		/** Nome da missão da tarefa, quando houver (mostrado como etiqueta) */
		missionTitle?: string | null;
		onOpenMission?: () => void;
		/** Define/limpa o prazo ("YYYY-MM-DD" ou null) */
		onSetDue?: (id: string, due: string | null) => void;
		pending?: boolean;
		index?: number;
	} = $props();

	const due = $derived(item.due_date && !item.completed ? dueInfo(item.due_date) : null);
	let picker = $state<HTMLInputElement | null>(null);

	function openPicker() {
		if (!picker) return;
		// showPicker abre o calendário nativo; navegadores antigos caem no foco
		if (typeof picker.showPicker === 'function') picker.showPicker();
		else picker.focus();
	}
</script>

<div
	class="row card-enter"
	class:done={item.completed}
	style="animation-delay: {Math.min(index, 10) * 30}ms"
>
	<button
		type="button"
		class="tick"
		aria-pressed={item.completed}
		aria-label={item.completed ? `Desfazer ${item.content}` : `Concluir ${item.content}`}
		aria-busy={pending}
		onclick={() => onToggle(item.id)}
	>
		{#if item.completed}<Check size={13} strokeWidth={3.5} />{/if}
	</button>

	<div class="flex min-w-0 flex-1 flex-col gap-1">
		<span class="text break-words">{item.content}</span>
		{#if due || missionTitle}
			<span class="meta">
				{#if due}
					{#if onSetDue}
						<button
							type="button"
							class="due due-{due.tone}"
							aria-label="Prazo: {due.label}. Alterar"
							onclick={openPicker}>{due.label}</button
						>
					{:else}
						<span class="due due-{due.tone}">{due.label}</span>
					{/if}
				{/if}
				{#if missionTitle}
					{#if onOpenMission}
						<button type="button" class="mission-tag" onclick={onOpenMission}>{missionTitle}</button
						>
					{:else}
						<span class="mission-tag">{missionTitle}</span>
					{/if}
				{/if}
			</span>
		{/if}
	</div>

	{#if onSetDue}
		<input
			bind:this={picker}
			class="picker"
			type="date"
			tabindex="-1"
			aria-hidden="true"
			value={item.due_date ?? ''}
			onchange={(e) => onSetDue?.(item.id, e.currentTarget.value || null)}
		/>
	{/if}

	<div class="actions">
		{#if onSetDue && !item.completed}
			<button
				type="button"
				class="icon-btn"
				aria-label={item.due_date ? 'Alterar prazo' : 'Definir prazo'}
				onclick={openPicker}
			>
				<CalendarDays size={16} />
			</button>
		{/if}
		{#if onTogglePriority}
			<button
				type="button"
				class="icon-btn"
				class:starred={item.priority}
				aria-pressed={item.priority}
				aria-label={item.priority ? 'Remover do foco' : 'Marcar como foco'}
				onclick={() => onTogglePriority?.(item.id)}
			>
				<Star size={16} fill={item.priority ? 'currentColor' : 'none'} />
			</button>
		{/if}
		<button
			type="button"
			class="icon-btn danger"
			aria-label="Apagar {item.content}"
			onclick={() => onDelete(item.id)}
		>
			<Trash2 size={16} />
		</button>
	</div>
</div>

<style>
	.row {
		position: relative;
		display: flex;
		align-items: center;
		gap: 12px;
		min-height: 52px;
		padding: 6px 8px 6px 12px;
		border-radius: var(--radius-field);
		transition: background 0.15s ease;
	}
	.row:hover {
		background: var(--color-base-100);
	}

	.tick {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 24px;
		height: 24px;
		flex-shrink: 0;
		border-radius: 999px;
		border: 2px solid color-mix(in oklab, var(--color-base-content) 40%, transparent);
		cursor: pointer;
		transition:
			border-color 0.15s ease,
			background 0.15s ease;
	}
	.tick:hover {
		border-color: var(--c-ops);
		background: var(--c-ops-soft);
	}
	.done .tick {
		border-color: var(--c-ops);
		background: var(--c-ops);
		color: var(--color-base-100);
	}
	.tick[aria-busy='true'] {
		cursor: progress;
	}

	.text {
		font-size: 15px;
		line-height: 1.35;
		transition: color 0.2s ease;
	}
	.done .text {
		text-decoration: line-through;
		color: color-mix(in oklab, var(--color-base-content) 50%, transparent);
	}

	.meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px;
	}
	.due {
		padding: 3px 8px;
		border-radius: var(--radius-selector);
		font-size: 12px;
		font-weight: 700;
		line-height: 1.2;
	}
	button.due {
		cursor: pointer;
	}
	.due-overdue {
		background: color-mix(in oklab, var(--color-error) 16%, transparent);
		color: var(--color-error);
	}
	.due-today {
		background: var(--c-protocols-soft);
		color: var(--c-protocols-ink);
	}
	.due-soon {
		background: var(--c-ops-soft);
		color: var(--c-ops-ink);
	}
	.due-later {
		background: var(--color-base-300);
		color: color-mix(in oklab, var(--color-base-content) 75%, transparent);
	}
	/* Input nativo de data, invisível: só serve para abrir o calendário */
	.picker {
		position: absolute;
		width: 1px;
		height: 1px;
		opacity: 0;
		pointer-events: none;
	}

	.mission-tag {
		align-self: flex-start;
		padding: 3px 8px;
		border-radius: var(--radius-selector);
		background: var(--c-missions-soft);
		color: var(--c-missions-ink);
		font-size: 12px;
		font-weight: 600;
		line-height: 1.2;
	}
	button.mission-tag {
		cursor: pointer;
	}
	button.mission-tag:hover {
		text-decoration: underline;
	}

	.actions {
		display: flex;
		align-items: center;
		gap: 2px;
		flex-shrink: 0;
	}
	/* Em telas com mouse, as ações aparecem no hover; no toque, ficam sempre visíveis */
	@media (hover: hover) {
		.actions {
			opacity: 0;
			transition: opacity 0.15s ease;
		}
		.row:hover .actions,
		.row:focus-within .actions {
			opacity: 1;
		}
		.actions:has(.starred) {
			opacity: 1;
		}
	}

	.icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		border-radius: 999px;
		color: color-mix(in oklab, var(--color-base-content) 55%, transparent);
		cursor: pointer;
	}
	.icon-btn:hover {
		background: var(--color-base-300);
		color: var(--color-base-content);
	}
	.icon-btn.starred {
		color: var(--c-protocols);
	}
	.icon-btn.danger:hover {
		color: var(--color-error);
	}

	button:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
