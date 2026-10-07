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

<div class="glass-card card-enter group relative p-4" style="animation-delay: {index * 60}ms">
	<div class="flex items-start gap-3">
		<!-- Image or icon -->
		{#if wishlistItem.image_url}
			<img
				src={wishlistItem.image_url}
				alt={wishlistItem.title}
				class="h-14 w-14 shrink-0 rounded-lg border object-cover"
				style="border-color: color-mix(in oklab, var(--color-primary) 15%, transparent)"
			/>
		{:else}
			<div
				class="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg"
				style="background: color-mix(in oklab, var(--color-secondary) 12%, transparent); border: 1px solid color-mix(in oklab, var(--color-secondary) 20%, transparent)"
			>
				<ShoppingBag size={20} class="text-secondary/60" />
			</div>
		{/if}

		<!-- Info -->
		<div class="min-w-0 flex-1">
			<div class="flex items-start justify-between gap-2">
				<a
					href={wishlistItem.url}
					target="_blank"
					rel="noopener noreferrer"
					class="group/link block flex items-center gap-1 truncate text-sm leading-snug font-semibold transition-colors hover:text-primary"
				>
					{wishlistItem.title}
					<ExternalLink
						size={10}
						class="mt-0.5 shrink-0 opacity-0 transition-opacity group-hover/link:opacity-60"
					/>
				</a>
				<button
					onclick={() => onDelete(wishlistItem.id)}
					class="btn shrink-0 rounded-full text-error/50 opacity-0 btn-ghost transition-opacity btn-xs group-hover:opacity-100 hover:text-error"
					title="Deletar"
					aria-label="Deletar da wishlist"
					disabled={pending}
				>
					{#if pending}
						<span class="loading loading-xs loading-spinner"></span>
					{:else}
						<Trash2 size={13} />
					{/if}
				</button>
			</div>

			{#if wishlistItem.description}
				<p class="mt-0.5 line-clamp-1 text-xs text-base-content/40">{wishlistItem.description}</p>
			{/if}

			<div class="mt-2 flex flex-wrap items-center gap-2">
				<span
					class="text-sm font-semibold"
					class:text-success={isGoodDeal}
					class:text-error={!isGoodDeal}
				>
					{formatPrice(wishlistItem.current_price)}
				</span>
				<span class="text-xs text-base-content/40"
					>meta: {formatPrice(wishlistItem.target_price)}</span
				>
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
