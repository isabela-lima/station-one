<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';

	// ── Lib ─────────────────────────────────────────────
	import { supabase } from '$lib/supabase';
	import * as api from '$lib/api';
	import { showToast } from '$lib/toast';
	import type { Goal, Habit, Item, Milestone, WishlistItem, Section, CreatableSection, FormType, FormPayload } from '$lib';

	// ── Components ───────────────────────────────────────
	import GoalCard from '$lib/components/GoalCard.svelte';
	import HabitCard from '$lib/components/HabitCard.svelte';
	import ItemCard from '$lib/components/ItemCard.svelte';
	import WishlistCard from '$lib/components/WishlistCard.svelte';
	import Toast from '$lib/components/Toast.svelte';
	import AppHeader from '$lib/components/dashboard/AppHeader.svelte';
	import CreateDialog from '$lib/components/dashboard/CreateDialog.svelte';
	import { SECTIONS, sectionColor } from '$lib/components/dashboard/types';
	import TodayView from '$lib/components/today/TodayView.svelte';
	import FinanceDashboard from '$lib/components/finance/FinanceDashboard.svelte';

	import { FlameKindling, Zap, Target, ShoppingBag, Trash2, Flame } from 'lucide-svelte';

	// ─── State ────────────────────────────────────────
	let items = $state<Item[]>([]);
	let goals = $state<Goal[]>([]);
	let milestones = $state<Milestone[]>([]);
	let wishlist = $state<WishlistItem[]>([]);
	let habits = $state<Habit[]>([]);

	let currentDate = $state('');
	let currentTime = $state('');
	let greeting = $state('Olá');
	let loading = $state(true);
	let userName = $state('');
	let profileName = $state<string | null>(null);

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

	let activeSection = $state<Section>('today');
	let selectedType = $state<FormType>('task');
	let createOpen = $state(false);
	let createKind = $state<CreatableSection>('operations');

	const DEFAULT_TYPE: Record<CreatableSection, FormType> = {
		operations: 'task',
		missions: 'goal',
		protocols: 'habit',
		finance: 'transaction',
		wishlist: 'wishlist'
	};

	/** Abre o formulário já no tipo da seção atual (Hoje → Operação) */
	function openCreate() {
		createKind = activeSection === 'today' ? 'operations' : activeSection;
		selectedType = DEFAULT_TYPE[createKind];
		createOpen = true;
	}

	/** IDs de itens com ação em andamento (delete, toggle) */
	let pendingIds = $state<Set<string>>(new Set());

	// ─── Derived ──────────────────────────────────────
	const completedTasks = $derived(items.filter((i) => i.type === 'task' && i.completed));
	/** Nome para a saudação: só o primeiro nome do perfil; sem nome no perfil, "Comandante" */
	const firstName = $derived(profileName?.trim().split(/\s+/)[0] || 'Comandante');
	const topStreak = $derived(habits.reduce((max, h) => Math.max(max, h.streak), 0));
	const currentSection = $derived(SECTIONS.find((s) => s.id === activeSection)!);
	const initials = $derived(
		userName.split(' ').slice(0, 2).map((w: string) => w[0]).join('').toUpperCase()
	);

	// ─── Date / Time ──────────────────────────────────
	function updateDateTime() {
		const now = new Date();
		const d = now.toLocaleDateString('pt-BR', { weekday: 'long', month: 'long', day: 'numeric' });
		currentDate = d.charAt(0).toUpperCase() + d.slice(1);
		currentTime = now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
		const h = now.getHours();
		greeting = h < 5 ? 'Boa noite' : h < 12 ? 'Bom dia' : h < 18 ? 'Boa tarde' : 'Boa noite';
	}

	// ─── Helpers ──────────────────────────────────────
	function setPending(id: string, on: boolean) {
		pendingIds = new Set(on ? [...pendingIds, id] : [...pendingIds].filter((x) => x !== id));
	}

	// ─── Handlers: Items ──────────────────────────────
	// As ações abaixo são otimistas: a tela muda na hora e a API confirma em
	// segundo plano. Se a API falhar, desfazemos e avisamos.
	async function handleToggleItem(id: string) {
		if (pendingIds.has(id)) return;
		const item = items.find((i) => i.id === id);
		if (!item) return;
		const completed = !item.completed;
		items = items.map((i) => (i.id === id ? { ...i, completed } : i));
		setPending(id, true);
		try {
			const updated = await api.items.update(id, { completed });
			items = items.map((i) => (i.id === id ? updated : i));
		} catch {
			items = items.map((i) => (i.id === id ? { ...i, completed: item.completed } : i));
			showToast('Erro ao atualizar item.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	async function handleDeleteItem(id: string) {
		if (pendingIds.has(id)) return;
		const index = items.findIndex((i) => i.id === id);
		if (index === -1) return;
		const removed = items[index];
		items = items.filter((i) => i.id !== id);
		setPending(id, true);
		try {
			await api.items.delete(id);
			showToast('Operação removida.');
		} catch {
			// Devolve só o item removido (sem desfazer outras mudanças feitas no meio tempo)
			const next = [...items];
			next.splice(Math.min(index, next.length), 0, removed);
			items = next;
			showToast('Erro ao remover operação.', 'error');
		} finally {
			setPending(id, false);
		}
	}

	async function handleTogglePriority(id: string) {
		if (pendingIds.has(id)) return;
		const item = items.find((i) => i.id === id);
		if (!item) return;
		const priority = !item.priority;
		items = items.map((i) => (i.id === id ? { ...i, priority } : i));
		setPending(id, true);
		try {
			const updated = await api.items.update(id, { priority });
			items = items.map((i) => (i.id === id ? updated : i));
		} catch {
			items = items.map((i) => (i.id === id ? { ...i, priority: item.priority } : i));
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
		const ms = milestones.find((m) => m.id === milestoneId);
		if (!ms) return;
		const completed = !ms.completed;
		milestones = milestones.map((m) => (m.id === milestoneId ? { ...m, completed } : m));
		setPending(milestoneId, true);
		try {
			const updated = await api.milestones.update(milestoneId, { completed });
			milestones = milestones.map((m) => (m.id === milestoneId ? updated : m));
		} catch {
			milestones = milestones.map((m) => (m.id === milestoneId ? { ...m, completed: ms.completed } : m));
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
		const before = habits.find((h) => h.id === id);
		if (!before) return;
		const done = !before.completed_today;
		habits = habits.map((h) =>
			h.id === id ? { ...h, completed_today: done, streak: Math.max(0, h.streak + (done ? 1 : -1)) } : h
		);
		setPending(id, true);
		try {
			const updated = await api.habits.toggleToday(id);
			habits = habits.map((h) => (h.id === id ? updated : h));
		} catch {
			habits = habits.map((h) => (h.id === id ? before : h));
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

			profileName = session.user.user_metadata?.name ?? null;
			userName = profileName ?? session.user.email?.split('@')[0] ?? 'Astronauta';
			updateDateTime();
			timer = setInterval(updateDateTime, 1000);
			initWeather();

			// Tudo em paralelo: cada requisição custa uma ida até o banco
			const [fetchedItems, fetchedGoals, fetchedWishlist, fetchedMilestones, fetchedHabits] = await Promise.all([
				api.items.list(),
				api.goals.list(),
				api.wishlist.list(),
				api.milestones.list(),
				api.habits.list()
			]);

			items = fetchedItems;
			goals = fetchedGoals;
			wishlist = fetchedWishlist;
			milestones = fetchedMilestones;
			habits = fetchedHabits;
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
<div class="mx-auto flex min-h-screen w-full max-w-[1320px] flex-col gap-6 px-4 pt-5 pb-12 sm:px-7 sm:pt-7">
	<AppHeader bind:activeSection {userName} {initials} onCreate={openCreate} onLogout={handleLogout} />

	{#if activeSection === 'today'}
		<!-- Hero -->
		<section class="flex flex-wrap items-end justify-between gap-4 px-1">
			<div class="flex flex-col gap-2">
				<p class="text-sm font-semibold text-base-content/70">
					{currentDate}{#if weather} · {weather.emoji} {weather.temp}°C{/if}
				</p>
				<h1 class="font-display hero-title">{greeting}, {firstName}.</h1>
			</div>
			<div class="flex flex-wrap gap-3">
				<div class="hero-stat">
					<span class="hero-stat-value font-mono-num">{currentTime}</span>
					<span class="hero-stat-label">agora</span>
				</div>
				{#if topStreak > 0}
					<div class="hero-stat sec-protocols streak-stat">
						<span class="hero-stat-value flex items-center gap-2">
							<Flame size={24} fill="currentColor" />{topStreak} {topStreak === 1 ? 'dia' : 'dias'}
						</span>
						<span class="hero-stat-label">maior streak ativo</span>
					</div>
				{/if}
			</div>
		</section>

		<TodayView
			{items}
			{habits}
			{goals}
			{milestones}
			{loading}
			{pendingIds}
			onToggleItem={handleToggleItem}
			onToggleHabit={handleToggleHabit}
			onOpenSection={(sec) => (activeSection = sec)}
		/>
	{:else}
		<!-- Página de seção -->
		<section class="tile sec-{sectionColor(activeSection)} flex flex-col gap-5">
			<div class="flex flex-wrap items-center justify-between gap-3">
				<h1 class="font-display flex items-center gap-3 text-2xl sm:text-3xl">
					<currentSection.Icon size={26} style="color: var(--sec)" />
					{currentSection.label}
				</h1>
				{#if activeSection === 'operations' && completedTasks.length > 0}
					<button onclick={handleClearCompleted} class="btn btn-ghost btn-sm gap-1.5 text-base-content/70 hover:text-error">
						<Trash2 size={14} />
						Limpar concluídas ({completedTasks.length})
					</button>
				{/if}
			</div>

			{#if activeSection === 'operations'}
				{#if loading}
					<div class="space-y-2">{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-10 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-0.5">
						{#each items as item, i (item.id)}
							<ItemCard {item} index={i} pending={pendingIds.has(item.id)} onToggle={handleToggleItem} onDelete={handleDeleteItem} onTogglePriority={handleTogglePriority} />
						{/each}
						{#if items.length === 0}
							<div class="empty-state">
								<Zap size={28} />
								<p>Nenhuma operação ainda.<br />Use o botão <strong>Novo</strong> para criar.</p>
							</div>
						{/if}
					</div>
				{/if}

			{:else if activeSection === 'missions'}
				{#if loading}
					<div class="space-y-3">{#each [1, 2] as i (i)}<div class="skeleton-pulse h-28 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-4">
						{#each goals as goal, i (goal.id)}
							<GoalCard {goal} index={i} milestones={milestonesForGoal(goal.id)} {pendingIds} onToggleMilestone={handleToggleMilestone} onDeleteGoal={handleDeleteGoal} onDeleteMilestone={handleDeleteMilestone} />
						{/each}
						{#if goals.length === 0}
							<div class="empty-state">
								<Target size={28} />
								<p>Nenhuma missão ainda.<br />Defina seus objetivos de longo prazo.</p>
							</div>
						{/if}
					</div>
				{/if}

			{:else if activeSection === 'protocols'}
				{#if loading}
					<div class="space-y-3">{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-20 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-3">
						{#each habits as habit (habit.id)}
							<HabitCard {habit} pending={pendingIds.has(habit.id)} onToggle={handleToggleHabit} onDelete={handleDeleteHabit} />
						{/each}
						{#if habits.length === 0}
							<div class="empty-state">
								<FlameKindling size={28} />
								<p>Nenhum protocolo ainda.<br />Construa seus hábitos diários.</p>
							</div>
						{/if}
					</div>
				{/if}

			{:else if activeSection === 'wishlist'}
				{#if loading}
					<div class="space-y-3">{#each [1, 2, 3] as i (i)}<div class="skeleton-pulse h-20 w-full" style="animation-delay: {i * 100}ms"></div>{/each}</div>
				{:else}
					<div class="space-y-3">
						{#each wishlist as wishlistItem, i (wishlistItem.id)}
							<WishlistCard {wishlistItem} index={i} pending={pendingIds.has(wishlistItem.id)} onDelete={handleDeleteWishlist} />
						{/each}
						{#if wishlist.length === 0}
							<div class="empty-state">
								<ShoppingBag size={28} />
								<p>Wishlist vazia.<br />Cole uma URL para adicionar itens.</p>
							</div>
						{/if}
					</div>
				{/if}

			{:else if activeSection === 'finance'}
				<FinanceDashboard />
			{/if}
		</section>
	{/if}
</div>

<CreateDialog bind:open={createOpen} bind:kind={createKind} bind:selectedType {goals} onSubmit={handleFormSubmit} />

<Toast />

<style>
	.hero-title {
		margin: 0;
		font-size: var(--hero-size);
		line-height: 1.05;
	}
	.hero-stat {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 14px 18px;
		border-radius: var(--tile-radius);
		background: var(--color-base-200);
		border: var(--tile-border);
		box-shadow: var(--tile-shadow);
	}
	.hero-stat-value {
		font-family: var(--font-display);
		font-weight: var(--display-weight);
		font-size: 30px;
		line-height: 1;
	}
	.hero-stat-label {
		font-size: 13px;
		color: color-mix(in oklab, var(--color-base-content) 65%, transparent);
	}
	.streak-stat {
		background: var(--sec-soft);
		color: var(--sec-ink);
	}
	.streak-stat .hero-stat-label {
		color: inherit;
		opacity: 0.85;
	}
	.empty-state {
		display: flex;
		flex-direction: column;
		align-items: center;
		gap: 12px;
		padding: 48px 0;
		text-align: center;
		font-size: 14px;
		color: color-mix(in oklab, var(--color-base-content) 60%, transparent);
	}
</style>
