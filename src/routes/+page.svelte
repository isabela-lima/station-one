<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { pb } from '$lib/pb';
	import GoalCard from '$lib/components/GoalCard.svelte';
	import ItemCard from '$lib/components/ItemCard.svelte';
	import WishlistCard from '$lib/components/WishlistCard.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import { showToast } from '$lib/toast';
	import type { Goal, Item, Milestone, WishlistItem } from '$lib/types';
	import {
		Plus,
		Zap,
		Target,
		ShoppingBag,
		LogOut,
		Trash2,
		Loader2,
		Link,
		FileText,
		CheckSquare,
		Flag,
		Star,
		Satellite
	} from 'lucide-svelte';

	// ─── State ────────────────────────────────────────────
	let items = $state<Item[]>([]);
	let goals = $state<Goal[]>([]);
	let milestones = $state<Milestone[]>([]);
	let wishlist = $state<WishlistItem[]>([]);

	let currentDate = $state('');
	let currentTime = $state('');
	let loading = $state(true);
	let userId = $state('');
	let userName = $state('');

	// Sidebar nav
	type Section = 'operations' | 'missions' | 'wishlist';
	let activeSection = $state<Section>('operations');

	// Mobile form sheet
	let showMobileForm = $state(false);

	function openMobileForm() {
		showMobileForm = true;
	}
	function closeMobileForm() {
		showMobileForm = false;
	}

	// Form state
	type FormType = 'note' | 'task' | 'link' | 'goal' | 'milestone' | 'wishlist';
	let selectedType = $state<FormType>('task');
	let content = $state('');
	let linkTitle = $state('');
	let goalsFormTitle = $state('');
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

	function toast(message: string, type: 'success' | 'error' | 'info' = 'success') {
		showToast(message, type);
	}

	// ─── Date / Time ──────────────────────────────────────
	function updateDateTime() {
		const now = new Date();
		currentDate = now.toLocaleDateString('pt-BR', {
			weekday: 'long',
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
		currentTime = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
	}

	// ─── Derived ──────────────────────────────────────────
	const focusItems = $derived(items.filter((i) => i.type === 'task' && i.priority && !i.completed));
	const completedTasks = $derived(items.filter((i) => i.type === 'task' && i.completed));
	const hasCompleted = $derived(completedTasks.length > 0);

	// ─── Handlers: Items ──────────────────────────────────
	async function handleToggleItem(id: string) {
		const item = items.find((i) => i.id === id);
		if (!item) return;
		await pb.collection('items').update(id, { completed: !item.completed });
	}

	async function handleDeleteItem(id: string) {
		await pb.collection('items').delete(id);
		toast('Operação removida.');
	}

	async function handleTogglePriority(id: string) {
		const item = items.find((i) => i.id === id);
		if (!item) return;
		await pb.collection('items').update(id, { priority: !item.priority });
		toast(item.priority ? 'Removido do foco.' : 'Marcado como foco!', 'info');
	}

	async function handleClearCompleted() {
		await Promise.all(completedTasks.map((t) => pb.collection('items').delete(t.id)));
		toast(`${completedTasks.length} operação(ões) concluída(s) removida(s).`);
	}

	// ─── Handlers: Goals / Milestones ────────────────────
	async function handleToggleMilestone(milestoneId: string) {
		const milestone = milestones.find((m) => m.id === milestoneId);
		if (!milestone) return;
		await pb.collection('milestones').update(milestoneId, { completed: !milestone.completed });
	}

	async function handleDeleteGoal(goalId: string) {
		// Also delete related milestones
		const related = milestones.filter((m) => m.goal === goalId);
		await Promise.all([
			pb.collection('goals').delete(goalId),
			...related.map((m) => pb.collection('milestones').delete(m.id))
		]);
		toast('Missão removida.');
	}

	async function handleDeleteMilestone(milestoneId: string) {
		await pb.collection('milestones').delete(milestoneId);
		toast('Marco removido.');
	}

	// ─── Handlers: Wishlist ───────────────────────────────
	async function handleDeleteWishlist(id: string) {
		await pb.collection('wishlist').delete(id);
		toast('Item removido da wishlist.');
	}

	// ─── Wishlist URL Scraping ────────────────────────────
	async function handleWishlistUrlBlur() {
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
			// Silently fail — user can fill manually
		} finally {
			wishlistFetching = false;
		}
	}

	// ─── Form Submit ──────────────────────────────────────
	async function handleSubmit() {
		if (selectedType === 'note' || selectedType === 'task') {
			if (!content.trim()) return;
			await pb.collection('items').create({
				type: selectedType,
				content: content.trim(),
				completed: false,
				priority: false,
				user: userId
			});
			content = '';
			toast(`${selectedType === 'task' ? 'Operação' : 'Nota'} criada!`);
		} else if (selectedType === 'link') {
			if (!content.trim()) return;
			await pb.collection('items').create({
				type: 'link',
				content: content.trim(),
				title: linkTitle.trim() || undefined,
				completed: false,
				user: userId
			});
			content = '';
			linkTitle = '';
			toast('Link adicionado!');
		} else if (selectedType === 'goal') {
			if (!goalsFormTitle.trim()) return;
			await pb.collection('goals').create({ title: goalsFormTitle.trim(), user: userId });
			goalsFormTitle = '';
			toast('Missão criada!');
		} else if (selectedType === 'milestone') {
			if (!milestoneTitle.trim() || !milestoneGoalId) return;
			await pb.collection('milestones').create({
				title: milestoneTitle.trim(),
				goal: milestoneGoalId,
				completed: false,
				user: userId
			});
			milestoneTitle = '';
			toast('Marco adicionado!');
		} else if (selectedType === 'wishlist') {
			const title = wishlistPreview?.title || wishlistUrl;
			if (!wishlistUrl.trim()) return;
			await pb.collection('wishlist').create({
				title,
				url: wishlistUrl.trim(),
				imageUrl: wishlistPreview?.imageUrl || undefined,
				description: wishlistPreview?.description || undefined,
				currentPrice: parseFloat(wishlistPreview?.currentPrice ?? '') || 0,
				targetPrice: parseFloat(wishlistPreview?.targetPrice ?? '') || 0,
				user: userId
			});
			wishlistUrl = '';
			wishlistPreview = null;
			toast('Item adicionado à wishlist!');
		}
	}

	// ─── PocketBase Realtime ──────────────────────────────
	const unsubscribers: (() => void)[] = [];

	onMount(async () => {
		userId = pb.authStore.model?.id ?? '';
		userName = pb.authStore.model?.name ?? pb.authStore.model?.email?.split('@')[0] ?? 'Astronauta';
		if (!userId) {
			goto('/login');
			return;
		}

		updateDateTime();
		const timer = setInterval(updateDateTime, 1000);

		const [fetchedItems, fetchedGoals, fetchedWishlist] = await Promise.all([
			pb.collection('items').getFullList<Item>({ filter: `user = '${userId}'`, sort: '-created' }),
			pb.collection('goals').getFullList<Goal>({ filter: `user = '${userId}'` }),
			pb.collection('wishlist').getFullList<WishlistItem>({
				filter: `user = '${userId}'`,
				sort: '-created'
			})
		]);

		items = fetchedItems;
		goals = fetchedGoals;
		wishlist = fetchedWishlist;

		// Fetch milestones filtered by the user's own goals
		if (fetchedGoals.length > 0) {
			const goalIds = fetchedGoals.map((g) => `goal = '${g.id}'`).join(' || ');
			milestones = await pb.collection('milestones').getFullList<Milestone>({ filter: goalIds });
		} else {
			milestones = [];
		}
		loading = false;

		// Realtime subscriptions
		const unsubItems = await pb.collection('items').subscribe<Item>('*', ({ action, record }) => {
			if (record.user !== userId) return;
			if (action === 'create') items = [record, ...items];
			else if (action === 'update') items = items.map((i) => (i.id === record.id ? record : i));
			else if (action === 'delete') items = items.filter((i) => i.id !== record.id);
		});

		const unsubGoals = await pb.collection('goals').subscribe<Goal>('*', ({ action, record }) => {
			if (record.user !== userId) return;
			if (action === 'create') goals = [record, ...goals];
			else if (action === 'update') goals = goals.map((g) => (g.id === record.id ? record : g));
			else if (action === 'delete') goals = goals.filter((g) => g.id !== record.id);
		});

		// Subscribe to milestones only if the user has goals — filter by known goal IDs
		const userGoalIds = new Set(fetchedGoals.map((g) => g.id));
		const unsubMilestones = await pb
			.collection('milestones')
			.subscribe<Milestone>('*', ({ action, record }) => {
				// Only handle milestones that belong to this user's goals
				if (!userGoalIds.has(record.goal)) return;
				if (action === 'create') milestones = [...milestones, record];
				else if (action === 'update')
					milestones = milestones.map((m) => (m.id === record.id ? record : m));
				else if (action === 'delete') milestones = milestones.filter((m) => m.id !== record.id);
			});

		const unsubWishlist = await pb
			.collection('wishlist')
			.subscribe<WishlistItem>('*', ({ action, record }) => {
				if (record.user !== userId) return;
				if (action === 'create') wishlist = [record, ...wishlist];
				else if (action === 'update')
					wishlist = wishlist.map((w) => (w.id === record.id ? record : w));
				else if (action === 'delete') wishlist = wishlist.filter((w) => w.id !== record.id);
			});

		unsubscribers.push(
			() => clearInterval(timer),
			() => unsubItems(),
			() => unsubGoals(),
			() => unsubMilestones(),
			() => unsubWishlist()
		);
	});

	onDestroy(() => {
		unsubscribers.forEach((fn) => fn());
	});

	function milestonesForGoal(goalId: string) {
		return milestones.filter((m) => m.goal === goalId);
	}

	function handleLogout() {
		pb.authStore.clear();
		goto('/login');
	}

	// Nav items
	const navItems = [
		{ id: 'operations' as Section, label: 'Operações', icon: Zap },
		{ id: 'missions' as Section, label: 'Missões', icon: Target },
		{ id: 'wishlist' as Section, label: 'Wishlist', icon: ShoppingBag }
	];

	// Auto-select form type when nav changes
	$effect(() => {
		if (activeSection === 'operations') selectedType = 'task';
		else if (activeSection === 'missions') selectedType = 'goal';
		else if (activeSection === 'wishlist') selectedType = 'wishlist';
	});

	// Close mobile form and submit
	async function handleMobileSubmit() {
		await handleSubmit();
		showMobileForm = false;
	}

	// User avatar initials
	const initials = $derived(
		userName
			.split(' ')
			.slice(0, 2)
			.map((w: string) => w[0])
			.join('')
			.toUpperCase()
	);
</script>

<div class="h-screen flex flex-col lg:flex-row font-sans overflow-hidden">
	<!-- ─── MAIN CONTENT ──────────────────────────────── -->
	<!-- Padding bottom on mobile for the fixed bottom nav -->
	<main class="flex-1 flex flex-col overflow-y-auto pb-20 lg:pb-0">
		<!-- Header -->
		<header class="flex items-end justify-between px-8 pt-8 pb-6">
			<div class="flex items-center gap-3">
				<div
					class="flex h-9 w-9 items-center justify-center rounded-full"
					style="background: rgba(6,182,212,0.12); border: 1px solid rgba(6,182,212,0.25)"
				>
					<Satellite size={18} class="text-primary" />
				</div>
				<div>
					<div class="text-xs font-medium tracking-widest uppercase text-primary/60">Station One</div>
					<div class="text-xs text-base-content/30 capitalize">{currentDate}</div>
				</div>
			</div>
			<div class="text-right">
				<div class="clock-display text-5xl lg:text-6xl font-bold leading-none">{currentTime}</div>
			</div>
		</header>

		<!-- Foco do Dia banner -->
		{#if focusItems.length > 0}
			<section class="px-8 pb-4">
				<div
					class="rounded-xl p-4"
					style="background: rgba(6,182,212,0.06); border: 1px solid rgba(6,182,212,0.2)"
				>
					<div class="mb-3 flex items-center gap-2">
						<Star size={14} class="text-warning" fill="currentColor" />
						<span class="text-xs font-semibold uppercase tracking-widest text-warning/80">Foco de Hoje</span>
					</div>
					<div class="space-y-2">
						{#each focusItems as item (item.id)}
							<label class="flex cursor-pointer items-center gap-3">
								<input
									type="checkbox"
									class="checkbox checkbox-sm border-primary/40 checked:border-primary checked:bg-primary"
									checked={item.completed}
									onchange={() => handleToggleItem(item.id)}
								/>
								<span class="text-sm font-medium">{item.content}</span>
							</label>
						{/each}
					</div>
				</div>
			</section>
		{/if}

		<!-- Section: Operações -->
		{#if activeSection === 'operations'}
			<section class="flex-1 px-8 pb-8">
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-2">
						<Zap size={16} class="text-primary" />
						<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Operações</h2>
						<span
							class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums"
							style="background: rgba(6,182,212,0.12); color: #06b6d4"
						>
							{items.length}
						</span>
					</div>
					{#if hasCompleted}
						<button
							onclick={handleClearCompleted}
							class="btn btn-ghost btn-xs gap-1 text-base-content/40 hover:text-error"
						>
							<Trash2 size={12} />
							Limpar concluídas ({completedTasks.length})
						</button>
					{/if}
				</div>

				{#if loading}
					<div class="space-y-3">
						{#each [1, 2, 3] as i (i)}
							<div class="skeleton-pulse h-16 w-full" style="animation-delay: {i * 100}ms"></div>
						{/each}
					</div>
				{:else}
					<div class="space-y-3">
						{#each items as item, i (item.id)}
							<ItemCard
								{item}
								index={i}
								onToggle={handleToggleItem}
								onDelete={handleDeleteItem}
								onTogglePriority={handleTogglePriority}
							/>
						{/each}
						{#if items.length === 0}
							<div class="flex flex-col items-center gap-3 py-16 text-base-content/25">
								<Zap size={32} />
								<p class="text-sm">Nenhuma operação ainda.<br />Adicione uma pela barra lateral.</p>
							</div>
						{/if}
					</div>
				{/if}
			</section>

		<!-- Section: Missões -->
		{:else if activeSection === 'missions'}
			<section class="flex-1 px-8 pb-8">
				<div class="mb-4 flex items-center gap-2">
					<Target size={16} class="text-secondary" />
					<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Missões</h2>
					<span
						class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums"
						style="background: rgba(139,92,246,0.15); color: #8b5cf6"
					>
						{goals.length}
					</span>
				</div>

				{#if loading}
					<div class="space-y-3">
						{#each [1, 2] as i (i)}
							<div class="skeleton-pulse h-28 w-full" style="animation-delay: {i * 100}ms"></div>
						{/each}
					</div>
				{:else}
					<div class="space-y-4">
						{#each goals as goal, i (goal.id)}
							<GoalCard
								{goal}
								index={i}
								milestones={milestonesForGoal(goal.id)}
								onToggleMilestone={handleToggleMilestone}
								onDeleteGoal={handleDeleteGoal}
								onDeleteMilestone={handleDeleteMilestone}
							/>
						{/each}
						{#if goals.length === 0}
							<div class="flex flex-col items-center gap-3 py-16 text-base-content/25">
								<Target size={32} />
								<p class="text-sm text-center">Nenhuma missão ainda.<br />Defina seus objetivos de longo prazo.</p>
							</div>
						{/if}
					</div>
				{/if}
			</section>

		<!-- Section: Wishlist -->
		{:else if activeSection === 'wishlist'}
			<section class="flex-1 px-8 pb-8">
				<div class="mb-4 flex items-center gap-2">
					<ShoppingBag size={16} class="text-accent" />
					<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Wishlist</h2>
					<span
						class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums"
						style="background: rgba(34,211,238,0.12); color: #22d3ee"
					>
						{wishlist.length}
					</span>
				</div>

				{#if loading}
					<div class="space-y-3">
						{#each [1, 2, 3] as i (i)}
							<div class="skeleton-pulse h-20 w-full" style="animation-delay: {i * 100}ms"></div>
						{/each}
					</div>
				{:else}
					<div class="space-y-3">
						{#each wishlist as wishlistItem, i (wishlistItem.id)}
							<WishlistCard {wishlistItem} index={i} onDelete={handleDeleteWishlist} />
						{/each}
						{#if wishlist.length === 0}
							<div class="flex flex-col items-center gap-3 py-16 text-base-content/25">
								<ShoppingBag size={32} />
								<p class="text-sm text-center">Wishlist vazia.<br />Cole uma URL para adicionar itens.</p>
							</div>
						{/if}
					</div>
				{/if}
			</section>
		{/if}
	</main>

	<!-- ─── SIDEBAR (desktop only) ──────────────────── -->
	<aside class="glass-sidebar hidden lg:flex lg:w-[340px] flex-col">
		<!-- User header -->
		<div
			class="flex items-center justify-between p-6"
			style="border-bottom: 1px solid rgba(6,182,212,0.08)"
		>
			<div class="flex items-center gap-3">
				<div
					class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-sm font-bold text-primary"
					style="background: rgba(6,182,212,0.12); border: 1px solid rgba(6,182,212,0.25)"
				>
					{initials}
				</div>
				<div>
					<div class="text-sm font-semibold leading-tight">{userName}</div>
					<div class="text-[10px] uppercase tracking-widest text-primary/50">Tenente</div>
				</div>
			</div>
			<button
				onclick={handleLogout}
				class="btn btn-ghost btn-sm gap-1.5 text-base-content/40 hover:text-error"
				title="Sair"
				aria-label="Logout"
			>
				<LogOut size={15} />
				<span class="text-xs">Sair</span>
			</button>
		</div>

		<!-- Nav -->
		<nav class="flex gap-1 p-3" style="border-bottom: 1px solid rgba(6,182,212,0.08)">
			{#each navItems as nav (nav.id)}
				<button
					onclick={() => (activeSection = nav.id)}
					class="flex flex-1 flex-col items-center gap-1 rounded-lg py-2.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-200"
					class:text-primary={activeSection === nav.id}
					class:text-base-content={activeSection !== nav.id}
					style={activeSection === nav.id
						? 'background: rgba(6,182,212,0.1); border: 1px solid rgba(6,182,212,0.2); opacity: 1'
						: 'background: transparent; border: 1px solid transparent; opacity: 0.4'}
				>
					<nav.icon size={16} />
					{nav.label}
				</button>
			{/each}
		</nav>

		<!-- Sidebar form -->
		<div class="flex-1 overflow-y-auto p-6">
			<div class="mb-4 flex items-center gap-2">
				<Plus size={14} class="text-primary/60" />
				<h2 class="text-xs font-semibold uppercase tracking-widest text-base-content/50">
					{activeSection === 'operations'
						? 'Nova Operação'
						: activeSection === 'missions'
							? 'Nova Missão'
							: 'Adicionar à Wishlist'}
				</h2>
			</div>

			<form
				class="space-y-3"
				onsubmit={(e) => {
					e.preventDefault();
					handleSubmit();
				}}
			>
				<!-- Operations form -->
				{#if activeSection === 'operations'}
					<!-- Type selector (tab-style) -->
					<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(6,182,212,0.08)">
						{#each [{ v: 'task', label: 'Tarefa', icon: CheckSquare }, { v: 'note', label: 'Nota', icon: FileText }, { v: 'link', label: 'Link', icon: Link }] as opt (opt.v)}
							<button
								type="button"
								onclick={() => (selectedType = opt.v as FormType)}
								class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-150"
								style={selectedType === opt.v
									? 'background: rgba(6,182,212,0.15); color: #06b6d4; border: 1px solid rgba(6,182,212,0.3)'
									: 'background: transparent; color: var(--color-base-content); opacity: 0.4; border: 1px solid transparent'}
							>
								<opt.icon size={11} />
								{opt.label}
							</button>
						{/each}
					</div>

					{#if selectedType === 'link'}
						<div class="form-control">
							<label class="label pb-1" for="link-title">
								<span class="label-text text-xs text-base-content/50">Título (opcional)</span>
							</label>
							<input
								id="link-title"
								type="text"
								class="input input-sm input-bordered"
								style="background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)"
								placeholder="Nome do link"
								bind:value={linkTitle}
							/>
						</div>
						<div class="form-control">
							<label class="label pb-1" for="link-url">
								<span class="label-text text-xs text-base-content/50">URL *</span>
							</label>
							<input
								id="link-url"
								type="url"
								class="input input-sm input-bordered"
								style="background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)"
								placeholder="https://exemplo.com"
								bind:value={content}
								required
							/>
						</div>
					{:else}
						<div class="form-control">
							<label class="label pb-1" for="content-text">
								<span class="label-text text-xs text-base-content/50">
									{selectedType === 'task' ? 'Descrição da tarefa' : 'Conteúdo da nota'}
								</span>
							</label>
							<textarea
								id="content-text"
								class="textarea textarea-bordered h-24 resize-none text-sm"
								style="background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)"
								placeholder={selectedType === 'task' ? 'Ex: Revisar relatório...' : 'Escreva sua nota...'}
								bind:value={content}
							></textarea>
						</div>
					{/if}

				<!-- Missions form -->
				{:else if activeSection === 'missions'}
					<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(139,92,246,0.1)">
						{#each [{ v: 'goal', label: 'Missão', icon: Target }, { v: 'milestone', label: 'Marco', icon: Flag }] as opt (opt.v)}
							<button
								type="button"
								onclick={() => (selectedType = opt.v as FormType)}
								class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-1.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-150"
								style={selectedType === opt.v
									? 'background: rgba(139,92,246,0.15); color: #8b5cf6; border: 1px solid rgba(139,92,246,0.3)'
									: 'background: transparent; color: var(--color-base-content); opacity: 0.4; border: 1px solid transparent'}
							>
								<opt.icon size={11} />
								{opt.label}
							</button>
						{/each}
					</div>

					{#if selectedType === 'goal'}
						<div class="form-control">
							<label class="label pb-1" for="goal-title">
								<span class="label-text text-xs text-base-content/50">Nome da missão *</span>
							</label>
							<input
								id="goal-title"
								type="text"
								class="input input-sm input-bordered"
								style="background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)"
								placeholder="Ex: Aprender Rust"
								bind:value={goalsFormTitle}
								required
							/>
						</div>
					{:else}
						<div class="form-control">
							<label class="label pb-1" for="ms-goal">
								<span class="label-text text-xs text-base-content/50">Missão *</span>
							</label>
							<select
								id="ms-goal"
								class="select select-sm select-bordered"
								style="background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)"
								bind:value={milestoneGoalId}
								required
							>
								<option value="" disabled>Selecione a missão</option>
								{#each goals as g (g.id)}
									<option value={g.id}>{g.title}</option>
								{/each}
							</select>
						</div>
						<div class="form-control">
							<label class="label pb-1" for="ms-title">
								<span class="label-text text-xs text-base-content/50">Título do marco *</span>
							</label>
							<input
								id="ms-title"
								type="text"
								class="input input-sm input-bordered"
								style="background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)"
								placeholder="Ex: Completar o capítulo 3"
								bind:value={milestoneTitle}
								required
							/>
						</div>
					{/if}

				<!-- Wishlist form -->
				{:else if activeSection === 'wishlist'}
					<div class="form-control">
						<label class="label pb-1" for="wl-url">
							<span class="label-text text-xs text-base-content/50">URL do produto *</span>
						</label>
						<div class="relative">
							<input
								id="wl-url"
								type="url"
								class="input input-sm input-bordered w-full pr-8"
								style="background: rgba(255,255,255,0.04); border-color: rgba(34,211,238,0.2)"
								placeholder="https://loja.com/produto"
								bind:value={wishlistUrl}
								onblur={handleWishlistUrlBlur}
								required
							/>
							{#if wishlistFetching}
								<div class="absolute right-2 top-1/2 -translate-y-1/2">
									<Loader2 size={14} class="text-primary animate-spin" />
								</div>
							{/if}
						</div>
					</div>

					{#if wishlistPreview}
						<div
							class="rounded-lg p-3 space-y-2"
							style="background: rgba(34,211,238,0.05); border: 1px solid rgba(34,211,238,0.15)"
						>
							<p class="text-[10px] font-semibold uppercase tracking-widest text-accent/60">Preview</p>
							{#if wishlistPreview.imageUrl}
								<img
									src={wishlistPreview.imageUrl}
									alt="preview"
									class="h-24 w-full object-cover rounded-md"
								/>
							{/if}
							<p class="text-sm font-medium leading-snug">{wishlistPreview.title}</p>
							{#if wishlistPreview.description}
								<p class="text-xs text-base-content/40 line-clamp-2">{wishlistPreview.description}</p>
							{/if}
							<div class="grid grid-cols-2 gap-2">
								<div class="form-control">
									<label class="label pb-1" for="wl-cur">
										<span class="label-text text-[10px] text-base-content/40">Preço atual</span>
									</label>
									<input
										id="wl-cur"
										type="number"
										step="0.01"
										class="input input-xs input-bordered"
										style="background: rgba(255,255,255,0.04)"
										placeholder="0,00"
										bind:value={wishlistPreview.currentPrice}
									/>
								</div>
								<div class="form-control">
									<label class="label pb-1" for="wl-tgt">
										<span class="label-text text-[10px] text-base-content/40">Meta</span>
									</label>
									<input
										id="wl-tgt"
										type="number"
										step="0.01"
										class="input input-xs input-bordered"
										style="background: rgba(255,255,255,0.04)"
										placeholder="0,00"
										bind:value={wishlistPreview.targetPrice}
									/>
								</div>
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
					{activeSection === 'operations'
						? 'Criar Operação'
						: activeSection === 'missions'
							? selectedType === 'goal'
								? 'Criar Missão'
								: 'Criar Marco'
							: 'Adicionar à Wishlist'}
				</button>
			</form>
		</div>

		<!-- Footer status -->
		<div
			class="px-6 py-3 flex items-center gap-2"
			style="border-top: 1px solid rgba(6,182,212,0.08)"
		>
			<div
				class="h-1.5 w-1.5 rounded-full animate-pulse"
				style="background: #06b6d4; box-shadow: 0 0 6px #06b6d4"
			></div>
			<span class="text-[10px] uppercase tracking-widest text-base-content/25">Sistema online</span>
		</div>
	</aside>
</div>

<!-- ─── MOBILE: Bottom Navigation Bar ─────────────────── -->
<nav
	class="lg:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center justify-around px-2 pb-safe"
	style="background: rgba(10,10,20,0.95); backdrop-filter: blur(20px); border-top: 1px solid rgba(6,182,212,0.12); height: 64px;"
>
	{#each navItems as nav (nav.id)}
		<button
			onclick={() => { activeSection = nav.id; showMobileForm = false; }}
			class="flex flex-col items-center gap-1 px-4 py-2 rounded-xl text-[10px] font-semibold uppercase tracking-wide transition-all duration-200"
			style={activeSection === nav.id
				? 'color: #06b6d4;'
				: 'color: rgba(226,232,240,0.35);'}
		>
			<nav.icon size={18} />
			{nav.label}
		</button>
	{/each}

	<!-- FAB -->
	<button
		onclick={openMobileForm}
		class="flex items-center justify-center w-12 h-12 rounded-full shadow-lg transition-transform duration-200 active:scale-95"
		style="background: linear-gradient(135deg, rgba(6,182,212,0.9), rgba(139,92,246,0.9)); box-shadow: 0 0 20px rgba(6,182,212,0.3);"
		aria-label="Adicionar"
	>
		<Plus size={20} class="text-white" />
	</button>
</nav>

<!-- ─── MOBILE: Bottom Sheet Form ──────────────────────── -->
{#if showMobileForm}
	<!-- Backdrop -->
	<div
		class="lg:hidden fixed inset-0 z-40"
		style="background: rgba(0,0,0,0.6); backdrop-filter: blur(4px);"
		onclick={closeMobileForm}
		aria-label="Fechar"
		role="button"
		tabindex="-1"
	></div>

	<!-- Sheet -->
	<div
		class="lg:hidden fixed bottom-0 left-0 right-0 z-50 rounded-t-2xl flex flex-col"
		style="background: #0f0f1c; border-top: 1px solid rgba(6,182,212,0.2); max-height: 85vh;"
	>
		<!-- Sheet handle -->
		<div class="flex justify-center pt-3 pb-1">
			<div class="w-10 h-1 rounded-full" style="background: rgba(6,182,212,0.25)"></div>
		</div>

		<!-- Sheet header -->
		<div class="flex items-center justify-between px-5 pt-2 pb-4">
			<div class="flex items-center gap-2">
				<Plus size={14} class="text-primary/60" />
				<span class="text-xs font-semibold uppercase tracking-widest text-base-content/50">
					{activeSection === 'operations'
						? 'Nova Operação'
						: activeSection === 'missions'
							? 'Nova Missão'
							: 'Adicionar à Wishlist'}
				</span>
			</div>
			<button
				onclick={closeMobileForm}
				class="btn btn-ghost btn-sm btn-circle text-base-content/40"
				aria-label="Fechar"
			>
				<svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
				</svg>
			</button>
		</div>

		<!-- Sheet form (scrollable) -->
		<div class="overflow-y-auto px-5 pb-8">
			<form
				class="space-y-3"
				onsubmit={(e) => { e.preventDefault(); handleMobileSubmit(); }}
			>
				{#if activeSection === 'operations'}
					<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(6,182,212,0.08)">
						{#each [{ v: 'task', label: 'Tarefa', icon: CheckSquare }, { v: 'note', label: 'Nota', icon: FileText }, { v: 'link', label: 'Link', icon: Link }] as opt (opt.v)}
							<button
								type="button"
								onclick={() => (selectedType = opt.v as FormType)}
								class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-[10px] font-semibold uppercase tracking-wide transition-all duration-150"
								style={selectedType === opt.v
									? 'background: rgba(6,182,212,0.15); color: #06b6d4; border: 1px solid rgba(6,182,212,0.3)'
									: 'background: transparent; color: rgba(226,232,240,0.4); border: 1px solid transparent'}
							>
								<opt.icon size={12} />
								{opt.label}
							</button>
						{/each}
					</div>
					{#if selectedType === 'link'}
						<input type="text" class="input input-bordered w-full" style="background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)" placeholder="Título (opcional)" bind:value={linkTitle} />
						<input type="url" class="input input-bordered w-full" style="background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)" placeholder="https://exemplo.com" bind:value={content} required />
					{:else}
						<textarea
							class="textarea textarea-bordered w-full h-28 resize-none text-sm"
							style="background: rgba(255,255,255,0.04); border-color: rgba(6,182,212,0.15)"
							placeholder={selectedType === 'task' ? 'Descreva a operação...' : 'Escreva sua nota...'}
							bind:value={content}
						></textarea>
					{/if}

				{:else if activeSection === 'missions'}
					<div class="flex gap-1 rounded-lg p-1" style="background: rgba(255,255,255,0.04); border: 1px solid rgba(139,92,246,0.1)">
						{#each [{ v: 'goal', label: 'Missão', icon: Target }, { v: 'milestone', label: 'Marco', icon: Flag }] as opt (opt.v)}
							<button
								type="button"
								onclick={() => (selectedType = opt.v as FormType)}
								class="flex flex-1 items-center justify-center gap-1.5 rounded-md py-2 text-[10px] font-semibold uppercase tracking-wide transition-all"
								style={selectedType === opt.v
									? 'background: rgba(139,92,246,0.15); color: #8b5cf6; border: 1px solid rgba(139,92,246,0.3)'
									: 'background: transparent; color: rgba(226,232,240,0.4); border: 1px solid transparent'}
							>
								<opt.icon size={12} />
								{opt.label}
							</button>
						{/each}
					</div>
					{#if selectedType === 'goal'}
						<input type="text" class="input input-bordered w-full" style="background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)" placeholder="Nome da missão" bind:value={goalsFormTitle} required />
					{:else}
						<select class="select select-bordered w-full" style="background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)" bind:value={milestoneGoalId} required>
							<option value="" disabled>Selecione a missão</option>
							{#each goals as g (g.id)}
								<option value={g.id}>{g.title}</option>
							{/each}
						</select>
						<input type="text" class="input input-bordered w-full" style="background: rgba(255,255,255,0.04); border-color: rgba(139,92,246,0.2)" placeholder="Título do marco" bind:value={milestoneTitle} required />
					{/if}

				{:else if activeSection === 'wishlist'}
					<div class="relative">
						<input type="url" class="input input-bordered w-full pr-8" style="background: rgba(255,255,255,0.04); border-color: rgba(34,211,238,0.2)" placeholder="https://loja.com/produto" bind:value={wishlistUrl} onblur={handleWishlistUrlBlur} required />
						{#if wishlistFetching}
							<div class="absolute right-2 top-1/2 -translate-y-1/2"><Loader2 size={14} class="text-primary animate-spin" /></div>
						{/if}
					</div>
					{#if wishlistPreview}
						<div class="rounded-lg p-3 space-y-2" style="background: rgba(34,211,238,0.05); border: 1px solid rgba(34,211,238,0.15)">
							<p class="text-[10px] font-semibold uppercase tracking-widest text-accent/60">Preview</p>
							{#if wishlistPreview.imageUrl}
								<img src={wishlistPreview.imageUrl} alt="preview" class="h-20 w-full object-cover rounded-md" />
							{/if}
							<p class="text-sm font-medium">{wishlistPreview.title}</p>
							<div class="grid grid-cols-2 gap-2">
								<input type="number" step="0.01" class="input input-xs input-bordered" style="background: rgba(255,255,255,0.04)" placeholder="Preço atual" bind:value={wishlistPreview.currentPrice} />
								<input type="number" step="0.01" class="input input-xs input-bordered" style="background: rgba(255,255,255,0.04)" placeholder="Meta" bind:value={wishlistPreview.targetPrice} />
							</div>
						</div>
					{/if}
				{/if}

				<button
					type="submit"
					class="btn w-full font-semibold mt-2"
					style="background: rgba(6,182,212,0.15); border-color: rgba(6,182,212,0.35); color: #06b6d4"
				>
					<Plus size={16} />
					{activeSection === 'operations'
						? 'Criar Operação'
						: activeSection === 'missions'
							? selectedType === 'goal' ? 'Criar Missão' : 'Criar Marco'
							: 'Adicionar à Wishlist'}
				</button>
			</form>
		</div>
	</div>
{/if}

<!-- Toast component -->
<Toast />
