<script lang="ts">
	import { onMount } from 'svelte';
	import { Check, ArrowRight, Star } from 'lucide-svelte';
	import * as api from '$lib/api';
	import type { FinanceOverview, Goal, Habit, Item, Section } from '$lib';
	import JournalTile from '$lib/components/journal/JournalTile.svelte';
	import { compareByUrgency, dueInfo } from '$lib/dates';

	let {
		items,
		habits,
		goals,
		loading,
		pendingIds,
		onToggleItem,
		onToggleHabit,
		onOpenSection
	}: {
		items: Item[];
		habits: Habit[];
		goals: Goal[];
		loading: boolean;
		pendingIds: Set<string>;
		onToggleItem: (id: string) => void;
		onToggleHabit: (id: string) => void;
		onOpenSection: (s: Section) => void;
	} = $props();

	// ─── Operações ────────────────────────────────────
	const tasks = $derived(items.filter((i) => i.type === 'task'));
	const goalTitle = $derived(new Map(goals.map((g) => [g.id, g.title])));
	// Tarefas concluídas aqui continuam visíveis (riscadas) até sair da tela,
	// para dar para ver o que foi feito e desfazer um clique errado.
	let justDone = $state<Set<string>>(new Set());
	function toggleTask(id: string, completed: boolean) {
		const next = new Set(justDone);
		if (completed) next.delete(id);
		else next.add(id);
		justDone = next;
		onToggleItem(id);
	}
	const openTasks = $derived(
		tasks
			.filter((t) => !t.completed || justDone.has(t.id))
			.sort(compareByUrgency)
			.slice(0, 6)
	);
	const doneCount = $derived(tasks.filter((t) => t.completed).length);

	// ─── Protocolos ───────────────────────────────────
	const habitsDone = $derived(habits.filter((h) => h.completed_today).length);

	// ─── Missões ──────────────────────────────────────
	const missionProgress = $derived(
		goals.slice(0, 4).map((g) => {
			const own = tasks.filter((t) => t.goal_id === g.id);
			const done = own.filter((t) => t.completed).length;
			return { goal: g, done, total: own.length, pct: own.length ? (done / own.length) * 100 : 0 };
		})
	);

	// ─── Finanças (carrega por conta própria) ─────────
	let finance = $state<FinanceOverview | null>(null);
	let financeFailed = $state(false);

	onMount(async () => {
		try {
			finance = await api.finance.overview();
		} catch {
			financeFailed = true;
		}
	});

	function brl(value: number, currency = 'BRL') {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(value);
	}
</script>

<div class="today-grid">
	<div class="today-col">
		<!-- ── Operações ──────────────────────────────────── -->
		<section class="tile sec-ops ops-tile flex flex-col gap-4" aria-labelledby="t-ops">
			<div class="tile-head">
				<h2 id="t-ops" class="font-display text-xl">Operações</h2>
				<span class="count">{doneCount}/{tasks.length}</span>
			</div>

			{#if loading}
				{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-12"></div>{/each}
			{:else if openTasks.length === 0}
				<p class="empty">Nada pendente. Bom trabalho.</p>
			{:else}
				<ul class="flex flex-col gap-2">
					{#each openTasks as t (t.id)}
						<li class="task" class:done={t.completed}>
							<button
								type="button"
								class="tick"
								aria-label={t.completed ? `Desfazer ${t.content}` : `Concluir ${t.content}`}
								aria-pressed={t.completed}
								aria-busy={pendingIds.has(t.id)}
								onclick={() => toggleTask(t.id, t.completed)}
							>
								{#if t.completed}<Check size={14} strokeWidth={3.5} />{/if}
							</button>
							<span class="flex min-w-0 flex-1 flex-col gap-1">
								<span class="task-text break-words">{t.content}</span>
								{#if (t.due_date && !t.completed) || (t.goal_id && goalTitle.has(t.goal_id))}
									<span class="meta">
										{#if t.due_date && !t.completed}
											{@const due = dueInfo(t.due_date)}
											<span class="due due-{due.tone}">{due.label}</span>
										{/if}
										{#if t.goal_id && goalTitle.has(t.goal_id)}
											<span class="mission-tag">{goalTitle.get(t.goal_id)}</span>
										{/if}
									</span>
								{/if}
							</span>
							{#if t.priority}
								<Star
									size={15}
									fill="currentColor"
									style="color: var(--c-protocols)"
									aria-label="Foco"
								/>
							{/if}
						</li>
					{/each}
				</ul>
			{/if}

			<button type="button" class="more" onclick={() => onOpenSection('operations')}>
				Ver todas <ArrowRight size={15} />
			</button>
		</section>
	</div>

	<div class="today-col">
		<!-- ── Protocolos ─────────────────────────────────── -->
		<section class="tile sec-protocols flex flex-col gap-4" aria-labelledby="t-hab">
			<div class="tile-head">
				<h2 id="t-hab" class="font-display text-xl">Protocolos</h2>
				<span class="count">{habitsDone}/{habits.length} hoje</span>
			</div>
			{#if loading}
				<div class="skeleton-pulse h-24"></div>
			{:else if habits.length === 0}
				<p class="empty">
					Nenhum protocolo ainda.
					<button type="button" class="link-btn" onclick={() => onOpenSection('protocols')}
						>Criar o primeiro</button
					>
				</p>
			{:else}
				<div class="habit-grid">
					{#each habits as h (h.id)}
						<button
							type="button"
							class="habit"
							class:done={h.completed_today}
							aria-pressed={h.completed_today}
							aria-label="{h.name}: {h.streak} {h.streak === 1
								? 'dia'
								: 'dias'} de streak{h.completed_today ? ', feito hoje' : ''}"
							aria-busy={pendingIds.has(h.id)}
							onclick={() => onToggleHabit(h.id)}
						>
							<span class="flex w-full items-center justify-between">
								<span class="streak font-mono-num">{h.streak}</span>
								{#if h.completed_today}<Check size={18} strokeWidth={3} />{:else}<span
										class="emoji"
										aria-hidden="true">{h.emoji}</span
									>{/if}
							</span>
							<span class="habit-name">{h.name}</span>
						</button>
					{/each}
				</div>
			{/if}
		</section>

		<!-- ── Diário ─────────────────────────────────────── -->
		<section class="tile sec-journal" aria-label="Diário de bordo">
			<JournalTile onOpen={() => onOpenSection('journal')} />
		</section>
	</div>

	<div class="today-col">
		<!-- ── Finanças ───────────────────────────────────── -->
		<section class="tile sec-finance flex flex-col gap-4" aria-labelledby="t-fin">
			<div class="tile-head">
				<h2 id="t-fin" class="font-display text-xl">Finanças</h2>
				<button type="button" class="more" onclick={() => onOpenSection('finance')}
					>Abrir <ArrowRight size={15} /></button
				>
			</div>
			{#if finance}
				<div class="flex flex-wrap gap-x-8 gap-y-4">
					<div class="fin-stat">
						<span class="fin-value font-mono-num"
							>{brl(finance.autonomy.free_balance, finance.autonomy.currency)}</span
						>
						<span class="fin-label">livre</span>
					</div>
					<div class="fin-stat">
						<span class="fin-value font-mono-num">{finance.autonomy.days_of_runway} dias</span>
						<span class="fin-label">de autonomia</span>
					</div>
				</div>
				{#if finance.total_debt > 0}
					<p class="text-sm text-base-content/70">
						Dívidas: <span class="font-mono-num font-semibold text-base-content"
							>{brl(finance.total_debt, finance.autonomy.currency)}</span
						>
					</p>
				{/if}
				{#if finance.alerts.length > 0}
					<p class="alert-line">{finance.alerts[0]}</p>
				{/if}
			{:else if financeFailed}
				<p class="empty">Não foi possível carregar as finanças.</p>
			{:else}
				<div class="skeleton-pulse h-16"></div>
			{/if}
		</section>

		<!-- ── Missões ────────────────────────────────────── -->
		<section class="tile sec-missions flex flex-col gap-4" aria-labelledby="t-mis">
			<div class="tile-head">
				<h2 id="t-mis" class="font-display text-xl">Missões</h2>
				<button type="button" class="more" onclick={() => onOpenSection('missions')}
					>Todas <ArrowRight size={15} /></button
				>
			</div>
			{#if loading}
				<div class="skeleton-pulse h-16"></div>
			{:else if missionProgress.length === 0}
				<p class="empty">Nenhuma missão ativa.</p>
			{:else}
				<ul class="flex flex-col gap-4">
					{#each missionProgress as m (m.goal.id)}
						<li class="flex flex-col gap-2">
							<div class="flex justify-between gap-3 text-[15px] font-semibold">
								<span class="min-w-0 break-words">{m.goal.title}</span>
								<span class="font-mono-num shrink-0" style="color: var(--sec-ink)"
									>{m.done}/{m.total}</span
								>
							</div>
							<div
								class="bar"
								role="progressbar"
								aria-valuenow={Math.round(m.pct)}
								aria-valuemin={0}
								aria-valuemax={100}
								aria-label="Progresso de {m.goal.title}"
							>
								<div class="bar-fill" style="width: {m.pct}%"></div>
							</div>
						</li>
					{/each}
				</ul>
			{/if}
		</section>
	</div>
</div>

<style>
	/* Três colunas independentes: cada uma empilha seus tiles, sem buracos */
	.today-grid {
		display: flex;
		flex-wrap: wrap;
		gap: 20px;
		align-items: flex-start;
	}
	.today-col {
		flex: 1 1 340px;
		min-width: 0;
		display: flex;
		flex-direction: column;
		gap: 20px;
	}

	.tile {
		animation: fadeSlideIn 0.3s ease both;
	}

	.tile-head {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: 12px;
	}
	.count {
		font: 700 14px/1 var(--font-body);
		color: var(--sec-ink);
		font-variant-numeric: tabular-nums;
	}
	.empty {
		font-size: 14px;
		color: color-mix(in oklab, var(--color-base-content) 65%, transparent);
	}
	.link-btn {
		color: var(--color-primary);
		text-decoration: underline;
		text-underline-offset: 2px;
		cursor: pointer;
	}

	/* Tarefas */
	.task {
		display: flex;
		align-items: center;
		gap: 12px;
		min-height: 48px;
		padding: 6px 12px;
		border-radius: var(--radius-field);
		background: var(--color-base-100);
		font-size: 15px;
		font-weight: 500;
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
		border-color: var(--sec);
		background: var(--sec-soft);
	}
	.task.done .tick {
		border-color: var(--sec);
		background: var(--sec);
		color: var(--color-base-100);
	}
	.task-text {
		transition: color 0.2s ease;
	}
	.task.done .task-text {
		text-decoration: line-through;
		color: color-mix(in oklab, var(--color-base-content) 50%, transparent);
	}

	.meta {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 6px;
	}
	.due {
		padding: 3px 8px;
		border-radius: var(--radius-selector);
		font-size: 12px;
		font-weight: 700;
		line-height: 1.2;
	}
	.due-overdue {
		background: color-mix(in oklab, var(--color-error) 16%, transparent);
		color: var(--color-error);
	}
	.due-today {
		background: var(--c-protocols-soft);
		color: var(--c-protocols-ink);
	}
	.due-soon {
		background: var(--c-ops-soft);
		color: var(--c-ops-ink);
	}
	.due-later {
		background: var(--color-base-300);
		color: color-mix(in oklab, var(--color-base-content) 75%, transparent);
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

	.more {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		align-self: flex-start;
		min-height: 36px;
		font: 700 14px/1 var(--font-body);
		color: var(--sec-ink);
		cursor: pointer;
	}
	.more:hover {
		text-decoration: underline;
		text-underline-offset: 3px;
	}

	/* Hábitos */
	.habit-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(118px, 1fr));
		gap: 10px;
	}
	.habit {
		display: flex;
		flex-direction: column;
		align-items: flex-start;
		gap: 10px;
		min-height: 96px;
		padding: 14px;
		border-radius: var(--radius-field);
		border: 2px dashed var(--color-base-300);
		background: transparent;
		color: var(--color-base-content);
		text-align: left;
		cursor: pointer;
		transition:
			background 0.15s ease,
			border-color 0.15s ease,
			transform 0.1s ease;
	}
	.habit:hover {
		border-color: var(--sec);
	}
	.habit:active {
		transform: scale(0.97);
	}
	.habit.done {
		border-style: solid;
		border-color: var(--sec);
		background: var(--sec-soft);
		color: var(--sec-ink);
	}
	.habit[aria-busy='true'],
	.tick[aria-busy='true'] {
		cursor: progress;
	}
	.streak {
		font-family: var(--font-display);
		font-weight: var(--display-weight);
		font-size: 28px;
		line-height: 1;
	}
	.habit-name {
		font-size: 14px;
		font-weight: 600;
		line-height: 1.25;
	}
	.emoji {
		font-size: 18px;
	}

	/* Finanças */
	.fin-stat {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.fin-value {
		font-family: var(--font-display);
		font-weight: var(--display-weight);
		font-size: 26px;
		line-height: 1.1;
	}
	.fin-label {
		font-size: 13px;
		color: color-mix(in oklab, var(--color-base-content) 65%, transparent);
	}
	.alert-line {
		font-size: 13px;
		padding: 8px 12px;
		border-radius: var(--radius-field);
		background: color-mix(in oklab, var(--color-warning) 14%, transparent);
		color: var(--color-base-content);
	}

	/* Missões */
	.bar {
		height: 10px;
		border-radius: 999px;
		background: var(--sec-soft);
		overflow: hidden;
	}
	.bar-fill {
		height: 100%;
		border-radius: 999px;
		background: var(--sec);
		transition: width 0.3s ease;
	}

	button:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
