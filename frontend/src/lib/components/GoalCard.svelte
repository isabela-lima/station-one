<script lang="ts">
	import type { Goal, Item } from '$lib';
	import { Trash2, Plus } from 'lucide-svelte';
	import ItemCard from './ItemCard.svelte';

	let {
		goal,
		tasks,
		onToggleTask,
		onDeleteTask,
		onTogglePriority,
		onAddTask,
		onDeleteGoal,
		pendingIds = new Set<string>(),
		index = 0
	}: {
		goal: Goal;
		/** Tarefas desta missão */
		tasks: Item[];
		onToggleTask: (id: string) => void;
		onDeleteTask: (id: string) => void;
		onTogglePriority: (id: string) => void;
		onAddTask: (goalId: string, content: string) => Promise<void>;
		onDeleteGoal: (goalId: string) => void;
		pendingIds?: Set<string>;
		index?: number;
	} = $props();

	const doneCount = $derived(tasks.filter((t) => t.completed).length);
	const progress = $derived(tasks.length > 0 ? (doneCount / tasks.length) * 100 : 0);
	// Pendentes primeiro, concluídas no fim
	const ordered = $derived([...tasks].sort((a, b) => Number(a.completed) - Number(b.completed)));

	let draft = $state('');
	let adding = $state(false);

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		const content = draft.trim();
		if (!content || adding) return;
		adding = true;
		try {
			await onAddTask(goal.id, content);
			draft = '';
		} finally {
			adding = false;
		}
	}
</script>

<article
	class="mission card-enter"
	style="animation-delay: {Math.min(index, 8) * 50}ms"
	aria-labelledby="goal-{goal.id}"
>
	<header class="flex items-start justify-between gap-3">
		<div class="flex min-w-0 flex-col gap-1">
			<h3 id="goal-{goal.id}" class="font-display text-lg break-words">{goal.title}</h3>
			<span class="text-sm text-base-content/65">
				{#if tasks.length === 0}Nenhuma tarefa ainda{:else}{doneCount} de {tasks.length} tarefas · {Math.round(
						progress
					)}%{/if}
			</span>
		</div>
		<button
			type="button"
			class="icon-btn"
			aria-label="Apagar missão {goal.title}"
			title="Apagar missão (as tarefas continuam, sem missão)"
			disabled={pendingIds.has(goal.id)}
			onclick={() => onDeleteGoal(goal.id)}
		>
			<Trash2 size={16} />
		</button>
	</header>

	<div
		class="bar"
		role="progressbar"
		aria-valuenow={Math.round(progress)}
		aria-valuemin={0}
		aria-valuemax={100}
		aria-label="Progresso de {goal.title}"
	>
		<div class="bar-fill" style="width: {progress}%"></div>
	</div>

	{#if ordered.length > 0}
		<div class="flex flex-col">
			{#each ordered as task, i (task.id)}
				<ItemCard
					item={task}
					index={i}
					pending={pendingIds.has(task.id)}
					onToggle={onToggleTask}
					onDelete={onDeleteTask}
					{onTogglePriority}
				/>
			{/each}
		</div>
	{/if}

	<form class="add" onsubmit={submit}>
		<label class="sr-only" for="add-{goal.id}">Nova tarefa em {goal.title}</label>
		<input
			id="add-{goal.id}"
			type="text"
			placeholder="Adicionar tarefa…"
			bind:value={draft}
			autocomplete="off"
		/>
		<button
			type="submit"
			class="add-btn"
			aria-label="Adicionar tarefa"
			disabled={!draft.trim() || adding}
		>
			<Plus size={18} />
		</button>
	</form>
</article>

<style>
	.mission {
		display: flex;
		flex-direction: column;
		gap: 14px;
		padding: 18px;
		border-radius: var(--radius-box);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
	}

	.bar {
		height: 8px;
		border-radius: 999px;
		background: var(--c-missions-soft);
		overflow: hidden;
	}
	.bar-fill {
		height: 100%;
		border-radius: 999px;
		background: var(--c-missions);
		transition: width 0.3s ease;
	}

	.add {
		display: flex;
		gap: 8px;
	}
	.add input {
		flex: 1;
		min-width: 0;
		min-height: 44px;
		padding: 0 14px;
		border-radius: var(--radius-field);
		background: var(--color-base-200);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
		font-size: 15px;
		outline: none;
	}
	.add input::placeholder {
		color: color-mix(in oklab, var(--color-base-content) 45%, transparent);
	}
	.add input:focus {
		border-color: var(--c-missions);
	}
	.add-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 44px;
		height: 44px;
		flex-shrink: 0;
		border-radius: var(--radius-field);
		background: var(--c-missions);
		color: var(--color-base-100);
		cursor: pointer;
	}
	.add-btn:disabled {
		opacity: 0.35;
		cursor: default;
	}

	.icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		flex-shrink: 0;
		border-radius: 999px;
		color: color-mix(in oklab, var(--color-base-content) 55%, transparent);
		cursor: pointer;
	}
	.icon-btn:hover {
		background: var(--color-base-300);
		color: var(--color-error);
	}

	button:focus-visible,
	input:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
