<script lang="ts">
	import type { Wallet } from '$lib/models/types';

	let { wallet }: { wallet: Wallet } = $props();

	function formatCurrency(amount: number, currency: string) {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(amount);
	}
</script>

<div
	class="group relative flex flex-col gap-2 overflow-hidden rounded-xl p-4 transition-all duration-300 hover:-translate-y-1"
	style="background: color-mix(in oklab, var(--color-base-200) 60%, transparent); border: 1px solid color-mix(in oklab, var(--color-primary) 15%, transparent); box-shadow: 0 4px 20px rgba(0,0,0,0.2)"
>
	<!-- Decorative background glow -->
	<div
		class="absolute -top-8 -right-8 h-24 w-24 rounded-full opacity-20 blur-2xl transition-opacity group-hover:opacity-40"
		style="background: {wallet.type === 'cash'
			? 'var(--color-success)'
			: wallet.type === 'vr'
				? 'var(--color-warning)'
				: 'var(--color-info)'};"
	></div>

	<div class="relative z-10 flex items-start justify-between">
		<div class="flex items-center gap-2">
			<span class="text-2xl drop-shadow-md">{wallet.emoji}</span>
			<div>
				<h3 class="text-xs font-semibold tracking-wider text-base-content/70 uppercase">
					{wallet.name}
				</h3>
				<p class="text-[10px] tracking-widest text-base-content/40 uppercase">{wallet.type}</p>
			</div>
		</div>
	</div>

	<div class="relative z-10 mt-2">
		<div
			class="text-2xl font-bold tracking-tight"
			style="color: {wallet.balance < 0 ? 'var(--color-error)' : 'var(--color-base-content)'}"
		>
			{formatCurrency(wallet.balance, wallet.currency)}
		</div>
	</div>
</div>
