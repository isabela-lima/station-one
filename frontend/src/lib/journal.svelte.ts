// ─── Diário de bordo: estado compartilhado ───────────────
// O tile de "Hoje" e a página do Diário leem e escrevem o mesmo estado,
// então uma entrada criada num aparece no outro sem recarregar.

import * as api from '$lib/api';
import { showToast } from '$lib/toast';
import type { JournalDay, LogEntry } from '$lib/models/types';

export const journalToday = $state<{ day: JournalDay | null; loading: boolean; failed: boolean }>({
	day: null,
	loading: false,
	failed: false
});

let inflight: Promise<void> | null = null;

/** Carrega o dia de hoje (uma vez; chamadas simultâneas compartilham a requisição) */
export function loadJournalToday(force = false): Promise<void> {
	if (inflight) return inflight;
	if (journalToday.day && !force) return Promise.resolve();
	journalToday.loading = !journalToday.day;
	inflight = api.journal
		.today()
		.then((day) => {
			journalToday.day = day;
			journalToday.failed = false;
		})
		.catch(() => {
			journalToday.failed = true;
		})
		.finally(() => {
			journalToday.loading = false;
			inflight = null;
		});
	return inflight;
}

const URL_RE = /https?:\/\/\S+/i;

/** Cria uma entrada (otimista). Um link no texto vira o `url` da entrada. */
export async function addEntry(text: string): Promise<boolean> {
	const day = journalToday.day;
	const content = text.trim();
	if (!day || !content) return false;

	const url = content.match(URL_RE)?.[0] ?? null;
	const temp: LogEntry = {
		// crypto.randomUUID só existe em HTTPS/localhost; no celular via IP da rede local, não
		id: `temp-${Date.now()}-${Math.random().toString(36).slice(2)}`,
		date: day.date,
		content,
		url,
		created_at: new Date().toISOString()
	};
	day.entries = [temp, ...day.entries];
	try {
		const saved = await api.journal.addEntry({ content, url });
		day.entries = day.entries.map((e) => (e.id === temp.id ? saved : e));
		return true;
	} catch {
		day.entries = day.entries.filter((e) => e.id !== temp.id);
		showToast('Não foi possível salvar a entrada.', 'error');
		return false;
	}
}

export async function deleteEntry(id: string) {
	const day = journalToday.day;
	if (!day) return;
	const before = day.entries;
	day.entries = before.filter((e) => e.id !== id);
	try {
		await api.journal.deleteEntry(id);
	} catch {
		day.entries = before;
		showToast('Não foi possível apagar a entrada.', 'error');
	}
}

/** Humor/energia (1–5). Tocar no valor já marcado limpa. */
export async function setCheckin(field: 'mood' | 'energy', value: number) {
	const day = journalToday.day;
	if (!day) return;
	const previous = day[field];
	const next = previous === value ? null : value;
	day[field] = next;
	try {
		await api.journal.checkin(day.date, { [field]: next });
	} catch {
		day[field] = previous;
		showToast('Não foi possível salvar o check-in.', 'error');
	}
}

export function entryTime(iso: string) {
	return new Date(iso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
}
