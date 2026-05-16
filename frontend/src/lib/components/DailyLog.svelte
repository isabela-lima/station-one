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

	const todayLabel = new Date().toLocaleDateString('pt-BR', {
		weekday: 'long',
		day: 'numeric',
		month: 'long'
	});

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

<section class="px-8 pb-2">
	<div class="daily-log-container rounded-xl p-4" style="background: rgba(255,255,255,0.025); border: 1px solid rgba(6,182,212,0.12)">

		<!-- Header -->
		<div class="mb-3 flex items-center justify-between">
			<div class="flex items-center gap-2">
				<BookOpen size={13} class="text-primary/60" />
				<span class="text-[10px] font-semibold uppercase tracking-widest text-primary/50">
					Log da Estação
				</span>
				<span class="text-[10px] text-base-content/25 capitalize">{todayLabel}</span>
			</div>
			<div class="flex items-center gap-1.5 h-4">
				{#if saving}
					<span class="text-[9px] uppercase tracking-widest text-base-content/25 animate-pulse">salvando...</span>
				{:else if saved}
					<Save size={10} class="text-success/60" />
					<span class="text-[9px] uppercase tracking-widest text-success/50">salvo</span>
				{/if}
			</div>
		</div>

		<!-- Textarea -->
		{#if loading}
			<div class="skeleton-pulse h-14 w-full rounded-lg"></div>
		{:else}
			<textarea
				bind:value={content}
				oninput={handleInput}
				placeholder="O que aconteceu hoje, Comandante?"
				class="daily-log-textarea w-full resize-none bg-transparent text-sm leading-relaxed text-base-content/70 placeholder:text-base-content/20 outline-none"
				rows={3}
			></textarea>
		{/if}
	</div>
</section>

<style>
	.daily-log-container {
		transition: border-color 0.2s ease;
	}
	.daily-log-container:focus-within {
		border-color: rgba(6, 182, 212, 0.28);
		background: rgba(255, 255, 255, 0.035) !important;
	}
	.daily-log-textarea {
		font-family: inherit;
		caret-color: #06b6d4;
	}
</style>
