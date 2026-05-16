<script lang="ts">
	import { LogOut, Plus, Zap, Target, ShoppingBag, LineChart, FlameKindling } from 'lucide-svelte';
	import AddForm from './AddForm.svelte';
	import type { Goal } from '$lib';
	import type { Section, FormType, FormPayload } from '$lib/components/dashboard';

	let {
		userName,
		initials,
		activeSection = $bindable<Section>(),
		selectedType = $bindable<FormType>(),
		goals,
		onLogout,
		onSubmit
	}: {
		userName: string;
		initials: string;
		activeSection: Section;
		selectedType: FormType;
		goals: Goal[];
		onLogout: () => void;
		onSubmit: (payload: FormPayload) => Promise<void>;
	} = $props();

	const NAV_ITEMS = [
		{ id: 'operations' as Section, label: 'Operações', Icon: Zap },
		{ id: 'missions' as Section, label: 'Missões', Icon: Target },
		{ id: 'protocols' as Section, label: 'Protocolos', Icon: FlameKindling },
		{ id: 'finance' as Section, label: 'Finanças', Icon: LineChart },
		{ id: 'wishlist' as Section, label: 'Wishlist', Icon: ShoppingBag }
	];

	const formTitle = $derived(
		activeSection === 'operations' ? 'Nova Operação'
		: activeSection === 'missions' ? 'Nova Missão'
		: activeSection === 'protocols' ? 'Novo Protocolo'
		: activeSection === 'finance' ? 'Nova Transação'
		: 'Adicionar à Wishlist'
	);
</script>

<aside class="glass-sidebar hidden lg:flex lg:w-[340px] flex-col">

	<!-- User header -->
	<div class="flex items-center justify-between p-6" style="border-bottom: 1px solid rgba(6,182,212,0.08)">
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
			onclick={onLogout}
			class="btn btn-ghost btn-sm gap-1.5 text-base-content/40 hover:text-error"
			aria-label="Logout"
		>
			<LogOut size={15} />
			<span class="text-xs">Sair</span>
		</button>
	</div>

	<!-- Section nav -->
	<nav class="flex gap-1 p-3" style="border-bottom: 1px solid rgba(6,182,212,0.08)">
		{#each NAV_ITEMS as nav (nav.id)}
			<button
				onclick={() => (activeSection = nav.id)}
				class="flex flex-1 flex-col items-center gap-1 rounded-lg py-2.5 text-[10px] font-semibold uppercase tracking-wide transition-all duration-200"
				class:text-primary={activeSection === nav.id}
				class:text-base-content={activeSection !== nav.id}
				style={activeSection === nav.id
					? 'background: rgba(6,182,212,0.1); border: 1px solid rgba(6,182,212,0.2); opacity: 1'
					: 'background: transparent; border: 1px solid transparent; opacity: 0.4'}
			>
				<nav.Icon size={16} />
				{nav.label}
			</button>
		{/each}
	</nav>

	<!-- Form -->
	<div class="flex-1 overflow-y-auto p-6">
		<div class="mb-4 flex items-center gap-2">
			<Plus size={14} class="text-primary/60" />
			<h2 class="text-xs font-semibold uppercase tracking-widest text-base-content/50">{formTitle}</h2>
		</div>
		<AddForm {activeSection} {goals} bind:selectedType {onSubmit} />
	</div>

	<!-- Footer status -->
	<div class="px-6 py-3 flex items-center gap-2" style="border-top: 1px solid rgba(6,182,212,0.08)">
		<div class="h-1.5 w-1.5 rounded-full animate-pulse" style="background: #06b6d4; box-shadow: 0 0 6px #06b6d4"></div>
		<span class="text-[10px] uppercase tracking-widest text-base-content/25">Sistema online</span>
	</div>

</aside>
