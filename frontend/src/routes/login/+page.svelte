<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { supabase } from '$lib/supabase';
	import { Satellite, Loader2, Mail, CheckCircle2, RotateCcw, KeyRound } from 'lucide-svelte';

	type Step = 'login' | 'register' | 'confirm' | 'forgot' | 'reset';
	let step = $state<Step>('login');

	let email = $state('');
	let password = $state('');
	let errorMsg = $state('');
	let loading = $state(false);
	let resendLoading = $state(false);
	let resendSuccess = $state(false);
	let resetSent = $state(false);
	let newPassword = $state('');
	let confirmPassword = $state('');

	// O link do email de recuperação volta para /login?reset=1 já com a sessão
	// de recuperação no hash da URL (o supabase-js consome o hash sozinho).
	onMount(async () => {
		const url = new URL(window.location.href);
		if (url.searchParams.get('reset') !== '1') return;

		const hashParams = new URLSearchParams(url.hash.slice(1));
		const { data } = await supabase.auth.getSession();
		if (data.session) {
			step = 'reset';
		} else {
			step = 'forgot';
			errorMsg =
				hashParams.get('error_code') === 'otp_expired'
					? 'Link expirado. Peça um novo abaixo.'
					: 'Link inválido. Peça um novo abaixo.';
		}
		history.replaceState(null, '', '/login');
	});

	async function handleForgot() {
		if (!email.trim()) return;
		loading = true;
		errorMsg = '';
		try {
			const { error } = await supabase.auth.resetPasswordForEmail(email, {
				redirectTo: `${window.location.origin}/login?reset=1`
			});
			if (error) {
				errorMsg = error.message;
				return;
			}
			resetSent = true;
		} catch {
			errorMsg = 'Erro de conexão. Tente novamente.';
		} finally {
			loading = false;
		}
	}

	async function handleReset() {
		errorMsg = '';
		if (newPassword.length < 6) {
			errorMsg = 'A senha precisa ter pelo menos 6 caracteres.';
			return;
		}
		if (newPassword !== confirmPassword) {
			errorMsg = 'As senhas não coincidem.';
			return;
		}
		loading = true;
		try {
			const { error } = await supabase.auth.updateUser({ password: newPassword });
			if (error) {
				errorMsg = error.message;
				return;
			}
			goto('/');
		} catch {
			errorMsg = 'Erro de conexão. Tente novamente.';
		} finally {
			loading = false;
		}
	}

	async function handleSubmit() {
		if (!email.trim() || !password.trim()) return;
		loading = true;
		errorMsg = '';

		try {
			if (step === 'login') {
				const { error } = await supabase.auth.signInWithPassword({ email, password });
				if (error) {
					if (error.message.toLowerCase().includes('email not confirmed')) {
						// Redirect to confirm screen so user can resend
						step = 'confirm';
					} else if (error.message.toLowerCase().includes('invalid login')) {
						errorMsg = 'Email ou senha inválidos.';
					} else {
						errorMsg = error.message;
					}
					return;
				}
				goto('/');
			} else {
				// register
				const { data, error } = await supabase.auth.signUp({ email, password });
				if (error) {
					errorMsg = error.message;
					return;
				}
				if (!data.session) {
					// Email confirmation required — show confirm screen
					step = 'confirm';
					return;
				}
				// Confirmation disabled — signed in immediately
				goto('/');
			}
		} catch {
			errorMsg = 'Erro de conexão. Tente novamente.';
		} finally {
			loading = false;
		}
	}

	async function handleResend() {
		if (!email.trim() || resendLoading) return;
		resendLoading = true;
		resendSuccess = false;
		try {
			const { error } = await supabase.auth.resend({ type: 'signup', email });
			if (!error) resendSuccess = true;
			else errorMsg = error.message;
		} catch {
			errorMsg = 'Não foi possível reenviar o email.';
		} finally {
			resendLoading = false;
		}
	}

	function goBack() {
		step = 'login';
		errorMsg = '';
		resendSuccess = false;
		resetSent = false;
	}
</script>

<div class="login-bg flex min-h-screen items-center justify-center p-4">
	<!-- Ambient glow -->
	<div class="pointer-events-none fixed inset-0 overflow-hidden" aria-hidden="true">
		<div class="glow-orb glow-orb-1"></div>
		<div class="glow-orb glow-orb-2"></div>
	</div>

	<div class="login-card w-full max-w-sm">
		<!-- Header -->
		<div class="mb-8 flex flex-col items-center gap-3">
			<div class="login-icon-ring">
				{#if step === 'confirm'}
					<Mail size={22} class="text-primary" />
				{:else if step === 'forgot' || step === 'reset'}
					<KeyRound size={22} class="text-primary" />
				{:else}
					<Satellite size={22} class="text-primary" />
				{/if}
			</div>
			<div class="text-center">
				<h1 class="text-2xl font-bold tracking-tight text-base-content">Station One</h1>
				<p class="mt-1 text-xs tracking-widest text-primary/50 uppercase">
					{#if step === 'login'}Acesso ao sistema
					{:else if step === 'register'}Novo operador
					{:else if step === 'forgot'}Recuperar acesso
					{:else if step === 'reset'}Nova senha
					{:else}Confirme seu email
					{/if}
				</p>
			</div>
		</div>

		<!-- ── Confirm Email Screen ─────────────────────── -->
		{#if step === 'confirm'}
			<div class="space-y-4">
				<div class="login-info-box">
					<div class="flex gap-3">
						<Mail size={18} class="mt-0.5 shrink-0" style="color: var(--color-primary)" />
						<div class="space-y-1">
							<p class="text-sm font-semibold" style="color: var(--color-primary)">
								Verifique sua caixa de entrada
							</p>
							<p class="text-xs leading-relaxed text-base-content/60">
								Enviamos um link de confirmação para <strong class="text-base-content/80"
									>{email}</strong
								>. Clique no link para ativar sua conta e depois volte aqui para entrar.
							</p>
						</div>
					</div>
				</div>

				{#if resendSuccess}
					<div class="flex items-center gap-2 px-1">
						<CheckCircle2 size={14} class="shrink-0 text-success" />
						<span class="text-xs text-success">Email reenviado com sucesso!</span>
					</div>
				{/if}

				{#if errorMsg}
					<div class="login-error">
						<span class="text-xs">{errorMsg}</span>
					</div>
				{/if}

				<button
					type="button"
					class="login-btn"
					onclick={handleResend}
					disabled={resendLoading || resendSuccess}
				>
					{#if resendLoading}
						<Loader2 size={16} class="animate-spin" />
					{:else}
						<RotateCcw size={14} />
					{/if}
					{resendSuccess ? 'Email reenviado!' : 'Reenviar email de confirmação'}
				</button>

				<button
					type="button"
					class="w-full py-1 text-center text-xs text-base-content/40 transition-colors hover:text-base-content/70"
					onclick={goBack}
				>
					← Voltar para o login
				</button>
			</div>

			<!-- ── Forgot Password ──────────────────────────── -->
		{:else if step === 'forgot'}
			{#if resetSent}
				<div class="space-y-4">
					<div class="login-info-box">
						<div class="flex gap-3">
							<Mail size={18} class="mt-0.5 shrink-0" style="color: var(--color-primary)" />
							<div class="space-y-1">
								<p class="text-sm font-semibold" style="color: var(--color-primary)">
									Verifique sua caixa de entrada
								</p>
								<p class="text-xs leading-relaxed text-base-content/60">
									Se existir uma conta para <strong class="text-base-content/80">{email}</strong>,
									você vai receber um link para definir uma nova senha.
								</p>
							</div>
						</div>
					</div>
					<button
						type="button"
						class="w-full py-1 text-center text-xs text-base-content/40 transition-colors hover:text-base-content/70"
						onclick={goBack}
					>
						← Voltar para o login
					</button>
				</div>
			{:else}
				<form
					class="space-y-4"
					onsubmit={(e) => {
						e.preventDefault();
						handleForgot();
					}}
				>
					<p class="text-xs leading-relaxed text-base-content/50">
						Informe o email da sua conta e enviaremos um link para redefinir a senha.
					</p>
					<div class="form-group">
						<label class="login-label" for="forgot-email">Email</label>
						<input
							id="forgot-email"
							type="email"
							class="login-input"
							placeholder="seu@email.com"
							bind:value={email}
							required
							autocomplete="email"
						/>
					</div>

					{#if errorMsg}
						<div class="login-error">
							<span class="text-xs">{errorMsg}</span>
						</div>
					{/if}

					<button type="submit" class="login-btn" disabled={loading}>
						{#if loading}
							<Loader2 size={16} class="animate-spin" />
						{/if}
						Enviar link de recuperação
					</button>
					<button
						type="button"
						class="w-full py-1 text-center text-xs text-base-content/40 transition-colors hover:text-base-content/70"
						onclick={goBack}
					>
						← Voltar para o login
					</button>
				</form>
			{/if}

			<!-- ── Reset Password (vindo do link do email) ───── -->
		{:else if step === 'reset'}
			<form
				class="space-y-4"
				onsubmit={(e) => {
					e.preventDefault();
					handleReset();
				}}
			>
				<div class="form-group">
					<label class="login-label" for="new-password">Nova senha</label>
					<input
						id="new-password"
						type="password"
						class="login-input"
						placeholder="••••••••"
						bind:value={newPassword}
						required
						minlength="6"
						autocomplete="new-password"
					/>
				</div>
				<div class="form-group">
					<label class="login-label" for="confirm-password">Confirmar senha</label>
					<input
						id="confirm-password"
						type="password"
						class="login-input"
						placeholder="••••••••"
						bind:value={confirmPassword}
						required
						minlength="6"
						autocomplete="new-password"
					/>
				</div>

				{#if errorMsg}
					<div class="login-error">
						<span class="text-xs">{errorMsg}</span>
					</div>
				{/if}

				<button type="submit" class="login-btn" disabled={loading}>
					{#if loading}
						<Loader2 size={16} class="animate-spin" />
					{/if}
					Salvar nova senha
				</button>
			</form>

			<!-- ── Login / Register Form ────────────────────── -->
		{:else}
			<form
				class="space-y-4"
				onsubmit={(e) => {
					e.preventDefault();
					handleSubmit();
				}}
			>
				<div class="form-group">
					<label class="login-label" for="email">Email</label>
					<input
						id="email"
						type="email"
						class="login-input"
						placeholder="seu@email.com"
						bind:value={email}
						required
						autocomplete="email"
					/>
				</div>

				<div class="form-group">
					<div class="flex items-baseline justify-between">
						<label class="login-label" for="password">Senha</label>
						{#if step === 'login'}
							<button
								type="button"
								class="text-[10px] text-primary/60 transition-colors hover:text-primary"
								onclick={() => {
									step = 'forgot';
									errorMsg = '';
									resetSent = false;
								}}
							>
								Esqueci minha senha
							</button>
						{/if}
					</div>
					<input
						id="password"
						type="password"
						class="login-input"
						placeholder="••••••••"
						bind:value={password}
						required
						autocomplete={step === 'login' ? 'current-password' : 'new-password'}
					/>
				</div>

				{#if errorMsg}
					<div class="login-error">
						<span class="text-xs">{errorMsg}</span>
					</div>
				{/if}

				<button type="submit" class="login-btn" disabled={loading}>
					{#if loading}
						<Loader2 size={16} class="animate-spin" />
					{/if}
					{step === 'login' ? 'Entrar' : 'Criar conta'}
				</button>
			</form>

			<!-- Toggle mode -->
			<p class="mt-6 text-center text-xs text-base-content/40">
				{step === 'login' ? 'Sem conta?' : 'Já tem conta?'}
				<button
					class="ml-1 text-primary/70 underline underline-offset-2 transition-colors hover:text-primary"
					onclick={() => {
						step = step === 'login' ? 'register' : 'login';
						errorMsg = '';
					}}
				>
					{step === 'login' ? 'Criar conta' : 'Entrar'}
				</button>
			</p>
		{/if}

		<!-- Footer -->
		<div class="mt-8 flex items-center justify-center gap-2">
			<div class="status-dot"></div>
			<span class="text-[10px] tracking-widest text-base-content/20 uppercase">Sistema online</span>
		</div>
	</div>
</div>

<style>
	.login-bg {
		background: var(--color-base-100);
	}

	.glow-orb {
		position: absolute;
		border-radius: 50%;
		filter: blur(80px);
		opacity: 0.12;
	}

	.glow-orb-1 {
		width: 500px;
		height: 500px;
		background: var(--color-primary);
		top: -200px;
		left: -150px;
	}

	.glow-orb-2 {
		width: 400px;
		height: 400px;
		background: var(--color-secondary);
		bottom: -180px;
		right: -100px;
	}

	.login-card {
		position: relative;
		background: color-mix(in oklab, var(--color-base-content) 3%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-primary) 15%, transparent);
		border-radius: 1.25rem;
		padding: 2.5rem;
		backdrop-filter: blur(24px);
		-webkit-backdrop-filter: blur(24px);
		box-shadow:
			0 0 0 1px color-mix(in oklab, var(--color-primary) 5%, transparent),
			0 24px 64px rgba(0, 0, 0, 0.35),
			0 0 40px color-mix(in oklab, var(--color-primary) 4%, transparent) inset;
	}

	.login-icon-ring {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 52px;
		height: 52px;
		border-radius: 50%;
		background: color-mix(in oklab, var(--color-primary) 10%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-primary) 25%, transparent);
		box-shadow: 0 0 20px color-mix(in oklab, var(--color-primary) 12%, transparent);
	}

	.form-group {
		display: flex;
		flex-direction: column;
		gap: 0.375rem;
	}

	.login-label {
		font-size: 0.65rem;
		font-weight: 600;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		color: color-mix(in oklch, var(--color-base-content) 50%, transparent);
	}

	.login-input {
		width: 100%;
		padding: 0.625rem 0.875rem;
		font-size: 0.875rem;
		background: color-mix(in oklab, var(--color-base-content) 4%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-primary) 18%, transparent);
		border-radius: 0.625rem;
		color: var(--color-base-content);
		outline: none;
		transition:
			border-color 0.15s,
			box-shadow 0.15s;
	}

	.login-input::placeholder {
		color: color-mix(in oklch, var(--color-base-content) 25%, transparent);
	}

	.login-input:focus {
		border-color: color-mix(in oklab, var(--color-primary) 50%, transparent);
		box-shadow: 0 0 0 3px color-mix(in oklab, var(--color-primary) 8%, transparent);
	}

	.login-info-box {
		padding: 1rem;
		border-radius: 0.75rem;
		background: color-mix(in oklab, var(--color-primary) 7%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-primary) 20%, transparent);
	}

	.login-error {
		padding: 0.5rem 0.75rem;
		border-radius: 0.5rem;
		background: color-mix(in oklab, var(--color-error) 8%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-error) 20%, transparent);
		color: var(--color-error);
	}

	.login-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		gap: 0.5rem;
		width: 100%;
		padding: 0.625rem 1rem;
		font-size: 0.875rem;
		font-weight: 600;
		border-radius: 0.625rem;
		background: color-mix(in oklab, var(--color-primary) 15%, transparent);
		border: 1px solid color-mix(in oklab, var(--color-primary) 35%, transparent);
		color: var(--color-primary);
		cursor: pointer;
		transition:
			background 0.15s,
			box-shadow 0.15s,
			opacity 0.15s;
		margin-top: 0.25rem;
	}

	.login-btn:hover:not(:disabled) {
		background: color-mix(in oklab, var(--color-primary) 22%, transparent);
		box-shadow: 0 0 16px color-mix(in oklab, var(--color-primary) 15%, transparent);
	}

	.login-btn:disabled {
		opacity: 0.6;
		cursor: not-allowed;
	}

	.status-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		background: var(--color-primary);
		box-shadow: 0 0 6px var(--color-primary);
		animation: pulse 2s infinite;
	}

	@keyframes pulse {
		0%,
		100% {
			opacity: 1;
		}
		50% {
			opacity: 0.4;
		}
	}
</style>
