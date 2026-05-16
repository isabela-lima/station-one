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
			console.error("Erro ao carregar dados financeiros:", e);
		} finally {
			loading = false;
		}
	});

	function formatCurrency(amount: number, currency: string) {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(amount);
	}
</script>

<section class="flex-1 px-8 pb-8 animate-fade-in">
	<div class="mb-6 flex items-center gap-2">
		<LineChart size={16} class="text-info" />
		<h2 class="text-sm font-semibold uppercase tracking-widest text-base-content/60">Finanças</h2>
		<span class="rounded-full px-2 py-0.5 text-[10px] font-bold tabular-nums" style="background: rgba(56,189,248,0.12); color: #38bdf8">HUD</span>
	</div>

	{#if loading}
		<div class="space-y-6">
			<div class="skeleton-pulse h-32 w-full rounded-xl"></div>
			<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
				{#each [1, 2, 3] as i}
					<div class="skeleton-pulse h-24 w-full rounded-xl" style="animation-delay: {i * 100}ms"></div>
				{/each}
			</div>
		</div>
	{:else if overview}
		<div class="space-y-6">
			<!-- Resumo / Autonomy -->
			<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
				<!-- Runaway HUD -->
				<div class="col-span-1 md:col-span-2 rounded-xl p-5 flex flex-col justify-center relative overflow-hidden" style="background: linear-gradient(135deg, rgba(6,182,212,0.1), rgba(59,130,246,0.05)); border: 1px solid rgba(6,182,212,0.2);">
					<div class="absolute right-0 top-0 opacity-10">
						<Activity size={120} />
					</div>
					<div class="relative z-10 text-xs font-semibold uppercase tracking-widest text-primary mb-1">
						Autonomia (Runway)
					</div>
					<div class="relative z-10 flex items-end gap-2">
						<span class="text-5xl font-bold tracking-tighter" style="color: #e0f2fe;">{overview.autonomy.days_of_runway}</span>
						<span class="text-sm text-base-content/50 uppercase tracking-widest mb-1">dias</span>
					</div>
					<div class="relative z-10 mt-3 flex items-center gap-4 text-xs">
						<div><span class="text-base-content/40">Gasto Médio:</span> <span class="font-bold text-base-content/80">{formatCurrency(overview.autonomy.avg_daily_expense, overview.autonomy.currency)}/dia</span></div>
						<div><span class="text-base-content/40">Livre:</span> <span class="font-bold text-success/80">{formatCurrency(overview.autonomy.free_balance, overview.autonomy.currency)}</span></div>
					</div>
				</div>

				<!-- Debt alert -->
				<div class="col-span-1 rounded-xl p-5 flex flex-col justify-center" style="background: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.2);">
					<div class="text-xs font-semibold uppercase tracking-widest text-error mb-1 flex items-center gap-1">
						<ShieldAlert size={14} /> Dívidas Ativas
					</div>
					<div class="text-2xl font-bold text-error tracking-tight mt-1">
						{formatCurrency(overview.total_debt, 'BRL')}
					</div>
					<div class="mt-2 text-[10px] text-base-content/40">
						{#if overview.alerts.length > 0}
							<div class="text-warning font-medium">{overview.alerts[0]}</div>
						{:else}
							Sem alertas críticos.
						{/if}
					</div>
				</div>
			</div>

			<!-- Wallets -->
			<div>
				<div class="flex items-center gap-2 mb-3">
					<WalletIcon size={14} class="text-base-content/40" />
					<h3 class="text-xs font-semibold uppercase tracking-widest text-base-content/50">Carteiras</h3>
				</div>
				<div class="grid grid-cols-1 md:grid-cols-3 gap-4">
					{#each overview.wallets as wallet (wallet.id)}
						<WalletCard {wallet} />
					{/each}
				</div>
			</div>

			<!-- Transactions -->
			<div>
				<div class="flex items-center justify-between mb-3">
					<h3 class="text-xs font-semibold uppercase tracking-widest text-base-content/50">Últimas Transações</h3>
				</div>
				<div class="rounded-xl p-2" style="background: rgba(0,0,0,0.1); border: 1px solid rgba(255,255,255,0.05);">
					<TransactionList {transactions} />
				</div>
			</div>
		</div>
	{:else}
		<div class="flex flex-col items-center justify-center p-12 text-center text-error border border-error/20 rounded-xl bg-error/5">
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
		from { opacity: 0; transform: translateY(10px); }
		to { opacity: 1; transform: translateY(0); }
	}
</style>
