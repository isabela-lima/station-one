<script lang="ts">
	import type { WishlistItem } from '$lib';
	import { ShoppingBag, ExternalLink, Trash2, TrendingDown } from 'lucide-svelte';

	let {
		wishlistItem,
		onDelete,
		pending = false,
		index = 0
	}: {
		wishlistItem: WishlistItem;
		onDelete: (id: string) => void;
		pending?: boolean;
		index?: number;
	} = $props();

	const isGoodDeal = $derived(wishlistItem.current_price <= wishlistItem.target_price);
	const savings = $derived(wishlistItem.target_price - wishlistItem.current_price);

	function formatPrice(value: number) {
		return value.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
	}
</script>

<div
	class="glass-card card-enter group relative p-4"
	style="animation-delay: {index * 60}ms"
>
	<div class="flex gap-3 items-start">
		<!-- Image or icon -->
		{#if wishlistItem.image_url}
			<img
				src={wishlistItem.image_url}
				alt={wishlistItem.title}
				class="w-14 h-14 object-cover rounded-lg shrink-0 border"
				style="border-color: color-mix(in oklab, var(--color-primary) 15%, transparent)"
			/>
		{:else}
			<div
				class="w-14 h-14 rounded-lg shrink-0 flex items-center justify-center"
				style="background: color-mix(in oklab, var(--color-secondary) 12%, transparent); border: 1px solid color-mix(in oklab, var(--color-secondary) 20%, transparent)"
			>
				<ShoppingBag size={20} class="text-secondary/60" />
			</div>
		{/if}

		<!-- Info -->
		<div class="flex-1 min-w-0">
			<div class="flex items-start justify-between gap-2">
				<a
					href={wishlistItem.url}
					target="_blank"
					rel="noopener noreferrer"
					class="font-semibold text-sm hover:text-primary transition-colors truncate block leading-snug group/link flex items-center gap-1"
				>
					{wishlistItem.title}
					<ExternalLink size={10} class="opacity-0 group-hover/link:opacity-60 shrink-0 mt-0.5 transition-opacity" />
				</a>
				<button
					onclick={() => onDelete(wishlistItem.id)}
					class="btn btn-ghost btn-xs text-error/50 hover:text-error rounded-full opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
					title="Deletar"
					aria-label="Deletar da wishlist"
					disabled={pending}
				>
					{#if pending}
						<span class="loading loading-spinner loading-xs"></span>
					{:else}
						<Trash2 size={13} />
					{/if}
				</button>
			</div>

			{#if wishlistItem.description}
				<p class="text-xs text-base-content/40 line-clamp-1 mt-0.5">{wishlistItem.description}</p>
			{/if}

			<div class="flex items-center gap-2 mt-2 flex-wrap">
				<span
					class="text-sm font-semibold"
					class:text-success={isGoodDeal}
					class:text-error={!isGoodDeal}
				>
					{formatPrice(wishlistItem.current_price)}
				</span>
				<span class="text-xs text-base-content/40">meta: {formatPrice(wishlistItem.target_price)}</span>
				{#if isGoodDeal && savings > 0}
					<span
						class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-semibold"
						style="background: color-mix(in oklab, var(--color-success) 12%, transparent); color: var(--color-success); border: 1px solid color-mix(in oklab, var(--color-success) 30%, transparent)"
					>
						<TrendingDown size={9} />
						economiza {formatPrice(savings)}
					</span>
				{/if}
			</div>
		</div>
	</div>
</div>
