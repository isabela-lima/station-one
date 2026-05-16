<script lang="ts">
	import { Plus, Zap, Target, ShoppingBag, LineChart, FlameKindling } from 'lucide-svelte';
	import type { Section } from './types';

	let {
		activeSection = $bindable<Section>(),
		showMobileForm = $bindable<boolean>()
	}: {
		activeSection: Section;
		showMobileForm: boolean;
	} = $props();

	const NAV_ITEMS = [
		{ id: 'operations' as Section, label: 'Operações', Icon: Zap },
		{ id: 'missions' as Section, label: 'Missões', Icon: Target },
		{ id: 'protocols' as Section, label: 'Protocolos', Icon: FlameKindling },
		{ id: 'finance' as Section, label: 'Finanças', Icon: LineChart },
		{ id: 'wishlist' as Section, label: 'Wishlist', Icon: ShoppingBag }
	];
</script>

<nav
	class="lg:hidden fixed bottom-0 left-0 right-0 z-40 flex items-center pb-safe"
	style="background: rgba(10,10,20,0.95); backdrop-filter: blur(20px); border-top: 1px solid rgba(6,182,212,0.12); height: 64px;"
>
	<!-- Scrollable tabs -->
	<div class="mobile-nav-scroll flex flex-1 items-center overflow-x-auto gap-1 px-2 no-scrollbar">
		{#each NAV_ITEMS as nav (nav.id)}
			<button
				onclick={() => { activeSection = nav.id; showMobileForm = false; }}
				class="flex shrink-0 flex-col items-center gap-1 px-3 py-2 rounded-xl text-[10px] font-semibold uppercase tracking-wide transition-all duration-200"
				style={activeSection === nav.id ? 'color: #06b6d4; background: rgba(6,182,212,0.08);' : 'color: rgba(226,232,240,0.35);'}
			>
				<nav.Icon size={18} />
				{nav.label}
			</button>
		{/each}
	</div>

	<!-- FAB -->
	<div class="px-2 shrink-0">
		<button
			onclick={() => (showMobileForm = true)}
			class="flex items-center justify-center w-12 h-12 rounded-full transition-transform duration-200 active:scale-95"
			style="background: linear-gradient(135deg, rgba(6,182,212,0.9), rgba(139,92,246,0.9)); box-shadow: 0 0 20px rgba(6,182,212,0.3);"
			aria-label="Adicionar"
		>
			<Plus size={20} class="text-white" />
		</button>
	</div>
</nav>

<style>
	.no-scrollbar::-webkit-scrollbar { display: none; }
	.no-scrollbar { -ms-overflow-style: none; scrollbar-width: none; }
</style>
