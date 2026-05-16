<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { supabase } from '$lib/supabase';
	import './layout.css';

	let { children } = $props();

	onMount(async () => {
		const { data } = await supabase.auth.getSession();
		if (!data.session && page.url.pathname !== '/login') {
			goto('/login');
		}

		// Listen for auth state changes (e.g. session expiry)
		supabase.auth.onAuthStateChange((_event, session) => {
			if (!session && page.url.pathname !== '/login') {
				goto('/login');
			}
		});
	});
</script>

{@render children()}
