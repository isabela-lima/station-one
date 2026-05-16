import { PUBLIC_API_URL } from '$env/static/public';
import type {
	Budget,
	DailyLog,
	Debt,
	DebtProjection,
	FinanceOverview,
	Goal,
	Habit,
	HealthLog,
	Item,
	Milestone,
	PersonalROI,
	SimulatorResponse,
	Transaction,
	Wallet,
	WalletSuggestion,
	WishlistItem
} from './models/types';
import { getAuthToken } from './supabase';

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
	const token = await getAuthToken();
	const res = await fetch(`${PUBLIC_API_URL}${path}`, {
		...options,
		headers: {
			'Content-Type': 'application/json',
			...(token ? { Authorization: `Bearer ${token}` } : {}),
			...options.headers
		}
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail ?? `HTTP ${res.status}`);
	}
	if (res.status === 204) return undefined as T;
	return res.json();
}

// ─── Items ────────────────────────────────────────────────

export const items = {
	list: (params?: { type?: string; priority?: boolean; completed?: boolean }) => {
		const q = new URLSearchParams();
		if (params?.type) q.set('type', params.type);
		if (params?.priority !== undefined) q.set('priority', String(params.priority));
		if (params?.completed !== undefined) q.set('completed', String(params.completed));
		return request<Item[]>(`/items?${q}`);
	},
	create: (body: Omit<Item, 'id' | 'user_id' | 'created_at'>) =>
		request<Item>('/items', { method: 'POST', body: JSON.stringify(body) }),
	update: (id: string, body: Partial<Item>) =>
		request<Item>(`/items/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
	delete: (id: string) => request<void>(`/items/${id}`, { method: 'DELETE' })
};

// ─── Daily Log ─────────────────────────────────────────

export const dailyLogs = {
	today: () => request<DailyLog>('/daily-logs/today'),
	update: (content: string) =>
		request<DailyLog>('/daily-logs/today', { method: 'PATCH', body: JSON.stringify({ content }) })
};

// ─── Habits ─────────────────────────────────────────────

export const habits = {
	list: () => request<Habit[]>('/habits'),
	create: (body: { name: string; emoji: string }) =>
		request<Habit>('/habits', { method: 'POST', body: JSON.stringify(body) }),
	toggleToday: (id: string) =>
		request<Habit>(`/habits/${id}/toggle-today`, { method: 'POST' }),
	delete: (id: string) => request<void>(`/habits/${id}`, { method: 'DELETE' })
};

// ─── Goals ────────────────────────────────────────────────

export const goals = {
	list: () => request<Goal[]>('/goals'),
	create: (body: { title: string }) =>
		request<Goal>('/goals', { method: 'POST', body: JSON.stringify(body) }),
	delete: (id: string) => request<void>(`/goals/${id}`, { method: 'DELETE' })
};

// ─── Milestones ───────────────────────────────────────────

export const milestones = {
	list: (goalId?: string) => {
		const q = goalId ? `?goal_id=${goalId}` : '';
		return request<Milestone[]>(`/milestones${q}`);
	},
	create: (body: { goal_id: string; title: string }) =>
		request<Milestone>('/milestones', { method: 'POST', body: JSON.stringify(body) }),
	update: (id: string, body: { completed?: boolean; title?: string }) =>
		request<Milestone>(`/milestones/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
	delete: (id: string) => request<void>(`/milestones/${id}`, { method: 'DELETE' })
};

// ─── Wishlist ─────────────────────────────────────────────

export const wishlist = {
	list: () => request<WishlistItem[]>('/wishlist'),
	create: (body: Omit<WishlistItem, 'id' | 'user_id' | 'created_at'>) =>
		request<WishlistItem>('/wishlist', { method: 'POST', body: JSON.stringify(body) }),
	delete: (id: string) => request<void>(`/wishlist/${id}`, { method: 'DELETE' })
};

// ─── Finance ──────────────────────────────────────────────

export const finance = {
	overview: () => request<FinanceOverview>('/finance/overview'),

	wallets: {
		list: () => request<Wallet[]>('/finance/wallets'),
		create: (body: { name: string; type: string; emoji?: string; currency?: string }) =>
			request<Wallet>('/finance/wallets', { method: 'POST', body: JSON.stringify(body) }),
		balance: (id: string) => request<{ balance: number }>(`/finance/wallets/${id}/balance`),
		suggest: (category: string) =>
			request<WalletSuggestion>(`/finance/wallets/suggest?category=${category}`)
	},

	transactions: {
		list: (params?: { wallet_id?: string; category?: string }) => {
			const q = new URLSearchParams(params as Record<string, string>);
			return request<Transaction[]>(`/finance/transactions?${q}`);
		},
		create: (body: Omit<Transaction, 'id' | 'user_id' | 'created_at'>) =>
			request<Transaction>('/finance/transactions', { method: 'POST', body: JSON.stringify(body) })
	},

	debts: {
		list: () => request<Debt[]>('/finance/debts'),
		create: (body: Omit<Debt, 'id' | 'user_id' | 'created_at'>) =>
			request<Debt>('/finance/debts', { method: 'POST', body: JSON.stringify(body) }),
		payment: (id: string, amount: number) =>
			request<Debt>(`/finance/debts/${id}/payment`, {
				method: 'PATCH',
				body: JSON.stringify({ amount })
			}),
		projection: (id: string) => request<DebtProjection>(`/finance/debts/${id}/projection`)
	},

	simulator: (body: { amount: number; installments: number }) =>
		request<SimulatorResponse>('/finance/simulator', {
			method: 'POST',
			body: JSON.stringify(body)
		}),

	budgets: {
		list: () => request<Budget[]>('/finance/budgets'),
		create: (body: {
			category: string;
			limit_amount: number;
			wallet_id?: string;
			currency?: string;
		}) => request<Budget>('/finance/budgets', { method: 'POST', body: JSON.stringify(body) }),
		delete: (id: string) => request<void>(`/finance/budgets/${id}`, { method: 'DELETE' })
	},

	healthLogs: {
		list: (month?: string) => {
			const q = month ? `?month=${month}` : '';
			return request<HealthLog[]>(`/finance/health-logs${q}`);
		},
		log: (body: { trained?: boolean; hrv_score?: number; energy_level?: number; notes?: string }) =>
			request<HealthLog>('/finance/health-logs', { method: 'POST', body: JSON.stringify(body) }),
		roi: () => request<PersonalROI>('/finance/health-logs/roi')
	}
};
