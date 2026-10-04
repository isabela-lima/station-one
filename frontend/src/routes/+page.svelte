<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';

	// ── Lib ─────────────────────────────────────────────
	import { supabase } from '$lib/supabase';
	import * as api from '$lib/api';
	import { showToast } from '$lib/toast';
	import type { Goal, Habit, Item, Milestone, WishlistItem, Section, FormType, FormPayload } from '$lib';

	// ── Components ───────────────────────────────────────
	import GoalCard from '$lib/components/GoalCard.svelte';
	import HabitCard from '$lib/components/HabitCard.svelte';
	import ItemCard from '$lib/components/ItemCard.svelte';
	import WishlistCard from '$lib/components/WishlistCard.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import DailyLog from '$lib/components/DailyLog.svelte';
	import AppSidebar from '$lib/components/dashboard/AppSidebar.svelte';
	import MobileNav from '$lib/components/dashboard/MobileNav.svelte';
	import MobileSheet from '$lib/components/dashboard/MobileSheet.svelte';
	import FinanceDashboard from '$lib/components/finance/FinanceDashboard.svelte';

	import { FlameKindling, Zap, Target, ShoppingBag, Star, Trash2, Satellite } from 'lucide-svelte';

	// ─── State ────────────────────────────────────────
	let items = $state<Item[]>([]);
	let goals = $state<Goal[]>([]);
	let milestones = $state<Milestone[]>([]);
	let wishlist = $state<WishlistItem[]>([]);
	let habits = $state<Habit[]>([]);

	let currentDate = $state('');
	let currentTime = $state('');
	let loading = $state(true);
	let userName = $state('');

	// ─── Weather ──────────────────────────────────────
	interface WeatherInfo { temp: number; emoji: string; }
	let weather = $state<WeatherInfo | null>(null);

	function weatherCodeToEmoji(code: number): string {
		if (code === 0) return '☀️';
		if (code <= 3) return '⛅';
		if (code <= 48) return '🌫️';
		if (code <= 67) return '🌧️';
		if (code <= 77) return '❄️';
		if (code <= 82) return '🌦️';
		if (code >= 95) return '⛈️';
		return '🌡️';
	}

	async function fetchWeather(lat: number, lon: number) {
		try {
			const res = await fetch(
				`https://api.open-meteo.com/v1/forecast?latitude=${lat}&longitude=${lon}&current=temperature_2m,weathercode`
			);
			const data = await res.json();
			const temp = Math.round(data.current.temperature_2m);
			const emoji = weatherCodeToEmoji(data.current.weathercode);
			weather = { temp, emoji };
		} catch {
			/* silently fail — clima é decorativo */
		}
	}

	function initWeather() {
		const cached = localStorage.getItem('weather_coords');
		if (cached) {
			const { lat, lon, ts } = JSON.parse(cached);
			// Cache válido por 30 minutos
			if (Date.now() - ts < 30 * 60 * 1000) {
				fetchWeather(lat, lon);
				return;
			}
		}
		if (!navigator.geolocation) return;
		navigator.geolocation.getCurrentPosition(
			({ coords }) => {
				const { latitude: lat, longitude: lon } = coords;
				localStorage.setItem('weather_coords', JSON.stringify({ lat, lon, ts: Date.now() }));
				fetchWeather(lat, lon);
			},
			() => { /* permissão negada — ok */ }
		);
	}

	let activeSection = $state<Section>('operations');
	let selectedType = $state<FormType>('task');
	let showMobileForm = $state(false);

	/** IDs de itens com ação em andamento (delete, toggle) */
	let pendingIds = $state<Set<string>>(new Set());

	// ─── Derived ──────────────────────────────────────
	const focusItems = $derived(items.filter((i) => i.type === 'task' && i.priority && !i.completed));
	const completedTasks = $derived(items.filter((i) => i.type === 'task' && i.completed));
	const initials = $derived(
		userName.split(' ').slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()
	);

	// ─── Date / Time ──────────────────────────────────
	function updateDateTime() {
		const now = new Date();
		currentDate = now.toLocaleDateString('pt-BR', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
		currentTime = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
	}

	// ─── Auto-select form type on section change ────────────────────────
	$effect(() => {
		if (activeSection === 'operations') selectedType = 'task';
		else if (activeSection === 'missions') selectedType = 'goal';
		else if (activeSection === 'wishlist') selectedType = 'wishlist';
		else if (activeSection === 'protocols') selectedType = 'habit';
	});

	// ─── Helpers ──────────────────────────────────────
	function setPending(id: string, on: boolean) {
		pendingIds = new Set(on ? [...pendingIds, id] : [...pendingIds].filter((x) => x !== id));
	}

	// ─── Handlers: Items ──────────────────────────────
	async function handleToggleItem(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			const item = items.find((i) => i.id === id);
			if (!item) return;
			const updated = await api.items.update(id, { completed: !item.completed });
			items = items.map((i) => (i.id === id ? updated : i));
		} catch {
			showToast('Erro ao atualizar item.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	async function handleDeleteItem(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			await api.items.delete(id);
			items = items.filter((i) => i.id !== id);
			showToast('Operação removida.');
		} catch {
			showToast('Erro ao remover operação.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	async function handleTogglePriority(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			const item = items.find((i) => i.id === id);
			if (!item) return;
			const updated = await api.items.update(id, { priority: !item.priority });
			items = items.map((i) => (i.id === id ? updated : i));
			showToast(item.priority ? 'Removido do foco.' : 'Marcado como foco!', 'info');
		} catch {
			showToast('Erro ao alterar prioridade.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	async function handleClearCompleted() {
		try {
			const count = completedTasks.length;
			await Promise.all(completedTasks.map((t) => api.items.delete(t.id)));
			items = items.filter((i) => !(i.type === 'task' && i.completed));
			showToast(`${count} tarefa(s) concluída(s) removida(s).`);
		} catch {
			showToast('Erro ao limpar tarefas.', 'error');
		}
	}

	// ─── Handlers: Goals / Milestones ────────────────
	async function handleToggleMilestone(milestoneId: string) {
		if (pendingIds.has(milestoneId)) return;
		setPending(milestoneId, true);
		try {
			const ms = milestones.find((m) => m.id === milestoneId);
			if (!ms) return;
			const updated = await api.milestones.update(milestoneId, { completed: !ms.completed });
			milestones = milestones.map((m) => (m.id === milestoneId ? updated : m));
		} catch {
			showToast('Erro ao atualizar marco.', 'error');
		} finally {
			setPending(milestoneId, false);
		}
	}

	async function handleDeleteGoal(goalId: string) {
		if (pendingIds.has(goalId)) return;
		setPending(goalId, true);
		try {
			await api.goals.delete(goalId); // CASCADE removes milestones on DB
			goals = goals.filter((g) => g.id !== goalId);
			milestones = milestones.filter((m) => m.goal_id !== goalId);
			showToast('Missão removida.');
		} catch {
			showToast('Erro ao remover missão.', 'error');
		} finally {
			setPending(goalId, false);
		}
	}

	async function handleDeleteMilestone(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			await api.milestones.delete(id);
			milestones = milestones.filter((m) => m.id !== id);
			showToast('Marco removido.');
		} catch {
			showToast('Erro ao remover marco.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	// ─── Handlers: Wishlist ───────────────────────────
	async function handleDeleteWishlist(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			await api.wishlist.delete(id);
			wishlist = wishlist.filter((w) => w.id !== id);
			showToast('Item removido da wishlist.');
		} catch {
			showToast('Erro ao remover item.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	// ─── Handlers: Habits ─────────────────────────────
	async function handleToggleHabit(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			const updated = await api.habits.toggleToday(id);
			habits = habits.map((h) => (h.id === id ? updated : h));
		} catch {
			showToast('Erro ao atualizar protocolo.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	async function handleDeleteHabit(id: string) {
		if (pendingIds.has(id)) return;
		setPending(id, true);
		try {
			await api.habits.delete(id);
			habits = habits.filter((h) => h.id !== id);
			showToast('Protocolo removido.');
		} catch {
			showToast('Erro ao remover protocolo.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	// Um toggle gera vários eventos realtime seguidos — agrupa num único refetch
	let habitsRefreshTimer: ReturnType<typeof setTimeout> | null = null;
	function scheduleHabitsRefresh() {
		if (habitsRefreshTimer) clearTimeout(habitsRefreshTimer);
		habitsRefreshTimer = setTimeout(async () => {
			habitsRefreshTimer = null;
			try {
				habits = await api.habits.list();
			} catch {
				/* silencioso — o próximo evento ou reload resolve */
			}
		}, 300);
	}

	// ─── Form Submit (dispatched from AddForm) ────────────

	async function handleFormSubmit(payload: FormPayload) {
		try {
			switch (payload.kind) {
				case 'item': {
					const created = await api.items.create({ type: payload.type, content: payload.content, title: payload.title, completed: false, priority: false });
					items = [created, ...items];
					const label = payload.type === 'task' ? 'Operação' : payload.type === 'note' ? 'Nota' : 'Link';
					showToast(`${label} criada!`);
					break;
				}
				case 'goal': {
					const created = await api.goals.create({ title: payload.title });
					goals = [...goals, created];
					showToast('Missão criada!');
					break;
				}
				case 'milestone': {
					const created = await api.milestones.create({ title: payload.title, goal_id: payload.goal_id });
					milestones = [...milestones, created];
					showToast('Marco adicionado!');
					break;
				}
				case 'wishlist': {
					const created = await api.wishlist.create({
						title: payload.title, url: payload.url,
						image_url: payload.image_url, description: payload.description,
						current_price: payload.current_price, target_price: payload.target_price,
						currency: payload.currency
					});
					wishlist = [created, ...wishlist];
					showToast('Item adicionado à wishlist!');
					break;
				}
				case 'transaction': {
					await api.finance.transactions.create({
						wallet_id: payload.wallet_id,
						amount: payload.amount,
						currency: payload.currency,
						category: payload.category,
						description: payload.description,
						date: payload.date,
						is_recurring: payload.is_recurring
					});
					showToast('Transação lançada com sucesso!');
					break;
				}
				case 'wallet': {
					await api.finance.wallets.create({
						name: payload.name,
						type: payload.type,
						emoji: payload.emoji,
						currency: payload.currency
					});
					showToast('Carteira criada com sucesso!');
					break;
				}
				case 'habit': {
					const created = await api.habits.create({ name: payload.name, emoji: payload.emoji });
					habits = [...habits, created];
					showToast('Protocolo criado! 🔥');
					break;
				}
			}
		} catch (e: unknown) {
			const msg = e instanceof Error ? e.message : 'Erro desconhecido.';
			showToast(msg, 'error');
		}
	}

	// ─── Auth & Realtime ──────────────────────────────
	let timer: ReturnType<typeof setInterval> | null = null;
	let realtimeChannel: ReturnType<typeof supabase.channel> | null = null;

	onMount(async () => {
		try {
			const { data: { session } } = await supabase.auth.getSession();
			if (!session) { goto('/login'); return; }

			userName = session.user.user_metadata?.name ?? session.user.email?.split('@')[0] ?? 'Astronauta';
			updateDateTime();
			timer = setInterval(updateDateTime, 1000);
			initWeather();

			const [fetchedItems, fetchedGoals, fetchedWishlist] = await Promise.all([
				api.items.list(),
				api.goals.list(),
				api.wishlist.list()
			]);

			items = fetchedItems;
			goals = fetchedGoals;
			wishlist = fetchedWishlist;
			milestones = fetchedGoals.length > 0 ? await api.milestones.list() : [];
			habits = await api.habits.list();
		} catch {
			showToast('Erro ao carregar dados. Verifique sua conexão.', 'error');
		} finally {
			loading = false;
		}

		// ─── Realtime subscriptions (com deduplicação) ────
		realtimeChannel = supabase
			.channel('station-one-realtime')
			.on('postgres_changes', { event: '*', schema: 'public', table: 'items' }, ({ eventType, new: rec, old }) => {
				if (eventType === 'INSERT') {
					if (!items.some((i) => i.id === (rec as Item).id))
						items = [rec as Item, ...items];
				} else if (eventType === 'UPDATE') {
					items = items.map((i) => (i.id === rec.id ? (rec as Item) : i));
				} else if (eventType === 'DELETE') {
					items = items.filter((i) => i.id !== old.id);
				}
			})
			.on('postgres_changes', { event: '*', schema: 'public', table: 'goals' }, ({ eventType, new: rec, old }) => {
				if (eventType === 'INSERT') {
					if (!goals.some((g) => g.id === (rec as Goal).id))
						goals = [...goals, rec as Goal];
				} else if (eventType === 'UPDATE') {
					goals = goals.map((g) => (g.id === rec.id ? (rec as Goal) : g));
				} else if (eventType === 'DELETE') {
					goals = goals.filter((g) => g.id !== old.id);
				}
			})
			.on('postgres_changes', { event: '*', schema: 'public', table: 'milestones' }, ({ eventType, new: rec, old }) => {
				if (eventType === 'INSERT') {
					if (!milestones.some((m) => m.id === (rec as Milestone).id))
						milestones = [...milestones, rec as Milestone];
				} else if (eventType === 'UPDATE') {
					milestones = milestones.map((m) => (m.id === rec.id ? (rec as Milestone) : m));
				} else if (eventType === 'DELETE') {
					milestones = milestones.filter((m) => m.id !== old.id);
				}
			})
			.on('postgres_changes', { event: '*', schema: 'public', table: 'wishlist' }, ({ eventType, new: rec, old }) => {
				if (eventType === 'INSERT') {
					if (!wishlist.some((w) => w.id === (rec as WishlistItem).id))
						wishlist = [rec as WishlistItem, ...wishlist];
				} else if (eventType === 'UPDATE') {
					wishlist = wishlist.map((w) => (w.id === rec.id ? (rec as WishlistItem) : w));
				} else if (eventType === 'DELETE') {
					wishlist = wishlist.filter((w) => w.id !== old.id);
				}
			})
			// Hábitos: a linha crua do banco não tem streak/completed_today (calculados
			// na API), então em vez de aplicar o evento direto, recarregamos a lista.
			.on('postgres_changes', { event: '*', schema: 'public', table: 'habits' }, scheduleHabitsRefresh)
			.on('postgres_changes', { event: '*', schema: 'public', table: 'habit_completions' }, scheduleHabitsRefresh)
			.subscribe();
	});

	onDestroy(() => {
		if (timer) clearInterval(timer);
		if (habitsRefreshTimer) clearTimeout(habitsRefreshTimer);
		if (realtimeChannel) supabase.removeChannel(realtimeChannel);
	});

	async function handleLogout() {
		try {
			await supabase.auth.signOut();
		} finally {
			goto('/login');
		}
	}

	function milestonesForGoal(goalId: string) {
		return milestones.filter((m) => m.goal_id === goalId);
	}
</script>

<!-- ─── Layout ─────────────────────────────────────────── -->
<div class="h-screen flex flex-col lg:flex-row font-sans overflow-hidden">

	<main class="flex-1 flex flex-col overflow-y-auto pb-20 lg:pb-0">

		<!-- Header -->
		<header class="flex items-end justify-between px-8 pt-6 pb-4">
			<div class="flex items-center gap-3">
				<div class="flex h-9 w-9 items-center justify-center rounded-full" style="background: rgba(6,182,212,0.12); border: 1px solid rgba(6,182,212,0.25)">
					<Satellite size={18} class="text-primary" />
				</div>
				<div>
					<div class="text-xs font-medium tracking-widest uppercase text-primary/60">Station One</div>
					<div class="flex items-center gap-2">
						<span class="text-xs text-base-content/30 capitalize">{currentDate}</span>
						{#if weather}
							<span
								class="weather-badge"
								title="Clima atual"
							>
								{weather.emoji} {weather.temp}°C
							</span>
						{/if}
					</div>
				</div>
			</div>
			<div class="clock-display text-5xl lg:text-6xl font-bold leading-none">{currentTime}</div>
		</header>

		<!-- Daily Log da Estação -->
		<DailyLog />

		<!-- Focus banner -->
		{#if focusItems.length > 0}
			<section class="px-8 pb-4">
				<div class="rounded-xl p-4" style="background: rgba(6,182,212,0.06); border: 1px solid rgba(6,182,212,0.2)">
					<div class="mb-3 flex items-center gap-2">
						<Star size={14} class="text-warning" fill="currentColor" />
						<span class="text-xs font-semibold uppercase tracking-widest text-warning/80">Foco de Hoje</span>
					</div>
					<div class="space-y-2">
						{#each focusItems as item (item.id)}
							<label class="flex cursor-pointer items-center gap-3">
								<input type="checkbox" class="checkbox checkbox-sm border-primary/40 checked:border-primary checked:bg-primary" checked={item.completed} onchange={() => handleToggleItem(item.id)} disabled={pendingIds.has(item.id)} />
								<span class="text-sm font-medium">{item.content}</span>
							</label>
						{/each}
					</div>
				</div>
			</section>
		{/if}

		<!-- ── Section: Operações ───────────────────────── -->
		{#if activeSection === 'operations'}
			<section class="flex-1 px-6 pb-6">
				<div class="mb-2 flex items-center justify-between px-1">
					<div class="flex items-center gap-2">
						<Zap size={14} class="text-primary" />
						<h2 class="text-xs font-semibold uppercase tracking-widest text-base-content/40">Operações</h2>
						<span class="rounded-full px-1.5 py-0.5 text-[10px] font-bold tabular-nums" style="background: rgba(6,182,212,0.12); color: #06b6d4">{items.length}</span>
					</div>
					{#if completedTasks.length > 0}
						<button onclick={handleClearCompleted} class="btn btn-ghost btn-xs gap-1 text-base-content/30 hover:text-error">
							<Trash2 size={11} />
							Limpar concluídas ({completedTasks.length})
						</button>
					{/if}
				</div>

				{#if loading}
					<div class="space-y-1">{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-8 w-full rounded-lg" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-0.5">
						{#each items as item, i (item.id)}
							<ItemCard {item} index={i} pending={pendingIds.has(item.id)} onToggle={handleToggleItem} onDelete={handleDeleteItem} onTogglePriority={handleTogglePriority} />
						{/each}
						{#if items.length === 0}
							<div class="flex flex-col items-center gap-3 py-16 text-base-content/25">
								<Zap size={28} />
								<p class="text-sm text-center">Nenhuma operação ainda.<br />Adicione uma pela barra lateral.</p>
							</div>
						{/if}
					</div>
				{/if}
			</section>

		<!-- ── Section: Missões ─────────────────────────── -->
		{:else if activeSection === 'missions'}
			<section class="flex-1 px-8 pb-8">
				<div class="mb-4 flex items-center gap-2">
					<Target size={16} class="text-secondary" />
					<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Missões</h2>
					<span class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums" style="background: rgba(139,92,246,0.15); color: #8b5cf6">{goals.length}</span>
				</div>

				{#if loading}
					<div class="space-y-3">{#each [1, 2] as i (i)}<div class="skeleton-pulse h-28 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-4">
						{#each goals as goal, i (goal.id)}
							<GoalCard {goal} index={i} milestones={milestonesForGoal(goal.id)} {pendingIds} onToggleMilestone={handleToggleMilestone} onDeleteGoal={handleDeleteGoal} onDeleteMilestone={handleDeleteMilestone} />
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

		<!-- ── Section: Protocolos ────────────────────── -->
		{:else if activeSection === 'protocols'}
			<section class="flex-1 px-8 pb-8">
				<div class="mb-4 flex items-center gap-2">
					<FlameKindling size={16} style="color: rgb(251,146,60)" />
					<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Protocolos</h2>
					<span class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums" style="background: rgba(251,146,60,0.12); color: rgb(251,146,60)">{habits.length}</span>
				</div>

				{#if loading}
					<div class="space-y-3">{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-20 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-3">
						{#each habits as habit (habit.id)}
							<HabitCard
								{habit}
								pending={pendingIds.has(habit.id)}
								onToggle={handleToggleHabit}
								onDelete={handleDeleteHabit}
							/>
						{/each}
						{#if habits.length === 0}
							<div class="flex flex-col items-center gap-3 py-16 text-base-content/25">
								<FlameKindling size={32} />
								<p class="text-sm text-center">Nenhum protocolo ainda.<br />Construa seus hábitos diários.</p>
							</div>
						{/if}
					</div>
				{/if}
			</section>

		<!-- ── Section: Wishlist ────────────────────────── -->
		{:else if activeSection === 'wishlist'}

			<section class="flex-1 px-8 pb-8">
				<div class="mb-4 flex items-center gap-2">
					<ShoppingBag size={16} class="text-accent" />
					<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Wishlist</h2>
					<span class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums" style="background: rgba(34,211,238,0.12); color: #22d3ee">{wishlist.length}</span>
				</div>

				{#if loading}
					<div class="space-y-3">{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-20 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-3">
						{#each wishlist as wishlistItem, i (wishlistItem.id)}
							<WishlistCard {wishlistItem} index={i} pending={pendingIds.has(wishlistItem.id)} onDelete={handleDeleteWishlist} />
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

		<!-- ── Section: Financeiro ────────────────────────── -->
		{:else if activeSection === 'finance'}
			<FinanceDashboard />
		{/if}

	</main>

	<AppSidebar
		{userName}
		{initials}
		bind:activeSection
		bind:selectedType
		{goals}
		onLogout={handleLogout}
		onSubmit={handleFormSubmit}
	/>
</div>

<MobileNav bind:activeSection bind:showMobileForm />

<MobileSheet
	bind:show={showMobileForm}
	{activeSection}
	bind:selectedType
	{goals}
	onSubmit={handleFormSubmit}
/>

<Toast />
