// ─── Toast ────────────────────────────────────────────────────────────────────

export interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info';
}

// ─── Items / Goals / Milestones ───────────────────────────────────────────────

export interface Item {
	id: string;
	user_id: string;
	type: 'note' | 'task' | 'link';
	content: string;
	title?: string;
	completed: boolean;
	priority: boolean;
	due_date?: string;
	created_at: string;
}

export interface DailyLog {
	id: string;
	user_id: string;
	date: string;
	content: string;
	created_at: string;
	updated_at: string;
}

export interface Habit {
	id: string;
	user_id: string;
	name: string;
	emoji: string;
	streak: number;
	completed_today: boolean;
	created_at: string;
}

export interface Goal {
	id: string;
	user_id: string;
	title: string;
	created_at: string;
}

export interface Milestone {
	id: string;
	user_id: string;
	goal_id: string;
	title: string;
	completed: boolean;
	created_at: string;
}

export interface WishlistItem {
	id: string;
	user_id: string;
	title: string;
	url: string;
	image_url?: string;
	description?: string;
	current_price: number;
	target_price: number;
	currency: string;
	created_at: string;
}

export interface Wallet {
	id: string;
	user_id: string;
	name: string;
	type: 'cash' | 'vr' | 'inflow';
	emoji: string;
	currency: string;
	balance: number;
	created_at: string;
}

export interface WalletSuggestion {
	category: string;
	suggested_wallet_type: string;
	reason: string;
}

export interface Transaction {
	id: string;
	user_id: string;
	wallet_id: string;
	amount: number;
	currency: string;
	category: string;
	description?: string;
	date: string;
	is_recurring: boolean;
	created_at: string;
}

export interface Debt {
	id: string;
	user_id: string;
	name: string;
	original_amount: number;
	current_amount: number;
	monthly_payment: number;
	currency: string;
	start_date: string;
	created_at: string;
}

export interface Budget {
	id: string;
	user_id: string;
	wallet_id?: string;
	category: string;
	limit_amount: number;
	currency: string;
	period: string;
	spent: number;
}

export interface DebtProjection {
	debt_id: string;
	current_amount: number;
	monthly_payment: number;
	estimated_end_date: string;
	months_remaining: number;
	timeline: Array<{ month: string; remaining_amount: number }>;
}

export interface HealthLog {
	id: string;
	user_id: string;
	date: string;
	trained: boolean;
	hrv_score?: number;
	energy_level?: number;
	notes?: string;
	created_at: string;
}

export interface PersonalROI {
	monthly_cost: number;
	trainings_this_month: number;
	cost_per_training?: number;
	target_trainings: number;
	target_cost_per_training: number;
	status: 'validated' | 'partial' | 'at_risk';
	message: string;
}

export interface AutonomyIndicator {
	days_of_runway: number;
	avg_daily_expense: number;
	free_balance: number;
	currency: string;
}

export interface FinanceOverview {
	wallets: Wallet[];
	total_debt: number;
	autonomy: AutonomyIndicator;
	alerts: string[];
}

export interface SimulatorResponse {
	purchase_amount: number;
	installments: number;
	monthly_impact: number;
	three_month_projection: Array<{
		month: string;
		installment_amount: number;
		projected_free_balance: number;
		debt_impact: number;
	}>;
	debt_payoff_delay_months: number;
	recommendation: 'go' | 'caution' | 'avoid';
	reason: string;
}
