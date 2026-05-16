// ─── Shared Dashboard Types ───────────────────────────────────────────────────

export type Section = 'operations' | 'missions' | 'wishlist' | 'finance' | 'protocols';
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
