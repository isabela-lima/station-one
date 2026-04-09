<script lang="ts">
	import { goto } from '$app/navigation';
	import { pb } from '$lib/pb';

	let email = $state('');
	let password = $state('');
	let errorMsg = $state('');
	let loading = $state(false);
	let mode = $state<'login' | 'register'>('login');

	async function handleSubmit() {
		if (!email.trim() || !password.trim()) return;
		loading = true;
		errorMsg = '';

		try {
			if (mode === 'login') {
				await pb.collection('users').authWithPassword(email, password);
			} else {
				await pb.collection('users').create({ email, password, passwordConfirm: password });
				await pb.collection('users').authWithPassword(email, password);
			}
			goto('/');
		} catch (e: unknown) {
			errorMsg =
				mode === 'login'
					? 'Email ou senha inválidos.'
					: 'Não foi possível criar a conta. Verifique os dados.';
		} finally {
			loading = false;
		}
	}
</script>

<div class="min-h-screen flex items-center justify-center p-4">
	<div class="card bg-base-200 w-full max-w-sm p-8 space-y-6">
		<div>
			<h1 class="text-2xl font-bold">Station One</h1>
			<p class="text-sm opacity-60 mt-1">
				{mode === 'login' ? 'Entre na sua conta' : 'Crie sua conta'}
			</p>
		</div>

		<form class="space-y-4" onsubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
			<div class="form-control">
				<label class="label" for="email">
					<span class="label-text">Email</span>
				</label>
				<input
					id="email"
					type="email"
					class="input input-bordered"
					placeholder="seu@email.com"
					bind:value={email}
					required
				/>
			</div>

			<div class="form-control">
				<label class="label" for="password">
					<span class="label-text">Senha</span>
				</label>
				<input
					id="password"
					type="password"
					class="input input-bordered"
					placeholder="••••••••"
					bind:value={password}
					required
				/>
			</div>

			{#if errorMsg}
				<p class="text-error text-sm">{errorMsg}</p>
			{/if}

			<button type="submit" class="btn btn-primary w-full" disabled={loading}>
				{#if loading}
					<span class="loading loading-spinner loading-sm"></span>
				{/if}
				{mode === 'login' ? 'Entrar' : 'Criar conta'}
			</button>
		</form>

		<p class="text-sm text-center opacity-60">
			{mode === 'login' ? 'Não tem conta?' : 'Já tem conta?'}
			<button
				class="link link-primary"
				onclick={() => {
					mode = mode === 'login' ? 'register' : 'login';
					errorMsg = '';
				}}
			>
				{mode === 'login' ? 'Criar conta' : 'Entrar'}
			</button>
		</p>
	</div>
</div>
