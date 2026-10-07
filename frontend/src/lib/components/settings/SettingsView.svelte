<script lang="ts">
	import { onMount } from 'svelte';
	import { KeyRound, Loader2, Trash2, ExternalLink, Check } from 'lucide-svelte';
	import * as api from '$lib/api';
	import { showToast } from '$lib/toast';
	import type { AssistantUsage, UserSettings } from '$lib/models/types';

	let prefs = $state<UserSettings | null>(null);
	let usage = $state<AssistantUsage | null>(null);
	let loadFailed = $state(false);

	let keyInput = $state('');
	let savingKey = $state(false);
	let keyError = $state('');
	let savingModel = $state<string | null>(null);

	onMount(async () => {
		try {
			[prefs, usage] = await Promise.all([api.settings.get(), api.settings.usage()]);
		} catch {
			loadFailed = true;
		}
	});

	async function saveKey(e: SubmitEvent) {
		e.preventDefault();
		if (!keyInput.trim() || savingKey) return;
		savingKey = true;
		keyError = '';
		try {
			prefs = await api.settings.setAnthropicKey(keyInput.trim());
			keyInput = '';
			showToast('Chave salva. O assistente está pronto.');
		} catch (err) {
			keyError = err instanceof Error ? err.message : 'Não foi possível salvar a chave.';
		} finally {
			savingKey = false;
		}
	}

	async function removeKey() {
		if (!confirm('Remover sua chave da API? O assistente para de funcionar até você colar outra.'))
			return;
		try {
			prefs = await api.settings.deleteAnthropicKey();
			showToast('Chave removida.');
		} catch {
			showToast('Não foi possível remover a chave.', 'error');
		}
	}

	async function pickModel(id: string) {
		if (!prefs || prefs.assistant_model === id) return;
		savingModel = id;
		try {
			prefs = await api.settings.setModel(id);
		} catch {
			showToast('Não foi possível trocar o modelo.', 'error');
		} finally {
			savingModel = null;
		}
	}

	function usd(value: string | number, digits = 2) {
		return new Intl.NumberFormat('pt-BR', {
			style: 'currency',
			currency: 'USD',
			minimumFractionDigits: digits,
			maximumFractionDigits: Math.max(digits, 4)
		}).format(Number(value));
	}
</script>

<div class="flex flex-col gap-8">
	{#if loadFailed}
		<p class="muted">Não foi possível carregar as configurações.</p>
	{:else if !prefs}
		<div class="skeleton-pulse h-40"></div>
	{:else}
		<!-- ── Chave da API ─────────────────────────────── -->
		<section class="flex flex-col gap-3" aria-labelledby="key-title">
			<h2 id="key-title" class="font-display flex items-center gap-2 text-lg">
				<KeyRound size={18} /> Chave da API da Anthropic
			</h2>
			<p class="muted">
				O assistente usa a <strong>sua</strong> conta da Anthropic, e o uso é cobrado nela. A chave
				fica guardada criptografada no servidor e nunca volta para o navegador.
				<a
					href="https://console.anthropic.com/settings/keys"
					target="_blank"
					rel="noopener noreferrer">Criar uma chave <ExternalLink size={12} class="inline" /></a
				>
			</p>

			{#if prefs.has_anthropic_key}
				<div class="key-status">
					<Check size={16} class="text-success" />
					<span class="flex-1"
						>Chave salva <span class="font-mono-num">{prefs.anthropic_key_hint}</span></span
					>
					<button type="button" class="ghost-btn danger" onclick={removeKey}>
						<Trash2 size={15} /> Remover
					</button>
				</div>
			{/if}

			<form class="key-form" onsubmit={saveKey}>
				<label class="sr-only" for="api-key">Chave da API</label>
				<input
					id="api-key"
					type="password"
					autocomplete="off"
					spellcheck="false"
					placeholder={prefs.has_anthropic_key ? 'Colar outra chave (sk-ant-…)' : 'sk-ant-…'}
					bind:value={keyInput}
				/>
				<button type="submit" class="primary-btn" disabled={!keyInput.trim() || savingKey}>
					{#if savingKey}<Loader2 size={16} class="animate-spin" /> Conferindo…{:else}Salvar{/if}
				</button>
			</form>
			{#if keyError}<p class="error-line" role="alert">{keyError}</p>{/if}
		</section>

		<!-- ── Modelo ───────────────────────────────────── -->
		<section class="flex flex-col gap-3" aria-labelledby="model-title">
			<h2 id="model-title" class="font-display text-lg">Modelo do assistente</h2>
			<p class="muted">
				Preços por milhão de tokens (entrada / saída). Um registro curto usa poucos milhares.
			</p>
			<div class="models" role="radiogroup" aria-labelledby="model-title">
				{#each prefs.models as m (m.id)}
					<button
						type="button"
						role="radio"
						aria-checked={prefs.assistant_model === m.id}
						class="model"
						class:on={prefs.assistant_model === m.id}
						disabled={savingModel !== null}
						onclick={() => pickModel(m.id)}
					>
						<span class="flex items-center justify-between gap-2">
							<span class="font-semibold">{m.label}</span>
							{#if savingModel === m.id}<Loader2
									size={15}
									class="animate-spin"
								/>{:else if prefs.assistant_model === m.id}<Check size={16} />{/if}
						</span>
						<span class="model-desc">{m.description}</span>
						<span class="model-price font-mono-num"
							>{usd(m.input_per_mtok, 0)} / {usd(m.output_per_mtok, 0)}</span
						>
					</button>
				{/each}
			</div>
		</section>

		<!-- ── Uso ──────────────────────────────────────── -->
		{#if usage}
			<section class="flex flex-col gap-3" aria-labelledby="usage-title">
				<h2 id="usage-title" class="font-display text-lg">Uso neste mês</h2>
				<div class="usage">
					<div>
						<span class="usage-value font-mono-num">{usage.calls}</span><span class="muted"
							>chamadas</span
						>
					</div>
					<div>
						<span class="usage-value font-mono-num">{usd(usage.cost_usd, 2)}</span><span
							class="muted">custo estimado</span
						>
					</div>
				</div>
				<p class="muted">
					Estimativa pelos preços públicos; o valor oficial está no console da Anthropic.
				</p>
			</section>
		{/if}
	{/if}
</div>

<style>
	.muted {
		margin: 0;
		font-size: 14px;
		line-height: 1.55;
		color: color-mix(in oklab, var(--color-base-content) 68%, transparent);
	}
	.muted a {
		color: var(--color-primary);
		white-space: nowrap;
	}

	.key-status {
		display: flex;
		align-items: center;
		gap: 10px;
		padding: 10px 12px;
		border-radius: var(--radius-field);
		background: color-mix(in oklab, var(--color-success) 12%, transparent);
		font-size: 14px;
	}
	.key-form {
		display: flex;
		gap: 8px;
	}
	.key-form input {
		flex: 1;
		min-width: 0;
		min-height: 46px;
		padding: 0 14px;
		border-radius: var(--radius-field);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
		font-family: var(--font-mono);
		font-size: 14px;
		outline: none;
	}
	.key-form input:focus {
		border-color: var(--color-primary);
	}
	.primary-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		min-height: 46px;
		padding: 0 18px;
		border-radius: var(--radius-field);
		background: var(--color-primary);
		color: var(--color-primary-content);
		font-weight: 700;
		cursor: pointer;
	}
	.primary-btn:disabled {
		opacity: 0.45;
		cursor: default;
	}
	.ghost-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		min-height: 36px;
		padding: 0 10px;
		border-radius: var(--radius-field);
		font-weight: 600;
		cursor: pointer;
	}
	.ghost-btn.danger:hover {
		background: color-mix(in oklab, var(--color-error) 14%, transparent);
		color: var(--color-error);
	}
	.error-line {
		margin: 0;
		font-size: 14px;
		color: var(--color-error);
	}

	.models {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 10px;
	}
	.model {
		display: flex;
		flex-direction: column;
		gap: 6px;
		padding: 14px;
		border-radius: var(--radius-box);
		border: 2px solid var(--color-base-300);
		background: var(--color-base-100);
		text-align: left;
		cursor: pointer;
		transition: border-color 0.15s ease;
	}
	.model:hover:not(:disabled) {
		border-color: color-mix(in oklab, var(--color-primary) 50%, var(--color-base-300));
	}
	.model.on {
		border-color: var(--color-primary);
	}
	.model-desc {
		font-size: 13px;
		line-height: 1.4;
		color: color-mix(in oklab, var(--color-base-content) 68%, transparent);
	}
	.model-price {
		font-size: 13px;
	}

	.usage {
		display: flex;
		flex-wrap: wrap;
		gap: 32px;
	}
	.usage > div {
		display: flex;
		flex-direction: column;
		gap: 4px;
	}
	.usage-value {
		font-family: var(--font-display);
		font-weight: var(--display-weight);
		font-size: 26px;
	}

	button:focus-visible,
	input:focus-visible,
	a:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
