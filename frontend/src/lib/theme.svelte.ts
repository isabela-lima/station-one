// ─── Tema visual ──────────────────────────────────────────
// Três temas, mesmo layout. O tema salvo é aplicado antes do primeiro
// paint por um script inline em app.html; aqui só mantemos o estado
// reativo e persistimos a escolha.

export type ThemeId = 'orbita' | 'diario' | 'painel';

export const THEMES: { id: ThemeId; label: string; description: string }[] = [
	{ id: 'orbita', label: 'Órbita', description: 'Escuro, espacial' },
	{ id: 'diario', label: 'Diário', description: 'Escuro, minimalista' },
	{ id: 'painel', label: 'Painel', description: 'Claro, colorido' }
];

const STORAGE_KEY = 'station-theme';

function isThemeId(value: unknown): value is ThemeId {
	return THEMES.some((t) => t.id === value);
}

function initialTheme(): ThemeId {
	if (typeof document === 'undefined') return 'orbita';
	const current = document.documentElement.dataset.theme;
	return isThemeId(current) ? current : 'orbita';
}

export const theme = $state<{ current: ThemeId }>({ current: initialTheme() });

export function setTheme(id: ThemeId) {
	theme.current = id;
	document.documentElement.dataset.theme = id;
	try {
		localStorage.setItem(STORAGE_KEY, id);
	} catch {
		/* modo privado etc. — o tema vale só para esta sessão */
	}
}
