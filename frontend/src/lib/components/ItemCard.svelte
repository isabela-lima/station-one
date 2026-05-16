<script lang="ts">
	import type { Item } from '$lib';
	import { FileText, Link, Trash2, Star } from 'lucide-svelte';

	let {
		item,
		onToggle,
		onDelete,
		onTogglePriority,
		pending = false,
		index = 0
	}: {
		item: Item;
		onToggle: (id: string) => void;
		onDelete: (id: string) => void;
		onTogglePriority?: (id: string) => void;
		pending?: boolean;
		index?: number;
	} = $props();
</script>

<div
	class="card-enter group flex items-start gap-3 rounded-lg px-3 py-2 transition-colors hover:bg-white/[0.03]"
	style="animation-delay: {index * 40}ms"
>
	<!-- Ícone / Checkbox -->
	<div class="mt-0.5 shrink-0">
		{#if item.type === 'task'}
			<input
				type="checkbox"
				class="checkbox checkbox-xs border-white/20 checked:border-primary checked:bg-primary"
				checked={item.completed}
				onchange={() => onToggle(item.id)}
				disabled={pending}
			/>
		{:else if item.type === 'note'}
			<FileText size={13} class="text-primary/50" />
		{:else}
			<Link size={13} class="text-secondary/60" />
		{/if}
	</div>

	<!-- Conteúdo -->
	<div class="min-w-0 flex-1">
		{#if item.type === 'task'}
			<span
				class="text-sm leading-snug"
				class:line-through={item.completed}
				class:opacity-35={item.completed}
			>{item.content}</span>
		{:else if item.type === 'note'}
			<p class="text-sm leading-snug text-base-content/70 whitespace-pre-wrap">{item.content}</p>
		{:else}
			<a
				href={item.content}
				target="_blank"
				rel="noopener noreferrer"
				class="text-sm text-secondary/80 hover:text-secondary underline-offset-2 hover:underline break-all leading-snug"
			>{item.title || item.content}</a>
			{#if item.title}
				<p class="text-[11px] text-base-content/30 truncate mt-0.5">{item.content}</p>
			{/if}
		{/if}
	</div>

	<!-- Ações (aparecem no hover) -->
	<div class="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
		{#if item.type === 'task' && onTogglePriority}
			<button
				onclick={() => onTogglePriority?.(item.id)}
				class="btn btn-ghost btn-xs rounded-full p-1"
				class:text-warning={item.priority}
				class:text-base-content/30={!item.priority}
				title={item.priority ? 'Remover do foco' : 'Foco do dia'}
				disabled={pending}
			>
				<Star size={12} fill={item.priority ? 'currentColor' : 'none'} />
			</button>
		{/if}
		<button
			onclick={() => onDelete(item.id)}
			class="btn btn-ghost btn-xs rounded-full p-1 text-base-content/30 hover:text-error"
			title="Deletar"
			disabled={pending}
		>
			{#if pending}
				<span class="loading loading-xs loading-spinner"></span>
			{:else}
				<Trash2 size={12} />
			{/if}
		</button>
	</div>
</div>
