<script lang="ts">
	import type { Item } from '$lib/types';
	import { FileText, CheckSquare, Link, Trash2, Star } from 'lucide-svelte';

	let {
		item,
		onToggle,
		onDelete,
		onTogglePriority,
		index = 0
	}: {
		item: Item;
		onToggle: (id: string) => void;
		onDelete: (id: string) => void;
		onTogglePriority?: (id: string) => void;
		index?: number;
	} = $props();

	const typeConfig = {
		note: { label: 'Nota', color: 'text-primary', bg: 'rgba(6,182,212,0.12)', border: 'rgba(6,182,212,0.3)' },
		task: { label: 'Tarefa', color: 'text-success', bg: 'rgba(52,211,153,0.12)', border: 'rgba(52,211,153,0.3)' },
		link: { label: 'Link', color: 'text-secondary', bg: 'rgba(139,92,246,0.12)', border: 'rgba(139,92,246,0.3)' }
	};

	const cfg = $derived(typeConfig[item.type]);
</script>

<div
	class="glass-card card-enter group relative p-4"
	style="animation-delay: {index * 50}ms"
>
	<!-- Header row: badge + priority + delete -->
	<div class="mb-2 flex items-center justify-between gap-2">
		<div class="flex items-center gap-2">
			<span
				class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide"
				style="background: {cfg.bg}; color: {cfg.border}; border: 1px solid {cfg.border}"
			>
				{#if item.type === 'note'}
					<FileText size={10} />
				{:else if item.type === 'task'}
					<CheckSquare size={10} />
				{:else}
					<Link size={10} />
				{/if}
				{cfg.label}
			</span>

			{#if item.priority}
				<span class="text-warning" title="Foco do dia">
					<Star size={13} fill="currentColor" />
				</span>
			{/if}
		</div>

		<div class="flex items-center gap-1 opacity-0 transition-opacity duration-150 group-hover:opacity-100">
			{#if item.type === 'task' && onTogglePriority}
				<button
					onclick={() => onTogglePriority?.(item.id)}
					class="btn btn-ghost btn-xs rounded-full"
					class:text-warning={item.priority}
					class:text-base-content={!item.priority}
					title={item.priority ? 'Remover do foco' : 'Marcar como foco'}
					aria-label="Alternar foco"
				>
					<Star size={13} fill={item.priority ? 'currentColor' : 'none'} />
				</button>
			{/if}
			<button
				onclick={() => onDelete(item.id)}
				class="btn btn-ghost btn-xs text-error/60 hover:text-error rounded-full"
				title="Deletar"
				aria-label="Deletar item"
			>
				<Trash2 size={13} />
			</button>
		</div>
	</div>

	<!-- Content -->
	{#if item.type === 'note'}
		<p class="whitespace-pre-wrap text-sm leading-relaxed text-base-content/80">{item.content}</p>
	{:else if item.type === 'task'}
		<label class="flex cursor-pointer items-start gap-3">
			<input
				type="checkbox"
				class="checkbox checkbox-sm mt-0.5 border-primary/40 checked:border-primary checked:bg-primary"
				checked={item.completed}
				onchange={() => onToggle(item.id)}
			/>
			<span
				class="text-sm leading-relaxed"
				class:line-through={item.completed}
				class:opacity-40={item.completed}
			>
				{item.content}
			</span>
		</label>
	{:else if item.type === 'link'}
		<a
			href={item.content}
			target="_blank"
			rel="noopener noreferrer"
			class="group/link flex items-start gap-2 text-sm"
		>
			<Link size={14} class="mt-0.5 shrink-0 text-secondary/70" />
			<span class="text-secondary/90 underline-offset-2 group-hover/link:text-secondary group-hover/link:underline break-all">
				{item.title || item.content}
			</span>
		</a>
		{#if item.title}
			<p class="mt-1 truncate text-xs text-base-content/40">{item.content}</p>
		{/if}
	{/if}
</div>
