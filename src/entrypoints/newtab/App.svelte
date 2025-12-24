<script lang="ts">
  import { onMount } from "svelte";

  import { goalsStorage, itemsStorage } from "@/lib/storage";
  import GoalCard from "./GoalCard.svelte";
  import ItemCard from "./ItemCard.svelte";
  import type { Goal, Item } from "./types";

  import "./app.css";

  let items: Item[] = [];
  let goals: Goal[] = [];
  let currentDate = "";
  let currentTime = "";

  let selectedType: Item["type"] = "note";
  let content = "";

  function updateDateTime() {
    const now = new Date();
    currentDate = now.toLocaleDateString("pt-BR", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
    currentTime = now.toLocaleTimeString("pt-BR", {
      hour: "2-digit",
      minute: "2-digit",
    });
  }

  async function handleSubmit() {
    if (!content.trim()) return;
    const newItem: Item = {
      id: crypto.randomUUID(),
      type: selectedType,
      content: content.trim(),
      completed: selectedType === "task" ? false : undefined,
    };
    items = [...items, newItem];
    await itemsStorage.setValue(items);
    content = "";
  }

  async function handleToggleTask(event: CustomEvent<{ id: string }>) {
    const { id } = event.detail;
    items = items.map((item) =>
      item.id === id ? { ...item, completed: !item.completed } : item
    );
    await itemsStorage.setValue(items);
  }

  async function handleToggleMilestone(
    event: CustomEvent<{ goalId: string; milestoneId: string }>
  ) {
    const { goalId, milestoneId } = event.detail;

    goals = goals.map((g) => {
      if (g.id === goalId) {
        const updatedMilestones = g.milestones.map((m) => {
          if (m.id === milestoneId) {
            return { ...m, completed: !m.completed };
          }
          return m;
        });
        return { ...g, milestones: updatedMilestones };
      }
      return g;
    });

    await goalsStorage.setValue(goals);
  }

  onMount(() => {
    (async () => {
      items = await itemsStorage.getValue();
      goals = await goalsStorage.getValue();
      updateDateTime();
    })();

    updateDateTime();
    const timer = setInterval(updateDateTime, 1000);

    return () => clearInterval(timer);
  });
</script>

<div class="h-screen grid grid-cols-[1fr_350px] font-sans">
  <div class="flex flex-col">
    <header class="p-8">
      <div class="text-right">
        <div class="text-7xl font-bold">{currentTime}</div>
        <div class="text-xl text-slate-400">{currentDate}</div>
      </div>
    </header>

    <section class="p-8 pt-0">
      <h2 class="text-xl font-bold mb-4 opacity-80">Metas de Longo Prazo</h2>

      <div class="space-y-4">
        {#each goals as goal (goal.id)}
          <GoalCard {goal} on:toggleMilestone={handleToggleMilestone} />
        {/each}
      </div>
    </section>

    <main class="flex-grow p-8 overflow-y-auto space-y-4">
      <h2 class="text-xl font-bold mb-4 opacity-80">Itens Diários</h2>
      <div class="space-y-4">
        {#each items as item (item.id)}
          <ItemCard {item} on:toggle={handleToggleTask} />
        {/each}
      </div>
    </main>
  </div>

  <aside class="p-8 overflow-y-auto flex w-full">
    <div class="divider divider-horizontal"></div>
    <div>
      <h2 class="text-2xl font-bold mb-6">Adicionar Item</h2>
      <form class="space-y-4" on:submit|preventDefault={handleSubmit}>
        <div class="form-control w-full max-w-xs">
          <label class="label" for="item-type">
            <span class="label-text">Tipo de Item</span>
          </label>
          <select
            id="item-type"
            class="select select-bordered"
            bind:value={selectedType}
          >
            <option value="note">Nota</option>
            <option value="task">Tarefa</option>
            <option value="link">Link</option>
          </select>
        </div>

        {#if selectedType === "note" || selectedType === "task"}
          <div class="form-control">
            <label class="label" for="content-text">
              <span class="label-text">Conteúdo</span>
            </label>
            <textarea
              id="content-text"
              class="textarea textarea-bordered h-24"
              placeholder="Escreva sua nota ou tarefa..."
              bind:value={content}
            ></textarea>
          </div>
        {:else if selectedType === "link"}
          <div class="form-control w-full max-w-xs">
            <label class="label" for="content-link">
              <span class="label-text">URL do Link</span>
            </label>
            <input
              type="url"
              id="content-link"
              class="input input-bordered w-full max-w-xs"
              placeholder="https://exemplo.com"
              bind:value={content}
            />
          </div>
        {/if}

        <button class="btn btn-primary w-full">Adicionar</button>
      </form>
    </div>
  </aside>
</div>

<style>
  :global(body) {
    font-family: "Inter", sans-serif;
  }
</style>
