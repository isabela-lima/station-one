<script lang="ts">
	import type { Goal, Milestone } from '$lib/types';
	import { Target, Flag, Trash2, CheckCircle2, Circle } from 'lucide-svelte';

	let {
		goal,
		milestones,
		onToggleMilestone,
		onDeleteGoal,
		onDeleteMilestone,
		index = 0
	}: {
		goal: Goal;
		milestones: Milestone[];
		onToggleMilestone: (milestoneId: string) => void;
		onDeleteGoal: (goalId: string) => void;
		onDeleteMilestone: (milestoneId: string) => void;
		index?: number;
	} = $props();

	const completedCount = $derived(milestones.filter((m) => m.completed).length);
	const progress = $derived(milestones.length > 0 ? (completedCount / milestones.length) * 100 : 0);
</script>

<div
	class="glass-card card-enter group relative p-4"
	style="animation-delay: {index * 60}ms"
>
	<!-- Goal header -->
	<div class="mb-3 flex items-start justify-between gap-2">
		<div class="flex items-center gap-2">
			<div
				class="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
				style="background: rgba(139,92,246,0.15); border: 1px solid rgba(139,92,246,0.3)"
			>
				<Target size={14} class="text-secondary" />
			</div>
			<h3 class="font-semibold text-base-content">{goal.title}</h3>
		</div>
		<button
			onclick={() => onDeleteGoal(goal.id)}
			class="btn btn-ghost btn-xs text-error/50 hover:text-error rounded-full opacity-0 transition-opacity group-hover:opacity-100"
			title="Deletar missão"
			aria-label="Deletar missão"
		>
			<Trash2 size={13} />
		</button>
	</div>

	<!-- Progress bar -->
	{#if milestones.length > 0}
		<div class="mb-3">
			<div class="mb-1 flex items-center justify-between text-[10px] text-base-content/40">
				<span>{completedCount}/{milestones.length} marcos</span>
				<span>{Math.round(progress)}%</span>
			</div>
			<div class="h-1 w-full overflow-hidden rounded-full" style="background: rgba(255,255,255,0.06)">
				<div
					class="h-full rounded-full transition-all duration-500"
					style="width: {progress}%; background: linear-gradient(90deg, #06b6d4, #8b5cf6)"
				></div>
			</div>
		</div>
	{/if}

	<!-- Milestones -->
	<ul class="space-y-2">
		{#each milestones as milestone (milestone.id)}
			<li class="group/ms flex items-center gap-2">
				<button
					onclick={() => onToggleMilestone(milestone.id)}
					class="shrink-0 text-base-content/30 transition-colors hover:text-primary"
					class:text-primary={milestone.completed}
					aria-label="Alternar marco"
				>
					{#if milestone.completed}
						<CheckCircle2 size={15} />
					{:else}
						<Circle size={15} />
					{/if}
				</button>
				<span
					class="flex-1 text-sm"
					class:line-through={milestone.completed}
					class:opacity-40={milestone.completed}
				>
					{milestone.title}
				</span>
				<button
					onclick={() => onDeleteMilestone(milestone.id)}
					class="btn btn-ghost btn-xs text-error/40 hover:text-error rounded-full opacity-0 transition-opacity group-hover/ms:opacity-100 shrink-0 p-0 w-5 h-5 min-h-0"
					title="Deletar marco"
					aria-label="Deletar marco"
				>
					<Trash2 size={11} />
				</button>
			</li>
		{/each}
		{#if milestones.length === 0}
			<li class="flex items-center gap-2 text-xs text-base-content/30 italic">
				<Flag size={11} />
				<span>Nenhum marco ainda.</span>
			</li>
		{/if}
	</ul>
</div>
