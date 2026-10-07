// ─── Shared Dashboard Types ───────────────────────────────────────────────────

import {
	Sun,
	Zap,
	Target,
	FlameKindling,
	LineChart,
	ShoppingBag,
	BookOpen,
	Settings
} from 'lucide-svelte';

export type Section =
	| 'today'
	| 'operations'
	| 'missions'
	| 'journal'
	| 'wishlist'
	| 'finance'
	| 'protocols'
	| 'settings';

/** Seções criadas pelo botão "Novo" (o diário tem campo próprio na página) */
export type CreatableSection = Exclude<Section, 'today' | 'journal' | 'settings'>;

/** Ordem da navegação; `color` mapeia para a classe .sec-<color> (tokens do tema) */
export const SECTIONS = [
	{ id: 'today', label: 'Hoje', color: 'today', Icon: Sun },
	{ id: 'operations', label: 'Operações', color: 'ops', Icon: Zap },
	{ id: 'missions', label: 'Missões', color: 'missions', Icon: Target },
	{ id: 'protocols', label: 'Protocolos', color: 'protocols', Icon: FlameKindling },
	{ id: 'journal', label: 'Diário', color: 'journal', Icon: BookOpen },
	{ id: 'finance', label: 'Finanças', color: 'finance', Icon: LineChart },
	{ id: 'wishlist', label: 'Wishlist', color: 'wishlist', Icon: ShoppingBag }
] as const satisfies readonly { id: Section; label: string; color: string; Icon: unknown }[];

/** Páginas que não aparecem nos chips (abertas pelo menu do avatar) */
export const HIDDEN_SECTIONS = [
	{ id: 'settings', label: 'Configurações', color: 'today', Icon: Settings }
] as const satisfies readonly { id: Section; label: string; color: string; Icon: unknown }[];

export function sectionColor(id: Section): string {
	return [...SECTIONS, ...HIDDEN_SECTIONS].find((s) => s.id === id)?.color ?? 'today';
}
export type FormType = 'task' | 'goal' | 'wishlist' | 'transaction' | 'wallet' | 'habit';

export type FormPayload =
	| { kind: 'task'; content: string; goal_id: string | null; due_date: string | null }
	| { kind: 'goal'; title: string }
	| {
			kind: 'wishlist';
			title: string;
			url: string;
			image_url?: string;
			description?: string;
			current_price: number;
			target_price: number;
			currency: string;
	  }
	| {
			kind: 'transaction';
			wallet_id: string;
			amount: number;
			currency: string;
			category: string;
			description?: string;
			date: string;
			is_recurring: boolean;
	  }
	| {
			kind: 'wallet';
			name: string;
			type: 'cash' | 'vr' | 'inflow';
			emoji: string;
			currency: string;
	  }
	| {
			kind: 'habit';
			name: string;
			emoji: string;
	  };
