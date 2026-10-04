<script lang="ts">
	import { Flame, Trash2, Check } from 'lucide-svelte';
	import type { Habit } from '$lib';

	let {
		habit,
		pending = false,
		onToggle,
		onDelete
	}: {
		habit: Habit;
		pending?: boolean;
		onToggle: (id: string) => void;
		onDelete: (id: string) => void;
	} = $props();
</script>

<div
	class="habit-card glass-card flex items-center gap-4 rounded-xl p-4 transition-all duration-200"
	class:completed={habit.completed_today}
>
	<!-- Emoji + Toggle button -->
	<button
		onclick={() => onToggle(habit.id)}
		disabled={pending}
		class="habit-toggle relative flex h-14 w-14 shrink-0 items-center justify-center rounded-xl text-2xl transition-all duration-200 select-none"
		class:done={habit.completed_today}
		aria-label={habit.completed_today ? 'Desmarcar hábito' : 'Marcar hábito como feito'}
	>
		<span class="emoji leading-none">{habit.emoji}</span>
		{#if habit.completed_today}
			<div class="check-overlay absolute inset-0 flex items-center justify-center rounded-xl">
				<Check size={20} class="text-success" strokeWidth={3} />
			</div>
		{/if}
	</button>

	<!-- Info -->
	<div class="min-w-0 flex-1">
		<p
			class="truncate text-sm leading-tight font-semibold"
			class:line-through={habit.completed_today}
			class:opacity-50={habit.completed_today}
		>
			{habit.name}
		</p>
		<div class="mt-1 flex items-center gap-1.5">
			{#if habit.streak > 0}
				<span class="streak-badge flex items-center gap-1 text-[10px] font-bold">
					<Flame size={11} class="text-orange-400" fill="currentColor" />
					{habit.streak}
					{habit.streak === 1 ? 'dia' : 'dias'}
				</span>
			{:else}
				<span class="text-[10px] text-base-content/25">Nenhum streak ainda</span>
			{/if}
		</div>
	</div>

	<!-- Delete -->
	<button
		onclick={() => onDelete(habit.id)}
		disabled={pending}
		class="btn text-base-content/20 btn-ghost transition-colors btn-xs hover:text-error"
		aria-label="Remover hábito"
	>
		<Trash2 size={13} />
	</button>
</div>

<style>
	.habit-card {
		animation: fadeSlideIn 0.3s ease both;
	}

	.habit-toggle {
		background: color-mix(in oklab, var(--color-base-content) 4%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-primary) 15%, transparent);
	}

	.habit-toggle:hover:not(:disabled) {
		background: color-mix(in oklab, var(--color-primary) 8%, transparent);
		border-color: color-mix(in oklab, var(--color-primary) 30%, transparent);
		transform: scale(1.05);
	}

	.habit-toggle.done {
		background: color-mix(in oklab, var(--color-success) 8%, transparent);
		border-color: color-mix(in oklab, var(--color-success) 30%, transparent);
	}

	.habit-toggle .emoji {
		transition: opacity 0.15s ease;
	}

	.habit-toggle.done .emoji {
		opacity: 0.3;
	}

	.check-overlay {
		background: color-mix(in oklab, var(--color-success) 10%, transparent);
		animation: fadeSlideIn 0.2s ease both;
	}

	.streak-badge {
		padding: 1px 6px;
		border-radius: 999px;
		background: color-mix(in oklab, var(--c-protocols) 10%, transparent);
		border: 1px solid color-mix(in oklab, var(--c-protocols) 20%, transparent);
		color: var(--c-protocols);
	}

	.habit-card.completed {
		border-color: color-mix(in oklab, var(--color-success) 15%, transparent);
		background: color-mix(in oklab, var(--color-success) 2%, transparent);
	}
</style>
