<script lang="ts">
	import { onMount } from 'svelte';
	import { LineChart, Wallet as WalletIcon, ShieldAlert, Activity } from 'lucide-svelte';
	import * as api from '$lib/api';
	import type { FinanceOverview, Transaction } from '$lib/models/types';
	import WalletCard from './WalletCard.svelte';
	import TransactionList from './TransactionList.svelte';

	let overview = $state<FinanceOverview | null>(null);
	let transactions = $state<Transaction[]>([]);
	let loading = $state(true);

	onMount(async () => {
		try {
			const [overviewData, txData] = await Promise.all([
				api.finance.overview(),
				api.finance.transactions.list()
			]);
			overview = overviewData;
			// Pega as 5 ultimas transacoes
			transactions = txData.slice(0, 5);
		} catch (e) {
			console.error('Erro ao carregar dados financeiros:', e);
		} finally {
			loading = false;
		}
	});

	function formatCurrency(amount: number, currency: string) {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(amount);
	}
</script>

<section class="animate-fade-in flex-1 px-8 pb-8">
	<div class="mb-6 flex items-center gap-2">
		<LineChart size={16} class="text-info" />
		<h2 class="text-sm font-semibold tracking-widest text-base-content/60 uppercase">Finanças</h2>
		<span
			class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums"
			style="background: color-mix(in oklab, var(--color-info) 12%, transparent); color: var(--color-info)"
			>HUD</span
		>
	</div>

	{#if loading}
		<div class="space-y-6">
			<div class="skeleton-pulse h-32 w-full rounded-xl"></div>
			<div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
				{#each [1, 2, 3] as i}
					<div
						class="skeleton-pulse h-24 w-full rounded-xl"
						style="animation-delay: {i * 100}ms"
					></div>
				{/each}
			</div>
		</div>
	{:else if overview}
		<div class="space-y-6">
			<!-- Resumo / Autonomy -->
			<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
				<!-- Runaway HUD -->
				<div
					class="relative col-span-1 flex flex-col justify-center overflow-hidden rounded-xl p-5 md:col-span-2"
					style="background: linear-gradient(135deg, color-mix(in oklab, var(--color-primary) 10%, transparent), color-mix(in oklab, var(--color-info) 5%, transparent)); border: 1px solid color-mix(in oklab, var(--color-primary) 20%, transparent);"
				>
					<div class="absolute top-0 right-0 opacity-10">
						<Activity size={120} />
					</div>
					<div
						class="relative z-10 mb-1 text-xs font-semibold tracking-widest text-primary uppercase"
					>
						Autonomia (Runway)
					</div>
					<div class="relative z-10 flex items-end gap-2">
						<span
							class="text-5xl font-bold tracking-tighter"
							style="color: var(--color-base-content);">{overview.autonomy.days_of_runway}</span
						>
						<span class="mb-1 text-sm tracking-widest text-base-content/50 uppercase">dias</span>
					</div>
					<div class="relative z-10 mt-3 flex items-center gap-4 text-xs">
						<div>
							<span class="text-base-content/40">Gasto Médio:</span>
							<span class="font-bold text-base-content/80"
								>{formatCurrency(
									overview.autonomy.avg_daily_expense,
									overview.autonomy.currency
								)}/dia</span
							>
						</div>
						<div>
							<span class="text-base-content/40">Livre:</span>
							<span class="font-bold text-success/80"
								>{formatCurrency(overview.autonomy.free_balance, overview.autonomy.currency)}</span
							>
						</div>
					</div>
				</div>

				<!-- Debt alert -->
				<div
					class="col-span-1 flex flex-col justify-center rounded-xl p-5"
					style="background: color-mix(in oklab, var(--color-error) 5%, transparent); border: 1px solid color-mix(in oklab, var(--color-error) 20%, transparent);"
				>
					<div
						class="mb-1 flex items-center gap-1 text-xs font-semibold tracking-widest text-error uppercase"
					>
						<ShieldAlert size={14} /> Dívidas Ativas
					</div>
					<div class="mt-1 text-2xl font-bold tracking-tight text-error">
						{formatCurrency(overview.total_debt, 'BRL')}
					</div>
					<div class="mt-2 text-[10px] text-base-content/40">
						{#if overview.alerts.length > 0}
							<div class="font-medium text-warning">{overview.alerts[0]}</div>
						{:else}
							Sem alertas críticos.
						{/if}
					</div>
				</div>
			</div>

			<!-- Wallets -->
			<div>
				<div class="mb-3 flex items-center gap-2">
					<WalletIcon size={14} class="text-base-content/40" />
					<h3 class="text-xs font-semibold tracking-widest text-base-content/50 uppercase">
						Carteiras
					</h3>
				</div>
				<div class="grid grid-cols-1 gap-4 md:grid-cols-3">
					{#each overview.wallets as wallet (wallet.id)}
						<WalletCard {wallet} />
					{/each}
				</div>
			</div>

			<!-- Transactions -->
			<div>
				<div class="mb-3 flex items-center justify-between">
					<h3 class="text-xs font-semibold tracking-widest text-base-content/50 uppercase">
						Últimas Transações
					</h3>
				</div>
				<div
					class="rounded-xl p-2"
					style="background: rgba(0,0,0,0.1); border: 1px solid color-mix(in oklab, var(--color-base-content) 5%, transparent);"
				>
					<TransactionList {transactions} />
				</div>
			</div>
		</div>
	{:else}
		<div
			class="flex flex-col items-center justify-center rounded-xl border border-error/20 bg-error/5 p-12 text-center text-error"
		>
			<ShieldAlert size={32} class="mb-3" />
			<p>Não foi possível acessar o núcleo financeiro.</p>
		</div>
	{/if}
</section>

<style>
	.animate-fade-in {
		animation: fadeIn 0.4s ease-out forwards;
	}
	@keyframes fadeIn {
		from {
			opacity: 0;
			transform: translateY(10px);
		}
		to {
			opacity: 1;
			transform: translateY(0);
		}
	}
</style>
