import { Goal, Item } from "@/entrypoints/newtab/types";

export const itemsStorage = storage.defineItem<Item[]>("local:items", {
  fallback: [
    {
      id: crypto.randomUUID(),
      type: "note",
      content: "Bem vindo à Station One!",
      completed: false,
    },
  ],
});

export const goalsStorage = storage.defineItem<Goal[]>("local:goals", {
  fallback: [
    {
      id: crypto.randomUUID(),
      title: "Aprender Japonês",
      milestones: [
        {
          id: crypto.randomUUID(),
          title: "Completar o Nível 1 do WaniKani",
          completed: false,
        },
        {
          id: crypto.randomUUID(),
          title: "Aprender Hiragana",
          completed: false,
        },
        {
          id: crypto.randomUUID(),
          title: "Aprender Katakana",
          completed: false,
        },
      ],
    },
  ],
});
