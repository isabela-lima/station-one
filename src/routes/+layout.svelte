<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { pb } from '$lib/pb';
	import './layout.css';

	let { children } = $props();

	onMount(() => {
		if (!pb.authStore.isValid && $page.url.pathname !== '/login') {
			goto('/login');
		}
	});
</script>

{@render children()}
