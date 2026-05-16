<script lang="ts">
	import { Loader2, Plus, CheckSquare, FileText, Link as LinkIcon, Target, Flag, ArrowRightLeft, Wallet as WalletIcon, FlameKindling } from 'lucide-svelte';
	import type { Goal } from '$lib';
	import type { Section, FormType, FormPayload } from '$lib/components/dashboard';
	import type { Wallet } from '$lib';
	import * as api from '$lib/api';

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
	let linkTitle = $state('');
	let goalTitle = $state('');
	let milestoneTitle = $state('');
	let milestoneGoalId = $state('');
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
			api.finance.wallets.list().then(w => wallets = w).catch(() => {});
		}
	});

	// ── Style constants ───────────────────────────────────
	const S = {
		cyan: 'background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)',
		violet: 'background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)',
		teal: 'background: rgba(255,255,255,0.04); border-color: rgba(34,211,238,0.2)',
		blue: 'background: rgba(255,255,255,0.04); border-color: rgba(56,189,248,0.2)',
		plain: 'background: rgba(255,255,255,0.04)'
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
		if (selectedType === 'note' || selectedType === 'task') {
			if (!content.trim()) return;
			await onSubmit({ kind: 'item', type: selectedType, content: content.trim(), completed: false, priority: false });
			content = '';
		} else if (selectedType === 'link') {
			if (!content.trim()) return;
			await onSubmit({ kind: 'item', type: 'link', content: content.trim(), title: linkTitle.trim() || undefined, completed: false, priority: false });
			content = '';
			linkTitle = '';
		} else if (selectedType === 'goal') {
			if (!goalTitle.trim()) return;
			await onSubmit({ kind: 'goal', title: goalTitle.trim() });
			goalTitle = '';
		} else if (selectedType === 'milestone') {
			if (!milestoneTitle.trim() || !milestoneGoalId) return;
			await onSubmit({ kind: 'milestone', title: milestoneTitle.trim(), goal_id: milestoneGoalId });
			milestoneTitle = '';
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
			api.finance.wallets.list().then(w => wallets = w).catch(() => {});
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
				? selectedType === 'goal'
					? 'Criar Missão'
					: 'Criar Marco'
				: activeSection === 'protocols'
					? 'Criar Protocolo'
					: activeSection === 'finance'
						? selectedType === 'transaction'
							? 'Lançar Transação'
							: 'Criar Carteira'
						: 'Adicionar à Wishlist'
	);

	const OPS_TYPES = [
		{ v: 'task' as FormType, label: 'Tarefa', Icon: CheckSquare },
		{ v: 'note' as FormType, label: 'Nota', Icon: FileText },
		{ v: 'link' as FormType, label: 'Link', Icon: LinkIcon }
	];

	const MISSION_TYPES = [
		{ v: 'goal' as FormType, label: 'Missão', Icon: Target },
		{ v: 'milestone' as FormType, label: 'Marco', Icon: Flag }
	];

	const FINANCE_TYPES = [
		{ v: 'transaction' as FormType, label: 'Transação', Icon: ArrowRightLeft },
		{ v: 'wallet' as FormType, label: 'Carteira', Icon: WalletIcon }
	];
</script>

<form class="space-y-3" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>

	{#if activeSection === 'operations'}
		<!-- Type tabs -->
		<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(6,182,212,0.08)">
			{#each OPS_TYPES as opt (opt.v)}
				<button
					type="button"
					onclick={() => (selectedType = opt.v)}
					class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-150"
					style={selectedType === opt.v
						? 'background: rgba(6,182,212,0.15); color: #06b6d4; border: 1px solid rgba(6,182,212,0.3)'
						: 'background: transparent; color: var(--color-base-content); opacity: 0.4; border: 1px solid transparent'}
				>
					<opt.Icon size={11} />
					{opt.label}
				</button>
			{/each}
		</div>

		{#if selectedType === 'link'}
			<input class="input input-sm input-bordered w-full" style={S.cyan} type="text" placeholder="Título (opcional)" bind:value={linkTitle} />
			<input class="input input-sm input-bordered w-full" style={S.cyan} type="url"  placeholder="https://exemplo.com" bind:value={content} required />
		{:else}
			<textarea
				class="textarea textarea-bordered h-24 resize-none text-sm w-full"
				style={S.cyan}
				placeholder={selectedType === 'task' ? 'Ex: Revisar relatório...' : 'Escreva sua nota...'}
				bind:value={content}
			></textarea>
		{/if}

	{:else if activeSection === 'missions'}
		<!-- Type tabs -->
		<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(139,92,246,0.1)">
			{#each MISSION_TYPES as opt (opt.v)}
				<button
					type="button"
					onclick={() => (selectedType = opt.v)}
					class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-150"
					style={selectedType === opt.v
						? 'background: rgba(139,92,246,0.15); color: #8b5cf6; border: 1px solid rgba(139,92,246,0.3)'
						: 'background: transparent; color: var(--color-base-content); opacity: 0.4; border: 1px solid transparent'}
				>
					<opt.Icon size={11} />
					{opt.label}
				</button>
			{/each}
		</div>

		{#if selectedType === 'goal'}
			<input class="input input-sm input-bordered w-full" style={S.violet} type="text" placeholder="Ex: Aprender Rust" bind:value={goalTitle} required />
		{:else}
			<select class="select select-sm select-bordered w-full" style={S.violet} bind:value={milestoneGoalId} required>
				<option value="" disabled>Selecione a missão</option>
				{#each goals as g (g.id)}
					<option value={g.id}>{g.title}</option>
				{/each}
			</select>
			<input class="input input-sm input-bordered w-full" style={S.violet} type="text" placeholder="Ex: Completar o capítulo 3" bind:value={milestoneTitle} required />
		{/if}

	{:else if activeSection === 'finance'}
		<!-- Type tabs -->
		<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(56,189,248,0.1)">
			{#each FINANCE_TYPES as opt (opt.v)}
				<button
					type="button"
					onclick={() => (selectedType = opt.v)}
					class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-150"
					style={selectedType === opt.v
						? 'background: rgba(56,189,248,0.15); color: #38bdf8; border: 1px solid rgba(56,189,248,0.3)'
						: 'background: transparent; color: var(--color-base-content); opacity: 0.4; border: 1px solid transparent'}
				>
					<opt.Icon size={11} />
					{opt.label}
				</button>
			{/each}
		</div>

		{#if selectedType === 'transaction'}
			<select class="select select-sm select-bordered w-full" style={S.blue} bind:value={txType}>
				<option value="expense">Despesa (Saída)</option>
				<option value="income">Receita (Entrada)</option>
			</select>
			<select class="select select-sm select-bordered w-full" style={S.blue} bind:value={txWalletId} required>
				<option value="" disabled>Selecione a carteira</option>
				{#each wallets as w (w.id)}
					<option value={w.id}>{w.emoji} {w.name} ({w.currency})</option>
				{/each}
			</select>
			<div class="grid grid-cols-2 gap-2">
				<input class="input input-sm input-bordered w-full" style={S.blue} type="number" step="0.01" placeholder="Valor" bind:value={txAmount} required />
				<input class="input input-sm input-bordered w-full" style={S.blue} type="text" placeholder="Categoria" bind:value={txCategory} required />
			</div>
			<input class="input input-sm input-bordered w-full" style={S.blue} type="text" placeholder="Descrição (opcional)" bind:value={txDescription} />
		{:else if selectedType === 'wallet'}
			<input class="input input-sm input-bordered w-full" style={S.blue} type="text" placeholder="Nome da Carteira" bind:value={walletName} required />
			<div class="grid grid-cols-2 gap-2">
				<select class="select select-sm select-bordered w-full" style={S.blue} bind:value={walletType} required>
					<option value="cash">Cash (Dinheiro)</option>
					<option value="vr">VR/VA (Benefício)</option>
					<option value="inflow">Inflow (Receita)</option>
				</select>
				<input class="input input-sm input-bordered w-full" style={S.blue} type="text" placeholder="Emoji (ex: 💰)" bind:value={walletEmoji} />
			</div>
		{/if}

	{:else if activeSection === 'protocols'}
		<!-- Habit form -->
		<div class="space-y-2">
			<div class="flex items-center gap-2">
				<input
					class="input input-sm input-bordered w-16 text-center text-lg"
					style="background: rgba(255,255,255,0.04); border-color: rgba(251,146,60,0.2)"
					type="text"
					placeholder="⚡"
					bind:value={habitEmoji}
					maxlength="2"
				/>
				<input
					class="input input-sm input-bordered flex-1"
					style="background: rgba(255,255,255,0.04); border-color: rgba(251,146,60,0.2)"
					type="text"
					placeholder="Ex: Meditar 10 minutos"
					bind:value={habitName}
					required
				/>
			</div>
			<p class="text-[10px] text-base-content/25 pl-1">Protocolos são hábitos diários com contagem de streak 🔥</p>
		</div>

	{:else if activeSection === 'wishlist'}

		<div class="relative">
			<input
				class="input input-sm input-bordered w-full pr-8"
				style={S.teal}
				type="url"
				placeholder="https://loja.com/produto"
				bind:value={wishlistUrl}
				onblur={handleWishlistBlur}
				required
			/>
			{#if wishlistFetching}
				<Loader2 size={14} class="absolute right-2 top-1/2 -translate-y-1/2 text-primary animate-spin" />
			{/if}
		</div>

		{#if wishlistPreview}
			<div class="rounded-lg p-3 space-y-2" style="background: rgba(34,211,238,0.05); border: 1px solid rgba(34,211,238,0.15)">
				<p class="text-[10px] font-semibold uppercase tracking-widest text-accent/60">Preview</p>
				{#if wishlistPreview.imageUrl}
					<img src={wishlistPreview.imageUrl} alt="preview" class="h-24 w-full object-cover rounded-md" />
				{/if}
				<p class="text-sm font-medium leading-snug">{wishlistPreview.title}</p>
				{#if wishlistPreview.description}
					<p class="text-xs text-base-content/40 line-clamp-2">{wishlistPreview.description}</p>
				{/if}
				<div class="grid grid-cols-2 gap-2">
					<input type="number" step="0.01" class="input input-xs input-bordered" style={S.plain} placeholder="Preço atual" bind:value={wishlistPreview.currentPrice} />
					<input type="number" step="0.01" class="input input-xs input-bordered" style={S.plain} placeholder="Meta" bind:value={wishlistPreview.targetPrice} />
				</div>
			</div>
		{/if}
	{/if}

	<button
		type="submit"
		class="btn btn-sm w-full font-semibold mt-1"
		style="background: rgba(6,182,212,0.15); border-color: rgba(6,182,212,0.35); color: #06b6d4"
	>
		<Plus size={14} />
		{submitLabel}
	</button>
</form>
