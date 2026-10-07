<script lang="ts">
	import {
		Loader2,
		Plus,
		ArrowRightLeft,
		Wallet as WalletIcon,
		FlameKindling
	} from 'lucide-svelte';
	import type { Goal } from '$lib';
	import type { Section, FormType, FormPayload } from '$lib/components/dashboard';
	import type { Wallet } from '$lib';
	import * as api from '$lib/api';
	import { addDaysISO, nextWeekdayISO, todayISO } from '$lib/dates';

	// ── Props ─────────────────────────────────────────────
	let {
		activeSection,
		goals,
		selectedType = $bindable<FormType>(),
		onSubmit
	}: {
		activeSection: Section;
		goals: Goal[];
		selectedType: FormType;
		onSubmit: (payload: FormPayload) => Promise<void>;
	} = $props();

	// ── Internal Form State ───────────────────────────────
	let content = $state('');
	let taskGoalId = $state('');
	let taskDue = $state(''); // "YYYY-MM-DD" ou vazio
	let goalTitle = $state('');
	let wishlistUrl = $state('');
	let wishlistFetching = $state(false);
	let wishlistPreview = $state<{
		title: string;
		imageUrl: string;
		description: string;
		currentPrice: string;
		targetPrice: string;
	} | null>(null);

	// Finance State
	let wallets = $state<Wallet[]>([]);
	let txWalletId = $state('');
	let txAmount = $state('');
	let txCategory = $state('');
	let txDescription = $state('');
	let txType = $state('expense'); // expense ou income

	let walletName = $state('');
	let walletType = $state('cash');
	let walletEmoji = $state('💰');

	// Protocols State
	let habitName = $state('');
	let habitEmoji = $state('⚡');

	$effect(() => {
		if (activeSection === 'finance') {
			api.finance.wallets
				.list()
				.then((w) => (wallets = w))
				.catch(() => {});
		}
	});

	// ── Style constants ───────────────────────────────────
	const S = {
		cyan: 'background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border-color: color-mix(in oklab, var(--color-primary) 15%, transparent)',
		violet:
			'background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border-color: color-mix(in oklab, var(--color-secondary) 20%, transparent)',
		teal: 'background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border-color: color-mix(in oklab, var(--color-primary) 20%, transparent)',
		blue: 'background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border-color: color-mix(in oklab, var(--color-info) 20%, transparent)',
		plain: 'background: color-mix(in oklab, var(--color-base-content) 4%, transparent)'
	};

	// ── Wishlist URL scraping ─────────────────────────────
	async function handleWishlistBlur() {
		if (!wishlistUrl.trim() || !wishlistUrl.startsWith('http')) return;
		wishlistFetching = true;
		wishlistPreview = null;
		try {
			const res = await fetch(`https://api.microlink.io?url=${encodeURIComponent(wishlistUrl)}`);
			const data = await res.json();
			if (data.status === 'success') {
				wishlistPreview = {
					title: data.data.title ?? '',
					imageUrl: data.data.image?.url ?? '',
					description: data.data.description ?? '',
					currentPrice: '',
					targetPrice: ''
				};
			}
		} catch {
			/* silently fail — user can fill manually */
		} finally {
			wishlistFetching = false;
		}
	}

	// ── Submit ────────────────────────────────────────────
	async function handleSubmit() {
		if (selectedType === 'task') {
			if (!content.trim()) return;
			await onSubmit({
				kind: 'task',
				content: content.trim(),
				goal_id: taskGoalId || null,
				due_date: taskDue || null
			});
			content = '';
			taskDue = '';
		} else if (selectedType === 'goal') {
			if (!goalTitle.trim()) return;
			await onSubmit({ kind: 'goal', title: goalTitle.trim() });
			goalTitle = '';
		} else if (selectedType === 'wishlist') {
			if (!wishlistUrl.trim()) return;
			await onSubmit({
				kind: 'wishlist',
				title: wishlistPreview?.title || wishlistUrl,
				url: wishlistUrl.trim(),
				image_url: wishlistPreview?.imageUrl || undefined,
				description: wishlistPreview?.description || undefined,
				current_price: parseFloat(wishlistPreview?.currentPrice ?? '') || 0,
				target_price: parseFloat(wishlistPreview?.targetPrice ?? '') || 0,
				currency: 'BRL'
			});
			wishlistUrl = '';
			wishlistPreview = null;
		} else if (selectedType === 'transaction') {
			if (!txWalletId || !txAmount || !txCategory) return;
			const amountNum = parseFloat(txAmount);
			await onSubmit({
				kind: 'transaction',
				wallet_id: txWalletId,
				amount: txType === 'expense' ? -Math.abs(amountNum) : Math.abs(amountNum),
				currency: 'BRL',
				category: txCategory.trim(),
				description: txDescription.trim() || undefined,
				date: new Date().toISOString(),
				is_recurring: false
			});
			txAmount = '';
			txDescription = '';
		} else if (selectedType === 'wallet') {
			if (!walletName.trim()) return;
			await onSubmit({
				kind: 'wallet',
				name: walletName.trim(),
				type: walletType as 'cash' | 'vr' | 'inflow',
				emoji: walletEmoji.trim() || '💰',
				currency: 'BRL'
			});
			walletName = '';
			// Refresh wallets inside AddForm
			api.finance.wallets
				.list()
				.then((w) => (wallets = w))
				.catch(() => {});
		} else if (selectedType === 'habit') {
			if (!habitName.trim()) return;
			await onSubmit({ kind: 'habit', name: habitName.trim(), emoji: habitEmoji.trim() || '⚡' });
			habitName = '';
			habitEmoji = '⚡';
		}
	}

	const submitLabel = $derived(
		activeSection === 'operations'
			? 'Criar Operação'
			: activeSection === 'missions'
				? 'Criar Missão'
				: activeSection === 'protocols'
					? 'Criar Protocolo'
					: activeSection === 'finance'
						? selectedType === 'transaction'
							? 'Lançar Transação'
							: 'Criar Carteira'
						: 'Adicionar à Wishlist'
	);

	const DUE_SHORTCUTS = [
		{ label: 'Hoje', value: () => todayISO() },
		{ label: 'Amanhã', value: () => addDaysISO(todayISO(), 1) },
		{ label: 'Sexta', value: () => nextWeekdayISO(5) },
		{ label: 'Semana que vem', value: () => nextWeekdayISO(1) }
	];

	const FINANCE_TYPES = [
		{ v: 'transaction' as FormType, label: 'Transação', Icon: ArrowRightLeft },
		{ v: 'wallet' as FormType, label: 'Carteira', Icon: WalletIcon }
	];
</script>

<form
	class="space-y-3"
	onsubmit={(e) => {
		e.preventDefault();
		handleSubmit();
	}}
>
	{#if activeSection === 'operations'}
		<label class="sr-only" for="task-content">Tarefa</label>
		<textarea
			id="task-content"
			class="textarea-bordered textarea h-24 w-full resize-none text-sm"
			style={S.cyan}
			placeholder="Ex: Revisar relatório…"
			bind:value={content}
		></textarea>
		<div class="flex flex-col gap-1.5 text-xs text-base-content/70">
			<label for="task-due">Prazo (opcional)</label>
			<div class="flex flex-wrap items-center gap-1.5">
				{#each DUE_SHORTCUTS as s (s.label)}
					<button
						type="button"
						class="due-chip"
						class:on={taskDue === s.value()}
						aria-pressed={taskDue === s.value()}
						onclick={() => (taskDue = taskDue === s.value() ? '' : s.value())}>{s.label}</button
					>
				{/each}
				<input
					id="task-due"
					type="date"
					class="input input-sm w-auto"
					style={S.cyan}
					bind:value={taskDue}
				/>
			</div>
		</div>
		{#if goals.length > 0}
			<label class="flex flex-col gap-1.5 text-xs text-base-content/70">
				Missão (opcional)
				<select
					class="select-bordered select w-full select-sm"
					style={S.cyan}
					bind:value={taskGoalId}
				>
					<option value="">Sem missão</option>
					{#each goals as g (g.id)}
						<option value={g.id}>{g.title}</option>
					{/each}
				</select>
			</label>
		{/if}
	{:else if activeSection === 'missions'}
		<label class="sr-only" for="goal-title">Missão</label>
		<input
			id="goal-title"
			class="input-bordered input input-sm w-full"
			style={S.violet}
			type="text"
			placeholder="Ex: Aprender Rust"
			bind:value={goalTitle}
			required
		/>
		<p class="text-xs text-base-content/60">
			Depois de criar, adicione as tarefas da missão na página Missões.
		</p>
	{:else if activeSection === 'finance'}
		<!-- Type tabs -->
		<div
			class="flex gap-1 rounded-lg p-1"
			style="background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border: 1px solid color-mix(in oklab, var(--color-info) 10%, transparent)"
		>
			{#each FINANCE_TYPES as opt (opt.v)}
				<button
					type="button"
					onclick={() => (selectedType = opt.v)}
					class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-[10px] font-semibold tracking-wide uppercase transition-all duration-150"
					style={selectedType === opt.v
						? 'background: color-mix(in oklab, var(--color-info) 15%, transparent); color: var(--color-info); border: 1px solid color-mix(in oklab, var(--color-info) 30%, transparent)'
						: 'background: transparent; color: var(--color-base-content); opacity: 0.4; border: 1px solid transparent'}
				>
					<opt.Icon size={11} />
					{opt.label}
				</button>
			{/each}
		</div>

		{#if selectedType === 'transaction'}
			<select class="select-bordered select w-full select-sm" style={S.blue} bind:value={txType}>
				<option value="expense">Despesa (Saída)</option>
				<option value="income">Receita (Entrada)</option>
			</select>
			<select
				class="select-bordered select w-full select-sm"
				style={S.blue}
				bind:value={txWalletId}
				required
			>
				<option value="" disabled>Selecione a carteira</option>
				{#each wallets as w (w.id)}
					<option value={w.id}>{w.emoji} {w.name} ({w.currency})</option>
				{/each}
			</select>
			<div class="grid grid-cols-2 gap-2">
				<input
					class="input-bordered input input-sm w-full"
					style={S.blue}
					type="number"
					step="0.01"
					placeholder="Valor"
					bind:value={txAmount}
					required
				/>
				<input
					class="input-bordered input input-sm w-full"
					style={S.blue}
					type="text"
					placeholder="Categoria"
					bind:value={txCategory}
					required
				/>
			</div>
			<input
				class="input-bordered input input-sm w-full"
				style={S.blue}
				type="text"
				placeholder="Descrição (opcional)"
				bind:value={txDescription}
			/>
		{:else if selectedType === 'wallet'}
			<input
				class="input-bordered input input-sm w-full"
				style={S.blue}
				type="text"
				placeholder="Nome da Carteira"
				bind:value={walletName}
				required
			/>
			<div class="grid grid-cols-2 gap-2">
				<select
					class="select-bordered select w-full select-sm"
					style={S.blue}
					bind:value={walletType}
					required
				>
					<option value="cash">Cash (Dinheiro)</option>
					<option value="vr">VR/VA (Benefício)</option>
					<option value="inflow">Inflow (Receita)</option>
				</select>
				<input
					class="input-bordered input input-sm w-full"
					style={S.blue}
					type="text"
					placeholder="Emoji (ex: 💰)"
					bind:value={walletEmoji}
				/>
			</div>
		{/if}
	{:else if activeSection === 'protocols'}
		<!-- Habit form -->
		<div class="space-y-2">
			<div class="flex items-center gap-2">
				<input
					class="input-bordered input input-sm w-16 text-center text-lg"
					style="background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border-color: color-mix(in oklab, var(--c-protocols) 20%, transparent)"
					type="text"
					placeholder="⚡"
					bind:value={habitEmoji}
					maxlength="2"
				/>
				<input
					class="input-bordered input input-sm flex-1"
					style="background: color-mix(in oklab, var(--color-base-content) 4%, transparent); border-color: color-mix(in oklab, var(--c-protocols) 20%, transparent)"
					type="text"
					placeholder="Ex: Meditar 10 minutos"
					bind:value={habitName}
					required
				/>
			</div>
			<p class="pl-1 text-[10px] text-base-content/25">
				Protocolos são hábitos diários com contagem de streak 🔥
			</p>
		</div>
	{:else if activeSection === 'wishlist'}
		<div class="relative">
			<input
				class="input-bordered input input-sm w-full pr-8"
				style={S.teal}
				type="url"
				placeholder="https://loja.com/produto"
				bind:value={wishlistUrl}
				onblur={handleWishlistBlur}
				required
			/>
			{#if wishlistFetching}
				<Loader2
					size={14}
					class="absolute top-1/2 right-2 -translate-y-1/2 animate-spin text-primary"
				/>
			{/if}
		</div>

		{#if wishlistPreview}
			<div
				class="space-y-2 rounded-lg p-3"
				style="background: color-mix(in oklab, var(--color-primary) 5%, transparent); border: 1px solid color-mix(in oklab, var(--color-primary) 15%, transparent)"
			>
				<p class="text-[10px] font-semibold tracking-widest text-accent/60 uppercase">Preview</p>
				{#if wishlistPreview.imageUrl}
					<img
						src={wishlistPreview.imageUrl}
						alt="preview"
						class="h-24 w-full rounded-md object-cover"
					/>
				{/if}
				<p class="text-sm leading-snug font-medium">{wishlistPreview.title}</p>
				{#if wishlistPreview.description}
					<p class="line-clamp-2 text-xs text-base-content/40">{wishlistPreview.description}</p>
				{/if}
				<div class="grid grid-cols-2 gap-2">
					<input
						type="number"
						step="0.01"
						class="input-bordered input input-xs"
						style={S.plain}
						placeholder="Preço atual"
						bind:value={wishlistPreview.currentPrice}
					/>
					<input
						type="number"
						step="0.01"
						class="input-bordered input input-xs"
						style={S.plain}
						placeholder="Meta"
						bind:value={wishlistPreview.targetPrice}
					/>
				</div>
			</div>
		{/if}
	{/if}

	<button
		type="submit"
		class="btn mt-1 w-full font-semibold btn-sm"
		style="background: color-mix(in oklab, var(--color-primary) 15%, transparent); border-color: color-mix(in oklab, var(--color-primary) 35%, transparent); color: var(--color-primary)"
	>
		<Plus size={14} />
		{submitLabel}
	</button>
</form>

<style>
	.due-chip {
		min-height: 32px;
		padding: 0 10px;
		border-radius: var(--radius-selector);
		background: var(--c-ops-soft);
		color: var(--c-ops-ink);
		font-weight: 600;
		cursor: pointer;
	}
	.due-chip.on {
		background: var(--c-ops);
		color: var(--color-base-100);
	}
</style>
