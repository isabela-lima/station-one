<script lang="ts">
	import { CornerDownLeft } from 'lucide-svelte';
	import { addEntry } from '$lib/journal.svelte';

	let {
		placeholder = 'Registrar algo… (Enter salva)',
		disabled = false
	}: { placeholder?: string; disabled?: boolean } = $props();

	let text = $state('');
	let input = $state<HTMLInputElement | null>(null);

	async function submit(e: SubmitEvent) {
		e.preventDefault();
		const value = text;
		if (!value.trim()) return;
		text = ''; // limpa na hora; se falhar, devolve o texto
		const ok = await addEntry(value);
		if (!ok) text = value;
		input?.focus();
	}
</script>

<form class="composer" onsubmit={submit}>
	<label class="sr-only" for="entry-input">Nova entrada no diário</label>
	<input
		id="entry-input"
		bind:this={input}
		bind:value={text}
		type="text"
		{placeholder}
		{disabled}
		autocomplete="off"
		maxlength="2000"
	/>
	<button type="submit" aria-label="Salvar entrada" disabled={disabled || !text.trim()}>
		<CornerDownLeft size={17} />
	</button>
</form>

<style>
	.composer {
		display: flex;
		gap: 8px;
	}
	input {
		flex: 1;
		min-width: 0;
		min-height: 48px;
		padding: 0 14px;
		border-radius: var(--radius-field);
		background: var(--color-base-100);
		border: 1px solid var(--color-base-300);
		color: var(--color-base-content);
		font-size: 15px;
		outline: none;
		transition: border-color 0.15s ease;
	}
	input::placeholder {
		color: color-mix(in oklab, var(--color-base-content) 45%, transparent);
	}
	input:focus {
		border-color: var(--c-journal);
	}
	button {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 48px;
		height: 48px;
		flex-shrink: 0;
		border-radius: var(--radius-field);
		background: var(--c-journal);
		color: var(--color-base-100);
		cursor: pointer;
	}
	button:disabled {
		opacity: 0.35;
		cursor: default;
	}
	button:focus-visible,
	input:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}
</style>
