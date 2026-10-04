<script lang="ts">
	import { onMount } from 'svelte';
	import { BookOpen, Save } from 'lucide-svelte';
	import * as api from '$lib/api';

	// ── State ─────────────────────────────────────────────
	let content = $state('');
	let saving = $state(false);
	let saved = $state(false);
	let loading = $state(true);
	let debounceTimer: ReturnType<typeof setTimeout> | null = null;

	const rawLabel = new Date().toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long' });
	const todayLabel = rawLabel.charAt(0).toUpperCase() + rawLabel.slice(1);

	// ── Load today's log ──────────────────────────────────
	onMount(async () => {
		try {
			const log = await api.dailyLogs.today();
			content = log.content;
		} catch {
			// silently ignore — user can still write
		} finally {
			loading = false;
		}
	});

	// ── Auto-save with 1s debounce ────────────────────────
	function handleInput() {
		if (debounceTimer) clearTimeout(debounceTimer);
		saved = false;
		debounceTimer = setTimeout(async () => {
			saving = true;
			try {
				await api.dailyLogs.update(content);
				saved = true;
				setTimeout(() => (saved = false), 2000);
			} catch {
				/* silent — log é decorativo */
			} finally {
				saving = false;
			}
		}, 1000);
	}
</script>

<div class="flex flex-col gap-3">
	<div class="flex items-center justify-between gap-3">
		<h2 class="font-display flex items-center gap-2 text-lg">
			<BookOpen size={18} style="color: var(--sec, var(--color-primary))" />
			Log da estação
		</h2>
		<span class="flex h-4 items-center gap-1.5 text-xs" aria-live="polite">
			{#if saving}
				<span class="text-base-content/60">salvando…</span>
			{:else if saved}
				<Save size={12} class="text-success" />
				<span class="text-success">salvo</span>
			{:else}
				<span class="text-base-content/60">{todayLabel}</span>
			{/if}
		</span>
	</div>

	{#if loading}
		<div class="skeleton-pulse h-28 w-full"></div>
	{:else}
		<label for="daily-log" class="sr-only">Log de hoje</label>
		<textarea
			id="daily-log"
			bind:value={content}
			oninput={handleInput}
			placeholder="O que aconteceu hoje, Comandante?"
			class="daily-log-textarea w-full resize-y text-[15px] leading-relaxed outline-none"
			rows={4}
		></textarea>
	{/if}
</div>

<style>
	.daily-log-textarea {
		font-family: inherit;
		padding: 12px 14px;
		border-radius: var(--radius-field);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
		caret-color: var(--color-primary);
		transition: border-color 0.15s ease;
	}
	.daily-log-textarea::placeholder {
		color: color-mix(in oklab, var(--color-base-content) 45%, transparent);
	}
	.daily-log-textarea:focus {
		border-color: var(--color-primary);
	}
</style>
