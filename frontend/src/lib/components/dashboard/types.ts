// ─── Shared Dashboard Types ───────────────────────────────────────────────────

import { Sun, Zap, Target, FlameKindling, LineChart, ShoppingBag } from 'lucide-svelte';

export type Section = 'today' | 'operations' | 'missions' | 'wishlist' | 'finance' | 'protocols';

/** Seções que têm formulário de criação (todas menos 'today') */
export type CreatableSection = Exclude<Section, 'today'>;

/** Ordem da navegação; `color` mapeia para a classe .sec-<color> (tokens do tema) */
export const SECTIONS = [
	{ id: 'today', label: 'Hoje', color: 'today', Icon: Sun },
	{ id: 'operations', label: 'Operações', color: 'ops', Icon: Zap },
	{ id: 'missions', label: 'Missões', color: 'missions', Icon: Target },
	{ id: 'protocols', label: 'Protocolos', color: 'protocols', Icon: FlameKindling },
	{ id: 'finance', label: 'Finanças', color: 'finance', Icon: LineChart },
	{ id: 'wishlist', label: 'Wishlist', color: 'wishlist', Icon: ShoppingBag }
] as const satisfies readonly { id: Section; label: string; color: string; Icon: unknown }[];

export function sectionColor(id: Section): string {
	return SECTIONS.find((s) => s.id === id)?.color ?? 'today';
}
export type FormType = 'note' | 'task' | 'link' | 'goal' | 'milestone' | 'wishlist' | 'transaction' | 'wallet' | 'habit';

export type FormPayload =
	| {
			kind: 'item';
			type: 'note' | 'task' | 'link';
			content: string;
			title?: string;
			completed: boolean;
			priority: boolean;
	  }
	| { kind: 'goal'; title: string }
	| { kind: 'milestone'; title: string; goal_id: string }
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
