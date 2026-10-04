<script lang="ts">
	import type { Item } from '$lib';
	import { Check, Trash2, Star } from 'lucide-svelte';

	let {
		item,
		onToggle,
		onDelete,
		onTogglePriority,
		missionTitle = null,
		onOpenMission,
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
		pending?: boolean;
		index?: number;
	} = $props();
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
		{#if missionTitle}
			{#if onOpenMission}
				<button type="button" class="mission-tag" onclick={onOpenMission}>{missionTitle}</button>
			{:else}
				<span class="mission-tag">{missionTitle}</span>
			{/if}
		{/if}
	</div>

	<div class="actions">
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
