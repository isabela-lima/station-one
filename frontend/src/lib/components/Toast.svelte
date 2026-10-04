<script lang="ts">
	import { toasts } from '$lib/toast';
</script>

<div class="toast toast-end toast-bottom z-50 gap-2">
	{#each $toasts as toast (toast.id)}
		<div
			class="alert glass-card flex items-center gap-2 py-3 px-4 shadow-lg"
			style="border-color: {toast.type === 'success'
				? 'color-mix(in oklab, var(--color-success) 40%, transparent)'
				: toast.type === 'error'
					? 'color-mix(in oklab, var(--color-error) 40%, transparent)'
					: 'color-mix(in oklab, var(--color-primary) 40%, transparent)'}; min-width: 240px; max-width: 340px"
		>
			{#if toast.type === 'success'}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4 shrink-0 text-success"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
				</svg>
			{:else if toast.type === 'error'}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4 shrink-0 text-error"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			{:else}
				<svg
					xmlns="http://www.w3.org/2000/svg"
					class="h-4 w-4 shrink-0 text-primary"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
					/>
				</svg>
			{/if}
			<span class="text-sm">{toast.message}</span>
		</div>
	{/each}
</div>
