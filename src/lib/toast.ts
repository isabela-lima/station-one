import { writable } from 'svelte/store';
import type { Toast } from './models/types';

export const toasts = writable<Toast[]>([]);

export function showToast(message: string, type: Toast['type'] = 'success') {
	const id = crypto.randomUUID();
	toasts.update((list) => [...list, { id, message, type }]);
	setTimeout(() => {
		toasts.update((list) => list.filter((t) => t.id !== id));
	}, 3000);
}
