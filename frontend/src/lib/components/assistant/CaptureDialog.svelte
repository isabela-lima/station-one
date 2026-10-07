<script lang="ts">
	import { tick } from 'svelte';
	import {
		X,
		Sparkles,
		Loader2,
		CheckSquare,
		Wallet,
		BookOpen,
		HeartPulse,
		Settings,
		CornerDownLeft
	} from 'lucide-svelte';
	import * as api from '$lib/api';
	import { ApiError } from '$lib/api';
	import type { AssistantAction, CaptureResponse, ExpenseCategory, Goal } from '$lib/models/types';

	let {
		open = $bindable<boolean>(),
		goals,
		onApplied,
		onOpenSettings
	}: {
		open: boolean;
		goals: Goal[];
		/** Chamado depois de gravar, para a página recarregar o que mudou */
		onApplied: (created: Record<string, number>) => void;
		onOpenSettings: () => void;
	} = $props();

	type Draft = AssistantAction & { include: boolean };

	let dialog = $state<HTMLDialogElement | null>(null);
	let textarea = $state<HTMLTextAreaElement | null>(null);
	let text = $state('');
	let phase = $state<'input' | 'thinking' | 'review' | 'applying'>('input');
	let error = $state('');
	let needsKey = $state(false);
	let result = $state<CaptureResponse | null>(null);
	let drafts = $state<Draft[]>([]);

	const CATEGORIES: { id: ExpenseCategory; label: string }[] = [
		{ id: 'food', label: 'Comida' },
		{ id: 'transport', label: 'Transporte' },
		{ id: 'health', label: 'Saúde' },
		{ id: 'pharma', label: 'Farmácia' },
		{ id: 'personal', label: 'Pessoal' },
		{ id: 'debt', label: 'Dívida' },
		{ id: 'savings', label: 'Reserva' },
		{ id: 'other', label: 'Outros' }
	];

	const selected = $derived(drafts.filter((d) => d.include && isComplete(d)));

	// Abre/fecha o <dialog> nativo junto com a prop e foca o campo ao abrir
	$effect(() => {
		if (!dialog) return;
		if (open && !dialog.open) {
			dialog.showModal();
			tick().then(() => textarea?.focus());
		} else if (!open && dialog.open) dialog.close();
	});

	function reset() {
		text = '';
		phase = 'input';
		error = '';
		needsKey = false;
		result = null;
		drafts = [];
	}

	function close() {
		open = false;
		if (phase !== 'applying') reset();
	}

	/** Uma ação só pode ser aplicada se tiver o essencial */
	function isComplete(d: Draft): boolean {
		if (d.type === 'create_task' || d.type === 'add_journal_entry')
			return d.content.trim().length > 0;
		if (d.type === 'create_transaction') return d.amount > 0 && !!d.wallet_id;
		return d.mood != null || d.energy != null;
	}

	async function interpret() {
		if (!text.trim() || phase === 'thinking') return;
		phase = 'thinking';
		error = '';
		needsKey = false;
		try {
			result = await api.assistant.capture(text.trim());
			drafts = result.actions.map((a) => ({ ...a, include: true }));
			phase = 'review';
		} catch (err) {
			needsKey = err instanceof ApiError && err.status === 409;
			error = err instanceof Error ? err.message : 'Não foi possível falar com o assistente.';
			phase = 'input';
		}
	}

	async function applySelected() {
		if (selected.length === 0) return;
		phase = 'applying';
		error = '';
		try {
			// Só os campos que a API aceita (sem os de exibição e o `include`)
			const actions = selected.map((d) => {
				const { include: _include, ...rest } = d;
				if (rest.type === 'create_task') {
					const { goal_title: _goalTitle, ...task } = rest;
					return { ...task, goal_id: task.goal_id || null, due_date: task.due_date || null };
				}
				if (rest.type === 'create_transaction') {
					const { wallet_name: _walletName, ...tx } = rest;
					return { ...tx, amount: Number(tx.amount), date: tx.date || null };
				}
				return rest;
			}) as AssistantAction[];
			const { created } = await api.assistant.apply(actions);
			onApplied(created);
			reset();
			open = false;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Não foi possível registrar.';
			phase = 'review';
		}
	}

	function onKeydown(e: KeyboardEvent) {
		// Enter envia; Shift+Enter quebra linha
		if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
			e.preventDefault();
			interpret();
		}
	}

	function usd(value: string) {
		return new Intl.NumberFormat('pt-BR', {
			style: 'currency',
			currency: 'USD',
			maximumFractionDigits: 4
		}).format(Number(value));
	}
</script>

<dialog
	bind:this={dialog}
	class="capture-dialog"
	aria-labelledby="capture-title"
	onclose={close}
	onclick={(e) => {
		if (e.target === dialog && phase !== 'applying') close();
	}}
>
	<div class="panel">
		<div class="flex items-center justify-between gap-3">
			<h2 id="capture-title" class="font-display flex items-center gap-2 text-xl">
				<Sparkles size={20} style="color: var(--color-primary)" /> Registrar
			</h2>
			<button type="button" class="icon-btn" aria-label="Fechar" onclick={close}
				><X size={18} /></button
			>
		</div>

		{#if phase === 'input' || phase === 'thinking'}
			<p class="muted">
				Escreva do seu jeito: tarefas, gastos, o que aconteceu, como você está. Ex.: “pagar a fatura
				sexta, gastei 45 no mercado e tô cansada”.
			</p>
			<div class="composer">
				<label class="sr-only" for="capture-text">O que você quer registrar?</label>
				<textarea
					id="capture-text"
					bind:this={textarea}
					bind:value={text}
					rows="3"
					maxlength="2000"
					placeholder="O que você quer registrar?"
					disabled={phase === 'thinking'}
					onkeydown={onKeydown}
				></textarea>
				<button
					type="button"
					class="send"
					aria-label="Interpretar"
					disabled={!text.trim() || phase === 'thinking'}
					onclick={interpret}
				>
					{#if phase === 'thinking'}<Loader2 size={18} class="animate-spin" />{:else}<CornerDownLeft
							size={18}
						/>{/if}
				</button>
			</div>
			{#if phase === 'thinking'}<p class="muted" aria-live="polite">Interpretando…</p>{/if}
			{#if error}
				<div class="error-box" role="alert">
					<span>{error}</span>
					{#if needsKey}
						<button
							type="button"
							class="link-btn"
							onclick={() => {
								close();
								onOpenSettings();
							}}><Settings size={14} /> Abrir Configurações</button
						>
					{/if}
				</div>
			{/if}
		{:else if result}
			<!-- ── Revisão ─────────────────────────────────── -->
			{#if result.summary}<p class="summary">{result.summary}</p>{/if}
			{#if result.question}<p class="question">{result.question}</p>{/if}

			{#if drafts.length === 0}
				<p class="muted">Nada para registrar. Volte e escreva com mais detalhes.</p>
			{/if}

			<ul class="actions">
				{#each drafts as d, i (i)}
					<li class="action" class:off={!d.include}>
						<label class="include">
							<input type="checkbox" bind:checked={d.include} />
							<span class="sr-only">Incluir</span>
						</label>
						<div class="flex min-w-0 flex-1 flex-col gap-2">
							{#if d.type === 'create_task'}
								<span class="kind sec-ops"><CheckSquare size={14} /> Tarefa</span>
								<input class="field" aria-label="Tarefa" bind:value={d.content} />
								<div class="row">
									<label class="mini"
										>Prazo <input type="date" class="field" bind:value={d.due_date} /></label
									>
									{#if goals.length > 0}
										<label class="mini"
											>Missão
											<select class="field" bind:value={d.goal_id}>
												<option value={null}>Sem missão</option>
												{#each goals as g (g.id)}<option value={g.id}>{g.title}</option>{/each}
											</select>
										</label>
									{/if}
									<label class="mini check"
										><input type="checkbox" bind:checked={d.priority} /> Foco</label
									>
								</div>
							{:else if d.type === 'create_transaction'}
								<span class="kind sec-finance"
									><Wallet size={14} /> {d.kind === 'expense' ? 'Gasto' : 'Receita'}</span
								>
								<div class="row">
									<label class="mini"
										>Valor (R$)
										<input
											type="number"
											class="field"
											min="0.01"
											step="0.01"
											bind:value={d.amount}
										/>
									</label>
									<label class="mini"
										>Categoria
										<select class="field" bind:value={d.category}>
											{#each CATEGORIES as c (c.id)}<option value={c.id}>{c.label}</option>{/each}
										</select>
									</label>
									<label class="mini"
										>Carteira
										<select class="field" bind:value={d.wallet_id}>
											{#each result.wallets as w (w.id)}<option value={w.id}>{w.name}</option
												>{/each}
										</select>
									</label>
								</div>
								<input
									class="field"
									aria-label="Descrição"
									placeholder="Descrição"
									bind:value={d.description}
								/>
								{#if result.wallets.length === 0}
									<p class="warn">Crie uma carteira em Finanças para lançar gastos.</p>
								{/if}
							{:else if d.type === 'add_journal_entry'}
								<span class="kind sec-journal"><BookOpen size={14} /> Diário</span>
								<textarea
									class="field"
									rows="2"
									aria-label="Entrada do diário"
									bind:value={d.content}
								></textarea>
							{:else if d.type === 'set_checkin'}
								<span class="kind sec-journal"><HeartPulse size={14} /> Check-in</span>
								<div class="row">
									<label class="mini"
										>Humor
										<select class="field" bind:value={d.mood}>
											<option value={null}>—</option>
											{#each [1, 2, 3, 4, 5] as n (n)}<option value={n}>{n}</option>{/each}
										</select>
									</label>
									<label class="mini"
										>Energia
										<select class="field" bind:value={d.energy}>
											<option value={null}>—</option>
											{#each [1, 2, 3, 4, 5] as n (n)}<option value={n}>{n}</option>{/each}
										</select>
									</label>
								</div>
							{/if}
						</div>
					</li>
				{/each}
			</ul>

			{#if error}<div class="error-box" role="alert"><span>{error}</span></div>{/if}

			<div class="footer">
				<span class="cost font-mono-num" title="Custo estimado desta interpretação"
					>{usd(result.cost_usd)} · {result.model.replace('claude-', '')}</span
				>
				<div class="flex gap-2">
					<button
						type="button"
						class="ghost-btn"
						disabled={phase === 'applying'}
						onclick={() => (phase = 'input')}>Editar texto</button
					>
					<button
						type="button"
						class="primary-btn"
						disabled={selected.length === 0 || phase === 'applying'}
						onclick={applySelected}
					>
						{#if phase === 'applying'}<Loader2 size={16} class="animate-spin" />{/if}
						Registrar {selected.length > 0 ? `(${selected.length})` : ''}
					</button>
				</div>
			</div>
		{/if}
	</div>
</dialog>

<style>
	.capture-dialog {
		margin: 8vh auto auto;
		padding: 0;
		border: none;
		background: transparent;
		color: inherit;
		width: min(600px, calc(100vw - 32px));
		max-height: 84vh;
	}
	.capture-dialog::backdrop {
		background: rgba(0, 0, 0, 0.5);
		backdrop-filter: blur(3px);
	}
	@media (max-width: 640px) {
		.capture-dialog {
			margin: auto 0 0;
			width: 100vw;
			max-width: 100vw;
			max-height: 92vh;
		}
		.panel {
			border-radius: var(--tile-radius) var(--tile-radius) 0 0;
			padding-bottom: calc(24px + env(safe-area-inset-bottom));
		}
	}
	.panel {
		display: flex;
		flex-direction: column;
		gap: 16px;
		padding: 22px;
		border-radius: var(--tile-radius);
		background: var(--color-base-200);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
	}

	.muted {
		margin: 0;
		font-size: 14px;
		line-height: 1.5;
		color: color-mix(in oklab, var(--color-base-content) 65%, transparent);
	}

	.composer {
		display: flex;
		gap: 8px;
		align-items: flex-end;
	}
	.composer textarea {
		flex: 1;
		min-width: 0;
		resize: vertical;
		padding: 12px 14px;
		border-radius: var(--radius-field);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
		font: inherit;
		font-size: 16px; /* 16px evita o zoom automático do iOS ao focar */
		line-height: 1.45;
		outline: none;
	}
	.composer textarea:focus {
		border-color: var(--color-primary);
	}
	.send {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		flex-shrink: 0;
		border-radius: var(--radius-field);
		background: var(--color-primary);
		color: var(--color-primary-content);
		cursor: pointer;
	}
	.send:disabled {
		opacity: 0.4;
		cursor: default;
	}

	.summary {
		margin: 0;
		font-size: 15px;
		font-weight: 600;
	}
	.question {
		margin: 0;
		padding: 10px 12px;
		border-radius: var(--radius-field);
		background: color-mix(in oklab, var(--color-warning) 14%, transparent);
		font-size: 14px;
	}

	.actions {
		display: flex;
		flex-direction: column;
		gap: 10px;
		margin: 0;
		padding: 0;
		list-style: none;
		max-height: 50vh;
		overflow-y: auto;
	}
	.action {
		display: flex;
		gap: 12px;
		padding: 12px;
		border-radius: var(--radius-box);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
		transition: opacity 0.15s ease;
	}
	.action.off {
		opacity: 0.5;
	}
	.include {
		display: flex;
		align-items: flex-start;
		padding-top: 2px;
		cursor: pointer;
	}
	.include input,
	.check input {
		width: 20px;
		height: 20px;
		accent-color: var(--color-primary);
	}
	.kind {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		align-self: flex-start;
		padding: 3px 8px;
		border-radius: var(--radius-selector);
		background: var(--sec-soft);
		color: var(--sec-ink);
		font-size: 12px;
		font-weight: 700;
	}
	.row {
		display: flex;
		flex-wrap: wrap;
		gap: 8px;
		align-items: flex-end;
	}
	.mini {
		display: flex;
		flex-direction: column;
		gap: 4px;
		font-size: 12px;
		color: color-mix(in oklab, var(--color-base-content) 65%, transparent);
	}
	.mini.check {
		flex-direction: row;
		align-items: center;
		gap: 6px;
		min-height: 40px;
		font-size: 14px;
		color: var(--color-base-content);
	}
	.field {
		min-height: 40px;
		padding: 6px 10px;
		border-radius: var(--radius-field);
		background: var(--color-base-200);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
		font: inherit;
		font-size: 16px;
		outline: none;
		min-width: 0;
	}
	.field:focus {
		border-color: var(--color-primary);
	}
	textarea.field {
		resize: vertical;
	}
	.warn {
		margin: 0;
		font-size: 13px;
		color: var(--color-warning);
	}

	.footer {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		justify-content: space-between;
		gap: 10px;
	}
	.cost {
		font-size: 12px;
		color: color-mix(in oklab, var(--color-base-content) 55%, transparent);
	}
	.primary-btn,
	.ghost-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		min-height: 44px;
		padding: 0 16px;
		border-radius: var(--radius-field);
		font-weight: 700;
		cursor: pointer;
	}
	.primary-btn {
		background: var(--color-primary);
		color: var(--color-primary-content);
	}
	.ghost-btn:hover {
		background: var(--color-base-300);
	}
	.primary-btn:disabled,
	.ghost-btn:disabled {
		opacity: 0.45;
		cursor: default;
	}

	.error-box {
		display: flex;
		flex-wrap: wrap;
		align-items: center;
		gap: 10px;
		padding: 10px 12px;
		border-radius: var(--radius-field);
		background: color-mix(in oklab, var(--color-error) 14%, transparent);
		font-size: 14px;
	}
	.link-btn {
		display: inline-flex;
		align-items: center;
		gap: 4px;
		font-weight: 700;
		color: var(--color-primary);
		cursor: pointer;
	}
	.icon-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 40px;
		height: 40px;
		border-radius: 999px;
		cursor: pointer;
	}
	.icon-btn:hover {
		background: var(--color-base-300);
	}

	button:focus-visible,
	input:focus-visible,
	select:focus-visible,
	textarea:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
