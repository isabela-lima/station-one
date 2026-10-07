// ─── Datas de calendário (prazos) ────────────────────────
// Prazos são dias ("2026-10-10"), não instantes. Nunca use `new Date('2026-10-10')`:
// isso é meia-noite UTC e vira o dia anterior no Brasil. Tudo aqui usa o fuso local.

/** "YYYY-MM-DD" de uma data, no fuso local */
export function toISODate(d: Date): string {
	const y = d.getFullYear();
	const m = String(d.getMonth() + 1).padStart(2, '0');
	const day = String(d.getDate()).padStart(2, '0');
	return `${y}-${m}-${day}`;
}

/** Data local (meio-dia, para não escorregar de dia) a partir de "YYYY-MM-DD" */
export function parseISODate(iso: string): Date {
	const [y, m, d] = iso.split('-').map(Number);
	return new Date(y, m - 1, d, 12);
}

export function todayISO(): string {
	return toISODate(new Date());
}

export function addDaysISO(iso: string, days: number): string {
	const d = parseISODate(iso);
	d.setDate(d.getDate() + days);
	return toISODate(d);
}

/** Dias de `from` até `to` (negativo se `to` já passou) */
export function daysBetween(from: string, to: string): number {
	return Math.round((parseISODate(to).getTime() - parseISODate(from).getTime()) / 86_400_000);
}

/** Próxima ocorrência de um dia da semana (0 = domingo); hoje conta como "daqui a 7" */
export function nextWeekdayISO(weekday: number, from = todayISO()): string {
	const d = parseISODate(from);
	const delta = (weekday - d.getDay() + 7) % 7 || 7;
	return addDaysISO(from, delta);
}

export type DueTone = 'overdue' | 'today' | 'soon' | 'later';

/** Rótulo curto e tom visual de um prazo em relação a hoje */
export function dueInfo(due: string, today = todayISO()): { label: string; tone: DueTone } {
	const diff = daysBetween(today, due);
	const date = parseISODate(due);
	const short = date
		.toLocaleDateString('pt-BR', { day: 'numeric', month: 'short' })
		.replace('.', '');

	if (diff < 0) return { label: diff === -1 ? 'ontem' : `atrasada · ${short}`, tone: 'overdue' };
	if (diff === 0) return { label: 'hoje', tone: 'today' };
	if (diff === 1) return { label: 'amanhã', tone: 'soon' };
	if (diff < 7) {
		const weekday = date.toLocaleDateString('pt-BR', { weekday: 'short' }).replace('.', '');
		return { label: weekday, tone: 'soon' };
	}
	return { label: short, tone: 'later' };
}

/**
 * Ordem de urgência para tarefas: atrasadas, hoje, próximas por data, sem prazo.
 * Empate: foco (priority) primeiro.
 */
export function compareByUrgency(
	a: { due_date?: string | null; priority: boolean },
	b: { due_date?: string | null; priority: boolean }
): number {
	if (a.due_date && b.due_date && a.due_date !== b.due_date)
		return a.due_date < b.due_date ? -1 : 1;
	if (a.due_date && !b.due_date) return -1;
	if (!a.due_date && b.due_date) return 1;
	return Number(b.priority) - Number(a.priority);
}
