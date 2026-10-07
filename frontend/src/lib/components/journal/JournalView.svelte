<script lang="ts">
	import { onMount } from 'svelte';
	import { ChevronDown, CheckCircle2, Flame, Wallet, MessageSquare } from 'lucide-svelte';
	import * as api from '$lib/api';
	import type { DaySummary, JournalDay } from '$lib/models/types';
	import { journalToday, loadJournalToday, deleteEntry, setCheckin } from '$lib/journal.svelte';
	import CheckinPicker from './CheckinPicker.svelte';
	import EntryComposer from './EntryComposer.svelte';
	import EntryList from './EntryList.svelte';
	import RecapCard from './RecapCard.svelte';

	const PAGE = 14;

	let history = $state<DaySummary[]>([]);
	let historyLoading = $state(true);
	let historyFailed = $state(false);
	let exhausted = $state(false);

	/** Dias abertos no histórico: data → detalhes (null enquanto carrega) */
	let expanded = $state<Record<string, JournalDay | null>>({});

	onMount(() => {
		loadJournalToday(true);
		loadMore();
	});

	async function loadMore() {
		historyLoading = true;
		try {
			const before = history.length > 0 ? history[history.length - 1].date : undefined;
			const page = await api.journal.history({ before, days: PAGE });
			history = [...history, ...page];
			// Para de oferecer "mais" depois de 6 meses
			if (history.length >= 180) exhausted = true;
		} catch {
			historyFailed = true;
		} finally {
			historyLoading = false;
		}
	}

	async function toggleDay(date: string) {
		if (date in expanded) {
			const { [date]: _, ...rest } = expanded;
			expanded = rest;
			return;
		}
		expanded = { ...expanded, [date]: null };
		try {
			const day = await api.journal.day(date);
			if (date in expanded) expanded = { ...expanded, [date]: day };
		} catch {
			const { [date]: _, ...rest } = expanded;
			expanded = rest;
		}
	}

	const hasAnything = (d: DaySummary) =>
		d.mood != null ||
		d.energy != null ||
		d.entries_count > 0 ||
		d.tasks_done > 0 ||
		d.habits_done > 0 ||
		d.spent > 0;

	// Faixa dos últimos 30 dias (mais antigo → mais recente), colorida pelo humor
	const strip = $derived(history.slice(0, 30).reverse());

	function dayLabel(iso: string) {
		const d = new Date(`${iso}T12:00:00`);
		const s = d.toLocaleDateString('pt-BR', { weekday: 'short', day: 'numeric', month: 'short' });
		return s.charAt(0).toUpperCase() + s.slice(1);
	}

	function brl(v: number) {
		return new Intl.NumberFormat('pt-BR', {
			style: 'currency',
			currency: 'BRL',
			maximumFractionDigits: 0
		}).format(v);
	}

	const MOOD_WORD = ['péssimo', 'ruim', 'ok', 'bom', 'ótimo'];
</script>

<div class="journal">
	<!-- ── Hoje ─────────────────────────────────────────── -->
	<div class="today">
		<div class="flex flex-col gap-5">
			{#if journalToday.day}
				<div class="checkins">
					<CheckinPicker
						kind="mood"
						value={journalToday.day.mood}
						onPick={(v) => setCheckin('mood', v)}
					/>
					<CheckinPicker
						kind="energy"
						value={journalToday.day.energy}
						onPick={(v) => setCheckin('energy', v)}
					/>
				</div>
			{/if}

			<EntryComposer disabled={!journalToday.day} />

			{#if journalToday.loading}
				<div class="skeleton-pulse h-24"></div>
			{:else if journalToday.failed}
				<p class="muted">Não foi possível carregar o diário de hoje.</p>
			{:else if journalToday.day && journalToday.day.entries.length > 0}
				<EntryList entries={journalToday.day.entries} onDelete={deleteEntry} />
			{:else}
				<p class="muted">
					Nada registrado hoje. Anote o que está acontecendo, uma ideia, um link: cada entrada fica
					com a hora.
				</p>
			{/if}
		</div>

		{#if journalToday.day}
			<aside class="recap-box">
				<RecapCard recap={journalToday.day.recap} title="Até agora, hoje" />
			</aside>
		{/if}
	</div>

	<!-- ── Histórico ────────────────────────────────────── -->
	<section class="flex flex-col gap-4" aria-labelledby="hist-title">
		<div class="flex flex-wrap items-end justify-between gap-3">
			<h2 id="hist-title" class="font-display text-xl">Dias anteriores</h2>
			{#if strip.length > 0}
				<div class="strip" aria-label="Humor nos últimos {strip.length} dias">
					{#each strip as d (d.date)}
						<span
							class="cell"
							style="--lvl: {d.mood ?? 0}"
							class:none={d.mood == null}
							title="{dayLabel(d.date)}: {d.mood ? MOOD_WORD[d.mood - 1] : 'sem registro'}"
						></span>
					{/each}
				</div>
			{/if}
		</div>

		{#if historyFailed && history.length === 0}
			<p class="muted">Não foi possível carregar o histórico.</p>
		{/if}

		<ul class="days">
			{#each history as d (d.date)}
				{#if hasAnything(d)}
					<li class="day">
						<button
							type="button"
							class="day-head"
							aria-expanded={d.date in expanded}
							onclick={() => toggleDay(d.date)}
						>
							<span class="flex min-w-0 flex-1 flex-col gap-1 text-left">
								<span class="font-semibold"
									>{dayLabel(d.date)}{#if d.mood}
										· {MOOD_WORD[d.mood - 1]}{/if}</span
								>
								{#if d.first_entry}<span class="first">“{d.first_entry}”</span>{/if}
								<span class="chips">
									{#if d.entries_count > 0}<span><MessageSquare size={13} />{d.entries_count}</span
										>{/if}
									{#if d.tasks_done > 0}<span><CheckCircle2 size={13} />{d.tasks_done}</span>{/if}
									{#if d.habits_done > 0}<span><Flame size={13} />{d.habits_done}</span>{/if}
									{#if d.spent > 0}<span><Wallet size={13} />{brl(d.spent)}</span>{/if}
								</span>
							</span>
							<ChevronDown size={18} class="chev {d.date in expanded ? 'open' : ''}" />
						</button>

						{#if d.date in expanded}
							<div class="day-body">
								{#if expanded[d.date] === null}
									<div class="skeleton-pulse h-16"></div>
								{:else if expanded[d.date]}
									{@const full = expanded[d.date]!}
									{#if full.entries.length > 0}
										<EntryList entries={[...full.entries]} />
									{/if}
									<RecapCard recap={full.recap} />
								{/if}
							</div>
						{/if}
					</li>
				{/if}
			{/each}
		</ul>

		{#if history.length > 0 && !history.some(hasAnything)}
			<p class="muted">Nenhum registro nos últimos {history.length} dias.</p>
		{/if}

		{#if historyLoading}
			<div class="skeleton-pulse h-16"></div>
		{:else if !exhausted && !historyFailed}
			<button type="button" class="more" onclick={loadMore}>Carregar mais {PAGE} dias</button>
		{/if}
	</section>
</div>

<style>
	.journal {
		display: flex;
		flex-direction: column;
		gap: 36px;
	}

	.today {
		display: flex;
		flex-wrap: wrap;
		gap: 28px;
		align-items: flex-start;
	}
	.today > :first-child {
		flex: 999 1 420px;
		min-width: 0;
	}
	.recap-box {
		flex: 1 1 260px;
		padding: 18px;
		border-radius: var(--radius-box);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
	}

	.checkins {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 20px;
	}

	.muted {
		margin: 0;
		font-size: 14px;
		line-height: 1.5;
		color: color-mix(in oklab, var(--color-base-content) 62%, transparent);
	}

	/* Faixa de humor */
	.strip {
		display: flex;
		gap: 3px;
		flex-wrap: wrap;
	}
	.cell {
		width: 12px;
		height: 12px;
		border-radius: 3px;
		background: color-mix(in oklab, var(--c-journal) calc(var(--lvl) * 20%), var(--color-base-300));
	}
	.cell.none {
		background: var(--color-base-300);
		opacity: 0.6;
	}

	/* Lista de dias */
	.days {
		display: flex;
		flex-direction: column;
		gap: 8px;
		list-style: none;
		margin: 0;
		padding: 0;
	}
	.day {
		border-radius: var(--radius-box);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
		overflow: hidden;
	}
	.day-head {
		display: flex;
		width: 100%;
		align-items: center;
		gap: 12px;
		min-height: 56px;
		padding: 12px 16px;
		cursor: pointer;
		font-size: 15px;
	}
	.day-head:hover {
		background: color-mix(in oklab, var(--color-base-content) 3%, transparent);
	}
	.first {
		font-size: 14px;
		color: color-mix(in oklab, var(--color-base-content) 70%, transparent);
		overflow: hidden;
		text-overflow: ellipsis;
		white-space: nowrap;
	}
	.chips {
		display: flex;
		flex-wrap: wrap;
		gap: 12px;
		font-size: 13px;
		color: color-mix(in oklab, var(--color-base-content) 62%, transparent);
	}
	.chips span {
		display: inline-flex;
		align-items: center;
		gap: 4px;
	}
	.day-head :global(.chev) {
		flex-shrink: 0;
		transition: transform 0.2s ease;
		color: color-mix(in oklab, var(--color-base-content) 55%, transparent);
	}
	.day-head :global(.chev.open) {
		transform: rotate(180deg);
	}
	.day-body {
		display: flex;
		flex-direction: column;
		gap: 16px;
		padding: 4px 16px 16px;
	}

	.more {
		align-self: flex-start;
		min-height: 44px;
		padding: 0 16px;
		border-radius: var(--radius-selector);
		background: var(--c-journal-soft);
		color: var(--c-journal-ink);
		font-weight: 600;
		font-size: 14px;
		cursor: pointer;
	}

	.day-head:focus-visible,
	.more:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: -2px;
	}
</style>
