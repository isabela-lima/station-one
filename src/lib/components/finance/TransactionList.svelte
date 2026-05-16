<script lang="ts">
	import type { Transaction } from '$lib/models/types';
	import { ArrowUpRight, ArrowDownRight, RefreshCcw } from 'lucide-svelte';

	let { transactions }: { transactions: Transaction[] } = $props();

	function formatCurrency(amount: number, currency: string) {
		return new Intl.NumberFormat('pt-BR', { style: 'currency', currency }).format(amount);
	}

	function formatDate(dateString: string) {
		const date = new Date(dateString);
		return date.toLocaleDateString('pt-BR', { day: '2-digit', month: 'short' });
	}
</script>

<div class="space-y-2">
	{#each transactions as tx (tx.id)}
		<div class="flex items-center justify-between p-3 rounded-lg" style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05)">
			<div class="flex items-center gap-3">
				<div class="flex h-8 w-8 items-center justify-center rounded-full" style="background: {tx.amount < 0 ? 'rgba(239,68,68,0.1)' : 'rgba(34,197,94,0.1)'}; color: {tx.amount < 0 ? '#ef4444' : '#22c55e'}">
					{#if tx.amount < 0}
						<ArrowDownRight size={14} />
					{:else}
						<ArrowUpRight size={14} />
					{/if}
				</div>
				<div>
					<div class="text-sm font-medium leading-none">{tx.description || tx.category}</div>
					<div class="text-[10px] text-base-content/40 uppercase tracking-wider mt-1 flex items-center gap-1">
						{tx.category} 
						{#if tx.is_recurring}
							<RefreshCcw size={8} class="inline opacity-50" />
						{/if}
					</div>
				</div>
			</div>
			<div class="text-right">
				<div class="text-sm font-semibold" style="color: {tx.amount < 0 ? '#ef4444' : '#22c55e'}">
					{formatCurrency(tx.amount, tx.currency)}
				</div>
				<div class="text-[10px] text-base-content/40">{formatDate(tx.date)}</div>
			</div>
		</div>
	{/each}
	
	{#if transactions.length === 0}
		<div class="text-center py-8 text-sm text-base-content/30 italic">
			Nenhuma transação recente.
		</div>
	{/if}
</div>
