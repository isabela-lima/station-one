export interface Item {
  completed?: boolean;
  id: string;
  type: string;
  content: string;
}

export interface Goal {
  id: string;
  title: string;
  milestones: Milestone[];
}

export interface Milestone {
  id: string;
  title: string;
  completed: boolean;
}
