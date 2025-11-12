import { Item } from "@/entrypoints/newtab/types";

export const itemsStorage = storage.defineItem<Item[]>("local:items", {
  fallback: [
    {
      id: Date.now(),
      type: "note",
      content: "Bem vindo à Station One!",
      completed: false,
    },
  ],
});
