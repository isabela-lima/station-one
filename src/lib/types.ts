export interface Item {
	id: string;
	type: 'note' | 'task' | 'link';
	content: string;
	title?: string;
	completed: boolean;
	priority?: boolean;
	dueDate?: string;
	user: string;
	created?: string;
}

export interface Goal {
	id: string;
	title: string;
	user: string;
}

export interface Milestone {
	id: string;
	goal: string;
	title: string;
	completed: boolean;
}

export interface WishlistItem {
	id: string;
	title: string;
	url: string;
	currentPrice: number;
	targetPrice: number;
	imageUrl?: string;
	description?: string;
	user: string;
}

export interface Habit {
	id: string;
	name: string;
	emoji: string;
	user: string;
}

export interface HabitCompletion {
	id: string;
	habit: string;
	date: string;
	user: string;
}

export interface DailyLog {
	id: string;
	date: string;
	content: string;
	user: string;
}

export interface Toast {
	id: string;
	message: string;
	type: 'success' | 'error' | 'info';
}
