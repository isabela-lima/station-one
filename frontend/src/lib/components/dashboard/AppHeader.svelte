<script lang="ts">
	import { Plus, LogOut, Check, Sparkles, Settings } from 'lucide-svelte';
	import { THEMES, theme, setTheme } from '$lib/theme.svelte';
	import { SECTIONS, type Section } from './types';

	let {
		activeSection = $bindable<Section>(),
		userName,
		initials,
		onCreate,
		onAssistant,
		onLogout
	}: {
		activeSection: Section;
		userName: string;
		initials: string;
		onCreate: () => void;
		onAssistant: () => void;
		onLogout: () => void;
	} = $props();

	let menu = $state<HTMLDetailsElement | null>(null);

	function closeMenu() {
		if (menu) menu.open = false;
	}
</script>

<header class="flex flex-wrap items-center justify-between gap-3">
	<nav aria-label="Seções" class="chips flex gap-2 overflow-x-auto">
		{#each SECTIONS as s (s.id)}
			<button
				type="button"
				class="chip sec-{s.color}"
				class:active={activeSection === s.id}
				aria-current={activeSection === s.id ? 'page' : undefined}
				onclick={() => (activeSection = s.id)}
			>
				<s.Icon size={15} strokeWidth={2.2} />
				{s.label}
			</button>
		{/each}
	</nav>

	<!-- ml-auto: quando o cabeçalho quebra de linha (celular), os botões ficam à direita
	     e o menu do avatar, ancorado na direita, não sai da tela -->
	<div class="ml-auto flex items-center gap-2">
		<button
			type="button"
			class="assistant-btn"
			aria-label="Registrar com o assistente (⌘K)"
			title="Registrar com o assistente (⌘K)"
			onclick={onAssistant}
		>
			<Sparkles size={18} />
		</button>
		<button type="button" class="new-btn" onclick={onCreate}>
			<Plus size={18} strokeWidth={2.4} />
			Novo
		</button>

		<details class="relative" bind:this={menu}>
			<summary class="avatar-btn" aria-label="Menu de {userName}">{initials || '?'}</summary>
			<div class="menu-panel">
				<div class="px-3 pt-2 pb-3 text-sm font-semibold">{userName}</div>
				<div class="px-3 pb-1 text-xs text-base-content/60">Tema</div>
				{#each THEMES as t (t.id)}
					<button
						type="button"
						class="menu-item"
						onclick={() => {
							setTheme(t.id);
							closeMenu();
						}}
					>
						<span class="theme-dot" data-theme={t.id} aria-hidden="true"></span>
						<span class="flex flex-1 flex-col items-start">
							<span class="text-sm">{t.label}</span>
							<span class="text-xs text-base-content/60">{t.description}</span>
						</span>
						{#if theme.current === t.id}<Check size={16} class="text-primary" />{/if}
					</button>
				{/each}
				<div class="my-1 h-px bg-base-300"></div>
				<button
					type="button"
					class="menu-item"
					onclick={() => {
						activeSection = 'settings';
						closeMenu();
					}}
				>
					<Settings size={16} />
					<span class="text-sm">Configurações</span>
				</button>
				<button type="button" class="menu-item text-error" onclick={onLogout}>
					<LogOut size={16} />
					<span class="text-sm">Sair</span>
				</button>
			</div>
		</details>
	</div>
</header>

<style>
	.chips {
		scrollbar-width: none;
		max-width: 100%;
	}
	.chips::-webkit-scrollbar {
		display: none;
	}

	.chip {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		flex-shrink: 0;
		min-height: 40px;
		padding: 0 14px;
		border-radius: var(--radius-selector);
		background: var(--sec-soft);
		color: var(--sec-ink);
		font: 600 13px/1 var(--font-body);
		cursor: pointer;
		transition:
			background 0.15s ease,
			color 0.15s ease;
	}
	.chip:hover {
		background: color-mix(in oklab, var(--sec) 22%, var(--sec-soft));
	}
	.chip.active {
		background: var(--sec);
		color: var(--color-base-100);
	}
	.chip:focus-visible,
	.new-btn:focus-visible,
	.avatar-btn:focus-visible,
	.menu-item:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}

	.new-btn {
		display: inline-flex;
		align-items: center;
		gap: 6px;
		min-height: 44px;
		padding: 0 18px;
		border-radius: var(--radius-selector);
		background: var(--color-primary);
		color: var(--color-primary-content);
		font: 700 14px/1 var(--font-body);
		cursor: pointer;
	}
	.new-btn:hover {
		filter: brightness(1.08);
	}

	.assistant-btn {
		display: flex;
		align-items: center;
		justify-content: center;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: color-mix(in oklab, var(--color-primary) 16%, transparent);
		color: var(--color-primary);
		cursor: pointer;
	}
	.assistant-btn:hover {
		background: color-mix(in oklab, var(--color-primary) 26%, transparent);
	}
	.assistant-btn:focus-visible {
		outline: 2px solid var(--color-primary);
		outline-offset: 2px;
	}

	.avatar-btn {
		list-style: none;
		display: flex;
		align-items: center;
		justify-content: center;
		width: 44px;
		height: 44px;
		border-radius: 999px;
		background: var(--color-base-300);
		color: var(--color-base-content);
		font: var(--display-weight) 15px/1 var(--font-display);
		cursor: pointer;
		user-select: none;
	}
	.avatar-btn::-webkit-details-marker {
		display: none;
	}

	.menu-panel {
		position: absolute;
		right: 0;
		top: calc(100% + 8px);
		z-index: 50;
		width: 240px;
		max-width: calc(100vw - 32px);
		padding: 6px;
		border-radius: var(--radius-box);
		background: var(--color-base-200);
		border: 1px solid var(--color-base-300);
		box-shadow: 0 12px 32px rgba(0, 0, 0, 0.25);
	}

	.menu-item {
		display: flex;
		align-items: center;
		gap: 10px;
		width: 100%;
		min-height: 44px;
		padding: 6px 10px;
		border-radius: var(--radius-field);
		text-align: left;
		cursor: pointer;
	}
	.menu-item:hover {
		background: var(--color-base-300);
	}

	/* Bolinha de prévia: usa as cores do próprio tema via data-theme */
	.theme-dot {
		width: 22px;
		height: 22px;
		flex-shrink: 0;
		border-radius: 999px;
		background: linear-gradient(135deg, var(--color-base-100) 50%, var(--color-primary) 50%);
		border: 1px solid var(--color-base-300);
	}
</style>
