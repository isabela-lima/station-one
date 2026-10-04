<script lang="ts">
	import { ExternalLink, Trash2 } from 'lucide-svelte';
	import type { LogEntry } from '$lib/models/types';
	import { entryTime } from '$lib/journal.svelte';

	let {
		entries,
		onDelete,
		limit
	}: {
		entries: LogEntry[];
		onDelete?: (id: string) => void;
		limit?: number;
	} = $props();

	const shown = $derived(limit ? entries.slice(0, limit) : entries);

	function hostOf(url: string) {
		try {
			return new URL(url).hostname.replace(/^www\./, '');
		} catch {
			return url;
		}
	}
</script>

<ol class="timeline">
	{#each shown as e (e.id)}
		<li class="entry" class:saving={e.id.startsWith('temp-')}>
			<time class="time font-mono-num" datetime={e.created_at}>{entryTime(e.created_at)}</time>
			<div class="flex min-w-0 flex-1 flex-col gap-1">
				<p class="content">{e.content}</p>
				{#if e.url}
					<a class="link" href={e.url} target="_blank" rel="noopener noreferrer">
						<ExternalLink size={13} />{hostOf(e.url)}
					</a>
				{/if}
			</div>
			{#if onDelete && !e.id.startsWith('temp-')}
				<button type="button" class="del" aria-label="Apagar entrada das {entryTime(e.created_at)}" onclick={() => onDelete?.(e.id)}>
					<Trash2 size={15} />
				</button>
			{/if}
		</li>
	{/each}
</ol>

<style>
	.timeline {
		display: flex;
		flex-direction: column;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.entry {
		position: relative;
		display: flex;
		align-items: flex-start;
		gap: 14px;
		padding: 10px 4px 10px 0;
		border-top: 1px solid var(--color-base-300);
	}
	.entry:first-child {
		border-top: 0;
	}
	.entry.saving {
		opacity: 0.6;
	}
	.time {
		flex-shrink: 0;
		width: 44px;
		padding-top: 2px;
		font-size: 13px;
		color: var(--c-journal-ink);
	}
	.content {
		margin: 0;
		font-size: 15px;
		line-height: 1.45;
		white-space: pre-wrap;
		overflow-wrap: anywhere;
	}
	.link {
		display: inline-flex;
		align-items: center;
		gap: 5px;
		align-self: flex-start;
		font-size: 13px;
		color: var(--color-primary);
		text-decoration: none;
	}
	.link:hover {
		text-decoration: underline;
	}
	.del {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 36px;
		height: 36px;
		margin-top: -6px;
		flex-shrink: 0;
		border-radius: 999px;
		color: color-mix(in oklab, var(--color-base-content) 50%, transparent);
		cursor: pointer;
	}
	.del:hover {
		background: var(--color-base-300);
		color: var(--color-error);
	}
	@media (hover: hover) {
		.del {
			opacity: 0;
		}
		.entry:hover .del,
		.del:focus-visible {
			opacity: 1;
		}
	}
	.del:focus-visible,
	.link:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
